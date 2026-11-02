"""Print the player's player configuration in a running match, the bytes every bot starts from (native/<game>.cpp add
bot: a copy of player 0's), 16 a row with UTF-16 text shown, to find where each game keeps the look (helmet, colours,
service tag) before probing single bytes with tools/look_probe.py. Read only. Saves logs/looks/<game>_player_<n>.bin.
Offsets are the ones botcore's look window uses (hb_apply_look): CE the network record (player +0x84), Halo 2 the
configuration built in native/h2.cpp (+0x18 = player +0xC0).

usage: python -I look_dump.py <ce|h2|h3|odst|reach|h4|h2a> [label]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
from brain.live import Live, LiveH2, LiveH3, LiveH4F, LiveODST, LiveReach, PLAYERS_PTR  # noqa: E402

H4F_DLL = {"h2a": "groundhog.dll", "h4": "halo4.dll"}      # as tools/play.py

# (TLS block pointer slot, offset of player 0's configuration from it, size): native/h3.cpp, odst.cpp, reach.cpp, h4f.cpp
SOURCE = {"h3": (0x48, 0x200, 0xB8), "odst": (0x40, 0x200, 0x98), "reach": (0x48, 0x2D8, 0xA0),
          "h4": (0x90, 0x358, 0x200), "h2a": (0x90, 0x358, 0x200)}


def live_for(game):
    """The brain/live.py reader for a game."""
    if game in H4F_DLL:
        return LiveH4F(H4F_DLL[game])
    return {"ce": Live, "h2": LiveH2, "h3": LiveH3, "odst": LiveODST, "reach": LiveReach}[game]()


def map_folder(game, live):
    """The running map's folder under maps/ (as tools/play.py names it: CE by its scenario, the rest <game>_<map>)."""
    if game == "ce":
        return live.tag_path(0).replace("/", "\\").rsplit("\\", 1)[-1]
    return f"{game}_{live.map_name()}"


def person_config(game, live=None):
    live = live or live_for(game)
    if game == "ce":                                  # native/botcore.cpp add_bot: the network record, player +0x84
        base, _, size = live._array(PLAYERS_PTR)
        return live.g.read(base + 0x84, 0x4C)
    if game == "h2":                                  # native/h2.cpp: cfg + 0x18 = player 0 + 0xC0 (0x84 bytes)
        base, _, size = live._array(live.PLAYERS)
        return bytes(0x18) + live.g.read(base + 0xC0, 0x84)
    slot, off, size = SOURCE[game]
    return live.g.read(live.g.u64(live._blk + slot) + off, size)


def show(b):
    for r in range(0, len(b), 16):
        row = b[r:r + 16]
        text = "".join(chr(row[k]) if 32 <= row[k] < 127 and row[k + 1:k + 2] == b"\0" else "." for k in range(0, len(row), 2))
        print(f"{r:03X}: {row.hex(' ')}  {text}")


if __name__ == "__main__":
    game = sys.argv[1]
    b = person_config(game)
    show(b)
    out = os.path.join(ROOT, "logs", "looks")
    os.makedirs(out, exist_ok=True)
    label = sys.argv[2] if len(sys.argv) > 2 else "now"
    open(os.path.join(out, f"{game}_player_{label}.bin"), "wb").write(b)
