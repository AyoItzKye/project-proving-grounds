"""Offline checks for F7 shot recordings (the player: Stonetown's gate button and bridge locks): the
recorder keeps each shot's stand point, aim and impact and what moved meanwhile, and a Roomba
replays the recipe: walks to the stand point, aims at the impact (pitch too), fires, then stops.

usage: python -I test_shot_recipes.py      -> "shot recipes OK"
"""
import math
import struct
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lidar  # noqa: E402

MAP = "h2a_ca_zanzibar"


class FakeMem:
    def __init__(s):
        s.blocks = {}                                  # address -> bytearray

    def read(s, a, n):
        for base, b in s.blocks.items():
            if base <= a and a + n <= base + len(b):
                return bytes(b[a - base:a - base + n])
        return None


class FakeLive:
    """objects(): handle -> (type, pos); object() / g.read: each object's memory. The switch (type 8, at
    the impact point) keeps its damage at +0x5fc (more negative per hit, as Stonetown's gate switch did
    live); every device has a timer at +0x120 that ticks on its own."""
    def __init__(s):
        s.objs = {1: (10, (5.0, 5.0, 1.0)),           # a crate (the bridge)
                  2: (8, (3.0, 4.0, 0.6)),            # the switch the player shoots
                  3: (7, (30.0, 30.0, 1.0))}          # a far machine
        s.g = FakeMem()
        for h in s.objs:
            s.g.blocks[h * 0x1000] = bytearray(0x600)

    def objects(s, types=None):
        return [(h, t, "x", p) for h, (t, p) in s.objs.items() if types is None or t in types]

    def object(s, h):
        return h * 0x1000 if h in s.objs else None

    def poke(s, h, off, v):
        struct.pack_into("<f", s.g.blocks[h * 0x1000], off, v)

    def tick(s, t):
        for h in s.objs:
            if h * 0x1000 in s.g.blocks:
                s.poke(h, 0x120, t * 60.0)


