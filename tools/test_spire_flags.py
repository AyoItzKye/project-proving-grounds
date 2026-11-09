"""the player's Spire Invasion flags of (match 220515, Legendary Spartans attacking, Normal Elites), each at its live
moment:

1. Man cannons: a person's ride up recorded from 4.1 u off the middle cannon's pad (three bots circled there pressing
   jump: "Do these stupid fucks think the man cannon is there?") starts on the pad, marked a ride; a hop by a pad and a
   ride far from any pad stay as they were; on Spire's map every launch up starts on its pad
2. Attackers' urgency ("defenders have urgency ... the same is not for attackers"): an Invasion attacker running for
   the core, an Elite seen 6 u off its line: that fight weighs a seventh (it was fought at full, as anything within
   8 u); the man shooting it is still fought at full, and a gun a step away still taken
3. Armor lock that never locked (NovaHunter, 187-190 s, held 3 s standing, health 0.73 -> 0.15): hurt in it, the bot
   lets go and fights on; locked (the game shows it on), it holds still as before
4. The Warthog under the core (Spartan68, 100 s at (-178.9, -403.3) with the core 36 u up): its driver gets out within
   1 s (as near as a Warthog goes)
5. Reach's loose guns are read by its own parent field (+0x14), not CE's (no power weapon run in the match)

usage: python -I test_spire_flags.py      -> "spire flags OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import Energy, Kit  # noqa: E402
from brain.maps import anchor_launches, get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

M = get_map("reach_35_island")
T = terrain(M)
CORE = Vec(-178.24, -405.33, -22.9)
DELIVER = Vec(-163.05, -432.09, -58.37)
MID_PAD = (-160.95, -380.78, -57.96)


def bot(seed=1):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(seed)), M, random.Random(seed))
    b._terrain, b.notes = T, []
    return b


def main():
    testdata.need_lidar("reach_35_island")
    fails = []
    # 1. rides anchored on their pads
    pad = [dict(kind="launcher", pos=list(MID_PAD))]
    ride = dict(take_off=[-162.0, -384.7, -58.4], land=[-168.8, -394.7, -24.3], runup=[-162.5, -385.0])
    hop = dict(take_off=[-162.0, -384.7, -58.4], land=[-163.0, -386.0, -57.9])
    far = dict(take_off=[-150.0, -370.0, -56.0], land=[-160.0, -380.0, -24.3])
    a, h, f = anchor_launches([ride, hop, far], pad)
    # (its run-up the cannon's entrance, 1.5 u back along the throw, not the person's 4.1 u off: brain/maps CANNON_ENTRY)
    to, ld, ru = a["take_off"], a["land"], a.get("runup") or [math.nan, math.nan]
    back = ((ru[0] - to[0]) * (ld[0] - to[0]) + (ru[1] - to[1]) * (ld[1] - to[1])) / math.hypot(ld[0] - to[0], ld[1] - to[1])
    if (math.hypot(to[0] - MID_PAD[0], to[1] - MID_PAD[1]) > 0.01 or not a.get("ride")
            or not -1.55 < back < -1.45 or ride["take_off"][0] != -162.0):
        fails.append(f"the ride 4.1 u off the pad: {a} (want it on the pad, a ride, from its entrance 1.5 u back, the "
                     f"original left alone)")
    if h != hop or f != far:
        fails.append(f"a hop by the pad {h} or a ride 13 u off it {f}: changed (want as they were)")
    # (match 230700: the marker sits up to 1.2 u into the cannon; the trigger is where people's rides start, so with
    # one of those 0.6 u off the marker the far ride starts there, not on the marker)
    good = dict(take_off=[-160.56, -380.3, -57.7], land=[-169.2, -392.5, -24.3])
    a2, g2 = anchor_launches([ride, good], pad)
    if math.hypot(a2["take_off"][0] - good["take_off"][0], a2["take_off"][1] - good["take_off"][1]) > 0.01:
        fails.append(f"with a person's ride 0.6 u off the marker: the far ride starts at {a2['take_off'][:2]} (want "
                     f"{good['take_off'][:2]}, the trigger)")
    pads = [p["pos"] for p in M["features"] if p.get("kind") == "launcher"]
    for _, _, k, _ in T.hjumps:
        to = k["take_off"]
        if k["land"][2] - to[2] > 10.0:
            d = min(math.hypot(p[0] - to[0], p[1] - to[1]) for p in pads)
            if 1.2 < d < 5.0:
                fails.append(f"Spire: a launch up from {to[:2]} starts {d:.1f} u off its man cannon (want at its trigger)")

    # 2. an attacker's urgency on its run for the core
    me = PlayerState(1, 0, "runner", Vec(-170.0, -385.0, -59.0))
    elite_pos = Vec(-164.5, -382.5, -59.0)
    elite = PlayerState(5, 1, "elite", elite_pos)
    snap = Snapshot(100.0, [me, elite], mode="invasion", inv_phase=3, inv_attackers=0, inv_core=CORE,
                    inv_core_carrier=None, inv_delivery=DELIVER)
    gun = Vec(-170.6, -385.4, -59.0)

    def weigh(shot_by=False):
        b = bot()
        b.order, b.grab_point = Order("runner", CORE), CORE
        b.per.beliefs[5] = Belief(elite_pos, Vec(), 100.0, True, "eyes")
        if shot_by:
            b.per.attacker_id, b.per.attacker_t = 5, 99.5
        scores = {("fight", 5): 3.0, ("objective", CORE): 1.0, ("item", gun): 1.0}
        b.keep_role(scores, me, snap, {5})
        return scores

    s = weigh()
    if abs(s[("fight", 5)] - 3.0 * 0.15) > 1e-6:
        fails.append(f"an attacker's run for the core, an Elite 6 u off its line: the fight weighs {s[('fight', 5)]:.2f} "
                     f"(want 0.45, a seventh of 3.0)")
    if s[("item", gun)] != 1.0:
        fails.append(f"a gun 0.7 u away on its way: {s[('item', gun)]:.2f} (want 1.0, taken)")
    s = weigh(shot_by=True)
    if s[("fight", 5)] != 3.0:
        fails.append(f"the man shooting it: {s[('fight', 5)]:.2f} (want 3.0, fought)")

    # 3. armor lock that never locked
    def lock(on):
        b = bot()
        k = Kit(b.p, "reach")
        k.kind, k.energy = "armor_lock", Energy("reach", "armor_lock")
        k.press, k.hold_until, k.press_t0, k.press_hp = ("armor_lock", "self", None, 1.5, "test"), 101.5, 100.0, (1.0, 1.0)
        me = PlayerState(1, 0, "nova", Vec(-154.9, -389.8, -58.5), shield=0.28, health=1.0, equipment="armor_lock",
                         ability_on=on)
        act = Action(forward=1.0, fire=True)
        note = k.act(b, 100.3, 1 / 30, me, Snapshot(100.3, [me]), act)
        return act, note

    act, note = lock(False)
    if act.equipment or act.forward != 1.0 or "did not lock" not in str(note):
        fails.append(f"hurt in an armor lock the game does not show on: equipment {act.equipment}, forward "
                     f"{act.forward}, note {note!r} (want let go, moving, noted)")
    act, note = lock(True)
    if not act.equipment or act.forward != 0.0 or act.fire:
        fails.append(f"in a real lock: equipment {act.equipment}, forward {act.forward}, fire {act.fire} (want held, "
                     f"still, silent)")

    # 4. the Warthog under the core
    hog_at = Vec(-178.9, -403.3, -59.0)
    hog = dict(handle=5, kind="warthog", pos=(hog_at.x, hog_at.y, hog_at.z), riders=1, occupied=True,
               fwd=(math.cos(-1.25), math.sin(-1.25), 0.0), turrets=[], manned=[], gunner=False)
    w = bot(3)
    w.order, w.seat, w.seat_for, w.enter_want, w.enter_riders, w.drive_to = Order("runner", CORE), "driver", None, \
        "driver", 0, CORE
    out_at = None
    for k in range(60):
        t = 10.0 + k / 30
        wme = PlayerState(1, 0, "w", hog_at, yaw=-1.25, vehicle=5)
        a = Action(yaw=-1.25)
        w.drive(t, 1 / 30, wme, Snapshot(t, [wme], vehicles=[hog], mode="invasion", inv_phase=3, inv_attackers=0,
                                         inv_core=CORE, inv_delivery=DELIVER), a, lambda p, q, **kw: q)
        if a.action:
            out_at = t - 10.0
            break
    if out_at is None or out_at > 1.0:
        fails.append(f"a Warthog under the core 36 u up: out after {out_at} s (want within 1 s)")

    # 5. Reach's loose guns
    from brain.live import LiveH2, LiveReach
    if LiveReach.ground_weapons is not LiveH2.ground_weapons or LiveReach.PARENT_AT != 0x14:
        fails.append("Reach's loose guns: not read by its own parent field (+0x14)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("spire flags OK (rides start on their man cannons; attackers run for the objective; a failed armor lock is let"
          " go; a Warthog under the core is left; Reach's loose guns by +0x14)")


if __name__ == "__main__":
    main()
