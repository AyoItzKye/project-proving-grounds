"""Live test: walk a bot to a player with the brain's terrain paths, then shoot when in sight.

usage: python -I live_walk.py <bot slot> <bot player index> <target player index | x,y> [seconds] [--no-fire]
Prints progress; ends when the target's shield drops (hit), on arrival at x,y, on timeout, or when the bot dies.
"""
import math
import os
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brain.core import Vec  # noqa: E402
from brain.maps import BLOODGULCH  # noqa: E402
from brain.terrain import Terrain  # noqa: E402
from brain.live import Live  # noqa: E402
import botctl  # noqa: E402

EYE = 0.6          # standing eye height above the biped origin
FIRE_RANGE = 25.0


def main():
    slot, me_i = map(int, sys.argv[1:3])
    point = tuple(map(float, sys.argv[3].split(","))) if "," in sys.argv[3] else None
    tgt_i = None if point else int(sys.argv[3])
    secs = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else 60
    fire_ok = "--no-fire" not in sys.argv
    T = Terrain(BLOODGULCH["heightmap"], BLOODGULCH["bases"])
    live, m = Live(), botctl.shm()
    t0, last_print, yaw, pitch = time.time(), 0, 0.0, 0.0
    shield0 = None
    try:
        while time.time() - t0 < secs:
            ps = {d["index"]: d for d in live.players()}
            me = ps[me_i]
            tgt = ps[tgt_i] if point is None else dict(pos=(point[0], point[1], T.nav_z(*point)), shield=1.0, health=1.0)
            if not me["pos"] or not tgt["pos"]:
                print("dead:", "bot" if not me["pos"] else "target"); break
            if shield0 is None:
                shield0 = tgt["shield"]
            a, b = Vec(*me["pos"]), Vec(*tgt["pos"])
            d = math.dist(me["pos"][:2], tgt["pos"][:2])
            seen = T.los(Vec(a.x, a.y, a.z + EYE), Vec(b.x, b.y, b.z + EYE))
            buttons, fwd = 0, 1.0
            if point and d < 0.6:
                print(f"ARRIVED at ({a.x:.2f},{a.y:.2f},{a.z:.2f}) after {time.time() - t0:.1f}s"); break
            if seen and d < FIRE_RANGE and not point:
                yaw = math.atan2(b.y - a.y, b.x - a.x)
                pitch = math.atan2(b.z - a.z, d)
                fwd, buttons = 0.0, botctl.BTN["fire"] if fire_ok else 0
            else:
                w = T.nav(a, b)
                yaw, pitch = math.atan2(w.y - a.y, w.x - a.x), 0.0
            botctl.act(m, slot, fwd, 0.0, yaw, pitch, buttons)
            if time.time() - last_print > 1.0:
                last_print = time.time()
                print(f"{time.time() - t0:5.1f}s bot ({a.x:.1f},{a.y:.1f},{a.z:.1f}) dist {d:5.1f} "
                      f"seen {seen} fire {bool(buttons)} target shield {tgt['shield']:.2f} health {tgt['health']:.2f}",
                      flush=True)
            if tgt["shield"] < shield0 - 0.01 or tgt["health"] < 1.0:
                print(f"HIT: target shield {shield0:.2f} -> {tgt['shield']:.2f}, health {tgt['health']:.2f}"); break
            time.sleep(0.05)
    finally:
        botctl.act(m, slot, 0.0, 0.0, yaw, pitch, 0)


if __name__ == "__main__":
    main()
