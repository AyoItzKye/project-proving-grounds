"""Pilots that hit a wall get unstuck and do not fly back into it (at 31.6 s, "dumb ass banshee stuck again" at 320.4 s;
"we need to implement some sort of short sighted lidar or something that once a bot detects its hitting a wall or
something, it turns around and gets unstuck instead of repeatedly flying into the same spot"). Live: Warthog_2's
Banshee sat at (12.3, -32.1, 6.7) by Sidewinder's red base 36-125 s at full throttle, ReaperMoose's at (4.4, -1.9, 4.4)
under the middle arch 257-425 s; drive's old recovery backed off twice a spot and then pushed on at the same wall for
good (logs/tmp/stalls.py on the trace).

1. Terrain.fly_clear (the probe): from Warthog_2's stuck frame the way it pushed (west) is blocked within 2 u, the way
   it came (east) is open 8+ u; in open air 10 u over the blue side's floor every heading is open
2. Warthog_2's frame and ReaperMoose's frame, flown 25 s in a kinematic Banshee (turn 2.5 rad/s, 9 u/s, climbs on its
   pitch with speed; a move into the level data's solid is stopped), pushed every tick straight at where its trip went
   (drive's way with no painted air): out of the pocket (3+ u from the stuck spot) within 6 s, stalled (pushing, under
   0.3 u in 2 s) under 5 s in all, never back within 1 u of the spot once out
3. a wall the level data lacks (an invisible slab in the model only) across a Banshee's way in open air: stuck once,
   then the remembered spot keeps it off: no second stall, past the slab within 20 s
4. a Banshee cruising in open air at speed, and one setting down at its destination: no probe notes, input untouched
5. a Falcon (vtol) against Sidewinder's red base wall turns its stick, not its facing (its gunners keep their side)
The kinematic model is this test's assumption; drive() itself is not run (its stand-in pushes at the goal each tick).

usage: python -I test_air_stuck.py      -> "air stuck OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
DT = 1.0 / 30.0
STUCK1, GOAL1 = Vec(12.27, -32.28, 6.58), Vec(-19.9, -31.4, 6.0)      # Warthog_2, trip to the blue flag (att path)
STUCK2, GOAL2 = Vec(4.41, -1.95, 4.44), Vec(-6.7, 1.2, 4.0)            # ReaperMoose, its fly point (att path)
OPEN = Vec(-43.0, 42.0, 21.59)        # 10 u over the floor, every heading 12 u clear (logs/tmp/open_air.py)


def solid(q, floor):
    return T.fly_clear(q, 0.0, 0.01, dzs=(0.0,), floor=floor, start=0.0) < 0.01


def fly(start, goal, seconds=25.0, kind="banshee", slab=None, landing=False, yaw0=None):
    """The kinematic flight. slab: (x0, x1, y0, y1, z0, z1) solid the level data does not have."""
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, rng=random.Random(1))
    b._terrain, b.seat, b.seat_since = T, "driver", -10.0
    pos, v, vz = start, 0.0, 0.0
    head = math.atan2(goal.y - start.y, goal.x - start.x) if yaw0 is None else yaw0
    trail, notes, stall, hist, fal = [], set(), 0.0, [], None
    for k in range(int(seconds / DT)):
        t = k * DT
        b.now, b.notes, b.landing = t, [], landing
        h = T.height_over(pos.x, pos.y, pos.z)
        vel = Vec(math.cos(head) * v, math.sin(head) * v, vz)
        me = PlayerState(1, 0, "pilot", pos, vel=vel, yaw=head, alive=True, vehicle=9)
        gy = math.atan2(goal.y - pos.y, goal.x - pos.x)
        act = Action(yaw=gy)                                       # (drive's stand-in: at the goal, full on)
        act.forward, act.pitch = 1.0, max(-0.35, min(0.45, (9.0 - h) * 0.12))
        snap = Snapshot(t, [me], vehicles=[dict(handle=9, kind=kind, pos=(pos.x, pos.y, pos.z), occupied=True,
                                                riders=1, team=0)])
        b.air_guard(me, act, snap)
        notes |= {n.split(",")[0] for n in b.notes}
        d = math.atan2(math.sin(act.yaw - head), math.cos(act.yaw - head))
        if kind == "falcon":
                                                           # (a Falcon slides where the stick points)
            mv = act.yaw + math.atan2(act.strafe, act.forward)
            sp = math.hypot(act.forward, act.strafe)
            want_v = 9.0 * sp
        else:
            head = head + max(-2.5 * DT, min(2.5 * DT, d))
            mv, want_v = head, act.forward * (9.0 if act.forward > 0 else 2.5)
        v += max(-8.0 * DT, min(8.0 * DT, want_v - v))
        vz = max(-0.5, min(0.5, act.pitch)) * max(v, 0.0) * 0.9 + (2.5 * act.vertical if kind == "falcon" else 0.0)
        floor = pos.z - h
        q = Vec(pos.x + math.cos(mv) * v * DT, pos.y + math.sin(mv) * v * DT, pos.z)
        blocked = solid(q, floor) or (slab and slab[0] <= q.x <= slab[1] and slab[2] <= q.y <= slab[3]
                                      and slab[4] <= q.z <= slab[5])
        if blocked:
            v, q = 0.0, pos
        up = Vec(q.x, q.y, q.z + vz * DT)
        if solid(up, floor) or up.z < floor + 0.3:
            vz, up = 0.0, q
        pos = up
        trail.append((t, pos))
        hist.append((t, pos))
        while hist and t - hist[0][0] > 2.0:
            hist.pop(0)
        if act.forward > 0.5 and t > 2.0 and max((p - pos).flat() for _, p in hist) < 0.3:
            stall += DT
        if kind == "falcon" and b.notes and fal is None:
            fal = (gy, act.yaw, act.forward, act.strafe)
    return trail, notes, stall, fal


def escape(trail, spot, out=3.0):
    """When the craft first got out u from spot, and its time back within 1 u of it after that."""
    t_out = next((t for t, p in trail if (p - spot).flat() >= out), None)
    back = sum(DT for t, p in trail if t_out is not None and t > t_out and (p - spot).flat() < 1.0)
    return t_out, back


def main():
    fails, info = [], []
    f1 = T.height_over(STUCK1.x, STUCK1.y, STUCK1.z)
    west = T.fly_clear(STUCK1, 3.113, 12.0, floor=STUCK1.z - f1)
    east = T.fly_clear(STUCK1, 0.0, 12.0, floor=STUCK1.z - f1)
    opens = [T.fly_clear(OPEN, math.radians(a), 12.0, floor=OPEN.z - T.height_over(OPEN.x, OPEN.y, OPEN.z))
             for a in range(0, 360, 45)]
    if not (west < 2.0 and east >= 8.0) or min(opens) < 12.0:
        fails.append(f"probe: west {west:.1f} (want < 2), east {east:.1f} (want 8+), open air {min(opens):.1f} (want 12)")
    for name, spot, goal in (("Warthog_2 at the red base", STUCK1, GOAL1), ("ReaperMoose under the arch", STUCK2, GOAL2)):
        trail, notes, stall, _ = fly(spot, goal)
        t_out, back = escape(trail, spot)
        info.append(f"{name}: out at {t_out if t_out is None else round(t_out, 1)} s, stalled {stall:.1f} s")
        if t_out is None or t_out > 6.0 or stall > 5.0 or back > 0.0:
            fails.append(f"{name}: out 3 u at {t_out} s (want <= 6), stalled {stall:.1f} s (want < 5), back by the spot "
                         f"{back:.1f} s (want 0); notes {sorted(notes)}")
    # 3. an unmapped slab across the way, in open air
    g = Vec(OPEN.x, OPEN.y + 24.0, OPEN.z)
    slab = (OPEN.x - 2.0, OPEN.x + 2.0, OPEN.y + 6.0, OPEN.y + 6.6, OPEN.z - 6.0, OPEN.z + 30.0)
    trail, notes, stall, _ = fly(OPEN, g, seconds=20.0, slab=slab)
    past = next((t for t, p in trail if p.y > slab[3] + 0.5), None)
    stalls, run, prev = 0, 0, None
    for t, p in trail:                                  # stall episodes: 1.2 s within 0.3 u
        run = run + DT if prev is not None and (p - prev).flat() < 0.3 * DT / 2.0 else 0.0
        if abs(run - 1.2) < DT / 2:
            stalls += 1
        prev = p
    info.append(f"unmapped slab: past it at {past if past is None else round(past, 1)} s, {stalls} stall(s)")
    if past is None or stalls > 1:
        fails.append(f"unmapped slab: past it at {past} (want within 20 s), {stalls} stalls (want 1 at most); "
                     f"notes {sorted(notes)}")
    # 4. cruising in open air, and setting down: untouched
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, rng=random.Random(1))
    b._terrain, b.seat, b.seat_since, b.now = T, "driver", -10.0, 10.0
    for pos, landing, what in ((OPEN, False, "cruising in open air"),
                               (Vec(OPEN.x, OPEN.y, OPEN.z - 9.0), True, "setting down")):
        b.notes, b.landing, b.air_still, b.air_rec = [], landing, None, None
        me = PlayerState(1, 0, "pilot", pos, vel=Vec(0.0, 8.0, 0.0), yaw=math.pi / 2, alive=True, vehicle=9)
        act = Action(yaw=math.pi / 2)
        act.forward, act.pitch = 1.0, -0.2
        b.air_guard(me, act, Snapshot(10.0, [me], vehicles=[dict(handle=9, kind="banshee", pos=(pos.x, pos.y, pos.z),
                                                                   occupied=True, riders=1, team=0)]))
        if act.forward != 1.0 or act.pitch != -0.2 or act.yaw != math.pi / 2 or b.notes:
            fails.append(f"{what}: forward {act.forward}, pitch {act.pitch}, yaw {act.yaw}, notes {b.notes} (want untouched)")
    # 5. a Falcon at the red base wall: the stick turns, its facing stays
    _, notes, _, fal = fly(STUCK1 + Vec(2.0, 0.0, 0.0), GOAL1, seconds=2.0, kind="falcon")
    if fal is None or abs(fal[1] - fal[0]) > 1e-9 or (abs(fal[3]) < 0.1 and fal[2] > 0.0):
        fails.append(f"a Falcon at the red base wall: first override {fal} (want its yaw kept, the stick turned); "
                     f"notes {sorted(notes)}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails + info))
    print("air stuck OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
