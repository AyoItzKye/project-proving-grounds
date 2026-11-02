"""The objective game types beyond Slayer, CTF, King, Oddball and Invasion.

Halo: Reach first (every game type runs on its Megalo engine; the variant's name says which, its engine icon only
for the ones read live: CTF 0, Oddball 2, King 3, Invasion 9). Each mode's places come from the map's scenario
(maps/<map>/objects.json netgame flags with their boundaries, tools/reach_export.py):
  territories   terr_object zones: take the ones not ours, hold the ones we have
  assault       as_bomb (the bomb's stand: one neutral, or one per team), as_goal (a team's goal: the enemy plants
                there): carry the bomb to their goal and stand on it; defend ours
  stockpile     stp_flag (neutral flags), stp_goal (a team's goal): carry flags home, keep them there
  headhunter    hh_drop_point zones: bank the skulls picked up from kills
  infection     inf_haven zones: survivors hold a haven together, the infected hunt the nearest survivor
  juggernaut, vip  played as Slayer (who the juggernaut or VIP is is not read yet)
Objects (the bomb, stockpile flags) are found the way CTF flags are (brain/live.py flags_by_stand: the weapon object
first seen on its stand). Zone ownership in Territories is not read from the game: a team that held a zone alone for
the game's CAPTURE_S owns it until the other team does the same (ponytail: the game's own capture state, once decoded).
"""
from .core import Vec, dist

# the objective modes past CTF, King and Oddball: each has its own team plan in the director (mode_slots,
# invasion_slots) and its own objective points (Director.objective_points)
NEW_MODES = ("invasion", "territories", "assault", "stockpile", "headhunter", "infection")

NAMES = (("territories", ("TERRITOR", "LAND GRAB", "PLOTS")),("assault", ("ASSAULT", "BOMB", "NEUTRAL BOMB")),
         ("stockpile", ("STOCKPILE",)), ("headhunter", ("HEADHUNTER",)),
         ("infection", ("INFECTION", "SAFE HAVEN", "ALPHA ZOMBIE", "ZOMBIE", "FLOOD")),   # (Flood: Halo 4's)
         ("juggernaut", ("JUGGERNAUT",)), ("vip", ("VIP",)),
         # Halo 4 and H2A: played as the mode they are like (ALIAS), on their own places (KINDS)
         ("ricochet", ("RICOCHET",)), ("grifball", ("GRIFBALL",)), ("dominion", ("DOMINION",)))
# a mode played as another, on its own netgame flags: Ricochet carries the ball to their endzone (Assault's carry to the
# goal; the ball's thrown score not played), Grifball the bomb to their goal, Dominion holds bases as territories
# (their fortifying not played)
ALIAS = {"ricochet": "assault", "grifball": "assault", "dominion": "territories"}
KINDS = {"ricochet": {"rico_ballspawn": "bomb", "rico_endzone": "bomb_goal"},
         "grifball": {"grif_spawn": "bomb", "grif_goal": "bomb_goal"},
         "dominion": {"dom_base_zone": "territory"}}
# every game's names for the places the modes use (Reach's, and Halo 2's: its Assault plates are each team's "bomb
# return" by its own base, its bombs' stands "bomb spawn" per team and one neutral; maps/h2_*/objects.json)
PLACES = {"terr_object": "territory", "as_bomb": "bomb", "as_goal": "bomb_goal", "stp_flag": "stockpile_flag",
          "stp_goal": "stockpile_goal", "hh_drop_point": "drop_point", "inf_haven": "haven",
          "Territories flag": "territory", "Assault bomb spawn": "bomb", "Assault bomb return": "bomb_goal"}
# Halo 3 names no variant in memory read so far: its game engine number says the mode (each read live on Construct:
# 1 CTF, 2 Slayer, 3 Oddball, 4 King, 5 Juggernaut, 6 Territories, 7 Assault, 8 Infection, 9 VIP)
H3_ENGINES = {5: "juggernaut", 6: "territories", 7: "assault", 8: "infection", 9: "vip"}
# H2A by its variant's engine icon where the name says nothing (live, Lockdown: Territories' built-in "3 Plots", icon
# 8, read as Slayer by its name)
H2A_ICONS = {8: "territories"}
# held alone this long, a zone counts as that team's (Territories): the game's capture time (guide 19 6.1 and
# TERR-SYM-02: Halo 2 contest 5 s then control 5 s, Halo 3 and Reach 30 s), so its takers stay in it until it is theirs
CAPTURE_S = {"h2": 10.0, "h3": 30.0, "reach": 30.0}
OBJECT_MODES = ("territories", "assault", "stockpile", "headhunter", "infection", "juggernaut", "vip",
                "ricochet", "grifball", "dominion")   # (juggernaut and vip:
