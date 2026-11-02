"""Armor abilities and equipment pressed or held the right way in every game, and the jetpack used well ("people can jump
off spire and jet back almost near the floor and let down safely, they can jump up to 3x their normal height and avoid
stairs and hills"):

1. the press-vs-hold table (brain/equipment.py USE) as Kit.act carries it out, kind by kind: Halo 3 equipment one short
   press; Reach jetpack and armor lock held for the use, evade / hologram / drop shield the player's 0.2-0.25 s tap, camo
   one tick; Halo 4 thruster and hologram a tap, the toggles one tick
2. what reaches Reach: maps/_inputs/reach.json through tools/live_bots.py buttons and hb_apply_buttons (as
   tools/test_buttons.py replays it): the hold-mode kinds hold the action's +0x08 bit 8 for every pressed tick; the
   toggle-mode ones (sprint, camo: these came on live) never set it. Live no hold-mode kind ever came on without it
3. the jetpack fall brake: a bot falling off Spire's top past a heat vent (2.5 u off it, as 22 of 29 deaths off the top
   came down) lands at a safe speed (SAFE_LAND), not 16 u/s; too slow or too high a fall: no brake; Easy: none
4. the jetpack climb: a goal 3 u up and 5 u off that the walk winds round to (stairs) is flown at, straight; not when the
   walk heads there already, nor with a man in sight
5. armor lock is held while the rocket stays on it (past the plan's 2 s), let go within 0.6 s once he looks away
6. Halo 3: with the enemy driving, a trip mine goes down on a route people drove (Sandtrap's rides.json); not without

usage: python -I test_ability_hold.py      -> "ability hold OK (...)"
"""
import math
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import live_bots  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
import brain.equipment as EQ  # noqa: E402
from brain.equipment import Energy, Kit  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from test_buttons import apply  # noqa: E402
from test_equipment import A, DT, bot, foe, run  # noqa: E402
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

SAFE_LAND = getattr(EQ, "SAFE_LAND", 5.0)   # (the code before had none: the test runs there too, and fails)
G = 4.1                 # Reach gravity (brain/bot.py GRAVITY)
JET_UP = G + 1.4         # the jetpack's push: the player's net lift 1.4 u/s^2 (brain/equipment.py JET_BRAKE)


def presses(game, kind, plan, seconds=1.5, tier="top"):
    """Kit.act from a forced plan (kind, how, point, hold, why) for `seconds`: [(t, equipment, ability)] per tick."""
    b = bot(tier, game, kind)
    out, t, first = [], 1.0, True
    while t < 1.0 + seconds:
        me = PlayerState(b.id, 0, "bot", A, alive=True, equipment=kind)
        snap = Snapshot(t, [me])
        b.kit.perceive(b, t, me, snap)
        if first:
            b.kit.plan = lambda *a, **k: plan
            first = False
        else:
            b.kit.plan = lambda *a, **k: None
        a = Action(forward=1.0 if kind == "sprint" else 0.0)   # (a sprint is pressed only with the stick forward)
        b.kit.act(b, t, DT, me, snap, a)
        out.append((t, a.equipment, getattr(a, "ability", False)))
        t += DT
    return out


def held_for(ticks, i=1):
    """Seconds the button (i 1: equipment, 2: the hold bit) stayed down from the first tick, and ticks down in all."""
    n = 0
    for row in ticks:
        if not row[i]:
            break
        n += 1
    return n * DT, sum(1 for row in ticks if row[i])


