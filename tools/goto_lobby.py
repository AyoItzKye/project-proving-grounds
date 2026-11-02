"""From one of MCC's menus (main menu, Multiplayer, Custom Multiplayer) to a game's custom game lobby (verified routes; by
arrow keys since), optionally start the match with the lobby's current settings; screenshot to logs/nav_now.jpg. Enter
only on a row seen focused (its highlight bar), and on the title screen after --restart.

usage: python -I goto_lobby.py <ce|h2|h2a|h3|h4|reach|odst-ff> [--restart] [--start]
  --restart  kill MCC and start it with launch.py first (loads the newest botcore)
  --start    START tile, then START; waits until the game runs
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcc_nav  # noqa: E402
from memread import Game  # noqa: E402

TITLE_ROW = {"reach": 0, "ce": 1, "h2": 2, "h2a": 3, "h3": 4, "h4": 5}   # Custom Multiplayer list
BUILT_IN_STEP = {"ce", "h3"}           # these ask Built in / Modded maps first (H2 no longer does)


def keys(*names):
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "key", *names], capture_output=True)


def on_screen(name, timeout=40.0, fatal=True):
    """Wait until the menu title region (nav_now.jpg coordinates 260..760 x 20..85) matches
    tools/menu_titles/<name>.png better than any other template; exit if it never does."""
    import numpy as np
    from PIL import Image
    d = os.path.join(HERE, "menu_titles")
    def text(im, k):                     # the menus' white and light-blue text; not the video's warm light streaks
        a = np.asarray(im.convert("RGB")).astype(int)      # (a brightness cut alone took streaks and dropped letters:
        if k == "title":                                   # the same menu scored 0.38 apart); the title screen
            return (a[..., 0] > 150) & (a[..., 0] > a[..., 2] + 60)   # by its gold HALO logo: its PRESS [Enter] line
        return (a[..., 2] > 150) & (a[..., 2] >= a[..., 0])  # pulses, 162 down to under 90
    t = {f[:-4]: text(Image.open(os.path.join(d, f)), f[:-4]) for f in os.listdir(d) if f.endswith(".png")}
    end = time.time() + timeout
    while time.time() < end:
        shot = screen()
        diff = {}
        for k, v in t.items():               # each template in its own region: of the text pixels in either, the
            now = text(shot.crop(region_of(k)), k)   # share that differ (text is a few % of the area: a plain pixel
            if v.shape == now.shape:              # share put the main menu 0.006 from the multiplayer menu)
                diff[k] = float((now ^ v).sum()) / max(float((now | v).sum()), 1.0)
        if diff and min(diff, key=diff.get) == name and diff[name] < MATCH:
            time.sleep(0.8)                                # let the list finish animating in
            return True
        time.sleep(0.5)
    if not fatal:
        return False
    mcc_nav.shot()
    sys.exit(f"not on the {name} screen (see logs/nav_now.jpg); stopped before clicking")


# what a screen is recognised by: the title AND the left menu column (1600x900 view). The title strip alone (260..760
# x 20..85, before) was blank on the main menu, so the main menu's template "matched" any screen with little text
# there: on the Multiplayer screen it clicked the second row, COMPETITIVE GAMES (online; MCC refused, anti-cheat off).
# Templates re-made with --capture on each screen.
TITLE = (40, 20, 760, 100)            # the screen's title (two lines: "MAIN MENU / MULTIPLAYER")
MENU = (40, 220, 440, 620)            # the left menu column (its text only: the video's lights are further right): the
                                      # main menu has no title text
REGIONS = {"main_menu": MENU, "multiplayer": MENU, "custom_multiplayer": MENU,
           "title": (560, 380, 1040, 570),     # (the title screen: the logo and PRESS [Enter] TO START)
           "region_notice": (625, 335, 975, 505)}   # (MCC's "Server Regions Invalid" notice: its title and text)
MATCH = 0.3


def region_of(name):
    return REGIONS.get(name, TITLE)


def stop_if_notice():
    """MCC's matchmaking notice "Server Regions Invalid" (CHANGE REGIONS / RESTORE DEFAULTS, the focus on either): the
    player's rule is no region changes, so nothing is pressed while it is up (it came up on the main menu after a
    back-navigation and right after a launch; an Enter there presses its focused button)."""
    if on_screen("region_notice", timeout=0.3, fatal=False):
        mcc_nav.shot()
        sys.exit("MCC's 'Server Regions Invalid' notice is up (logs/nav_now.jpg): nothing pressed, the server regions "
                 "are the player's to set")


def screen():
    img = mcc_nav.grab()                                   # MCC's window, on whichever monitor
    img.thumbnail((1600, 900))
    return img


def capture(name):
    """Save the screen on now as tools/menu_titles/<name>.png (the region on_screen compares for that name)."""
    screen().crop(region_of(name)).save(os.path.join(HERE, "menu_titles", name + ".png"))


ROWS = [234 + 55 * k for k in range(7)]   # a menu's rows, y in the 1600x900 view (its text from x 273)


def focused_row(n, img=None):
    """Which of a menu's first n rows has the focus: the one with the highlight bar down its left edge (x 259-265, a
    bright line the height of the row; the others have none), or None when no row stands out."""
    import numpy as np
    a = np.asarray((img or screen()).convert("RGB")).astype(float)
    # the bar against the strip just left of it, and blue (the menu video behind can be bright: a warm highlight beside
    # row 3 read 27 to the focused bar's 73 there); caught mid-animation no row stands out: None, read again
    score = []
    for y in ROWS[:n]:
        bar, left = a[y - 14:y + 14, 259:266], a[y - 14:y + 14, 250:256]
        blue = (bar[..., 2] - bar[..., 0]).mean() > 12.0
        score.append(bar.mean() - left.mean() if blue else 0.0)
    k = int(np.argmax(score))
    rest = sorted(score)[-2] if n > 1 else 0.0
    return k if score[k] > 30.0 and score[k] > rest + 20.0 else None


def go_keys(here, n, target, there):
    """On screen `here` (checked), the focus moved to row `target` of its n by arrow keys, seen there, then Enter, until
    screen `there` shows. Enter only on the row seen focused: never on what MCC happened to leave focused (an Enter off
    a known menu started Reach's campaign; SOCIAL GAMES, Multiplayer's first row, is online)."""
    on_screen(here)
    for _ in range(4):
        k = focused_row(n)
        if k is None:
            time.sleep(1.0)
            continue
        if k != target:
            keys(*(["down"] * (target - k) if target > k else ["up"] * (k - target)))
            time.sleep(0.8)
            continue
        stop_if_notice()                                   # (it can come up between the read and the press)
        keys("enter")
        if there is not None and on_screen(there, timeout=10, fatal=False):
            return
        if there is None and not on_screen(here, timeout=6, fatal=False):
            return                                         # (no picture of the next screen yet: this one gone is enough)
        on_screen(here)                                    # still here: the row is checked again before the next Enter
    mcc_nav.shot()
    sys.exit(f"on {here}: the focus never got to row {target + 1} (see logs/nav_now.jpg); no Enter pressed there")


def wake(timeout=150.0):
    """After a launch: MCC's window to monitor 2 (the test recipe; it goes back to the main monitor after the title
    screen), Enter on the title screen only ("PRESS [Enter] TO START", its template), until the main menu shows."""
    end = time.time() + timeout
    while time.time() < end:
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "move", "2"], capture_output=True)
        stop_if_notice()                                   # (no 150 s wait behind it either)
        if on_screen("main_menu", timeout=3, fatal=False):
            return
        if on_screen("title", timeout=2, fatal=False):
            stop_if_notice()
            keys("enter")
        time.sleep(4)
    mcc_nav.shot()
    sys.exit("MCC never showed its main menu (see logs/nav_now.jpg)")


def in_game():
    try:
        g = Game("MCC-Win64-Shipping.exe")
        return g.read(g.base + 0x4000B8C + 0x11, 1)[0] == 1
    except SystemExit:
        return False


def walk(title):
    """By arrow keys since (MCC's newer menus moved every click spot, and with MCC on monitor 2 a click only pressed
    whatever was focused: END GAME clicked opened LEAVE), never before the expected screen is up, each Enter on a row
    seen focused (go_keys). Each screen is recognised by tools/menu_titles/*.png (re-made)."""
    if not any(on_screen(n, timeout=t, fatal=False) for n, t in (("main_menu", 4), ("multiplayer", 1),
                                                                 ("custom_multiplayer", 1))):
        mcc_nav.shot()
        sys.exit("not on a known menu (see logs/nav_now.jpg): get to the main menu first")
    if not on_screen("custom_multiplayer", timeout=3, fatal=False):   # from whichever menu is up
        if not on_screen("multiplayer", timeout=3, fatal=False):
            go_keys("main_menu", 7, 1, "multiplayer")      # MULTIPLAYER (2nd of 7)
        go_keys("multiplayer", 4, 2, "custom_multiplayer")  # CUSTOM MULTIPLAYER (3rd; the 4th is the online browser)
    lobby = title + "_lobby"
    go_keys("custom_multiplayer", 6, TITLE_ROW[title], title + "_builtin" if title in BUILT_IN_STEP else lobby)
    if title in BUILT_IN_STEP:
        go_keys(title + "_builtin", 2, 0, lobby)          # BUILT IN MAPS
    on_screen(lobby, timeout=20)


def main():
    title = sys.argv[1]
    if title == "--capture":           # goto_lobby.py --capture <screen name>: re-make a template (by sight first)
        capture(sys.argv[2])
        return
    if "--restart" in sys.argv:
        subprocess.run(["taskkill", "/F", "/IM", "MCC-Win64-Shipping.exe"], capture_output=True)
        time.sleep(12)                    # Steam needs a moment, or it says "already running"
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "launch.py")])
        wake()
    if title == "odst-ff":
        sys.exit("odst-ff: not mapped on the new menus yet (Firefight's 2nd row is MATCHMAKING, online)")
    if not on_screen(title + "_lobby", timeout=2, fatal=False):     # (already in it: nothing to walk)
        walk(title)
    if "--start" in sys.argv:
        keys("up", "up", *["left"] * 4, *["right"] * 3)   # the top row's START tile (4th: map, game type, options)
        for _ in range(3):                                # Enter starts the countdown (now and then a second one)
            stop_if_notice()
            keys("enter")
            t0 = time.time()
            while time.time() - t0 < 60 and not in_game():
                time.sleep(3)
            if in_game():
                break
        time.sleep(10)
    mcc_nav.shot()


if __name__ == "__main__":
    main()
