"""The owner's issue #3 (Halo 3 Infection on Rat's Nest, Scaling; Halo 4 Flood), each part failing on the code before:
1. a sword at a man 4.3 u off: no grenade, so no own-grenade "bubble" round him (own_grenade turned every step toward
   him away for 3 s), and the run goes at him
2. a sword at arm's length: no bend round the man it runs at (give_way bent round every player within 1.3 u)
3. the red reticle: the sword's autoaim range and cone (tags: 2.25 u and 6 deg in Reach / Halo 4 / H2A); no press 0.35
   rad off at 1.4 u (a swing at the air)
4. a sword clash: Heroic follows its press with one melee while the sword man still stands in reach; Easy never; the
   hammer never melees
5. the infected's own swords named: Halo 4's storm_flood_sword, H2A's h2a_energy_sword_infected -> "sword"; Halo 3 by
   the map's tag names (melee kinds), and a Halo 3 zombie still "unknown" plays the sword
6. Halo 4 Flood under any variant name: an infected-only gun in a hand says Infection (modes.mode_of); a free for all
   with no raw gun tags splits by gun names (survivors stopped fighting each other)
7. survivors hold rooms with few ways in (modes.find_holds), in groups far apart; the infected wait at the corners of a
   survivor's hold, and at survivors grouped and holding they rally, then go in together as hunters

usage: python -I test_melee_infection.py      -> "melee infection OK (...)"
"""
import math
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import modes  # noqa: E402
from brain.bot import Belief, Bot, red_reticle  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.live import LiveH3, LiveH4F, brain_name  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

A = Vec(-2.0, 7.7, 6.4)          # Construct, red side's walk, one floor (tools/test_sword.py)
DT = 1 / 30
M = get_map("h3_construct")


def mk(tier="top", game="h3", i=5, grenades=None):
    b = Bot(i, 0, make_profile(tier, "rusher", random.Random(i)), M, random.Random(i))
    b.game, b.can_pickup = game, False
    if grenades is not None:
        b.p.grenades, b.p.tactics = grenades, 1.0
    return b


