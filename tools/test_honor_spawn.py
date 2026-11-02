"""Invasion respawns by the player's honor system ("if tier 1 > Spawn river unlocked, Spawn Spire locked, if tier 2 >
Spawn spire unlocked, Elites prefer spire spawn, Spartans prefer River and surrounding area spawn and ally"; the spawn
names he read off the spawn screen in match 211159: River, Conveyor Belt for the Spartans, BFG, High Trail #1 and #2
for the Elites). brain/invasion.py honor_spawn, tools/live_bots.py spawn_check, botctl.spawn_at:

1. Spire's named spawns: who gets each, in which phases, every point on floor
2. phase 1: Spartans only River, Elites only BFG (the spire locked); phases 2-3: Elites only the High Trails, Spartans
   River or Conveyor Belt, River most
3. a teammate out of the fight: Spartans spawn behind him about half the time (1 u, on floor, in his sight, facing his
   way); never behind one who is hurt, seen by an enemy within 25 u, in a vehicle or carrying the core
4. two bots picking at once never share a point, nor one a player stands on
5. spawn_check: nothing before the sides are known; a dead bot's pick sent once (traced with its name), again in a new
   phase; a spot behind a teammate redone every half second, the pick redone when he is no longer clear; under half the
   players alive (a round's change) a pick sent is called off (NaN) and nothing is sent; watch.placed lists the bots
   with a pick out, and the Watch keeps their respawns out of its phase vote
6. botctl.spawn_at: the target at OFF_SPAWN + 16 x index, its seq bumped after; SIZE = native/shared.h's size

usage: python -I test_honor_spawn.py      -> "honor spawn OK"
"""
import io
import json
import math
import os
import random
import re
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import botctl  # noqa: E402
import live_bots  # noqa: E402
from brain import invasion  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

M = get_map("reach_35_island")
T = terrain(M)
SPAWNS = invasion.honor_spawns("reach_35_island")
RIVER = Vec(-112.7, -327.0, -63.2)                  # where the player spawned at River (phase 1)


def man(pid, team, pos, yaw=0.0, **k):
    return PlayerState(pid, team, f"p{pid}", pos, yaw=yaw, **k)


def names(phase, side, players=(), n=400):
    rng, me = random.Random(1), man(9, 0 if side == "att" else 1, Vec(), alive=False)
    out = Counter()
    for _ in range(n):
        o = invasion.honor_spawn(SPAWNS, phase, side, me, list(players), rng, T)
        out["ally" if o["mate"] is not None else o["name"]] += 1
    return out


