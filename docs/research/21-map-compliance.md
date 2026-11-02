# Guide 21 compliance: the map brain against the code, and how it fits the other four brains

the player's fifth brain, `docs/research/21-map-brain.md` (copied unchanged from Desktop/Halo_MCC_Bot_brains/
halo_mcc_map_brain.md), rule by rule. Status: **done** (coded; offline test named where one exists),
**partial** (what is missing is named), **open** (not coded), **blocked** (needs a game read or an input botcore does
not have yet; the note names it). Blocked is not "not applicable". Nothing here is "seen live" unless a trace is named.

Audit at HEAD 0b5696f. Bare file names are under `brain/`. Units: the guide uses metres, the code world units
(1 u = 10 ft = 3.048 m): 8 m = 2.6 u, 10 m = 3.3 u, 20 m = 6.6 u, 1 m = 0.33 u.

Coded for this audit: `Bot.exit_held` (c8eb95f, `tools/test_exit_held.py`), the MCMD-BAIT limits in `coach.validate`
(0b5696f, `tools/test_coach.py`). Coded on branch r17-mapbrain (offline tests only, nothing seen live): MAP-05 /
MAP-06 (the anchor's post by score and hot zone; people's walk weights the score, positions.json not regenerated),
MAP-10, MAP-09, INTER-LIFT-01's sightline (with INTER-TELE-01 and INTER-CANNON-02), MAP-08 / CALL-04 (spawn guess),
CALL-01 aliases, INTER-TELE-01's way round, INTER-LIFT-02's rider, MAP-12's Halo 3 delay (`tools/test_director_map.py`
and the tests named per row). Found and fixed on the way (not a map-brain rule, but the map brain's Sandtrap entry
names the Elephant decks): Halo 3 bots could not pick up a flag whose stand rides an Elephant (botcore s136, f7eff15).

## How the map layer fits: the "knowledge pack" already exists, spread over files

The guide's Part 0.1 asks for one JSON pack per map per game. The code has that pack in memory: `maps.load(name)`
builds one dict per map folder `maps/<game>_<map>/` (Halo 2's Lockout and H2A's Lockdown are separate folders, as
MAP-01 asks), from these files. No second source of truth was added; each pack field maps onto what is there:

| Pack field | Where it lives now | Missing |
|---|---|---|
| game, map, one pack per remake | the folder name (`h2_lockout`, `h2a_ca_lockout`) | nothing |
| teams.base_node | `callouts.json` base_radius / roof_z with the flags (`m["bases"]`) | nothing |
| nodes with callouts | `callouts.json` zones (polygon, height band, priority, name, long name), `callouts.ZoneMap` | cover and sightlines per node; community names outside CE (CALL-01) |
| lanes | `callouts.json` "lanes" (points) and "sneak" routes per team | names, `vehicle_ok`, `carrier_safe_if`, `blind_corners` |
| power_positions | `positions.json` (`tools/power_positions.py`: height, floor seen, cover, escape, items) | per-mode tags (MAP-06) |
| hold_spots | `callouts.json` holds per team (`tools/gen_zones.py`, `make_zones.py`) | per-mode tags, single-approach test (MAP-07) |
| spawn_zones | `objects.json` spawns per team per game type (`m["spawns"]`) | which enemy positions push spawns where (MAP-08) |
| weapon / power-up spawns and timers | `objects.json` equipment, `maps.POWER`, the scenario's spawn time (`maps.power_items`) | `timer_rule` (MAP-12) |
| vehicle spawns | `objects.json` vehicles, live vehicle reads | respawn timers in planning (INTER-VEH-01) |
| interactables | `features.json` kinds teleporter, launcher, lift, control, door, shield (`tools/map_features.py`); teleporter pairs in `objects.json` | trigger, effect, duration, who, cooldown, and any live state |
| traversal (cannon flights, lift rides, drops, jumps) | `lidar.json` links learned from play: 12,079 jumps, 1,170 routes, 2 crouch paths over 123 maps; `terrain.jump_ways` makes rides and big drops one-way | a weight-based cannon's vehicle landing (INTER-CANNON-01) |
| kill edges | the level's void read by `Bot.edge_guard` and the nav's `safe` carrier field | not stored as named edges (no need found) |
| overlays per game type | spawns per type and objective spots per type (hills, balls, territories, bombs: `m["spots"]`) | per-mode lanes, power positions, hot zones (MAP-03) |
| callout_aliases | a zone's long name (`Zone.full`) and its aliases (`Zone.aka`, 677 of 1660 zones; resolved by `director.order_points`) | aliases for the other zones (CALL-01) |

