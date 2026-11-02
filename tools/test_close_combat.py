"""Offline checks for what the player's Reach game showed (tools/engagement.py on
logs/trace_reach_50_panopticon.jsonl): an armor lock the game never got froze bots in the open; a plasma
launcher bot fought him 28 s at arm's length without one shot (no melee in Reach, its own blast, the aim
chasing a man circling it); bots stuck mid-fight wiggled at random; shotguns fired at 10+ units. Plus
the Halo 3 CTF game where no bot touched a flag (flags were never found).

usage: python -I test_close_combat.py      -> "close combat OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import Kit  # noqa: E402
from brain.live import NONE, flags_by_stand, one_flag_owner  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
A = Vec(70.0, -120.0, T.nav_z(70.0, -120.0))
DT = 1 / 30


def bot(i=1, tier="top", weapon="assault_rifle", weapons=None, can_melee=True, game="reach", kind=""):
    b = Bot(i, 0, make_profile(tier, "rusher", random.Random(i)), MAP, random.Random(i))
    b.kit = Kit(b.p, game)
    b.can_melee = can_melee
    b.can_pickup = False          # no run for a power item before it has noticed the man in front
    b.weapon, b.weapons, b.kind = weapon, weapons or [weapon], kind
    return b


def run(b, t1, foes, pos=lambda t: A, los=T.los):
    out, t, yaw, pitch = [], 0.0, math.pi, 0.0
    while t < t1:
        me = PlayerState(b.id, 0, "bot", pos(t), yaw=yaw, pitch=pitch, alive=True, weapon=b.weapon,
                         weapons=list(b.weapons), equipment=b.kind)
        fs = foes(t) if callable(foes) else foes
        a = b.think(t, DT, Snapshot(t, [me] + fs), los, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        out.append((t, a, list(b.notes)))
        t += DT
    return out


def main():
    fails = []
    west = A + Vec(-10.0, 0.0, 0.0)

    # 1. no equipment button in this game (live Reach before the decode): no armor lock plan, so no
    #    freezing in the open; with the button, it locks
    for pressable, want in ((False, False), (True, True)):
        b = bot(kind="armor_lock")
        b.kit.pressable = pressable
        acts = run(b, 2.0, [PlayerState(2, 1, "human", west, alive=True, weapon="rockets", yaw=0.0)])
        locked = sum(1 for t, a, _ in acts if t > 0.5 and a.equipment)
        if bool(locked) != want:
            fails.append(f"button reaches the game = {pressable}: armor lock planned {locked} ticks")
        if not pressable and sum(1 for t, a, _ in acts if t > 0.5 and a.fire) == 0:
            fails.append("without the button the bot did not fight the rocket man")

    # 2. a man circling us at arm's length: shoot while turning (it was never "on target")
    w = 2.25                                               # run speed (2.25 units/s) on a 1-unit circle
    circle = lambda t: [PlayerState(2, 1, "human", A + Vec(math.cos(w * t), math.sin(w * t), 0.0),
                                    vel=Vec(-w * math.sin(w * t), w * math.cos(w * t), 0.0), alive=True, yaw=0.0)]
    acts = run(bot(), 4.0, circle)
    share = sum(1 for t, a, _ in acts if t > 1.0 and a.fire) / sum(1 for t, a, _ in acts if t > 1.0)
    if share < 0.3:
        fails.append(f"point blank vs a circling man: fired {share:.0%} of ticks")

    # 3. plasma launcher, nothing else, no melee in this game, he stays at arm's length: trade after
    #    1.5 s; with melee there is a melee and no shot inside the blast
    near = [PlayerState(2, 1, "human", A + Vec(-1.2, 0.0, 0.0), alive=True, yaw=0.0)]
    acts = run(bot(weapon="plasma_launcher", can_melee=False), 3.0, near)
    shots = [t for t, a, _ in acts if a.fire]
    if not shots or shots[0] < 1.5:
        fails.append(f"one launcher, no melee, cornered: first shot at {shots[0] if shots else None} (want after 1.5 s)")
    acts = run(bot(weapon="plasma_launcher", can_melee=True), 3.0, near)
    if any(a.fire for _, a, _ in acts) or not any(a.melee for _, a, _ in acts):
        fails.append("launcher at arm's length with melee: fired or did not melee")

    # 4. a launcher and a magnum at arm's length: switch to the magnum (it kept the launcher)
    acts = run(bot(weapon="plasma_launcher", weapons=["plasma_launcher", "magnum"]), 2.0, near)
    if not any(a.weapon == 1 for _, a, _ in acts):
        fails.append("did not switch from the launcher to the magnum at point blank")

    # 5. a shotgun at 12 units holds its fire (62% of shotgun shots were out of reach). At 3 units (fires before
    #    ffbfb4d, holds since) and 2: awaits the player, tools/test_spec_pending.py
    for d, want in ((12.0, False),):
        acts = run(bot(weapon="shotgun"), 2.5, [PlayerState(2, 1, "human", A + Vec(-d, 0, 0), alive=True, yaw=0.0)])
        if any(a.fire for t, a, _ in acts if t > 0.6) != want:
            fails.append(f"shotgun at {d} units: fired = {not want}")

    # 6. blocked mid-fight: strafe the other way, not the random wiggle; a man standing in us: step back
    b = bot()
    acts = run(b, 3.0, [PlayerState(2, 1, "human", west, alive=True, yaw=0.0)])      # we never move: a wall
    ns = [n for _, _, nn in acts for n in nn]
    if not any("strafe the other way" in n for n in ns) or any("unstuck wiggle" in n for n in ns[:1]):
        fails.append(f"blocked in a fight: {sorted(set(ns))[:4]}")
    b = bot()
    acts = run(b, 3.0, [PlayerState(2, 1, "human", A + Vec(-0.8, 0.0, 0.0), alive=True, yaw=0.0)])
    if not any("body block" in n for _, _, nn in acts for n in nn):
        fails.append("a man standing in us: no step back")

    # 7. Halo 3 flags: found on the stands, carried, a respawned one takes its stand's team, other
    #    weapons are not flags
    stands = {0: Vec(0.0, 0.0, 1.0), 1: Vec(30.0, 0.0, 1.0)}
    tags, teams = set(), {}
    weapons = [(1, 77, NONE, (0.1, 0.2, 1.2)), (2, 77, NONE, (30.0, -0.3, 1.0)), (3, 55, NONE, (12.0, 4.0, 1.0))]
    got = flags_by_stand(weapons, {}, stands, tags, teams)
    if sorted((f["team"], f["carrier"]) for f in got) != [(0, None), (1, None)]:
        fails.append(f"flags on their stands: {got}")
    carrier = dict(index=5, pos=(15.0, 1.0, 1.0))
    got = flags_by_stand([(1, 77, 999, (15.0, 1.0, 1.3)), (2, 77, NONE, (30.0, 0.0, 1.0))], {1: carrier}, stands, tags, teams)
    if dict((f["team"], f["carrier"]) for f in got) != {0: 5, 1: None}:
        fails.append(f"red flag carried by #5: {got}")
    got = flags_by_stand([(9, 77, NONE, (0.0, 0.1, 1.0))], {}, stands, tags, teams)
    if [f["team"] for f in got] != [0]:
        fails.append(f"a flag respawned at home: {got}")
    # a rifle dropped on a stand later is no flag (Reach: a swap on their stand made every rifle one)
    got = flags_by_stand([(9, 77, NONE, (0.0, 0.1, 1.0)), (4, 55, NONE, (30.1, 0.1, 1.0))], {}, stands, tags, teams)
    if [f["team"] for f in got] != [0] or 55 in tags:
        fails.append(f"a rifle on a stand read as a flag: {got}")
    # a fresh reader: a gun on a stand that a player holds a copy of is no flag; a flag first seen carried is
    # the carrier's enemy's (its object reads 0, 0, 0)
    tags2, teams2 = set(), {}
    red = dict(index=3, team=0, pos=(20.0, 0.0, 1.0))
    got = flags_by_stand([(6, 55, NONE, (30.0, 0.0, 1.0)), (7, 55, 999, (0.0, 0.0, 0.0))], {7: red}, stands, tags2, teams2)
    if got or tags2:
        fails.append(f"a held gun's tag learned as a flag: {got} {tags2}")
    tags2.add(77)
    got = flags_by_stand([(8, 77, 999, (0.0, 0.0, 0.0))], {8: red}, stands, tags2, teams2)
    if [(f["team"], f["carrier"]) for f in got] != [(1, 3)]:
        fails.append(f"a flag first seen carried by red: {got}, want blue's")
    # One Flag: the flag keeps stand 0 while the sides swap; each new round's flag object belongs to the team that
    # spawns beside it (Boardwalk: round 2's defenders were blue, on red's stand)
    state = {}
    flag = dict(team=0, stand=0, handle=50, pos=(0.0, 0.0, 1.0), carrier=None)
    ppl = [dict(index=1, team=1, pos=(1.0, 1.0, 1.0)), dict(index=2, team=1, pos=(2.0, 0.0, 1.0)),
           dict(index=3, team=0, pos=(30.0, 0.0, 1.0))]
    owner_r2 = one_flag_owner(flag, ppl, state)
    owner_r2_later = one_flag_owner(flag, [dict(index=3, team=0, pos=(0.5, 0.0, 1.0))], state)   # red reaches it: no flip
    flag3 = dict(flag, handle=51)
    owner_r3 = one_flag_owner(flag3, [dict(index=3, team=0, pos=(1.0, 0.0, 1.0))], state)
    if (owner_r2, owner_r2_later, owner_r3) != (1, 1, 0):
        fails.append(f"one flag owners {owner_r2, owner_r2_later, owner_r3}, want 1, 1 (kept), then 0 (next round)")

    # 9. no melee press from 1.4 u (his own
    #    close melees 18 of 19 within 1.18 u; bots pressed it from 1.55 u), one at 1.2 u (arm's length, above)
    for d, want in ((1.4, False), (1.2, True)):
        acts = run(bot(), 3.0, [PlayerState(2, 1, "human", A + Vec(-d, 0.0, 0.0), alive=True, yaw=0.0)])
        if any(a.melee for _, a, _ in acts) != want:
            fails.append(f"a man {d} u off: melee {'pressed' if not want else 'never pressed'} (want {'one' if want else 'none'})")

    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("close combat OK")


if __name__ == "__main__":
    main()
