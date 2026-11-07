"""Firefight teammates (Nov 6): they follow the player around; if the player dies they roam or find a safe spot. With
the player alive every bot escorts the player; with the player down they hold the map's two safe spots nearest where
the player fell (its holds and named points), split between them, not the open middle.

usage: python -I tools/test_firefight_team.py      -> "firefight team OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.bot import Belief, Bot  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.maps import get_map  # noqa: E402

M = get_map("reach_ff20_courtyard")


def main():
    fails = []
    d = Director(0, M, {}, random.Random(1))
    me = Vec(-101.0, 36.0, 19.0)
    human = PlayerState(0, 0, "you", me, is_bot=False)
    bots = [PlayerState(i, 0, f"b{i}", me + Vec(i, 0, 0)) for i in (1, 2, 3)]
    sn = Snapshot(10.0, [human] + bots, mode="firefight")
    slots = d.role_slots(10.0, sn, 3)
    if any(r != "escort" or dist(p, me) > 0.01 for r, p, _ in slots):
        fails.append(f"player alive: {slots} (want 3 escorts on him)")
    dead = PlayerState(0, 0, "you", me, is_bot=False, alive=False)
    sn = Snapshot(14.0, [dead] + bots, mode="firefight")
    slots = d.role_slots(14.0, sn, 3)
    spots = sorted([q for h in M["holds"].values() for q in h] + list(M["points"].values()), key=lambda q: dist(q, me))
    pts = {(round(p.x, 2), round(p.y, 2)) for _, p, _ in slots}
    want = {(round(q.x, 2), round(q.y, 2)) for q in spots[:2]}
    if any(r != "defender" for r, _, _ in slots) or pts != want:
        fails.append(f"player down: {[(r, p) for r, p, _ in slots]} (want defenders on the 2 spots nearest him {want})")
    if dist(M["points"]["mid"], me) > 5.0 and any(dist(p, M["points"]["mid"]) < 0.5 for _, p, _ in slots):
        fails.append("player down: a bot sent to the open middle")
    # the orders themselves (live Beachhead Nov 6, s172: with him standing at the start the three roamed 25-45 u off,
    # their escort orders named nobody, Order.target -1, so Bot.lead had no one and the escort leash never held): every
    # bot, Easy too, escorts the person by name
    tiers = ("novice", "average", "top")
    team = {i: Bot(i, 0, make_profile(t, "rusher", random.Random(i)), M, random.Random(i)) for i, t in zip((1, 2, 3), tiers)}
    d = Director(0, M, team, random.Random(1))
    sn = Snapshot(20.0, [human] + bots, mode="firefight")
    d.assign_roles(20.0, sn)
    for i, b in team.items():
        lead = b.lead(sn.player(i), sn)
        if b.order.role != "escort" or lead is None or lead.id != 0:
            fails.append(f"bot {i} ({tiers[i - 1]}): order {b.order.role} target {b.order.target} (want escort, lead you)")
    # and the team's vehicle picks do not take them off him (the same match: 3175 of their order rows were "drive", to
    # Mongooses 20-40 u off, 724 escort; director.crew_orders counted escorts as free bots)
    hog = dict(handle=77, kind="warthog", pos=(me.x + 6, me.y, me.z), riders=0, occupied=False, team=-1, gunner=False,
               turrets=[], manned=[], fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), left=1.0, dead=False)
    sn = Snapshot(22.0, [human] + bots, mode="firefight", vehicles=[hog])
    d.assign_roles(22.0, sn)
    d.vehicle_orders(22.0, sn, list(team.values()))
    if any(b.order.role != "escort" for b in team.values()):
        fails.append(f"an empty Warthog by them: orders {[(i, b.order.role) for i, b in team.items()]} (want all escort)")
    # nor their own goals: a hunt 30 u off with an empty Warthog by them is walked (live Beachhead s178: a bot left for
    # a Mongoose on a far hunt, 596 rows; driving, they went into walls, GitHub #12)
    # (the live frame, t 89.3: shot by an unseen Elite 35.5 u off, bot 3 turned to hunt him, then took a Mongoose)
    b3, picks = team[3], set()
    sn2 = Snapshot(22.5, [human] + bots, mode="firefight", vehicles=[hog])
    for k in range(12):
        t = 22.5 + k * 0.5
        b3.goal, b3.vehicle_retry_at = ("roam", None), 0.0
        b3.per.beliefs[1050] = Belief(me + Vec(-40.0, 0.0, 0.0), Vec(), t, False, "hit")
        b3.per.attacker_id, b3.per.attacker_t, b3.per.attacker_notice = 1050, t, 0.0
        picks.add(b3.decide(t, sn2.player(3), sn2)[0])
    if "vehicle" in picks or "hunt" not in picks:
        fails.append(f"an escort's own goals with an empty Warthog by it: {sorted(picks)} (want hunt, no vehicle)")
    # where each goes: a step behind him, three spots apart (the fixed match: median 0.2-0.7 u from him, standing on him)
    spots = [b.live_point(sn.player(i), sn) for i, b in team.items()]
    behind = Vec(-1.0, 0.0, 0.0)                                   # (he faces +x: yaw 0)
    if any(q is None or not 2.0 < dist(q, me) < 4.5 or (q - me).x * behind.x <= 0 for q in spots) or \
            min(dist(a, b) for k, a in enumerate(spots) for b in spots[k + 1:]) < 1.5:
        fails.append(f"escort spots {spots} (want 2-4.5 u behind him, 1.5 u apart)")
    # the live state (Beachhead s173, trace 20261106-033841): he stood at the start, facing -2.56, the spot straight
    # behind him off the walkable floor, and all three were sent onto him (objective 0.00 u from him in 1275-1357 rows)
    park = get_map("reach_ff50_park")
    at = Vec(-162.77, 60.1, -33.5)
    you = PlayerState(0, 0, "you", at, is_bot=False, yaw=-2.56)
    mates = [PlayerState(i, 0, f"b{i}", at + Vec(0.5 * i, 0, 0)) for i in (1, 2, 3)]
    crew = {i: Bot(i, 0, make_profile("top", "rusher", random.Random(i)), park, random.Random(i)) for i in (1, 2, 3)}
    d = Director(0, park, crew, random.Random(1))
    sn = Snapshot(30.0, [you] + mates, mode="firefight")
    d.assign_roles(30.0, sn)
    spots = [b.live_point(sn.player(i), sn) for i, b in crew.items()]
    if any(q is None or dist(q, at) < 2.0 for q in spots) or \
            min(dist(a, b) for k, a in enumerate(spots) for b in spots[k + 1:]) < 1.5:
        fails.append(f"Beachhead start: escort spots {spots} (want 2+ u off him on walkable floor, 1.5 u apart)")
    if fails:
        print("firefight team FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("firefight team OK")


if __name__ == "__main__":
    main()
