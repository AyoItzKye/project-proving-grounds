"""Offline checks for how bots use their guns ("keep trying to shoot their dry weapon", rockets inside their
own blast while "another enemy kill[s] you", burst-firing assault rifles in close quarters, the DMR fired
too slowly, charge weapons tapped, no zoom). The game applies a switch here as MCC does: the next tick
holds the asked-for gun.

usage: python -I test_weapons.py      -> "weapons OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
A = Vec(70.0, -120.0, T.nav_z(70.0, -120.0))
DT = 1 / 30


class Kit:
    """What the bot carries: names, rounds in each magazine, rounds in all (magazine + reserve)."""
    def __init__(s, weapons, mag=None, ammo=None):
        s.weapons, s.held = list(weapons), 0
        s.mag = list(mag) if mag else [-1] * len(weapons)
        s.ammo = list(ammo) if ammo else [-1] * len(weapons)


def run(tier, kit, t1, foe_at, foe_shield=1.0, game="reach", hurt=False, foes=True, setup=None, fxs=None):
    b = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), MAP, random.Random(1))
    b.game, b.can_pickup = game, False
    if setup:
        setup(b)
    out, t, yaw, pitch, shield = [], 0.0, math.pi, 0.0, 1.0
    while t < t1:
        if hurt:
            shield = max(0.0, shield - 0.02)       # someone is hitting us
        me = PlayerState(1, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=shield,
                         weapon=kit.weapons[kit.held], weapons=list(kit.weapons), ammo=list(kit.ammo), mag=list(kit.mag))
        d = foe_at(t) if callable(foe_at) else foe_at        # a distance, or one that changes over time
        at = Vec(A.x - d, A.y, T.nav_z(A.x - d, A.y))
        foe = [PlayerState(2, 1, "human", at, alive=True, yaw=0.0, shield=foe_shield)] if foes else []
        a = b.think(t, DT, Snapshot(t, [me] + foe), T.los, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        if fxs is not None:
            fxs.append((me.weapon, dict(b.fx or {})))     # the gun in hand this tick (the switch lands next tick)
        if a.weapon >= 0:
            kit.held = a.weapon
        out.append((t, a, kit.weapons[kit.held], list(b.notes)))
        t += DT
    return out


def presses(acts, after=0.0):
    return [t for (t, a, _, _), (_, p, _, _) in zip(acts[1:], acts) if t > after and a.fire and not p.fire]


def main():
    fails = []
    # 1. dry in hand, a loaded secondary: switch at once, no more trigger pulls on the empty gun
    kit = Kit(["dmr", "assault_rifle"], mag=[0, 32], ammo=[0, 96])
    acts = run("strong", kit, 2.0, 8.0)
    if kit.weapons[kit.held] != "assault_rifle" or any(a.fire for t, a, w, _ in acts if w == "dmr" and t > 0.1):
        fails.append("dry DMR: no switch to the AR, or kept pulling the empty trigger")
    # ... even right after a switch (the range rule waits; a dry gun does not), and a Recruit clicks a moment first
    kit = Kit(["dmr", "assault_rifle"], mag=[0, 32], ammo=[0, 96])
    run("strong", kit, 0.5, 8.0, setup=lambda b: setattr(b, "switch_ok_at", 99.0))
    if kit.weapons[kit.held] != "assault_rifle":
        fails.append("dry DMR right after a switch: no switch to the loaded AR")
    kit = Kit(["dmr", "assault_rifle"], mag=[0, 32], ammo=[0, 96])
    acts = run("novice", kit, 2.0, 8.0, setup=lambda b: setattr(b, "switch_ok_at", 99.0))
    first = next((t for t, a, w, _ in acts if w == "assault_rifle"), None)
    if first is None or first < 0.5:
        fails.append(f"a Recruit's dry switch at {first} (want after ~0.6 s of clicking)")
    # 2. the magazine runs out mid-fight with rounds in reserve and a loaded secondary: switch (beats the reload)
    kit = Kit(["battle_rifle", "assault_rifle"], mag=[0, 32], ammo=[24, 96])
    run("strong", kit, 1.5, 6.0)
    if kit.weapons[kit.held] != "assault_rifle":
        fails.append("empty BR magazine mid-fight: no switch to the loaded AR")
    # ... but a Recruit just reloads (the game does it on the next pull)
    kit = Kit(["battle_rifle", "assault_rifle"], mag=[0, 32], ammo=[24, 96])
    run("novice", kit, 1.5, 6.0)
    if kit.weapons[kit.held] != "battle_rifle":
        fails.append("a Recruit switched on an empty magazine")
    # ... and the emptied gun is not taken back mid-fight (the range rule took the AR back, the rule above swapped it
    # out again: live CE, AR <-> plasma pistol every 1.5-2 s with 491 rounds in reserve, never reloaded) ...
    kit = Kit(["plasma_pistol", "assault_rifle"], mag=[-1, 0], ammo=[-1, 491])
    acts = run("strong", kit, 4.0, 3.0, game="ce")
    seen = next((t for t, _, _, notes in acts if "switch: empty magazine mid-fight" in notes), 0.0)   # (before it
    if any(w == "assault_rifle" for t, _, w, _ in acts if t > seen + 0.1):    # sees him it takes the AR out to reload)
        fails.append("an AR with an empty magazine taken back out mid-fight")
    # ... it comes back out between fights, and is reloaded
    kit = Kit(["plasma_pistol", "assault_rifle"], mag=[-1, 0], ammo=[-1, 491])
    acts = run("strong", kit, 2.0, 3.0, game="ce", foes=False)
    if kit.weapons[kit.held] != "assault_rifle" or not any(a.reload and w == "assault_rifle" for _, a, w, _ in acts):
        fails.append("an AR with an empty magazine left in the pocket between fights (or not reloaded)")
    # ... but not in a retreat, where think() reloads nothing (third review B1: the empty AR came out behind cover and
    # was fired empty when the man came back), nor when it is named like the gun in hand (pick() cannot address it:
    # two Halo 3 "unknown"s, N8: a no-op switch every 1.2-2 s)
    for kind, guns, ammo, mag in (("retreat", ["plasma_pistol", "assault_rifle"], [-1, 491], [-1, 0]),
                                  ("roam", ["unknown", "unknown"], [30, 491], [12, 0])):
        b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
        b.game, b.notes, b.now = "h3" if kind == "roam" else "ce", [], 5.0
        me = PlayerState(1, 0, "bot", A, alive=True, weapon=guns[0], weapons=guns, ammo=ammo, mag=mag)
        got = b.choose_weapon(5.0, me, kind, None, Snapshot(5.0, [me]))
        if got != -1:
            fails.append(f"{kind}: {guns} with the second one's magazine empty: slot {got} (want to keep the first)")
    # the edges the third review's mutants passed: an empty gun ranked equal comes out (M06: >= kept), a man in view
    # 8 units off keeps it in the pocket (M07: the visible-enemy guard), and mid-fight at 12 units an empty BR is not
    # scored (M10: the rule's 15 units, the "empty magazine mid-fight" swap's own reach)
    foe8, foe12 = Vec(A.x - 8.0, A.y, A.z), Vec(A.x - 12.0, A.y, A.z)
    for case, kind, guns, ammo, mag, foe, want in (
            ("equal ranks", "roam", ["needler", "assault_rifle"], [20, 491], [20, 0], None, 1),
            ("a man in view", "roam", ["plasma_pistol", "assault_rifle"], [-1, 491], [-1, 0], foe8, -1),
            ("mid-fight at 12 units", "fight", ["plasma_pistol", "battle_rifle"], [-1, 36], [-1, 0], foe12, -1)):
        b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
        b.game, b.notes, b.now = "ce", [], 5.0
        snap = [PlayerState(1, 0, "bot", A, alive=True, weapon=guns[0], weapons=guns, ammo=ammo, mag=mag)]
        if foe is not None:
            b.per.beliefs[2] = Belief(foe, Vec(), 4.9, True, "eyes")
            b.per.recognized.add(2)
            snap.append(PlayerState(2, 1, "human", foe, alive=True, shield=1.0))
        got = b.choose_weapon(5.0, snap[0], kind, 2, Snapshot(5.0, snap))
        if got != want:
            fails.append(f"{case}: {guns}, magazines {mag}: slot {got} (want {want})")
    # 3. up close the AR comes out of a precision rifle bot's pocket (Halo 3's BR; in Reach and Halo 4 the DMR stays in
    #    hand at every range since the Nov 7 design rule, bot.DMR_OVER_AR, CMB-98); at range the rifle goes back in hand
    kit = Kit(["battle_rifle", "assault_rifle"])
    run("strong", kit, 2.0, 2.0, game="h3")
    if kit.weapons[kit.held] != "assault_rifle":
        fails.append("Halo 3, BR + AR at 2 units: no switch to the AR")
    kit = Kit(["dmr", "assault_rifle"])
    run("strong", kit, 2.0, 2.0)
    if kit.weapons[kit.held] != "dmr":
        fails.append("Reach, DMR + AR at 2 units: the AR came out (DMR_OVER_AR)")
    kit = Kit(["dmr", "assault_rifle"])
    kit.held = 1
    run("strong", kit, 2.0, 9.0)
    if kit.weapons[kit.held] != "dmr":
        fails.append("AR + DMR at 9 units: no switch to the DMR")
    # ... never while the man is one shot from dying
    kit = Kit(["dmr", "assault_rifle"])
    run("strong", kit, 2.0, 2.0, foe_shield=0.0)
    if kit.weapons[kit.held] != "dmr":
        fails.append("switched weapons on a man one shot from dying")
    # 4. rockets inside their own blast with a magnum: switch at once, a Recruit too (it has no range rule)
    kit = Kit(["rockets", "magnum"])
    acts = run("novice", kit, 2.0, 1.8)
    if kit.weapons[kit.held] != "magnum" or any(a.fire for t, a, w, _ in acts if w == "rockets"):
        fails.append("a Recruit with rockets at 1.8 units: no switch to the magnum, or fired the rocket")
    kit = Kit(["rockets", "magnum"])
    acts = run("strong", kit, 1.0, 1.8)
    if kit.weapons[kit.held] != "magnum" or any(a.fire for t, a, w, _ in acts if w == "rockets"):
        fails.append("rockets at 1.8 units: no switch to the magnum, or fired the rocket")
    # ... rockets alone, being shot, no swing landing (Halo 2: no melee decoded): trade within ~0.5 s
    b_kit = Kit(["rockets"])
    b = None
    acts = run("strong", b_kit, 2.0, 1.8, hurt=True, game="h2")
    first = presses(acts)
    if not first or first[0] > 1.2:
        fails.append(f"rockets alone at 1.8 units under fire: first shot at {first[0] if first else None} (want a quick trade)")
    # 5. plasma pistol on a shielded man with a BR along: hold the charge, let go on target, the BR comes out
    kit = Kit(["plasma_pistol", "battle_rifle"])
    acts = run("strong", kit, 4.0, 5.0, game="h3")
    held = max((sum(1 for _ in g) for g in _runs([a.fire for _, a, _, _ in acts])), default=0)
    released = next((t for (t, a, w, _), (_, p, _, _) in zip(acts[1:], acts) if p.fire and not a.fire and w == "plasma_pistol"), None)
    if held * DT < 0.85 or released is None:
        fails.append(f"plasma pistol: longest charge {held * DT:.2f} s, released at {released}")
    elif not any(w == "battle_rifle" for t, _, w, _ in acts if released < t < released + 1.6):
        fails.append("plasma pistol: no switch to the BR after the overcharged bolt (noob combo)")
    # ... an unshielded man gets plain shots (no charge)
    kit = Kit(["plasma_pistol", "battle_rifle"])
    acts = run("strong", kit, 3.0, 5.0, foe_shield=0.0, game="h3")
    if max((sum(1 for _ in g) for g in _runs([a.fire for _, a, _, _ in acts])), default=0) > 2:
        fails.append("plasma pistol charged on an unshielded man")
    # ... a charge does not outlive a switch to another gun (live Boardwalk: 124 AR ticks showed a launcher charge).
    #     He starts at 10 units (the launcher charges), then steps in to 2 (inside its blast: the AR comes out mid-charge).
    #     At a fixed 3.4 units the bot switched before charging once guns went by a close man's range on every tick
    #     (0999838), and this check stopped reaching the charge (mutation run, 5ba8072)
    fxs = []
    run("strong", Kit(["plasma_launcher", "assault_rifle"]), 3.0, lambda t: 10.0 if t < 1.5 else 2.0, fxs=fxs)
    charged = any(w == "plasma_launcher" and fx.get("charge") is not None for w, fx in fxs)
    stale = sum(1 for w, fx in fxs if w == "assault_rifle" and fx.get("charge") is not None)
    if not charged or stale or not any(w == "assault_rifle" for w, _ in fxs):
        fails.append(f"launcher charge kept after the switch to the AR: {stale} ticks (charging seen: {charged})")
    # 6. the spartan laser is held until it fires by itself (pulses never charge it)
    kit = Kit(["spartan_laser"])
    acts = run("strong", kit, 5.0, 15.0, game="h3")
    held = max((sum(1 for _ in g) for g in _runs([a.fire for _, a, _, _ in acts])), default=0)
    if held * DT < 2.9:
        fails.append(f"spartan laser held {held * DT:.2f} s at most (it needs ~3 s)")
    # 7. DMR cadence: spam up close, paced at range
    for d, lo, hi in ((2.0, 0.19, 0.3), (12.0, 0.43, 0.6)):
        kit = Kit(["dmr"])
        p = presses(run("strong", kit, 5.0, d), after=1.5)
        gaps = [b - a for a, b in zip(p, p[1:])]
        mean = sum(gaps) / len(gaps) if gaps else 9.0
        if not lo <= mean <= hi:
            fails.append(f"DMR at {d} units: a press every {mean:.2f} s (want {lo}-{hi})")
    # 8. an AR up close holds the trigger down through the fight
    kit = Kit(["assault_rifle"])
    acts = run("strong", kit, 3.0, 1.5)
    down = sum(1 for t, a, _, _ in acts if t > 1.0 and a.fire) / sum(1 for t, *_ in acts if t > 1.0)
    if down < 0.8:
        fails.append(f"AR at 1.5 units: trigger down {down:.0%} (close quarters: full auto)")
    # 9. zoom: a DMR past Short band scopes, up close it does not; a sniper at 25 the second level; Easy never
    for tier, w, d, want in (("strong", "dmr", 8.0, 1), ("strong", "dmr", 2.0, 0), ("strong", "sniper", 30.0, 2),
                             ("novice", "dmr", 8.0, 0)):
        acts = run(tier, Kit([w]), 2.5, d)
        z = max(a.zoom for t, a, _, _ in acts if t > 1.5)
        if z != want:
            fails.append(f"{tier} {w} at {d} units: zoom {z} (want {want})")
    # 9b. backing off or hunting with a man close by: the guns still go by his range, not the all-rounder (live
    #     Boardwalk: three AR -> DMR swaps with a man 2-3.4 units away on a retreat or hunt tick)
    #     (Halo 3's BR + AR; Reach's DMR is held at every range since Nov 7: DMR_OVER_AR, the AR never kept)
    for game, rifle in (("h3", "battle_rifle"), ("reach", "dmr")):
        for d, want_keep in ((2.0, game != "reach"), (12.0, False)):
            for kind in ("retreat", "hunt"):
                b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
                b.game, b.notes, b.now = game, [], 5.0
                foe_pos = Vec(A.x - d, A.y, A.z)
                b.per.beliefs[2] = Belief(foe_pos, Vec(), 4.5, True, "eyes")
                me = PlayerState(1, 0, "bot", A, alive=True, weapon="assault_rifle", weapons=[rifle, "assault_rifle"])
                snap = Snapshot(5.0, [me, PlayerState(2, 1, "human", foe_pos, alive=True)])
                got = b.choose_weapon(5.0, me, kind, A + Vec(5.0, 0, 0), snap)
                if (got == -1) != want_keep:
                    fails.append(f"{game}, {kind} with a man at {d} units: weapon slot {got} "
                                 f"(want {'keep the AR' if want_keep else 'the ' + rifle})")
    # 9c. review findings (logs/verify/review_ef3105a_613bffb.md):
    #   F1 the finishing hold keeps only a gun that can hit at his range (a shotgun or sword at 15 units goes)
    for game, w, alt in (("ce", "shotgun", "pistol"), ("h2", "sword", "battle_rifle")):
        b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
        b.game, b.notes, b.now = game, [], 5.0
        foe_pos = Vec(A.x - 15.0, A.y, A.z)
        b.per.beliefs[2] = Belief(foe_pos, Vec(), 4.9, True, "eyes")
        me = PlayerState(1, 0, "bot", A, alive=True, weapon=w, weapons=[w, alt])
        got = b.choose_weapon(5.0, me, "fight", 2, Snapshot(5.0, [me, PlayerState(2, 1, "human", foe_pos, alive=True, shield=0.0)]))
        if got != 1:
            fails.append(f"F1: {game} {w} vs a shieldless man at 15 units: slot {got} (want the {alt})")
    #   ... but a gun that still reaches him is kept: a CE shotgun fires to 2.5 units (second review: the hold used the
    #   band's 1.8 and switched to the pistol at 2.2-2.5)
    b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
    b.game, b.notes, b.now = "ce", [], 5.0
    foe_pos = Vec(A.x - 2.3, A.y, A.z)
    b.per.beliefs[2] = Belief(foe_pos, Vec(), 4.9, True, "eyes")
    me = PlayerState(1, 0, "bot", A, alive=True, weapon="shotgun", weapons=["shotgun", "pistol"])
    got = b.choose_weapon(5.0, me, "fight", 2, Snapshot(5.0, [me, PlayerState(2, 1, "human", foe_pos, alive=True, shield=0.0)]))
    if got != -1:
        fails.append(f"F1b: CE shotgun vs a shieldless man at 2.3 units (in its reach): slot {got} (want to keep it)")
    #   F4 the focus rifle is no close-quarters gun: at 2 units the magnum comes out
    b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
    b.game, b.notes, b.now = "reach", [], 5.0
    foe_pos = Vec(A.x - 2.0, A.y, A.z)
    b.per.beliefs[2] = Belief(foe_pos, Vec(), 4.9, True, "eyes")
    me = PlayerState(1, 0, "bot", A, alive=True, weapon="focus_rifle", weapons=["focus_rifle", "magnum"])
    got = b.choose_weapon(5.0, me, "fight", 2, Snapshot(5.0, [me, PlayerState(2, 1, "human", foe_pos, alive=True)]))
    if got != 1:
        fails.append(f"F4: focus rifle at 2 units: slot {got} (want the magnum)")
    #   F2 / F3 the lock wait: rockets in Halo 2 on a second vehicle (a stale timer skipped it), the missile pod in
    #   Halo 3 (its game was not in LOCK_GAMES)
    for game, w, ride in (("h2", "rockets", lambda t: 7 if t < 3.0 or t >= 6.0 else -1), ("h3", "missile_pod", lambda t: 7)):
        b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
        b.game, b.can_pickup = game, False
        t, yaw, pitch, on_at, shots, prev = 0.0, math.pi, 0.0, None, [], False
        start = 6.0 if game == "h2" else 0.0
        while t < 8.5:
            me = PlayerState(1, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, weapon=w, weapons=[w])
            at = Vec(A.x - 10.0, A.y, T.nav_z(A.x - 10.0, A.y))
            foe = PlayerState(2, 1, "human", at, alive=True, yaw=0.0, vehicle=ride(t))
            a = b.think(t, DT, Snapshot(t, [me, foe]), T.los, lambda p, q, **k: q, [])
            yaw, pitch = a.yaw, a.pitch
            if t >= start and ride(t) != -1:
                if a.fire and not prev:
                    shots.append(t)
            prev = a.fire
            t += DT
        # from the moment he is in the vehicle (fx "on" already includes the lock wait): before the fixes the rocket left
        # 0.47 s after he boarded again (a stale lock timer), the pod 0.37 s after first sight (no lock at all)
        if not shots or shots[0] - start < 0.9:
            fails.append(f"F2/F3: {game} {w} on a vehicle from {start} s: first shot at {shots[0] if shots else None} "
                         f"(want a ~0.9 s lock first)")
    # 10. reload between fights: magazine at a fifth (of 15 seen), reserve left, nobody in view
    kit = Kit(["dmr"], mag=[15], ammo=[60])
    b = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), MAP, random.Random(1))
    b.can_pickup = False
    reloads = []
    for k in range(60):
        t = k * DT
        mag = 15 if k < 5 else 3
        me = PlayerState(1, 0, "bot", A, alive=True, weapon="dmr", weapons=["dmr"], ammo=[48 + mag], mag=[mag])
        a = b.think(t, DT, Snapshot(t, [me]), T.los, lambda p, q, **kw: q, [])
        reloads.append(a.reload)
    if sum(reloads) != 1:
        fails.append(f"reload between fights: {sum(reloads)} presses (want 1)")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("weapons OK")


def _runs(flags):
    """Groups of consecutive True values."""
    import itertools
    return [list(g) for k, g in itertools.groupby(flags) if k]


if __name__ == "__main__":
    main()
