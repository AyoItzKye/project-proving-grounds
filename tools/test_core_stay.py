"""A bot on a loose objective it works by standing on it stays on it until the job is done (Bot.stand_point / stay_at):
the dropped Invasion core a defender returns or an attacker picks up, Breakpoint's bomb the same, a CTF flag of ours
dropped. It fights from on it; it leaves only to save its life (shield gone, body under half, a man in sight).

Live Spire, owner bug reports 20261105-143525 at 1011.1 s ("No one is recovering the core") and 1017.3 s ("they will go
to the core, then go somewhere else before the core is done recovering"); trace in the main repo
logs/bug_reports/reach_35_island_20261105-143525. The core dropped at 992.1 s at (-161.66, -422.55, -60.08) and lay
there 129 s (the defenders never returned it, the attackers took it at 1121.2 s). 26 defender visits within 2 u, the
longest 10.0 s, the median 1.8 s, each ended by (logs/tmp/core_stay/visits.py):
  1. a new post: #9 0.09 u off it at 1071.3 s, its order moved to a guard spot (-159.6, -426.1) 4.3 u off (#1 at
     1015.8 and 1074.8 s the same)
  2. a gun: #1 at 1026.8 s, a gun 5 u off 1.9 over the core 0.96 (#1 again at 1100.0 s)
  3. a fight: #11 at 1040.5 s fight #6 2.94 over the core 1.12, out 2-6 s at a time (#3 at 1090.9 and 1107.2 s)
  4. a reposition: #9 at 1056.4 s "a kill: off this spot" retreat 2.6
The attacker #6 at 1117.3 s 1.6 u off the loose core fought #7 (3.24) before it took it.

usage: python -I test_core_stay.py      -> "core_stay OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = "reach_35_island/variants/v3977bae2"
CORE = Vec(-161.66, -422.55, -60.08)          # where it lay 992-1121 s
STAND = Vec(-178.24, -405.33, -22.9)          # its stand (the world rows at 960 s)
DELIVER = Vec(-163.053, -432.088, -58.371)
GUARD = Vec(-159.64, -426.07, -59.12)         # #9's new post at 1071.3 s
FEET = -60.66                                 # #9's feet there
RUN = 2.3                                     # u/s on foot


def snap(t, players, attackers=1):
    sn = Snapshot(t, players, mode="invasion", inv_phase=3, inv_attackers=attackers, inv_core=CORE,
                  inv_core_carrier=None, inv_delivery=DELIVER, inv_zones=[DELIVER], inv_zone_r=[1.5], inv_phase_t=150.0)
    sn.inv_stand = STAND
    return sn


def run(bid, team, pers, order, start, secs=4.0, foes=(), ground=(), shield=1.0, health=1.0, mode="invasion",
        flags=None, extra=None):
    """Ticks of Bot.think at 30 Hz from start, the bot moved by its own input; foes [(id, pos)] stand still in sight.
    -> (largest flat distance from the objective, first tick it pressed Use within 0.9 u of it or None, the goals)."""
    m = get_map(M)
    b = Bot(bid, team, make_profile("top", pers, random.Random(bid)), m, random.Random(bid))
    b.order = order
    if extra:
        extra(b)
    pos, yaw, far, used, goals = start, math.atan2(CORE.y - start.y, CORE.x - start.x), 0.0, None, []
    obj = CORE if mode == "invasion" else flags[team].pos
    for k in range(int(secs * 30)):
        t = 1071.3 + k / 30
        me = PlayerState(bid, team, "b", pos, yaw=yaw, shield=shield, health=health, weapon="plasma_repeater",
                         weapons=["plasma_repeater", "plasma_pistol"], ammo=[200, 100], mag=[100, 100])
        them = [PlayerState(i, 1 - team, "e", p, yaw=math.atan2(pos.y - p.y, pos.x - p.x)) for i, p in foes]
        if mode == "invasion":
            sn = snap(t, [me] + them, attackers=1)
        else:
            sn = Snapshot(t, [me] + them, flags=flags, mode="ctf")
        sn.ground_weapons = list(ground)
        a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
        goals.append(b.goal[0])
        if a.action and (pos - obj).flat() < 0.9 and used is None:
            used = round(t - 1071.3, 2)
        h, n = a.yaw + math.atan2(a.strafe, a.forward), min(1.0, math.hypot(a.forward, a.strafe))
        pos = Vec(pos.x + RUN * n * math.cos(h) / 30, pos.y + RUN * n * math.sin(h) / 30, pos.z)
        yaw = a.yaw
        far = max(far, (pos - obj).flat())
    return far, used, goals


def main():
    fails = []
    on = Vec(CORE.x + 0.09, CORE.y, FEET)
    # 1. #9 at 1071.3 s: on the core, its order moved to a guard spot 4.3 u off
    far, _, g = run(9, 0, "objector", Order("defender", GUARD), on)
    if far > 1.0:
        fails.append(f"defender on the core, its post moved 4.3 u off: went {far:.1f} u off the core (want <= 1.0)")
    # 2. #1 at 1026.8 s: a gun 5 u off (a DMR on its way, UPGRADE_ON_WAY)
    far, _, g = run(1, 0, "rusher", Order("defender", CORE), on, ground=[("dmr", Vec(-162.16, -417.42, -60.6))])
    if far > 1.0:
        fails.append(f"defender on the core, a gun 5 u off: went {far:.1f} u off for it (want <= 1.0)")
    # 3. #11 at 1040.5 s: an attacker in sight 9 u off, fought: from on the core
    foe = Vec(-168.7, -417.0, -60.6)
    far, _, g = run(11, 0, "flanker", Order("defender", CORE), on, foes=[(6, foe)])
    if "fight" not in g:
        fails.append("defender on the core, a man in sight 9 u off: never fought him")
    if far > 1.3:
        fails.append(f"defender on the core fighting a man 9 u off: fought {far:.1f} u off the core (want <= 1.3)")
    # 4. #9 at 1056.4 s: "a kill: off this spot" (relocate_point)
    moved = Vec(-161.6, -425.6, -59.1)
    far, _, g = run(9, 0, "objector", Order("defender", CORE), on,
                    extra=lambda b: setattr(b, "relocate_point", lambda now, me, sn: moved))
    if far > 1.0:
        fails.append(f"defender on the core, a reposition after a kill: went {far:.1f} u off (want <= 1.0)")
    # 5. ... but about to die (shield gone, body at 0.3, the man shooting in sight) it may save itself
    _, _, g = run(11, 0, "flanker", Order("defender", CORE), on, foes=[(6, Vec(-163.5, -421.0, -60.6)),
                                                                        (8, Vec(-160.0, -420.2, -60.6))],
                  shield=0.0, health=0.3)
    if "retreat" not in g and "fight" not in g:
        fails.append("defender on the core about to die: neither fought nor backed off")
    # 6. #6 at 1117.3 s: an attacker 1.6 u off the loose core in a fight with a defender 6 u off: takes it within 2 s
    _, used, g = run(6, 1, "flanker", Order("runner", CORE), Vec(CORE.x - 1.59, CORE.y, FEET), secs=2.0,
                     foes=[(7, Vec(-156.0, -424.0, -60.6))], extra=lambda b: setattr(b, "goal", ("fight", 7)))
    if used is None:
        fails.append("attacker 1.6 u off the loose core, a defender in sight: no pickup in 2 s")
    # 7. CTF: our flag dropped, the returner on it, a gun 5 u off
    home = Vec(-140.0, -400.0, -60.0)
    fl = {0: FlagState(0, home, Vec(CORE.x, CORE.y, -60.08), state="dropped"), 1: FlagState(1, STAND, STAND)}
    far, _, g = run(3, 0, "flanker", Order("hunter", home), on, mode="ctf", flags=fl,
                    ground=[("dmr", Vec(-162.16, -417.42, -60.6))])
    if far > 1.0:
        fails.append(f"CTF: on our dropped flag, a gun 5 u off: went {far:.1f} u off it (want <= 1.0)")
    far, _, g = run(3, 0, "flanker", Order("hunter", home), on, mode="ctf", flags=fl,
                    extra=lambda b: setattr(b, "relocate_point", lambda now, me, sn: moved))
    if far > 1.0:
        fails.append(f"CTF: on our dropped flag, a reposition after a kill: went {far:.1f} u off it (want <= 1.0)")
    if fails:
        print("core_stay FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("core_stay OK")


if __name__ == "__main__":
    main()
