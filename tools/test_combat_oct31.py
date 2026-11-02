"""the player's combat asks (five matches: The Pit and Avalanche CTF, Spire Invasion, Ascension Slayer; death
critiques in docs/oct31/combat.md), each part failing on the code before:
1. the energy sword charges into the man and presses every ~0.17 s in reach (Halo 3's reach 1.8 u); it stopped and
   strafed in reach with one press per 0.6 s (The Pit 199.95 s)
2. Normal and up strafe in every fight (no per-fight roll); Easy keeps its roll
3. Normal and up close the distance with an automatic, or on a man whose shield is down; Easy does not
4. Normal melees at arm's length on the lower shield; Easy still holds off
5. between fights the precision rifle comes out (Reach: needle rifle over the plasma repeater); Easy keeps its gun
6. back in the scope 0.5 s after a hit (Normal and up), Halo 4 at once; Easy waits as before
7. a sniper in hand hunts a man 10 u off far less than a rifleman (gun sense: hold the lane)
8. a Halo 3 Warthog gunner ("unknown" turret) aims from the chaingun's height, not the eye
9. a vehicle it cannot walk to (no step closer in 6 s) is given up, its drive order too (The Pit's corner)

usage: python -I test_combat_oct31.py      -> "combat oct31 OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

A = Vec(-2.0, 7.7, 6.4)          # Construct, red side's walk, one floor (tools/test_sword.py)
DT = 1 / 30
M = get_map("h3_construct")


def mk(tier="top", game="h3", i=5, pers="rusher"):
    b = Bot(i, 0, make_profile(tier, pers, random.Random(i)), M, random.Random(i))
    b.game, b.can_pickup = game, False
    return b


def fight(b, weapon, d, secs, foe_shield=1.0, my_shield=1.0, weapons=None):
    """Ticks of b fighting a man d u ahead (east, it faces him): [(forward, strafe, fire, melee)]."""
    man = Vec(A.x + d, A.y, A.z)
    b.per.beliefs[2] = Belief(man, Vec(), 0.0, True, "eyes")
    b.per.recognized.add(2)
    out, t = [], 0.0
    while t < secs:
        b.per.last_seen[2] = t
        me = PlayerState(b.id, 0, "bot", A, alive=True, weapon=weapon, weapons=weapons or [weapon], ammo=[-1] * len(weapons or [weapon]),
                         mag=[-1] * len(weapons or [weapon]), yaw=0.0, shield=my_shield)
        foe = PlayerState(2, 1, "human", man, alive=True, yaw=math.pi, shield=foe_shield, weapon="assault_rifle")
        a = b.think(t, DT, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        if b.goal == ("fight", 2):
            out.append((a.forward, a.strafe, bool(a.fire), bool(a.melee)))
        t += DT
    return out


def presses(ticks, k):
    return sum(1 for i, x in enumerate(ticks) if x[k] and (i == 0 or not ticks[i - 1][k]))


def mean(xs):
    return sum(xs) / max(1, len(xs))


def main():
    fails, info = [], []
    # 1. the sword in reach: forward, pressed again and again; Halo 3's longer reach
    ticks = fight(mk(), "sword", 1.5, 0.7)
    fwd, n = mean([x[0] for x in ticks]), presses(ticks, 2)
    info.append(f"sword at 1.5 u: forward {fwd:.2f}, {n} presses in 0.7 s")
    if fwd < 0.5 or n < 3:
        fails.append(f"sword at 1.5 u: forward {fwd:.2f}, {n} presses in 0.7 s (want forward 0.5+, 3+ presses)")
    if presses(fight(mk(), "sword", 1.75, 0.3), 2) < 1:
        fails.append("Halo 3 sword, a man 1.75 u ahead: no press (the owner's kills from 1.2-2.0 u)")
    if presses(fight(mk(game="reach"), "sword", 1.75, 0.3), 2) != 0:
        fails.append("Reach sword, a man 1.75 u ahead: pressed (Reach keeps 1.6 u)")
    # 2. strafing in every fight, Normal and up
    for tier, want_all in (("average", True), ("strong", True), ("novice", False)):
        rolls = []
        for k in range(40):                    # (a fresh bot a fight: its clocks start with the fight)
            b = mk(tier, i=30 + k)
            b.p.strafe = min(b.p.strafe, 0.6)  # (Easy's own 0.9 would roll all 40 now and then: the roll is what counts)
            if fight(b, "battle_rifle", 6.0, 2 * DT):
                rolls.append(b.strafing)
        if len(rolls) < 30:
            fails.append(f"{tier}: only {len(rolls)} of 40 fights started")
        if all(rolls) != want_all:
            fails.append(f"{tier}: strafed {sum(rolls)} of {len(rolls)} fights (want {'all' if want_all else 'some, not all'})")
    # 3. closing in: an AR at 3.5 u, a BR on a man with no shield at 6 u; a BR on a full shield holds its range
    for tier, w, d, sh, lo, hi in (("average", "assault_rifle", 3.5, 1.0, 0.5, 9), ("top", "assault_rifle", 3.5, 1.0, 0.5, 9),
                                   ("top", "battle_rifle", 6.0, 0.0, 0.5, 9), ("top", "battle_rifle", 6.0, 1.0, -9, 0.3),
                                   ("novice", "assault_rifle", 3.5, 1.0, -9, 0.3)):
        f = mean([x[0] for x in fight(mk(tier), w, d, 1.0, foe_shield=sh)])
        info.append(f"{tier} {w} {d} u shield {sh}: forward {f:.2f}")
        if not lo <= f <= hi:
            fails.append(f"{tier} {w} at {d} u, his shield {sh}: forward {f:.2f} (want {lo}..{hi})")
    # 4. melee at arm's length on the lower shield: Normal swings, Easy holds off
    for tier, want in (("average", True), ("novice", False)):
        n = presses(fight(mk(tier, i=18), "assault_rifle", 1.0, 3.0, my_shield=0.2), 3)
        if (n > 0) != want:
            fails.append(f"{tier} at 1 u on the lower shield: {n} melee presses (want {'some' if want else 'none'})")
    # 5. between fights the rifle comes out
    for tier, game, held, inv, want in (("average", "reach", "plasma_repeater", ["plasma_repeater", "needle_rifle"], "needle_rifle"),
                                         ("top", "reach", "assault_rifle", ["assault_rifle", "dmr"], "dmr"),
                                         ("top", "h3", "assault_rifle", ["assault_rifle", "battle_rifle"], "battle_rifle"),
                                         ("novice", "reach", "plasma_repeater", ["plasma_repeater", "needle_rifle"], "plasma_repeater")):
        b = mk(tier, game)
        b.switch_ok_at, b.notes = 0.0, []
        me = PlayerState(b.id, 0, "bot", A, alive=True, weapon=held, weapons=inv, ammo=[200, 200], mag=[30, 30])
        got = b.choose_weapon(10.0, me, "objective", A + Vec(20, 0, 0), Snapshot(10.0, [me]))
        got = held if got < 0 else inv[got]
        if got != want:
            fails.append(f"{tier} {game} between fights holding the {held}: {got} (want the {want})")
    # 6. the scope after a hit
    for tier, game, w, ago, want in (("average", "h3", "battle_rifle", 0.6, 1), ("top", "h4", "battle_rifle", 0.1, 1),
                                     ("top", "h3", "battle_rifle", 0.2, 0), ("novice", "h3", "sniper", 0.6, 0)):
        b = mk(tier, game)
        b.hit_at = 10.0 - ago
        z = b.zoom_level(10.0, w, 10.0, True)
        if z != want:
            fails.append(f"{tier} {game} {w}, hit {ago} s ago at 10 u: zoom {z} (want {want})")
    # 7. gun sense: a sniper hunts a man 10 u off less than a rifleman
    hunts = {}
    for w in ("sniper", "battle_rifle"):
        b = mk("top", pers="flanker")
        b.per.beliefs[2] = Belief(Vec(A.x + 10.0, A.y, A.z), Vec(), 9.5, False, "heard")
        me = PlayerState(b.id, 0, "bot", A, alive=True, weapon=w, weapons=[w])
        b.decide(10.0, me, Snapshot(10.0, [me, PlayerState(2, 1, "human", Vec(A.x + 10.0, A.y, A.z), alive=True)]))
        hunts[w] = max((v for k, v in b.last_scores.items() if k[0] == "hunt"), default=0.0)
    info.append(f"hunt score sniper {hunts['sniper']:.2f}, BR {hunts['battle_rifle']:.2f}")
    if not hunts["sniper"] < 0.6 * hunts["battle_rifle"]:
        fails.append(f"hunt a man 10 u off: sniper {hunts['sniper']:.2f}, BR {hunts['battle_rifle']:.2f} (want the sniper's under 60%)")
    # 8. Halo 3's unnamed turret: the chaingun's height by the vehicle's kind
    try:
        h = vehicles.gun_height("unknown", "warthog")
    except TypeError:
        h = None
    if h != 0.92 or vehicles.gun_height("warthog_chaingun") != 0.92 or vehicles.gun_height("unknown", "ghost") is not None:
        fails.append(f"gun height for an unknown turret on a Warthog: {h} (want 0.92; named guns as before)")
    # 9. a vehicle it cannot walk to: given up after 6 s, the drive order no longer brings it back for a while
    b = mk("top")
    hog = dict(handle=7, kind="warthog", pos=(A.x + 3.0, A.y, A.z), occupied=False, riders=0, fwd=(1.0, 0.0, 0.0))
    b.order, b.goal, b.next_decide = Order("drive", target=7), ("vehicle", 7), 0.0
    b.per.beliefs[2] = Belief(Vec(A.x - 30.0, A.y, A.z), Vec(), 0.0, False, "heard")   # something else to do (a hunt)
    t, gave_up, goals = 0.0, None, []
    while t < 9.0:
        me = PlayerState(b.id, 0, "bot", A, alive=True, weapon="battle_rifle", weapons=["battle_rifle"])
        far = PlayerState(2, 1, "human", Vec(A.x - 30.0, A.y, A.z), alive=True)
        b.think(t, DT, Snapshot(t, [me, far], vehicles=[hog]), lambda p, q: False, lambda p, q, **k: p, [])   # no step closer
        if gave_up is None and "vehicle: no way to it, given up" in b.notes:
            gave_up = t
        if t > 7.5:
            goals.append(b.goal[0])
        t += DT
    info.append(f"unreachable vehicle given up at {gave_up if gave_up is None else round(gave_up, 1)} s")
    if gave_up is None or not 5.5 < gave_up < 7.5 or "vehicle" in goals:
        fails.append(f"unreachable vehicle: given up at {gave_up}, goals after 7.5 s {set(goals)} (want ~6 s, no vehicle)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("combat oct31 OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
