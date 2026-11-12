"""Offline Blood Gulch simulator: same Snapshot/Action interface as the game hook, so the
brain and directors can be exercised before the DLL exists. The ground, cliffs, hills,
base roofs and overhangs come from the real level mesh (brain/terrain.py); spawns, flags
and zones from the real scenario. Damage and movement are still crude (no vehicles, no
teleporters, no jumping onto roofs). It checks behaviour, not balance.

usage: python -m brain.sim [--seconds N] [--compare-comms]
"""
import argparse
import math
import random
import statistics
import time

from .core import Vec, PlayerState, FlagState, Snapshot, TICK, dist, angles_to, wrap, eye
from .profiles import make_profile
from .maps import BLOODGULCH, get_map, terrain as map_terrain
from .bot import Bot
from .director import Director
from .equipment import game_of
from .simgear import Gear

SPEED = 2.3          # world units/s (UNVERIFIED for CE, tune in-game)
# man cannons (Sim.cannons): onto the pad this near its ride's take-off; rides from this near the launcher; Narrows' 28 u in
# 4.2 s live (anchor_launches); the arc's height over the straight line
CANNON_PAD_R, CANNON_LINK_R, CANNON_SPEED, CANNON_ARC = 1.0, 2.0, 6.7, 6.0
BODY_DMG = {"pistol": 0.45, "assault_rifle": 0.09, "sniper": 1.1, "rockets": 2.5, "fuelrod": 1.5,
            "plasma_pistol": 0.12, "plasma_rifle": 0.08, "needler": 0.07, "shotgun": 0.9, "flamethrower": 0.05}
MELEE_REACH = {"sword": 2.25, "gravity_hammer": 1.35}   # the lunge weapons' reach (brain/bot.py LUNGE): no hit past it
BODY_DMG.update(sword=2.0, gravity_hammer=2.0)        # (one lunge kills)
HIT_SIZE = {"rockets": 3.0, "fuelrod": 2.0}   # splash: a near miss still hits
AMMO = {"rockets": 4, "sniper": 8, "fuelrod": 5}
SIM_GUNFIRE, SIM_MAG = True, 60   # players' magazines go down a round a shot, so gunfire is heard (Sim.gun_fired)
SHIELD_DELAY, SHIELD_REFILL = 5.0, 4.0   # CE: 5 s delay, about 4 s to refill (docs/research/05)
# known spots on Blood Gulch and the callout they must get (from the scenario's real objects)
ZONE_SPOTS = [   # (docs/research/06 sections 3 and 8.1)
    (Vec(95.69, -159.45, -0.3), "Red base"), (Vec(92.48, -156.41, 1.70), "Red top"),
    (Vec(40.24, -79.12, -0.3), "Blue base"), (Vec(43.19, -82.22, 1.70), "Blue top"),
    (Vec(82.83, -114.53, 0.70), "Red port"), (Vec(43.80, -126.23, 0.24), "Blue port"),
    (Vec(109.06, -108.28, 2.06), "OS"), (Vec(72.60, -126.34, 1.18), "Rockets"),
    (Vec(69.83, -88.17, 5.66), "Batcave"), (Vec(57.76, -150.00, 5.75), "Sunny"),
    (Vec(72.8, -103.6, 4.1), "Big Hill"), (Vec(92.9, -118.5, 3.3), "Water"),
    (Vec(97.5, -101.0, 4.5), "Tunnel"), (Vec(120.0, -183.2, 6.7), "Camp hill"),
    (Vec(80.7, -149.5, 0.1), "Red tree"), (Vec(39.1, -96.0, -0.2), "Blue tree"),
    (Vec(30.0, -110.0, 2.6), "Blue cliff"), (Vec(31.0, -57.0, 3.0), "Cubby"),
    (Vec(67.1, -119.8, 0.2), "Mid"), (Vec(59.0, -116.86, 1.84), "Camo"),
    (Vec(62.97, -136.52, 1.96), "Fuel rod"), (Vec(102.5, -169.3, 0.2), "Red back"),
    (Vec(33.4, -69.2, 0.5), "Blue back"), (Vec(106.0, -138.0, 0.5), "Dark red"),
    (Vec(24.0, -90.0, 1.0), "Light blue"), (Vec(57.0, -80.0, 0.5), "Dark blue"),
    (Vec(75.0, -166.0, 1.0), "Light red"),
]


def terrain_for(m):
    return map_terrain(m)