def main():
    fails = []
    # 1. the data
    if SPAWNS is None:
        sys.exit("FAIL: no named spawns for Spire (maps/reach_35_island/inv_spawns.json)")
    named = SPAWNS[0]
    got = {n["name"]: (n["side"], sorted(n["points"])) for n in named}
    want = {"River": ("att", ["1", "2", "3"]), "Conveyor Belt": ("att", ["2", "3"]), "BFG": ("def", ["1"]),
            "High Trail #1": ("def", ["2", "3"]), "High Trail #2": ("def", ["2", "3"])}
    if got != want:
        fails.append(f"Spire's named spawns {got} (want {want})")
    off = [(n["name"], ph, p) for n in named for ph, pts in n["points"].items() for p in pts
           if not T.ground_ok(p[0], p[1], p[2] + 0.4, drop=1.0)]
    if off or any(not pts for n in named for pts in n["points"].values()):
        fails.append(f"named spawn points off the floor or none: {off}")
    # 2. who spawns where, no teammate to spawn on
    for phase, side, allowed in ((1, "att", {"River"}), (1, "def", {"BFG"}), (2, "def", {"High Trail #1", "High Trail #2"}),
                                 (3, "def", {"High Trail #1", "High Trail #2"}), (2, "att", {"Conveyor Belt"}),
                                 (3, "att", {"Conveyor Belt"})):
        c = names(phase, side)
        if set(c) != allowed:
            fails.append(f"phase {phase} {side}: spawned at {dict(c)} (want only {sorted(allowed)}, each)")
    # 2b. phases 2-3 (the player match 221404): River only
    #     with a free vehicle by it, and then for it (ride); not one that is taken or another bot's errand
    hog = dict(handle=41, kind="warthog", pos=(-122.3, -313.5, -60.2), occupied=False)
    me = man(9, 0, Vec(), alive=False)
    picks = [invasion.honor_spawn(SPAWNS, 2, "att", me, [], random.Random(k), T, vehicles=[hog]) for k in range(400)]
    river = [o for o in picks if o["name"] == "River"]
    if not 0.1 <= len(river) / 400 <= 0.3 or any(o["ride"] != 41 for o in river) or any(o["ride"] for o in picks
                                                                                       if o["name"] != "River"):
        fails.append(f"phase 2 Spartans, a free Warthog by River: {Counter(o['name'] for o in picks)}, rides "
                     f"{Counter(o['ride'] for o in picks)} (want a few at River, each for the Warthog, most at Conveyor Belt)")
    for why, kw in (("taken", dict(vehicles=[dict(hog, occupied=True)])), ("another bot's errand", dict(vehicles=[hog], errands={41})),
                    ("70 u off", dict(vehicles=[dict(hog, pos=(-160.0, -370.0, -55.0))]))):
        if any(invasion.honor_spawn(SPAWNS, 2, "att", me, [], random.Random(k), T, **kw)["name"] == "River" for k in range(200)):
            fails.append(f"phase 2 Spartans spawned at River with its vehicle {why}")
    # 3. a teammate out of the fight
    mate = man(3, 0, RIVER, yaw=0.5)
    c = names(1, "att", [mate])
    if not 0.35 <= c["ally"] / 400 <= 0.65 or set(c) != {"ally", "River"}:
        fails.append(f"phase 1 Spartans with a clear teammate: {dict(c)} (want about half behind him, the rest River)")
    o = invasion.honor_spawn(SPAWNS, 1, "att", man(9, 0, Vec(), alive=False), [mate], random.Random(3), T)
    while o["mate"] is None:
        o = invasion.honor_spawn(SPAWNS, 1, "att", man(9, 0, Vec(), alive=False), [mate], random.Random(), T)
    p = o["pos"]
    behind = math.cos(math.atan2(p.y - mate.pos.y, p.x - mate.pos.x) - mate.yaw) < -0.5
    if not (0.9 <= (p - mate.pos).flat() <= 1.1 and behind and T.ground_ok(p.x, p.y, p.z + 0.4, drop=1.0)
            and T.los(mate.pos, p) and o["yaw"] == mate.yaw and o["mate"] == 3):
        fails.append(f"the spot behind a teammate: {o} (want 1 u behind him, on floor, in his sight, his facing)")
    seen = next((man(20, 1, q) for q in (Vec(RIVER.x + 6.0 * math.cos(a / 6.0), RIVER.y + 6.0 * math.sin(a / 6.0), RIVER.z)
                                         for a in range(38)) if T.ground_ok(q.x, q.y, q.z + 0.4) and T.los(q, mate.pos)),
                man(20, 1, RIVER))
    if not T.los(seen.pos, mate.pos) or (seen.pos - mate.pos).flat() < 5.0:
        fails.append("(test setup: the enemy 6 u off cannot see the teammate)")
    for why, players in (("hurt", [man(3, 0, RIVER, yaw=0.5, shield=0.6)]), ("seen by an enemy 6 u off", [mate, seen]),
                         ("in a vehicle", [man(3, 0, RIVER, yaw=0.5, vehicle=0x1234)]),
                         ("carrying the core", [man(3, 0, RIVER, yaw=0.5, has_flag=True)]),
                         ("dead", [man(3, 0, RIVER, yaw=0.5, alive=False)])):
        c = names(1, "att", players, n=60)
        if c["ally"]:
            fails.append(f"spawned behind a teammate {why}: {dict(c)}")
    far = man(20, 1, Vec(RIVER.x - 30.0, RIVER.y, RIVER.z))
    if not names(1, "att", [mate, far], n=200)["ally"]:
        fails.append("an enemy 30 u off kept every bot off a clear teammate (want only within 25 u)")
    # 4. no shared points
    rng, picks = random.Random(5), []
    standing = man(4, 0, Vec(*next(n for n in named if n["name"] == "BFG")["points"]["1"][0]))
    for k in range(5):
        o = invasion.honor_spawn(SPAWNS, 1, "def", man(10 + k, 1, Vec(), alive=False), [standing], rng, T,
                                 taken=[q["pos"] for q in picks])
        picks.append(o)
    close = [(a["pos"], b["pos"]) for i, a in enumerate(picks) for b in picks[i + 1:] if (a["pos"] - b["pos"]).flat() < 0.8]
    if close or any((q["pos"] - standing.pos).flat() < 0.8 for q in picks):
        fails.append(f"bots picking BFG at once shared a point or took one a player stands on: {close}")
    # 5. spawn_check
    sent = []
    send = lambda i, x, y, z, yaw: sent.append((i, x, y, z, yaw))

    class W:                                       # the Invasion watcher's fields spawn_check reads
        sides_set, placed = False, set()
    w, state, trace = W(), {}, io.StringIO()
    bots = {5: type("B", (), {})()}
    living = [man(k, 1, Vec(RIVER.x + 3.0 * k, RIVER.y - 40.0, RIVER.z)) for k in range(6, 12)]   # enemies, 40 u off
    dead = man(5, 0, Vec(), alive=False)

    def tick(now, phase=1, players=None, alive_bot=False):
        bot = man(5, 0, RIVER) if alive_bot else dead
        snap = Snapshot(now, [bot] + (living if players is None else players), mode="invasion", inv_phase=phase,
                        inv_attackers=0, inv_zones=[Vec(-159.8, -348.6, -55.1)])
        live_bots.spawn_check(send, bots, snap, now, state, SPAWNS, w, random.Random(int(now * 10)), T, trace)

    tick(1.0)
    if sent:
        fails.append(f"sent a pick before the sides were known: {sent}")
    w.sides_set = True
    tick(2.0)
    tick(2.5)
    tick(3.0)
    lines = [json.loads(x) for x in trace.getvalue().splitlines()]
    if len(sent) != 1 or sent[0][0] != 5 or not lines or lines[0].get("spawn") != "River" or w.placed != {5}:
        fails.append(f"a dead attacker in phase 1: sent {sent}, traced {lines}, placed {w.placed} (want River once, placed)")
    tick(3.5, phase=2)
    if len(sent) != 2:
        fails.append(f"a new phase: sent {len(sent) - 1} more (want the pick redone once)")
    # a River pick for its vehicle is the bot's errand, and the bot goes for that vehicle once it is in (Bot.decide)
    from brain.bot import Bot
    from brain.profiles import make_profile
    real = Bot(5, 0, make_profile("strong", "objector", random.Random(5)), M, random.Random(5))
    real._terrain = T
    eb, ewatch, estate = {5: real}, W(), {}
    ewatch.sides_set = True
    for k in range(60):
        estate.clear()
        snap = Snapshot(50.0 + k, [man(5, 0, Vec(), alive=False)] + living, mode="invasion", inv_phase=2, inv_attackers=0,
                        inv_zones=[Vec(-178.7, -398.4, -58.8)], vehicles=[hog])
        live_bots.spawn_check(lambda *a: None, eb, snap, 50.0 + k, estate, SPAWNS, ewatch, random.Random(k), T)
        if estate[5]["pick"]["name"] == "River":
            break
    if getattr(real, "errand", None) is None or real.errand[0] != 41:
        fails.append(f"a River pick in phase 2 with the Warthog by it: errand {getattr(real, 'errand', None)} (want the Warthog)")
    else:
        at = man(5, 0, Vec(-119.0, -313.0, -60.2))
        snap = Snapshot(55.0 + k, [at] + living, mode="invasion", inv_phase=2, inv_attackers=0,
                        inv_zones=[Vec(-178.7, -398.4, -58.8)], vehicles=[hog])
        real.vehicle_retry_at = 1e9               # (no trip by vehicle of its own: only the errand can send it)
        got = real.decide(55.0 + k, at, snap)
        if got != ("vehicle", 41):
            fails.append(f"spawned at River for the Warthog: decided {got} (want the Warthog)")
    sent.clear()
    tick(4.0, phase=2, alive_bot=True)
    if sent or state.get(5) or w.placed:
        fails.append(f"respawned: sent {sent}, state {state.get(5)}, placed {w.placed} (want it all cleared)")
    # a pick behind a teammate: redone every half second as he moves, redone elsewhere once he is hurt
    friend = man(6, 0, RIVER, yaw=0.5)
    others = [friend] + living[1:]
    for k in range(40):
        state.clear()
        sent.clear()
        tick(10.0 + k, players=others)
        if state[5]["pick"]["mate"] == 6:
            break
    else:
        fails.append("(test setup: no pick behind the teammate in 40 tries)")
    t = state[5]["t"]
    tick(t + 0.2, players=others)
    n_quiet = len(sent)
    friend.pos = Vec(RIVER.x + 1.0, RIVER.y + 0.5, RIVER.z)
    tick(t + 0.6, players=others)
    moved = sent[-1] if len(sent) > n_quiet else None
    if n_quiet != 1 or moved is None or math.dist(moved[1:3], (friend.pos.x, friend.pos.y)) > 1.1:
        fails.append(f"behind a teammate: sends {sent} (want none at 0.2 s, one at 0.6 s 1 u from where he is now)")
    friend.shield = 0.5
    tick(t + 1.2, players=others)
    if state[5]["pick"]["mate"] is not None:
        fails.append(f"the teammate hurt: the pick stayed on him ({state[5]['pick']})")
    # a round's change: everyone dead
    sent.clear()
    tick(30.0, players=[man(k, k % 2, Vec(), alive=False) for k in range(6, 12)])
    if len(sent) != 1 or not math.isnan(sent[0][1]) or state.get(5) or w.placed:
        fails.append(f"under half the players alive: sent {sent}, state {state.get(5)} (want the pick called off: NaN)")
    tick(31.0, players=[man(k, k % 2, Vec(), alive=False) for k in range(6, 12)])
    if len(sent) != 1:
        fails.append(f"still under half alive: sent {sent[1:]} (want nothing)")
    # the Watch: a placed bot's respawn says nothing of the phase
    inv = invasion.layout(M["objects"])
    wt = invasion.Watch(inv, T)
    wt.placed = {5}
    snap = Snapshot(40.0, [man(5, 0, Vec(), alive=False), man(6, 0, RIVER)], mode="invasion")
    wt.update(None, snap, 40.0)
    snap = Snapshot(41.0, [man(5, 0, RIVER), man(6, 0, RIVER)], mode="invasion")
    wt.update(None, snap, 41.0)
    if any(abs(p.x - RIVER.x) < 1e-6 and team == 0 and t_ == 41.0 for t_, team, p in wt.spawns):
        fails.append(f"the Watch counted a placed bot's respawn: {wt.spawns}")
    # 7. the simulator spawns the same way (brain/sim_modes.py spawn_points: sim team 1 attacks)
    from brain.sim import Sim
    s = Sim(mode="invasion", per_team=(1, 1), seed=1, map_name="reach_35_island")
    for phase in (1, 2, 3):
        s.objmodes.phase = phase
        for team, side in ((1, "att"), (0, "def")):
            ok = {tuple(p) for n in named if n["side"] == side for p in n["points"].get(str(phase), [])}
            got = {(round(p.x, 3), round(p.y, 3), round(p.z, 3)) for _ in range(40) for p in s.objmodes.spawn_points(team)}
            if not got or not got <= {tuple(round(v, 3) for v in q) for q in ok}:
                fails.append(f"the simulator's phase {phase} {side} spawns: {sorted(got)[:4]} (want only its named spawns' points)")
    # 6. botctl
    shared = open(os.path.join(HERE, "..", "native", "shared.h")).read()
    size = int(re.search(r"sizeof\(hb_shared\) == (\d+)", shared).group(1))
    m = bytearray(botctl.SIZE)
    botctl.spawn_at(m, 3, 1.5, -2.5, 3.25, 0.5)
    botctl.spawn_at(m, 3, 1.5, -2.5, 3.25, 0.5)
    if (botctl.SIZE != size or struct.unpack_from("<4f", m, botctl.OFF_SPAWN + 48) != (1.5, -2.5, 3.25, 0.5)
            or struct.unpack_from("<I", m, botctl.OFF_SPAWN + 256 + 12)[0] != 2):
        fails.append(f"botctl.spawn_at / SIZE {botctl.SIZE} vs shared.h {size}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"honor spawn OK (phase 2 Spartans: {dict(names(2, 'att'))}; Elites: {dict(names(2, 'def'))})")


if __name__ == "__main__":
    main()
