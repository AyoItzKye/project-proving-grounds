"""The Nov 4 Infection / Flood playtests (Halo 3 Deadlock, Halo 4 Blood Cavern x2 and Creeper), each part failing
on the code before:
1. the infected never go for guns lying about (Halo 3's zombies chose items 49% of their decisions)
2. an infected with a thruster (or Reach's evade) in a fight 6.5-11 u from a survivor dashes in at him (13-21 thrusts in
   16-20 Flood bot-minutes, 213-274 s a game closing within 4-14 u)
3. a survivor with a thruster thrusts sideways out of a lunge, cover or not (162-231 s a game with a Flood within 4.5 u,
   no thrust away)
4. a survivor never dashes in onto a sword (shotgun survivors dashed into the Flood)
5. an infected waits at one corner AMBUSH_S at most (waits of 53-279 s)

usage: python -I test_infection_pressure.py      -> "infection pressure OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from test_equipment import A, bot, foe, plan_now  # noqa: E402


def main():
    fails, info = [], []
    # 1. an infected bot, a gun lying 3 u off scored high (best_item), a survivor known far off
    rn = get_map("h3_armory")
    b = Bot(5, 1, make_profile("top", "rusher", random.Random(5)), rn, random.Random(5))
    b.game = "h3"
    here = Vec(-4.6, -1.4, -1.2)
    b.best_item = lambda now, me: (here + Vec(3, 0, 0), 2.5)
    b.order = Order("hunter", Vec(4.4, 22.6, -8.6))
    me = PlayerState(5, 1, "z", here, weapon="sword", weapons=["sword"])
    surv = PlayerState(2, 0, "s", Vec(4.4, 22.6, -8.6), weapon="shotgun")
    b.per.beliefs[2] = Belief(surv.pos, Vec(), 0.5, False, "radar")
    snap = Snapshot(1.0, [me, surv], mode="infection")
    snap.infected = 1
    g = b.decide(1.0, me, snap)
    info.append(f"infected with a gun lying by: {g[0]}")
    if g[0] in ("item", "vehicle", "retreat", "hold"):
        fails.append(f"an infected chose {g[0]} (want the hunt)")
    # ... a survivor still takes it
    b2 = Bot(6, 0, make_profile("top", "rusher", random.Random(6)), rn, random.Random(6))
    b2.game = "h3"
    b2.best_item = lambda now, me: (here + Vec(3, 0, 0), 2.5)
    me2 = PlayerState(6, 0, "s", here, weapon="shotgun", weapons=["shotgun"])
    if b2.decide(1.0, me2, Snapshot(1.0, [me2], mode="infection"))[0] != "item":
        fails.append("a survivor no longer takes a gun lying by")
    # 2. the infected's dash in
    for game, kind in (("h4", "thruster"), ("reach", "evade")):
        z = bot("top", game, kind)
        man = foe(A + Vec(8.0, 0, 0), yaw=math.pi, weapon="shotgun")
        p = plan_now(z, [man], (2,), ("fight", 2), me_kw=dict(weapon="sword"), mode="infection")
        info.append(f"{game} infected at 8 u: {p[4]}")
        if p[0] != kind or p[1] != "dash" or (p[2] - A).x < 2.5:
            fails.append(f"{game} infected {kind} at 8 u: {p} (want a dash in at him)")
        far = plan_now(bot("top", game, kind), [foe(A + Vec(16.0, 0, 0), weapon="shotgun")], (2,), ("fight", 2),
                       me_kw=dict(weapon="sword"), mode="infection")
        if far[0] is not None and far[1] == "dash":
            fails.append(f"{game} infected dashed at 16 u (want the last 11 u only)")
    # 3. a survivor's thrust out of a lunge (open gulch: no cover)
    s = bot("top", "h4", "thruster")
    s.cover_from = lambda me, threats: None
    z = foe(A + Vec(3.0, 0, 0), yaw=math.pi, weapon="sword")
    p = plan_now(s, [z], (2,), ("fight", 2), me_kw=dict(weapon="shotgun"), mode="infection")
    info.append(f"survivor, a Flood lunging at 3 u: {p[4]}")
    if p[0] != "thruster" or p[1] != "dash" or abs((p[2] - A).y) < 2.0:
        fails.append(f"survivor thruster, a Flood lunging at 3 u: {p} (want a thrust sideways)")
    # 4. never in onto a sword (a Flood 5 u off looking away: no lunge coming)
    s = bot("top", "h4", "thruster")
    z = foe(A + Vec(5.0, 0, 0), yaw=0.0, weapon="sword")
    p = plan_now(s, [z], (2,), ("fight", 2), me_kw=dict(weapon="shotgun"), mode="infection")
    if p[4] == "dash in to close":
        fails.append("a survivor with a shotgun dashed in onto a Flood")
    # 5. one corner AMBUSH_S at most, then free again after as long
    d = D.Director(1, rn, {})
    q = Vec(3.4, 7.1, -8.3)
    got = [d.ambush_fresh(t, q) for t in (0.0, D.AMBUSH_S - 1, D.AMBUSH_S + 1, 2 * D.AMBUSH_S + 1)]
    if got != [True, True, False, True]:
        fails.append(f"ambush corner over time: {got} (want waited {D.AMBUSH_S:.0f} s, then left as long)")
    # 6. (the Rat's Nest flags) round 1's zombie tag learned, round 2's zombies hold a sword of another tag:
    #    by name they are the infected
    from brain import modes
    w3 = modes.Watch("infection", {}, "h3")
    ps = [PlayerState(i, i, "p", Vec(), weapon="sword" if i == 0 else "shotgun") for i in range(6)]
    w3.update(None, Snapshot(0.0, ps), 0.0, raw=[dict(index=i, pos=(0, 0, 0), wtag=0xAA if i == 0 else 0xBB) for i in range(6)])
    ps = [PlayerState(i, i, "p", Vec(), weapon="sword" if i in (2, 4) else "shotgun") for i in range(6)]
    sn = Snapshot(9.0, ps)
    w3.update(None, sn, 9.0, raw=[dict(index=i, pos=(0, 0, 0), wtag=0xCC if i in (2, 4) else 0xBB) for i in range(6)])
    if [p.team for p in sn.players] != [0, 0, 1, 0, 1, 0]:
        fails.append(f"Halo 3 round 2, swords of a new tag: teams {[p.team for p in sn.players]} (want the sword holders 1)")
    # 7. (the Ragnarok flag 590.6 s) an infected at its corner fights a survivor 8 u off, 12 u from the corner:
    #    it runs at him; a survivor at its post still holds
    for team, weapon, want in ((1, "sword", True), (0, "shotgun", False)):
        cm = get_map("h3_construct")
        b = Bot(7, team, make_profile("top", "rusher", random.Random(7)), cm, random.Random(7))
        b.game = "h3"
        post = Vec(-2.0, -4.3, 6.4)
        here, him = Vec(-2.0, 7.7, 6.4), Vec(6.0, 7.7, 6.4)
        b.order = Order("defender", post)
        b.goal, b.next_decide = ("fight", 2), 1e9
        b.per.beliefs[2] = Belief(him, Vec(), 1.0, True, "eyes")
        b.per.recognized.add(2)
        fwd = []
        for k in range(15):
            t = 1.0 + k / 30
            b.per.last_seen[2] = t
            me = PlayerState(7, team, "bot", here, weapon=weapon, weapons=[weapon], ammo=[-1], mag=[-1], yaw=0.0)
            foe_ = PlayerState(2, 1 - team, "s", him, yaw=math.pi, weapon="shotgun" if team else "sword")
            sn = Snapshot(t, [me, foe_], mode="infection")
            sn.infected = 1
            a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **k: q, [])
            fwd.append(a.forward)
        f = sum(fwd) / len(fwd)
        info.append(f"{weapon} defender, a man 8 u off: forward {f:.2f}")
        if (f > 0.5) != want:
            fails.append(f"Infection {weapon} at a post, a man 8 u off: forward {f:.2f} (want {'run at him' if want else 'hold'})")
    if fails:
        sys.exit("\n".join("FAIL: " + f for f in fails))
    print("infection pressure OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