class Sim:
    def __init__(s, mode="ctf", per_team=8, seed=1, tiers=None, legacy_comms=False, map_name="bloodgulch",
                 personalities=None):
        s.rng = random.Random(seed)
        s.m = get_map(map_name)
        s.game = game_of(map_name)
        s.T = terrain_for(s.m)
        from .oob import Oob                     # out of bounds as the live brain has it (tools/live_bots.py): the
        s.oob = o = Oob(map_name)                # map's kill zones and learned spots (without them a map variant's
        if o.spots or o.volumes:                 # Invasion gates walling off Spire's core passed here, failed live)
            s.T.set_oob(o.spots, o.version, o.volumes)
        s.mode, s.now = mode, 0.0
        s.los, s.nav = s.T.sees, s.T.nav     # (sight: through windows and fences; shots: T.shot_los)
        s.objmodes = None
        if mode in ("invasion", "territories", "assault", "stockpile", "headhunter", "king", "crazy_king", "oddball",
                    "vip", "race", "juggernaut", "infection"):
            from .sim_modes import SimModes          # objective rules (brain/sim_modes.py)
            s.objmodes = SimModes(s)
        s.players, s.bots = [], {}
        s.state = {}
        s.stats = {}
        tiers = tiers or ["novice", "average", "strong", "top"]
        by_team = tiers if isinstance(tiers, dict) else {0: tiers, 1: tiers}   # {team: [tier, ...]}: tier against tier
        pers = personalities or ["rusher", "camper", "flanker", "objector", "spammer", "grudger", "sniper"]
        pid = 0
        counts = per_team if isinstance(per_team, tuple) else (per_team, per_team)
        for team in (0, 1):
            for i in range(counts[team]):
                prof = make_profile(by_team[team][i % len(by_team[team])], pers[(i + team) % len(pers)], s.rng)
                p = PlayerState(pid, team, f"{'RB'[team]}{i}-{prof.tier}-{prof.personality}", s.spawn_point(team))
                p.yaw = angles_to(p.pos, s.m["flags"][1 - team])[0]
                s.gun_fired(p, shot=False)
                s.players.append(p)
                s.bots[pid] = Bot(pid, team, prof, s.m, random.Random(seed * 100 + pid))
                s.bots[pid].feet_off = 0.0       # (bodies here stand on the floor; H2A / Halo 4 report 0.38 over it: Bot.feet)
                s.state[pid] = dict(last_hit=-99, respawn_at=None, airborne_until=0)
                s.stats[pid] = dict(shots=0, hits=0, kills=0, deaths=0, moved=0.0, caps=0, tier=prof.tier,
                                    jumps=0, fight_ticks=0, strafe_ticks=0)
                pid += 1
        s.flags = {t: FlagState(t, s.m["flags"][t], s.m["flags"][t]) for t in (0, 1)}
        s.score = {0: 0, 1: 0}
        s.log = []
        s.directors = {t: Director(t, s.m, {i: b for i, b in s.bots.items() if b.team == t},
                                   random.Random(seed + t), s.log, legacy_comms) for t in (0, 1)}
        s.flag_events = []
        s.comms = CommsMeter(s)
        # power items: up at the start, respawn on their timers after pickup
        s.items = [dict(it, up=True, back_at=0.0) for it in s.m["items"]]
        s.ammo = {}
        s.pickups = []    # (time, player id, item name), for tests
        s.gear = Gear(s)  # equipment and armor abilities (brain/simgear.py)

    def spawn_point(s, team):
        pts = s.m["spawns"]["ctf" if s.mode == "ctf" else "slayer"][team] or s.m["spawns"]["ctf"][team]
        group = s.m["spawns"]["ctf" if s.mode == "ctf" else "slayer"]
        sizes = sorted(len(group.get(t, ())) for t in (0, 1))
        # (one side's list a handful against the other's lot: the labels carry no team, both sides get the halves.
        # High Ground reads 94 and 2: team 0 spawned all over the map, beside the other flag too, and every run met
        # its respawns head on at the middle ridge: 0 pickups in 300 s)
        if len(pts) < 4 or (sizes[0] < 4 and sizes[1] > 5 * max(1, sizes[0])):
            # a map whose spawn points carry no team (Halo 3's: Construct reads 135 and 2): the half of all its spawns
            # nearer this team's flag
            every = [p for g in s.m["spawns"].values() for side in g.values() for p in side]
            home, away = s.m["flags"].get(team), s.m["flags"].get(1 - team)
            if every and home is not None and away is not None:
                pts = [p for p in every if dist(p, home) < dist(p, away)] or pts
        if getattr(s, "objmodes", None) is not None and s.objmodes.spawn_points(team):
            pts = s.objmodes.spawn_points(team)      # Invasion: the team's respawn zone of the phase
        p = s.rng.choice(pts)
        x, y = p.x + s.rng.uniform(-0.5, 0.5), p.y + s.rng.uniform(-0.5, 0.5)
        if not s.T.can_step(p, Vec(x, y)):
            x, y = p.x, p.y          # the jitter would land in a wall: use the exact spawn point
        return Vec(x, y, s.T.nav_z(x, y, p.z))

    def snapshot(s):
        snap = Snapshot(s.now, s.players, s.flags if s.mode == "ctf" else {}, dict(s.score), s.mode)
        snap.score_limit = getattr(s, "limit", 0)
        if s.objmodes is not None:
            s.objmodes.snapshot(snap)
        s.gear.snapshot(snap)                  # holograms among the players, domes / fields / mines
        return snap

    def report(s, team, now, speaker, kind, pos, enemy=None, busy=False, **extra):
        s.comms.reported(team, kind, enemy, now)
        status = s.directors[team].report(now, speaker, kind, pos, enemy=enemy, busy=busy, **extra)
        if status == "covered":
            s.comms.covered(team, kind, enemy)

    def step(s):
        s.now += TICK
        snap = s.snapshot()
        for d in s.directors.values():
            d.update(s.now, snap)
        s.comms.update()
        actions = {}
        for p in s.players:
            b = s.bots[p.id]
            actions[p.id] = b.think(s.now, TICK, snap, s.los, s.nav, s.directors[p.team].callouts,
                                    s.directors[p.team].item_up)
            for kind, eid, pos, t, busy in b.reports:
                s.report(p.team, t, p.id, kind, pos, eid, busy)
            b.reports.clear()
        s.last_actions = actions
        for p in s.players:
            st = s.state[p.id]
            if not p.alive:
                if s.now >= st["respawn_at"]:
                    p.alive, p.shield, p.health = True, 1.0, 1.0
                    p.pos, p.vel = s.spawn_point(p.team), Vec()
                    p.ability_on = False
                    if st.get("energy") is not None:
                        st["energy"].level = 1.0
                continue
            a = actions[p.id]
            p.yaw, p.pitch = wrap(a.yaw), max(-1.4, min(1.4, a.pitch))
            p.crouching = a.crouch
            mult, can_move, can_shoot = s.gear.tick_player(p, a, st)   # armor lock, sprint, dashes...
            fl = st.get("flight")
            if fl is not None:
                # thrown by a man cannon (cannons()): along the ride's line, an arc over it, the ride's time; no
                # steering, no shooting, seen and shot as anyone in the open
                a0, b0, t0, t1 = fl
                k = min(1.0, (s.now - t0) / (t1 - t0))
                p.pos = Vec(a0.x + (b0.x - a0.x) * k, a0.y + (b0.y - a0.y) * k,
                            a0.z + (b0.z - a0.z) * k + CANNON_ARC * math.sin(math.pi * k))
                p.vel = (b0 - a0) * (1.0 / (t1 - t0))
                if k >= 1.0:
                    st["flight"] = None
                    p.pos = b0
                continue
            sp = SPEED * (0.5 if a.crouch else 1.0) * mult
            fx, fy = math.cos(p.yaw), math.sin(p.yaw)
            vx = (fx * a.forward - fy * a.strafe) * sp if can_move else 0.0
            vy = (fy * a.forward + fx * a.strafe) * sp if can_move else 0.0
            n = math.hypot(vx, vy)
            if n > sp:
                vx, vy = vx / n * sp, vy / n * sp
            old, run = p.pos, p.vel     # (run: the speed carried into a jump)
            s.move(p, vx * TICK, vy * TICK)
            p.vel = Vec((p.pos.x - old.x) / TICK, (p.pos.y - old.y) / TICK, 0)
            s.stats[p.id]["moved"] += dist(old, p.pos)
            if a.jump and s.now > st["airborne_until"]:
                st["airborne_until"] = s.now + 0.6
                s.stats[p.id]["jumps"] += 1
                # a jump from a jump-link spot in the direction we run: land on the far side
                jumps = getattr(s.T, "jumps", {}).get(s.T._node(p.pos), ())
                if jumps and (vx or vy):
                    def along(t):
                        c = s.T._center(*t)
                        dx, dy = c.x - p.pos.x, c.y - p.pos.y
                        n = math.hypot(dx, dy) * math.hypot(vx, vy)
                        return (dx * vx + dy * vy) / n if n else -1
                    t = max(jumps, key=along)
                    if along(t) > 0.8:
                        c = s.T._center(*t)
                        p.pos = c
                elif vx or vy:
                    # a jump people made (LiDAR links: Reach has no gap-jump physics), from its take-off toward its
                    # landing at a run (half speed or more that way coming in: a standing hop lands where it began):
                    # land there (Spire's way down from the core is one, 35 u into the lift column)
                    for src, dst, k, w in getattr(s.T, "hjumps", ()):
                        to = k["take_off"]
                        if math.hypot(to[0] - p.pos.x, to[1] - p.pos.y) > 0.6 or abs(to[2] - p.pos.z) > 1.0:
                            continue
                        dx, dy = k["land"][0] - to[0], k["land"][1] - to[1]
                        n = math.hypot(dx, dy)
                        if n and (dx * vx + dy * vy) / n > 0.8 * math.hypot(vx, vy) and \
                                (dx * run.x + dy * run.y) / n > 0.5 * SPEED:
                            # onto the landing's nav node (Terrain.add_human_links: dst), not the raw LiDAR point: one
                            # on a cell edge whose own cell has no floor at that height (h3_construct (-5.76, -2.31,
                            # 11.53), a two-way link bots landed live 5 times) left the body off its node, every step
                            # refused (can_step), frozen for the rest of its life (sim A/B Nov 4)
                            p.pos = s.T._center(*dst)
                            break
            if s.bots[p.id].goal[0] == "fight":
                s.stats[p.id]["fight_ticks"] += 1
                s.stats[p.id]["strafe_ticks"] += abs(a.strafe) > 0.3
            if a.fire and not p.has_flag and can_shoot:
                s.shoot(p)
            if a.melee:
                s.melee(p)
            if a.grenade:
                s.grenade(p)
            if s.now - st["last_hit"] > SHIELD_DELAY and p.shield < 1.0:
                p.shield = min(1.0, p.shield + TICK / SHIELD_REFILL)
            if p.camo_until and s.now > p.camo_until:
                p.camo_until = 0.0
        s.gear.update()
        if s.mode == "ctf":
            s.ctf()
        if s.objmodes is not None:
            s.objmodes.step()
        s.update_items()

    def update_items(s):
        for i, it in enumerate(s.items):
            if not it["up"]:
                if s.now >= it["back_at"]:
                    it["up"] = True
                continue
            for p in s.players:
                if p.alive and dist(p.pos, it["pos"]) < 1.2 and s.pickup(p, it):
                    it["up"], it["back_at"] = False, s.now + it["respawn"]
                    s.pickups.append((round(s.now, 1), p.id, it["name"]))
                    # who knows the timer: the taker's team, and the other team if one of them saw it
                    s.directors[p.team].item_taken(i, s.now, it["respawn"])
                    if any(q.alive and q.team != p.team and s.los(q.pos, it["pos"]) and dist(q.pos, it["pos"]) < 60
                           for q in s.players):
                        s.directors[1 - p.team].item_taken(i, s.now, it["respawn"])
                    break

    def pickup(s, p, it):
        name = it["name"]
        if it["kind"] == "weapon":
            if p.has_flag or p.weapon == name:
                return False
            p.weapon = name
            s.ammo[p.id] = AMMO.get(name, 8)   # power weapons the table lacks (H2 sword): 8 uses
            return True
        if it["kind"] == "health":                       # a health pack: health whole again (CE, ODST)
            if p.health >= 1.0:
                return False
            p.health = 1.0
            return True
        if it["kind"] == "equipment":                    # Halo 3: one slot, the new one replaces it
            p.equipment = name
            return True
        if name == "speed_boost":
            return True                                    # (no speed model: taken, nothing more)
        if name == "camo" and s.rng.random() < 0.5:      # this spawn is 50% camo, 50% overshield
            p.camo_until = s.now + 30.0
            return True
        p.shield = 3.0                                     # overshield
        return True

    def move(s, p, dx, dy):
        """Walk on the real ground; cliffs and walls stop you, you slide along them."""
        # heights from the path grid, so movement and paths agree on what is a wall
        for k, (mx, my) in enumerate(((dx, dy), (dx, 0.0), (0.0, dy))):
            nx, ny = p.pos.x + mx, p.pos.y + my
            if not s.T.can_step(p.pos, Vec(nx, ny)) or s.T.crosses_barrier(p.pos, Vec(nx, ny, p.pos.z)):
                continue
            if k and s.T.nav_z(nx, ny, p.pos.z) < p.pos.z - 0.6:
                continue          # sliding along a rail never drops you off the ledge (a person stops at the edge)
            p.pos = Vec(nx, ny, s.T.nav_z(nx, ny, p.pos.z))
            lock = s.state[p.id].get("tele_from")
            if lock is not None and (p.pos - lock).flat() > 1.5:
                s.state[p.id]["tele_from"] = lock = None    # walked off the exit: pads work again
            for a, b in s.m["teleporters"] + s.lifts():   # stepping on a teleporter pad, into a gravity lift
                if lock is None and (p.pos - a).flat() < 1.0 and -1.6 <= p.pos.z - a.z <= 0.6:
                    p.pos = Vec(b.x, b.y, s.T.nav_z(b.x, b.y, b.z))
                    s.state[p.id]["tele_from"] = p.pos      # no ping-pong with a pad by the exit
                    break
            for a, b in s.cannons():                      # into a man cannon: thrown across (the flight above)
                if (p.pos - a).flat() < CANNON_PAD_R and -1.6 <= p.pos.z - a.z <= 1.0:
                    s.state[p.id]["flight"] = (p.pos, b, s.now, s.now + dist(p.pos, b) / CANNON_SPEED)
                    break
            return

    def cannons(s):
        """Man cannons (map "launcher" features) as one-way pads: each to where people's ride from beside it landed
        (LiDAR links from within CANNON_LINK_R of it, landing 8+ u off): Narrows' throw base to base, 28 u in 4.2 s live.
        The sim had none: bots that run through a cannon (live) walked into it and stood (Nov 9)."""
        if getattr(s, "_cannons", None) is None:
            s._cannons = []
            for f in s.m.get("features", []):
                if f.get("kind") != "launcher":
                    continue
                base = Vec(*f["pos"])
                rides = [k for src, dst, k, w in getattr(s.T, "hjumps", [])
                         if math.hypot(k["take_off"][0] - base.x, k["take_off"][1] - base.y) < CANNON_LINK_R
                         and abs(k["take_off"][2] - base.z) < 3.0
                         and math.hypot(k["land"][0] - k["take_off"][0], k["land"][1] - k["take_off"][1]) >= 8.0]
                if rides:
                    k = rides[0]
                    pad = Vec(*k["take_off"])
                    s._cannons.append((pad, s.T._center(*s.T._node(Vec(*k["land"])))))
        return s._cannons

    def lifts(s):
        """Gravity lifts as one-way pads (the sim has no lift physics): each map "lift" feature to where people's ride
        up it landed (LiDAR links rising 3+ from beside it), so bots' lift rides (Bot.ride_lift) work in the sim."""
        if getattr(s, "_lifts", None) is None:
            s._lifts = []
            for f in s.m.get("features", []):
                if f.get("kind") != "lift":
                    continue
                base = Vec(*f["pos"])
                lands = [k["land"] for src, dst, k, w in getattr(s.T, "hjumps", [])
                         if math.hypot(k["take_off"][0] - base.x, k["take_off"][1] - base.y) < 2.0
                         and k["land"][2] > base.z + 3.0]
                if lands:                                  # (onto the landing's nav node, as a jump's landing)
                    s._lifts.append((base, s.T._center(*s.T._node(Vec(*lands[0])))))
        return s._lifts

    def target_in_crosshair(s, p):
        best, best_err = None, 9
        for e in s.players + s.gear.decoys:
            if e.team == p.team or not e.alive:
                continue
            d = dist(p.pos, e.pos)
            if d > 80 or not s.T.shot_los(p.pos, e.pos):
                continue
            y, pt = angles_to(eye(p), e.pos + Vec(0, 0, 0.35))
            err = math.hypot(wrap(y - p.yaw), pt - p.pitch)
            if err < best_err:
                best, best_err = e, err
        return best

    def gun_fired(s, p, shot=True):
        """The gun in hand and its magazine, as a live game shows every player's (SIM_GUNFIRE): a shot takes a round, so
        the others' Perception.fired hears it (Bot aware: Legendary 1.0, Normal 0.35, Easy 0). Before, the sim's players
        carried no magazine and nobody ever heard a shot: one of Legendary's edges was gone from every sim. The
        rounds left stay unknown (-1): no reload, never dry, as before."""
        if not SIM_GUNFIRE:
            return
        if p.weapons != [p.weapon]:
            p.weapons, p.mag, p.ammo = [p.weapon], [SIM_MAG], [-1]
        if shot:
            p.mag[0] = p.mag[0] - 1 if p.mag[0] > 1 else SIM_MAG

    def shoot(s, p):
        s.stats[p.id]["shots"] += 1
        s.gun_fired(p)
        w = p.weapon                          # the shot uses the weapon in hand, even the last round
        if p.weapon in AMMO:
            s.ammo[p.id] -= 1
            if s.ammo[p.id] <= 0:
                p.weapon = "pistol"           # out of ammo: back to the sidearm
        e = s.target_in_crosshair(p)
        if not e or s.gear.blocked(p, e):    # (a dome between us stops the shot)
            return
        d = max(dist(p.pos, e.pos), 0.5)
        if w in MELEE_REACH and d > MELEE_REACH[w]:
            return                                # (a sword or hammer reaches no farther than its lunge)
        e_at = e.pos
        # where the shot crosses him: sideways off his middle, and how high above his feet. A Spartan's body is
        # about 0.12 to each side and 0.08-0.58 up, the head 0.07 to each side and 0.58-0.70 up (the player's
        # Reach games: well-aimed shots crossing 0.3-0.5 up hit 60-78%, 0.6 40%, 0.7 18%); crouched, 70% of
        # that. The old box (0.3 to each side, 0.54 up and down) counted almost every shot a bot fired
        y = angles_to(eye(p), e_at)[0]
        side = abs(d * math.sin(wrap(p.yaw - y)))
        h = eye(p).z + d * math.tan(p.pitch) - e_at.z
        k = (0.7 if getattr(e, "crouching", False) else 1.0) * HIT_SIZE.get(w, 1.0)
        if s.now < s.state.get(e.id, {}).get("airborne_until", 0.0):   # (a hologram has no state)
            k *= 0.85   # a jumping target is a little harder to track
        head = side < 0.07 * k and 0.58 * k <= h < 0.70 * k and w not in HIT_SIZE
        if not head and not (side < 0.12 * k and 0.08 * k < h < 0.58 * k):
            return
        s.stats[p.id]["hits"] += 1
        s.damage(e, p, BODY_DMG.get(w, 0.4), head)

    def melee(s, p):
        om = getattr(s, "objmodes", None)
        if om is not None and om.mode == "invasion" and om.core.get("carrier") == p.id:
            # Reach drops the Invasion core on its carrier's melee press (live Spire 18 of 18, Boneyard 2 of 2 carries
            # ended within 1 s; logs/tmp/invasion_regress/melee_drop.py): no swing, the core falls at his feet
            om.core["carrier"], om.core["pos"], p.has_flag = None, p.pos, False
            om.events.append((round(s.now, 1), f"{p.id} dropped the core (melee)"))
            return
        for e in s.players:
            if e.team != p.team and e.alive and dist(p.pos, e.pos) < 1.4:
                s.damage(e, p, 9 if p.has_flag else 0.8, False)   # flag melee kills
                return

    def grenade(s, p):
        e = s.target_in_crosshair(p)
        if e and dist(p.pos, e.pos) < 25 and s.rng.random() < 0.4:
            s.damage(e, p, 0.6, False)

    def damage(s, e, src, amount, head):
        if e.decoy:                          # a hologram dies to any hit (no kill: nobody was there)
            e.alive = False
            return
        if s.gear.immune(e, src):            # armor lock; a hardlight shield from in front
            return
        s.state[e.id]["last_hit"] = s.now
        had_shield = e.shield > 0
        if head and e.shield <= 0:
            e.health = 0
        else:
            take = min(e.shield, amount)
            e.shield -= take
            e.health -= amount - take
        if e.health <= 0 and e.alive:
            s.kill(e, src)
        elif e.alive and src.team != e.team:
            # the shooter calls it, like a player shouting "cracked" / "one shot"
            if had_shield and e.shield <= 0:
                s.report(src.team, s.now, src.id, "one_shot" if e.health < 0.5 else "cracked", e.pos, e.id, True)

    def switch_team(s, pid, team):
        """A player's side changes (Juggernaut, Infection): his bot moves to that team's director, its plan reset."""
        p = next(q for q in s.players if q.id == pid)
        b = s.bots[pid]
        if p.team == team:
            return
        s.directors[p.team].bots.pop(pid, None)
        s.directors[p.team].roles.pop(pid, None)
        p.team = b.team = team
        s.directors[team].bots[pid] = b
        b.per.beliefs.clear()

    def kill(s, e, src):
        e.alive = False
        s.state[e.id]["respawn_at"], s.state[e.id]["flight"] = s.now + 5.0, None
        s.stats[e.id]["deaths"] += 1
        s.stats[src.id]["kills"] += 1
        if s.mode == "slayer":
            s.score[src.team] += 1
        # dead players still talk: they call where the killer is and whether he is hurt
        s.report(e.team, s.now, e.id, "died", src.pos, src.id, killer_weak=src.shield <= 0, died_at=e.pos)
        s.bots[e.id].on_death(src.id)
        if s.objmodes is not None:
            s.objmodes.on_kill(e, src)
        if e.has_flag:
            e.has_flag = False
            f = s.flags[1 - e.team]
            f.state, f.pos, f.carrier = "dropped", e.pos, -1
            # owners see their dropped flag on the HUD waypoint: announcer-fast
            s.report(1 - e.team, s.now, -1, "flag_dropped", e.pos)

    def set_one_flag(s, defenders=0, round_s=180.0):
        """One Flag CTF (Avalanche live): one flag on team 0's stand, its the player the defending side; the attackers
        score on the other stand; the sides swap at a capture or after round_s (the flag keeps its stand)."""
        s.one_flag = dict(d=defenders, round_s=round_s, until=s.now + round_s, stand=s.m["flags"][0],
                          goal=s.m["flags"][1])
        s.flags = {defenders: FlagState(defenders, s.one_flag["stand"], s.one_flag["stand"])}

    def ctf_one(s):
        o = s.one_flag
        f = s.flags[o["d"]]
        over = s.now >= o["until"]
        for p in s.players:
            if not p.alive:
                continue
            if p.team != o["d"] and f.state != "carried" and dist(p.pos, f.pos) < 1.2:
                f.state, f.carrier, p.has_flag = "carried", p.id, True
                s.flag_events.append((s.now, "taken", p.team))
                s.report(o["d"], s.now, -1, "flag_taken", f.home)
            elif p.team == o["d"] and f.state == "dropped" and dist(p.pos, f.pos) < 1.2:
                f.state, f.pos = "home", f.home
                s.flag_events.append((s.now, "returned", p.team))
            if p.has_flag:
                f.pos = p.pos
                if dist(p.pos, o["goal"]) < 1.5:
                    s.score[p.team] += 1
                    s.stats[p.id]["caps"] += 1
                    s.flag_events.append((s.now, "captured", p.team))
                    over = True
        if over:                                    # the next round: the sides swap, the flag back on its stand
            for p in s.players:
                p.has_flag = False
            s.flag_events.append((s.now, "round", o["d"]))
            s.set_one_flag(1 - o["d"], o["round_s"])

    def ctf(s):
        if getattr(s, "one_flag", None) is not None:
            return s.ctf_one()
        for p in s.players:
            if not p.alive:
                continue
            enemy_flag, own_flag = s.flags[1 - p.team], s.flags[p.team]
            if enemy_flag.state != "carried" and dist(p.pos, enemy_flag.pos) < 1.2:
                enemy_flag.state, enemy_flag.carrier = "carried", p.id
                p.has_flag = True
                s.flag_events.append((s.now, "taken", p.team))
                s.report(1 - p.team, s.now, -1, "flag_taken", own_flag.home)   # announcer
            if own_flag.state == "dropped" and dist(p.pos, own_flag.pos) < 1.2:
                own_flag.state, own_flag.pos = "home", own_flag.home
                s.flag_events.append((s.now, "returned", p.team))
            if p.has_flag:
                enemy_flag.pos = p.pos
                if own_flag.state == "home" and dist(p.pos, own_flag.home) < 1.5:
                    s.score[p.team] += 1
                    s.stats[p.id]["caps"] += 1
                    p.has_flag = False
                    enemy_flag.state, enemy_flag.pos, enemy_flag.carrier = "home", enemy_flag.home, -1
                    s.flag_events.append((s.now, "captured", p.team))

    def run(s, seconds, trace=None, pace=False):
        """trace: an open file: the live trace format (tools/observer.py reads
        both): bot and world lines, plus who is who, every decision and every callout (brain/tracefmt.py).
        pace: run at wall-clock speed."""
        wall0, sim0 = time.monotonic(), s.now
        import json
        from .tracefmt import Everyone, blitz_rows, call_lines, meta_line, think_line
        said, decided = set(), {}
        everyone, bot_ids = Everyone(), {p.id for p in s.players}
        if trace is not None:
            name = (getattr(s, "m", None) or {}).get("name", "bloodgulch")
            for p in s.players:
                trace.write(meta_line(s.now, name, "sim", p.id, f"bot {p.id}", p.team, s.bots[p.id].p))
        notes = {p.id: [] for p in s.players}          # one-tick notes (an armor lock, a dash) between lines
        for k in range(int(seconds / TICK)):
            s.step()
            if pace and s.now - sim0 > time.monotonic() - wall0:
                time.sleep(s.now - sim0 - (time.monotonic() - wall0))
            if getattr(s, "limit", 0) and max(s.score.values()) >= s.limit:
                break                                  # the game ends on the score limit, as in Halo
            for p in s.players:
                notes[p.id] += [n for n in getattr(s.bots[p.id], "notes", []) if n not in notes[p.id]]
            if trace is not None and k % 3 == 0:
                for p in s.players:
                    b = s.bots[p.id]
                    a = s.last_actions[p.id]
                    line = dict(t=round(s.now, 3), id=p.id, team=p.team, pos=[round(p.pos.x, 2), round(p.pos.y, 2), round(p.pos.z, 2)],
                                yaw=round(p.yaw, 3), pitch=round(p.pitch, 3), goal=b.goal[0], arg=str(b.goal[1])[:40], veh=-1,
                                wpn=p.weapon, foes=[[e.id, round(e.shield, 2), round(e.health, 2)] for e in s.players if e.team != p.team],
                                cmd=[round(a.forward, 2), round(a.strafe, 2), round(a.yaw, 3), int(a.fire), round(a.pitch, 3)]
                                if p.alive else [0.0, 0.0, 0.0, 0, 0.0])
                    if p.alive and getattr(b, "fx", None):
                        line["fx"] = b.fx
                    if p.alive and getattr(b, "att", None):
                        line["att"] = b.att                  # what it looks at and why
                    if p.alive and notes[p.id]:
                        line["notes"] = notes[p.id]
                    notes[p.id] = []
                    if p.equipment:
                        line["eq"] = [p.equipment, p.ability_on]
                    trace.write(json.dumps(line) + "\n")
                    if p.alive and decided.get(p.id) != b.next_decide:   # it decided since the last line
                        decided[p.id] = b.next_decide
                        trace.write(think_line(s.now, p.id, b))
                for d in s.directors.values():
                    trace.writelines(call_lines(s.now, d, said))
            if trace is not None and k % 8 == 0:
                om = getattr(s, "objmodes", None)       # Invasion as the live trace writes it (tools/live_bots.py):
                inv = None                              # [phase, attackers, core x, y, z, carrier]
                if om is not None and s.mode == "invasion":
                    c = om.core["carrier"]
                    cp = s.players[c].pos if c is not None else om.core["pos"]
                    inv = [om.phase, 1, round(cp.x, 2), round(cp.y, 2), round(cp.z, 2), c]
                trace.write(json.dumps(dict(t=round(s.now, 3), mode=s.mode, score={str(t): v for t, v in s.score.items()},
                                            invasion=inv,
                                            limit=getattr(s, "limit", 0), time_left=None,
                                            posture={str(t): d.posture_state for t, d in s.directors.items()},
                                            blitz=blitz_rows(s.directors),
                                            world=everyone.rows(s.now, s.players, bot_ids, s.los),   # + still, formed up, sights
                                            deployed=[[d["kind"], round(d["pos"].x, 2), round(d["pos"].y, 2), round(d["pos"].z, 2), d["team"]]
                                                      for d in s.gear.deployed]
                                            + [["hologram", round(h.pos.x, 2), round(h.pos.y, 2), round(h.pos.z, 2), h.team]
                                               for h in s.gear.decoys])) + "\n")