## Conflicts with the other brains and the code, and how each is resolved

| # | Conflict | Resolution |
|---|---|---|
| C1 | Part 3.1's advice JSON (`ttl`, `posture`, `roles` map, a `map` command array, `note`) is not guide 18's 8.4 schema, which `coach.SCHEMA` implements as written (`additionalProperties: false`) | Guide 18's schema stays the transport (the map brain itself defers to "the addendum file Part 4"). Each MCMD rides on an 8.4 order: GO = push / hold with a callout target, HOLD = hold plus the anchor / guard roles, ROTATE = rotate, WATCH = watch, DENY = deny, BAIT = bait, TIMER = an order's `on: "timer:<item>"` (V6), CALL = `callouts`. LANE, AVOID and TRIGGER get no verb until named lanes, path costs and interactable reads exist: a verb the bots cannot act on would only let the coach issue orders that do nothing |
| C2 | Role names ANCHOR, RING, SCORER, ROAMER, RUNNER, ESCORT, GATE_OPENER, SHIELD_SWITCH are not in `coach.ROLES` | Read as anchor, guard, king, rotator, carrier, escort (`director.ROLE_FIT` maps those onto the director's slots). GATE_OPENER and SHIELD_SWITCH are jobs (MOVE-06), not roles: orders once switches can be read and pressed |
| C3 | MOVE-05: "Easy never" takes jump edges; the player: Easy uses jumps to get around, never as a fighting trick, coded as every bot using people's jumps | the player's rule stands. Jumps the nav computes itself are already for jump-minded personalities only (`jump >= 0.5`) |
| C4 | Spire (Part 6.6): "bots descend via the gravity vents, the phase-3 lifts, or Jetpack, never by jumping"; the code let bots use people's drops there and the reverse of people's rides up the middle lift | Resolved by the player (his Invasion match:, shown live): the eight heat-vent drops are his links (maps/reach_35_island/drops.json), climbs over 4 u are one-way (no jump down the middle lift), 9a7157b. People's other drops stay; the nav prefers the vents |
| C5 | MOVE-02 / INTER-LIFT-03: carriers take lifts and cannons only when a teammate holds the exit; the code's carriers deliver alone (Spire's core, CTF runners up Construct's lifts; the player's list flagged runners waiting 80 s at a lift) | Carriers obey the held-exit rule like everyone else (walk round, or wait 6 s at most), with no teammate needed. Assumption A2 |
| C6 | INTER-LIFT-01 is not tier-gated; the player's Easy rule: Easy never plans a detour | Easy rides into a held exit (`exit_held` returns early for Easy) |
| C7 | MCMD-BAIT "Legendary only; carriers never"; guide 18 put no limit on the bait order | Not a contradiction, a stricter rule: added (0b5696f) |
| C8 | CALL-02 splits fields by tier (Normal where / what, Heroic adds health); the voice gives every caller from Normal up count, place and health ("Weak", "One shot"); Easy calls nothing, which matches | Left as is: the player tuned the voice by ear; the split is open (CALL-02 row) |
| C9 | MAP-02 / CALL-01 / MAP-14 want community callouts; outside CE the zone names are generated ("Blue side" on Sandtrap) | No mismatch today: bots, the coach's MAP line and the observer all read the same zone names. Community names are a data job per map (open) |
| C10 | The brains folder's README still lists four files | the player's file; not changed |

No other conflict found: the vehicle, objective and equipment brains name map data (hold spots, lanes, power positions,
return routes) the map brain defines, and the code already feeds them from the files above.

## Part 0. How the map layer plugs in

| Rule | Status | Note | Where |
|---|---|---|---|
| MAP-01 one pack per map per game | done | one folder per map per game, remakes separate | maps.load |
| MAP-02 nodes named with callouts | partial | every zone named; community names only for CE (docs/research/06, 09); aliases name a zone in the coach's orders (CALL-01) | callouts.ZoneMap, director.order_points |
| MAP-03 gametype overlays | partial | spawns and objective spots per game type; no per-mode lanes, power positions or interactable values | maps.load |
| MAP-04 interactables first-class | partial | kind and place painted per map; no trigger, effect, duration, who, cooldown or state | tools/map_features.py |
| MAP-05 templates re-ranked live | partial | ODD-CORE-01 partial, FF-POS-01 open (guide 19 audit); Slayer: the hunters go to the hot zone (seen in the last 20 s), the anchor's post is drawn by its score and twice as likely where it sees the hot zone | director.slayer_slots, hot_spot, test_director_map |

