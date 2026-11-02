"""Equipment and armor abilities in the simulator (brain/sim.py), so the brain's uses and counters
(brain/equipment.py) run end to end offline. The effects are the guide's (guide 08), the energy the
kits' tags (brain/equipment_tags.json); amounts like a heal field's rate are the simulator's own
round numbers (it checks behaviour, not balance). Not modelled: grav lift launches, deployable
cover walls (they are placed and seen, nothing more), vehicles stopped by domes.

Reach bots carry the default Spartan abilities in turn, Halo 4 bots the Halo 4 ones; Halo 3 bots
pick equipment up where the map places it."""
import math

from .core import Vec, PlayerState, dist, angles_to, wrap, TICK
from .equipment import DOMES, HEALS, ITEM, TAGS, Energy, hold_bit

PALETTE = {"reach": ["sprint", "armor_lock", "jetpack", "hologram", "active_camo", "drop_shield", "evade"],
           "h4": ["thruster", "promethean_vision", "hardlight_shield", "hologram", "active_camo", "regen_field",
                  "autosentry", "jetpack"]}
ONE_SHOT = {"hologram", "thruster", "evade", "drop_shield", "regen_field", "autosentry"}   # fire on the press
THROWN = {"power_drain", "flare", "radar_jammer"}       # Halo 3: thrown ahead, the rest placed in front
HEAL_RATE = {"regenerator": 0.4, "drop_shield": 0.3, "regen_field": 0.3}    # shield a second, inside
DRAIN_RATE = 0.6                                         # power drain, shield a second
NADE_SEEN = 2.0                                          # s a thrown grenade is on the ground to be seen (a frag's fuse)
SPEED = {"sprint": 1.5, "jetpack": 1.1, "hardlight_shield": 0.5, "active_camo": 0.6}