class CommsMeter:
    """Measures callouts: per-call latency (event -> teammates understood), how long a team
    takes to learn about an enemy one of them saw, how stale the info is when heard, and
    how many sightings never reach the team."""

    def __init__(s, sim):
        s.sim = sim
        s.seen_at = {}        # (team, enemy) -> first sighting time of the current episode
        s.team_latency = []   # first sighting -> first heard callout naming that enemy
        s.never = 0
        s.call_latency = {}   # kind -> [latency]
        s.stale = []          # world units between where it was called and where he is when heard
        s.start_gap = s.hear_gap = 1e9
        s.by_tier = {}        # speaker tier -> sighting call latencies

        s.covered_n = 0       # sightings the team already knew from a call about that zone

    def reported(s, team, kind, enemy, now):
        if kind == "seen" and enemy is not None and (team, enemy) not in s.seen_at:
            s.seen_at[(team, enemy)] = now

    def covered(s, team, kind, enemy):
        if kind == "seen" and s.seen_at.pop((team, enemy), None) is not None:
            s.covered_n += 1

    def update(s):
        now = s.sim.now
        for team, d in s.sim.directors.items():
            for c in d.callouts:
                if getattr(c, "metered", False):   # (not id(): ids are reused after objects die)
                    continue
                c.metered = True
                s.call_latency.setdefault(c.kind, []).append(c.t_heard - c.t_event)
                if c.speaker >= 0 and not d.voice.legacy:
                    s.start_gap = min(s.start_gap, c.t_start - c.t_event)    # invariant: >= 0.22
                    s.hear_gap = min(s.hear_gap, c.t_heard - c.t_key)        # invariant: >= 0.10
                    if c.kind == "seen":
                        s.by_tier.setdefault(c.tier, []).append(c.t_heard - c.t_event)
                for e in c.enemies:
                    if e is None or e < 0:
                        continue
                    t0 = s.seen_at.pop((team, e), None)
                    if t0 is not None and c.kind in ("seen", "flag_carrier"):
                        s.team_latency.append(c.t_heard - t0)
                    if e >= len(s.sim.players):        # a hologram someone called out: no player to check
                        continue
                    pl = s.sim.players[e]
                    if c.kind == "seen" and pl.alive:
                        s.stale.append(math.hypot(pl.pos.x - c.pos_said.x, pl.pos.y - c.pos_said.y))
        for k, t0 in list(s.seen_at.items()):
            if now - t0 > 6.0:      # nobody ever told the team
                del s.seen_at[k]
                s.never += 1

    def summary(s):
        q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
        seen = s.call_latency.get("seen", [])
        urgent = [x for k in ("flag_taken", "flag_carrier", "died_at_flag", "flag_dropped") for x in s.call_latency.get(k, [])]
        n_calls = sum(len(v) for v in s.call_latency.values())
        minutes = max(s.sim.now / 60, 1e-9)
        return {
            "calls_per_min_per_team": round(n_calls / minutes / 2, 1),
            "sighting_call_median_s": round(statistics.median(seen), 2) if seen else None,
            "sighting_call_p90_s": round(q(seen, 0.9), 2),
            "urgent_call_median_s": round(statistics.median(urgent), 2) if urgent else None,
            "team_knows_median_s": round(statistics.median(s.team_latency), 2) if s.team_latency else None,
            "team_knows_p90_s": round(q(s.team_latency, 0.9), 2),
            "sightings_never_called_pct": round(100 * s.never / max(1, s.never + len(s.team_latency) + s.covered_n), 1),
            "stale_wu_median": round(statistics.median(s.stale), 1) if s.stale else None,
            "merged": sum(d.voice.merged for d in s.sim.directors.values()),
            "dropped": sum(d.voice.dropped for d in s.sim.directors.values()),
            "talk_share_pct": round(100 * statistics.mean(d.voice.talk_share(s.sim.now) for d in s.sim.directors.values()), 1),
            "sighting_median_by_tier": {t: round(statistics.median(v), 2) for t, v in sorted(s.by_tier.items())},
        }


