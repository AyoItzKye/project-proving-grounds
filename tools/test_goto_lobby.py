"""The lobby walker's focus reading (tools/goto_lobby.py focused_row: MCC's menus by arrow keys, Enter only on the row seen
focused): on a made-up 1600x900 menu with the highlight bar down the left edge of row k (x 259-265, the row's height) it
reads k, for each of 7 rows; with no bar, or two equal bars, it reads None (no Enter on a guess); bright text on every
row is not a bar. And on_screen: each tools/menu_titles picture is read as its own screen and no other.

usage: python -I test_goto_lobby.py      -> "goto_lobby OK"
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goto_lobby  # noqa: E402


def menu(bars=(), text=True):
    img = Image.new("RGB", (1600, 900), (20, 30, 40))
    d = ImageDraw.Draw(img)
    for y in goto_lobby.ROWS:
        if text:
            d.rectangle((273, y - 9, 420, y + 9), fill=(120, 180, 230))       # a row's text
    for k in bars:
        y = goto_lobby.ROWS[k]
        d.rectangle((259, y - 20, 264, y + 20), fill=(170, 220, 255))        # the focus bar
    return img


def main():
    fails = []
    for k in range(7):
        got = goto_lobby.focused_row(7, menu([k]))
        if got != k:
            fails.append(f"bar on row {k + 1}: read row {None if got is None else got + 1}")
    for bars, why in (((), "no bar"), ((1, 4), "two bars")):
        got = goto_lobby.focused_row(7, menu(bars))
        if got is not None:
            fails.append(f"{why}: read row {got + 1} (want None: no Enter on a guess)")
    if goto_lobby.focused_row(4, menu([2])) != 2:
        fails.append("a 4-row menu, bar on row 3: not read")
    # each saved screen picture, put back where it was taken on a blank frame, is read as that screen and no other
    # (the lobbies and Built in pages share one title strip; the title screen goes by its gold logo)
    d = os.path.join(HERE, "menu_titles")
    names = [f[:-4] for f in os.listdir(d) if f.endswith(".png")]
    for name in names:
        frame = Image.new("RGB", (1600, 900), (10, 12, 16))
        frame.paste(Image.open(os.path.join(d, name + ".png")), goto_lobby.region_of(name)[:2])
        goto_lobby.screen = lambda: frame
        if not goto_lobby.on_screen(name, timeout=0.3, fatal=False):
            fails.append(f"{name}: its own picture not read as {name}")
        wrong = [n for n in names if n != name and goto_lobby.on_screen(n, timeout=0.1, fatal=False)]
        if wrong:
            fails.append(f"{name}: also read as {wrong}")
    # MCC's "Server Regions Invalid" notice coming up between the focus read and the Enter (on the main menu, its
    # focus on RESTORE DEFAULTS): the walker stops, no Enter sent (the player's rule: no region changes)
    def frame_of(names, bar=None):
        f = Image.new("RGB", (1600, 900), (10, 12, 16))
        for n in names:
            f.paste(Image.open(os.path.join(d, n + ".png")), goto_lobby.region_of(n)[:2])
        if bar is not None:
            y = goto_lobby.ROWS[bar]
            ImageDraw.Draw(f).rectangle((259, y - 20, 264, y + 20), fill=(170, 220, 255))
        return f
    seq = [frame_of(["main_menu"], bar=1)] * 2 + [frame_of(["region_notice"])] * 20
    shots = iter(seq)
    goto_lobby.screen = lambda: next(shots, seq[-1])
    pressed, real_keys, real_shot = [], goto_lobby.keys, goto_lobby.mcc_nav.shot
    goto_lobby.keys, goto_lobby.mcc_nav.shot = (lambda *k: pressed.extend(k)), (lambda: None)
    try:
        goto_lobby.go_keys("main_menu", 7, 1, "multiplayer")
        fails.append("the region notice came up before the Enter: the walker went on")
    except SystemExit as e:
        if "enter" in pressed or "Server Regions" not in str(e):
            fails.append(f"the region notice came up before the Enter: keys {pressed}, stop '{e}'")
    finally:
        goto_lobby.keys, goto_lobby.mcc_nav.shot = real_keys, real_shot
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"goto_lobby OK (the focus bar read on each of 7 rows; none when no bar or two; {len(names)} screen "
          "pictures each read as their own screen only)")


if __name__ == "__main__":
    main()
