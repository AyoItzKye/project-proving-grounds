"""Live check of the bots' scope (botcore s69+, native/shared.h hb_set_zoom): for every bot, the level the brain
asks (its shared-memory action, buttons bits 12-13) next to its unit's desired zoom byte, read from the game
(CE unit +0x301: ghidra/ce_uc.c line 65; Halo 3 unit +0x299: ghidra/h3_input.c line 28; Halo 2 unit +0x255:
found live with --scan, +0x254 next to it follows too, as Halo 3's +0x298; 0xFF = none).

usage: python -I zoom_probe.py <ce|h2|h3> [seconds] [--drive] [--scan]     (a match with bots running)
prints (asked level, unit byte) pairs with counts; asked 0/1/2 should read 0xFF/0/1
--drive: with no brain running (play.py done), this script asks levels 0, 1, 2 in turn (2 s each) for every bot
itself, standing still: checks botcore's path into the unit whatever the bots hold (the unit control writes the
byte every tick, scope or not)
--scan (with --drive): which unit bytes follow the level asked (0xFF / 0 / 1 in 98%+ of samples): finds the field
in a game where it is not decoded (Halo 2)
"""
import collections
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
from ammo_scan import release  # noqa: E402
from brain.live import Live, LiveH2, LiveH3  # noqa: E402

UNIT_ZOOM = {"ce": 0x301, "h2": 0x255, "h3": 0x299}   # h2: found by --scan live (+0x254/+0x255 follow)


def main():
    game = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    live = {"ce": Live, "h2": LiveH2, "h3": LiveH3}[game]()
    scan, seen, total = "--scan" in sys.argv, collections.Counter(), 0
    m = botctl.shm()
    drive = "--drive" in sys.argv
    pairs = collections.Counter()
    t0 = time.time()
    try:
        while time.time() - t0 < seconds:
            units = {p["index"]: p["unit"] for p in live.players() if p.get("pos") is not None}
            level = int((time.time() - t0) / 2.0) % 3
            for slot, index in botctl.status(m)["bots"].items():
                if index not in units:
                    continue
                o = live.object(units[index])
                if not o:
                    continue
                if drive:
                    yaw = struct.unpack_from("<f", m, botctl.OFF_ACTIONS + slot * 24 + 8)[0]
                    botctl.act(m, slot, 0.0, 0.0, yaw, 0.0, level << 12)
                    if (time.time() - t0) % 2.0 < 0.3:
                        continue                # the first ticks of a new level: the game has not taken it yet
                asked = (struct.unpack_from("<I", m, botctl.OFF_ACTIONS + slot * 24 + 16)[0] >> 12) & 3
                if scan:
                    want, buf = (0xFF, 0, 1)[asked], live.g.read(o, 0x800)
                    seen.update(k for k in range(len(buf)) if buf[k] == want)
                    total += 1
                    continue
                pairs[(asked, live.g.read(o + UNIT_ZOOM[game], 1)[0])] += 1
            time.sleep(1 / 30 if drive else 0.1)
    finally:
        if drive:
            release(m)                          # no zoom left asked, whatever stopped the loop (botcore has no watchdog)
    if scan:
        print(f"{total} samples; unit offsets that followed the level:", [hex(k) for k, n in sorted(seen.items()) if n >= 0.98 * total])
    for (asked, got), n in sorted(pairs.items()):
        print(f"asked {asked} -> unit byte {got:#04x}: {n} samples")


if __name__ == "__main__":
    main()
