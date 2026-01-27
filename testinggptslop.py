# main.py
"""
PyTermGUI: Search bar + Collapsible dropdown + optional mpv playback.

Fixes:
- Dropdown navigation handled inside the InputField (↑/↓/Enter/Esc) so focus doesn't drift to Buttons.
- Mouse-picking a result re-selects the InputField.
- Window binds avoid clobbering InputField navigation keys.

Controls:
- Type to search
- ↑/↓ : move selection (when dropdown open)
- Enter: pick selected (when dropdown open)
- Esc  : close dropdown
- /    : focus search
- Space: play/pause (if mpv available)
- n/p  : next/prev
- r    : toggle repeat
- q    : quit
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Sequence

import pytermgui as ptg
from pytermgui.file_loaders import YamlLoader

BASE_DIR = Path(__file__).resolve().parent
MUSIC_DIR = BASE_DIR / "music"
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}

THEME = """
config:
  Window:
    styles:
      fill: "@235 252"
      border: "@235 81"
      corner: "@235 81"
  Container:
    styles:
      fill: "@235 252"
      border: "@235 81"
      corner: "@235 81"
  Label:
    styles:
      value: "@235 252"
  InputField:
    styles:
      prompt: "@235 252 dim italic"
      value: "@235 255"
      cursor: "@81 235"
  Button:
    styles:
      fill: "@237 252"
      label: "@237 252"
      border: "@237 81"
      corner: "@237 81"
      highlight: "@81 235 bold"
  Collapsible:
    styles:
      fill: "@235 252"
      border: "@235 81"
      corner: "@235 81"
