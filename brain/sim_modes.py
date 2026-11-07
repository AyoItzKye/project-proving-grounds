"""Objective rules for the offline simulator (brain/sim.py), so the brain's game types can be checked on every map
without the game.

Rules, simplified from Reach's built-in variants (it checks behaviour, not balance):
  invasion     phases 1-2: an attacker alone in a territory of the phase for TAKE_S takes it (gates open at phase 2);
               phase 3: the core sits on its stand, an attacker picks it up and carries it to the delivery point:
               the attackers win the round. A phase runs PHASE_S; when time is up the defenders win the round.
               Each team respawns in its zone of the phase; the nav has Invasion's barriers (one-way shields,
               gates while closed).
  territories  a team alone in a zone for the game's modes.CAPTURE_S owns it; 1 point per owned zone every 10 s.
  assault      the bomb (each as_bomb stand) is picked up by walking over it, carried to the enemy's goal and held
               there ARM_S: 1 point, the bomb goes home. A carrier who dies drops it.
  stockpile    flags (stp_flag stands) are carried into a team's own goal and stay; every 60 s each goal's flags
               score and go home.
  headhunter   a dead player drops one skull (plus any it carried); walking over picks it up; standing in a drop
               zone banks them (1 point a skull). The active drop zone rotates every 60 s.
  king         one hill (hills(): the map's own, else derived spots): a team alone in it scores 1 a second, both
               teams in it = contested, nobody scores. "king" keeps the hill nearest mid; "crazy_king" moves it to the
               next hill every HILL_MOVE_S (the snapshot's mode is "king" for both: the director has one King plan).
  oddball      one ball at its spawn nearest mid (ball_spawn()); walking over it picks it up (no shooting while
               carried, as a flag: Sim.shoot / Sim.melee); its carrier's team scores 1 a second; dropped where its
               carrier dies; back to its spawn after BALL_RESET_S loose.
  vip          each team has one VIP (snap.vips); killing the other team's VIP scores 1, then that team picks a new one
               (INFERRED from Halo 3 VIP's goal, its point values not read). Other kills score nothing.
Infection and Juggernaut are not simulated (a player's side changes on death or with the Juggernaut: the sim's directors
are fixed per team); Infection's live roles are checked by tools/test_modes.py.
"""
from . import invasion, modes
from .core import TICK, Vec, dist

TAKE_S, PHASE_S, ARM_S, PICKUP_R = 10.0, 180.0, 3.0, 1.2
# the dropped core goes home after this long with a defender on it and no attacker (the tested Tempest variant: Core
# Return Time 30 s; ASSUMED for every map, and that stepping off starts it again: live Spire 20261105-143525 a person
# 11.5 s on it did not return it)
CORE_RETURN_S = 30.0
# a moving hill's stay; a loose ball's time before it goes home (INFERRED: Halo 3 and Reach's ball reset default, not
# read from a variant); a zone's height (as territories)
HILL_MOVE_S, BALL_RESET_S, ZONE_DZ = 60.0, 30.0, 2.5
SPOT_MODES = ("king", "crazy_king", "oddball", "vip")


def hills(m):
    """Every King hill on the map, [(Vec, radius)]: Reach's, Halo 3's (koth_hill_static, renamed by maps.load_map),
    Halo 4's and H2A's koth_hill one per flag, radius from its boundary (modes.radius, 3 u without one: Halo 3's
    HILL_R); CE's "hill - flag" and Halo 2's "King Hill N" are rings of markers, one hill per index (centre their mean,
    radius the farthest marker, as CE's live king_hill). A map with none: its mid and first power positions."""
    flags = m["objects"].get("netgame_flags", [])
    out = [(Vec(*f["pos"]), modes.radius(f)) for f in flags if f["type"] == "koth_hill"]
    if not out:
        rings = {}
        for f in flags:
            key = f["id"] if f["type"] == "hill - flag" else f["type"] if f["type"].startswith("King Hill ") else None
            if key is not None:
                rings.setdefault(key, []).append(Vec(*f["pos"]))
        for key in sorted(rings, key=str):
            ps = rings[key]
            c = Vec(sum(p.x for p in ps) / len(ps), sum(p.y for p in ps) / len(ps), sum(p.z for p in ps) / len(ps))
            out.append((c, max(1.0, min(8.0, max((p - c).flat() for p in ps)))))
    return out or [(p, 3.0) for p in [m["points"]["mid"]] + m.get("positions", [])[:3]]


