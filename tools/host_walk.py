"""Walk the host's own player (the player's seat in a test match) to open ground and face the open side, so probe bots
can line up in front of the camera in good light. Real keyboard and mouse input to MCC's window (W, mouse turn),
steered by the live position on the map's nav grid. Test matches only.

usage: python -I host_walk.py [--game h3|odst|reach|h4|h2a] [--near X,Y]   (open ground nearest the player or X,Y)
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from input_replay import INPUT, INPUT_MOUSE, MI, U, key, send  # noqa: E402
from look_dump import live_for, map_folder  # noqa: E402
import mcc_nav  # noqa: E402

W_SCAN = 0x11                     # W (scan code, set 1)


def me(live):
    p = live.players()[0]
    return Vec(*p["pos"]), math.atan2(p["aim"][1], p["aim"][0])


def mouse_dx(dx, dy=0):
    steps = max(1, max(abs(int(dx)), abs(int(dy))) // 15)
    for _ in range(steps):
        send(INPUT(INPUT_MOUSE, U(mi=MI(int(dx / steps), int(dy / steps), 0, 0x0001, 0, 0))))
        time.sleep(0.01)


def pitch(live):
    a = live.players()[0]["aim"]
    return math.atan2(a[2], math.hypot(a[0], a[1]))


def calibrate_pitch(live):
    """Mouse counts per radian of pitch (sign included), from a small test nod."""
    p0 = pitch(live)
    mouse_dx(0, 120)
    time.sleep(0.3)
    d = pitch(live) - p0
    if abs(d) < 0.01:
        sys.exit("the view did not nod")
    return 120 / d


def look_at(live, yaw, pit, k, kp):
    """Turn to yaw and pitch (radians) with real mouse moves."""
    for _ in range(5):
        _, y = me(live)
        dy_ = wrap(yaw - y)
        dp = pit - pitch(live)
        if abs(dy_) < 0.03 and abs(dp) < 0.03:
            return True
        mouse_dx(dy_ * k, dp * kp)
        time.sleep(0.25)
    return False


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def calibrate(live):
    """Mouse counts per radian of yaw (sign included), from a test turn."""
    _, y0 = me(live)
    mouse_dx(300)
    time.sleep(0.3)
    _, y1 = me(live)
    d = wrap(y1 - y0)
    if abs(d) < 0.02:
        sys.exit("the view did not turn: MCC not focused, or the player is dead")
    return 300 / d


def face(live, yaw, k):
    for _ in range(4):
        _, y = me(live)
        d = wrap(yaw - y)
        if abs(d) < 0.04:
            return True
        mouse_dx(d * k)
        time.sleep(0.25)
    return False


def open_ground(T, live, near, rmax=14.0):
    """(spot, facing yaw): the walkable spot nearest `near` with a clear 6 x 3.5 unit field in front of it (rows of
    probe bots at 1.1 to 3.4 units out, 2.8 to each side), in sight from the spot (no walls)."""
    for r in [x * 0.5 for x in range(0, int(rmax * 2))]:
        for a in range(0, 360, 15 if r else 360):
            c = near + Vec(math.cos(math.radians(a)), math.sin(math.radians(a)), 0) * r
            if not T.walkable(c):
                continue
            c = Vec(c.x, c.y, T.nav_z(c.x, c.y))
            for yd in range(0, 360, 30):
                y = math.radians(yd)
                f, s = Vec(math.cos(y), math.sin(y), 0), Vec(-math.sin(y), math.cos(y), 0)
                field = [c + f * u + s * v for u in (1.1, 2.2, 3.4) for v in (-2.8, -1.4, 0, 1.4, 2.8)]
                if all(T.walkable(p) for p in field) and all(T.los(c + Vec(0, 0, 0.6), Vec(p.x, p.y, c.z + 0.6)) for p in field):
                    return c, y
    return None


def goto(live, T, goal, k, seconds=45.0):
    t0 = time.time()
    while time.time() - t0 < seconds:
        pos, _ = me(live)
        if (pos - goal).flat() < 0.4:
            return True
        w = T.nav(pos, goal)
        face(live, math.atan2(w.y - pos.y, w.x - pos.x), k)
        key({"scan": W_SCAN, "extended": False, "down": True})
        time.sleep(0.3 if (pos - goal).flat() > 1.5 else 0.12)
        key({"scan": W_SCAN, "extended": False, "down": False})
    return False


def main():
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "h3"
    live = live_for(game)
    T = terrain(get_map(map_folder(game, live)))
    pos, _ = me(live)
    near = Vec(*map(float, sys.argv[sys.argv.index("--near") + 1].split(",")), pos.z) if "--near" in sys.argv else pos
    found = open_ground(T, live, near)
    if not found:
        sys.exit("no open ground found near " + str((round(near.x, 1), round(near.y, 1))))
    spot, yaw = found
    h = mcc_nav.mcc_window()
    if not h or not mcc_nav.focus(h):
        sys.exit("MCC window not found or not focused")
    k = calibrate(live)
    ok = goto(live, T, spot, k)
    face(live, yaw, k)
    pos, y = me(live)
    print(f"{'at' if ok else 'stopped short of'} open ground ({spot.x:.1f}, {spot.y:.1f}); player ({pos.x:.1f}, {pos.y:.1f}) "
          f"facing {math.degrees(y):.0f} deg (wanted {math.degrees(yaw):.0f}); {k:.0f} mouse counts per radian")
    mcc_nav.shot()


if __name__ == "__main__":
    main()
