"""Crouched targets.

1. the aim point: on a crouched man the bot aims at core.CROUCH_HEAD / CROUCH_CHEST over his feet, standing at 0.62 /
   0.35; both crouched heights land in a crouched body under either size (CE's camera ratio 0.35 / 0.62 and the sim's
   70%), the head one in the head under the first
2. in the sim, a Legendary bot 15 u from a man who crouches and stands still kills him in 20 s and lands most of its
   hits (before: every head shot passed over him)
3. the live snapshot: the person crouches while he holds his crouch key, a bot while its last command crouched, nobody
   dead; the crouch key counts only with MCC in front
4. the three aims at an enemy pass his stance (fight, a gunner's, a driver's gun)

usage: python -I test_crouch_aim.py      -> "crouch aim OK"
"""
import inspect
import math
import os
import random
import sys
from types import SimpleNamespace as NS

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain import core  # noqa: E402
from brain.bot import Aim, Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec, angles_to, eye  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.sim import Sim  # noqa: E402


def aim_height(crouched, head, d=15.0):
    """The height over his feet the bot's plan aims at, a man d u off, its hand error nil."""
    p = make_profile("top", "rusher", random.Random(1))
    p.aim_err, p.lead = 0.0, 0.0
    a = Aim(p, random.Random(2))
    me = PlayerState(1, 0, "b", Vec(0, 0, 0), alive=True, weapon="dmr")
    a.step(0.0, 1 / 30, me, 7, Vec(d, 0, 0), Vec(), head, crouched=crouched)
    return eye(me).z + d * math.tan(a.goal[1])


def main():
    fails = []
    # 1
    got = {(c, h): aim_height(c, h) for c in (False, True) for h in (False, True)}
    want = {(False, False): 0.35, (False, True): 0.62, (True, False): core.CROUCH_CHEST, (True, True): core.CROUCH_HEAD}
    if any(abs(got[k] - want[k]) > 0.01 for k in want):
        fails.append(f"1. aim heights {[(k, round(v, 3)) for k, v in got.items()]} (want {want})")
    for k in (0.35 / 0.62, 0.7):
        if not (0.08 * k < core.CROUCH_CHEST < 0.58 * k and 0.08 * k < core.CROUCH_HEAD < 0.70 * k):
            fails.append(f"1. at a crouched size of {k:.2f} a crouched aim misses him")
    if not 0.58 * 0.35 / 0.62 <= core.CROUCH_HEAD < 0.70 * 0.35 / 0.62:
        fails.append("1. the crouched head aim is not in the head at CE's camera ratio")
    # 2
    m = get_map("bloodgulch")
    T = terrain(m)
    a = Vec(70.0, -120.0, T.nav_z(70.0, -120.0))
    b = Vec(85.0, -120.0, T.nav_z(85.0, -120.0))
    sim = Sim("slayer", per_team=1, seed=5, tiers=["top"])
    shooter, target = sim.players[0], sim.players[1]
    shooter.pos, target.pos = a, b
    shooter.yaw = angles_to(a, b)[0]
    sim.bots[target.id].think = lambda *x, **k: Action(yaw=angles_to(b, a)[0], pitch=0.0, crouch=True)
    sim.spawn_point = lambda team: a if team == shooter.team else b      # (back to the same spots)
    sim.run(20.0)
    st = sim.stats[shooter.id]
    if st["kills"] < 1 or st["hits"] < 0.3 * max(1, st["shots"]):
        fails.append(f"2. 20 s at a crouched man standing still 15 u off: {st['kills']} kills, {st['hits']} hits of "
                     f"{st['shots']} shots (want a kill and 30%+ hits)")
    # 3
    import live_bots
    import collector
    raw = [dict(index=0, name="Owner", team=0, unit=1, pos=(0.0, 0.0, 0.0), fwd=None, aim=(1.0, 0.0, 0.0), vehicle=-1,
                health=1.0, shield=1.0, weapon="dmr"),
           dict(index=1, name="Bot1", team=1, unit=2, pos=(5.0, 0.0, 0.0), fwd=None, aim=(1.0, 0.0, 0.0), vehicle=-1,
                health=1.0, shield=1.0, weapon="dmr"),
           dict(index=2, name="Bot2", team=1, unit=3, pos=None, fwd=None, aim=None, vehicle=-1, health=0.0, shield=0.0,
                weapon="none")]
    live = NS(players=lambda: [dict(d) for d in raw], flags=lambda raw, stands=None: [], objects=lambda types_: [])
    # (test_bad_places' fake game)

    def stance(crouch, person):
        try:
            snap = live_bots.snapshot(live, 1.0, {}, {1, 2}, crouch, person)
        except Exception as e:                   # (a snapshot the fake game cannot feed: say what)
            return f"{type(e).__name__}: {e}"
        return {p.id: p.crouching for p in snap.players}
    s1, s2 = stance({1, 2}, True), stance(set(), False)
    if s1 != {0: True, 1: True, 2: False} or s2 != {0: False, 1: False, 2: False}:
        fails.append(f"3. snapshot stance: {s1} / {s2} (want the person and bot 1 crouched, the dead bot not; then none)")
    held = {162}
    keys = {162: "crouch", 32: "jump"}
    on = collector.crouch_held(1, state=lambda vk: vk in held, front=lambda: True, keymap=keys)
    away = collector.crouch_held(1, state=lambda vk: vk in held, front=lambda: False, keymap=keys)
    up = collector.crouch_held(1, state=lambda vk: False, front=lambda: True, keymap=keys)
    if not (on() and not away() and not up()):
        fails.append(f"3. crouch key: held {on()}, MCC behind {away()}, not held {up()} (want True, False, False)")
    # 4
    src = inspect.getsource(Bot)
    if src.count("crouched=crouched(") != 3:
        fails.append(f"4. {src.count('crouched=crouched(')} of the 3 aims at an enemy pass his stance")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"crouch aim OK (crouched head {core.CROUCH_HEAD}, chest {core.CROUCH_CHEST}; sim: {st['kills']} kills, "
          f"{st['hits']}/{st['shots']} hits on a crouched man)")


if __name__ == "__main__":
    main()