# Watch.mark_special; without them here Halo 3 Juggernaut played as Slayer, live)


def mode_of(game, live):
    """The objective mode a running game is in for tools/live_bots.py, or None (Slayer, CTF, King, Oddball, Invasion are
    read elsewhere): Halo 3 by its engine number, Halo 2 by its variant's own name (its Territories, Assault and
    Juggernaut played as Slayer before), the others by the variant's name, H2A by its engine icon where the name says
    nothing. A failed read is None (played as Slayer) and never stops the brain's tick."""
    try:
        if game == "h3":
            return H3_ENGINES.get(live.engine())
        mode = detect(live.variant()["name"] if game == "h2" else live.variant_name())
        return mode if mode is not None or game != "h2a" else H2A_ICONS.get(live.engine_icon())
    except Exception:
        return None


def detect(variant_name):
    """The mode a Reach variant's name says, or None (Slayer, CTF, King, Oddball, Invasion are read elsewhere)."""
    name = (variant_name or "").upper()
    if "INVASION" in name:
        return None
    return next((mode for mode, words in NAMES if any(w in name for w in words)), None)


def _v(p):
    return Vec(p[0], p[1], p[2])


def radius(f, default=3.0):
    """A netgame flag's zone size from its boundary: a cylinder's radius, half a box's short side."""
    b = f.get("boundary") or {}
    r = b.get("w", 0) if b.get("shape") == "cylinder" else min(b.get("w", 0), b.get("l", 0) or b.get("w", 0)) / 2
    return max(0.6, min(8.0, r)) if r else default


def layout(objs, mode=None):
    """Every mode's places on this map: {kind: [(Vec, radius, team)]}; a mode in KINDS: its own places only."""
    out = {}
    places = KINDS.get(mode, PLACES)
    for f in objs.get("netgame_flags", []):
        kind = places.get(f["type"])
        if kind:
            out.setdefault(kind, []).append((_v(f["pos"]), radius(f), f.get("team", 8)))
    if "bomb_goal" not in out:          # Halo 3: the bomb is armed on the CTF flag return areas (Construct: no
        out["bomb_goal"] = [(_v(f["pos"]), radius(f), f.get("team", 8))   # other goal object on the map)
                            for f in objs.get("netgame_flags", []) if f["type"] == "CTF flag return"]
        out["ctf_stand"] = [(_v(f["pos"]), 1.0, f.get("team", 8))
                            for f in objs.get("netgame_flags", []) if f["type"] == "ctf - flag"]
    return out


