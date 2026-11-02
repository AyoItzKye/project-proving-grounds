"""No shot without a clear line, nothing run into ("add something to the bots where they detect when an object is in front
of them ... running into a wall and jumping and shooting at walls").

1. a man in the open: the bot fires; the same man "seen" only because he hit us through the level (Perception counts the
   man shooting us for 1.5 s): never; a vehicle across the line: never
2. property (Code Master TS-11), 300 generated scenes: after Bot.fire_gate the trigger is down only with an enemy in
   front of the aim whose line is clear (line_clear); with no fresh clear line to anyone it is always up; a held
   plasma pistol charge is never let go by the gate (letting go fires it)
3. in a fight a strafe into a wall goes the other way (before the 0.6 s push unstuck needed), a step straight into it
   goes round; walking, a wall is left to redirect but a vehicle in the way is walked round; standing still: untouched
4. no jump into a wall at eye height; a jump along the wall, a planned jump: untouched

usage: python -I test_clear_line.py      -> "clear line OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec, wrap  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
A = Vec(70.0, -120.0, T.nav_z(70.0, -120.0))
FOE = A + Vec(-8.0, 0.0, 0.0)


def bot():
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(3)), MAP, random.Random(3))
    b.can_pickup = False
    return b


def fires(los, through_level=False, vehicles=(), seconds=4.0):
    b, t, yaw, pitch, n, ticks = bot(), 0.0, math.pi, 0.0, 0, 0
    while t < seconds:
        if through_level:
            b.per.attacker_sure = (2, t)                 # (he keeps hitting us: Perception counts him as seen)
        me = PlayerState(1, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, weapon="assault_rifle",
                         weapons=["assault_rifle"])
        foe = PlayerState(2, 1, "human", FOE, alive=True)
        a = b.think(t, 1 / 30, Snapshot(t, [me, foe], vehicles=list(vehicles)), lambda p, q: los,
                    lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        if t > 1.5:
            ticks += 1
            n += bool(a.fire)
        t += 1 / 30
    return n / max(ticks, 1)


class Walls:
    """A terrain whose only wall stands toward `toward` (rad): clearance 0.3 u within 0.4 rad of it, 3 u elsewhere."""
    def __init__(s, toward):
        s.toward = toward

    def clearance(s, p, yaw, far=3.0, height=0.4, waist=True):
        return 0.3 if abs(wrap(yaw - s.toward)) < 0.4 else far


def guarded(goal, fwd, strafe, wall=None, vehicles=(), yaw=0.0):
    b = bot()
    b._terrain = Walls(wall if wall is not None else 99.0)
    b.goal, b.strafe_dir, b.next_strafe_flip, b.notes, b.planned_jump = goal, 1, 0.0, [], False
    act = Action(yaw=yaw)
    act.forward, act.strafe = fwd, strafe
    me = PlayerState(1, 0, "bot", A, yaw=yaw, alive=True)
    b.obstacle_guard(10.0, me, act, Snapshot(10.0, [me], vehicles=list(vehicles)))
    return b, act


def main():
    fails = []
    # 1
    open_, hidden = fires(True), fires(False, through_level=True)
    van = dict(handle=77, kind="warthog", pos=((A.x + FOE.x) / 2, A.y, A.z), occupied=False)
    behind_van = fires(True, vehicles=[van])
    if open_ < 0.2:
        fails.append(f"a man in the open, 8 u: fired {open_:.0%} of the ticks (want 20% or more)")
    if hidden > 0.0:
        fails.append(f"a man seen only through the level: fired {hidden:.0%} of the ticks (want none)")
    if behind_van > 0.0:
        fails.append(f"a Warthog across the line: fired {behind_van:.0%} of the ticks (want none)")
    # 2 property
    rng = random.Random(11)
    for k in range(300):
        b = bot()
        now = 50.0
        me = PlayerState(1, 0, "bot", A, yaw=rng.uniform(-math.pi, math.pi), alive=True,
                         weapon=rng.choice(["assault_rifle", "plasma_pistol"]))
        foes = [PlayerState(10 + i, 1, "foe", A + Vec(rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(-2, 2)),
                            alive=True) for i in range(rng.randint(0, 4))]
        for f in foes:
            if rng.random() < 0.5:
                b.per.clear_at[f.id] = now - rng.uniform(0.0, 0.4)
        vans = [dict(handle=200 + i, kind="ghost", pos=(A.x + rng.uniform(-15, 15), A.y + rng.uniform(-15, 15), A.z),
                     occupied=False) for i in range(rng.randint(0, 2))]
        snap = Snapshot(now, [me] + foes, vehicles=vans)
        charging = me.weapon == "plasma_pistol" and rng.random() < 0.5
        b.charge_since = now - 0.5 if charging else None
        act = Action(yaw=rng.uniform(-math.pi, math.pi))
        act.fire, b.notes = True, []
        b.fire_gate(now, me, act, snap)
        fresh = [f for f in foes if now - b.per.clear_at.get(f.id, -9.0) <= b.LINE_FRESH]
        if charging:
            if not act.fire:
                fails.append(f"scene {k}: the gate let a held plasma pistol charge go")
                break
            continue
        if not fresh and act.fire:
            fails.append(f"scene {k}: fired with no fresh clear line to anyone")
            break
        if act.fire:
            ok = any(b.line_clear(now, me, f.id, snap) and (
                math.dist((A.x, A.y), (f.pos.x, f.pos.y)) < 2.0
                or abs(wrap(math.atan2(f.pos.y - A.y, f.pos.x - A.x) - act.yaw))
                < max(0.15, math.atan2(1.2, math.dist((A.x, A.y), (f.pos.x, f.pos.y))))) for f in foes)
            if not ok:
                fails.append(f"scene {k}: fired with no clear-lined enemy in front of the aim")
                break
    # 3
    b, act = guarded(("fight", 2), 0.0, 1.0, wall=math.pi / 2)          # strafing left into a wall on the left
    if not act.strafe < -0.5 or b.strafe_dir != -1 or not any("the other way" in n for n in b.notes):
        fails.append(f"fight, strafing into a wall: strafe {act.strafe:.2f}, notes {b.notes} (want the other way)")
    b, act = guarded(("fight", 2), 1.0, 0.0, wall=0.0)                  # straight into it
    way = math.atan2(act.strafe, act.forward)
    if abs(way) < 0.4 or not any("round it" in n for n in b.notes):
        fails.append(f"fight, straight into a wall: goes {math.degrees(way):.0f} deg, notes {b.notes} (want round it)")
    b, act = guarded(("hunt", Vec(0, 0, 0)), 1.0, 0.0, wall=0.0)        # walking: redirect's
    if (act.forward, act.strafe) != (1.0, 0.0):
        fails.append(f"walking into a wall: moved to {act.forward:.2f}, {act.strafe:.2f} (want redirect's, untouched)")
    car = dict(handle=5, kind="warthog", pos=(A.x + 1.0, A.y, A.z), occupied=False)
    b, act = guarded(("hunt", Vec(0, 0, 0)), 1.0, 0.0, vehicles=[car])
    if abs(math.atan2(act.strafe, act.forward)) < 0.4 or not any("vehicle ahead" in n for n in b.notes):
        fails.append(f"walking into a Warthog: goes {act.forward:.2f}, {act.strafe:.2f}, notes {b.notes} (want round)")
    b, act = guarded(("fight", 2), 0.1, 0.1, wall=0.0)
    if (act.forward, act.strafe) != (0.1, 0.1):
        fails.append("standing still by a wall in a fight: the guard moved it")
    # 4
    for wall, planned, want in ((0.0, False, False), (math.pi / 2, False, True), (0.0, True, True)):
        b = bot()
        b._terrain, b.planned_jump, b.notes = Walls(wall), planned, []
        act = Action(yaw=0.0)
        act.forward, act.jump = 1.0, True
        b.no_wall_jump(PlayerState(1, 0, "bot", A, yaw=0.0, alive=True), act)
        if act.jump != want:
            fails.append(f"a jump with a wall toward {wall:.2f} rad, planned {planned}: jump {act.jump} (want {want})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"clear line OK (in the open {open_:.0%} of ticks fired, through the level and past a Warthog none; 300 "
          f"scenes; walls and vehicles stepped round)")


if __name__ == "__main__":
    main()
