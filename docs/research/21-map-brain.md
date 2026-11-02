# Halo MCC Map Brain: Map Control, Interactables, Callouts, and Coach Map Commands

Fifth file in the set. The other brains refer to "hold spots," "power positions," "lanes," "return routes," and "spawn zones" without saying where they are. This file is the layer that supplies them: how a map is described as data, what every kind of interactable does to bot logic (man cannons, lifts, teleporters, switch-operated gates, falling stalactites, trains, shield doors, EMP switches, moving wheels), how power positions and callouts are built, the map command set the optional Ollama coach uses, and per-game entries for the MCC map pools.

**Status tags:** **Rule** (how the map or feature works, sourced to Halopedia, Fandom, StrategyWiki, or developer statements), **Source** (a tactic reported by a guide or community thread), **Proposed** (design for this mod, untested), **Verify** (believed correct from general knowledge, not confirmed by a retrieved source; check in MCC before coding against it).

**ID formats:** `MAP-NN` framework rules, `INTER-<TYPE>-NN` interactable rules, `CALL-NN` callout grammar, `MCMD-<NAME>` coach map commands, and per-map play IDs `<GAME>-<MAP>-PLAY-NN`.

---

## Part 0. How the map layer plugs in

```
MAP KNOWLEDGE PACK (one JSON per map, per game)
   nodes, lanes, sightlines, power positions, hold spots, spawn zones,
   objective positions per gametype, weapon/power-up/vehicle spawns + timers,
   interactables (type, trigger, effect, duration, who can use), callout names
            |
            v
OBJECTIVE BRAIN reads the pack to resolve "hold spot", "power position", "return route", "lane", "spawn zone"
VEHICLE BRAIN reads lanes, vehicle spawns, ram-safe roads, blind corners, man-cannon trajectories
EQUIPMENT BRAIN reads power-up spawns and timers
COACH (optional) receives the pack's callout names and interactable list and may issue map commands (Part 3)
```

- `MAP-01` **One pack per map per game.** Remakes are separate packs (Blood Gulch, Coagulation, Bloodline, Hemorrhage, Valhalla, Ragnarok are six packs) because spawns, vehicles, timers, and interactables differ.
- `MAP-02` **Nodes are named with callouts.** Every node carries its community callout (Part 2.3) so bots, logs, and the coach use the same vocabulary.
- `MAP-03` **Gametype overlays.** A pack holds one base layout plus per-gametype overlays: objective positions, which lanes are carrier-safe, which power positions matter for that mode, and which interactables change value (the Zanzibar gate matters in One Flag far more than in Slayer).
- `MAP-04` **Interactables are first-class.** Each one is an object with `type`, `trigger` (walk / shoot / melee / press / timed / scripted), `effect`, `duration`, `reversible`, `who` (either team, one team, anyone), `cooldown`, and `bot_rules` (links to Part 1).
- `MAP-05` **Everything here is a starting template.** Power positions and hold spots in Part 4 come from guides and community consensus; the objective brain's scorers (`ODD-CORE-01`, `FF-POS-01`) re-rank them with live data (where the enemy actually is, which vehicles are up).

### 0.1 Map knowledge pack schema (Proposed)

```json
{
  "game": "H3", "map": "Narrows", "layout": "symmetric", "size": "medium", "players": "4v4",
  "teams": {"blue": {"base_node": "blue_base"}, "yellow": {"base_node": "yellow_base"}},
  "nodes": [
    {"id": "top_mid", "callout": "Top Mid", "pos": [x,y,z], "level": 2, "cover": 0.4, "sightlines_to": ["blue_top","yellow_top","bottom_mid"]},
    {"id": "blue_cannon_pad", "callout": "Blue Cannon", "pos": [..], "level": 1}
  ],
  "lanes": [
    {"id": "top_bridge", "nodes": ["blue_top","top_mid","yellow_top"], "vehicle_ok": false, "carrier_safe_if": ["no_enemy_at:top_mid"]},
    {"id": "bottom_bridge", "nodes": ["blue_bottom","bottom_mid","yellow_bottom"], "vehicle_ok": false},
    {"id": "cannon_blue_to_yellow", "nodes": ["blue_cannon_pad","yellow_top"], "type": "man_cannon", "carrier_safe_if": ["no_enemy_at:yellow_top"]}
  ],
  "power_positions": [{"node": "top_mid", "value": 0.9, "modes": ["SLAY","KOTH"]}],
  "hold_spots": [{"node": "blue_low", "single_approach": true, "modes": ["ODD"]}],
  "spawn_zones": [{"id": "blue_spawns", "nodes": ["blue_base","blue_low"], "team": "blue", "weight_rules": "away_from_enemy_los"}],
  "spawns": {
    "weapons": [{"item": "rocket_launcher", "node": "bottom_mid", "timer": 180, "timer_rule": "game_clock"}],
    "powerups": [{"item": "overshield", "node": "blue_low", "timer": 120, "timer_rule": "after_pickup"}],
    "vehicles": []
  },
  "interactables": [
    {"id": "blue_cannon", "type": "man_cannon", "trigger": "walk", "from": "blue_cannon_pad", "to": "yellow_top_landing",
     "trajectory": "fixed", "flight_time": 3.5, "effect": "launch", "who": "anyone", "bot_rules": ["INTER-CANNON-01..06"]}
  ],
  "overlays": {
    "CTF-MULTI": {"flags": {"blue": "blue_flag_stand", "yellow": "yellow_flag_stand"}, "return_routes": ["bottom_bridge","cannon_*"], "hot_zones": ["top_mid"]},
    "KOTH-STATIC": {"hill_candidates": ["top_mid","bottom_mid"], "ring_positions": {"top_mid": ["blue_top","yellow_top"]}}
  },
  "callout_aliases": {"top_mid": ["Top Mid", "Mid Bridge"], "bottom_mid": ["Bottom Mid", "Low Bridge"]}
}
```

---

## Part 1. Interactable taxonomy and bot rules

Each type below lists how it works, what it does to bot pathing and tactics, and how the enemy exploits it. The vehicle, objective, and equipment brains call these rules by ID.

### 1.1 Man cannons (large gravity launchers)

**Rule:** Halo 3 introduced them (Valhalla, Narrows, Avalanche, Sandtrap, Guardian, Standoff, Sandbox, Orbital); Reach and Halo 4 keep them on some maps (Ragnarok, Exile, Longbow, Forge pieces). Narrows cannons fire on a **fixed trajectory** regardless of weight; Valhalla cannons are **weight-based** (a Mongoose flies lower and shorter) (Halopedia Narrows). On Narrows the cannons are the fastest route across, the flag can be thrown through a cannon and the thrower stays behind, a Power Drain or grenades can be thrown into a cannon to hit the landing, a Regenerator can push a player back through a cannon, and the easiest kill is to wait at the receiving end (Halopedia, Fandom). On Valhalla, throwing a Power Drain from the ground into the cannon does not reach the hill; the player must ride the cannon and throw in flight (Halopedia Valhalla). Trip mines in a cannon overload it (Forge).

**Bot rules**
- `INTER-CANNON-01` Pathfinding treats a cannon as a one-way edge with a fixed `flight_time` and a fixed landing node; the bot cannot steer mid-air (except Valhalla-style weight-based cannons where vehicles land shorter: the pack stores a vehicle landing node separately).
- `INTER-CANNON-02` Never take a cannon when an enemy is at or within 10 m of the landing node (sightlines in the pack). A flying bot is a free kill; the coach callout "watch cannon" sets the landing node to hot.
- `INTER-CANNON-03` Flag/bomb/ball through the cannon: in modes where the objective can be thrown, the carrier throws the objective into the cannon and lets a teammate at the landing catch it (`CTF` Narrows play); the carrier itself only rides when the landing is clear.
- `INTER-CANNON-04` Grenade and Power Drain delivery: a bot with line of sight to a cannon throws grenades (or a Power Drain, Halo 3) into it to land on a known camper at the landing; on weight-based cannons the bot rides and throws in flight.
- `INTER-CANNON-05` Landing ambush: the RING/ANCHOR role pre-aims the landing node of any cannon that leads to our position; the combat brain gets a predicted-arrival event (`flight_time` after the enemy is seen entering).
- `INTER-CANNON-06` Vehicles in cannons: a Mongoose or Warthog through a cannon is a flank, not a transport for carriers (vehicle file: never put the carrier in a vehicle through a lane the enemy controls). Chopper and Ghost through a cannon land on top of infantry: a splatter opportunity if the landing is an infantry node.

### 1.2 Gravity lifts (vertical)

**Rule:** Lockout/Lockdown, Ascension/Zenith, Ivory Tower/Reflection, Construct (three lifts, any floor to top), Guardian, Blackout, Warlock/Warlord (one lift per corner to the raised platform), Sword Base, Countdown, Reach and Halo 4 Forge pieces. Lifts are slow, loud, one-way, and the exit is a fixed point.

