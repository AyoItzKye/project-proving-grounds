"""Objective game types (brain/modes.py): Reach variant names to modes, the map's places with their sizes, Territories
ownership after CAPTURE_S alone in a zone, Assault goals per team (four-team stands left out), Infection's infected
team by swords, and a short simulated game per mode moving its objective (brain/sim_modes.py).

usage: python -I test_modes.py      -> "modes OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import modes  # noqa: E402
from brain.core import Vec, Snapshot, PlayerState  # noqa: E402
from brain.maps import get_map  # noqa: E402


def main():
    fails = []
    want = {"TERRITORIES": "territories", "LAND GRAB": "territories", "ASSAULT": "assault", "NEUTRAL BOMB": "assault",
            "STOCKPILE": "stockpile", "HEADHUNTER PRO": "headhunter", "INFECTION": "infection", "SAFE HAVEN": "infection",
            "JUGGERNAUT": "juggernaut", "TEAM SLAYER": None, "INVASION: BONEYARD": None, "CAPTURE THE FLAG": None}
    for name, mode in want.items():
        if modes.detect(name) != mode:
            fails.append(f"{name!r} -> {modes.detect(name)}, want {mode}")
    # Halo 2's places (its Territories and Assault played as Slayer before: no names for its flags), Halo 4 / H2A's
    # Ricochet, Grifball and Dominion played as Assault / Territories on their own places
    for name, mode in (("RICOCHET", "ricochet"), ("GRIFBALL", "grifball"), ("DOMINION", "dominion"),
                       ("Team Territories", "territories"), ("Neutral Bomb", "assault"), ("3 Plots", "territories")):
        if modes.detect(name) != mode:
            fails.append(f"{name!r} -> {modes.detect(name)}, want {mode}")
    # H2A's seven built-in Territories variants (live: all seven started, every one engine icon 8): by name or icon 8
    for name in ("3 Plots", "Incursion", "Land Grab", "Gold Rush", "Control Issues", "Contention", "Lockdown"):
        if (modes.detect(name) or modes.H2A_ICONS.get(8)) != "territories":
            fails.append(f"H2A {name!r}: read as {modes.detect(name) or modes.H2A_ICONS.get(8)} (want territories)")
    # modes.mode_of, the live loop's read: each game's way, and a reader that raises is None (played as Slayer), never
    # a crash of the brain's tick (Code Master DD-01 item 8)
    class Stub:
        def __init__(s, name="", icon=2, engine=2, fail=False):
            s.name, s.icon, s.eng, s.fail = name, icon, engine, fail

        def variant_name(s):
            if s.fail:
                raise OSError("read failed")
            return s.name

        def variant(s):
            return {"name": s.variant_name()}

        def engine_icon(s):
            if s.fail:
                raise OSError("read failed")
            return s.icon

        def engine(s):
            return s.eng
    for game, stub, want in (("h2a", Stub("3 Plots"), "territories"), ("h2a", Stub("Gold Rush", icon=8), "territories"),
                             ("h2a", Stub("Team Slayer", icon=1), None), ("h2", Stub("$multi_bomb"), "assault"),
                             ("h3", Stub(engine=6), "territories"), ("reach", Stub("Gold Rush", icon=8), None),
                             ("h2a", Stub(fail=True), None), ("reach", Stub(fail=True), None)):
        try:
            got = modes.mode_of(game, stub)
        except Exception as e:                   # (a raise out of mode_of would stop the live tick)
            got = f"raised {type(e).__name__}"
        if got != want:
            fails.append(f"mode_of({game}, {stub.name!r}, icon {stub.icon}, fail {stub.fail}) -> {got} (want {want})")
    # Halo 4 Extraction plays as Slayer until its live sites are read (live Adrift: the plant itself was done by the
    # host, but the reader of 82b3b55 followed where players stood, not the live sites, and was backed out)
    if modes.detect("Extraction") is not None:
        fails.append(f"'Extraction' -> {modes.detect('Extraction')} (want None: Slayer until its live sites are read)")
    h2 = modes.layout(get_map("h2_ascension")["objects"])
    goals = sorted({t for _, _, t in h2.get("bomb_goal", [])})
    if len(h2.get("territory", [])) < 5 or goals != [0, 1] or len(h2.get("bomb", [])) != 3:
        fails.append(f"Halo 2 Ascension: {len(h2.get('territory', []))} territories, bomb goals of teams {goals}, "
                     f"{len(h2.get('bomb', []))} bomb stands (want 5+, [0, 1], 3)")
    for kind, objs_map, want_mode, stand, goal in (("ricochet", "h4_ca_creeper", "assault", "rico_ballspawn", "rico_endzone"),
                                                    ("grifball", "h4_ca_canyon", "assault", "grif_spawn", "grif_goal")):
        try:
            o = get_map(objs_map)["objects"]
        except Exception:
            continue
        w = modes.Watch(kind, o, "h4")
        n_s = sum(f["type"] == stand for f in o["netgame_flags"])
        n_g = sum(f["type"] == goal for f in o["netgame_flags"])
        if w.mode != want_mode or w.kind != kind or len(w.lay.get("bomb", [])) != n_s or len(w.lay.get("bomb_goal", [])) != n_g:
            fails.append(f"{kind} on {objs_map}: played as {w.mode}, {len(w.lay.get('bomb', []))} stands / "
                         f"{len(w.lay.get('bomb_goal', []))} goals (want {want_mode}, {n_s} / {n_g}, its own places only)")
    objs = get_map("reach_30_settlement")["objects"]
    lay = modes.layout(objs)
    if len(lay.get("territory", [])) != 5 or not all(r == 2.0 or r == 2.5 for p, r, t in lay["territory"]):
        fails.append(f"Settlement territories {lay.get('territory')}")
    # Reach takes a territory in 30 s (guide 19 6.1): held alone, still nobody's at 15 s, team 0's at 31 s
    w = modes.Watch("territories", objs)
    z, r, _ = lay["territory"][0]
    owner = {}
    for t in range(32):
        ps = [PlayerState(1, 0, "a", z, Vec(), 0, 0, True, 1, 1, "dmr")]
        sn = Snapshot(float(t), ps)
        w.update(None, sn, float(t))
        owner[t] = sn.obj_zones[0][2]
    if owner[15] != -1 or owner[31] != 0:
        fails.append(f"a Reach zone held alone: owner at 15 s {owner[15]}, at 31 s {owner[31]} (want nobody, team 0)")
    w2 = modes.Watch("assault", objs)

    class Live:
        def objective_items(s, raw, stands, key):
            return [dict(pos=(stands[k].x, stands[k].y, stands[k].z), carrier=None, stand=k) for k in stands]
    sn = Snapshot(0.0, [])
    w2.update(Live(), sn, 0.0, raw=[])
    if set(sn.obj_goals) != {0, 1} or any(len(g) != 1 for g in sn.obj_goals.values()):
        fails.append(f"assault goals {sn.obj_goals} (want one each for teams 0 and 1)")
    if sorted(it["team"] for it in sn.obj_items) != [0, 1, 8]:
        fails.append(f"assault bombs' teams {[it['team'] for it in sn.obj_items]} (want 0, 1 and the neutral 8)")
    # team 1's bomb lying on team 0's goal with nobody carrying it is armed there; the bombs at home are not (Settlement's
    # team 0 stand lies in its own goal) (guide 19 ASS-MULTI-09/03): team 0 sends all but one onto it and may take it
    # (Use disarms), team 1 guards it and never takes it again
    import random
    from brain.bot import Bot
    from brain.director import Director
    from brain.profiles import make_profile
    if any(it.get("armed") is not None for it in sn.obj_items):
        fails.append(f"assault: a bomb at home read as armed {[it.get('armed') for it in sn.obj_items]}")
    placed = [(p, t) for p, r, t in lay["bomb"] if t in (0, 1, 8)]
    k0, k1 = (next(k for k, (p, t) in enumerate(placed) if t == team) for team in (0, 1))
    g0 = next(p for p, r, t in lay["bomb_goal"] if t == 0)

    class Planted:                                # (team 0 plays the neutral bomb: its own is not in this game)
        def objective_items(s, raw, stands, key):
            return [dict(pos=(g0.x, g0.y, g0.z) if k == k1 else (q.x, q.y, q.z), carrier=None, stand=k)
                    for k, q in stands.items() if k != k0]
    sa = Snapshot(0.0, [])
    modes.Watch("assault", objs).update(Planted(), sa, 0.0, raw=[])
    if sorted(map(str, (it.get("armed") for it in sa.obj_items))) != ["0", "None"]:
        fails.append(f"assault: team 1's bomb on team 0's goal: armed {[it.get('armed') for it in sa.obj_items]} "
                     f"(want 0 once)")
    sm = get_map("reach_30_settlement")
    for team, want in ((0, "runner"), (1, "defender")):
        dd = Director(team, sm, {i: Bot(i, team, make_profile("strong", "objector", random.Random(i)), sm, random.Random(i))
                                 for i in range(1, 5)}, rng=random.Random(1))
        on = [r for r, p, f in dd.mode_slots(0.0, sa, 4)[:4] if (p - g0).flat() < 0.5]
        if on != [want] * (3 if team == 0 else 1):
            fails.append(f"assault, team {team}, an armed bomb on team 0's goal: slots on it {on}")
        me = PlayerState(9, team, "p", g0 + Vec(0.5, 0, 0))
        took = Bot.on_loose_objective(me, sa)
        if (took is not None and (took - g0).flat() < 0.5) != (team == 0):
            fails.append(f"assault, team {team} on the armed bomb on team 0's goal: Use on {took}")
    inf = Snapshot(0.0, [PlayerState(1, 1, "z", Vec(), Vec(), 0, 0, True, 1, 1, "energy_sword"),
                         PlayerState(2, 0, "h", Vec(), Vec(), 0, 0, True, 1, 1, "shotgun")])
    if modes.zombie_team(inf) != 1:
        fails.append("infected team not found by swords")
    # Halo 3: a free for all (each his own team); the zombie is the one holding the kind nobody else holds, and a
    # survivor who dies comes back infected
    w3 = modes.Watch("infection", objs)
    ps = [PlayerState(i, i, "p", Vec(), Vec(), 0, 0, True, 1, 1, "unknown") for i in range(5)]
    raw = [dict(index=i, pos=(0, 0, 0), wtag=0xAA if i == 3 else 0xBB) for i in range(5)]
    sn = Snapshot(0.0, ps)
    w3.update(None, sn, 0.0, raw=raw)
    if [p.team for p in sn.players] != [0, 0, 0, 1, 0] or modes.zombie_team(sn) != 1:
        fails.append(f"Halo 3 infection split {[p.team for p in sn.players]}")
    ps = [PlayerState(i, i, "p", Vec(), Vec(), 0, 0, i != 1, 1, 1, "unknown") for i in range(5)]
    raw[1] = dict(index=1, pos=None, wtag=None)
    sn = Snapshot(1.0, ps)
    w3.update(None, sn, 1.0, raw=raw)
    if [p.team for p in sn.players] != [0, 1, 0, 1, 0]:
        fails.append(f"a dead survivor is not infected: {[p.team for p in sn.players]}")
    # Halo 3 Juggernaut (a free for all): the marked man against everyone else; nobody marked yet, as it is. VIP: each
    # team's marked man in snap.vips, our escorts follow ours, one hunts theirs
    class Marks:
        def __init__(s, ids):
            s.ids = ids

        def marked_players(s, raw):
            return set(s.ids)
    wj = modes.Watch("juggernaut", objs)        # (the Juggernaut: his overshield, live)
    for ids, want in (((), [0, 1, 2, 3, 4]), ((2,), [0, 0, 1, 0, 0])):
        sn = Snapshot(2.0, [PlayerState(i, i, "p", Vec(), Vec(), 0, 0, True, 3.0 if i in ids else 1.0, 1, "unknown")
                            for i in range(5)])
        wj.update(Marks(()), sn, 2.0, raw=raw)
        if [p.team for p in sn.players] != want or (ids and sn.infected != 1):
            fails.append(f"Halo 3 Juggernaut marked {ids}: teams {[p.team for p in sn.players]}, want {want}")
    # ... still him once hurt (his shield under 1.0: the split held 35% of a match on the shield alone, live)
    sn = Snapshot(3.0, [PlayerState(i, i, "p", Vec(), Vec(), 0, 0, True, 0.4, 1, "unknown") for i in range(5)])
    wj.update(Marks(()), sn, 3.0, raw=raw)
    if [p.team for p in sn.players] != [0, 0, 1, 0, 0]:
        fails.append(f"Halo 3 Juggernaut hurt: teams {[p.team for p in sn.players]}, want him still marked")
    # a bot drops the fight with the man who just became its ally (live: at 60 s every bot still fought its old
    # opponent, its foes list only the juggernaut)
    import random
    from brain.bot import Bot, Belief
    from brain.profiles import make_profile
    jb = Bot(1, 0, make_profile("strong", "rusher", random.Random(1)), get_map("h3_construct"), random.Random(1))
    jb.goal = ("fight", 3)
    jb.per.beliefs[3] = Belief(Vec(3, 0, 0), Vec(), 0.0, True, "eyes")
    jb.think(4.0, 0.1, sn, lambda a, c: True, lambda a, c, **k: c, [])
    if jb.goal == ("fight", 3) or 3 in jb.per.beliefs:
        fails.append(f"Juggernaut: a bot still fights its new ally: {jb.goal}")
    from brain.bot import Bot
    from brain.director import Director
    from brain.profiles import make_profile
    import random
    cm = get_map("h3_construct")
    wv = modes.Watch("vip", modes.layout(cm["objects"]) and cm["objects"])
    ps = [PlayerState(i, i % 2, "p", Vec(i, 0, 0), Vec(), 0, 0, True, 1, 1, "br") for i in range(1, 9)]
    sn = Snapshot(3.0, ps)
    wv.update(Marks((2, 5)), sn, 3.0, raw=raw)
    team0 = {i: Bot(i, 0, make_profile("strong", "objector", random.Random(i)), cm, random.Random(i)) for i in (2, 4, 6, 8)}
    d = Director(0, cm, team0, rng=random.Random(1))
    d.assign_roles(3.0, sn)
    esc = [i for i, r in d.roles.items() if r == "escort"]       # (the director's plan: a bot may go rogue a round)
    hunt = [i for i, r in d.roles.items() if r == "hunter"]
    if sn.vips != (2, 5) or len(esc) != 2 or d.roles.get(2) != "free" or len(hunt) != 1 or any(
            team0[i].order.target != 2 for i in esc if team0[i].order.role == "escort"):
        fails.append(f"VIP: vips {sn.vips}, roles {d.roles}, orders {[(b.id, b.order.role, b.order.target) for b in team0.values()]}")
    # a Forge World variant's CTF stands (the export has only the blank canvas's): where its flags lie at the start,
    # each to the team that spawned nearest; the flag object named by the map's tag names (Paradiso CTF played as
    # Slayer)
    st = modes.stands_by_spawn([Vec(40, 5, 0), Vec(-40, 0, 0)], [(1, Vec(-35, 2, 0)), (1, Vec(-38, -3, 0)), (0, Vec(36, 0, 0))])
    if st != {0: Vec(40, 5, 0), 1: Vec(-40, 0, 0)} or modes.stands_by_spawn([], [(0, Vec())]) != {}:
        fails.append(f"Forge stands by spawn: {st}")
    from brain.live import LiveReach
    lr = LiveReach.__new__(LiveReach)
    lr._tag_name_list = ["objects\\multi\\models\\mp_flag_base\\mp_flag_base", "objects\\weapons\\multiplayer\\flag\\flag",
                         "objects\\weapons\\multiplayer\\flag\\shaders\\flag_cloth", "objects\\weapons\\multiplayer\\flag\\bitmaps\\flag_d"]
    if lr._own_name(0xE1230003, "multiplayer") != "flag" or lr._own_name(0xE1230000, "multiplayer") is not None:
        fails.append("Forge flag tag not named from the map's tag names")
    if modes.layout(get_map("h3_construct")["objects"]).get("bomb_goal", [None])[0] is None:
        fails.append("Halo 3 Construct: no bomb goals (the CTF flag return areas)")
    from brain.sim import Sim
    for mode in ("territories", "assault", "stockpile", "headhunter"):
        sim = Sim(mode, per_team=4, seed=5, map_name="reach_30_settlement")
        sim.run(150)
        if not sim.objmodes.events:
            fails.append(f"simulated {mode} on Settlement: the objective never moved")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("modes OK")


if __name__ == "__main__":
    main()