def ball_spawn(m):
    """The ball's spawn: the map's ball spot nearest its mid (Reach / H4 / H2A oddball_ball, Halo 3's renamed spawn
    points, CE's "oddball - ball spawn", Halo 2's "Oddball spawn"), else the mid."""
    mid = m["points"]["mid"]
    spots = [Vec(*f["pos"]) for f in m["objects"].get("netgame_flags", [])
             if f["type"] in ("oddball_ball", "oddball - ball spawn", "Oddball spawn")]
    return min(spots, key=lambda p: dist(p, mid), default=mid)


class SimModes:
    def __init__(s, sim):
        s.sim, s.mode = sim, sim.mode
        objs = sim.m["objects"]
        s.events = []                            # (time, text): phase changes, captures, plants, banks
        if s.mode == "invasion":
            s.inv = invasion.layout(objs)
            if s.inv is None:
                raise ValueError(f"{sim.m['name']}: no Invasion setup on this map")
            s.inv["map"] = sim.m["name"]               # (its phase rules by map: invasion.phase_link_gates)
            invasion.apply_barriers(sim.T, s.inv)
            s.round_start()
        elif s.mode == "race":                   # CE's in-order race on foot (no vehicle model): a lap a point
            s.race = modes.Race(modes.race_gates(objs), "normal", ce=sim.game == "ce")
            if not s.race.gates:
                raise ValueError(f"{sim.m['name']}: no race gates on this map")
        elif s.mode in SPOT_MODES:
            mid = sim.m["points"]["mid"]
            # hills on a floor the nav knows (a placeholder flag at the origin under Lockout's floor is no hill)
            s.hills = [h for h in hills(sim.m) if abs(sim.T.nav_z(h[0].x, h[0].y, h[0].z) - h[0].z) < ZONE_DZ] \
                or hills(sim.m)
            s.hill_k = min(range(len(s.hills)), key=lambda k: dist(s.hills[k][0], mid))   # the static hill: nearest mid
            b = ball_spawn(sim.m)                  # on the floor the nav knows there (H4 Warhouse's spot is 1.3 u over
            b = Vec(b.x, b.y, sim.T.nav_z(b.x, b.y, b.z))   # the nav's floor: the bots' paths ended under it, never
            s.ball = dict(home=b, carrier=None, loose_since=None)   # in reach, 0 pickups in 2 games)
            s.ball["pos"] = s.ball["home"]
            s.owned = {0: 0.0, 1: 0.0}             # seconds a team scored (in the hill, or with the ball): its points
            s.contested = 0.0                      # King: seconds with both teams in the hill
            s.takes = 0                            # Oddball: ball pickups; King: hill takeovers (a new team alone)
            s.last_holder = None
            s.vips = {}                            # VIP: team -> its VIP (picked on the first tick: the sim makes its
            #                                        players after its modes)
        else:
            s.lay = modes.layout(objs)
            s.owner, s.held, s.next_score = {}, {}, 10.0
            stands = [(p, r, t) for p, r, t in s.lay.get("bomb" if s.mode == "assault" else "stockpile_flag", [])
                      if t in (0, 1, 8)]
            if s.mode == "assault" and not stands:      # Halo 3: the export lists no bomb spawn; each team's bomb lies
                stands = [x for x in s.lay.get("ctf_stand", []) if x[2] in (0, 1)]   # on its CTF stand (live: modes.
            #                                             Watch.live_stands, "a stand on a CTF flag spot is that team's")
            if s.mode == "assault" and any(t in (0, 1) for p, r, t in stands):
                stands = [x for x in stands if x[2] in (0, 1)]   # Assault: each team's own bomb (no neutral one)
            s.items = [dict(pos=p, home=p, carrier=None, since=None, team=t) for p, r, t in stands]
            s.goals = {}
            for p, r, t in s.lay.get("bomb_goal" if s.mode == "assault" else "stockpile_goal", []):
                for team in ((0, 1) if t == 8 else (t,) if t in (0, 1) else ()):
                    s.goals.setdefault(team, []).append((p, r))
            s.skulls, s.carried, s.active = [], {}, 0

    # --- Invasion
    def round_start(s):
        s.phase, s.phase_t, s.held = 1, s.sim.now, {}
        s.core = dict(pos=s.inv["core"], carrier=None)
        invasion.apply_barriers(s.sim.T, s.inv)          # gates closed again
        s.sim.oob.set_phase(s.sim.T, 1)                  # (and their kill volumes: brain/oob.py volumes)
        invasion.phase_link_gates(s.sim.T, s.inv, 1, s.inv.get("map"))   # (its man cannons not up yet)

    def spawn_points(s, team):
        """A team's respawn points this phase: where the live game respawned that side in this phase (maps/<map>/
        inv_spawns.json, tools/inv_spawns.py: Spire's scenario zones put the phase 2 defenders 44 u off), else the
        scenario's respawn zones."""
        if s.mode != "invasion":
            return None
        named = s.__dict__.get("_named")
        if named is None:
            hs = invasion.honor_spawns(s.sim.m.get("base") or s.sim.m["name"])
            named = s._named = hs[0] if hs else []
        offers = [n for n in named if n["side"] == ("att" if team == 1 else "def") and str(s.phase) in n["points"]
                  and invasion.spawn_weight(n, s.phase) > 0 and str(s.phase) not in n.get("for_vehicles", ())]
        if offers:      # as the live bots spawn: a spawn its side's spawn screen offers, by the player's weights (brain/
            n = s.sim.rng.choices(offers, weights=[invasion.spawn_weight(o, s.phase) for o in offers])[0]   # invasion.py
            from .core import Vec                       # honor_spawn; no teammates' spots or vehicle errands here)
            return [Vec(*p) for p in n["points"][str(s.phase)]]
        live = s.__dict__.get("_live_spawns")
        if live is None:
            import json
            import os
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "maps", s.sim.m["name"], "inv_spawns.json")
            live = s._live_spawns = json.load(open(path)) if os.path.exists(path) else {}
        pts = live.get("att" if team == 1 else "def", {}).get(str(s.phase), [])
        if len(pts) >= 3:
            from .core import Vec
            return [Vec(*p) for p in pts]
        label = s.inv["attackers"] if team == 1 else s.inv["defenders"]   # sim team 1 attacks
        return s.inv["res"][label].get(s.phase) or s.inv["res"][label][1]

    def players(s):
        return [p for p in s.sim.players if p.alive]

    def step(s):
        now = s.sim.now
        if s.mode == "invasion":
            return s.step_invasion(now)
        if s.mode in SPOT_MODES:
            return s.step_spot(now)
        if s.mode == "race":
            laps = dict(s.race.laps)
            s.race.step([(p.id, p.pos, p.alive, False) for p in s.sim.players])
            for pid, n in s.race.laps.items():
                if n > laps.get(pid, 0):
                    p = s.sim.players[pid]
                    s.sim.score[p.team] += 1
                    s.events.append((round(now, 1), f"{p.name} finished lap {n}"))
            return
        if s.mode == "territories":
            for k, (pos, r, _) in enumerate(s.lay.get("territory", [])):
                teams = {p.team for p in s.players() if dist(p.pos, pos) <= r and abs(p.pos.z - pos.z) < 2.5}
                if len(teams) == 1:
                    t = next(iter(teams))
                    team, since = s.held.get(k, (t, now))
                    s.held[k] = (t, now if team != t else since)
                    if now - s.held[k][1] >= modes.CAPTURE_S.get(s.sim.game, 30.0) and s.owner.get(k) != t:
                        s.owner[k] = t
                        s.events.append((round(now, 1), f"team {t} took territory {k}"))
                else:
                    s.held.pop(k, None)
            if now >= s.next_score:
                s.next_score = now + 10.0
                for t in s.owner.values():
                    s.sim.score[t] += 1
        elif s.mode in ("assault", "stockpile"):
            s.step_carry(now)
        elif s.mode == "headhunter":
            drops = s.lay.get("drop_point", [])
            if drops and int(now // 60) % len(drops) != s.active:
                s.active = int(now // 60) % len(drops)
            for sk in list(s.skulls):
                p = next((p for p in s.players() if dist(p.pos, sk["pos"]) < PICKUP_R), None)
                if p is not None:
                    s.carried[p.id] = s.carried.get(p.id, 0) + sk["n"]
                    s.skulls.remove(sk)
            if drops:
                pos, r, _ = drops[s.active]
                for p in s.players():
                    if s.carried.get(p.id) and dist(p.pos, pos) <= r + 0.3:
                        s.sim.score[p.team] += s.carried.pop(p.id)
                        s.events.append((round(now, 1), f"{p.name} banked skulls"))

    def step_carry(s, now):
        for it in s.items:
            c = s.sim.players[it["carrier"]] if it["carrier"] is not None else None
            if c is not None:
                it["pos"] = c.pos
                goals = s.goals.get(1 - c.team if s.mode == "assault" else c.team, [])
                inside = next(((g, r) for g, r in goals if dist(c.pos, g) <= max(r, 1.5)), None)
                if inside and s.mode == "assault":
                    it["since"] = it["since"] if it["since"] is not None else now
                    if now - it["since"] >= ARM_S:
                        s.sim.score[c.team] += 1
                        s.events.append((round(now, 1), f"team {c.team} planted the bomb"))
                        c.has_flag, it["carrier"], it["pos"], it["since"] = False, None, it["home"], None
                elif inside:                              # stockpile: the flag stays in the goal
                    c.has_flag, it["carrier"], it["pos"] = False, None, inside[0]
                    it["in_goal"] = c.team
                else:
                    it["since"] = None
                continue
            if it.get("in_goal") is not None and s.mode == "stockpile":
                continue
            p = next((p for p in s.players() if not p.has_flag and dist(p.pos, it["pos"]) < PICKUP_R
                      and it["team"] in (8, p.team)), None)     # a team carries its own bomb (or the neutral one)
            if p is not None:
                it["carrier"], p.has_flag = p.id, True
                s.events.append((round(now, 1), f"{p.name} took the {'bomb' if s.mode == 'assault' else 'flag'}"))
        if s.mode == "stockpile" and now >= s.next_score:
            s.next_score = now + 60.0
            for it in s.items:
                if it.get("in_goal") is not None:
                    s.sim.score[it["in_goal"]] += 1
                    it["pos"], it["in_goal"] = it["home"], None

    def pay(s, team, dt):
        """A second of holding scores a point: the whole seconds a team has held so far, as the game's integer score."""
        s.owned[team] += dt
        s.sim.score[team] = int(s.owned[team] + 1e-6)

    def step_spot(s, now):
        from .core import TICK
        if s.mode == "vip":
            for t in (0, 1):
                if s.vips.get(t) is None:
                    s.pick_vip(t)
            return
        if s.mode == "crazy_king" and len(s.hills) > 1 and now >= HILL_MOVE_S * (1 + s.__dict__.get("moves", 0)):
            s.moves = s.__dict__.get("moves", 0) + 1
            s.hill_k = (s.hill_k + 1) % len(s.hills)
            s.events.append((round(now, 1), f"the hill moved to {s.hill_k}"))
        if s.mode in ("king", "crazy_king"):
            pos, r = s.hills[s.hill_k]
            teams = {p.team for p in s.players() if (p.pos - pos).flat() <= r and abs(p.pos.z - pos.z) < ZONE_DZ}
            if len(teams) == 1:
                t = next(iter(teams))
                if t != s.last_holder:
                    s.takes += 1
                    s.events.append((round(now, 1), f"team {t} took the hill"))
                s.last_holder = t
                s.pay(t, TICK)
            elif teams:
                s.contested += TICK
            return
        b = s.ball                                 # Oddball
        if b["carrier"] is not None:
            c = s.sim.players[b["carrier"]]
            b["pos"] = c.pos
            s.pay(c.team, TICK)
            return
        if b["loose_since"] is not None and now - b["loose_since"] >= BALL_RESET_S:
            b["pos"], b["loose_since"] = b["home"], None
            s.events.append((round(now, 1), "the ball went home"))
        p = next((p for p in s.players() if not p.has_flag and dist(p.pos, b["pos"]) < PICKUP_R), None)
        if p is not None:
            b["carrier"], b["loose_since"], p.has_flag = p.id, None, True
            s.takes += 1
            s.events.append((round(now, 1), f"{p.name} took the ball"))

    def pick_vip(s, team, not_id=None):
        ids = [p.id for p in s.sim.players if p.team == team]
        s.vips[team] = s.sim.rng.choice([i for i in ids if i != not_id] or ids)

    def step_invasion(s, now):
        att = 1
        if s.phase in (1, 2):
            for k, z in enumerate(s.inv["phases"][s.phase]):
                r = invasion.zone_radius(s.inv, z)
                teams = {p.team for p in s.players() if dist(p.pos, z) <= r + 0.2 and abs(p.pos.z - z.z) < 2.5}
                if teams == {att}:
                    since = s.held.setdefault(k, now)
                    if now - since >= TAKE_S:
                        s.phase, s.phase_t, s.held = s.phase + 1, now, {}
                        s.sim.score[att] += 1
                        s.events.append((round(now, 1), f"attackers took phase {s.phase - 1} (territory {k})"))
                        s.sim.oob.set_phase(s.sim.T, s.phase)
                        invasion.phase_link_gates(s.sim.T, s.inv, s.phase, s.inv.get("map"))
                        if s.phase == 2:          # the gates open
                            invasion.apply_barriers(s.sim.T, s.inv, {b["key"]: False for b in s.inv["barriers"]
                                                                     if b["kind"] == "gate"})
                        break
                else:
                    s.held.pop(k, None)
        elif s.phase == 3:
            core = s.core
            c = s.sim.players[core["carrier"]] if core["carrier"] is not None else None
            if c is not None:
                core["pos"] = c.pos
                if dist(c.pos, s.inv["phases"][3][0]) <= max(1.5, invasion.zone_radius(s.inv, s.inv["phases"][3][0])):
                    s.sim.score[att] += 1
                    s.events.append((round(now, 1), "attackers delivered the core: round to the attackers"))
                    c.has_flag = False
                    return s.round_start()
            else:
                p = next((p for p in s.players() if p.team == att and dist(p.pos, core["pos"]) < PICKUP_R), None)
                if p is not None:
                    core["carrier"], p.has_flag, core["back"] = p.id, True, 0.0
                    s.events.append((round(now, 1), f"{p.name} picked up the core"))
                elif dist(core["pos"], s.inv["core"]) > 1.5:      # dropped: a defender on it takes it home
                    on = any(p.team != att and dist(p.pos, core["pos"]) < PICKUP_R for p in s.players())
                    core["back"] = core.get("back", 0.0) + TICK if on else 0.0
                    if core["back"] >= CORE_RETURN_S:
                        core["pos"], core["back"] = s.inv["core"], 0.0
                        s.events.append((round(now, 1), "the defenders returned the core"))
        if now - s.phase_t > PHASE_S:
            s.sim.score[1 - att] += 1
            s.events.append((round(now, 1), f"phase {s.phase} timed out: round to the defenders"))
            for p in s.sim.players:
                p.has_flag = False
            s.round_start()

    def on_kill(s, e):
        if s.mode == "invasion" and s.core["carrier"] == e.id:
            s.core["carrier"], e.has_flag = None, False
        if s.mode in ("assault", "stockpile"):
            for it in s.items:
                if it["carrier"] == e.id:
                    it["carrier"], it["since"], e.has_flag = None, None, False
        if s.mode == "headhunter":
            s.skulls.append(dict(pos=e.pos, n=1 + s.carried.pop(e.id, 0)))
        if s.mode == "oddball" and s.ball["carrier"] == e.id:     # dropped where he fell
            s.ball.update(carrier=None, pos=e.pos, loose_since=s.sim.now)
            e.has_flag = False
            s.events.append((round(s.sim.now, 1), f"{e.name} dropped the ball"))
        if s.mode == "vip" and s.vips.get(e.team) == e.id:        # (two teams: the other one killed him)
            s.sim.score[1 - e.team] += 1
            s.events.append((round(s.sim.now, 1), f"team {1 - e.team} killed the VIP"))
            s.pick_vip(e.team, not_id=e.id)

    def snapshot(s, snap):
        snap.mode = "king" if s.mode == "crazy_king" else s.mode
        if s.mode in ("king", "crazy_king"):
            snap.hill, snap.hill_r = s.hills[s.hill_k]
            return
        if s.mode == "oddball":
            snap.ball, snap.ball_carrier = s.ball["pos"], s.ball["carrier"]
            return
        if s.mode == "vip":
            snap.vips = tuple(sorted(v for v in s.vips.values() if v is not None))
            return
        if s.mode == "race":
            r = s.race
            snap.obj_zones = [(g, rad, -1) for g, rad, _, _ in r.gates]
            snap.race_next = {p.id: r.gates[r.next_gate(p.id, p.pos)][0] for p in s.sim.players}
            return
        if s.mode == "invasion":
            snap.inv_phase, snap.inv_attackers, snap.inv_phase_t = s.phase, 1, s.sim.now - s.phase_t
            snap.inv_zones = list(s.inv["phases"][3 if s.phase == 3 else s.phase])
            snap.inv_zone_r = [invasion.zone_radius(s.inv, z) for z in snap.inv_zones]
            snap.inv_delivery = s.inv["phases"][3][0]
            if s.phase == 3:
                snap.inv_core, snap.inv_core_carrier = s.core["pos"], s.core["carrier"]
            snap.inv_stand = s.inv["core"]
            return
        if s.mode == "territories":
            snap.obj_zones = [(p, r, s.owner.get(k, -1)) for k, (p, r, _) in enumerate(s.lay.get("territory", []))]
        if s.mode == "headhunter" and s.lay.get("drop_point"):
            p, r, _ = s.lay["drop_point"][s.active]   # only the active drop zone (players see it on the HUD)
            snap.obj_zones = [(p, r, -1)]
        if s.mode in ("assault", "stockpile"):
            snap.obj_items = [dict(pos=it["pos"], carrier=it["carrier"], kind="bomb", team=it["team"]) for it in s.items]
            snap.obj_goals = {t: [g for g, r in gs] for t, gs in s.goals.items()}
        if s.mode == "headhunter":                # dropped skulls: the objects to pick up
            snap.obj_items = [dict(pos=sk["pos"], carrier=None, kind="skull", team=8) for sk in s.skulls]
