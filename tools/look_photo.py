"""Close-ups for tools/look_probe.py: each probe bot in turn walks to a spot 1.6 units in front of the player's player
(under its crosshair, so the name tag shows), faces it, and is photographed; then it steps aside for the next. Saves
logs/looks/<label>_<bot name>.png (the middle of the screen, full size). Reach, Halo 3, ODST, Halo 4, H2A.

usage: python -I look_photo.py <label> [--game G]
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import botctl  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from look_dump import live_for, map_folder  # noqa: E402


def walk(m, live, T, slot, index, goal, face_to, seconds=12.0):
    """Drive one bot to goal, then face face_to; True when it got there."""
    t0 = time.time()
    while time.time() - t0 < seconds:
        p = next((q for q in live.players() if q["index"] == index), None)
        if not p or not p.get("pos"):
            return False
        pos = Vec(*p["pos"])
        if (pos - goal).flat() < 0.25:
            botctl.act(m, slot, 0.0, 0.0, math.atan2(face_to.y - pos.y, face_to.x - pos.x), 0.0)
            return True
        w = T.nav(pos, goal)
        d = (pos - goal).flat()
        botctl.act(m, slot, 1.0 if d > 1.0 else 0.35, 0.0, math.atan2(w.y - pos.y, w.x - pos.x), 0.0)
        time.sleep(1 / 30)
    return False


def main():
    label = sys.argv[1]
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "reach"
    import mcc_nav
    m = botctl.shm()
    live = live_for(game)
    T = terrain(get_map(map_folder(game, live)))
    me = live.players()[0]
    origin, look = Vec(*me["pos"]), Vec(*me["aim"])
    yaw0 = math.atan2(look.y, look.x)
    fwd, side = Vec(math.cos(yaw0), math.sin(yaw0), 0), Vec(-math.sin(yaw0), math.cos(yaw0), 0)
    # in front of look_probe's rows (1.8 and 3.0 units out), so the way there and back is clear (parked behind
    # the camera, the others found the way blocked)
    photo = origin + fwd * 1.1
    out = os.path.join(ROOT, "logs", "looks")
    os.makedirs(out, exist_ok=True)
    slots = sorted(botctl.status(m)["bots"].items())
    if "--aim" in sys.argv:           # no walking: turn the host's view onto each bot where it stands (its name tag
        import host_walk              # shows under the crosshair) and cut the middle of the screen
        h = mcc_nav.mcc_window()
        if not h or not mcc_nav.focus(h):
            sys.exit("MCC window not found or not focused")
        zoom = "--zoom" in sys.argv   # the pistol's scope (right mouse button): bots twice as big, turning slower
        if zoom:
            from input_replay import mouse
            l, t, r, b = mcc_nav.mcc_rect()
            mouse({"action": "right_down", "x": (l + r) // 2, "y": (t + b) // 2})
            time.sleep(0.05)
            mouse({"action": "right_up", "x": (l + r) // 2, "y": (t + b) // 2})
            time.sleep(0.6)
        k, kp = host_walk.calibrate(live), host_walk.calibrate_pitch(live)
        eye = origin.z + float(os.environ.get("EYE", "0.62"))   # the host's camera (a Spartan's eyes, units)
        for slot, index in slots:
            p = next((q for q in live.players() if q["index"] == index), None)
            if not p or not p.get("pos"):
                continue
            pos = Vec(*p["pos"])
            mid = pos.z + float(os.environ.get("MID", "0.33"))   # the middle of the bot, head to feet
            dist = max(0.3, (pos - origin).flat())
            host_walk.look_at(live, math.atan2(pos.y - origin.y, pos.x - origin.x), math.atan2(mid - eye, dist), k, kp)
            time.sleep(0.5)
            img = mcc_nav.grab()
            w, hh = img.size
            name = p["name"].replace("+", "p").replace(" ", "_")
            img.crop((w // 2 - 300, hh // 2 - 380, w // 2 + 300, hh // 2 + 320)).save(os.path.join(out, f"{label}_{name}.png"))
            print("photographed", p["name"], flush=True)
        host_walk.look_at(live, yaw0, 0.0, k, kp)
        if zoom:
            mouse({"action": "right_down", "x": (l + r) // 2, "y": (t + b) // 2})
            time.sleep(0.05)
            mouse({"action": "right_up", "x": (l + r) // 2, "y": (t + b) // 2})
        return
    for n, (slot, index) in enumerate(slots):
        p = next((q for q in live.players() if q["index"] == index), None)
        if not p:
            continue
        # done: far out to the sides, past look_probe's rows (walked back home, one stayed in the next shots)
        away = origin + fwd * (2.5 + 0.5 * (n // 2)) + side * (((n % 2) * 2 - 1) * (4.0 + 0.4 * (n // 2)))
        if not walk(m, live, T, slot, index, photo, origin, seconds=float(os.environ.get("WALK_S", "20"))):
            print(p["name"], "did not get to the spot")
            walk(m, live, T, slot, index, away, origin, seconds=8.0)
            continue
        time.sleep(0.8)
        crowd = [q["name"] for q in live.players() if q["index"] not in (index, me["index"]) and q.get("pos")
                 and (Vec(*q["pos"]) - photo).flat() < 0.8]
        if crowd:                                        # another bot by the spot would be in the photo
            print(p["name"], "not photographed: in the way", crowd)
        else:
            img = mcc_nav.grab()                         # MCC's window, on whichever monitor
            w, h = img.size
            name = p["name"].replace("+", "p").replace(" ", "_")
            img.crop((w // 2 - 450, int(h * 0.12), w // 2 + 450, int(h * 0.98))).save(os.path.join(out, f"{label}_{name}.png"))
            print("photographed", p["name"], flush=True)
        walk(m, live, T, slot, index, away, origin, seconds=10.0)


if __name__ == "__main__":
    main()