class Watch:
    """The live state of one of OBJECT_MODES for tools/live_bots.py: fills the snapshot's obj_ fields every tick."""

    def __init__(s, mode, objs, game="reach"):
        s.kind, s.mode, s.lay = mode, ALIAS.get(mode, mode), layout(objs, mode)   # (kind: the mode read, mode: as played)
        s.capture = CAPTURE_S.get(game, 30.0)     # (tools/live_bots.py names none: Reach's, whose territories it reads)
        s.owner, s.held = {}, {}          # territories: zone index -> owner team; -> (team, since) while held alone
        s.items_t, s.items = -9.0, []
        s.stands, s.stands_t = [], -9.0
        s.zombie_tag, s.infected_ids = None, {}    # Halo 3 Infection (split_infected)

    def live_stands(s, live, now):
        """Halo 3 Assault: the map export lists no bomb spawn, so the bombs' stands are read from the game once the bombs
        lie on them (live.item_stands); a stand on a CTF flag spot is that team's, else neutral."""
        if not s.stands and now - s.stands_t > 5.0:
            s.stands_t = now
            try:
                for p in live.item_stands():
                    p = _v(p)
                    team = next((t for q, _, t in s.lay.get("ctf_stand", []) if dist(p, q) < 1.0), 8)
                    s.stands.append((p, team))
            except Exception:
                s.stands = []
        return s.stands

    def split_infected(s, snap, raw):
        """Halo 3 Infection is a free for all to the game (each player his own team): the infected are told by their
        gun. The zombies all hold one kind nobody else holds, the kind the fewest hold at the start (Save One Bullet,
        Construct: one zombie's apart from nine survivors' shotguns); a survivor who dies comes back infected. The
        snapshot's teams become 0 survivors, 1 infected."""
        if len({p.team for p in snap.players}) < len(snap.players):
            return                          # the game's own teams (Reach): zombie_team() reads the swords
        tags = {d["index"]: d.get("wtag") for d in raw if d.get("pos") is not None and d.get("wtag")}
        if s.zombie_tag is None:
            count = {}
            for t in tags.values():
                count[t] = count.get(t, 0) + 1
            tag, n = min(count.items(), key=lambda kv: kv[1], default=(None, 0))
            if len(count) < 2 or len(tags) < 3 or n > len(tags) // 3:
                return
            s.zombie_tag = tag
        for p in snap.players:
            if p.id in tags:
                s.infected_ids[p.id] = tags[p.id] == s.zombie_tag
            elif not p.alive and p.id in s.infected_ids:
                s.infected_ids[p.id] = True
            p.team = 1 if s.infected_ids.get(p.id) else 0
        snap.infected = 1

    def mark_special(s, live, snap, raw):
        """Halo 3 Juggernaut and VIP: who the game marks (VIP: the HUD waypoint over his body, LiveH3.marked_players;
        the Juggernaut: his overshield).
        Juggernaut is a free for all with one marked man: the snapshot's teams become 0 everyone else (allies against
        him: guide 07, "team up with the nearest player on the Juggernaut"), 1 the Juggernaut; nobody marked yet (the
        first kill makes one): free for all as it is. VIP: each team's VIP in snap.vips."""
        if s.mode == "vip":
            try:
                snap.vips = tuple(sorted(live.marked_players(raw)))
            except Exception:
                pass
            return
        # the Juggernaut: his overshield (Construct, live: the juggernaut's shield read over 1.0 in 870 of 909 world
        # rows, nobody else's ever; the HUD waypoint block holds no marker on a body in this mode), kept while he
        # lives: damage takes it under 1.0 (the split held only 35% of a match on the shield alone)
        over = {p.id for p in snap.players if p.alive and p.shield > 1.05}
        cur = getattr(s, "jugg", None)
        if over:
            s.jugg = cur if cur in over else min(over)
        elif cur is not None and not any(p.id == cur and p.alive for p in snap.players):
            s.jugg = None
        marked = {s.jugg} if getattr(s, "jugg", None) is not None else set()
        if not marked or len({p.team for p in snap.players}) < len(snap.players):
            return                          # (a team Juggernaut variant: the game's own teams)
        for p in snap.players:
            p.team = 1 if p.id in marked else 0
        snap.infected = 1                   # (live_bots: free-for-all directors follow their bot's side)

    def one_bomb(s, now, items):
        """One Bomb (guide 19 ASS-ONE-01: one team attacks with the only bomb, the other defends, sides swap each round):
        the team whose stand the game's one bomb belongs to, else None. Two-bomb Assault shows two bombs, Neutral Bomb's
        one is nobody's (team 8): both goals stay. Judged on 10-20 s of reads that found a bomb (a failed read finds
        none; a swap of sides shows both teams in the window and waits for it to pass). Before, One Bomb's attackers
        posted two defenders on their own goal, where nobody plants (director.mode_slots)."""
        hist = s.__dict__.setdefault("bomb_hist", [])
        if items and (not hist or hist[-1][0] != now):
            hist.append((now, len(items), items[0].get("team", 8)))
        while hist and now - hist[0][0] > 20.0:
            hist.pop(0)
        if not hist or now - hist[0][0] < 10.0 or any(n != 1 for _, n, _ in hist):
            return None
        teams = {t for _, _, t in hist}
        return next(iter(teams)) if len(teams) == 1 and teams <= {0, 1} else None

    def update(s, live, snap, now, raw=None):
        snap.mode = s.mode
        if s.mode == "headhunter" and raw is not None and hasattr(live, "loose_named") and now - s.items_t > 0.25:
            # the skulls lying where men died (guide 19 HH-01: walk over them to take them; director.mode_slots sends
            # runners to the nearest): Reach's skull weapon objects with no parent (the map's tag names: Headhunter and
            # Oddball share objects\weapons\multiplayer\skull\skull). Never filled before: no runner went for one live
            s.items_t = now
            try:
                s.skulls = [Vec(*q) for q in live.loose_named("skull")]
            except Exception:
                s.skulls = []
        if s.mode == "headhunter":
            snap.obj_items = [dict(pos=q, carrier=None, kind="skull", team=8) for q in getattr(s, "skulls", [])]
        if s.mode == "infection" and raw is not None:
            s.split_infected(snap, raw)
        if s.mode in ("juggernaut", "vip") and raw is not None and (s.mode == "juggernaut" or hasattr(live, "marked_players")):
            # (the Juggernaut is told by his overshield alone: Halo 2's reader has no HUD marks)
            s.mark_special(live, snap, raw)
        alive = [p for p in snap.players if p.alive]
        if s.mode in ("territories", "headhunter", "infection"):
            kind = {"territories": "territory", "headhunter": "drop_point", "infection": "haven"}[s.mode]
            zones = s.lay.get(kind, [])
            out = []
            for k, (pos, r, _) in enumerate(zones):
                teams = {p.team for p in alive if dist(p.pos, pos) <= r + 0.3 and abs(p.pos.z - pos.z) < 2.5}
                if s.mode == "territories":
                    if len(teams) == 1:
                        t = next(iter(teams))
                        team, since = s.held.get(k, (t, now))
                        if team != t:
                            since = now
                        s.held[k] = (t, since)
                        if now - since >= s.capture:
                            s.owner[k] = t
                    else:
                        s.held.pop(k, None)
                out.append((pos, r, s.owner.get(k, -1)))
            snap.obj_zones = out
        if s.mode in ("assault", "stockpile"):
            stand_kind, goal_kind = ("bomb", "bomb_goal") if s.mode == "assault" else ("stockpile_flag", "stockpile_goal")
            # two teams: stands and goals of team 0, 1 or neutral (8); 2 and 3 are the four-team game's
            placed = [(pos, t) for pos, r, t in s.lay.get(stand_kind, []) if t in (0, 1, 8)]
            if not placed and s.mode == "assault" and hasattr(live, "item_stands"):
                placed = s.live_stands(live, now)
            stands = {k: pos for k, (pos, t) in enumerate(placed)}
            if raw is not None and stands and now - s.items_t > 0.25:
                s.items_t = now
                try:
                    s.items = live.objective_items(raw, stands, s.mode)
                except Exception:
                    s.items = []
            snap.obj_items = [dict(pos=Vec(*it["pos"]), carrier=it["carrier"], kind=stand_kind,
                                   team=placed[it["stand"]][1] if it.get("stand") in stands else 8) for it in s.items]
            # Assault: a bomb with nobody carrying it in the other team's goal, off its own stand, is armed there (as
            # brain/invasion.py's inv_armed: the carrier stood on the goal and the game took it from his hands): "armed"
            # is that goal's team, the one to disarm it (guide 19 ASS-MULTI-03/09). A team's stand lies in its own goal
            # on most maps (Settlement, Halo 2's, Halo 3's): a bomb at home is never armed
            for it, got in zip(snap.obj_items, s.items):
                home = stands.get(got.get("stand"))
                it["armed"] = None if s.mode != "assault" or it["carrier"] is not None or (
                    home is not None and (it["pos"] - home).flat() < 1.0) else next(
                    (t for g, r, t in s.lay.get(goal_kind, []) if t in (0, 1) and t != it["team"]
                     and (it["pos"] - g).flat() <= r + 0.5), None)
            goals = {}
            for pos, r, t in s.lay.get(goal_kind, []):
                for team in ((0, 1) if t == 8 else (t,) if t in (0, 1) else ()):
                    goals.setdefault(team, []).append(pos)
            one = s.one_bomb(now, snap.obj_items) if s.mode == "assault" else None
            if one is not None:                   # One Bomb: the attackers' own goal is nobody's target
                goals.pop(one, None)
            snap.obj_goals = goals
            carriers = {it["carrier"] for it in s.items if it["carrier"] is not None}
            for p in snap.players:
                if p.id in carriers:
                    p.has_flag = True             # carries the objective: runs, no stopping to fight


