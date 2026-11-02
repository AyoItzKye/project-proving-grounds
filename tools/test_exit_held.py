"""Offline check of the map brain's held-exit rule (Bot.exit_held: INTER-LIFT-01, INTER-CANNON-02, MOVE-01/02).
On real level data find two big drops people could take (a ledge 2.2-5 units over the floor below, 1-2.5 units
out): one with a short way round, one without. Add each as a person's link and check that a Normal bot at the
take-off: drops when nobody is known at the landing (and when the sighting is 10 s old); with an enemy seen at
the landing walks the way round (first drop) or waits at the edge and drops after 6 s (second); an Easy bot drops
anyway (Easy never plans a detour); a man 5-20 u off with a line of sight onto the landing holds it too, one as far
off behind a wall does not.

usage: python -I test_exit_held.py      -> "exit held OK"
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import Terrain  # noqa: E402

MAPS = ("h2a_ca_ascension", "h3_construct", "h2_lockout", "reach_35_island")


def find_drops(m, rng):
    """{"round": (T, a, b), "wait": (T, a, b)}: take-off and landing points of a big drop with a way round no more
    than 2.5 times as long, and one with none that short, each on its own Terrain with the drop added as a link and
    offered by the nav at the take-off."""
    found = {}
    spawns = [p for mode in m["spawns"].values() for team in mode.values() for p in team]
    base = Terrain(m["heightmap"], m["bases"])
    base.set_spawns(spawns)
    ls, js, is_ = np.nonzero(base.lwalk & base.reach)
    for _ in range(20000):
        if len(found) == 2:
            break
        k = rng.randrange(len(ls))
        src = (int(ls[k]), int(js[k]), int(is_[k]))
        dj, di = rng.randint(-10, 10), rng.randint(-10, 10)
        if not 16 <= dj * dj + di * di <= 100:
            continue
        j, i = src[1] + dj, src[2] + di
        if not (0 <= j < base.nh and 0 <= i < base.nw):
            continue
        for l in range(base.L):
            if not (base.lwalk[l, j, i] and base.reach[l, j, i] and 2.2 <= base.lz[src] - base.lz[l, j, i] <= 5.0):
                continue
            a, b = base._center(*src), base._center(l, j, i)
            w = math.hypot(b.x - a.x, b.y - a.y) * 1.5 + 1.0
            walk = float(base._field(b)[src])
            kind = "round" if w + 2.0 < walk <= 2.5 * w + 12.0 else "wait" if walk > 2.5 * w + 20.0 else None
            if kind is None or kind in found:
                continue
            T = Terrain(m["heightmap"], m["bases"])
            T.set_spawns(spawns)
            if T.add_human_links([dict(take_off=[a.x, a.y, a.z], land=[b.x, b.y, b.z], human=1)]) != 1:
                continue
            if hasattr(T.nav(a, b, human=True), "sx"):
                found[kind] = (T, a, b)
    return found


def watch_spots(T, b, rng):
    """Floor 5-20 u off the landing b (5+ u on the flat: outside the near radius) with a line of sight onto it, and
    floor as far off with none (None where none found)."""
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    see = hide = None
    for k in rng.sample(range(len(ls)), len(ls)):
        q = T._center(int(ls[k]), int(js[k]), int(is_[k]))
        if (q - b).flat() > 5.0 and dist(q, b) < 20.0:
            if T.los(q, b):
                see = q if see is None else see
            else:
                hide = q if hide is None else hide
        if see is not None and hide is not None:
            break
    return see, hide


def step(bot, T, a, b, now):
    bot.now = now
    act = Action(yaw=0.0)
    bot.move_to(PlayerState(1, 0, "bot", a, yaw=0.0), b, act, lambda p, q, **k: T.nav(p, q, **k))
    return act


def fresh(m, T, tier, enemy_at=None, seen=0.0):
    bot = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), m, random.Random(1))
    bot._terrain = T
    if enemy_at is not None:
        bot.per.beliefs[7] = Belief(pos=enemy_at, vel=Vec(0, 0, 0), t=seen, seen=True, source="eyes")
    return bot


def main():
    fails, used = [], None
    for name in MAPS:
        m = get_map(name)
        drops = find_drops(m, random.Random(3))
        if len(drops) == 2:
            used = name
            break
    if used is None:
        sys.exit("FAIL: no map with both kinds of test drop")
    now, watched, hidden = 100.0, [], []
    for kind, (T, a, b) in drops.items():
        if not step(fresh(m, T, "average"), T, a, b, now).jump:
            fails.append(f"{kind}: no enemy, did not drop")
        if not step(fresh(m, T, "average", b, now - 10.0), T, a, b, now).jump:
            fails.append(f"{kind}: a 10 s old sighting held the drop")
        if not step(fresh(m, T, "novice", b, now), T, a, b, now).jump:
            fails.append(f"{kind}: Easy took a detour")
        assault = fresh(m, T, "top", b, now)          # an Invasion attacker in phase 3 (Bot.think sets it): the
        assault.assaulting = True                     # defenders hold the top by design; its way up is taken at once
        if not step(assault, T, a, b, now).jump:      # (live Spire: 6 s at each man cannon)
            fails.append(f"{kind}: a phase 3 Invasion attacker held back from the drop")
        # INTER-LIFT-01 "or holds a sightline onto it": a man 5-20 u off who sees the landing holds it; one as far off
        # behind a wall does not (the second drop lands in a hole no floor 5-20 u off sees)
        see, hide = watch_spots(T, b, random.Random(5))
        if see is not None:
            watched.append(kind)
            if step(fresh(m, T, "average", see, now), T, a, b, now).jump:
                fails.append(f"{kind}: dropped with a man {dist(see, b):.1f} u off watching the landing")
        if hide is not None:
            hidden.append(kind)
            if not step(fresh(m, T, "average", hide, now), T, a, b, now).jump:
                fails.append(f"{kind}: a man {dist(hide, b):.1f} u off with no sight of the landing held the drop")
        bot = fresh(m, T, "average", b + Vec(1.0, 0.0, 0.0), now)
        act = step(bot, T, a, b, now)
        if act.jump:
            fails.append(f"{kind}: dropped onto a known enemy")
        elif kind == "round":
            if getattr(bot, "round_until", 0.0) <= now or (act.forward == 0.0 and act.strafe == 0.0):
                fails.append("round: did not take the way round")
            if step(bot, T, a, b, now + 1.0).jump:
                fails.append("round: dropped while walking round")
            humans = []                                   # a goal elsewhere gets people's jumps back at once
            bot.now = now + 2.0
            bot.move_to(PlayerState(1, 0, "bot", a, yaw=0.0), b + Vec(8.0, 0.0, 0.0), Action(yaw=0.0),
                        lambda p, q, **k: (humans.append(k.get("human")), T.nav(p, q, **k))[1])
            if not humans or not humans[0]:
                fails.append("round: a new goal still kept off people's jumps")
        else:
            if act.forward != 0.0 or act.strafe != 0.0:
                fails.append("wait: moved instead of waiting at the edge")
            t, jumped = now, None
            while t < now + 8.0 and jumped is None:
                t += 0.5
                bot.per.beliefs[7].t = t                  # still seen there
                if step(bot, T, a, b, t).jump:
                    jumped = t - now
            if jumped is None or not 6.0 <= jumped <= 7.0:
                fails.append(f"wait: dropped after {jumped} s, not after the 6 s wait")
    # Bot.think sets it: an Invasion attacker (the bot's team, 0) in phase 3 only; not in phase 2, not a defender,
    # not in another mode
    for mode, phase, attackers, want in (("invasion", 3, 0, True), ("invasion", 2, 0, False),
                                         ("invasion", 3, 1, False), ("slayer", 3, 0, False)):
        tb = fresh(m, T, "top")
        snap = Snapshot(now, [PlayerState(1, 0, "bot", a, yaw=0.0)], mode=mode, inv_phase=phase,
                        inv_attackers=attackers)
        tb.think(now, 1 / 30, snap, T.los, lambda p, q, **k: T.nav(p, q, **k), [])
        if getattr(tb, "assaulting", None) is not want:
            fails.append(f"Bot.think in {mode}, phase {phase}, attackers {attackers} (the bot's team 0): "
                         f"assaulting {getattr(tb, 'assaulting', None)}, want {want}")
    if not watched or not hidden:
        fails.append(f"test premise: landings seen from 5-20 u off {watched}, hidden from there {hidden} (want one each)")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print(f"exit held OK ({used}: a drop with a way round, a drop without; a man watching the landing of {watched})")


if __name__ == "__main__":
    main()
