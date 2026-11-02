"""Offline check of the decoded-button path: maps/_inputs/<game>.json -> live_bots.decoded_buttons ->
botctl.set_button_map writes entries the way native/shared.h hb_btn_entry lays them out, and the
apply rule (clear, then set while held / on the press tick) as hb_apply_buttons does it.

usage: python -I test_buttons.py      -> "buttons OK"
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
import live_bots  # noqa: E402
from brain.core import Action  # noqa: E402


def apply(entries, game, act, now, prev):
    """hb_apply_buttons in Python (native/shared.h)."""
    for btn, off, press, g, mask in entries:
        if not btn or g != game or off + 8 > len(act):
            continue
        w = struct.unpack_from("<Q", act, off)[0] & ~mask
        if now & btn and not (press and prev & btn):
            w |= mask
        struct.pack_into("<Q", act, off, w)


def main():
    fails = []
    rows = live_bots.decoded_buttons("h3")
    if ("h3", "equipment", 8, 16, True) not in rows:
        fails.append(f"Halo 3's statically decoded equipment bit not loaded: {rows}")
    for want in (("h3", "reload", 0x28, 0x100000000, False), ("h3", "reload", 0x40, 0x3000, False)):
        if want not in rows:                       # decoded live (reload=r), checked by tools/reload_probe.py h3
            fails.append(f"Halo 3's decoded reload entry {want} not loaded: {rows}")
    if live_bots.decoded_buttons("ce") != []:
        fails.append("a game with no decode file got buttons")
    # the table's layout on a known input (the file's own rows grow as buttons are decoded)
    m = bytearray(botctl.SIZE)
    rows = [r for r in rows if r[1] == "equipment"]
    botctl.set_button_map(m, rows + [("reach", "melee", 0x40, 0x80, False)])
    got = [struct.unpack_from("<IHBBQ", m, botctl.OFF_BTN_MAP + 4 + 16 * k) for k in range(botctl.BTN_MAP_N)]
    if got[0] != (botctl.BTN["equipment"], 8, 1, botctl.GAME_ID["h3"], 16) or got[1][0] != botctl.BTN["melee"]:
        fails.append(f"button table layout {got[:2]}")
    if any(e[0] for e in got[2:]):
        fails.append("unused entries not cleared")
    if struct.unpack_from("<I", m, botctl.OFF_BTN_MAP)[0] != 1:
        fails.append("button table seq not bumped")
    # the apply rule: a press-only bit on the first tick, not while held; the player's bit in
    # the template is cleared for a bot that does not press
    entries = [e for e in got if e[0]]
    act = bytearray(0x88)
    struct.pack_into("<Q", act, 8, 0x10 | 0x2)          # template: the player pressing equipment + jump
    apply(entries, 3, act, 0, 0)
    if struct.unpack_from("<Q", act, 8)[0] != 0x2:
        fails.append("the player's equipment bit leaked into a bot's action")
    a = Action(equipment=True)
    b = live_bots.buttons(a)
    apply(entries, 3, act, b, 0)
    first = struct.unpack_from("<Q", act, 8)[0] & 0x10
    apply(entries, 3, act, b, b)
    held = struct.unpack_from("<Q", act, 8)[0] & 0x10
    if not first or held:
        fails.append(f"press-only equipment: first tick {first:#x}, held {held:#x}")
    if live_bots.buttons(Action(sprint=True)) != botctl.BTN["sprint"]:
        fails.append("sprint bit")
    # the scope level: the brain packs Action.zoom where native/shared.h reads it (HB_ZOOM_SHIFT), clear of every
    # button bit and the weapon slot
    import re
    with open(os.path.join(HERE, "..", "native", "shared.h"), encoding="utf-8") as f:
        header = f.read()
    shift = re.search(r"HB_ZOOM_SHIFT\s*=\s*(\d+)", header)
    if not shift:
        fails.append("native/shared.h has no HB_ZOOM_SHIFT: botcore never reads the zoom bits")
    else:
        k = int(shift.group(1))
        for z in (0, 1, 2):
            w = live_bots.buttons(Action(zoom=z, fire=True, weapon=1))
            if (w >> k) & 3 != z or w & ~(3 << k) != live_bots.buttons(Action(fire=True, weapon=1)):
                fails.append(f"zoom {z}: buttons {w:#x} (shift {k})")
        if (3 << k) & (sum(botctl.BTN.values()) | (7 << 8)):
            fails.append("the zoom bits overlap a button or the weapon slot")
    # a hovering aircraft's vertical input: Action.vertical -> the 2-bit level botcore turns into Reach's +0x3C
    # (shared.h HB_VERT_SHIFT, hb_vertical: 1 up +1, 2 down -1, 3 hold +0.5)
    vs = re.search(r"HB_VERT_SHIFT\s*=\s*(\d+)", header)
    if not vs:
        fails.append("native/shared.h has no HB_VERT_SHIFT")
    else:
        k = int(vs.group(1))
        for v, level in ((0.0, 0), (1.0, 1), (-1.0, 2), (0.5, 3)):
            w = live_bots.buttons(Action(vertical=v, seat=2))
            if (w >> k) & 3 != level or w & ~(3 << k) != live_bots.buttons(Action(seat=2)):
                fails.append(f"vertical {v}: buttons {w:#x} (want level {level} at bit {k})")
        if (3 << k) & (sum(botctl.BTN.values()) | (7 << 8) | (3 << 12) | (15 << 14) | (1 << 18)):
            fails.append("the vertical bits overlap a button, the weapon, zoom or seat bits")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("buttons OK")


if __name__ == "__main__":
    main()