class Gear:
    def __init__(s, sim):
        s.sim, s.game = sim, sim.game
        s.deployed, s.decoys, s.next_id = [], [], 100
        s.nades = []                                         # grenades thrown, for the snapshot (NADE_SEEN s)
        for p in sim.players:
            kinds = PALETTE.get(s.game)
            if kinds:
                p.equipment = kinds[p.id % len(kinds)]
            sim.state[p.id].update(energy=Energy(s.game, p.equipment) if p.equipment in TAGS.get(s.game, {}) else None,
                                   pressed=False, on_until=0.0)

    # ---------------------------------------------------------------- per player, per tick
    def tick_player(s, p, a, st):
        """The press -> the ability: returns (speed factor, may move, may shoot)."""
        now, kind, en = s.sim.now, p.equipment, st.get("energy")
        if a.grenade and not st.get("nade_prev"):
            # a throw others can see land: by the man in its sights, else 8 u ahead (the simulator's grenade does its
            # damage at once, Sim.grenade; this is only what a player sees coming, for Kit.plan's dash out of it)
            e = s.sim.target_in_crosshair(p)
            at = e.pos if e is not None else p.pos + Vec(math.cos(p.yaw), math.sin(p.yaw), 0) * 8.0
            s.nades.append(dict(pos=at, team=p.team, t=now))
        st["nade_prev"] = a.grenade
        # Reach reads a hold-mode ability (its tag's mode) only with the held bit as well (brain/equipment.py hold_bit;
        # live: without it no armor lock, evade, jetpack, hologram or drop shield ever came on)
        held = a.equipment and (a.ability or not (s.game == "reach" and hold_bit(s.game, kind)))
        edge = held and not st["pressed"]
        st["pressed"] = held
        if kind in ITEM and kind not in TAGS.get(s.game, {}):          # Halo 3: single-use equipment
            if edge:
                s.deploy(p, kind)
                p.equipment = ""
            return 1.0, True, True
        if en is None:
            return 1.0, True, True
        was = p.ability_on
        if kind in ONE_SHOT:
            on = False
            if edge and en.ready():
                s.fire_one(p, kind, a)
                en.level = 0.0 if en.need >= 1.0 else en.level - max(en.cost, 0.0)
                on = True
                st["on_until"] = now + (0.4 if kind in ("thruster", "evade") else 0.1)
        elif en.mode == "toggle":
            on = (not was and en.ready()) if edge else was
        else:
            on = held and (was or en.ready())
        on = en.tick(now, TICK, on) if kind not in ONE_SHOT else on
        p.ability_on = on or now < st["on_until"]
        if was and not p.ability_on and kind == "armor_lock":
            for e in s.sim.players:                     # the lock ends in an EMP: nearby shields pop
                if e.team != p.team and e.alive and dist(e.pos, p.pos) < ITEM["armor_lock"][2]:
                    e.shield = min(e.shield, 0.0)
        if kind == "active_camo" and p.ability_on:
            p.camo_until = now + 0.3
            if a.fire:                                  # firing breaks camo (guide 08)
                p.ability_on, p.camo_until = False, 0.0
                en.tick(now, TICK, False)
        if not p.ability_on:
            return 1.0, True, True
        if kind == "armor_lock":
            return 0.0, False, False
        if kind == "hardlight_shield":
            return SPEED[kind], True, False
        if kind == "sprint":
            return SPEED[kind], True, False
        return SPEED.get(kind, 1.0), True, True

    def fire_one(s, p, kind, a):
        now = s.sim.now
        ahead = Vec(math.cos(p.yaw), math.sin(p.yaw), 0)
        if kind == "hologram":
            s.next_id += 1
            to = p.pos + ahead * 10.0
            d = PlayerState(s.next_id, p.team, "hologram", p.pos, vel=ahead * 2.2, yaw=p.yaw, alive=True,
                            weapon=p.weapon, decoy=True, is_bot=False)
            d.until, d.goal = now + ITEM["hologram"][1], to
            s.decoys.append(d)
        elif kind in ("thruster", "evade"):
            c, sn = math.cos(p.yaw), math.sin(p.yaw)
            wx, wy = a.forward * c - a.strafe * sn, a.forward * sn + a.strafe * c
            n = math.hypot(wx, wy) or 1.0
            if math.hypot(wx, wy) < 0.1:
                wx, wy, n = c, sn, 1.0
            for _ in range(5):                          # a dash of about 1.5 units, wall-aware
                s.sim.move(p, wx / n * 0.3, wy / n * 0.3)
        else:
            s.deploy(p, kind)

    def deploy(s, p, kind):
        """Halo 3 equipment (thrown ahead or set down in front) and the Reach / Halo 4 fields."""
        how, dur, _ = ITEM[kind]
        ahead = Vec(math.cos(p.yaw), math.sin(p.yaw), 0)
        if kind in THROWN:
            pos = p.pos + ahead * 3.0
        elif how == "front" or kind == "trip_mine":
            pos = p.pos + ahead * 1.0
        else:
            pos = p.pos
        s.deployed.append(dict(kind=kind, pos=pos, team=p.team, t=s.sim.now, until=s.sim.now + dur,
                               owner=p.id, hp=1.5, next_shot=0.0))

    # ---------------------------------------------------------------- the world, per tick
    def update(s):
        now = s.sim.now
        s.deployed = [d for d in s.deployed if now < d["until"] and d["hp"] > 0]
        for d in s.deployed:
            k = d["kind"]
            r = ITEM[k][2]
            for e in s.sim.players:
                if not e.alive or dist(e.pos, d["pos"]) > r:
                    continue
                if k in HEAL_RATE and e.shield < 1.0:
                    e.shield = min(1.0, e.shield + HEAL_RATE[k] * TICK)
                if k == "power_drain":
                    e.shield = max(0.0, e.shield - DRAIN_RATE * TICK)
            if k == "trip_mine" and now - d["t"] > 3.0:
                hit = [e for e in s.sim.players if e.alive and e.team != d["team"] and dist(e.pos, d["pos"]) < 0.6]
                if hit:
                    src = next((q for q in s.sim.players if q.id == d["owner"]), hit[0])
                    for e in s.sim.players:
                        if e.alive and dist(e.pos, d["pos"]) < 1.5:
                            s.sim.damage(e, src, 2.0, False)
                    d["hp"] = 0
            if k == "autosentry" and now >= d["next_shot"]:
                d["next_shot"] = now + 0.25
                foes = [e for e in s.sim.players if e.alive and e.team != d["team"] and dist(e.pos, d["pos"]) < r
                        and s.sim.los(d["pos"], e.pos)]
                if foes:
                    src = next((q for q in s.sim.players if q.id == d["owner"]), foes[0])
                    s.sim.damage(min(foes, key=lambda e: dist(e.pos, d["pos"])), src, 0.04, False)
        for h in s.decoys:
            if not h.alive or now > h.until:
                h.alive = False
                continue
            old = h.pos
            if dist(h.pos, h.goal) > 0.4:
                step = (h.goal - h.pos).norm() * (2.2 * TICK)
                nxt = Vec(h.pos.x + step.x, h.pos.y + step.y, h.pos.z)
                if s.sim.T.can_step(h.pos, nxt):
                    h.pos = Vec(nxt.x, nxt.y, s.sim.T.nav_z(nxt.x, nxt.y, h.pos.z))
            h.vel = Vec((h.pos.x - old.x) / TICK, (h.pos.y - old.y) / TICK, 0)
        s.decoys = [h for h in s.decoys if h.alive]

    def snapshot(s, snap):
        snap.players = list(snap.players) + s.decoys
        snap.deployed = [dict(kind=d["kind"], pos=d["pos"], team=d["team"], t=d["t"]) for d in s.deployed]
        s.nades = [g for g in s.nades if s.sim.now - g["t"] < NADE_SEEN]
        snap.grenades = [dict(g) for g in s.nades]

    # ---------------------------------------------------------------- shots and damage
    def blocked(s, shooter, target):
        """A dome between them: shots do not cross it (a drop shield takes the damage and breaks)."""
        for d in s.deployed:
            if d["kind"] in DOMES:
                r = ITEM[d["kind"]][2]
                if (dist(shooter.pos, d["pos"]) < r) != (dist(target.pos, d["pos"]) < r):
                    if d["kind"] == "drop_shield":
                        d["hp"] -= 0.3
                    return True
        return False

    def immune(s, e, src):
        """Armor lock takes nothing; a hardlight shield takes nothing from in front."""
        if not e.ability_on:
            return False
        if e.equipment == "armor_lock":
            return True
        if e.equipment == "hardlight_shield":
            yaw, _ = angles_to(e.pos, src.pos)
            return abs(wrap(yaw - e.yaw)) < 1.0
        return False