## Part 1. Interactables

| Rule | Status | Note | Where |
|---|---|---|---|
| INTER-CANNON-01 one-way edge, fixed landing | partial | people's cannon rides are one-way links with their landing; bots find launchers by exploring (lidar.Roomba); no vehicle landing for weight-based cannons | terrain.jump_ways |
| INTER-CANNON-02 never into a held landing | done | an enemy known within 10 m (3.3 u) of a flight's landing in the last 4 s, or with a sightline onto it from within 25 u: walk round or wait 6 s; Easy rides | Bot.exit_held, exit_watched, test_exit_held |
| INTER-CANNON-03 objective through the cannon | open | | |
| INTER-CANNON-04 grenades into a cannon | open | | |
| INTER-CANNON-05 pre-aim the landing | done | an enemy known in the last 0.5 s (seen, heard, radar) on a launch (a teleporter pad; a man cannon ride or a lift climb from people's links, with their airtime) whose landing is within 25 u and in sight: any Normal+ bot not fighting pre-aims the landing until 1.5 s after he is due (not only ring / anchor roles); being shot at comes first; Easy never. Blood Gulch: faced the exit in 1.4 s (never with the rule patched out) | Bot.arrival, Bot.launches, test_arrival |
| INTER-CANNON-06 vehicles through cannons | open | | |
| INTER-LIFT-01 never ride into a held exit | done | a man known in the last 4 s within 8 m (2.6 u) of the exit, or within 25 u with a line of sight onto it: the way round (the walk graph's, no more than 2.5 times as long) or wait 6 s; Easy rides | Bot.exit_held, exit_watched, test_exit_held |
| INTER-LIFT-02 grenade the exit on the lift sound | partial | no sound read; the stand-in is coded: a man seen or on radar stepping into a lift (any launch with airtime), Heroic and Legendary grenade its exit 0.8-2.5 s before he is due (Bot.arrival). The attacker's side: up a lift with nobody known, a Normal+ rider aims at the exit's cover (LiDAR's nearest cover spot 3-10 u off the landing that sees it), aimed, not fired | think (landing grenade), Bot.exit_cover, test_arrival 3 and 5 |
| INTER-LIFT-03 carriers only with the exit held | partial | carriers obey the held-exit rule; no teammate requirement (C5) | Bot.exit_held |
| INTER-LIFT-04 grenades ride lifts | open | | |
| INTER-TELE-01 instant edge, no ride into a held exit | done | the held exit: a route whose next 6 u end on a pad, with a man seen, heard, on radar or felt in the last 4 s within 3.3 u of its exit, or within 25 u with a line of sight onto it: the way round (the walk with every edge onto or off a pad's trigger costed as a wall, Terrain no_tele, no more than 2.5 times as long, walked 10 s while the goal stays put; Blood Gulch, a man at the exit: over the gulch instead), else it stops short of the pad, 6 s at most; Easy goes | Bot.pad_held, exit_watched, Terrain._field no_tele, test_tele_watch |
| INTER-TELE-02 vehicle parked by the teleporter for the flag | open | | |
| INTER-TELE-03 turn and pre-aim the way you came | done | out of a teleporter with a man seen or felt in the last 3 s nearer the pad it went in by: backs 2 u off the exit turned to it and watches it 3 s (a man seen since ends it); Easy and flag carriers go on. Blood Gulch sim: faced the exit 100% of 1-3 s, shot the chaser 0.13 s after he came out (never without the rule) | Bot.came_through, test_tele_watch |
| INTER-TELE-04 switch-activated teleporters | blocked | no switch read or press | |
| INTER-GATE-01 closed gate is a wall | blocked | the nav comes from the level mesh; gates are devices whose state is not read | |
| INTER-GATE-02 attackers open, defenders never | blocked | as GATE-01, plus no press on a control | |
| INTER-GATE-03 shoot-switches | blocked | no device state read | |
| INTER-GATE-04 close-switches | blocked | as GATE-03 | |
| INTER-GATE-05 hinges and blast covers | blocked | as GATE-03 | |
| INTER-GATE-06 toggle doors | blocked | as GATE-01 | |
| INTER-MOVE-01 train | blocked | Terminal's train is not read | |
| INTER-MOVE-02 wheel | blocked | the wheel's motion is not read | |
| INTER-MOVE-03 conveyors | blocked | belts not read | |
| INTER-FALL-01 stalactite targets | blocked | stalactite objects and their state not read | |
| INTER-FALL-02 no holds under an intact stalactite | blocked | as FALL-01 | |
| INTER-FALL-03 glass floor | blocked | as FALL-01 | |
| INTER-FALL-04 Sandtrap mines | open | the mine ring is not in the vehicle nav | |
| INTER-SHIELD-01 shield doors are melee doors | partial | Forge shield pieces block sight and shots, not movement (e9344c7); no melee lead | tools/test_forge_shields.py |
| INTER-SHIELD-02 Zenith shield | blocked | no switch press or shield state | |
| INTER-SHIELD-03 Shrine waterfall | blocked | no device state | |
| INTER-SHIELD-04 Bloodline EMP | blocked | no switch press | |
| INTER-SHIELD-05 Narrows energy bridge | open | | |
| INTER-LOWG-01 low-gravity jumps | open | | |
| INTER-LOWG-02 low-gravity exposure | open | | |
| INTER-VEH-01 vehicle spawns and timers | partial | spawns known and fetched; respawn timers not used for pre-positioning: objects.json has a vehicle's spawn_time on Halo 2, H2A, Halo 3 and Reach maps (not CE), but when its clock starts (destroyed, or driven off its spawn) is not verified, and nothing reports a vehicle gone the way items are (tools/live_bots.py) | objects.json |
| INTER-VEH-02 ram-safe roads per lane | open | | |
| INTER-VEH-03 vehicle access by gate state | blocked | as GATE-01 | |

## Part 2. Map control and callouts

| Rule | Status | Note | Where |
|---|---|---|---|
| MAP-06 power position score | partial | scored by height, floor seen, cover, escape, items near; the floor seen weighted by where people walked (LiDAR walk counts, 39 of 123 maps have some; their positions.json not regenerated yet); the director draws the anchor's post by the score; no vehicle-lane exposure; not per mode | tools/power_positions.py traffic, director.slayer_slots, test_director_map |
| MAP-07 hold spot score | partial | holds per team; no single-approach or stalactite / track penalty | tools/gen_zones.py |
| MAP-08 spawn zones and spawn pressure | partial | spawns stored per team and game type; with no fight to go to, the Slayer hunters go to the enemy spawn the director predicts: near the living enemies our bots know of (10 s), far from our men, none of us within 5 u or seeing it from within 40 u. Which positions push spawns where is not stored (no game spawn weights); SP-01 open (guide 19 audit) | director.spawn_guess, test_director_map |
| MAP-09 named lanes with vehicle_ok / carrier_safe_if | partial | lanes and sneak routes as points; a CTF carrier goes home by the lane the threat map rates quietest (pick_route, a sneak route the other way) and keeps it while home stays put; no names or conditions; generated maps' three lanes often lie in one zone (Construct, Panopticon: all Mid), where the threat cannot tell them apart | callouts.json, director.assign_roles, test_ctf_roles |
| MAP-10 hot zones per mode | partial | the director's threat per zone (seen, deaths; hot_spot: the hottest, seen in the last 20 s) drives the Slayer hunters and the anchor's post, and is the default sightline of every bot at a post with nobody known (Easy none); not per mode (no nodes the enemy must cross for the objective) | director.hot_spot, Bot.look_point, test_director_map |
| CALL-01 canonical callout plus aliases | partial | one name and a long name per zone; 677 of 1660 zones carry aliases ("aka", on 144 maps), and a coach order to an alias goes to its zone, the zone's own name first ("red roof" is Beaver Creek's "Top red"); no note of what spawns at a weapon-named node now | callouts.Zone, director.order_points, test_coach |
| CALL-02 enemy callouts: where, what, health, movement | partial | count, place, health; no weapon / vehicle or movement; no per-tier field split (C8) | director.text |
| CALL-03 self callouts | partial | a dead bot calls its killer ("Dead, he's ..."); no "I'm weak" or "carrier at" | director.text |
| CALL-04 predicted spawns | partial | the prediction is made (MAP-08) and sends the hunters, at every tier that takes team orders (as the old look toward their side did); no bot says it ("they'll spawn Green Box", Legendary only) | director.spawn_guess, test_director_map |
| CALL-05 interactable callouts | blocked | no interactable states to call | |
| CALL-06 timer callouts | partial | timers reach the coach ("up in N s (likely)"); bots do not voice them | director coach state |

## Part 3. Coach map commands (each through guide 18's schema, C1)

| Rule | Status | Note | Where |
|---|---|---|---|
| MCMD-GO | partial | push / hold to a callout (V4); no carrier-safe or emp-zone limits (no such data) | coach.validate |
| MCMD-HOLD | done | hold order plus anchor / guard roles; V9 keeps the mode's minimum role | coach.validate |
| MCMD-LANE | open | no named lanes | |
| MCMD-ROTATE | partial | rotate to a callout; no via-lane | coach.validate |
| MCMD-TRIGGER | blocked | no interactable state or press | |
| MCMD-AVOID | open | no coach path costs | |
| MCMD-WATCH | partial | watch order to a callout; no predicted-arrival event | coach.validate, director.VERB_ROLE |
| MCMD-TIMER | partial | an order's timer trigger moves 5 s before the item (V6); not capped by tier | coach.validate |
| MCMD-CALL | partial | callouts pass the text check (V16), not a node / timer / interactable parse | coach.validate |
| MCMD-DENY | done | deny order to the item's callout | coach.validate |
| MCMD-BAIT | done | Legendary only, never a carrier (0b5696f); the hazard is the coach's choice | coach.validate, test_coach |
| Snapshot additions (power positions held, interactables, hot nodes, timers, gate states, hazard cycle, lanes blocked) | partial | the state has callouts, timers, enemy sightings by zone; no interactable, gate or hazard lines (blocked with the reads) | director coach state |
| System-prompt addition | open | its plays need TRIGGER and the interactables; adding the text before they exist would invite orders the validator drops | coach.SYSTEM |

## Part 4. Per-game plays (58)

All map-specific plays are **open** as plays; where generic code already covers part of one, the note says so.

| Map | Plays | Generic coverage today |
|---|---|---|
| CE Blood Gulch | CE-BG-PLAY-01, 02 | Banshee crews fill anti-air first (PLAY-AIR-DENIAL partial); no teleporter shuttle |
| CE Hang 'Em High | CE-HEH-PLAY-01, 02 | rockets fetched by timer; no tunnel route choice |
| H2 Lockout / H2A Lockdown | H2-LOCK-PLAY-01, 02; H2A-LOCKDOWN-PLAY-01, 02 | power positions held; stalactites blocked |
| H2 Zanzibar / Last Resort | H2-ZAN-PLAY-01..03 | gate blocked; wheel blocked |
| H2 Relic / H2A Remnant | H2-REL-PLAY-01, 02 | switch blocked |
| H2 Ascension | H2-ASC-PLAY-01, 02 | Banshee crews; lift held-exit rule |
| H2A Zenith | H2A-ZEN-PLAY-01..03 | shield blocked |
| H2A Stonetown | H2A-STONE-PLAY-01, 02 | switches blocked |
| H2A Shrine | H2A-SHRINE-PLAY-01, 02 | waterfall blocked |
| H2A Bloodline | H2A-BLOOD-PLAY-01, 02 | EMP blocked |
| H2A Warlord | H2A-WARLORD-PLAY-01, 02 | teleporters walked; no exit watch |
| H3 Narrows | H3-NAR-PLAY-01..03 | held-exit rule on the cannons; no landing ambush |
| H3 Valhalla | H3-VAL-PLAY-01..03 | held-exit rule; no Power Drain in flight |
| H3 The Pit | H3-PIT-PLAY-01..03 | power positions; no named routes |
| H3 Guardian | H3-GUARD-PLAY-01..03 | held-exit rule on lifts and cannons |
| H3 Sandtrap | H3-SAND-PLAY-01..03 | bots ride the Elephants, take their flags (s136) and carry them in up the rear ramp to the flag return in the bay (8a9deab); no bomb run or road block |
| H3 Avalanche | H3-AVA-PLAY-01, 02 | held-exit rule on the base cannon; no escort-held check |
| Reach Spire | REACH-SPIRE-PLAY-01..03 | Falcon flown; no core carrier ferried (the core is carried as a turret, it cannot ride; the CTF ferry never ran in Invasion); off the top onto the heat vents (9a7157b); Falcon drops of attackers on the top: open |
| Reach Hemorrhage | REACH-HEM-PLAY-01..03 | vehicle roles; no cliff sniper post |
| H4 Ragnarok | H4-RAG-PLAY-01, 02 | Mantis and Banshee roles; no Laser-hill anchor |
| H4 Exile | H4-EXILE-PLAY-01, 02 | upright-only boarding (s134); no cave posts |

The guide's generic plays (PLAY-OUTSKIRTS-RUN, PLAY-CROSSMAP, PLAY-TIMER-DENY, PLAY-SPAWN-TRAP, PLAY-BREAKOUT,
PLAY-CHOPPER-LANE, PLAY-AIR-DENIAL) are guide 18's; their status is in `18-tiers-compliance.md`.

## Part 5. Build order and verification

| Rule | Status | Note |
|---|---|---|
| MAP-11 build order | partial | every map's files are generated from its own data (123 maps with learned links); the hand-made layer (names, lanes, interactable rules) is not started |
| MAP-12 timers and timer_rule | partial | the scenario's respawn time, else 60 s power-ups / 45 s weapons (unverified for CE); Halo 3 weapons 2 s longer from the pickup (their timer starts 2 s after the weapon is disturbed: maps.power_items, test_director_map 4); no game-clock vs after-pickup |
| MAP-13 verify list | partial | Spire's lifts verified by play (bots ride them, cores delivered-28); the rest not checked |
| MAP-13b Waterfall, Edge, Icebox | partial | Waterfall and Edge have map folders (`h3_s3d_waterfall`, `h3_s3d_edge`); no Icebox folder found |
| MAP-13c Part 6 inventory confirmed in Forge | open | |
| MAP-14 callout audit | open | |

## Part 6. Human movement (6.0) and the per-map inventory

| Rule | Status | Note | Where |
|---|---|---|---|
| MOVE-01 drops are routes, hot when held | done | people's drops are one-way links; a drop over 2 u into a known enemy is held (walk round or wait) | terrain.jump_ways, Bot.exit_held |
| MOVE-02 lifts and cannons with a cost | partial | used when cheapest, held when the exit is; carriers without the teammate rule (C5) | Bot.exit_held |
| MOVE-03 never walk off a death drop | done | edge guard on walk, strafe, juke and jump; carriers round big drops | Bot.edge_guard, test_edge_guard |
| MOVE-04 ladders (CE, Halo 2) | open | not checked whether any MCC CE or Halo 2 map has a climbable ladder |
| MOVE-05 jump edges per tier | partial | people's jumps for every bot (the player's rule, C3); computed jumps for jump-minded bots; no per-tier success rates |
| MOVE-06 switches are jobs | blocked | no switch press or state |
| MOVE-07 hazards as avoid and bait | blocked | hazard objects not read; bait limits done (MCMD-BAIT) |

Part 6.1-6.7's per-map inventories are data for the packs; the learned links already give every map its jumps, drops,
lift rides and cannon flights as people did them. The switches and hazards in those entries are blocked with the
INTER rows above.

## Per-game matrix (what works on each game's maps today)

| Feature | CE | H2 | H2A | H3 | Reach | H4 |
|---|---|---|---|---|---|---|
| people's jumps, drops, cannon flights | yes | yes | yes | yes | yes | yes |
| gravity lifts (ride_lift) | no lifts | yes | yes | yes | yes | yes |
| teleporters walked | yes | yes | yes (features) | yes | yes | yes (features) |
| held exits (exit_held) | yes | yes | yes | yes | yes | yes |
| interactable state (gates, switches, shields) | blocked | blocked | blocked | blocked | blocked | blocked |

## Counts

79 rule rows (16 framework MAP-01..14 with 13b and 13c, 37 interactable, 6 callout, 11 coach commands and the 2 coach
additions, 7 movement): done 11, partial 31, open 16, blocked 21 (counted from the tables by
`logs/tmp/count_status.py`, the matrix row left out). 58 map plays: open as plays, generic coverage named per map.

## Top gaps for live play

1. Interactable state reads (gates, switches, shields, hazards): 24 rows wait on them; the first to decode would be a
   device's position / power value (Zanzibar's gate, Zenith's shield switch).
2. Teleporters (INTER-TELE-01): a held exit stops the bot short of the pad or, where the walk is no more than 2.5 times as long, sends it the way round; not seen live yet.
3. Landing and lift-exit ambush (INTER-CANNON-05, INTER-LIFT-02): done (pre-aim, Heroic+ grenade); the lift's sound is not read.
4. Named lanes with conditions (MAP-09) for MCMD-LANE and carrier-safe returns.
5. Timer rules (MAP-12) and timer callouts from bots (CALL-06).
6. Community callout names for the most played maps (MAP-14).
