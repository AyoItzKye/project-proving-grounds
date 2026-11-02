"""Vehicle target scoring (docs/research/17-vehicle-tactics-guide.md §4.2, §4.4, §4.5), on the seats' picks:

1. a Banshee pilot takes an enemy Banshee 30 u off over a man on foot 10 u off (air targets x2)
2. a Gauss gunner takes a Warthog 25 u off over a man 10 u off (vehicles x1.5, men x0.5)
3. Reach's rocket hog gunner holds fire on a man on foot ("hold fire on ground targets") and takes a Ghost; CE's shoots
   the man
4. a chaingun gunner takes our flag's carrier 20 u off over a man 10 u off (objective weight 2)
5. ... and a man with a rocket launcher over one with a rifle at the same distance (base threat 0.9 / 0.3)
6. Halo 3's tank gunner shoots the man on the hull before a Banshee 20 u off (its standing order); Reach's the Banshee
7. a cannon behind an enemy tank aims at its back hatch, not its middle; in front of it, its middle
8. a Wraith's mortar takes a man standing still over a running one

usage: python -I test_vehicle_targets.py      -> "vehicle targets OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("bloodgulch")
A = Vec(60.0, -100.0, 0.0)


def game(name):
    return dict(M, name=name)


def pick(g, kind, seat, foes, extra=(), flags=None, turret=""):
    """The seat's pick among foes (PlayerStates, all in sight); extra: their vehicles."""
    b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), g, random.Random(1))
    b.seat = seat
    for f in foes:
        b.per.beliefs[f.id] = Belief(f.pos, f.vel, 10.0, True, "eyes")
        b.per.recognized.add(f.id)
    me = PlayerState(1, 0, "me", A, vehicle=5, gunner_seat=seat == "gunner", turret=turret)
    v = dict(handle=5, kind=kind, pos=(A.x, A.y, A.z), riders=2, occupied=True, fwd=(1.0, 0.0, 0.0), turrets=[],
             manned=[], gunner=seat == "gunner", team=0)
    snap = Snapshot(10.0, [me] + list(foes), flags=flags or {}, vehicles=[v] + list(extra))
    seen = [f.id for f in foes]
    return (b.crew_target(me, snap, v, seen, own=True) if seat == "gunner" else
            b.vehicle_pick(me, v, "driver", seen, snap)), b, me, snap


def foe(pid, at, weapon="assault_rifle", vehicle=-1, **kw):
    return PlayerState(pid, 1, f"f{pid}", at, weapon=weapon, weapons=[weapon], vehicle=vehicle, **kw)


def veh(h, kind, at, fwd=(1.0, 0.0, 0.0)):
    return dict(handle=h, kind=kind, pos=(at.x, at.y, at.z), riders=1, occupied=True, fwd=fwd, team=1)


def main():
    fails = []
    R, CE, H3 = game("reach_35_island"), M, game("h3_valhalla")
    # 1. Banshee: air first
    got, *_ = pick(R, "banshee", "driver", [foe(2, A + Vec(30, 0, 5), vehicle=8), foe(3, A + Vec(10, 0, 0))],
                   [veh(8, "banshee", A + Vec(30, 0, 5))])
    if got != 2:
        fails.append(f"Banshee pilot took {got} (want 2, the enemy Banshee)")
    # 2. Gauss: the Warthog
    got, *_ = pick(R, "gauss", "gunner", [foe(2, A + Vec(25, 0, 0), vehicle=8), foe(3, A + Vec(10, 0, 0))],
                   [veh(8, "warthog", A + Vec(25, 0, 0))])
    if got != 2:
        fails.append(f"Gauss gunner took {got} (want 2, the Warthog)")
    # 3. rocket hog: Reach holds on men, takes a Ghost; CE shoots the man
    got, *_ = pick(R, "rwarthog", "gunner", [foe(3, A + Vec(10, 0, 0))])
    if got is not None:
        fails.append(f"Reach rocket hog gunner took a man on foot ({got}; want holding fire)")
    got, *_ = pick(R, "rwarthog", "gunner", [foe(2, A + Vec(25, 0, 0), vehicle=8), foe(3, A + Vec(10, 0, 0))],
                   [veh(8, "ghost", A + Vec(25, 0, 0))])
    if got != 2:
        fails.append(f"Reach rocket hog gunner took {got} (want 2, the Ghost)")
    got, *_ = pick(CE, "rwarthog", "gunner", [foe(3, A + Vec(10, 0, 0))])
    if got != 3:
        fails.append(f"CE rocket hog gunner took {got} (want 3, the man)")
    # 4. the carrier
    got, *_ = pick(R, "warthog", "gunner", [foe(2, A + Vec(20, 0, 0), has_flag=True), foe(3, A + Vec(10, 0, 0))])
    if got != 2:
        fails.append(f"chaingun gunner took {got} (want 2, the flag carrier)")
    # 5. the rocket man
    got, *_ = pick(R, "warthog", "gunner", [foe(2, A + Vec(0, 12, 0), weapon="rockets"), foe(3, A + Vec(12, 0, 0))])
    if got != 2:
        fails.append(f"chaingun gunner took {got} (want 2, the man with the rocket launcher)")
    # 6. the tank gunner's hull rule: Halo 3 yes, Reach by the scores
    for g, want in ((H3, 3), (R, 2)):
        got, *_ = pick(g, "scorpion", "gunner", [foe(2, A + Vec(20, 0, 6), vehicle=8), foe(3, A + Vec(1.5, 0, 1))],
                       [veh(8, "banshee", A + Vec(20, 0, 6))])
        if got != want:
            fails.append(f"{g['name']} Scorpion gunner took {got} (want {want})")
    # 7. the back hatch: behind an enemy Scorpion facing north at (20, 5) -> its rear (20, 4.2); in front of one facing
    #    south, its middle
    for fwd, want in (((0.0, 1.0, 0.0), Vec(20.0, 4.2, 0.0)), ((0.0, -1.0, 0.0), Vec(20.0, 5.0, 0.0))):
        t = foe(2, A + Vec(20, 5, 0), vehicle=8)
        _, b, me, snap = pick(R, "scorpion", "driver", [t], [veh(8, "scorpion", A + Vec(20, 5, 0), fwd=fwd)])
        q = b.weak_point(me, 2, b.per.beliefs[2], snap, "cannon")
        if (q - (A + want)).length() > 0.05:
            fails.append(f"cannon on an enemy Scorpion facing {fwd[:2]}: aimed at {q - A} (want {want})")
    # 8. the Wraith's mortar: the man standing still
    still, run = foe(2, A + Vec(20, 3, 0)), foe(3, A + Vec(20, -3, 0), vel=Vec(0.0, 2.2, 0.0))
    got, *_ = pick(R, "wraith", "driver", [still, run])
    if got != 2:
        fails.append(f"Wraith mortar took {got} (want 2, the man standing still)")
    if fails:
        print("vehicle targets FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("vehicle targets OK")


if __name__ == "__main__":
    main()
