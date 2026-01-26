# /main.py

#TestUI using pytermgui
import pytermgui as ptg
from pytermgui.file_loaders import YamlLoader
from pytermgui.enums import SizePolicy
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

# def build_music_player_menu(manager: ptg.WindowManager, username: str = "") -> ptg.Window:
#     repeat_state = {"on": False} #repeat is on no repeat is off
#     play_state = {"on": False} #play is on pause is off
#     music_player_menu = ptg.Window(width=50, box="DOUBLE").set_title("[210 bold]Termify").center()

#     music_player_menu += ptg.Label("[bold]SONGNAME[/]", parent_align=ptg.HorizontalAlignment.CENTER)#replace songname with actual song name
#     music_player_menu += ""
#     music_player_menu += ""
#     music_player_menu += ""
#     music_player_menu += ""
#     music_player_menu += ""#TODO insert some ascii stuff or sum

#     def toggle_repeat(*_):
#         manager.toast("Pressed repeat")
#         repeat_state["on"] = not repeat_state["on"]
#         btn_repeat.label = "Repeat: ON" if repeat_state["on"] else "Repeat: OFF"
#         #Plays this song on repeat

#     def on_play_song(*_):
#         play_state["on"] = not play_state["on"]
#         btn_play.label = "⏸" if play_state["on"] else "▶"
#         if play_state["on"]:
#             manager.toast("Playing SONGNAME")
#         else:
#             manager.toast("SONGNAME Paused")
#         #Play button, when pressed becomes pause button

#     def on_skip_song(*_):
#         manager.toast("Pressed skip")
#         #Skip to next in list

#     def on_prev_song(*_):
#         manager.toast("Pressed prev")
#         #Replay previous in list

#     def on_sign_out(*_):
#         manager.toast("Signing Out")
#         manager.remove(music_player_menu)
#         manager.add(build_start_menu(manager))
#     '''
#     def filler():
#         w = ptg.Label("")
#         w.size_policy = SizePolicy.FILL
#         return w   
#     '''
#     #row1
#     btn_repeat = ptg.Button("Repeat: OFF", toggle_repeat, parent_align=ptg.HorizontalAlignment.CENTER, centered=True)
#     music_player_menu += btn_repeat
#     music_player_menu += ""

#     #row2
#     gap_left1 = ptg.Label("")
#     #gap_left2 = ptg.Label(" ")
#     btn_prev = ptg.Button("⏮Prev", on_prev_song, centered=True)
#     btn_play = ptg.Button("▶", on_play_song, centered=True)
#     btn_next = ptg.Button("Skip⏭", on_skip_song, centered=True)
#     gap_right1 = ptg.Label("")
#     #gap_right2 = ptg.Label(" ")
#     row2 = ptg.Splitter(gap_left1, btn_prev, btn_play, btn_next, gap_right1)
#     row2.chars["separator"] = ""
#     row2.styles.separator = "@235 252"
#     music_player_menu += row2
#     music_player_menu += ""

#     #row3
#     btn_signout = ptg.Button("Sign Out", on_sign_out, parent_align=ptg.HorizontalAlignment.LEFT, centered=True)
#     btn_quit = ptg.Button("Quit", lambda *_: manager.stop(),parent_align=ptg.HorizontalAlignment.RIGHT, centered=True)
#     row3 = ptg.Splitter(btn_signout, btn_quit)
#     row3.chars["separator"] = ""
#     row3.styles.separator = "@235 252"
#     music_player_menu += row3
#     music_player_menu += ""
#     music_player_menu += ptg.Label("Use Arrow Keys To Toggle Repeat, Play")
#     music_player_menu += ptg.Label("Previous, Pause/Play, and Skip Ahead")

#     for b in (btn_repeat, btn_prev, btn_play, btn_next, btn_signout, btn_quit):
#         b.chars["delimiter"] = [" ", " "]

#     #Keybinds using arrows
#     music_player_menu.bind(ptg.keys.UP, lambda *_: toggle_repeat())
#     music_player_menu.bind(ptg.keys.LEFT,  lambda *_: on_prev_song())
#     music_player_menu.bind(ptg.keys.DOWN, lambda *_: on_play_song())
#     music_player_menu.bind(ptg.keys.RIGHT, lambda *_: on_skip_song())


#     return music_player_menu
def build_music_player_menu(manager: ptg.WindowManager, username: str = "") -> ptg.Window:
    play_state = {"on": False} # local variable we will use to see
    #1. Create a interactable search
    search_input = ptg.InputField("", prompt = "Search Song: ")
    music_player_menu = ptg.Window(width = 60, box = "DOUBLE").set_title("[210 bold]Termify").center() #just setting title, search bar using library

    music_player_menu += ptg.Label("[bold]Now Playing[/]", parent_align=ptg.HorizontalAlignment.CENTER) # start current playing song label

    song_label = ptg.Label("[dim]No song selected[/]", parent_align=ptg.HorizontalAlignment.CENTER)
    music_player_menu += song_label # add default song title to menu 
    music_player_menu += ""

    music_player_menu += search_input # add search to menu
    music_player_menu += ""

    def on_play_song(*_):
        play_state["on"] = not play_state["on"]

        btn_play.label = "⏸" if play_state["on"] else "▶" # update icon

        if play_state["on"]:
            query = search_input.value
            if query: 
                manager.toast(f"Search for {query}...")
                song_label.value = f"[bold]{query}[/]"

                # BACKEND CONNECTION
                player.play_song(query)
            else:
                manager.toast("Please enter a song name first!")
                play_state["on"] = False # reset for no input
                btn_play.label = "▶"
        else:
            manager.toast("Stopping playback")
            player.stop_song() # backend stop
    
    def on_sign_out(*_):
        player.stop_song()
        manager.toast("Signing Out")
        manager.remove(music_player_menu)
        manager.add(build_start_menu(manager))
    
    btn_prev = ptg.Button("⏮Prev", lambda *_: manager.toast("Prev"), centered=True)
    btn_play = ptg.Button("▶", on_play_song, centered=True)
    btn_next = ptg.Button("Skip⏭", lambda *_: manager.toast("Skip"), centered=True)

    # Row 2
    row2 = ptg.Splitter(ptg.Label(""), btn_prev, btn_play, btn_next, ptg.Label(""))
    row2.chars["seperator"] = ""
    music_player_menu += row2
    music_player_menu += ""

    # Row 3
    btn_signout = ptg.Button("Sign out", on_sign_out, centered=True)
    btn_quit = ptg.Button("Quit", lambda *_: manager.stop(), centered=True)
    row3 = ptg.Splitter(btn_signout, btn_quit)
    row3.chars["Separator"] = ""
    music_player_menu += row3

    # Keybinds
    music_player_menu.bind(ptg.keys.DOWN, lambda *_ : on_play_song())

    return music_player_menu