**Bot rules**
- `INTER-LIFT-01` One-way vertical edge; the exit node is a known camp point. Never ride a lift when an enemy is within 8 m of the exit or holds a sightline onto it; use the ramp route instead (the pack lists the alternate).
- `INTER-LIFT-02` Lift exits are grenade points: a defender throws a grenade onto the exit when the lift sound plays; the attacker pre-fires the exit's cover when it arrives.
- `INTER-LIFT-03` Lifts are escape routes for carriers and ball holders only when the exit is held by a teammate (Ascension: the ball carrier's two escapes are the teleporter and the lift, Source davenportz).
- `INTER-LIFT-04` Objects ride lifts: grenades thrown into some lifts ride up (Halo 2 Lockout, Verify per map); bots may use this to clear a lift exit camper.

### 1.3 Teleporters

**Rule:** CE (Blood Gulch, Hang 'Em High, Damnation, Chill Out, Boarding Action, Rat Race, Sidewinder, Danger Canyon, Chiron TL-34, Derelict, Wizard), Halo 2 (Ascension, Warlock, Beaver Creek, Gemini, Relic's switch-activated two-way teleporter, Coagulation Verify), H2A Warlord (two-way teleporters between corners), Remnant (switch-activated), Halo 3 Forge receivers/senders, Valhalla's man cannons replaced its teleporters. Teleporters are instant, two-way or one-way, and the exit is a camp point.

**Bot rules**
- `INTER-TELE-01` Instant edge; exit camping is the standard counter. Same no-ride rule as lifts when the exit is hot.
- `INTER-TELE-02` Objectives through teleporters: CE Blood Gulch `CE-CTF-02` (park a vehicle at the teleporter, run the flag through, drive away). The pack stores vehicle-parkable nodes beside each teleporter exit.
- `INTER-TELE-03` Two-way teleporters are retreat routes: a losing fight at one end relocates instantly, so a bot that goes through turns and pre-aims the teleporter it came out of (the chaser may follow).
- `INTER-TELE-04` Switch-activated teleporters (Relic/Remnant): the switch in the Bowl opens a two-way teleporter to Teleport Ridge for both teams (Halopedia Remnant). Activating it opens the enemy's shortcut into our base too; the objective brain activates it only when we are attacking (One Flag/One Bomb offense) and posts a guard on our side's exit when it is open.

### 1.4 Switch-operated gates, doors, and shutters (open-only or toggle)

**Rule:** Zanzibar/Last Resort/Stonetown: a gate at the base, opened by a switch that either team can open but not close; vehicles drive through the open gate directly into the base (Halopedia Zanzibar). Stonetown moved the switch above the gate so it must be **shot** to activate; a generator inside the power plant, when shot, brings the large gate **down**; two walkways to the wheel start raised and drop when their red hinges are shot or meleed; blast covers on the Station 7 windows seal when their arms are shot (Halopedia Stonetown, Fandom Stonetown). High Ground: a main gate opened by a switch inside the base (Verify). Containment (Halo 2): base doors on switches (Verify). Standoff: switch-operated doors and windows (Fandom Standoff, as cited in the objective file). Longshore: a switch-operated shutter (Verify).

**Bot rules**
- `INTER-GATE-01` A closed gate is a wall in the pathfinder; an open gate is a vehicle lane. The objective brain tracks the gate's state as part of `objective.state`.
- `INTER-GATE-02` Attackers open, defenders do not. In One Flag/One Bomb on Zanzibar-type maps, the attacking team's first job is the switch (one bot assigned `GATE_OPENER`), because the open gate lets the Warthog carry the runner into the base (`CTF-ONE-05`). Defenders never touch an open-only switch and stand on it to block attackers from reaching it.
- `INTER-GATE-03` Shoot-switches (Stonetown): any bot with line of sight can open from range; the opener does not need to approach. The defending team's ANCHOR watches the switch and kills anyone aiming at it.
- `INTER-GATE-04` Close-switches (Stonetown generator brings the gate down): defenders shoot the generator when an enemy vehicle commits to the gate lane, timing the drop to trap or crush the vehicle (Verify whether the gate damages vehicles).
- `INTER-GATE-05` Walkway hinges and blast covers (Stonetown): attackers drop the walkways to reach the wheel/sword faster; defenders seal the blast covers to deny long sightlines into the plant before a push. Both are single-shot actions; the pack stores who benefits.
- `INTER-GATE-06` Toggle doors (Standoff): a defender closes doors behind a retreating carrier; an attacker opens the door and throws a grenade through before entering.

### 1.5 Moving hazards: trains, wheels, rotating structures

**Rule:** Terminal (Halo 2, MCC-exclusive map pack): a train crosses the map and kills anything on the tracks; it is the map's top killer (Collider). Zanzibar/Last Resort/Stonetown: the wheel spins; players can ride a spoke to the top to get the Energy Sword in the center niche (Halo 2) or the power-up in the hub (Last Resort, Verify item), and can fall or be crushed (Halopedia Zanzibar). Colossus/Elongation: conveyor belts move players and objects (Verify).

**Bot rules**
- `INTER-MOVE-01` Train: the tracks are a timed kill volume. The pack stores the train's cycle; the pathfinder blocks track nodes for 3 s before and during each pass; the coach callout "train" triggers an immediate clear of the tracks. Bots bait enemies onto the tracks by crossing just ahead of the train (Legendary only).
- `INTER-MOVE-02` Wheel: riding the spoke is a timed path edge (`entry_window`, `ride_time`); only a bot with no enemy sightline on the wheel takes it; the sword/power-up in the hub is a power item in the pack with a `risk` flag so the objective brain sends the rusher personality.
- `INTER-MOVE-03` Conveyors: movement vectors are added to the bot's velocity in the pathfinder; grenades roll along them (bots throw grenades upstream of a camper).

### 1.6 Destructible hazards and falling objects

**Rule:** Lockdown: three ice stalactites (above the BR tower, above top-center's glass skylight, above the ramp behind the sniper tower) can be shot to fall and damage or kill players below; the center glass takes significant damage to break but the stalactite breaks it instantly, and the glass regenerates (Halopedia Lockdown, Fandom, Halo Esports Wiki). Waterworks (Halo 2): falling stalactites in the center (Verify). Sandtrap: mines at the map's outer edges that destroy vehicles (Verify). Avalanche: none. Reach Forge/Halo 4: none native.

**Bot rules**
- `INTER-FALL-01` Each falling object is a one-shot area attack with a known footprint. The pack stores `footprint_node` and `shooter_positions`. The objective brain adds a target weight 2.0 on any enemy standing in a footprint while a stalactite is intact, and the combat brain shoots the stalactite instead of the enemy when the enemy is inside the footprint (a guaranteed kill or forced move beats a duel).
- `INTER-FALL-02` Counter: bots do not hold a footprint node while its stalactite is intact (hold-spot scorer penalty -3); after it has fallen, the node is safe until the object regenerates (Lockdown glass regenerates; stalactites do not, Verify).
- `INTER-FALL-03` Break-the-glass: Lockdown's center glass can be broken to drop a player below; the combat brain treats broken glass as a drop edge and intact glass as a floor.
- `INTER-FALL-04` Mines (Sandtrap): vehicle lanes exclude the mined edges; a Legendary driver can use the mined edge as a trap by baiting a chaser across it.

### 1.7 Shield doors, energy bridges, and LOS blockers

**Rule:** Shield doors (Snowbound, Epitaph, Halo 3 Forge, Reach Forge): block projectiles and grenades, let players and vehicles through, both ways. Narrows: an energy bridge under the main bridge (Halopedia). Zenith: a large energy shield in the center of the map, triggered by any of three switches on the outskirts; the shield can be activated repeatedly (achievement for three activations in one game) (Halopedia Zenith; Gamingbolt). Shrine: a device on each base's ceiling, when shot, releases a waterfall that blocks lines of sight through the base's front openings for 30 seconds (Fandom Shrine). Bloodline: a switch on each base sends out an EMP wave (Fandom Bloodline).

**Bot rules**
- `INTER-SHIELD-01` Shield doors are melee doors: a bot entering a shield door expects melee or a shotgun on the other side and leads with its own melee or a shotgun; grenades cannot go through, so clearing is by pushing or by waiting at the door. Vehicles pass; splatters through a shield door are legal.
- `INTER-SHIELD-02` Zenith center shield: the activating switch is a defensive tool. When our team holds the center (hill, ball, or just a setup), a bot activates the shield to block enemy fire into mid; when the enemy holds mid, we do not activate it (it protects them). The objective brain assigns `SHIELD_SWITCH` to the ROAMER when `we_hold_mid` is true. Counter: push through the shield in a group (it blocks shots, not bodies) with melee/shotgun, or wait for it to drop (duration Verify).
- `INTER-SHIELD-03` Shrine waterfall: shoot the ceiling device when the enemy sniper or anchor holds a sightline into our base through the front openings; 30 s of blocked LOS is a free flag grab, bomb arm, or respawn regroup. The attacking team shoots the enemy's device to blind their base defenders during a push. The pack stores the two shooter positions and the 30 s cooldown (Verify cooldown).
- `INTER-SHIELD-04` Bloodline EMP switch: the base switch emits an EMP wave that disables vehicles near the base (Fandom). Defenders hit it when an enemy Warthog, Ghost, or Gungoose enters the base lane (stall, then board or kill the crew; vehicle file EMP rules); it also strips shields in range if it behaves like a Power Drain (Verify). Attackers never drive into a base whose switch is manned; the vehicle brain marks the base interior as `emp_zone` while the enemy holds the switch.
- `INTER-SHIELD-05` Energy bridge (Narrows underside): a crossing lane without cover; treat as a man cannon for ambush purposes (pre-aim the far end).

### 1.8 Low-gravity and vacuum zones

**Rule:** Reach: Anchor 9 has an exterior low-gravity section; Condemned has a low-gravity core; Zealot's upper "space" area is low gravity (Verify each). Halo 4: none in stock MP.

**Bot rules**
- `INTER-LOWG-01` Jump arcs are longer and floatier; the combat brain extends jump prediction time; grenades travel farther; Jetpack fuel goes further.
- `INTER-LOWG-02` Low-gravity areas are sniper lanes: floating targets are easy headshots; the objective brain gives these zones a `exposure` penalty of 0.6 and only crosses them to deny a power weapon that spawns there.

### 1.9 Vehicle-specific map features

**Rule:** Sandtrap: two Elephants (vehicle file). Avalanche: a large man cannon in front of each base that lands near the top of the base; Hornets and Ghosts near the teleporter (Cheat Happens; objective file). Valhalla: Spartan Laser at the central hill; two cannons per base, one to near-mid, one to a sniper spot (StrategyWiki Halo 3/Maps). Coagulation: each base has an underground level with a Banshee (Wikipedia Blood Gulch). Bloodline: UNSC vehicle access bridges added (Fandom).

**Bot rules**
- `INTER-VEH-01` Vehicle spawn nodes and their timers are in the pack; `PW-01` style pre-positioning applies to vehicles (be at the Banshee/Hornet 5 s before it spawns; Avalanche's Hornet is "taken almost instantly").
- `INTER-VEH-02` Ram-safe roads and blind corners per lane feed the vehicle brain's ram geometry and the Chopper lane play.
- `INTER-VEH-03` Base interiors with vehicle access (open gates, Bloodline bridges) are `vehicle_ok` only while the gate/bridge state allows.

---

## Part 2. Map control, power positions, hold spots, and callouts

### 2.1 Principles (Source: Halo 3 MLG guide, Bungie.net MLG thread, Team Liquid)

- The team that controls the map's power position (most sightlines, best cover, access to the next position) wins at even skill; on small maps like Guardian, holding one base is enough; on Construct, hold one side (Bungie.net MLG thread).
- Map control is exerted through **spawn pressure**: spawns are chosen by the highest-weighted location, which moves away from enemy line of sight; a team that covers the enemy's spawn zones forces cross-map spawns and a fight through fire to reach the objective (Team Liquid).
- Power weapon control is timed; MLG settings put OS and camo on 2-minute post-pickup timers and rockets on a 3-minute game-clock timer in Halo 3 (Halo 3 MLG guide); MCC Halo 3 weapon timers start 2 s after the weapon is disturbed (Steam Halo 3 spawn guide). Each pack records `timer_rule` per item.
- A sniper holds a lane that covers the enemy's spawn exits while the team takes objectives (Team Liquid).

### 2.2 Computing power positions, hold spots, and spawn zones (Proposed)

- `MAP-06` **Power position score** = sightlines onto high-traffic nodes (3) + cover from the enemy's power position (2) + access to the next position without crossing open ground (2) + proximity to a power weapon or power-up spawn (1) - exposure to vehicle lanes (2 if any vehicle can reach it). Top three per map per mode are stored; the objective brain picks among them live.
- `MAP-07` **Hold spot score** (Oddball, Juggernaut, last-man, Infection) as `ODD-CORE-01`: single approach (3), cover from long sightlines (2), elevation (2), escape route within 20 m (2), distance from enemy spawn (1); minus 3 if under an intact stalactite or on a train track.
- `MAP-08` **Spawn zones** are the map's spawn point clusters per team; the pack stores which enemy positions push spawns to which zones so `SP-01` and `PLAY-SPAWN-TRAP` have data.
- `MAP-09` **Lanes** are named node sequences with `vehicle_ok`, `carrier_safe_if`, and `blind_corners`. Every CTF return route, Oddball rotation, and Chopper road is a lane.
- `MAP-10` **Hot zones** per mode: nodes the enemy must cross for that mode's objective; the ANCHOR's default sightline covers the hottest.

### 2.3 Callout grammar (Proposed, built from community conventions)

Community callouts are mostly of the form **[team color or side] + [structure] + [level/side]**: "Blue Base," "Top Mid," "Bottom Blue," "Sniper Tower," "Yellow Lift," "Elbow," "BR Tower," "Long Hall," "Short Hall," "Green Box," "Training," "Shotgun," "Rockets," "S3" (Halo 3 MLG guide and Halopedia map pages). Rules for the pack and the coach:

- `CALL-01` Every node has one canonical callout and up to three aliases (`callout_aliases`). Weapon-named nodes keep the weapon name even after Bungie moved the weapon (MLG kept "Long Hall where rockets used to spawn"); the pack notes what actually spawns there now.
- `CALL-02` Enemy callouts carry four fields: **where** (node callout), **what** (count, weapon, vehicle), **health** ("one shot," "no shields," "overshield"), **movement** ("pushing Top Mid," "going Snipe"). Bots broadcast all four when their tier allows (Legendary all, Heroic where/what/health, Normal where/what, Easy none; addendum tiers).
- `CALL-03` Self callouts: "getting double-teamed Top Mid," "carrier at Low Bridge." These feed the objective brain's role reassignment.
- `CALL-04` Predicted spawns: "they'll spawn Green Box" after a kill near the opposite side (Legendary only).
- `CALL-05` Interactable callouts are verbs: "gate open," "gate dropping," "shield up mid," "waterfall blue," "train," "stalactite BR tower," "cannon incoming," "lift coming." Each has a fixed string in the pack so the coach and bots match exactly.
- `CALL-06` Timer callouts: "rockets 30," "OS up," "camo in 10," "Banshee 20," "Hornet up" (integer seconds or "up").

---

## Part 3. Coach map command set (optional Ollama layer)

The coach (addendum file Part 4) receives the map's knowledge pack summary in its snapshot and may issue these commands in its advice JSON. All are validated against the pack (node and lane names must exist; interactable IDs must exist and be usable by the issuing team; cooldowns respected) and expire with the advice TTL. The deterministic brains do all of this without the coach; the coach only sequences and times it.

| Command | Fields | What the objective brain does with it | Hard limits |
|---|---|---|---|
| `MCMD-GO` | `bot`, `node`, `stance` | sets `goal` to the node with HOLD/PUSH/FLANK/CAMP | carriers only to carrier-safe nodes; never into an `emp_zone` or an intact stalactite footprint |
| `MCMD-HOLD` | `bots[]`, `power_position` | assigns ANCHOR/RING to the position's stored sightline set | one SCORER rule in KOTH still applies |
| `MCMD-LANE` | `bot`, `lane` | sets the bot's route (carrier return, vehicle road, rotation) | lane must be `vehicle_ok` for vehicles; `carrier_safe_if` must evaluate true for carriers |
| `MCMD-ROTATE` | `bots[]`, `from_node`, `to_node`, `via_lane` | a timed cross-map rotation (`PLAY-CROSSMAP`) | none beyond lane validation |
| `MCMD-TRIGGER` | `bot`, `interactable`, `when` (`now`, `on_enemy_commit`, `on_push`, `at_t_minus:N`) | fires a switch, shoots a stalactite/device/hinge, opens or drops a gate, activates the Zenith shield or Shrine waterfall or Bloodline EMP, or activates the Relic teleporter | respects `who` (one team only), `cooldown`, and the side rules in Part 1 (defenders never open open-only gates; never activate Zenith's shield when the enemy holds mid) |
| `MCMD-AVOID` | `nodes[]` or `lanes[]`, `ttl` | adds a pathfinding cost (hot landing, train tracks, mined edge, enemy sniper lane) | none |
| `MCMD-WATCH` | `bot`, `node` (a cannon landing, lift exit, teleporter exit, gate, switch) | pre-aim assignment; the combat brain gets predicted-arrival events | none |
| `MCMD-TIMER` | `item`, `node`, `bot`, `arrive_early` | pre-position for a weapon, power-up, or vehicle spawn (`PW-01`, `INTER-VEH-01`) | `arrive_early` capped by tier |
| `MCMD-CALL` | `text` | injects a callout into `callouts_in` using the pack's fixed strings | must parse to a node, timer, or interactable string |
| `MCMD-DENY` | `node` | hold a power weapon/power-up spawn to deny it (`EQP-03`, `PLAY-TIMER-DENY`) | none |
| `MCMD-BAIT` | `bot`, `node`, `interactable` | stand where an enemy will chase onto a hazard (train track, mined edge, stalactite footprint, Armor Lock lane) | Legendary only; carriers never |

**Snapshot additions for the coach (per map):** `map.power_positions` (callouts + which team holds each), `map.interactables` (id, callout, state, cooldown, usable_by_us), `map.hot_nodes` (where enemies were seen in the last 10 s), `map.timers`, `map.gate_states`, `map.hazard_cycle` (train ETA), `map.lanes_blocked`.

**Coach system-prompt addition (paste after the addendum's prompt):**
```
You also receive the map's callout list, power positions, lanes, and interactables with their current state.
Use only those names. Prefer MCMD-TRIGGER on an interactable when it changes a fight more than a kill would:
drop a Lockdown stalactite on an entrenched enemy, blind an enemy base with the Shrine waterfall before a push,
raise the Zenith shield only when we hold mid, open the Zanzibar/Stonetown gate only when we are attacking,
EMP the Bloodline base only when an enemy vehicle commits, clear the Terminal tracks when the train is due.
Call man cannon and lift exits with MCMD-WATCH before any enemy push. Keep callouts in the exact strings given.
```

### 3.1 Worked example: Narrows, Multi Flag, Heroic coach

Snapshot excerpt: `score 1-1, time 6:40 left, our flag home, their flag home, enemy seen Top Mid (2) and Yellow Top (1), rockets up in 25, blue cannon landing (Yellow Top) hot`.

Coach advice:
```json
{"ttl": 20, "posture": "BALANCED", "play": "PLAY-OUTSKIRTS-RUN",
 "roles": {"bot1": "RUNNER", "bot2": "ESCORT", "bot3": "ESCORT", "bot4": "ANCHOR"},
 "map": [
   {"cmd": "MCMD-TIMER", "item": "rocket_launcher", "node": "bottom_mid", "bot": "bot3", "arrive_early": 5},
   {"cmd": "MCMD-LANE", "bot": "bot1", "lane": "bottom_bridge"},
   {"cmd": "MCMD-WATCH", "bot": "bot4", "node": "yellow_cannon_landing"},
   {"cmd": "MCMD-AVOID", "lanes": ["cannon_blue_to_yellow"], "ttl": 20},
   {"cmd": "MCMD-CALL", "text": "rockets 25"}
 ],
 "note": "they sit top; take rockets low, run the flag bottom, anchor watches their cannon"}
```
The objective brain validates each command against the Narrows pack, applies them, and the runner goes low while bot3 arrives at rockets 5 s early.

---

## Part 4. Per-game map entries

Each game has a roster table (layout, size, best modes, interactables, vehicles) and detailed entries for the maps that carry the most play or the most interactables. Detailed entries give: power positions, hold spots, lanes, spawn pressure, key timers where sourced, mode notes, interactable rules, and plays. Entries marked Verify for a feature should be checked in MCC. Maps not given a detailed entry still get a pack built from the schema in Part 0 using the roster notes.

**MCC-era additions covered in this part (Rule: Giant Bomb MCC summary, Halo Waypoint Season 6/8 posts, 343 June 2021 patch notes, Halopedia map file list):** Halo 3 gained Waterfall (Season 6, 2021), Edge (June 2021), and Icebox (Season 8, 2021), all ported from Halo Online; Halo 3: ODST Firefight gained per-wave customization with Sentinels and Flood (Season 8) and the Hornet on Lost Platoon; Halo: Reach's Forge palette gained the Sabre, Seraph, Falcon variants, Forklift, and Troop Hog (vehicle file); Halo 4 includes Forge Island. CE, Halo 2 Classic, H2A, and Halo 4 received no new multiplayer maps in MCC beyond their original base and DLC pools. If a later MCC update adds maps after October 2026, build their packs from the schema in Part 0.

### 4.1 Halo: Combat Evolved (MCC)

**Roster (Rule: all CE multiplayer maps are in MCC; PC maps Danger Canyon, Death Island, Gephyrophobia, Ice Fields, Infinity, Timberland included)**

| Map | Layout | Size / modes | Interactables | Vehicles | Notes |
|---|---|---|---|---|---|
| Blood Gulch | symmetric, two bases | large, CTF/Slayer/KOTH | teleporters (one per base, to the mid cliffs) | Warthog, Rocket Hog, Ghost, Banshee (PC/MCC), Scorpion | the reference CTF map; OS/camo mid on 3:00 timers (Halo 1 Guide) |
| Battle Creek | symmetric, two bases | small, CTF/Slayer | teleporters, ladders | none | sniper on top of base |
| Chill Out | asymmetric | small, FFA/Slayer | teleporters (multiple), ladders | none | power-ups on 2:00 (Halo 1 Guide) |
| Chiron TL-34 | teleporter maze | small, FFA | teleporters everywhere | none | radar is useless; pre-aim exits |
| Damnation | asymmetric, vertical | medium, Slayer/CTF | teleporters, ladders, lifts (Verify) | none | rockets and camo on the upper levels (Verify) |
| Derelict | symmetric, vertical | small, FFA | teleporters/gravity lifts (Verify) | none | |
| Hang 'Em High | asymmetric, open | medium, CTF/Slayer | teleporters (base to base, Verify), ladders | none | top-mid power-up on 3:00 (Halo 1 Guide); sniper lanes everywhere |
| Longest | symmetric corridor | small, Slayer | none | none | two long hallways with side rooms |
| Prisoner | symmetric, vertical | small, FFA | ladders | none | top floor controls |
| Rat Race | asymmetric loop | small, FFA | teleporter | none | power-ups on 1:30 (Halo 1 Guide) |
| Sidewinder | symmetric canyon | large, CTF | teleporters per base | Warthog, Ghost, Banshee (Verify), Scorpion | ice; remade as Avalanche |
| Wizard | rotational symmetric | small, FFA | teleporters/lifts (Verify) | none | remade as Warlock/Warlord |
| Boarding Action | two ships | medium, CTF/Slayer | teleporters between ships | none | sniper duels across the gap |
| Danger Canyon | symmetric canyon | large, CTF | teleporters | Warthog, Rocket Hog, Ghost, Banshee, Scorpion | bottom-mid power-up on 3:00 |
| Death Island | symmetric island | large, CTF | teleporters (Verify) | Warthog, Ghost, Banshee, Scorpion | water kills; Banshee dominant |
| Gephyrophobia | symmetric bridge | large, CTF | none | Warthog, Ghost, Banshee | one long bridge with upper/lower decks |
| Ice Fields | symmetric | large, CTF | teleporters | Warthog, Ghost, Banshee, Scorpion | bottom-mid power-up on 3:00 |
| Infinity | symmetric | huge, CTF | teleporters (Verify) | all CE vehicles | longest CE map |
| Timberland | symmetric forest | large, CTF | teleporters (Verify) | Warthog, Ghost, Banshee | |

**Blood Gulch (detailed)**
- Power positions: top of each base (sniper over the field); the mid cliffs by the teleporter exits; the rock outcrops on each side of mid.
- Hold spots: base interior lower floor (Oddball), teleporter alcoves.
- Lanes: `left_wall`, `right_wall`, `center_field` (open; vehicle lane), `teleporter_hop` (base to mid cliff).
- Spawn pressure: kills near a base push the enemy to spawn in the far caves or behind the base; a Banshee over the base forces cross-map spawns.
- Timers: mid OS/camo 3:00 (Halo 1 Guide); weapons default 1:00 (verify per playlist).
- CTF: `CE-CTF-01` to `-05` (enter-grab-leave in a hog, teleporter park, support circle, gunner-through-wall, solo grab). Interactable rule: `INTER-TELE-02`.
- KOTH: hill usually mid; `CE-KOTH-01` to `-04`; a Scorpion parked on the hill edge blocks the field approach.
- Plays: `CE-BG-PLAY-01` Banshee air superiority first (the only aircraft, no boarding, 45-s camo pilot is nearly unkillable); `CE-BG-PLAY-02` Warthog teleporter shuttle (hog parked at the teleporter exit while the runner teleports with the flag).

**Hang 'Em High (detailed)**
- Power positions: the raised "Tombstone" platform and the sniper ledge over mid; the base roofs.
- Hold spots: inside the base pillars (Oddball); the lower tunnels.
- Lanes: top catwalks (exposed), floor (fast, exposed to everything), tunnels (safe, slow).
- Timers: top-mid power-up 3:00 (Halo 1 Guide).
- Plays: `CE-HEH-PLAY-01` rockets first, then the top platform; `CE-HEH-PLAY-02` CTF runner uses the tunnels, escorts hold the catwalks.

### 4.2 Halo 2 (MCC)

**Roster (Rule: Halo 2 launch maps, Multiplayer Map Pack, Maptacular, Killtacular, and Blastacular packs plus Vista-only maps are in MCC; Relic and Terminal are MCC-exclusive to the Maptacular pack)**

| Map | Layout | Size / modes | Interactables | Vehicles | Notes |
|---|---|---|---|---|---|
| Lockout | asymmetric, catwalks | small, Slayer/Oddball/KOTH/1 Flag | gravity lift, drop-downs | none | sniper tower and BR tower are the power positions; remade as Blackout and Lockdown |
| Ascension | asymmetric island | medium, Slayer/CTF/Oddball | gravity lift, teleporter, satellite dish | Banshee | Oddball hide spot with two escapes (teleporter, lift) (davenportz) |
| Midship | symmetric, two levels | small, Slayer/CTF | none | none | top-mid "carbine" and the pink/blue towers; remade as Heretic |
| Ivory Tower | asymmetric, vertical | small, Slayer/Oddball/KOTH | gravity lift, elevator (Verify) | none | remade as Reflection |
| Beaver Creek | symmetric | small, CTF/Slayer | teleporters | none | |
| Burial Mounds | asymmetric | medium, 1 Flag/Slayer | gravity lift (Verify) | Warthog, Ghost | |
| Coagulation | symmetric, two bases | large, CTF/Slayer | base lower level, teleporters (Verify) | Warthog, Gauss Hog, Ghost, Banshee (in each base's underground level), Scorpion (Verify), Spectre (Verify) | remade as Bloodline |
| Colossus | symmetric | medium, Slayer/CTF | conveyor belts (Verify) | none | |
| Foundation | symmetric | medium, Slayer/CTF | none | none | |
| Headlong | asymmetric city | large, 1 Flag/Assault | cranes, lifts (Verify) | Warthog, Ghost, Banshee | remade as Breakneck |
| Zanzibar | asymmetric | large, 1 Flag/1 Bomb | gate switch (open-only, either team), the spinning wheel with the sword in its hub, base-room panel for the side gate | Warthog, Ghost | the series' interactable showcase (Halopedia) |
| Waterworks | symmetric cavern | large, CTF/Slayer | falling stalactites (Verify) | Warthog, Ghost, Wraith, Banshee (Verify) | |
| Backwash | symmetric swamp | small, Slayer | fog | none | radar matters |
| Containment | symmetric | large, CTF/Assault | base doors on switches (Verify) | Warthog, Ghost, Wraith, Scorpion, Banshee, Spectre (Verify) | |
| Elongation | symmetric | small, Slayer | conveyor belts (Verify) | none | |
| Gemini | symmetric | small, Slayer | teleporters (Verify) | none | |
| Relic | asymmetric | large, 1 Flag/1 Bomb | switch-activated two-way teleporter (Bowl to Teleport Ridge) | Warthog, Ghost, Banshee, Spectre (Verify) | remade as Remnant |
| Sanctuary | symmetric ruins | small, CTF/Slayer | none | none | remade as Shrine |
| Terminal | asymmetric station | large, 1 Flag/Assault | the train (kill hazard on the tracks) | Warthog, Ghost, Banshee (Verify), Scorpion (Verify) | |
| Turf | asymmetric streets | medium, Slayer/CTF | none | Warthog, Ghost | |
| Warlock | rotational symmetric | small, Slayer/CTF | teleporters, gravity lifts | none | remade as Warlord |
| Desolation | symmetric | small, Slayer | teleporters (Verify) | none | Derelict remake |
| Tombstone | asymmetric | medium, Slayer/CTF | teleporters (Verify) | none | Hang 'Em High remake |
| Uplift | symmetric | medium, Slayer/CTF | lifts (Verify) | Warthog (Verify) | Vista/MCC |
| District | asymmetric city | large, Slayer/CTF | none | Warthog, Ghost | Vista/MCC |

**Lockout (detailed)**
- Power positions: Sniper Tower (top), BR Tower, the "Elbow" walkway landing (Observation Platform in Lockdown), Library/Shotgun door. Source: Halo 2 tournament map notes (GameSpot/Halopedia Lockdown).
- Hold spots (Oddball): Library interior, bottom of the lift room, under Sniper Tower.
- Lanes: `lift_to_sniper` (gravity lift), `elbow` (long walkway, the map's most exposed route), `center_glass` (top center), `library_route` (bottom).
- Interactables: gravity lift (`INTER-LIFT-01..04`); Lockdown adds stalactites and breakable regenerating glass (`INTER-FALL-01..03`).
- Spawn pressure: a team holding Sniper and BR towers spawns the enemy at Library/bottom and holds them there.
- Plays: `H2-LOCK-PLAY-01` take Sniper and BR towers, hold the Elbow with a BR; `H2-LOCK-PLAY-02` Oddball in Library with the ring at the two doors; `H2A-LOCKDOWN-PLAY-01` shoot the BR tower stalactite when the enemy sets up there (`MCMD-TRIGGER` on_enemy_commit), `H2A-LOCKDOWN-PLAY-02` drop the top-center stalactite through the glass on a hill contest.

**Zanzibar (detailed)**
- Power positions: the base's second floor (flag room overlooks the yard), the sniper tower by the wheel, the beach cliff overlooking the gate, the camp (sea wall) on the attackers' side.
- Interactables: gate switch (open-only, either team; vehicles drive through into the base: `INTER-GATE-01/02`); the wheel (ride a spoke to the top; drop into the hub niche for the sword: `INTER-MOVE-02`); the side gate opened from the base room's second-floor panel.
- One Flag attacking: `CTF-ONE-01..06` plus: GATE_OPENER goes first; the Warthog drives through the open gate into the yard to draw fire (`CTF-ONE-05`); the runner takes the back route via the beach and the side ramp.
- One Flag defending: stand on the gate switch; snipe from the tower; a bot on the wheel bridge watches the sword.
- Plays: `H2-ZAN-PLAY-01` gate-and-hog siege; `H2-ZAN-PLAY-02` sword run (rusher rides the wheel for the sword at round start); `H2-ZAN-PLAY-03` beach flank for the flag with the yard as decoy.

**Terminal (detailed)**
- Power positions: the station's upper platforms over the tracks; the parking-garage roof (Verify names).
- Interactable: the train (`INTER-MOVE-01`): tracks are a timed kill volume; the pack stores the cycle; `MCMD-BAIT` is the Legendary trick of crossing just ahead of the train.
- One Flag/Assault: the carrier never uses the tracks as a route; escorts cross only on the coach/pack "train clear" window.

**Relic (detailed)**
- Interactable: the switch inside the Bowl activates a two-way teleporter to Teleport Ridge (`INTER-TELE-04`); attackers activate it to shortcut the main structure; defenders guard the ridge exit while it is open.
- One Flag attacking: `H2-REL-PLAY-01` teleporter switch first, then flag; One Flag defending: `H2-REL-PLAY-02` one bot on the switch room, one on the ridge exit.

**Ascension (detailed)**
- Power positions: the two towers (sniper tower, Banshee pad tower), the dish is avoided (Goomba Stomp: best avoided).
- Interactables: gravity lift, teleporter (Oddball escapes, davenportz).
- Plays: `H2-ASC-PLAY-01` Banshee first (only vehicle), tower hold; `H2-ASC-PLAY-02` Oddball in the lift room with the teleporter as escape.

### 4.3 Halo 2: Anniversary multiplayer (MCC)

**Roster (Rule: Halopedia/Fandom; HCS used Warlord, Shrine, and Lockdown)**

| Map | Remake of | Layout | Modes | Dynamic elements (Rule) | Vehicles |
|---|---|---|---|---|---|
| Lockdown | Lockout | small arena | Slayer/Oddball/KOTH/1 Flag | three stalactites (BR tower, top-center glass, sniper-tower ramp); breakable regenerating center glass; cover added to the Elbow | none |
| Zenith | Ascension | medium | Slayer/CTF/Oddball | large center energy shield triggered by any of three outskirt switches (repeatable) | Banshee (Verify) |
| Bloodline | Coagulation | large two-base | CTF/Slayer/Gungoose CTF | base switch emits an EMP wave; UNSC vehicle access bridges; single-level bases | Warthog, Gauss Hog, Ghost, Banshee, Scorpion, Gungoose (Verify set) |
| Stonetown | Zanzibar | large asymmetric | 1 Flag/1 Bomb/Slayer | gate switch moved above the gate (must be shot); generator in the plant drops the gate when shot; two wheel walkways drop when hinges are shot/meleed; Station 7 blast covers seal when their arms are shot | Warthog, Ghost (Verify) |
| Shrine | Sanctuary | small symmetric | Slayer/CTF/KOTH/Oddball | ceiling device per base releases a 30-s waterfall blocking the base's front LOS; grav lift in the shotgun tunnel to the room above | none |
| Warlord | Warlock | small rotational | Slayer/CTF/Oddball | per-corner gravity lifts, two-way teleporters between corners | none |
| Remnant | Relic | large asymmetric | 1 Flag/1 Bomb/Slayer/Race | switch in the Bowl opens a two-way teleporter to Teleport Ridge | Warthog, Ghost, Banshee (Verify) |
| Skyward | Forge canvas (Zenith skybox) | any | Forge | scripted switches (H2A Forge scripting) | Forge |
| Awash, Nebula | Forge canvases | any | Forge | scripted switches | Forge |

**Zenith (detailed)**
- Power positions: the two towers (as Ascension); mid is a trap unless the shield is up for our side.
- Interactable: center shield (`INTER-SHIELD-02`): three switches on the outskirts; activate only when we hold mid (hill on mid, our ball carrier in mid, our setup in mid). Achievement text confirms repeatable activation; duration Verify.
- Plays: `H2A-ZEN-PLAY-01` hold mid behind the shield in KOTH (SCORER inside, RING on the towers, ROAMER on the nearest switch); `H2A-ZEN-PLAY-02` CTF runner crosses mid under the shield; `H2A-ZEN-PLAY-03` when the enemy holds mid, do NOT raise the shield; push through with melee/shotgun (shield blocks shots, not bodies) or wait it out.

**Stonetown (detailed)**
- Interactables as the roster. Attacking: `GATE_OPENER` shoots the switch above the gate from range (`INTER-GATE-03`); drop the wheel walkways for the sword; the Warthog enters through the open gate. Defending: shoot the generator to drop the gate when an enemy vehicle commits (`INTER-GATE-04`); seal the blast covers before the enemy's push to deny the plant sightlines (`INTER-GATE-05`); stand on nothing (the switch is now shot, not pressed, so defenders snipe anyone aiming at it instead).
- Plays: `H2A-STONE-PLAY-01` range-open the gate, hog siege; `H2A-STONE-PLAY-02` generator drop as the hog enters.

**Shrine (detailed)**
- Power positions: the two shrines' upper rooms, "Blue/Red Sniper" ledges, the rocks between shrines.
- Interactable: the ceiling device (`INTER-SHIELD-03`). Attack: shoot the enemy base's device to blind their defenders for 30 s, then push; defense: shoot our own device when the enemy sniper is holding a line into our base. The grav lift in the shotgun tunnel is a `INTER-LIFT` edge to the room above (exit camp point).
- Plays: `H2A-SHRINE-PLAY-01` waterfall-then-push on One Flag/Neutral Bomb; `H2A-SHRINE-PLAY-02` waterfall-defense on respawn regroup.

**Bloodline (detailed)**
- Interactable: base EMP switch (`INTER-SHIELD-04`): defenders fire it when an enemy vehicle enters the base; attackers never drive into a base whose switch is manned; after the EMP, boarders take the stalled vehicle. Gungoose CTF uses `CTF-VEH-01..03`.
- Plays: `H2A-BLOOD-PLAY-01` EMP trap (bait the enemy hog into the base with a "weak" defender, fire the switch, board); `H2A-BLOOD-PLAY-02` Gungoose CTF lane control with the escort Gungoose ramming head-on.

**Warlord (detailed)**
- Rotational symmetry: four corners, each with a lift to its raised platform, two-way teleporters between corners (Halopedia). Power positions: the corner platforms; the spire top (Verify reachable). Plays: `H2A-WARLORD-PLAY-01` hold two adjacent corners (half the map) with teleporter exits watched (`INTER-TELE-01`); `H2A-WARLORD-PLAY-02` CTF: teleporter flag run (grab, teleport to the diagonal corner, run the short way home) only when the exit is held by an escort.

### 4.4 Halo 3 (MCC)

**Roster (Rule: all Halo 3 maps including Heroic, Legendary, Mythic, and Mythic II packs plus Forge canvases and MLG variants are in MCC; the Steam Halo 3 spawn guide covers 130 maps)**

| Map | Layout | Size / modes | Interactables | Vehicles | Power positions (Source where cited) |
|---|---|---|---|---|---|
| Valhalla | semi-symmetric canyon | large, CTF/Slayer/Assault | two man cannons per base (center one to near-mid where the Laser is; side one to a sniper spot), caves | Warthog, Gauss (heavy), Mongoose, Ghost, Banshee, Wraith (heavy, Verify) | Laser hill, base tops, the caves (StrategyWiki) |
| Narrows | symmetric bridge | medium, CTF/Slayer/KOTH | man cannon per base (fixed trajectory), energy bridge underside, two bridge levels | none | Top Mid; each base's low point (OS at Blue low; Yellow had camo, replaced by OS) |
| The Pit | symmetric | medium, Slayer/CTF/Oddball/KOTH | none | none | Sniper towers ("S3"), Green Box, Training, Long Hall, Short Hall (MLG guide) |
| Guardian | asymmetric, multi-level | small, Slayer/Oddball/KOTH | lifts and man cannons (bottom blue to sniper tower, to center, yellow lift to camo), catwalks | none | Sniper Tower (OS spawns there), Blue Room, Yellow Lift/camo, Gold Lift, Elbow (Halopedia Guardian) |
| Construct | vertical | medium, Slayer/CTF | three gravity lifts (any floor to top) | none | Top floor; hold one side (MLG thread) |
| Sandtrap | symmetric desert | huge, BTB CTF/Assault | mines at the edges (Verify), Elephants (mobile bases), man cannons (Verify) | Warthog, Gauss, Mongoose, Ghost, Chopper, Banshee, Wraith, Scorpion (Heavy), Elephant x2 | the temple tops; the Elephant deck |
| Last Resort | asymmetric | large, 1 Flag/1 Bomb | gate switch (as Zanzibar), the wheel (power-up/camo in the hub, Verify), base room panel | Warthog, Mongoose, Ghost | the base's second floor, the camp, the sea wall |
| High Ground | asymmetric | medium, 1 Flag/1 Bomb | main gate switch inside the base (Verify), bunker tunnels | Mongoose, Warthog (Verify) | the base upper deck, the pipe/tunnel exits |
| Snowbound | symmetric | small, Slayer | shield doors on the base entrances, underground tunnel, turrets | Ghost | the hill between bases; tunnel exits |
| Epitaph | symmetric | small, Slayer | shield doors, lifts (Verify) | none | top floor |
| Isolation | asymmetric | medium, Slayer/CTF | Flood tunnels below | none | the hill, the tunnel exits |
| Standoff | symmetric | medium, CTF/Slayer | switch-operated doors and windows in the bases (Fandom) | Warthog, Mongoose | the base roofs, the rock in the middle, the outskirts route (Halopedia Standoff CTF) |
| Rat's Nest | asymmetric loop | large, CTF/Slayer | none | Warthog, Mongoose, Ghost | the interior catwalks; the vehicle loop is a ram lane |
| Foundry | Forge canvas | any | Forge | Forge | |
| Avalanche | symmetric canyon | huge, BTB CTF/Assault | a large man cannon in front of each base to the base top; three small cannons per side (back-corner ones go to back-center); teleporter area | Warthog, Gauss, Mongoose, Ghost, Hornet (near the teleporter, "taken instantly"), Scorpion, Wraith (heavy), Chopper (heavy) | base tops; the ice cave; the hornet pad |
| Blackout | Lockout remake | small | gravity lift | none | as Lockout |
| Ghost Town | asymmetric | medium, Slayer/Oddball | none | none | the tower; the pipes |
| Cold Storage | Chill Out remake | small | teleporters, Flood lift (Verify) | none | as Chill Out |
| Assembly | symmetric | small, Slayer/CTF | lifts (Verify) | none | the center platform |
| Orbital | symmetric | medium, Slayer/CTF | man cannons (Verify) | none | the long hall |
| Sandbox | Forge canvas (ground, sky bubble, crypt) | any | man cannons, grav lifts, Forge | Forge; Hornet as a Forge object | |
| Citadel | symmetric | small, Slayer | none | none | top walkways |
| Heretic | Midship remake | small | none | none | top-mid |
| Longshore | asymmetric docks | medium, 1 Flag/Slayer | switch-operated shutter (Verify), cranes | Mongoose, Warthog (Verify) | the warehouse roof |
| MLG variants (Amplified, Assembly, Construct, Guardian, Heretic, Narrows, Onslaught, The Pit) | as base | 4v4 competitive | as base; weapons spawn in the air (timer starts on landing) | none | as base |
| **Waterfall** (MCC-exclusive, Season 6, from Halo Online) | symmetric Forerunner jungle with waterfalls | medium, Slayer/objective (4v4 to 6v6, Verify) | none confirmed (Verify) | none (Verify) | the upper waterfall platforms (Verify) |
| **Edge** (MCC-exclusive, June 2021, from Halo Online) | symmetric cliff-side with an "ancient database" interior (343 patch notes) | 4 to 12 players, supports all major Halo 3 variants (343) | none confirmed (Verify) | none (Verify) | the database interior; the cliff vista overlooks (Verify) |
| **Icebox** (MCC-exclusive, Season 8, from Halo Online) | asymmetric snowy city (Turf remake, Tyumen) | medium, Slayer/CTF/Oddball | none (Turf has none) | Warthog, Ghost (as Turf; Verify in Icebox) | as Turf: the overlooks on the main street, the back alleys |

**Not in stock MCC:** Diamondback, Lockout (Halo 3), Powerhouse, and Reactor are Halo Online maps available only through the Halo 3 Editing Kit (Halopedia map file list); do not build packs for them unless the mod ships them.

**Narrows (detailed)**
- Power positions: Top Mid (the center of the upper bridge: the map's single most important node); each base's "top" entrance; Bottom Mid for rockets (verify current rocket position in MCC playlists).
- Hold spots: each base's low point (lower than Low Bridge, Halopedia Narrows) for Oddball; the alcoves under the cannons.
- Lanes: `top_bridge`, `bottom_bridge`, `energy_bridge_underside`, `cannon_blue`, `cannon_yellow` (fixed trajectory, `INTER-CANNON-01`).
- Interactables: two man cannons (fixed trajectory; all of `INTER-CANNON-01..06`), energy bridge (`INTER-SHIELD-05`). Yellow's Power Drain sits in front of its cannon and Blue's Bubble Shield in front of its cannon (Halopedia): the drain is the Yellow team's anti-cannon tool (throw it into the cannon to land on a Blue camper or at a landing camper), the bubble is Blue's flag-grab tool.
- Timers: OS at each base low (post-pickup timer, 2:00 in MLG settings); rockets on the game clock.
- CTF: flags can be thrown through the cannons (`INTER-CANNON-03`); the runner goes Bottom Bridge when Top Mid is contested (`PLAY-OUTSKIRTS-RUN` equivalent is "go low"); escorts hold Top Mid or deny it with grenades.
- KOTH: hills alternate top and bottom; `KOTH-STATIC` with the ring on the two base tops; Crazy King rotations use the cannon only when its landing is clear.
- SWAT: cannons land players on the enemy's top level (Fandom); a Team SWAT push is two bots through both cannons at once while two hold mid.
- Plays: `H3-NAR-PLAY-01` Top Mid setup (two BRs on Top Mid, one low, one on rockets timer); `H3-NAR-PLAY-02` cannon ambush (ANCHOR pre-aims the enemy landing; grenades into their cannon when they commit); `H3-NAR-PLAY-03` flag-throw through our cannon with a catcher at our landing.

**Valhalla (detailed)**
- Power positions: the Laser hill (center), the base tops (sniper), the caves (BRs spawn in each), the turret rocks.
- Lanes: `river_mid` (vehicle lane, exposed), `cliff_sides` (foot), `center_cannon` (to near the Laser hill), `side_cannon` (to the sniper spot "almost no one uses" because snipers there die in under 30 s, StrategyWiki).
- Interactables: four man cannons (weight-based: vehicles fly lower; `INTER-CANNON-01`), caves.
- Vehicles: Warthog, Mongoose, Ghost, Banshee; Gauss and Wraith in Heavy variants (Verify). The Banshee decides Valhalla; `PLAY-AIR-DENIAL` is the opener for the team without it; the Laser is the Banshee counter and the first timer to track (`CTF-MULTI-18`, `EQ-DMG-01` if a Damage Boost exists in a variant).
- Spawn pressure: holding the enemy base's cannon landings and the river forces spawns into the caves; a sniper on our base top keeps them there.
- CTF: runner on foot through the cliff side opposite the enemy Banshee's patrol; escort hog on the river as a decoy; `INTER-CANNON-04` Power Drain in flight at the Laser hill when the enemy holds it (Halopedia tip).
- Plays: `H3-VAL-PLAY-01` Laser-and-Banshee opener (one bot cannons to the Laser with a Power Drain thrown in flight, one takes the Banshee, two hold base top); `H3-VAL-PLAY-02` cave flag run; `H3-VAL-PLAY-03` river hog decoy.

**The Pit (detailed)**
- Power positions: Sniper tower (S3), Green Box, the Training/Long Hall junction, the top of each base (MLG guide). Hold one side's Training-to-Green-Box line.
- Lanes: Long Hall (where rockets used to spawn, MLG callout), Short Hall (in front of the rocket spawn), Sword room route, the open courtyard (exposed to both towers).
- Timers (Halo 3 MLG settings): OS/custom and camo 2:00 after pickup; rockets 3:00 on the game clock; sniper 2:30; mauler 2:00 (MLG guide). MCC default playlists may differ; the pack stores both.
- Spawn pressure: rushing the enemy's Green Box kills their shotgun/long-hall spawns and their platform (MLG guide "aggressive rush").
- Plays: `H3-PIT-PLAY-01` Green Box rush (`PLAY-BREAKOUT` variant); `H3-PIT-PLAY-02` sniper-tower hold with Long Hall BR support; `H3-PIT-PLAY-03` CTF: flag out through Training while the escort holds the courtyard wall.

**Guardian (detailed)**
- Power positions: Sniper Tower (OS), Blue Room, Gold/Yellow Lift (camo), the Elbow catwalk; it is small enough that holding one base is map control (MLG thread).
- Interactables: man cannons (bottom blue to Sniper Tower; another to the center platform; one to yellow lift's camo) and the lifts; "know where each man cannon leads" (Halopedia); do not use the bottom-blue cannon at Team Slayer start because the enemy holds the OS at Sniper Tower (Halopedia).
- Plays: `H3-GUARD-PLAY-01` Sniper Tower OS at start via the inside route, not the cannon; `H3-GUARD-PLAY-02` Oddball in Blue Room with the ring on the Elbow and Gold Lift exit (`INTER-LIFT-02` grenade on the exit); `H3-GUARD-PLAY-03` camo cannon run (yellow lift camo, then cannon to center for a sword or ball play).

**Sandtrap (detailed)**
- Power positions: the temple tops (snipers, Laser), the Elephant decks.
- Interactables: two Elephants (vehicle file: invincible mobile bases; `H3-DEF-04`, `H3-ASS-05/08/09`), mines at the outer edges (`INTER-FALL-04`, Verify), vehicle spawns: Chopper, Ghost, Warthog, Gauss, Mongoose, Banshee, Wraith, Scorpion (Heavy, Verify).
- Plays: `H3-SAND-PLAY-01` Elephant bomb run; `H3-SAND-PLAY-02` Chopper road block on the enemy's temple approach (`PLAY-CHOPPER-LANE`); `H3-SAND-PLAY-03` Banshee counter: Laser on the temple top.

**Avalanche (detailed)**
- Interactables: the big cannon in front of each base lands near the base top (fast flag exits); back-corner small cannons go to back-center; the Hornet by the teleporter is the first timer to track (objective file: taken instantly by a player with a passenger).
- Plays: `H3-AVA-PLAY-01` Hornet steal at spawn, then the ice-cave flag route; `H3-AVA-PLAY-02` base-cannon flag exit (carrier rides the big cannon only when the base top is held by an escort).

**Last Resort and High Ground (detailed)**
- Last Resort: Zanzibar rules (`H2-ZAN-PLAY-01..03`); the wheel hub item is a power-up (Verify which); gate switch open-only.
- High Ground: the main gate switch is inside the base (Verify); attackers send one bot through the bunker tunnel to the switch while the others push the beach; defenders hold the switch room and the upper deck; `CTF-ONE` and `ASS-ONE` rules.

**Standoff (detailed)**
- Interactables: switch-operated doors and windows (Fandom); `INTER-GATE-06` (close doors behind a retreating carrier; grenade through an opened door). Outskirts route and back door for the carrier (`H3-CTF-05/08`); Warthog havoc decoy (`H3-CTF-03`); Mongoose for the carrier on the outer route.

### 4.5 Halo 3: ODST (MCC)

Firefight only (MCC ODST has no competitive multiplayer). Map entries feed the Firefight brain (`FF-POS-01`).

| Map | Hold positions (Source: Steam ODST Firefight guide, GameFAQs) | Vehicles and drops | Notes |
|---|---|---|---|
| Lost Platoon | the roofed main building (mortar-immune), the garage | Hornet (MCC addition), Choppers, Warthogs, Ghosts dropped by Phantoms | the best vehicle Firefight map; hijacked Chopper is the lane tool |
| Crater | the ramp interior, the upper walkways | Ghosts dropped (Verify) | Night version adds VISR play |
| Rally Point | the back corridors | none | corner holds |
| Security Zone | the elevated platform | none | |
| Alpha Site | the courtyard arches | none | |
| Windward | the rooftop interiors | Banshee (Verify) | |
| Chasm Ten | the central ramp | none | |
| Last Exit | the stairwells (Splatter Spree achievement guide: hijack a Ghost) | Ghosts dropped | |
| Crater (Night), Rally Point (Night) (Verify the exact night set) | as the day versions | as the day versions | VISR outlines enemies; the FF brain lowers engagement range at night and relies on VISR callouts |

MCC Season 8 added per-wave customization to ODST Firefight with Sentinels and Flood as enemy types; the FF brain's enemy procedures (`FF-` rules) need Sentinel and Flood entries if your mod uses those waves (Sentinels: shoot the beam emitter, they are shield-only and die to plasma; Flood: headshots do nothing, shotgun and melee, kill the Carrier forms at range).

### 4.6 Halo: Reach (MCC)

**Roster (Rule: all Reach maps, Noble, Defiant, and Anniversary packs, plus Forge World variants and MCC Forge additions are in MCC)**

| Map | Layout | Size / modes | Interactables | Vehicles | Power positions |
|---|---|---|---|---|---|
| Sword Base | asymmetric, vertical | medium, Slayer/KOTH/Oddball | gravity lifts, elevator shaft (Verify) | none | the top of the lift, the bridge |
| Countdown | symmetric | small, Slayer/CTF | gravity lifts, the central shaft (Verify) | none | the top platforms |
| Reflection | Ivory Tower remake | small | gravity lift | none | the lift top, the window |
| Zealot | symmetric, two-level plus "space" | small, Slayer/Oddball/KOTH | the upper low-gravity space area (Verify) | none | the upper level; space is a sniper lane |
| Boardwalk | asymmetric | medium, Slayer/CTF | none | none | the boardwalk upper deck |
| Powerhouse | asymmetric | medium, Slayer/CTF/KOTH | none | Warthog (Verify) | the pump room roof, the bridge |
| Spire | asymmetric | huge, Invasion | the Spire's gravity lift to the top (Verify), the beach Pelican | Falcon, Warthog, Mongoose, Ghost, Banshee, Wraith, Revenant, Scorpion (by phase) | the Spire top; the beach |
| Boneyard | asymmetric | huge, Invasion | ship doors by phase (Verify) | Warthog, Ghost, Wraith, Scorpion, Banshee (by phase) | the ship interior |
| Hemorrhage | Blood Gulch remake (Forge World) | large, CTF/BTB | none; players can leave the canyon (Engadget) | Warthog, Gauss, Rocket Hog, Mongoose, Ghost, Banshee, Wraith, Scorpion, Revenant | base tops, the cliff above the caves |
| Asylum | Sanctuary remake (Forge World) | small | none | none | as Sanctuary |
| Pinnacle | Ascension remake (Forge World) | medium | gravity lift, teleporter (Verify) | Banshee (Verify) | the towers |
| The Cage | asymmetric (Forge World) | small | none | none | top platform |
| Paradiso | asymmetric island (Forge World) | large, BTB | none | Warthog, Mongoose, Ghost, Banshee, Falcon (Verify) | the hill |
| Select | Narrows-inspired (Forge World) | medium | side walkways instead of cannons; bidirectional man cannon under the bridge (Halopedia Narrows) | none | top mid |
| Anchor 9 | symmetric station | small, Slayer/CTF | exterior low-gravity section (Verify) | none | the interior top |
| Tempest | symmetric | medium, CTF/Slayer | none | Warthog, Mongoose, Ghost (Verify); Sabre/Seraph in MCC Forge palette | the center structure |
| Condemned | symmetric station | medium, Slayer/CTF | low-gravity core (Verify) | none | the ring walkways |
| Highlands | asymmetric | huge, Invasion/BTB | base shields by phase (Verify) | Warthog, Gauss, Mongoose, Ghost, Banshee, Falcon, Wraith, Scorpion, Revenant | the center structure |
| Breakpoint | asymmetric | huge, Invasion | base doors by phase (Verify) | as Highlands | the ridge |
| Battle Canyon, High Noon, Penance, Ridgeline, Solitary, Headlong (Breakneck), Timberland (Ridgeline) | Anniversary remakes | various | as originals | as originals | as originals |
| Forge World | canvas | any | man cannons, lifts, teleporters as Forge objects; MCC adds Sabre, Seraph, Falcon variants, Forklift, Troop Hog | Forge | |

**Reach Firefight maps (Rule: base plus Defiant and Anniversary packs; all in MCC)**

| Map | Hold positions (Proposed from layout; Verify) | Drops and vehicles | Notes |
|---|---|---|---|
| Beachhead | the upper bunker and the ridge above the beach | Wraith and Ghost drops on the beach (Verify) | the beach is the kill zone |
| Corvette | the central room behind the pillars; the upper catwalks | Phantom drops into the hangar | interior; grenades matter |
| Courtyard | the balcony over the courtyard | Ghost drops | Sword Base section |
| Glacier | the cave mouth and the high ledge | Ghost and Wraith drops (Verify) | large, vehicles roam |
| Holdout | the rooftop interior | Banshee/Ghost drops (Verify) | the roof edges are drop points |
| Outpost | the garage interior and the rooftop | Ghost, Wraith (Verify) | |
| Overlook | the generator plateau | Wraith drops (Verify) | the Generator Defense map |
| Waterfront | the upper deck of the building | Ghost drops | |
| Unearthed (Defiant) | the mine entrance interior | Warthog (Rocket Hog) available to players; Ghost and Wraith drops | the only Firefight map with a player Warthog at start (Verify) |
| Installation 04 (Anniversary) | the gully cover near the Pelican crash | Ghost, Wraith, Banshee drops (Verify) | campaign-style terrain |

**Spire (Invasion, detailed)**
- Phases: 1 (territories, no vehicles, beach side), 2 (vehicles), 3 (core from the Spire top to the beach Pelican) (objective file Part 8.1).
- Interactables: the Spire's lift to the top (Verify; Jetpack is the alternative, `EQ-JET-05`), the Pelican extraction point.
- Plays: `REACH-SPIRE-PLAY-01` Falcon core delivery (`REACH-INV-01`), `REACH-SPIRE-PLAY-02` Elite Wraith denial of the beach, `REACH-SPIRE-PLAY-03` phase-2 vehicle spawn rush (`REACH-INV-03`).
  - Correction: the core is carried as a turret, so PLAY-01 is the Falcon dropping attackers on the top for the core, not a core delivery by air.

**Hemorrhage (detailed)**
- Blood Gulch rules plus: the Revenant and Rocket Hog change the vehicle meta (rocket hog locks on Banshees; `REACH-PUR-02`); players can leave the canyon (sniper perches on the cliffs); Armor Lock on vehicle lanes (`EQ-LOCK-06`).
- Plays: `REACH-HEM-PLAY-01` rocket hog air denial; `REACH-HEM-PLAY-02` cliff sniper over the enemy base; `REACH-HEM-PLAY-03` Scorpion parked on the enemy's cave exits.

### 4.7 Halo 4 (MCC)

**Roster (Rule: launch maps plus Crimson, Majestic, Castle, Champions, and Bullseye packs and Forge canvases are in MCC)**

| Map | Layout | Size / modes | Interactables | Vehicles | Power positions |
|---|---|---|---|---|---|
| Ragnarok | Valhalla remake | large, CTF/BTB/Dominion | man cannons (as Valhalla) | Warthog, Gauss, Mongoose, Ghost, Banshee, Mantis | Laser hill, base tops, caves |
| Exile | asymmetric crater | large, BTB/CTF/Dominion | man cannons (Verify), the cave | Warthog, Gauss, Mongoose, Ghost, Banshee, Scorpion, Wraith (Dominion) | the sniper cave, the central rock |
| Haven | symmetric ring | small, Slayer/CTF/KOTH/Oddball | none | none | top mid ring, the two "nests" |
| Adrift | symmetric | small, Slayer/CTF | none | none | the center bridge |
| Abandon | asymmetric | small, Slayer/Oddball | none | none | the tower top |
| Complex | asymmetric | medium, Slayer/CTF/Dominion | none | Warthog, Mongoose, Ghost (Dominion) | the roof |
| Longbow | symmetric | large, BTB/CTF/Dominion | man cannons (Verify) | Warthog, Gauss, Mongoose, Ghost, Banshee, Scorpion (Dominion) | the center bridge |
| Meltdown | symmetric | large, BTB/CTF/Dominion | none | Warthog, Mongoose, Ghost, Banshee, Wraith (Dominion) | the center tower |
| Solace | symmetric | small, Slayer/CTF | none | none | the center bridge |
| Vortex | asymmetric | large, Dominion/BTB | none | Warthog, Gauss, Mongoose, Ghost, Banshee, Scorpion, Mantis | the center structure |
| Harvest, Shatter, Wreckage (Crimson) | various | BTB/Dominion | none (Shatter has a Mantis) | BTB sets | |
| Landfall, Monolith, Skyline (Majestic) | symmetric | small, Slayer | none | none | |
| Daybreak, Outcast, Perdition (Castle) | various | BTB/Dominion | none | BTB sets | |
| Pitfall (The Pit remake), Vertigo | symmetric | small | Vertigo: a central lift shaft (Verify) | none | as The Pit |
| Impact, Erosion, Ravine (Forge canvases) | any | Forge | Forge pieces incl. man cannons and lifts | Forge | |
| Forge Island (free DLC canvas; MCC) | three flat islands | any | Forge pieces; a Banshee is placed in the stock version (vehicle file note) | Forge | |

**Dominion overlay (all Dominion maps):** each base is a node cluster with `fortify_turrets`, `shield_doors` (Lockdown variant removes both), `resupply_timer` 25 s, `vehicle_spawn_on_supply`. The objective brain's `DOM-01..08` use these; the pack marks which base spawns which vehicle on supply so `DOM-04` can pre-position.

**Ragnarok (detailed):** Valhalla's pack with the Mantis added (`H4-KOTH-03` hill anchor; `H4-PUR-02` lane hold) and the Halo 4 Banshee's non-tracking fuel rod (vehicle file). Plays: `H4-RAG-PLAY-01` Mantis anchors the Laser hill while the Banshee goes air-denial; `H4-RAG-PLAY-02` Gauss hog on the river against the enemy Mantis (Gauss collision damage versus thick armor, vehicle file matrix).

**Exile (detailed):** the sniper cave over the central rock is the power position; the Scorpion and Banshee spawn on opposite sides; Plays: `H4-EXILE-PLAY-01` Scorpion parks at the cave mouth covering the crater; `H4-EXILE-PLAY-02` CTF runner uses the cave route with the Warthog as river decoy.

---

## Part 5. Build order and verification

- `MAP-11` **Build order (Proposed):** build packs first for the maps with the most play and the most interactables: Narrows, Valhalla, The Pit, Guardian, Sandtrap, Last Resort, Avalanche (Halo 3); Lockdown, Zenith, Shrine, Stonetown, Bloodline, Warlord, Remnant (H2A); Lockout, Zanzibar, Midship, Ascension, Relic, Terminal, Coagulation (Halo 2); Blood Gulch, Hang 'Em High, Chill Out (CE); Hemorrhage, Spire, Boneyard, Countdown, Sword Base, Zealot (Reach); Ragnarok, Exile, Haven, Longbow (Halo 4). Then the rest from the roster tables.
- `MAP-12` **Timers:** pull exact weapon, power-up, and vehicle timers per map from the Steam spawn-time guides for CE and Halo 3 (both cited in the file set) and from the gametype variant for the others; store `timer_rule` (game clock vs after pickup; Halo 3's 2 s disturbance delay).
- `MAP-13` **Verify list:** every item tagged Verify above, especially: High Ground's gate switch location, Containment's base doors, Longshore's shutter, Waterworks stalactites, Sandtrap mines, Zenith shield duration, Shrine waterfall cooldown, Bloodline EMP effect on shields, Stonetown gate damage to vehicles, Last Resort wheel hub item, the Reach low-gravity zones, Spire's lift, Halo 4 man cannon placements on Exile and Longbow, Vertigo's shaft, and vehicle sets per Heavy variant.
- `MAP-13b` **MCC-exclusive map verification:** Waterfall, Edge, and Icebox have no published power-position or interactable data in the sources retrieved; build their packs from in-game observation (Edge's 343 description names sentinel beams and silenced SMGs as its signature weapons and a cliff vista plus a database interior as its two zones). Confirm the ODST night-variant set and the Reach Firefight drop tables.
- `MAP-13c` **Part 6 inventory:** every map's traversal and switch inventory is in Part 6; its Verify items are the first thing to confirm in Forge.
- `MAP-14` **Callout audit:** confirm each node's canonical callout against the community names used in MCC today (the Halo 3 MLG callout post and Halopedia map pages are the seeds); the coach and bots must share the exact strings.

---

## Part 6. Complete per-map traversal, interactable, and power-position inventory

This part exists so bots use maps the way humans do: ride lifts and man cannons, take drop-downs, use the Spire's gravity lifts instead of dying off the ledge, shoot the Stonetown hinges to drop the bridges, open the High Ground gate, hop through teleporters, and hold the right power positions. Every map in MCC is listed. Each block gives:

- **Traversal:** lifts, man cannons, teleporters, elevators, ladders, drop-downs, climbable crates, jump routes.
- **Switches and hazards:** anything shot, pressed, or timed; anything that kills.
- **Power positions:** the two to four nodes that decide map control (named with their community callouts where known).
- **Bot movement notes:** the human habits the pathfinder and objective brain should copy on this map.

Status: items confirmed by a retrieved source are stated plainly; **Verify** marks general-knowledge items to confirm in MCC. Power positions are seeded from guides and consensus and are re-ranked live by the objective brain (`MAP-06`).

### 6.0 Human-movement rules that apply to every map (Proposed)

- `MOVE-01` **Drops are routes.** Any ledge a human drops from without fall damage is a one-way edge in the pathfinder. Bots take drops to cut corners, to escape, and to land on enemies; the pathfinder marks a drop `hot` if an enemy holds the landing.
- `MOVE-02` **Lifts and cannons are routes with a cost.** Use them whenever the alternative is a long walk, unless the exit or landing is `hot` (`INTER-LIFT-01`, `INTER-CANNON-02`). Carriers use them only when the exit is held by a teammate.
- `MOVE-03` **Never walk off a death drop.** Maps with lethal falls (Spire top, Lockout/Lockdown edges, Guardian, Ascension/Zenith, Boarding Action, Complex's ocean side, Construct's abyss, Zealot's space edge) have `kill_edges` in the pack; the pathfinder never routes across them and the combat brain stops strafing within 1 m of one. Jetpack or a gravity vent is the only sanctioned way down from a lethal height.
- `MOVE-04` **Ladders are slow and blind** (CE and Halo 2 only): never climb into a held position; climb only when the top is clear on radar/callouts; drop instead of climbing down.
- `MOVE-05` **Crate and ledge jumps** that humans use (Adrift crates to the next level, Lockout BR-tower jumps, The Pit's training-to-green-box hops, Midship's ramp jumps) are stored per map as `jump_edges` with a success rate per tier (Easy never, Normal common jumps, Heroic most, Legendary all).
- `MOVE-06` **Switches are jobs.** Every switch in a map pack has a `who_benefits` field; the objective brain assigns a bot to it when that benefit is live (attacker opens gates; defender drops gates, seals shutters, raises Zenith's shield when we hold mid).
- `MOVE-07` **Hazards are weapons.** Trains, mines, stalactites, turrets, and gravity vents go in the pack as both `avoid` and `bait` objects (`MCMD-BAIT` at Legendary).

### 6.1 Halo: Combat Evolved

**Blood Gulch**
- Traversal: two one-way teleporters (one per base, to the mid cliffs); base interior ramps to the roof; two ground entrances per base.
- Switches/hazards: none.
- Power positions: base roofs (sniper over the whole canyon), the mid cliffs at the teleporter exits, the rock outcrops on each side of mid.
- Bot notes: hog shuttle at the teleporter exit for the flag (`CE-CTF-02`); Banshee pilots never land near the enemy base; snipers rotate between roof corners after two shots.

**Battle Creek**
- Traversal: a teleporter per base; ladders onto the base roofs; drop-downs from the roofs into the creek.
- Switches/hazards: none.
- Power positions: the base roofs (sniper), the creek-side rocks, the mid rock pillar.
- Bot notes: ladders are the blind route (`MOVE-04`); the flag leaves by the side ramps, not the ladder.

**Chill Out**
- Traversal: several teleporters linking the rooms; ladders; drop-downs from the upper walkways.
- Switches/hazards: none.
- Power positions: the OS/camo room overlook, the long hallway's upper end, the teleporter hub.
- Bot notes: pre-aim every teleporter exit; power-ups on 2:00 (Halo 1 Guide).

**Chiron TL-34**
- Traversal: a teleporter maze; almost every room connects by teleporter only.
- Switches/hazards: none.
- Power positions: the room with the most teleporter exits in view; the shotgun room.
- Bot notes: radar is useless; shotgun and pre-aim; never stand in a teleporter's line of sight.

**Damnation**
- Traversal: ladders, drop-downs between the three levels, the waterfall drop (Verify no fall damage), lifts (Verify).
- Switches/hazards: the lower water channel (Verify lethal).
- Power positions: the top walkway over the central pit, the rocket ledge, the camo alcove.
- Bot notes: control the top level; drops are faster than ladders in every direction.

**Derelict**
- Traversal: teleporters between the two mirrored halves (Verify) and the central lift/vents (Verify).
- Power positions: the upper ring over the center, the shotgun hallway.
- Bot notes: FFA map; hold a corner with a single approach.

**Hang 'Em High**
- Traversal: ladders up the pillars and bases, drop-downs from the catwalks, teleporters (Verify which pairs).
- Switches/hazards: lethal pits at the map edge (Verify).
- Power positions: the Tombstone platform, the sniper ledge over mid, base roofs.
- Bot notes: catwalks are fast but exposed; tunnels for carriers; drops to escape snipers.

**Longest**
- Traversal: side rooms with ramps; drop-downs from the side platforms.
- Power positions: the two side-room overlooks on the long hallways.
- Bot notes: never cross a hallway without grenades first.

**Prisoner**
- Traversal: ramps and ladders between four floors; drop-downs from every floor.
- Power positions: the top floor corners, the rocket ledge.
- Bot notes: top-floor control; drop to escape, climb only when clear.

**Rat Race**
- Traversal: one teleporter closing the loop; ramps.
- Power positions: the teleporter exit overlook, the top of the ramp loop.
- Bot notes: the loop runs one direction; bots circle against the enemy's flow.

**Sidewinder**
- Traversal: a teleporter per base (to the far cliff), base interior ramps, the frozen river.
- Switches/hazards: none.
- Power positions: base tops, the central ice bridge/tunnel mouths, the cliff above each base.
- Bot notes: Warthogs slide on ice (fixed in Avalanche); vehicle lanes avoid the center ice at speed.

**Wizard**
- Traversal: four corner lifts/ramps to the upper platforms (Verify lifts vs ramps), teleporters.
- Power positions: the upper corner platforms.
- Bot notes: hold two adjacent corners (as Warlord).

**Boarding Action**
- Traversal: teleporters between the two ships; ladders inside each ship; drop-downs between decks.
- Switches/hazards: the gap between the ships is a death drop (`MOVE-03`).
- Power positions: each ship's top deck (sniper duels across the gap), the teleporter rooms.
- Bot notes: never strafe near the gap; teleporter exits are pre-aimed.

**Danger Canyon**
- Traversal: teleporters (Verify), base tunnels, the underground mid.
- Power positions: base tops, the bottom-mid power-up room, the cliff overlooks.
- Bot notes: vehicles on the surface, carriers underground.

**Death Island**
- Traversal: teleporters (Verify), beach ramps.
- Switches/hazards: water is lethal; vehicles sink.
- Power positions: base tops, the island's central hill.
- Bot notes: Banshee dominant; vehicles stay off the surf line.

**Gephyrophobia**
- Traversal: the bridge's upper and lower decks with ramps at each end and drop-downs between decks.
- Switches/hazards: the chasm on both sides is a death drop.
- Power positions: the bridge's upper deck mid, the base towers.
- Bot notes: snipers on the upper deck; vehicles on the lower deck; no strafing at the rails.

**Ice Fields**
- Traversal: teleporters, base ramps, ice bridges.
- Power positions: base tops, the bottom-mid power-up room, the ice bridge overlooks.
- Bot notes: as Sidewinder.

**Infinity**
- Traversal: teleporters (Verify), long base ramps.
- Power positions: base tops, the central structure.
- Bot notes: the longest CE map; vehicles are mandatory for carriers.

**Timberland**
- Traversal: teleporters (Verify), tree-line paths.
- Power positions: base tops, the mid hill.
- Bot notes: forest cover favors flanks on foot; vehicles stay on the open lanes.

### 6.2 Halo 2

**Lockout**
- Traversal: the gravity lift (bottom to sniper tower side), drop-downs from every tower (BR tower to bottom, sniper tower to library side, elbow to bottom), the glass center, Library doors.
- Switches/hazards: edges are death drops.
- Power positions: Sniper Tower top, BR Tower top, the Elbow landing, Library doorway.
- Bot notes: humans drop everywhere on Lockout; the pathfinder uses every drop; the lift is only for a fast sniper-tower approach when the top is clear.

**Ascension**
- Traversal: the gravity lift to the upper platform, the teleporter, ramps around the dish, drop-downs from the towers.
- Switches/hazards: edges over the sea are death drops; the dish is exposed.
- Power positions: the sniper tower, the Banshee tower, the top of the lift.
- Bot notes: avoid the dish; Oddball in the lift room with teleporter escape (`H2-ASC-PLAY-02`).

**Midship**
- Traversal: ramps to the two towers, the "carbine" walkway, drop-downs from pink/blue towers to bottom mid, ramp jumps (`jump_edges`).
- Switches/hazards: none.
- Power positions: top mid (carbine), pink tower top, blue tower top.
- Bot notes: hold top mid plus one tower; drops to reset fights.

**Ivory Tower**
- Traversal: the elevator (up to the middle of the top hallway, down to the middle of the bottom hallway), the giant stone steps, the rocket alley to the drainage grate, drop-downs from the upper balconies (Verify).
- Switches/hazards: none.
- Power positions: the top of the elevator (sniper spawn), the upper hallway balconies over the circular room, the alley mouth.
- Bot notes: the elevator exit is a camp point both ways; One Flag Fast offense races the sniper at the top versus defense's rockets in the alley (Halopedia).

**Beaver Creek**
- Traversal: teleporters, base roof ladders (Verify ramps in Halo 2), creek drops.
- Power positions: base roofs, the creek rocks.

**Burial Mounds**
- Traversal: a gravity lift at the Covenant structure (Verify), ramps up the mounds, tunnels.
- Power positions: the top of the main structure, the Wraith-side hill (Verify).

**Coagulation**
- Traversal: base roofs via interior ramps; each base has an underground level with the Banshee; teleporters (Verify).
- Power positions: base roofs, the mid rocks, the caves.
- Bot notes: Banshee from the basement at spawn; hog routes along the walls.

**Colossus**
- Traversal: conveyor belts (Verify) and lifts between the two long floors.
- Power positions: the upper walkway ends.

**Foundation**
- Traversal: four corner stairways to the upper ring; drop-downs to the center.
- Power positions: the upper ring corners.

**Headlong**
- Traversal: building stairs, the crane gantries, drop-downs from rooftops, lifts (Verify).
- Switches/hazards: construction-site edges.
- Power positions: the sniper building roof, the garage roof, the central bridge.
- Bot notes: vehicles on the street loop, infantry on the rooftops.

**Zanzibar**
- Traversal: the wheel's spokes to the top and the hub niche (sword), the bridge to the wheel from the flag room, base stairs, the sea-wall ramp, the beach path.
- Switches/hazards: the gate switch (open-only, either team; vehicles then drive into the base), the base-room second-floor panel for the side gate; the wheel can crush/fling.
- Power positions: the base second floor (flag room), the sniper tower by the wheel, the sea wall, the beach cliff over the gate.
- Bot notes: `H2-ZAN-PLAY-01..03`; attackers open the gate first; sword run via the wheel for the rusher.

**Waterworks**
- Traversal: cavern ramps, lifts (Verify), tunnels.
- Switches/hazards: falling stalactites in the center (Verify).
- Power positions: the upper cavern ledges, the mid structure top.

**Backwash**
- Traversal: swamp paths, the central structure ramps.
- Switches/hazards: fog (sightlines short).
- Power positions: the structure's upper level.
- Bot notes: radar-led play; shotgun/sword.

**Containment**
- Traversal: base interiors, bridges over the chasm, tunnels.
- Switches/hazards: base doors on switches (Verify), the chasm is a death drop.
- Power positions: base tops, the mid bridge ends.
- Bot notes: attackers hit the door switch before the vehicle push (as High Ground).

**Elongation**
- Traversal: two conveyor belts along the long axis (Verify direction), side rooms.
- Power positions: the ends of the belts, the side-room overlooks.
- Bot notes: grenades ride the belts (`INTER-MOVE-03`).

**Gemini**
- Traversal: teleporters linking the two halves (Verify), ramps.
- Power positions: the upper ring.

**Relic**
- Traversal: the switch-activated two-way teleporter (Bowl to Teleport Ridge), the beach ramps, the structure's interior lifts (Verify).
- Switches/hazards: the teleporter switch (either team).
- Power positions: the structure top (sniper), the Bowl, Teleport Ridge.
- Bot notes: `H2-REL-PLAY-01/02`.

**Sanctuary**
- Traversal: ramps into the shrines' upper rooms, the shotgun tunnel, rock jumps.
- Power positions: the shrine upper rooms, the sniper ledges, the rocks between shrines.

**Terminal**
- Traversal: station stairs, the overpass, the tracks (lethal when the train passes).
- Switches/hazards: the train (scripted cycle); Verify whether a switch controls it.
- Power positions: the station upper platforms, the garage roof.
- Bot notes: `INTER-MOVE-01`.

**Turf**
- Traversal: alley stairs, rooftops via ramps, drop-downs into the street.
- Power positions: the main-street overlooks, the back-alley rooftop.
- Bot notes: Warthog on the main street only; infantry in the alleys.

**Warlock**
- Traversal: four corner gravity lifts to the raised platforms, two-way teleporters between corners.
- Power positions: the corner platforms.
- Bot notes: as Warlord.

**Desolation**
- Traversal: as Derelict (teleporters, Verify).

**Tombstone**
- Traversal: as Hang 'Em High (teleporters, ladders replaced by ramps, Verify).

**Uplift**
- Traversal: lifts (Verify), ramps.
- Power positions: the center structure top.

**District**
- Traversal: building stairs, rooftops.
- Power positions: the tallest rooftop, the plaza overlooks.

### 6.3 Halo 2: Anniversary multiplayer

**Lockdown** (Lockout plus)
- Traversal: as Lockout, with added cover on the Elbow; the center glass is a floor until broken.
- Switches/hazards: three stalactites (BR tower, top-center glass, sniper-tower ramp) shot to drop; the glass regenerates.
- Power positions: as Lockout.
- Bot notes: `INTER-FALL-01..03`; never set up under an intact stalactite.

**Zenith** (Ascension plus)
- Traversal: lift, teleporter, ramps as Ascension.
- Switches/hazards: the center energy shield from any of three outskirt switches (repeatable).
- Power positions: the towers; mid only behind our own shield.
- Bot notes: `INTER-SHIELD-02`, `H2A-ZEN-PLAY-01..03`.

**Bloodline** (Coagulation plus)
- Traversal: single-level bases with one entrance/exit where the drop and lift used to be; UNSC vehicle bridges.
- Switches/hazards: the base EMP switch.
- Power positions: base roofs, the mid rocks, the bridges' far ends.
- Bot notes: `INTER-SHIELD-04`, `H2A-BLOOD-PLAY-01/02`.

**Stonetown** (Zanzibar plus)
- Traversal: as Zanzibar; two wheel walkways start raised and drop when their red hinges are shot or meleed.
- Switches/hazards: the gate switch above the gate (shoot to open); the generator in the plant (shoot to drop the gate); the Station 7 blast-cover arms (shoot to seal the windows).
- Power positions: as Zanzibar.
- Bot notes: `INTER-GATE-03..05`, `H2A-STONE-PLAY-01/02`.

**Shrine** (Sanctuary plus)
- Traversal: a gravity lift in the shotgun tunnel to the room above; rock jumps.
- Switches/hazards: the ceiling device per base (30-s waterfall blocks the base's front LOS).
- Power positions: as Sanctuary.
- Bot notes: `INTER-SHIELD-03`.

**Warlord** (Warlock plus)
- Traversal: per-corner lifts, two-way teleporters.
- Power positions: the corner platforms.

**Remnant** (Relic plus)
- Traversal: the Bowl switch opens a two-way teleporter to Teleport Ridge.
- Power positions: as Relic.

**Skyward, Awash, Nebula**: Forge canvases with scripted switches; packs come from the Forge variant.

### 6.4 Halo 3

**Valhalla**
- Traversal: two man cannons per base (center to near the Laser hill, side to the sniper rock), base roof ramps, the caves, the river.
- Switches/hazards: none (the river is a vehicle lane, not lethal).
- Power positions: the Laser hill, base roofs, the caves, the turret rocks.
- Bot notes: `INTER-CANNON-01..06` (weight-based cannons), `H3-VAL-PLAY-01..03`.

**Narrows**
- Traversal: one man cannon per base (fixed trajectory, lands on the enemy's top level), the top bridge, the low bridge, the energy bridge under the main bridge, each base's low point.
- Switches/hazards: none; the sides are death drops.
- Power positions: Top Mid, each base's top entrance, the low points for Oddball.
- Bot notes: `H3-NAR-PLAY-01..03`; flag throws through the cannon.

**The Pit**
- Traversal: base ramps, the sword-room ramps, the training-to-green-box hops (`jump_edges`), drop-downs from the sniper towers.
- Switches/hazards: none.
- Power positions: Sniper towers (S3), Green Box, Training/Long Hall junction, base tops.
- Bot notes: `H3-PIT-PLAY-01..03`.

**Guardian**
- Traversal: man cannons (bottom blue to sniper tower; a second to the center platform; one to yellow lift's camo), the gold and yellow lifts, catwalks, drop-downs from blue room to the dead-end hall and from the elbow.
- Switches/hazards: the hologram is scenery; edges are death drops.
- Power positions: Sniper Tower (OS), Blue Room, Gold Lift/camo, the Elbow.
- Bot notes: `H3-GUARD-PLAY-01..03`; "know where each man cannon leads."

**Construct**
- Traversal: three gravity lifts (any floor to the top), ramps between floors, drop-downs.
- Switches/hazards: the central abyss is a death drop.
- Power positions: the top floor, one full side of the map.
- Bot notes: hold one side (MLG thread); lift exits are grenade points.

**Sandtrap**
- Traversal: temple ramps and gravity lifts inside the temples (lifts stop working when the map is overloaded, Fandom), the Elephants (walk the ramp), man cannons (Verify).
- Switches/hazards: the minefield ring (vertically launching mines at the boundary; "Brute landmines"); the light bulbs lining it stop vehicles.
- Power positions: the temple tops, the Elephant decks, the central dune.
- Bot notes: vehicle lanes exclude the minefield; `H3-SAND-PLAY-01..03`.

**Last Resort**
- Traversal: as Zanzibar (the wheel spokes, the bridge from the flag room, the sea wall, the beach).
- Switches/hazards: the gate switch (open-only); the wheel hub item (Verify).
- Power positions: the base second floor, the sniper tower by the wheel, the sea wall, the camp.

**High Ground**
- Traversal: the main gate (closed only in asymmetric gametypes), side passages into the base, the lower level to the pillbox bunker with a bunker hatch, the catwalk to the gate controls, the watchtower above the bunker.
- Switches/hazards: the gate switch on the catwalk (permanent open, as Zanzibar; "usually open within the first minute"); the machine-gun turret mounted above the gate; movable gates near the SAM launcher (Fandom).
- Power positions: the upper deck over the gate (turret), the gate-switch catwalk (the defenders' chokepoint), the bunker, the watchtower.
- Bot notes: attackers send one bot through the bunker/side passages to the switch while the rest push the beach; defenders hold the catwalk and the turret; once open, the Warthog goes through.

**Snowbound**
- Traversal: the underground tunnel between bases, base entrances through shield doors, the surface hill.
- Switches/hazards: built-in shield doors on the base entrances; automated turrets at the map boundary (kill players who leave).
- Power positions: the hill between bases, the tunnel exits, the base interiors behind the shield doors.
- Bot notes: `INTER-SHIELD-01` (melee through the doors); the Ghost cannot enter the bases.

**Epitaph**
- Traversal: gravity lifts between floors, the floating center platform, shield doors in the hallways.
- Switches/hazards: shield doors.
- Power positions: the top floor, the floating platform.
- Bot notes: shield doors are melee doors; the platform is exposed from every floor.

**Isolation**
- Traversal: lifts (Fandom), the Flood tunnels below, ramps up the hill.
- Power positions: the hill, the tunnel exits, the two base structures.

**Standoff**
- Traversal: base interior ramps to the roofs, the back door, the rock in the middle, the outskirts route.
- Switches/hazards: switch-operated doors and windows in the bases.
- Power positions: base roofs, the mid rock, the satellite dish side.
- Bot notes: `INTER-GATE-06`, `H3-CTF-03/05/08`.

**Rat's Nest**
- Traversal: the vehicle loop road (even terrain, Halopedia), interior catwalks, side tunnels ("rarely used"), vents.
- Switches/hazards: none built in.
- Power positions: the interior catwalks over the road, the base interiors.
- Bot notes: Ghost on the loop; infantry on catwalks; carriers through the side tunnels.

**Foundry**: Forge canvas; packs per variant.

**Avalanche**
- Traversal: a large man cannon in front of each base to the base top; three small cannons per side (back-corner ones to back-center); base interior ramps; the ice cave; the teleporter (Verify two-way).
- Switches/hazards: none.
- Power positions: base tops, the ice cave, the hornet pad by the teleporter, the center hill.
- Bot notes: `H3-AVA-PLAY-01/02`; cannons disable if the map is overloaded (irrelevant in stock play).

**Blackout** (Lockout remake)
- Traversal: the air lift, drops as Lockout.
- Power positions: as Lockout.

**Ghost Town**
- Traversal: the tower stairs, the pipes, drop-downs from the walls.
- Power positions: the tower, the pipe overlook, the central courtyard edges.

**Cold Storage** (Chill Out remake)
- Traversal: teleporters as Chill Out; Flood growths block some lines (Verify).
- Power positions: as Chill Out.

**Assembly**
- Traversal: air lifts (a blue lift and yellow lifts) to the upper ring; ramps.
- Power positions: the upper ring over the center platform.
- Bot notes: lift exits are the fight.

**Orbital**
- Traversal: the long hall, side stairs, a man cannon (Verify).
- Power positions: the long hall ends, the upper side rooms.

**Sandbox**: Forge canvas (ground, sky bubble, crypt); man cannons and lifts as placed.

**Citadel**
- Traversal: ramps to the top walkways, drop-downs.
- Power positions: the top walkways' corners.

**Heretic** (Midship remake)
- Traversal: as Midship; grav lifts (Fandom) in place of some ramps (Verify where).
- Power positions: top mid, the towers.

**Longshore**
- Traversal: warehouse stairs, the roof, cranes (Verify), the dock edges.
- Switches/hazards: a switch-operated shutter (Verify).
- Power positions: the warehouse roof, the fish-house overlook.

**Waterfall, Edge, Icebox (MCC-exclusive)**
- Waterfall: symmetric Forerunner jungle; traversal and power positions from in-game observation (Verify).
- Edge: a cliff vista and a database interior; 4 to 12 players; sentinel beams and silenced SMGs (343); Verify traversal.
- Icebox: Turf remake; as Turf (alleys, rooftops, main street); Verify changes.

**MLG variants**: as their base maps; weapons spawn in the air.

### 6.5 Halo 3: ODST (Firefight)

Every ODST Firefight map is a campaign space; traversal is stairs, drop-downs, and in some cases vehicles. The FF brain's hold rules (`FF-POS-01`) use these:

- **Lost Platoon:** the roofed main building (mortar-immune), the garage; vehicle lanes around the outside; Hornet pad (MCC).
- **Crater / Crater (Night):** the ramp interior, the upper walkways; Ghost drops.
- **Rally Point / Rally Point (Night):** the back corridors; stairs between the plaza levels.
- **Security Zone:** the elevated platform; the stairwells.
- **Alpha Site:** the courtyard arches; the upper balcony.
- **Windward:** rooftop interiors; the stairwell down; Banshee drops (Verify).
- **Chasm Ten:** the central ramp; the side corridors.
- **Last Exit:** the stairwells; the plaza where Ghosts drop (Splatter Spree guide).

### 6.6 Halo: Reach

**Sword Base**
- Traversal: three gravity lifts (the central Covenant lift in the atrium was weakened from the beta; two others), High Bridge, Low Bridge, the Elbow, Security Lobby, Research Atrium, Server Room stairs; sprint-onto-lift ledge trick removed (Fandom).
- Switches/hazards: none.
- Power positions: the top of the central lift, High Bridge, the Elbow, the Server Room overlook.
- Bot notes: lift exits are grenade points; Infection holds in the Server Room.

**Countdown**
- Traversal: two airlift landings on the Catwalk (the sword spawns between them), the Ventilation room lift to the third floor, stairs between all three floors, drop-downs from every floor ("jumping down from a higher floor or taking the vents up").
- Switches/hazards: none (the central shaft is a death drop, Verify).
- Power positions: the Catwalk, the top-floor corners, the Ventilation exit.
- Bot notes: humans drop to the fight and lift away from it.

**Reflection** (Ivory Tower remake)
- Traversal: the elevator (up and down), the stone steps, the rocket alley, balconies.
- Power positions: the top of the elevator, the upper balconies.

**Zealot**
- Traversal: ground-level man cannons to the second-floor middle room; a ground lift to the third floor (space); second-floor lifts to the third floor; ramps.
- Switches/hazards: the third floor is outside the ship beyond a shield that players pass but projectiles do not; low gravity there (longer jumps, slower falls).
- Power positions: the upper level, the second-floor middle room; space is an escape and a sniper lane, not a hold.
- Bot notes: `INTER-LOWG-01/02`; the space shield means a bot being shot at can step through it to break the shot.

**Boardwalk**
- Traversal: the boardwalk's upper deck stairs, the plaza ramps, drop-downs to the lower walk.
- Power positions: the upper deck, the balcony over the plaza.

**Powerhouse**
- Traversal: the pump-room stairs, the bridge, the hillside paths, drop-downs from the roof.
- Switches/hazards: the water channel (not lethal, Verify).
- Power positions: the pump-room roof, the bridge, the hill.

**Spire**
- Traversal: gravity lifts at the bottom of the spire send players to the top (the mid-level generators are reached by riding up and jumping down, or by reacting fast in the lift); in Invasion phase 2 the lifts do not go to the top; in phase 3 three gravity lifts spawn for ground access; jumping from the top is death unless the player lands on a light-gravity vent, a passing air vehicle, or uses the Jetpack; the beach, Devil's Den, BFG, Bluff.
- Switches/hazards: the top edge (`MOVE-03`), a plasma grenade thrown into the bottom lifts bounces between them and damages users (Fandom).
- Power positions: the spire top, the mid generator deck, the beach Pelican, Devil's Den.
- Bot notes: bots descend via the gravity vents, the phase-3 lifts, or Jetpack, never by jumping; Elites contest the lift bases; `REACH-SPIRE-PLAY-01..03`.

**Boneyard**
- Traversal: the ship's interior ramps and lifts (Verify), the yard, the dropship area.
- Switches/hazards: phase doors (Verify).
- Power positions: the ship interior overlooks, the yard's central wreck.

**Hemorrhage**
- Traversal: base roofs via interior ramps; the cliffs are climbable (players can leave the canyon).
- Power positions: base roofs, the cliff perches, the caves.

**Asylum, Pinnacle, The Cage, Paradiso, Select** (Forge World variants)
- Asylum: as Sanctuary (no device).
- Pinnacle: as Ascension (lift and teleporter, Verify).
- The Cage: ramps and drop-downs to the lower ring; the edge is a death drop.
- Paradiso: the island hill, beach lanes; vehicles.
- Select: side walkways instead of cannons; a bidirectional man cannon under the bridge (Halopedia Narrows).

**Anchor 9**
- Traversal: interior stairs, the exterior low-gravity walkway (Verify).
- Power positions: the interior top, the exterior overlook.

**Tempest**
- Traversal: the center structure ramps, beach lanes, base roofs; MCC Forge adds Sabre and Seraph.
- Power positions: the center structure top, base roofs.

**Condemned**
- Traversal: the ring walkways, the low-gravity core (Verify).
- Power positions: the ring's upper walkways.

**Highlands**
- Traversal: the center structure, base interiors, phase shields (Verify).
- Power positions: the center structure, the ridge.

**Breakpoint**
- Traversal: base interiors, the ridge paths, phase doors (Verify).
- Power positions: the ridge, the base roofs.

**Anniversary pack (Battle Canyon, High Noon, Penance, Ridgeline, Solitary, Breakneck)**: as their CE/Halo 2 originals (Battle Creek, Hang 'Em High, Damnation, Timberland, Prisoner, Headlong) with Reach movement; Verify teleporter and lift placements per remake.

**Forge World**: canvas; packs per variant.

**Reach Firefight maps**: hold positions in Part 4.6; traversal is campaign geometry (stairs, ramps, ledges).

### 6.7 Halo 4

**Ragnarok** (Valhalla remake)
- Traversal: as Valhalla (two man cannons per base, caves, base roofs).
- Power positions: the Laser hill, base roofs, the caves.
- Bot notes: Mantis on the hill (`H4-RAG-PLAY-01`).

**Exile**
- Traversal: the central rock ramps, the sniper cave, the river bed, man cannons (Verify).
- Power positions: the sniper cave, the central rock, the Scorpion spawn side.

**Haven**
- Traversal: the ring's ramps, the two "nests," drop-downs from the top ring to the floor.
- Power positions: top mid, the nests.

**Adrift**
- Traversal: outer man cannons around the map; two gravity lifts on the lower level (across from each other) leading to the hallway by either base; four stairwells; crates to jump up a level; a platform with a single man cannon to the base/objective (Halopedia).
- Power positions: the center room's upper level, the base hallways.
- Bot notes: humans use the crate jumps and cannons constantly; `MOVE-05`.

**Abandon**
- Traversal: the tower stairs, the jungle paths, drop-downs from the tower.
- Power positions: the tower top, the cave mouth.

**Complex**
- Traversal: building stairs, rooftops, walkways; one side open to the ocean (lethal fall).
- Power positions: the roof of the central building, the two base buildings' upper floors.
- Bot notes: `MOVE-03` on the ocean side.

**Longbow**
- Traversal: the center bridge, base interiors, man cannons (Verify), the mass-driver platforms.
- Power positions: the center bridge, the base towers.

**Meltdown**
- Traversal: a figure-8 lower vehicle loop and upper infantry paths and tunnels through the rock; numerous man cannons that send players and vehicles across the map (Fandom).
- Power positions: the center tower, the tunnel mouths.
- Bot notes: vehicles through cannons (`INTER-CANNON-06`).

**Solace**
- Traversal: the center bridge, side ramps, drop-downs.
- Power positions: the center bridge, the towers.

**Vortex**
- Traversal: the center structure ramps, base interiors, the canyon lanes.
- Power positions: the center structure, the Mantis side.

**Harvest, Shatter, Wreckage** (Crimson)
- Harvest: the farm structures' roofs; vehicles on the roads.
- Shatter: the crystal canyon; Mantis; the center bridge.
- Wreckage: the crashed-ship interior; the central hull.

**Landfall, Monolith, Skyline** (Majestic)
- Landfall: the beach structures' upper floors.
- Monolith: central man cannons, short corridors, almost no cover (Halopedia); power positions are the corners.
- Skyline: the rooftops; the crane.

**Daybreak, Outcast, Perdition** (Castle)
- Daybreak: the center bridge; base roofs.
- Outcast: the canyon ridges; vehicles.
- Perdition: the stadium interior; the upper deck.

**Pitfall** (The Pit remake), **Vertigo**
- Pitfall: as The Pit.
- Vertigo: a central lift shaft (Verify); the upper platforms.

**Impact, Erosion, Ravine, Forge Island**: canvases; packs per variant.

### 6.8 Build priority for Part 6 data (Proposed)

Confirm the Verify items by playing each map once in Forge/custom games with a checklist (lifts, cannons, teleporters, switches, hazards, death edges, jump edges), then fill the pack. Start with the maps whose traversal is most "human": Spire, Lockout/Lockdown, Guardian, Construct, Narrows, Valhalla/Ragnarok, Zealot, Countdown, Adrift, Meltdown, Zanzibar/Stonetown/Last Resort, High Ground, Avalanche, Sandtrap.
