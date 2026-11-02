"""Reach armor abilities the way the player uses them (his Spire game with every ability, logs/tmp/owner_inputs.py):

1. sprint is held up to 4 s while its reason lasts (his: Shift held 1.6-4.0 s, median 2.4), not 1 s and a cool
2. evade covers ground: travelling with nobody near, a dash 3.4 u on along the way (his: 20 of 27 at full shield, straight
   ahead); then not again for 4 s at least; never off the floor's end or into a wall
3. evade out of the fire: hit, shield under 0.6, a man within 9 u: a dash across his aim (his: 7 of 27)
4. the drop shield goes down in a held objective as the fight there starts, full shield too (the player: "Inside these
   objectives would be a good place to use the shield bubbles")
5. the jetpack is held for the climb: 0.7 s a unit (his: 5.3 u in 3.9 s, 1.6-2.4 u in 1.0-1.5 s), not a 0.5 s pulse
6. a held sprint is forward and steer: the stick
   forward only, the view swinging to the way it goes at 6 rad/s at most

usage: python -I test_player_abilities.py -> "player abilities OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.equipment import Kit, jet_hold  # noqa: E402
from test_equipment import A, T, bot, foe, ground, plan_now  # noqa: E402


def main():
    fails = []
    far = ground(A.x + 40.0, A.y)
    # 1
    b = bot("top", "reach", "sprint")
    k, how, point, hold, why = plan_now(b, [], goal=("objective", far))
    if k != "sprint" or hold != 4.0:
        fails.append(f"sprint on a clear route: {k} held {hold} s ({why}) (want held 4 s)")
    # 2
    b = bot("top", "reach", "evade")
    b.wp = ground(A.x + 5.0, A.y)
    k, how, point, hold, why = plan_now(b, [], goal=("objective", far))
    if k != "evade" or how != "dash" or point is None or abs((point - A).flat() - 3.4) > 0.1:
        fails.append(f"evade along a clear way: {k} {how} to {point} ({why}) (want a dash 3.4 u on)")
    k2 = plan_now(b, [], goal=("objective", far), now=2.0)[0]
    if k2 == "evade":
        fails.append("evade along the way again 1 s later (want 4 s at least between)")
    walled = bot("top", "reach", "evade")
    walled.wp = ground(A.x + 5.0, A.y)
    T.clearance, real = (lambda *a, **kw: 1.0), T.clearance                    # (a wall 1 u on)
    try:
        if plan_now(walled, [], goal=("objective", far))[0] == "evade":
            fails.append("evade along the way into a wall 1 u on")
    finally:
        T.clearance = real
    # 3
    b = bot("top", "reach", "evade")
    man = foe(ground(A.x + 5.0, A.y))
    k, how, point, hold, why = plan_now(b, [man], seen=(man.id,), goal=("fight", man.id), hit=True,
                                        me_kw=dict(shield=0.5))
    if k != "evade" or how != "dash":
        fails.append(f"hit at shield 0.5, a man 5 u off: {k} {how} ({why}) (want an evade across his aim)")
    # 4
    b = bot("top", "reach", "drop_shield")
    man = foe(ground(A.x + 7.0, A.y))
    k, how, point, hold, why = plan_now(b, [man], seen=(man.id,), goal=("hold", A), me_kw=dict(shield=1.0))
    if k != "drop_shield" or how != "feet":
        fails.append(f"holding an objective at full shield, a man 7 u off: {k} ({why}) (want the drop shield down)")
    # 5
    b = bot("top", "reach", "jetpack")
    up = Vec(A.x + 6.0, A.y, A.z + 2.5)
    k, how, point, hold, why = plan_now(b, [], goal=("objective", up))
    if k != "jetpack" or abs(hold - jet_hold(2.5)) > 1e-6 or not 1.7 < hold < 2.1:
        fails.append(f"a goal 2.5 u up: {k} held {hold} s ({why}) (want about 1.95 s)")
    if not (abs(jet_hold(5.3) - 3.9) < 0.1 and abs(jet_hold(1.9) - 1.5) < 0.2):
        fails.append(f"jetpack holds {jet_hold(1.9):.2f} s for 1.9 u, {jet_hold(5.3):.2f} s for 5.3 u (his 1.2-1.5, 3.9)")
    # 6
    me = PlayerState(1, 0, "bot", A, yaw=0.0, alive=True)
    act = Action(yaw=0.0)
    act.forward, act.strafe = 0.5, 0.8                                   # 58 deg left of the view
    Kit.sprint_steer(1 / 30, me, act)
    if act.strafe != 0.0 or not 0.0 < act.yaw <= 6.0 / 30 + 1e-9 or not act.forward > 0.0:
        fails.append(f"a sprint with a strafe: forward {act.forward:.2f}, strafe {act.strafe}, view {act.yaw:.3f} "
                     f"(want forward only, the view turning 0.2 rad at most)")
    act = Action(yaw=0.0)
    act.forward, act.strafe = 1.0, 0.0
    Kit.sprint_steer(1 / 30, me, act)
    if (act.forward, act.strafe, act.yaw) != (1.0, 0.0, 0.0):
        fails.append(f"a straight sprint changed: {act.forward}, {act.strafe}, {act.yaw}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("player abilities OK (sprint held 4 s, forward and steer; evade along the way and out of fire; shield in "
          "the hold; jetpack for the climb)")


if __name__ == "__main__":
    main()