def build_start_menu(manager: ptg.WindowManager) -> ptg.Window:
    def on_login(*_):
        manager.toast("Log In Pressed")
        login_menu = build_login_menu(manager)
        manager.remove(start_menu)
        manager.add(login_menu)

    def on_create_account(*_):
        manager.toast("Create Account Pressed")
        create_account_menu = build_create_account_menu(manager)
        manager.remove(start_menu)
        manager.add(create_account_menu)

    header = ptg.Container(
        ptg.Label("[bold]A Terminal Based Music Player[/]",parent_align=ptg.HorizontalAlignment.LEFT,),
        ptg.Label("Made by:\nJordan Yang\nBen Wang\nMichael Ampong\nAshish Tomar\nFor the DEV.0 Hackathon",
        parent_align=ptg.HorizontalAlignment.LEFT,),box="EMPTY_VERTICAL",width=60,
    )

    start_menu = (ptg.Window(header,"",width=60,box="DOUBLE",).set_title("[210 bold]Termify by Ben's Wangs").center())



    btn_login = ptg.Button("Log In", on_login, centered=True)
    btn_create = ptg.Button("Create Account", on_create_account, centered=True)
    btn_quit = ptg.Button("Quit", lambda *_: manager.stop(), centered=True)

    # Make the clickable/visual padding consistent (helps “hitbox vs frame” feel)
    for b in (btn_login, btn_create, btn_quit):
        b.chars["delimiter"] = [" ", " "]  # 1-space padding each side

    buttons = ptg.Splitter(btn_login, btn_create, btn_quit)
    buttons.chars["separator"] = "   "       # spacing between buttons
    buttons.styles.separator = "@235 252"    # match background, no dark gaps

    start_menu += buttons
    return start_menu

def build_create_account_menu(manager: ptg.WindowManager) -> ptg.Window:
    username = ptg.InputField("", prompt="Username: ")
    password = ptg.InputField("", prompt="Password: ")

    create_account_menu = ptg.Window(width=50, box="DOUBLE").set_title("[210 bold]Termify").center()

    def go_back(*_):
        manager.toast("Back Pressed")
        manager.remove(create_account_menu)
        manager.add(build_start_menu(manager))  # rebuild start cleanly

    def do_create_account(*_):
        manager.toast(f"Account Created as {username.value}")
        manager.remove(create_account_menu)
        manager.add(build_music_player_menu(manager))

    #button name, function called when pressed, center text in button frame
    btn_back = ptg.Button("Back", go_back, centered=True)
    btn_submit = ptg.Button("Submit", do_create_account, centered=True)

    #assign spaces on either side of button text to make button look nice
    for b in (btn_back, btn_submit):
        b.chars["delimiter"] = [" ", " "]

    #splitter function
    actions = ptg.Splitter(btn_back, btn_submit)
    actions.chars["separator"] = "     "
    actions.styles.separator = "@235 252"

    create_account_menu += ptg.Label("[bold] A Valid Username And Password[/]", parent_align=ptg.HorizontalAlignment.LEFT)
    create_account_menu += ""
    create_account_menu += username
    create_account_menu += password
    create_account_menu += ""
    create_account_menu += actions

    return create_account_menu


def build_login_menu(manager: ptg.WindowManager) -> ptg.Window:
    username = ptg.InputField("", prompt="Username: ")
    password = ptg.InputField("", prompt="Password: ")

    login_menu = ptg.Window(width=50, box="DOUBLE").set_title("[210 bold]Termify").center()

    def go_back(*_):
        manager.toast("Back Pressed")
        manager.remove(login_menu)
        manager.add(build_start_menu(manager))  # rebuild start cleanly

    def do_login(*_):
        manager.toast(f"Logging In As {username.value}")
        manager.remove(login_menu)
        manager.add(build_music_player_menu(manager))

    #button name, function called when pressed, center text in button frame
    btn_back = ptg.Button("Back", go_back, centered=True)
    btn_submit = ptg.Button("Submit", do_login, centered=True)

    #assign spaces on either side of button text to make button look nice
    for b in (btn_back, btn_submit):
        b.chars["delimiter"] = [" ", " "]

    #splitter function
    actions = ptg.Splitter(btn_back, btn_submit)
    actions.chars["separator"] = "     "
    actions.styles.separator = "@235 252"

    login_menu += ptg.Label("[bold]Log In[/]", parent_align=ptg.HorizontalAlignment.LEFT)
    login_menu += ""
    login_menu += username
    login_menu += password
    login_menu += ""
    login_menu += actions

    return login_menu


with ptg.WindowManager() as manager:
    manager.add(build_start_menu(manager))