def fight(b, weapon, d, secs, foe_weapon="assault_rifle", yaw=0.0, t0=1.0):
    """Ticks of b fighting a man d u east (it looks yaw): [(t, action, notes)]."""
    man = Vec(A.x + d, A.y, A.z)
    b.per.beliefs[2] = Belief(man, Vec(), t0, True, "eyes")
    b.per.recognized.add(2)
    out, t = [], t0
    while t < t0 + secs:
        b.per.last_seen[2] = t
        me = PlayerState(b.id, 0, "bot", A, alive=True, weapon=weapon, weapons=[weapon], ammo=[-1], mag=[-1], yaw=yaw)
        foe = PlayerState(2, 1, "human", man, alive=True, yaw=math.pi, weapon=foe_weapon)
        a = b.think(t, DT, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        if b.goal == ("fight", 2):
            out.append((t, a, list(b.notes)))
        t += DT
    return out


def main():
    fails, info = [], []
    # 1. no grenade with the sword, no bubble
    ticks = fight(mk(grenades=1.0), "sword", 4.3, 1.0)
    nades = sum(a.grenade for _, a, _ in ticks)
    fwd = sum(a.forward for _, a, _ in ticks) / max(1, len(ticks))
    clear = sum("grenade: clear of my own" in n for _, _, n in ticks)
    info.append(f"sword at 4.3 u: {nades} grenades, forward {fwd:.2f}")
    if nades or clear or fwd < 0.6:
        fails.append(f"sword at 4.3 u: {nades} grenades, {clear} own-grenade turns, forward {fwd:.2f} (want 0, 0, 0.6+)")
    # 2. no bend round the man it runs at
    ticks = fight(mk(), "sword", 1.1, 0.5)
    side = sum(abs(a.strafe) for _, a, _ in ticks) / max(1, len(ticks))
    info.append(f"sword at 1.1 u: strafe {side:.2f}")
    if side > 0.2:
        fails.append(f"sword at 1.1 u: strafe {side:.2f} (bent round him; want under 0.2)")
    # 3. the red reticle
    me = PlayerState(1, 0, "bot", A, yaw=0.0)
    for w, game, d, off, want in (("sword", "reach", 2.1, 0.0, True), ("sword", "reach", 2.4, 0.0, False),
                                  ("sword", "h4", 2.2, 0.1, True), ("sword", "h3", 2.0, 0.0, False),
                                  ("sword", "h3", 1.4, 0.35, False), ("sword", "h3", 1.4, 0.15, True),
                                  ("gravity_hammer", "reach", 1.3, 0.0, True), ("gravity_hammer", "h3", 1.6, 0.0, False)):
        at = Vec(A.x + d * math.cos(off), A.y + d * math.sin(off), A.z)
        if red_reticle(me, at, w, game) != want:
            fails.append(f"{game} {w}, a man {d} u off, {off} rad off the view: red {not want} (want {want})")
    if fight(mk(), "sword", 1.4, 0.3, yaw=0.35) and any(a.fire for _, a, _ in fight(mk(), "sword", 1.4, 0.3, yaw=0.35)):
        fails.append("sword: pressed with the man 0.35 rad off the view (no red reticle)")
    # 4. the clash
    for tier, want in (("strong", True), ("top", True), ("novice", False)):
        ticks = fight(mk(tier), "sword", 1.0, 0.8, foe_weapon="sword")
        first = next((t for t, a, _ in ticks if a.fire), None)
        mel = [t for t, a, _ in ticks if a.melee]
        ok = bool(mel) and first is not None and all(0.1 <= t - first <= 0.75 for t in mel) and len(mel) == 1
        info.append(f"{tier} sword clash: press {first and round(first - 1.0, 2)}, melee {[round(t - 1.0, 2) for t in mel]}")
        if (ok if want else bool(mel)) != want:
            fails.append(f"{tier} sword v sword at 1.0 u: press at {first}, melee at {mel} (want the follow-up {want})")
    if any(a.melee for _, a, _ in fight(mk(), "gravity_hammer", 1.0, 0.8, foe_weapon="sword")):
        fails.append("the hammer pressed melee")
    # 4b. a shotgun against a sword holds its ground (owner's Wraparound Flood, Nov 6 16:01: survivors walked at the
    # Flood 44% of the time from 3-10 u and fired nothing there)
    for tier in ("strong", "top"):
        ticks = fight(mk(tier, game="h4"), "shotgun", 5.0, 1.0, foe_weapon="sword")
        fwd = max((a.forward for _, a, _ in ticks), default=0.0)
        info.append(f"{tier} shotgun v sword at 5 u: forward at most {fwd:.2f}")
        if not ticks or fwd > 0.05:
            fails.append(f"{tier} shotgun v sword at 5 u: forward {fwd:.2f} over {len(ticks)} ticks (want no step in on him)")
    # 5. names
    for raw, want in (("storm_flood_sword", "sword"), ("h2a_energy_sword_infected", "sword"),
                      ("storm_energy_sword", "sword"), ("storm_gravity_hammer", "gravity_hammer")):
        if brain_name(raw) != want:
            fails.append(f"{raw} -> {brain_name(raw)} (want {want})")
    h3 = object.__new__(LiveH3)
    h3._names, h3._placements = {}, []
    h3._h3_tag_names = [""] * 8
    h3._h3_tag_names[5] = "objects\\weapons\\melee\\energy_blade\\energy_blade"
    h3._h3_tag_names[6] = "objects\\weapons\\rifle\\battle_rifle\\battle_rifle"

    class G:
        def __init__(s, tag):
            s.tag = tag

        def read(s, a, n):
            return struct.pack("<I", s.tag)[:n]
    h3.object = lambda h: 1
    for idx, want in ((5, "sword"), (6, "battle_rifle")):
        h3.g = G((0xE12 << 16) | idx)
        if h3.weapon_name(1) != want:
            fails.append(f"Halo 3 gun at tag index {idx}: {h3.weapon_name(1)} (want {want}: by the tag name)")
    h4 = object.__new__(LiveH4F)
    h4._names = {}
    h4._own_name = lambda tag, folder: "storm_flood_sword"
    h4._learn(0x1234, None)
    if h4._names.get(0x1234) != "sword" or not getattr(h4, "zombie_seen", False):
        fails.append(f"Halo 4 Flood prongs: named {h4._names.get(0x1234)}, zombie seen {getattr(h4, 'zombie_seen', None)}")

    class V:
        zombie_seen = True

        def variant_name(s):
            return "Custom Game"
    if modes.mode_of("h4", V()) != "infection":
        fails.append(f"Halo 4 with the Flood's prongs in a hand: mode {modes.mode_of('h4', V())} (want infection)")
    # 6. a free for all with no raw tags (Halo 4 / H2A / Reach readers): split by the gun's name
    w = modes.Watch("infection", M.get("objects", {}), "h4")
    ps = [PlayerState(i, i, "p", Vec(), weapon="sword" if i == 4 else "shotgun") for i in range(6)]
    sn = Snapshot(0.0, ps)
    w.update(None, sn, 0.0, raw=[dict(index=i, pos=(0, 0, 0)) for i in range(6)])
    if [p.team for p in sn.players] != [0, 0, 0, 0, 1, 0] or sn.infected != 1:
        fails.append(f"Halo 4 Flood free for all: teams {[p.team for p in sn.players]} (want the prongs' holder alone)")
    # (live Reach Boardwalk: one sword, two shotguns and a magnum at the start; the fewest-held rule took the magnum)
    wr = modes.Watch("infection", M.get("objects", {}), "reach")
    sn = Snapshot(0.0, [PlayerState(i, i, "p", Vec(), weapon=w) for i, w in enumerate(("shotgun", "magnum", "sword", "shotgun"))])
    wr.update(None, sn, 0.0, raw=[dict(index=i, pos=(0, 0, 0)) for i in range(4)])
    if [p.team for p in sn.players] != [0, 0, 1, 0]:
        fails.append(f"Reach free for all, sword / shotguns / magnum: teams {[p.team for p in sn.players]}")
    w3 = modes.Watch("infection", M.get("objects", {}), "h3")
    ps = [PlayerState(i, i, "p", Vec(), weapon="unknown" if i == 2 else "shotgun") for i in range(5)]
    sn = Snapshot(0.0, ps)
    w3.update(None, sn, 0.0, raw=[dict(index=i, pos=(0, 0, 0), wtag=0xAA if i == 2 else 0xBB) for i in range(5)])
    if sn.players[2].team != 1 or sn.players[2].weapon != "sword":
        fails.append(f"Halo 3 zombie with an unnamed gun: team {sn.players[2].team}, weapon {sn.players[2].weapon}")
    # 7. holds, groups, corners, the charge (Rat's Nest)
    rn = get_map("h3_armory")
    zb = {i: Bot(i, 1, make_profile("top", "rusher", random.Random(i)), rn, random.Random(i)) for i in (10, 11, 12)}
    sv = {i: Bot(i, 0, make_profile("top", "camper", random.Random(i)), rn, random.Random(i)) for i in range(6)}
    ds, dz = Director(0, rn, sv), Director(1, rn, zb)
    hs = modes.holds(ds.terrain(), rn["name"], wait=True)
    top = hs[0] if hs else None
    info.append(f"Rat's Nest: {len(hs)} holds, best {top and (top['entrances'], round(top['exposure'], 1))}")
    if not hs or top["entrances"] > 2 or not top["roof"]:
        fails.append(f"Rat's Nest holds: {len(hs)}, best {top and {k: top[k] for k in ('entrances', 'roof', 'area')}}")
    picked = modes.pick_holds(hs, 2)
    if len(picked) < 2 or dist(picked[0]["pos"], picked[1]["pos"]) < modes.HOLD_APART:
        fails.append("two survivor groups: holds not 12 u apart")
    mid = rn["points"]["mid"]
    surv = [PlayerState(i, 0, "s", mid + Vec(i, 0, 0), weapon="shotgun") for i in range(6)]
    zom = [PlayerState(i, 1, "z", mid + Vec(30 + 10 * k, 0, 0), weapon="sword") for k, i in enumerate((10, 11, 12))]
    snap = Snapshot(5.0, surv + zom, mode="infection")
    snap.infected = 1
    slots = ds.mode_slots(5.0, snap, 6)
    at = {min(range(len(picked)), key=lambda k: dist(q, picked[k]["pos"])) for _, q, _ in slots}
    far = max(min(dist(q, h["pos"]) for h in picked) for _, q, _ in slots)
    info.append(f"survivors: {len(at)} groups, farthest {far:.1f} u from its hold")
    if len(at) < 2 or far > 2.5 or any(r != "defender" for r, _, _ in slots):
        fails.append(f"survivors: slots in {len(at)} holds, {far:.1f} u off them (want 2 groups, each in its hold)")
    # a survivor in a hold: a corner the hold's middle does not see
    snap2 = Snapshot(5.0, [PlayerState(0, 0, "s", top["pos"], weapon="shotgun")] + zom, mode="infection")
    snap2.infected = 1
    amb = dz.ambush_spots(snap2, [snap2.players[0]], 2)
    if not amb:
        fails.append("infected: no corner to wait round at the survivor's hold")
    # three survivors together, standing: the infected rally, then charge as hunters
    h = top["pos"]
    grp = [PlayerState(i, 0, "s", h + Vec(0.4 * i, 0, 0), weapon="shotgun") for i in range(3)]
    snap3 = Snapshot(6.0, grp + zom, mode="infection")
    snap3.infected = 1
    want = dz.desperate(6.0, snap3)
    if want is None or want[1] != "infection: they hold":
        fails.append(f"infected v three survivors holding: desperate {want}")
    else:
        dz.blitz_tick(6.0, snap3)
        bz = getattr(dz, "blitz", None)
        if bz is None or bz["go"] is not None:
            fails.append(f"infected 10 u apart: no rally first ({bz and bz['go']})")
        else:
            rally = bz["rally"]
            zom2 = [PlayerState(i, 1, "z", rally + Vec(0.5 * k, 0, 0), weapon="sword") for k, i in enumerate((10, 11, 12))]
            snap4 = Snapshot(7.0, grp + zom2, mode="infection")
            snap4.infected = 1
            dz.blitz_tick(7.0, snap4)
            roles = sorted(b.order.role for b in zb.values())
            info.append(f"infected charge: {roles}")
            if dz.blitz["go"] is None or roles != ["hunter"] * 3:
                fails.append(f"infected at the rally: go {dz.blitz['go']}, roles {roles} (want all hunters together)")
    # 7b. holds people stood in come first (owner's Blood Cavern Nov 6 16:48: the best "holds" were the pit under the back
    #     walkway, z 0.1-0.6, ways in only drops, nobody ever stood there; three survivors pushed 35 s at its rim for their
    #     posts): the 4 groups' holds are rooms people walked, none on that floor
    bc = get_map("h4_ca_blood_cavern")
    bh = modes.pick_holds(modes.find_holds(terrain(bc)), 4)
    pit = [h for h in bh if h["pos"].x < -8.5 and -9.0 < h["pos"].y < 21.0 and h["pos"].z < 1.0]
    info.append("Blood Cavern: 4 groups' holds " + str([tuple(round(c, 1) for c in (h["pos"].x, h["pos"].y, h["pos"].z))
                                                        for h in bh]))
    if len(bh) < 4 or pit or not all(h["walked"] for h in bh):
        fails.append(f"Blood Cavern holds: {len(bh)}, in the pit {len(pit)}, walked {[h['walked'] for h in bh]}")
    # 8. the lunge's target reaches every game: the brain packs it (shared.h HB_TARGET_SHIFT, bits 24-28 = player + 1),
    # each game's botcore writes it; Reach / Halo 4 / H2A attack with the melee action, Halo 2 / 3 with the trigger
    import live_bots
    from brain.core import Action
    if (live_bots.buttons(Action(lunge_at=5)) >> 24) & 31 != 6 or live_bots.buttons(Action()) >> 24:
        fails.append("buttons(): the lunge target is not in bits 24-28")
    shared = open(os.path.join(HERE, "..", "native", "shared.h"), encoding="utf-8").read()
    if "HB_TARGET_SHIFT = 24" not in shared:
        fails.append("shared.h: no HB_TARGET_SHIFT 24")
    for src in ("h2.cpp", "h3.cpp", "reach.cpp", "h4f.cpp"):
        if "hb_target(a.buttons)" not in open(os.path.join(HERE, "..", "native", src), encoding="utf-8").read():
            fails.append(f"native/{src}: the lunge target is never written")
    for game, melee in (("h2", False), ("h3", False), ("reach", True), ("h4", True), ("h2a", True)):
        for tier in ("top", "novice"):
            ticks = fight(mk(tier, game=game), "sword", 1.2, 0.4, foe_weapon="assault_rifle")
            press = next((a for _, a, _ in ticks if a.fire), None)
            if press is None or press.lunge_at != 2 or bool(press.melee) != melee:
                fails.append(f"{game} {tier} sword press at 1.2 u: {press and (press.lunge_at, press.melee)} "
                             f"(want target 2, melee {melee})")
    if fails:
        sys.exit("\n".join("FAIL: " + f for f in fails))
    print("melee infection OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