"""


def discover_tracks(folder: Path) -> List[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    return [p for p in sorted(folder.rglob("*")) if p.is_file() and p.suffix.lower() in AUDIO_EXTS]


def _redraw(manager: ptg.WindowManager) -> None:
    try:
        manager.compositor.set_redraw()
    except Exception:
        pass


def _set_input_text(field: ptg.InputField, text: str) -> None:
    lines = text.splitlines() or [""]
    field._lines = lines  # noqa: SLF001
    field.cursor.row = 0
    field.cursor.col = len(lines[0])
    field._selection_length = 1  # noqa: SLF001
    field._styled_cache = None  # noqa: SLF001


def focus_widget(manager: ptg.WindowManager, window: ptg.Window, widget: ptg.Widget) -> None:
    """Focus a window and select a widget inside it (so it receives keys)."""
    manager.focus(window)
    try:
        for idx, (w, _inner) in enumerate(window.selectables):
            if w is widget:
                window.select(idx)
                break
    except Exception:
        pass


class MpvIpc:
    """Minimal mpv JSON IPC controller."""

    def __init__(self) -> None:
        self.proc: Optional[subprocess.Popen] = None
        self.ipc_addr = self._make_ipc_addr()
        self.current: Optional[Path] = None

    @staticmethod
    def _make_ipc_addr() -> str:
        pid = os.getpid()
        if os.name == "nt":
            return rf"\\.\pipe\ptg-mpv-{pid}"
        return str(Path("/tmp") / f"ptg-mpv-{pid}.sock")

    def _ensure_mpv(self) -> str:
        mpv = shutil.which("mpv")
        if not mpv:
            raise RuntimeError("mpv not found on PATH.")
        return mpv

    def start(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            return

        mpv = self._ensure_mpv()

        if os.name != "nt":
            try:
                Path(self.ipc_addr).unlink(missing_ok=True)
            except Exception:
                pass

        self.proc = subprocess.Popen(
            [
                mpv,
                "--no-video",
                "--idle=yes",
                "--really-quiet",
                f"--input-ipc-server={self.ipc_addr}",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + 2.0
        last_err: Optional[Exception] = None
        while time.time() < deadline:
            try:
                _ = self._request({"command": ["get_property", "mpv-version"]})
                return
            except Exception as e:
                last_err = e
                time.sleep(0.05)

        raise RuntimeError(f"mpv IPC not ready: {last_err!r}")

    def _request(self, payload: dict) -> dict:
        data = (json.dumps(payload) + "\n").encode("utf-8")

        if os.name == "nt":
            with open(self.ipc_addr, "r+b", buffering=0) as f:
                f.write(data)
                line = f.readline()
                if not line:
                    raise RuntimeError("No IPC response from mpv.")
                return json.loads(line.decode("utf-8", errors="replace"))

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(self.ipc_addr)
            s.sendall(data)
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
            if not buf:
                raise RuntimeError("No IPC response from mpv.")
            return json.loads(buf.decode("utf-8", errors="replace"))
        finally:
            s.close()

    def cmd(self, *command) -> dict:
        self.start()
        return self._request({"command": list(command)})

    def load(self, path: Path) -> None:
        self.start()
        self.current = path
        self.cmd("loadfile", str(path), "replace")
        self.cmd("set_property", "pause", False)

    def toggle_pause(self) -> bool:
        self.start()
        self.cmd("cycle", "pause")
        res = self.cmd("get_property", "pause")
        return bool(res.get("data"))

    def set_repeat(self, on: bool) -> None:
        self.start()
        self.cmd("set_property", "loop-file", "inf" if on else "no")

    def quit(self) -> None:
        if self.proc is None:
            return
        try:
            self.cmd("quit")
        except Exception:
            pass
        try:
            if self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass
        self.proc = None
        self.current = None


@dataclass(frozen=True)
class SearchConfig:
    input_width: int = 58
    max_results: int = 12
    results_height: int = 9


class SearchDropdown:
    """InputField + Collapsible dropdown (focus-safe)."""

    def __init__(
        self,
        manager: ptg.WindowManager,
        window: ptg.Window,
        items: Sequence[Path],
        *,
        cfg: SearchConfig,
        on_pick: Callable[[Path], None],
    ) -> None:
        self.manager = manager
        self.window = window
        self.items = list(items)
        self.cfg = cfg
        self.on_pick = on_pick

        self.results = ptg.Container(
            box="EMPTY",
            height=cfg.results_height,
            overflow=ptg.Overflow.SCROLL,
            parent_align=ptg.HorizontalAlignment.LEFT,
        )
        self.dropdown = ptg.Collapsible("Matches", self.results, parent_align=ptg.HorizontalAlignment.LEFT)

        self.open = False
        self.matches: List[Path] = []
        self.selected = 0
        self._mute_rebuild = False

        self.search = self._make_search()

    def widgets(self) -> list[ptg.Widget]:
        return [self.search, self.dropdown]

    def _make_search(self) -> ptg.InputField:
        outer = self

        class SearchField(ptg.InputField):
            def handle_key(self, key: str) -> bool:  # type: ignore[override]
                # When dropdown is open, arrows & enter/esc control it, not cursor/focus.
                if outer.open:
                    if key == ptg.keys.UP:
                        outer.move(-1)
                        return True
                    if key == ptg.keys.DOWN:
                        outer.move(+1)
                        return True
                    if key == ptg.keys.ENTER:
                        outer.choose()
                        return True
                    if key == ptg.keys.ESC:
                        outer.close()
                        return True

                old = self.value
                handled = super().handle_key(key)

                if handled and not outer._mute_rebuild and self.value != old:
                    outer.rebuild(self.value)

                return handled

        field = SearchField(prompt="Search: ", width=self.cfg.input_width)
        return field

    def rebuild(self, query: str) -> None:
        q = query.strip().lower()

        self.selected = 0
        self.results.set_widgets([])

        if not q:
            self.close()
            return

        found: List[Path] = []
        for p in self.items:
            if q in p.stem.lower():
                found.append(p)
                if len(found) >= self.cfg.max_results:
                    break

        self.matches = found
        self.open = True
        self.dropdown.expand()

        if not self.matches:
            self.results.set_widgets([ptg.Label("[ptg.detail]No matches[/ptg.detail]", parent_align=0)])
            _redraw(self.manager)
            return

        self.render()
        _redraw(self.manager)

    def render(self) -> None:
        if not self.open or not self.matches:
            return

        if self.selected >= len(self.matches):
            self.selected = 0

        rows: List[ptg.Widget] = []
        for i, p in enumerate(self.matches):
            prefix = "▶ " if i == self.selected else "  "
            btn = ptg.Button(
                prefix + p.stem,
                lambda *_ignore, idx=i: self.pick(idx),
                centered=False,
                parent_align=ptg.HorizontalAlignment.LEFT,
            )
            btn.chars["delimiter"] = [" ", " "]
            rows.append(btn)

        self.results.set_widgets(rows)

    def move(self, delta: int) -> None:
        if not self.open:
            self.rebuild(self.search.value)
            return
        if not self.matches:
            return
        self.selected = (self.selected + delta) % len(self.matches)
        self.render()
        _redraw(self.manager)

    def pick(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.matches):
            return
        picked = self.matches[idx]

        self._mute_rebuild = True
        try:
            _set_input_text(self.search, picked.stem)
        finally:
            self._mute_rebuild = False

        self.on_pick(picked)
        self.close()
        focus_widget(self.manager, self.window, self.search)

    def choose(self) -> None:
        if not self.open:
            self.rebuild(self.search.value)
            return
        if not self.matches:
            return
        self.pick(self.selected)

    def close(self) -> None:
        self.open = False
        self.matches = []
        self.selected = 0
        self.results.set_widgets([])
        self.dropdown.collapse()
        _redraw(self.manager)


def build_ui(manager: ptg.WindowManager) -> ptg.Window:
    tracks = discover_tracks(MUSIC_DIR)
    player = MpvIpc()
    state = {"repeat": False, "index": 0, "paused": False}

    win = ptg.Window(width=64, box="DOUBLE").set_title("[210 bold]Termify (refined)").center()

    header = ptg.Container(
        ptg.Label("[bold]Termify[/]", parent_align=ptg.HorizontalAlignment.LEFT),
        ptg.Label(f"Music folder: {MUSIC_DIR}", parent_align=ptg.HorizontalAlignment.LEFT),
        ptg.Label(f"Tracks: {len(tracks)}", parent_align=ptg.HorizontalAlignment.LEFT),
        box="EMPTY_VERTICAL",
        width=62,
    )

    now_playing = ptg.Label(
        "[ptg.detail]Now playing:[/ptg.detail] (none)",
        parent_align=ptg.HorizontalAlignment.CENTER,
    )

    help_line = ptg.Label(
        "[ptg.detail]Type to search • ↑/↓ select • Enter play • Esc close • / focus search • q quit[/ptg.detail]",
        parent_align=ptg.HorizontalAlignment.CENTER,
    )

    def toast(msg: str) -> None:
        try:
            manager.toast(msg)
        except Exception:
            pass

    def set_now(path: Optional[Path]) -> None:
        now_playing.value = (
            "[ptg.detail]Now playing:[/ptg.detail] (none)"
            if path is None
            else f"[ptg.detail]Now playing:[/ptg.detail] [bold]{path.stem}[/]"
        )

    def safe_start() -> bool:
        if not tracks:
            toast(f"No audio files in {MUSIC_DIR}")
            return False
        try:
            player.start()
            return True
        except Exception as e:
            toast(str(e))
            return False

    def play_index(idx: int) -> None:
        if not safe_start():
            return
        state["index"] = idx % len(tracks)
        path = tracks[state["index"]]
        try:
            player.load(path)
            player.set_repeat(state["repeat"])
            state["paused"] = False
            set_now(path)
        except Exception as e:
            toast(str(e))

    def on_pick(path: Path) -> None:
        try:
            idx = tracks.index(path)
        except ValueError:
            return
        play_index(idx)

    search = SearchDropdown(
        manager,
        win,
        tracks,
        cfg=SearchConfig(),
        on_pick=on_pick,
    )
    win._search_widget = search.search  # noqa: SLF001 (store for main focus)

    btn_prev = ptg.Button("Prev (p)", lambda *_: play_index(state["index"] - 1), centered=True)
    btn_play = ptg.Button("Play/Pause (Space)", lambda *_: toggle_pause(), centered=True)
    btn_next = ptg.Button("Next (n)", lambda *_: play_index(state["index"] + 1), centered=True)
    btn_repeat = ptg.Button("Repeat (r)", lambda *_: toggle_repeat(), centered=True)
    btn_quit = ptg.Button("Quit (q)", lambda *_: manager.stop(), centered=True)

    for b in (btn_prev, btn_play, btn_next, btn_repeat, btn_quit):
        b.chars["delimiter"] = [" ", " "]

    controls = ptg.Splitter(btn_prev, btn_play, btn_next)
    controls.chars["separator"] = "   "
    controls.styles.separator = "@235 252"

    bottom = ptg.Splitter(btn_repeat, btn_quit)
    bottom.chars["separator"] = "   "
    bottom.styles.separator = "@235 252"

    def toggle_pause() -> None:
        if not safe_start():
            return
        if player.current is None and tracks:
            play_index(state["index"])
            return
        try:
            paused = player.toggle_pause()
            state["paused"] = paused
            toast("Paused" if paused else "Playing")
        except Exception as e:
            toast(str(e))

    def toggle_repeat() -> None:
        state["repeat"] = not state["repeat"]
        if safe_start():
            try:
                player.set_repeat(state["repeat"])
            except Exception:
                pass
        toast("Repeat ON" if state["repeat"] else "Repeat OFF")

    win += header
    win += ""
    for w in search.widgets():
        win += w
    win += ""
    win += now_playing
    win += ""
    win += controls
    win += ""
    win += bottom
    win += ""
    win += help_line

    def focus_search(*_args: object) -> None:
        focus_widget(manager, win, search.search)

    win.bind("/", focus_search, "Focus search")
    win.bind("q", lambda *_: manager.stop(), "Quit")
    win.bind(" ", lambda *_: toggle_pause(), "Play/pause")
    win.bind("n", lambda *_: play_index(state["index"] + 1), "Next")
    win.bind("p", lambda *_: play_index(state["index"] - 1), "Prev")
    win.bind("r", lambda *_: toggle_repeat(), "Repeat")
    win.bind(ptg.keys.ESC, lambda *_: search.close(), "Close dropdown")

    set_now(None)
    return win


def main() -> None:
    with YamlLoader() as loader:
        loader.load(THEME)

    with ptg.WindowManager() as manager:
        win = build_ui(manager)
        manager.add(win)
        focus_widget(manager, win, win._search_widget)  # noqa: SLF001
        manager.run()


if __name__ == "__main__":
    main()