def report(sim, label):
    st = sim.stats
    acc = {}
    for v in st.values():
        a = acc.setdefault(v["tier"], [0, 0])
        a[0] += v["hits"]; a[1] += v["shots"]
    kills = sum(v["kills"] for v in st.values())
    print(f"== {label}: score {sim.score}, kills {kills}, callouts {len(sim.log)}")
    print("   accuracy by tier:", {k: f"{h / max(n, 1):.0%} ({n} shots)" for k, (h, n) in acc.items()})
    for ev in sim.flag_events[:6]:
        print("   flag", ev)
    for line in sim.log[:8]:
        print("   callout", line)
    print("   comms:", sim.comms.summary())
    return acc


def compare_comms(seconds=300, seeds=(7, 8, 9)):
    """Same games, old flat-delay comms vs the voice channel."""
    rows = {}
    for legacy in (True, False):
        agg = {}
        for sd in seeds:
            sim = Sim("ctf", per_team=8, seed=sd, legacy_comms=legacy)
            sim.run(seconds)
            for k, v in sim.comms.summary().items():
                if isinstance(v, dict):
                    for t, x in v.items():
                        agg.setdefault(f"sighting_median_{t}", []).append(x)
                elif v is not None and not (isinstance(v, float) and math.isnan(v)):
                    agg.setdefault(k, []).append(v)
        rows["old flat delay" if legacy else "voice channel"] = {k: round(statistics.mean(v), 2) for k, v in agg.items()}
    keys = list(next(iter(rows.values())).keys())
    print(f"{'metric':32s}" + "".join(f"{n:>18s}" for n in rows))
    for k in keys:
        print(f"{k:32s}" + "".join(f"{rows[n].get(k, float('nan')):>18}" for n in rows))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=600)
    ap.add_argument("--compare-comms", action="store_true")
    ap.add_argument("--trace", help="one game only, written in the live trace format (tools/observer.py)")
    ap.add_argument("--map", default="bloodgulch")
    ap.add_argument("--mode", default="slayer")
    ap.add_argument("--per-team", type=int, default=4)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    if a.trace:
        sim = Sim(a.mode, per_team=a.per_team, seed=a.seed, map_name=a.map)
        sim.limit = a.limit
        with open(a.trace, "w") as f:
            sim.run(a.seconds, trace=f)
        report(sim, f"{a.mode} {a.per_team}v{a.per_team} on {a.map}, {a.seconds:.0f} s")
        return
    if a.compare_comms:
        compare_comms()
        return
    t0 = time.monotonic()
    slayer = Sim("slayer", per_team=4, seed=3)
    slayer.run(300)
    acc = report(slayer, "Slayer 4v4, 300 s")
    ctf = Sim("ctf", per_team=8, seed=7)
    ctf.run(a.seconds)
    acc_ctf = report(ctf, f"CTF 8v8, {a.seconds:.0f} s")
    small = Sim("ctf", per_team=(3, 1), seed=11, tiers=["strong", "novice"])
    small.run(400)
    report(small, "CTF 3v1, 400 s")
    print(f"   wall time {time.monotonic() - t0:.1f} s")

    # --- self-checks: the smallest things that fail if the brain breaks
    assert sum(v["kills"] for v in slayer.stats.values()) >= 10, "bots barely fight"
    # both team matches pooled: one 4v4 seed is 100-300 shots a tier, and any behaviour change sends it down another
    # path (Easy 36% -> 47%, Normal 42% -> 32% from a look change alone)
    rate = lambda t: (acc[t][0] + acc_ctf.get(t, (0, 0))[0]) / max(acc[t][1] + acc_ctf.get(t, (0, 0))[1], 1)
    # the player: difficulty is behaviour;: Legendary's hands sharper ("better accuracy"), never an aimbot's
    assert -0.05 < rate("top") - rate("novice") < 0.25, f"tier accuracy off: top {rate('top'):.2f} novice {rate('novice'):.2f}"
    lat = [x for *_, x, _k in ctf.log]
    assert lat and min(lat) >= 0.3 and max(lat) <= 6.0, f"callout latency out of range {min(lat)}..{max(lat)}"
    # research 07 anti-psychic invariants
    assert ctf.comms.start_gap >= 0.22 - 1e-9, f"a call started {ctf.comms.start_gap:.2f} s after recognition"
    assert ctf.comms.hear_gap >= 0.10 - 1e-9, f"a call was understood {ctf.comms.hear_gap:.2f} s after its key words"
    zones = BLOODGULCH["zones"]
    for spot, want in ZONE_SPOTS:
        got = zones.name(spot)
        assert got == want, f"zone at {spot} is {got}, expected {want}"
    zone_names = {z.name for z in zones.zones}
    assert any(any(n in text for n in zone_names) for _, _, text, *_ in ctf.log), "callouts do not name zones"
    assert any(e[1] == "taken" for e in small.flag_events), "no one ever took a flag"
    assert small.score[0] >= 1, "flag taken but never brought home"
    assert all(v["moved"] > 30 for k, v in ctf.stats.items()
               if ctf.bots[k].order.role != "defender"), "a bot never moved"   # defenders may stand guard
    roles = [set(d.roles.values()) for d in ctf.directors.values()]
    assert all({"defender", "runner"} & r for r in roles), f"roles not handed out: {roles}"
    print("self-check OK")


if __name__ == "__main__":
    main()
