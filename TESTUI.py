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
#config dictates colors @background color foreground color
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

#     return music_player_menu
def build_music_player_menu(manager: ptg.WindowManager, username: str = "") -> ptg.Window:
    play_state = {"on": False} # local variable we will use to see
    def on_play_song(*_):
        query = search_input.value
        if not query: 
            manager.toast("Please enter a song name first!")
            return

        manager.toast(f"Search for {query}...")

        def update_title_label(title):
            song_label.value= f"[bold]{title}[/]"
        
        # BACKEND CONNECTION
        player.play_song(query, title_callback=update_title_label)
        play_state["on"] = True 
        btn_play.label = "⏸"

    def on_toggle_play(*_):
        if not player.last_query:
            manager.toast("Search for a song first!")
            return
        
        play_state["on"] = not play_state["on"]
        btn_play.label = "⏸" if play_state["on"] else "▶"

        if play_state["on"]:
            manager.toast("Resuming...")
            player.resume_song()
        else:
            manager.toast("Paused")
            player.pause_song()

    def on_sign_out(*_):
        player.stop_song()
        manager.toast("Signing Out")
        manager.remove(music_player_menu)
        manager.add(build_start_menu(manager))

    def on_quit(*_):
        player.stop_song()
        manager.toast("Goodbye")
        manager.stop()
    
    def on_prev(*_):
        player.stop_song()
        manager.toast("Rewinding")
        player.play_song(player.last_query)
        play_state["on"] = True
        btn_play.label = "⏸"
    
    
    #1. Create a interactable search: Row 1
    search_input = ptg.InputField("", prompt = "Search Song: ", centered=False, padding=0)
    search_btn = ptg.Button("⌕", on_play_song, centered=False, padding=0, parent_align=ptg.HorizontalAlignment.RIGHT)
    # row1 = ptg.Splitter(search_input, search_btn)
    # row1.set_char("separator", "")
    music_player_menu = ptg.Window(height = 10, width = 80, box = "DOUBLE").set_title("[210 bold]Termify").center() #just setting title, search bar using library

    music_player_menu += ptg.Label("[bold]Now Playing[/]", parent_align=ptg.HorizontalAlignment.CENTER) # start current playing song label

    song_label = ptg.Label("[dim]No song selected[/]", parent_align=ptg.HorizontalAlignment.CENTER)
    music_player_menu += song_label # add default song title to menu 
    music_player_menu += ""

    music_player_menu += search_input # add search to menu
    music_player_menu += search_btn
    # music_player_menu += row1
    # music_player_menu += ""


    
    btn_prev = ptg.Button("⏮Prev", on_prev, centered=True)
    btn_play = ptg.Button("⏸", on_toggle_play, centered=True)
    btn_next = ptg.Button("Skip⏭", lambda *_: manager.toast("Skip"), centered=True)

    # Row 2
    row2 = ptg.Splitter(ptg.Label(""), btn_prev, btn_play, btn_next, ptg.Label(""))
    row2.chars["separator"] = ""
    music_player_menu += row2
    music_player_menu += ""

    # Row 3
    btn_signout = ptg.Button("Log out", on_sign_out, centered=True)
    btn_quit = ptg.Button("Quit", on_quit, centered=True)
    row3 = ptg.Splitter(btn_signout, btn_quit)
    row3.chars["separator"] = ""
    music_player_menu += row3

    # Keybinds
    music_player_menu.bind(ptg.keys.ENTER, lambda *_ : on_play_song())
    music_player_menu.bind(ptg.keys.ESC, lambda *_ : (player.stop_song(), manager.stop()))
    # music_player_menu.bind(ptg.keys.ESC, lambda *_ : on_sign_out())

    return music_player_menu




def build_start_menu(manager: ptg.WindowManager) -> ptg.Window:
    def on_login(*_):
        manager.toast("Logging in")
        # login_menu = build_login_menu(manager)
        login_menu = build_music_player_menu(manager)
        manager.remove(start_menu)
        manager.add(login_menu)

    def on_create_account(*_):
        manager.toast("Create Account Pressed")
        # create_account_menu = build_create_account_menu(manager)
        # manager.remove(start_menu)
        # manager.add(create_account_menu)

    header = ptg.Container(
        ptg.Label("[bold]A Terminal Based Music Player[/]",parent_align=ptg.HorizontalAlignment.LEFT,),
        ptg.Label("Made by:\nJordan Yang\nBen Wang\nMichael Ampong\nAshish Tomar\nFor the DEV.0 Hackathon",
        parent_align=ptg.HorizontalAlignment.LEFT,),box="EMPTY_VERTICAL",width=60,
    )

    start_menu = (ptg.Window(header,"",width=60,box="DOUBLE",).set_title("[210 bold]Termify by Ben's Wangs").center())



    btn_login = ptg.Button("Log In", on_login, centered=True)
    # btn_create = ptg.Button("Create Account", on_create_account, centered=True)
    btn_quit = ptg.Button("Quit", lambda *_: manager.stop(), centered=True)

    # Make the clickable/visual padding consistent (helps “hitbox vs frame” feel)
    for b in (btn_login, btn_quit):
        b.chars["delimiter"] = [" ", " "]  # 1-space padding each side

    buttons = ptg.Splitter(btn_login, btn_quit)
    buttons.chars["separator"] = "   "       # spacing between buttons
    buttons.styles.separator = "@235 252"    # match background, no dark gaps

    start_menu.bind(ptg.keys.ESC, lambda *_ : manager.stop())
    start_menu.bind(ptg.keys.ENTER, on_login)

    start_menu += buttons
    return start_menu

    

with ptg.WindowManager() as manager:
    manager.add(build_start_menu(manager))
