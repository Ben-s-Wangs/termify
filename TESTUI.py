import pytermgui as ptg
from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets import Container 

# --- WINDOWS-EXCLUSIVE BUGFIX ---
# including container keys because they cannot be found on windows for some reason
if not hasattr(Container, "keys"):
    Container.keys = {} 

# use set() here, NOT []
Container.keys["scroll_down"] = set() 
Container.keys["scroll_up"] = set()

from backend import AudioBackend

player = AudioBackend()
#config dictates colors following the format @background color foreground color
#See pytermgui documentation for more info on styling
CONFIG = """
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
  Splitter:
    styles:
      fill: "@235 252"
      separator: "@235 252"
"""

with YamlLoader() as loader:
    loader.load(CONFIG)

#Menus are built using functions to allow for easy switching between them by adding and removing them from the window manager
# return music_player_menu
def build_music_player_menu(manager: ptg.WindowManager, username: str = "") -> ptg.Window:
    play_state = {
        "on": False,
        "duration": 2,
        "current_time": 0
    } # local state variables
    def on_play_song(*_):
        query = search_input.value
        if not query: #Cant play music if a song wasnt searched
            manager.toast("Please Enter A Song Name First!")
            return

        manager.toast(f"Search for {query}...")

        def update_title_label(title): #update song title label
            song_label.value= f"[bold]{title}[/]"
        
        def update_progress_val(val): #update progress bar and duration
            play_state["duration"] = val if val > 0 else 2
            duration_label.value = f"{(val // 60):02d}:{(val % 60):02d}"
        
        # BACKEND CONNECTION
        player.play_song(query, title_callback=update_title_label, progress_callback=update_progress_val, seconds_callback=update_seconds_val)
        play_state["on"] = True 
        btn_play.label = "⏸"

    def update_seconds_val(seconds): #update seconds label and progress bar
        seconds_label.value = f"{(seconds // 60):02d}:{(seconds % 60):02d}"
        progress.value = seconds / play_state["duration"]
    def on_toggle_play(*_): #play/pause button logic
        if not player.last_query: #Cant play/pause if no song was played
            manager.toast("Search For A Song First!")
            return
        
        play_state["on"] = not play_state["on"]
        btn_play.label = "⏸" if play_state["on"] else "▶" #Change the button label accordingly

        if play_state["on"]: #resume or pause song
            manager.toast("Resuming...")
            player.resume_song()
        else:
            manager.toast("Paused")
            player.pause_song()

    def on_back(*_): #back to main menu logic
        player.stop_song()
        manager.toast("Back To Welcome")
        manager.remove(music_player_menu)
        manager.add(build_start_menu(manager))

    def on_quit(*_): #quit logic
        player.stop_song()
        manager.toast("Goodbye")
        manager.stop()

    def on_rewind(*_): #rewind logic
        player.stop_song()
        manager.toast("Rewinding...")
        player.play_song(player.last_query, seconds_callback=update_seconds_val)
        play_state["on"] = True
        btn_play.label = "⏸"
    
    
    #Create a interactable search: Top Row 
    search_input = ptg.InputField("", prompt = "Search Song: ", centered=False, padding=0)
    search_btn = ptg.Button("⌕", on_play_song, centered=False, padding=0, parent_align=ptg.HorizontalAlignment.RIGHT)

    music_player_menu = ptg.Window(height = 10, width = 80, box = "DOUBLE").set_title("[210 bold]Termify").center() #just setting title, search bar using library

    music_player_menu += ptg.Label("[bold]Now Playing[/]", parent_align=ptg.HorizontalAlignment.CENTER) # start current playing song label

    song_label = ptg.Label("[dim]No song selected[/]", parent_align=ptg.HorizontalAlignment.CENTER)
    music_player_menu += song_label # add default song title to menu 
    music_player_menu += ""

    music_player_menu += search_input # add search to menu
    music_player_menu += search_btn

    progress = ptg.Slider(locked=False)
    music_player_menu += progress
    seconds_label = ptg.Label(f"-:--", centered=False, padding=0, parent_align=ptg.HorizontalAlignment.LEFT)
    duration_label = ptg.Label(f"-:--", centered=False, padding=0, parent_align=ptg.HorizontalAlignment.RIGHT)
    timestamps = ptg.Splitter(seconds_label, duration_label)
    timestamps.chars["separator"] = ""
    music_player_menu += timestamps
    

    #Bottom Row Buttons
    btn_back = ptg.Button("Back to Menu", on_back, centered=True)
    btn_play = ptg.Button("⏸", on_toggle_play, centered=True)
    btn_rewind = ptg.Button("↩️   Rewind", on_rewind, centered=True)
    btn_quit = ptg.Button("Quit", on_quit, centered=True)

    bottom_row = ptg.Splitter(btn_back, btn_play, btn_quit)
    bottom_row.chars["separator"] = ""
    music_player_menu += bottom_row

    #Real Bottom Row
    music_player_menu += ""
    music_player_menu += btn_rewind

    # Keybinds
    music_player_menu.bind(ptg.keys.ENTER, lambda *_ : on_play_song()) #search song
    music_player_menu.bind(ptg.keys.ESC, lambda *_ : (player.stop_song(), manager.stop())) #quit
    music_player_menu.bind(ptg.keys.CTRL_P, lambda *_ : on_toggle_play()) #play/pause
    music_player_menu.bind(ptg.keys.CTRL_B, lambda *_ : on_back()) #back to main menu
    music_player_menu.bind(ptg.keys.CTRL_R, lambda *_ : on_rewind()) #rewind


    return music_player_menu

#Function to build the start menu
def build_start_menu(manager: ptg.WindowManager) -> ptg.Window:
    def on_start(*_):
        manager.toast("Starting Music Player")
        music_player_menu = build_music_player_menu(manager)
        manager.remove(start_menu)
        manager.add(music_player_menu)

    header = ptg.Container(
        ptg.Label("[bold]A Terminal Based Music Player[/]",parent_align=ptg.HorizontalAlignment.LEFT,),
        ptg.Label("Made by:\nJordan Yang\nBen Wang\nMichael Ampong\nFor the DEV.0 Hackathon",
        parent_align=ptg.HorizontalAlignment.LEFT,),box="EMPTY_VERTICAL",width=60,
    )

    start_menu = (ptg.Window(header,"",width=60,box="DOUBLE",).set_title("[210 bold]Termify by Ben's Wangs").center())

    btn_start = ptg.Button("Start", on_start, centered=True)
    btn_quit = ptg.Button("Quit", lambda *_: manager.stop(), centered=True)

    # Make the clickable/visual padding consistent (helps “hitbox vs frame” feel)
    for b in (btn_start, btn_quit):
        b.chars["delimiter"] = [" ", " "]  # 1-space padding each side

    buttons = ptg.Splitter(btn_start, btn_quit)
    buttons.chars["separator"] = "   "       # spacing between buttons
    buttons.styles.separator = "@235 252"    # match background, no dark gaps

    start_menu.bind(ptg.keys.ESC, lambda *_ : manager.stop())
    start_menu.bind(ptg.keys.ENTER, on_start)

    start_menu += buttons
    return start_menu

# main function to help clean exit
if __name__ == '__main__':
    import sys
    try:
        with ptg.WindowManager() as manager:
            manager.add(build_start_menu(manager))
    except KeyboardInterrupt:
        pass
    finally:
        if 'player' in globals():
            player.stop_song()

        print("\033[?1000l\033[?1003l\033[?1006l\033[?1015l", end="")
        sys.exit(0)