def main():
    testdata.need_lidar("h3_shrine", "reach_35_island")
    fails, info = [], []

    # 1 + 2. the table, and the bits it puts into a Reach action
    entries = [(live_bots.botctl.BTN.get(n, 0), off, press, 4, mask)
               for g, n, off, mask, press in live_bots.decoded_buttons("reach")]
    if not any(n == "ability" for _, n, *_ in live_bots.decoded_buttons("reach")):
        fails.append("maps/_inputs/reach.json has no hold-mode ability entry (+0x08 bit 8)")
    cases = [  # game, kind, plan, want (equipment seconds lo, hi), want the hold bit
        ("h3", "bubble_shield", ("bubble_shield", "feet", None, 0.1, "t"), (0.09, 0.14), False),
        ("h3", "trip_mine", ("trip_mine", "front", A + Vec(2, 0, 0), 0.1, "t"), (0.09, 0.14), False),
        ("reach", "jetpack", ("jetpack", "self", None, 1.2, "t"), (1.18, 1.24), True),
        ("reach", "armor_lock", ("armor_lock", "self", None, 0.4, "t"), (0.38, 0.44), True),
        ("reach", "evade", ("evade", "dash", A + Vec(0, 3, 0), 0.1, "t"), (0.18, 0.24), True),
        ("reach", "hologram", ("hologram", "aim", A + Vec(8, 0, 0), 0.1, "t"), (0.18, 0.24), True),
        # (0.7 s, was the player's 0.2 s tap: a drop shield let go inside its 0.5 s warmup stops unstarted; his held
        # 1.06 / 1.44 s ones went down, use_of)
        ("reach", "drop_shield", ("drop_shield", "feet", None, 0.6, "t"), (0.68, 0.74), True),
        ("reach", "active_camo", ("active_camo", "self", None, 0.5, "t"), (0.03, 0.04), False),
        ("reach", "sprint", ("sprint", "self", None, 0.5, "t"), (0.48, 0.54), False),
        ("h4", "thruster", ("thruster", "dash", A + Vec(0, 3, 0), 0.1, "t"), (0.18, 0.24), True),
        ("h4", "jetpack", ("jetpack", "self", None, 1.0, "t"), (0.98, 1.04), True),
        ("h4", "promethean_vision", ("promethean_vision", "self", None, 2.0, "t"), (0.03, 0.04), False),
    ]
    for game, kind, plan, (lo, hi), want_bit in cases:
        ticks = presses(game, kind, plan)
        secs, _ = held_for(ticks)
        bit_secs, bit_n = held_for(ticks, 2)
        if not lo <= secs <= hi:
            fails.append(f"{game} {kind}: button held {secs:.2f} s (want {lo}-{hi})")
        if want_bit and abs(bit_secs - secs) > 1e-6:
            fails.append(f"{game} {kind}: hold bit {bit_secs:.2f} s with the button {secs:.2f} s (want with it)")
        if not want_bit and bit_n:
            fails.append(f"{game} {kind}: hold bit sent {bit_n} ticks (a toggle-mode or Halo 3 kind: never)")
        if game == "reach":
            act, prev, bit8, key, press31, bit16, first31 = bytearray(0xA8), 0, 0, 0, 0, 0, None
            for _, eq, ab in ticks:
                b = live_bots.buttons(Action(equipment=eq, **({"ability": ab} if ab else {})))
                apply(entries, 4, act, b, prev)
                prev = b
                w8, w40 = struct.unpack_from("<Q", act, 8)[0], struct.unpack_from("<Q", act, 0x40)[0]
                bit8 += bool(w8 & 0x100)
                bit16 += bool(w8 & 0x10000)
                key += (w40 & 0x3000) == 0x3000
                press31 += bool(w40 & 0x80000000)
                first31 = first31 if first31 is not None else bool(w40 & 0x80000000)
            n = round(secs / DT)
            if want_bit and bit8 != n:
                fails.append(f"reach {kind}: +0x08 bit 8 on {bit8} of {n} pressed ticks (the game runs a "
                             f"hold-mode ability only while it is set)")
            if not want_bit and bit8:
                fails.append(f"reach {kind}: +0x08 bit 8 on {bit8} ticks (a toggle-mode kind, it came on live without)")
            # as the game's own input sends it (FUN_18005df80): a hold-mode kind the key held and bit 8, never the
            # toggle-mode press (+0x40 bit 31) or the sprint state (+0x08 bit 16); a toggle-mode kind its press, once
            if want_bit and (key != n or press31 or bit16):
                fails.append(f"reach {kind}: key bits on {key} of {n} ticks, the toggle press on {press31}, bit 16 on "
                             f"{bit16} (want the key held, no press, no bit 16)")
            if not want_bit and kind != "sprint" and not first31:
                fails.append(f"reach {kind}: no toggle press (+0x40 bit 31) on its first tick")
        if game == "h4" and want_bit:
            h4 = [(live_bots.botctl.BTN.get(nm, 0), off, press, 7, mask)
                  for g, nm, off, mask, press in live_bots.decoded_buttons("h4")]
            act, prev, ok = bytearray(0x100), 0, 0
            for _, eq, ab in ticks:
                b = live_bots.buttons(Action(equipment=eq, **({"ability": ab} if ab else {})))
                apply(h4, 7, act, b, prev)
                prev = b
                ok += (struct.unpack_from("<Q", act, 8)[0] & 0x100 and
                       struct.unpack_from("<Q", act, 0x40)[0] & 0xC0C0 == 0xC0C0) if eq else 0
            if ok != round(secs / DT):
                fails.append(f"h4 {kind}: the decoded jetpack bits (+0x08 0x100, +0x40 0xC0C0) on {ok} of "
                             f"{round(secs / DT)} pressed ticks (want every one, as live)")
        info.append(f"{kind} {secs:.2f}s{'+bit' if bit_n else ''}")

    # 3. the fall brake, off Spire's top past a heat vent
    spire = get_map("reach_35_island")
    fb = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), spire, random.Random(1))
    fb.kit = Kit(fb.p, "reach")
    T = fb.T()
    land_vent = Vec(-185.35, -386.17, -58.18)                 # maps/reach_35_island/drops.json's first vent
    start = Vec(land_vent.x + 2.5, land_vent.y, -24.33)
    floor = start.z - T.height_over(start.x, start.y, start.z)

    def fall(b, brake=True):
        pos, vz, t, on_s = Vec(start.x, start.y, start.z), 0.0, 0.0, 0.0
        while pos.z > floor + 0.05 and t < 20.0:
            me = PlayerState(b.id, 0, "bot", pos, vel=Vec(0, 0, vz), alive=True, equipment="jetpack")
            snap = Snapshot(t, [me])
            b.kit.perceive(b, t, me, snap)
            a = Action()
            b.kit.act(b, t, DT, me, snap, a)
            on = brake and a.equipment and getattr(a, "ability", False)
            on_s += DT if on else 0.0
            vz += (-G + (JET_UP if on else 0.0)) * DT
            pos = Vec(pos.x, pos.y, max(floor, pos.z + vz * DT))
            t += DT
        return -vz, on_s, t

    v_free, _, _ = fall(fb, brake=False)
    fb.kit = Kit(fb.p, "reach")
    v, on_s, t_fall = fall(fb)
    if v > SAFE_LAND + 0.3:
        fails.append(f"jetpack fall off Spire's top ({start.z - floor:.1f} u): touched down at {v:.1f} u/s (want "
                     f"{SAFE_LAND} or less; no brake {v_free:.1f})")
    info.append(f"Spire fall {start.z - floor:.0f} u: {v_free:.1f} -> {v:.1f} u/s, jet {on_s:.1f} s")
    eb = Bot(2, 0, make_profile("novice", "rusher", random.Random(2)), spire, random.Random(2))
    eb.kit = Kit(eb.p, "reach")
    if fall(eb)[1] > 0:
        fails.append("an Easy bot used the jetpack (Easy uses no armor ability)")
    chk = Bot(3, 0, make_profile("top", "rusher", random.Random(3)), spire, random.Random(3))
    chk.kit = Kit(chk.p, "reach")
    chk.kit.kind, chk.kit.energy = "jetpack", Energy("reach", "jetpack")
    brake = getattr(chk.kit, "jet_brake", lambda *a: False)
    for z, vz, want in ((start.z - 4.0, -8.0, False), (start.z - 4.0, -12.0, True), (floor + 2.0, -3.0, False), (floor + 2.0, -7.0, True)):
        me = PlayerState(3, 0, "bot", Vec(start.x, start.y, z), vel=Vec(0, 0, vz), alive=True, equipment="jetpack")
        if brake(chk, 1.0, me) != want:
            fails.append(f"fall brake {z - floor:.0f} u over the floor at {-vz} u/s down: {not want} (want {want})")

    # 4. the jetpack climb over the stairs
    goal = A + Vec(5.0, 0.0, 3.0)

    def climb(wp, seen=False):
        b = bot("top", "reach", "jetpack")
        b.wp, b.goal = wp, ("objective", goal)
        foes = [foe(A + Vec(-8, 0, 0))] if seen else []
        if seen:
            from brain.bot import Belief
            b.per.beliefs[2] = Belief(foes[0].pos, Vec(), 1.0, True, "eyes")
            b.per.recognized.add(2)
        me = PlayerState(b.id, 0, "bot", A, alive=True, equipment="jetpack")
        snap = Snapshot(1.0, [me] + foes)
        b.kit.perceive(b, 1.0, me, snap)
        p = b.kit.plan(b, 1.0, me, snap)
        a = Action(forward=1.0)                        # the walk's stick: on toward the waypoint (north)
        b.kit.act(b, 1.0, DT, me, snap, a)
        return p, a

    p, a = climb(A + Vec(0.0, 2.0, 0.0))               # the stairs start north: the walk winds round
    if not p or p[1] != "fly" or p[2] != goal:
        fails.append(f"jetpack climb: a goal 3 u up 5 u off past winding stairs planned {p and p[:2]} (want fly to it)")
    elif abs(math.atan2(a.strafe, a.forward)) > 0.15 or not a.ability:
        fails.append(f"jetpack climb: stick {a.forward:.2f}/{a.strafe:.2f} hold bit {a.ability} (want straight at the "
                     f"goal, east, held)")
    p, _ = climb(A + Vec(2.0, 0.0, 0.6))
    if p and p[1] == "fly":
        fails.append("jetpack climb: flown while the walk already heads at the goal")
    p, _ = climb(A + Vec(0.0, 2.0, 0.0), seen=True)
    if p and p[1] == "fly":
        fails.append("jetpack climb: flown with a man in sight (a flyer cannot strafe)")

    # 5. armor lock held while the rocket stays on it
    b = bot("strong", "reach", "armor_lock")
    west = A + Vec(-10.0, 0.0, 0.0)
    rocket = lambda t: [foe(west, weapon="rockets", yaw=0.0 if t < 3.0 else math.pi / 2)]
    acts = run(b, 0.0, 4.5, rocket)
    held = [t for t, x, _ in acts if x.equipment]
    gap = [t for t, x, _ in acts if 0.6 < t < 2.9 and not x.equipment]
    late = [t for t in held if t > 3.6]
    if not held or gap:
        fails.append(f"armor lock: let go at {gap[:1]} s with the rocket still on it (want held to 3 s)")
    if late:
        fails.append(f"armor lock: still held {late[0]:.1f} s, the rocket looked away at 3.0 s (want let go by 3.6)")
    info.append(f"lock {held[0] if held else -1:.1f}-{held[-1] if held else -1:.1f}s")

    # 6. Halo 3: a trip mine goes down on a route people drove once the enemy drives (Sandtrap's rides.json)
    sand = get_map("h3_shrine")
    mb = Bot(4, 0, make_profile("strong", "rusher", random.Random(4)), sand, random.Random(4))
    mb.kit = Kit(mb.p, "h3")
    TS = mb.T()
    from brain.terrain import NAV_CELL
    l, j, i = sorted(getattr(TS, "drive_paint", [(0, 0, 0)]))[len(getattr(TS, "drive_paint", [0])) // 2]
    road = Vec(TS.x0 + (i + 0.5) * NAV_CELL, TS.y0 + (j + 0.5) * NAV_CELL, float(TS.lz[l, j, i]))

    def mine_plan(driving):
        from brain.bot import Belief
        mb.goal = ("roam", road + Vec(20, 0, 0))
        hog = PlayerState(9, 1, "human", road + Vec(30, 0, 0), alive=True, vehicle=7 if driving else -1)
        mb.per.beliefs[9] = Belief(hog.pos, Vec(), 1.0, False, "radar")
        me = PlayerState(mb.id, 0, "bot", road, alive=True, equipment="trip_mine")
        snap = Snapshot(1.0, [me, hog])
        mb.kit.perceive(mb, 1.0, me, snap)
        mb.kit.cool.clear()
        return mb.kit.plan(mb, 1.0, me, snap)

    p = mine_plan(True)
    if not p or p[0] != "trip_mine" or p[2] is None or TS._node_at(p[2].x, p[2].y, p[2].z, tol=0.6) not in set(TS.drive_paint):
        fails.append(f"Halo 3 trip mine: the enemy drives, the bot on a driven route planned {p and p[:3]} (want the mine "
                     f"on the route)")
    if mine_plan(False):
        fails.append("Halo 3 trip mine: planted on the road with nobody driving")

    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("ability hold OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