def main():
    live, sent = FakeLive(), []
    sh = lidar.ShotRec(live, MAP, lambda a, b: sent.append(a))
    sh.path = os.path.join(tempfile.mkdtemp(), "shots.json")
    person = dict(pos=[0.0, 0.0, 0.4], aim=[0.6, 0.8, 0.0], weapon="smg")
    live.tick(0.0)
    live.poke(2, 0x5fc, -100.0)
    sh.key(0.0, person)
    assert sent[-1] == "RECORDING SHOTS"
    live.objs[50] = (5, (0.3, 0.4, 0.6))               # a projectile leaves the player
    live.objs[51] = (5, (4.8, 6.4, 1.0))               # a fast one first seen 8 units out, on his aim line
    live.objs[52] = (5, (5.0, -3.0, 1.0))              # one off to the side: not his
    sh.update(0.1, person)
    live.objs[50] = (5, (3.0, 4.0, 0.6))               # flies
    live.objs[51] = (5, (3.0, 4.0, 0.6))               # the fast one hits the switch too
    sh.update(0.2, person)
    del live.objs[50], live.objs[51], live.objs[52]    # hit: gone
    live.objs[1] = (10, (5.0, 7.0, 1.0))               # the bridge extended
    live.poke(2, 0x5fc, -136.0)                        # the switch took 36 damage
    live.tick(1.0)
    sh.update(0.3, person)
    sh.key(1.0, person)
    assert sent[-1] == "SHOTS SAVED", sent
    data = lidar.load(sh.path)
    r = data[-1]
    assert r["target"] == [3.0, 4.0, 0.6] and r["stand"] == [0.0, 0.0, 0.4], r
    assert any(c.get("frm") == [5.0, 5.0, 1.0] and c.get("to") == [5.0, 7.0, 1.0] for c in r["changed"]), r["changed"]
    assert r["damage"] == dict(type=8, pos=[3.0, 4.0, 0.6], offset=0x5fc, drop=36.0), r["damage"]   # not the timer
    assert r["weapon"] == "smg"
    assert len(r["shots"]) == 2, r["shots"]            # the near one and the fast far one, not the side one

    # replay by damage: the bot keeps firing until the switch took 2 x 36, however many shots that is
    rec0 = lidar.Recorder(MAP, count_run=False)
    taken = [-200.0]
    rec0.damage_reader = lambda t, p, off: taken[0]
    b0 = lidar.Roomba(2, random.Random(2))
    t0 = dict(r, kind="shoot", name="dmg", take_off=r["stand"], eye=0.6, seconds=3.0, _feat=("shoot", 9, 0))
    b0.trial, b0.phase, b0.on_t = t0, "on", 0.0
    stopped_at = None
    for k in range(200):
        out = b0.shoot_steer(k * 0.1, list(r["stand"]), rec0, None, t0)
        if out is None:
            stopped_at = k * 0.1
            break
        taken[0] -= 1.0                                # 10 damage a second: 72 needs ~7.2 s, past the 3 s
    assert stopped_at is not None and 7.0 <= stopped_at <= 8.0, stopped_at

    # replay on the real map: a recipe on reachable floor near the gate switch (device_probe found it)
    T, _, _ = lidar.level_data(MAP)
    rec = lidar.Recorder(MAP, count_run=False)
    stand, target = [22.42, 1.25, 1.47], [22.9, 5.7, 3.5]
    rec.shot_recipes = [dict(stand=stand, target=target, seconds=3.0,
                             shots=[dict(stand=stand, impact=target,
                                         aim=[0.48 / 4.7, 4.45 / 4.7, (3.5 - 1.71) / 4.7])])]
    b = lidar.Roomba(1, random.Random(1))
    trial = b.shot_trial([18.0, 0.0, 1.0], rec, T)
    assert trial and trial["kind"] == "shoot" and 0.0 <= trial["eye"] <= 1.0, trial
    b.trial, b.phase, b.trial_t, b.trial_s = trial, "go", 0.0, 60.0
    out = b.shoot_steer(0.0, [18.0, 0.0, 1.0], rec, T, trial)
    assert out[0] > 0.5, "does not walk to the stand point"
    out = b.shoot_steer(0.1, list(stand), rec, T, trial)       # arrived
    assert b.phase == "on"
    fires, aim_ok = 0, True
    for k in range(80):                                     # no damage reading: 2 x his 3 s at 10 ticks a second
        out = b.shoot_steer(0.2 + k * 0.1, list(stand), rec, T, trial)
        if out is None:
            break
        _, _, yaw, buttons, pitch = out
        fires += bool(buttons & lidar.BTN_FIRE)
        aim_ok &= abs(yaw - math.atan2(target[1] - stand[1], target[0] - stand[0])) < 0.01 and pitch > 0.2
    assert fires >= 5 and aim_ok, (fires, aim_ok)
    assert out is None and rec.feat_tries.get(("shoot", 0, 0)) == 1, "did not stop after its seconds"
    assert b.shot_trial([18.0, 0.0, 1.0], rec, T) is None, "replays the same recipe twice in a match"
    # once a match: one bot claims a shot, a failed try frees it, a done one is never picked again
    rec2 = lidar.Recorder(MAP, count_run=False)
    rec2.shot_recipes = [dict(rec.shot_recipes[0])]
    b1, b2 = lidar.Roomba(1, random.Random(1)), lidar.Roomba(2, random.Random(2))
    t1 = b1.shot_trial([18.0, 0.0, 1.0], rec2, T)
    assert t1 is not None and b2.shot_trial([18.0, 0.0, 1.0], rec2, T) is None, "two bots on one shot"
    b1.trial = t1
    b1.tried_feat(t1, rec2)                            # b1 failed (died, no way there): free again
    t2 = b2.shot_trial([18.0, 0.0, 1.0], rec2, T)
    assert t2 is not None, "a failed claim was not freed"
    rec2.shot_done.add(0)                              # someone opened it
    b2.trial, b2.phase, b2.on_t = t2, "on", 0.0
    assert b2.shoot_steer(1.0, list(stand), rec2, T, t2) is None, "kept shooting a done shot"
    assert b1.shot_trial([18.0, 0.0, 1.0], rec2, T) is None, "picked a done shot"

    # a skilled player's recording is done for this match
    live3, sent3 = FakeLive(), []
    rec3 = lidar.Recorder(MAP, count_run=False)
    sh3 = lidar.ShotRec(live3, MAP, lambda a, b: sent3.append(a), rec3)
    sh3.path = os.path.join(tempfile.mkdtemp(), "shots.json")
    sh3.key(0.0, person)
    live3.objs[60] = (5, (0.3, 0.4, 0.6))
    sh3.update(0.1, person)
    del live3.objs[60]
    sh3.update(0.2, person)
    sh3.key(0.5, person)
    assert rec3.shot_done == {len(rec3.shot_recipes) - 1}, rec3.shot_done

    # anyone does it: the damage field drops by the player's amount, or enough bullets end on the
    # target
    live4 = FakeLive()
    rec4 = lidar.Recorder(MAP, count_run=False)
    rec4.shot_recipes = [dict(target=[3.0, 4.0, 0.6], damage=dict(type=8, pos=[3.0, 4.0, 0.6], offset=0x5fc, drop=36.0)),
                         dict(target=[9.0, 9.0, 1.0], damage=None,
                              shots=[dict(impact=[9.0, 9.0, 1.0])] * 3)]
    sh4 = lidar.ShotRec(live4, MAP, lambda a, b: None, rec4)
    live4.poke(2, 0x5fc, -10.0)
    sh4.watch(0.0)                                     # the match's starting value
    live4.poke(2, 0x5fc, -50.0)                        # another player shot it: 40 >= 36
    for k in range(3):                                 # three bullets end on the second target
        live4.objs[70 + k] = (5, (9.0, 9.0, 1.0))
        sh4.watch(1.0 + k * 0.1)
        del live4.objs[70 + k]
        sh4.watch(1.05 + k * 0.1)
    sh4.watch(5.0)
    assert rec4.shot_done == {0, 1}, rec4.shot_done
    print("shot recipes OK")


if __name__ == "__main__":
    main()