def carry_goal(mode, snap, team, pos):
    """Where a carrier of this team takes its object: Assault the enemy's goal, Stockpile its own."""
    goals = snap.obj_goals.get(1 - team if mode == "assault" else team) or []
    return min(goals, key=lambda g: dist(g, pos)) if goals else None


def zombie_team(snap):
    """Infection: the infected team (Reach's infected carry swords): the team with the most swords in hand."""
    if snap.infected != -1:
        return snap.infected
    swords = {}
    for p in snap.players:
        if p.alive and "sword" in (p.weapon or ""):
            swords[p.team] = swords.get(p.team, 0) + 1
    return max(swords, key=swords.get) if swords else None


def stands_by_spawn(spots, players):
    """A Forge map variant's CTF stands, which the scenario export lacks: {team: Vec} from where its flag objects lie at
    the start (spots) and the teams' players then (players: [(team, Vec)], at spawn by their own base). Each spot goes
    to the team whose players stand nearest, the best pairing overall (two flags, two teams); {} until both are read."""
    import itertools
    cent = {}
    for t, p in players:
        cent.setdefault(t, []).append(p)
    cent = {t: Vec(sum(p.x for p in ps) / len(ps), sum(p.y for p in ps) / len(ps), sum(p.z for p in ps) / len(ps))
            for t, ps in cent.items()}
    if not spots or not cent:
        return {}
    teams = sorted(cent)
    best = min(itertools.permutations(teams, min(len(spots), len(teams))),
               key=lambda ts: sum((spots[k] - cent[t]).flat() for k, t in enumerate(ts)))
    return {t: spots[k] for k, t in enumerate(best)}
