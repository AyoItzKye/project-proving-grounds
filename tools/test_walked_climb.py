"""Offline check: a person's walk up floor the level data lacks (a LiDAR link no jump makes: Boneyard's ramp under phase
1's territories, 3.8 u up in 3.4 s) is a route bots walk, not a jump they run at and fall short of (live 20261105-022641:
attackers 10-29 s a time at its foot, phase 1 lost both rounds). Real jumps and lift rides stay jumps.

usage: python -I test_walked_climb.py      -> "walked climb OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import ROUTE_JUMP, walked_climb  # noqa: E402

RAMP = dict(take_off=[250.94, 81.75, -9.75], land=[249.47, 89.99, -5.99], apex=-5.94, air_s=3.37, human=1,
            path=[[250.94, 81.75, -9.75], [251.04, 82.52, -9.47], [251.08, 83.6, -8.93], [250.96, 84.43, -8.6],
                  [250.5, 87.0, -7.6], [249.47, 89.99, -5.99]])


def main():
    assert walked_climb(RAMP, 0.67), "the ramp walk is a climb"
    hop = dict(RAMP, take_off=[247.21, 102.01, -6.0], land=[247.45, 100.21, -4.92], apex=-4.9, air_s=0.72,
               path=[[247.21, 102.01, -6.0], [247.45, 100.21, -4.92]])
    assert not walked_climb(hop, 0.67), "a 1.1 u hop up is a jump"
    assert not walked_climb(dict(RAMP, land=[249.47, 89.99, -3.0]), 0.67), "up 6.8 u: a lift, not a walk"
    assert not walked_climb(dict(RAMP, air_s=1.0), 0.67), "8 u in a second: carried"
    assert not walked_climb(dict(RAMP, apex=-4.5, path=RAMP["path"] + [[249.4, 90.0, -4.5]]), 0.67), "an arc over the end"
    assert not walked_climb(dict(RAMP, land=[251.0, 82.5, -5.99]), 0.67), "3.8 u up over 0.75 u: no walk is that steep"
    assert not walked_climb(dict(RAMP, ride=1), 0.67) and not walked_climb(dict(RAMP, kind="route"), 0.67)

    m = get_map("reach_70_boneyard/variants/v86d95e85")
    T = terrain(m)
    invasion.apply_barriers(T, invasion.layout(m["objects"]))
    at = lambda q, x, y: abs(q[0] - x) < 0.05 and abs(q[1] - y) < 0.05
    ups = [p for _, _, p, _ in T.hroutes if len(p) > 1 and at(p[1], 250.94, 81.75)]
    assert ups, "the ramp walk is one of the people's routes, from the person's run-up"
    assert not any(at(k["take_off"], 250.94, 81.75) for _, _, k, _ in T.hjumps), "the ramp walk is no jump"
    up = ups[0]
    assert at(up[0], 250.71, 80.39) and not up[0][3] & ROUTE_JUMP, "first his run-up (live 033058: from beside, the " \
        "hop went across the ramp's foot)"
    assert up[1][3] & ROUTE_JUMP and not any(q[3] & ROUTE_JUMP for q in up[2:]), \
        "a hop on at the take-off only (live 031842: walked at, the ramp's lip kept bots on the floor under it)"
    assert any(at(p[-1], 250.94, 81.75) and not any(q[3] & ROUTE_JUMP for q in p) for _, _, p, _ in T.hroutes), \
        "and down it the other way, no hop"

    # at the ramp's foot, beside its take-off: back to the run-up, not up the walking graph's false way over its lip
    # (live 20261105-041255: 10-12 s pushing at (251.47, 83.27) while the route cost 1.5 x its length)
    for foot in (Vec(250.9, 81.4, -9.72), Vec(249.7, 82.3, -9.7), Vec(250.85, 81.65, -9.74)):
        w = T.nav(foot, Vec(251.217, 94.975, -4.0), jump=True, human=True)
        assert w.y < 81.2 or hasattr(w, "path"), f"from {foot} to the run-up first, not {w}"

    # a route walked on the floor under it (z -10, its end at -6) is short; twice and the bot goes another way
    from brain.bot import Bot
    from brain.core import PlayerState
    from brain.profiles import make_profile
    from brain.terrain import RouteVec
    import random
    b = Bot(1, 1, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    b.now = 10.0
    rv = RouteVec(249.47, 89.99, -5.99, path=up)
    for n in (1, 2):
        b.route_key, b.route_end = (round(up[0][0], 1), round(up[0][1], 1)), Vec(*up[-1][:3])
        b.judge_route(PlayerState(1, 1, "b", Vec(249.45, 90.0, -10.2)))
        assert b.jump_blocked(rv) == (n == 2), f"after {n} short walks: blocked {b.jump_blocked(rv)}"
    b.jump_fails = {}
    b.route_key, b.route_end = (round(up[0][0], 1), round(up[0][1], 1)), Vec(*up[-1][:3])
    b.judge_route(PlayerState(1, 1, "b", Vec(249.4, 90.1, -6.0)))
    assert not b.jump_fails, "a route that got there is no fail"
    goal = Vec(251.217, 94.975, -4.0)                    # phase 1's north territory
    for start in (Vec(251.4, 83.0, -9.83), Vec(250.48, 84.85, -9.96), Vec(251.55, 83.2, -9.82)):
        q = start
        for _ in range(12):                               # the live stuck spots: walk on to the ramp's foot, then route
            w = T.nav(q, goal, jump=True, human=True)
            assert not hasattr(w, "sx") or (w - Vec(249.47, 89.99, -5.99)).flat() > 1.0, f"a jump up the ramp from {q}"
            if hasattr(w, "path"):
                break
            q = Vec(w.x, w.y, w.z)
        else:
            raise AssertionError(f"no route up the ramp from {start}")
    # Spire's rock climb up to phase 1's territory A: a third of the person's path over no nav floor (a face steeper
    # than the floor test) stays the jump it was (as a walk, live S5 / S6: 4 of 37 attacker visits got up, phase 1
    # lost all 4 rounds; as a jump S1-S4 took 8 of 8)
    S = terrain(get_map("reach_35_island/variants/v3977bae2"))
    near = lambda p: at(p, -135.37, -357.83) or at(p, -134.14, -357.52)
    assert not any(near(p[0]) for _, _, p, _ in S.hroutes), "Spire's rock climb at A is a route"
    assert any(at(k["take_off"], -135.37, -357.83) for _, _, k, _ in S.hjumps), "Spire's rock climb at A is no jump"
    print("walked climb OK")


if __name__ == "__main__":
    main()
