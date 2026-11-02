# Guide 18 compliance: difficulty tiers, the integration contract and the coach against the code

the player's guide `docs/research/18-tiers-integration-and-coach.md` (Fable: file 4 of the set) rule by rule.
Status: **done** (coded and tested offline, commit or test named), **partial** (what is missing is named), **open**
(not coded yet), **blocked** (what is missing to code it: a read, an input or a live test). Nothing in this file is
live-verified unless it says so. The guide's tier tables carry no row ids: they are numbered here in table order as
`TIER-<BRAIN>-NN`, the format the guide gives. Where a later the player instruction contradicts a table cell, the code follows
the player and the note says so. Rule ids from files 2 and 3 of the set (CTF-MULTI-05, EQP-04, SP-01 ...) are only
named here, not audited (docs/research/19, 20).

Tier names in the code (brain/profiles.py): Easy = novice, Normal = average, Heroic = strong, Legendary = top.

Updated (audit only, no code changed): HEAD 0880c6b; vehicle code as of the batches 0076364,
91e418a, c40d915, 1e16b43.

## Summary

- A tier is one Profile per bot (TIERS: hands, reaction, memory, radar, teamwork; CRAFT: jump, strafe, juke, routes,
  map_iq, tactics, aware; PERSONALITIES), each value jittered 0.9-1.1 once (make_profile). The on-foot brain, the director,
  the callouts and the equipment Kit read it. The vehicle brain reads only `reaction` and `juke` (Bot.evade) and `strafe`
  (Bot.drive): ram commit, the never-ram list, weak parts, target choice, crew coordination and boarding defense run at
  one level for every tier, which is about the table's Legendary row.
- The coach (brain/coach.py and Director.coach_*) is guide 10's (docs/bot-brain/10), not guide 18's: its own schema
  (play, phase, tempo pressure / neutral / stall, role_assignments, priorities, orders with ttl_seconds 5-20, callouts,
  coaching) and its own plays. It meets COACH-01, 02, 08, 10 and 12; COACH-03, 04, 05, 06, 07, 09 and 11 are partial:
  bounded authority yes but not in the guide's terms (no posture field, no target weights, no lanes, callouts dropped),
  ttl yes as answer expiry and order ttl but not a 20 s default, tier gating only for Easy (and Normal orders as
  suggestions), validation yes but an unknown play discards the whole answer. No vehicle hooks.
- No `PLAY-*` id exists in the code. 9 of the 23 have a near equivalent (a guide 10 play, a tempo, or a deterministic
  director behaviour the coach cannot call); 14 are open.
- Of the contract fields (1.2), role and vehicle_request are done under the code's own names; posture, goal,
  target_weights, fire_discipline, equipment_hint and callouts_in are partial; grenade_budget is open.

## Part 1. Integration contract

### 1.2 Fields the modules send to the on-foot brain

| Field | Status | Note | Evidence |
|---|---|---|---|
| `posture` | partial | a 0-1 value plus eleven score states (the player's score rules), not the four-value enum; Easy gets a fixed 0.5 | brain/match.py:posture, tempo; brain/director.py:Director.update; brain/bot.py:Bot.decide |
| `role` | done | Order.role: runner (carrier when holding), escort, defender, hunter, mid, free, plus ride, board, drive, ferry, driver_wait, give_seat; no SCORER / ANCHOR / ROTATOR names (the hill's defender, mid, hunter stand in) | brain/bot.py:Order; brain/director.py:Director.assign_roles, role_slots |
| `goal` | partial | Order.point plus via (an attack lane chosen by threat); no stance: HOLD / PUSH / FLANK / RETREAT / CAMP come from the role, personality and the bot's own retreat logic | brain/bot.py:Order, Bot.objective_point; brain/director.py:Director.pick_route |
| `target_weights` | partial | team shot (+30 threat on a teammate's target), vehicle target scoring's objective weights (carrier 2, hill 1.5, our flag 1.3), the Grenadier's +45 on vehicle crews; nothing above the bot sets a per-entity multiplier | brain/director.py:Director.update; brain/bot.py:Bot.threat, Bot.vehicle_pick; brain/vehicles.py:target_score |
| `fire_discipline` | partial | the carrier starts no fights, runners skip fights past 12 u, the VIP holds back, posture <= 0.3 fights only with the numbers (ADVANTAGE_ONLY in effect); no HOLD for camo stalkers; not a field the director sets | brain/bot.py:Bot.decide |
| `grenade_budget` | open | grenades are a personality trait and fight logic; no per-role budget between objective events | brain/profiles.py:PERSONALITIES |
| `vehicle_request` | done | director orders drive (by role), ride (the gun), board (a passenger seat), ferry (carrier pickup); the bot walks to the seat, the vehicle brain takes over seated | brain/director.py:Director.crew_orders, vehicle_orders, honk_orders; brain/bot.py:Bot.decide, Bot.think |
| `equipment_hint` | partial | each bot's trigger set comes from its tier ladder and its own situation; nothing per life from the objective brain | brain/equipment.py:level, Kit.plan |
| `callouts_in` | partial | heard calls become beliefs at the listener's tier timing, within its memory; Easy does not listen; kinds are sightings, cracked, one shot, deaths and the flag carrier: no enemy power weapon, enemy vehicle or predicted spawn | brain/director.py:Director.update, report; brain/callouts.py:TIMING; brain/bot.py:Perception.update |

### 1.3 Precedence

| Rule | Status | Note | Evidence |
|---|---|---|---|
| INT-01 carrier rule | partial | the carrier starts no fights, picks nothing up and runs home (objective score 3.0), the director keeps him a runner; the drop-and-fight exceptions (CTF-MULTI-05, ODD-CORE-04, ASS-MULTI-06) are not coded | brain/bot.py:Bot.decide; brain/director.py:Director.assign_roles |
| INT-02 survival rule | partial | losing-fight retreat to cover in reach (Easy fights in the open), held 7 s (guide 06), not 4 s; all_in lowers the cracked line to 5 % (the DESPERATE exception); the carrier is not exempt: retreat 2.5 + 0.5 tactics + 0.3 caution can beat his 3.0, so a cautious Heroic or Legendary carrier ducks to cover | brain/bot.py:Bot.decide |
| INT-03 vehicle handoff | partial | seated, Bot.drive owns the bot and the threat answers run before the trip; a role carries into the seat (crew patrol, ferry, driver_wait), but an ESCORT or other on-foot role does not change the driving | brain/bot.py:Bot.think, Bot.drive, Bot.evade |
| INT-04 equipment triggers | partial | the Kit plans and fires inside the bot's tick; never ram an Armor-Locked man: done; never Armor Lock in Infection: open (no mode check); never fire from camo unless the first burst kills: open | brain/equipment.py:Kit.plan, Kit.act; brain/bot.py:Bot.ram_ok |
| INT-05 weights are multipliers | partial | the weights that exist multiply the bot's own scoring, and a target its gun cannot hurt scores 0 (no shot); there is no weights channel to bound | brain/vehicles.py:target_score; brain/bot.py:Bot.vehicle_pick, Bot.threat |
| INT-06 posture caps aggression, not skill | done | posture changes fight acceptance, the cracked line and objective scores; reaction, aim, strafe and jumps read only TIERS and CRAFT | brain/bot.py:Bot.decide, Aim.step; brain/profiles.py:TIERS, CRAFT |
| INT-07 coach never reaches the on-foot brain | done | an answer is validated, then becomes the director's plan, tempo, roles and orders (Order through set_order); nothing touches aim, reaction or survival | brain/coach.py:validate; brain/director.py:Director.coach_apply, coach_posture, coach_ordered |
| INT-08 tick rates | partial | on-foot every tick, decide every ~0.1 s; vehicle every tick seated; equipment every tick; objective brain (roles) every 2 s (guide 0.5 s); coach every 5-30 s by match state (guide 15-30 s) | brain/bot.py:Bot.think; brain/director.py:Director.update, coach_period |

### 1.4 Posture onto the on-foot settings

| Posture | Status | Note | Evidence |
|---|---|---|---|
| AGGRESSIVE | partial | posture 0.7-0.9 (behind, far behind, tempo push) lowers the cracked line and favours the overshield; sprinting between covers and shorter peeks are not posture-driven | brain/bot.py:Bot.decide, Bot.best_item |
| BALANCED | done | 0.5: the tier's own settings | brain/match.py:posture |
| CONSERVATIVE | partial | posture <= 0.3 fights only with the numbers and backs off at up to 45 % shields; "saves one grenade for defense" and "relocates only to deny timers": open | brain/bot.py:Bot.decide |
| DESPERATE | partial | all_in (last minute behind, 0.9) nearly removes the back-off; straight lines to the objective are not posture-driven | brain/match.py:posture; brain/bot.py:Bot.decide |

## Part 2. Tier tables

### 2.1 Vehicle brain

| Row | Status | Note | Evidence |
|---|---|---|---|
| TIER-VEH-01 reaction to vehicle threats | partial | the tier's reaction (0.275 / 0.22 / 0.19 / 0.15 s), then one roll of the on-foot juke trait per threat: Easy never answers (table: misses half), Normal 1 in 10 (table: misses rare cues), Heroic 6 in 10 (table: all); no 0.3 s barrel prediction; lock tone and EMP glow not readable | brain/bot.py:Bot.evade; brain/profiles.py:REACTION, CRAFT |
| TIER-VEH-02 ram commit precision | partial | the ram is done (guide 17 §4.3: 18 u, RAM_THETA by kind, lead, abort, post-hit); commit distance and heading error do not vary by tier | brain/bot.py:Bot.ram_ok, Bot.drive; brain/vehicles.py:RAM_THETA |
| TIER-VEH-03 never-ram list | partial | every tier respects tanks, the Elephant, the Mantis and Armor Lock (the Legendary row); Easy's 30 % slip and Normal forgetting Armor Lock are not modelled; the lock's glow: away inside 1.5 u, juke-gated | brain/bot.py:Bot.ram_ok, Bot.evade; brain/vehicles.py:RAM_VEHICLES |
| TIER-VEH-04 gunnery lead on slow projectiles | partial | every seat leads by its gun's flight with one lead factor for every tier (HANDS 0.8 x 0.6-1.2: about 28 % short on average); tiered error and walked bursts not coded: the player's equal-hands rule against the table, the player to decide | brain/bot.py:Aim.step; brain/vehicles.py:gunner_gun, STRATEGY |
| TIER-VEH-05 weak-part aiming | partial | explosive and gauss shots go to a tank's back hatch from behind at every tier (the Legendary row); the Ghost's gas tank and the Warthog's glass: open (guide 17) | brain/bot.py:Bot.weak_point |
| TIER-VEH-06 boarding (attacker) | blocked | bots enter only empty vehicles or a teammate's (the Easy row, for every tier); Reach's boarding seats are listed (reach_seats.json "boarding enters seat"), the enter-seat interaction on an enemy vehicle needs one live test; EMP first: no EMP'd-state read | brain/bot.py:Bot.think; brain/vehicles.py:reach_seat |
| TIER-VEH-07 boarding defense (driver) | partial | tanks and the Revenant back off a man inside 6 u at every tier (Easy too; table: Easy does not react); light vehicles and aircraft go full throttle away from a man on foot inside the boarding radius (2 u, 3.3 u in the air; in view or a radar dot under 1 s) after the tier's reaction, by the juke roll: Easy never, Normal 1 in 10 ("if it notices"), Heroic 6 in 10, Legendary always (test_vehicle_threats 11); the gunner on boarders, Reach counter-board: open | brain/bot.py:Bot.evade, Bot.drive, Bot.ram_ok; brain/vehicles.py:BOARD_D |
| TIER-VEH-08 retreat and abandon thresholds | blocked | no hull read (guide 17 §4.1): the hull thresholds are not coded; guide 17's driver_shield_down retreat is (Halo 2 / 3: a broken shield and a man in view, to the nearest teammate or base 4 s at a time), Normal and up, Easy fights to the death in the seat | brain/bot.py:Bot.drive |
| TIER-VEH-09 vehicle selection | partial | Easy: its own pick by value and nearness for trips past 35 u (the Easy row); Normal to Legendary: the team's picks by role (§4.7) on their teamwork roll (Normal 0.55); counter-vehicle awareness (VC-02): open, the role order is fixed | brain/bot.py:Bot.decide; brain/vehicles.py:ride_score, ROLE_ORDER; brain/director.py:Director.crew_orders |
| TIER-VEH-10 blind spots | open | the overhead cone and the Chopper's rear only lower our own shot's score; no vehicle notices, avoids or denies its blind spot | brain/vehicles.py:target_score |
| TIER-VEH-11 boost timing | blocked | no vehicle boost input decoded | (none) |
| TIER-VEH-12 crew coordination | partial | full §4.5 coordination at every tier (the gunner's view target, the Falcon's manned side, the Warthog circle, passengers hold fire while carrying); no tier scaling; target-lost / reloading reports: open | brain/bot.py:Bot.crew_target, Bot.drive |
| TIER-VEH-13 splatter target choice | partial | an armed vehicle runs down the man its target score picks (carrier first), an unarmed one the nearest, at every tier; "not near a tank", the power-weapon holder, spawn-flip avoidance: open | brain/bot.py:Bot.drive, Bot.vehicle_pick |
| TIER-VEH-14 air | partial | attack runs low, travel high, a dive out of a rocket's line, a climb over a tank barrel, a Falcon or Hornet breaking off from a Banshee (juke-gated), at every tier; trick rolls (no lock read), rear-quarter attacks, tank bombing (bomb input blocked): open | brain/bot.py:Bot.drive, Bot.evade, Bot.air_terrain |

### 2.2 Objective brain

| Row | Status | Note | Evidence |
|---|---|---|---|
| TIER-OBJ-01 posture engine | partial | Easy: fixed 0.5 (done); Normal, Heroic and Legendary get the same full engine with the pace projection; Normal's "ignore time until the last 60 s" not gated | brain/director.py:Director.update; brain/match.py:posture, tempo |
| TIER-OBJ-02 roles | partial | Easy: a runner at the objective or free (done); every other tier fills every slot (Normal on its teamwork roll); reassigned every 2 s for all (Legendary: 0.5 s); no ROTATOR (hunter stands in) | brain/director.py:Director.assign_roles, role_slots, straight_objective |
| TIER-OBJ-03 power-weapon and power-up timers (PW-01) | partial | Easy: only what it sees on its way (done); timer error sd 8 (1 - map_iq) + 1 s (Normal ~6.6, Heroic ~3.4, Legendary ~1); it goes so the item is up on arrival; 10 s early and denial: open | brain/bot.py:Bot.best_item |
| TIER-OBJ-04 spawn control (SP-01) | open | likely_enemy looks toward their side (guide 06) at every non-Easy tier; no spawn weights, no spawn-flip avoidance | brain/director.py:Director.likely_enemy |
| TIER-OBJ-05 carrier memory | partial | memory 4 / 6 / 8 / 10 s by tier (done); the team report keeps a carrier past it; Legendary route prediction: open | brain/profiles.py:TIERS; brain/bot.py:Perception.update; brain/director.py:Director.enemy_rows |
| TIER-OBJ-06 callouts | partial | Easy calls nothing (done); call rate and timing by tier (p_call 0.65 / 0.85 / 0.95); no vehicle, power-weapon, predicted-spawn calls at any tier | brain/director.py:Director.report; brain/callouts.py:TIMING |
| TIER-OBJ-07 time-low branches | partial | Easy never (done); all_in / hide_and_hold (last minute) and tempo_push / close_out (pace) for every other tier; Normal's last-60-s-only and Legendary-only enemy pace not gated | brain/match.py:posture, tempo |
| TIER-OBJ-08 lives-limited (Elimination) | open | no lives read, no SLAY-ELIM formation | (none) |
| TIER-OBJ-09 hill / territory discipline | partial | Easy runs into the hill (done); every other tier: one on the hill, the rest on overlooks (the Heroic row; Normal's two in the hill not gated); Legendary's vehicle anchor and grenade-timed pushes: open | brain/director.py:Director.role_slots, straight_objective |
| TIER-OBJ-10 setups and traps | partial | power positions, overlooks, guard spots and the coach's holds at every non-Easy tier (not gated); breakout rushes and cross-map rotations: open | brain/director.py:Director.power_spots, guard_spots, slayer_slots |
| TIER-OBJ-11 map knowledge | done | CRAFT routes 0 / 0.3 / 0.7 / 1.0 and map_iq; Easy runs straight at the objective | brain/profiles.py:CRAFT; brain/director.py:Director.straight_objective |
| TIER-OBJ-12 coach availability | partial | Easy-only teams: no coach (done); Normal bots' orders are suggestions (V13) but a Normal team still gets plays (table: reminders only); Heroic plays (done); the tendency log is not Legendary-only | brain/director.py:Director.coach_on, match_line; brain/coach.py:validate |

### 2.3 Equipment brain

| Row | Status | Note | Evidence |
|---|---|---|---|
| TIER-EQP-01 pickup timing (EQP-04) | partial | Easy takes only what it walks past (done); the others go so it is up on arrival, with the tier's timing error; pre-positioning (Heroic) and 5 s early / denial (Legendary): open | brain/bot.py:Bot.best_item |
| TIER-EQP-02 pickup routing (EQP-06) | partial | per bot: speed boost for a runner, camo for flankers and snipers, the overshield by posture; nothing routes an overshield to the carrier; Easy keeps whatever (done) | brain/bot.py:Bot.best_item |
| TIER-EQP-03 triggers enabled | done | the tier ladder: Normal use-now, Heroic plus hold, bait and grenade counters (at the lock's end), Legendary plus sneaky uses (grav lift under him); Easy uses none by the player's rule (table: 1-2 basic triggers) | brain/equipment.py:level, Kit.plan, Kit.grenade_spot |
| TIER-EQP-04 hologram detection (EQ-HOLO-05) | blocked | simulator: Easy and Normal shoot every decoy, Heroic and Legendary hold after 1.5 s of straight running; live, holograms are not in the player list, so no tier sees one: needs a hologram object read; Legendary's corner watch: open | brain/equipment.py:Kit.decoy_suspect; tools/live_bots.py:main (decoys_listed) |
| TIER-EQP-05 camo detection | partial | the same at every tier: camo seen 10 % of the time past 4 u, the Reach / Halo 4 radar jam tell; Promethean Vision use by the ladder | brain/bot.py:Perception.update; brain/equipment.py:Kit.perceive, Kit.plan |
| TIER-EQP-06 Armor Lock use | partial | Easy none; Normal up: rockets and lasers aimed, a vehicle about to hit, lunges, Normal also at shield down; Legendary lets go beside a meleeing enemy; stuck-grenade trigger, EMP exit timing, body-blocks: open | brain/equipment.py:Kit.plan, Kit.act |
| TIER-EQP-07 Halo 4 loadout packages | partial | Easy never changes (default loadout); the others switch after 3 / 2 / 1 deaths of one kind to the slot that answers it; role loadouts (EQ-PKG-01), posture and ordnance order: open | brain/loadouts.py |

### 2.4 Firefight brain

| Row | Status | Note | Evidence |
|---|---|---|---|
| TIER-FF-01 hold position (FF-POS-01) | partial | Easy plays alone (no orders); every other tier escorts the nearest person; roofed, high, single-approach holds and a second hold: open | brain/director.py:Director.role_slots, assign_roles |
| TIER-FF-02 lives management (FF-LIFE-01) | open | no lives read | (none) |
| TIER-FF-03 wave reading (FF-WAVE-01) | open | no drop composition read | (none) |
| TIER-FF-04 three-enemy pacing (FF-WAVE-02) | open | every tier kills everything (the Easy / Normal row) | (none) |
| TIER-FF-05 enemy procedures | open | the AI is fought as players (its bipeds read as player-like dicts); no Grunt / Jackal / Hunter / Engineer procedures | brain/live.py:LiveReach.ai_units |
| TIER-FF-06 vehicle hijacks | blocked | hijacking needs boarding (TIER-VEH-06); a parked vehicle is taken by ride_score at any tier | brain/bot.py:Bot.decide |
| TIER-FF-07 skull adaptation (FF-WAVE-05) | open | no skull read | (none) |

### 2.5 Mixed and variance

| Rule | Status | Note | Evidence |
|---|---|---|---|
| TIER-MIX-01 rotation and pinning | done | Mixed deals Heroic, Normal, Legendary, Easy in turn ("strong,average,top,novice"), a tier on the BOTS list wins; one Profile feeds every brain, so a bot's module tier is its on-foot tier | tools/botctl.py:DIFFICULTY_TIERS; tools/live_bots.py:main; brain/profiles.py:make_profile |
| TIER-MIX-02 per-bot variance | partial | every profile value x 0.9-1.1 once when the bot joins (kept through deaths); the vehicle and director numbers (18 u ram reach, RAM_THETA, BOARD_D, evade windows, CREW_REACH) are shared constants | brain/profiles.py:make_profile; brain/vehicles.py; brain/bot.py:Bot.ram_ok |
| TIER-MIX-03 team brain at the highest living tier | partial | the director has no team tier: a team with one non-Easy bot gets the full posture, roles, timers and coach; each bot executes at its own tier; Easy bots are left out (done) | brain/director.py:Director.update, assign_roles, coach_on |

## Part 3. Personalities

The code has seven play styles (rusher, camper, flanker, objector, spammer, grudger, sniper); the guide maps four of
them and adds four. The spammer is the Grenadier, the only style with a vehicle job (Bot.vehicle_mission).

| Personality | Status | Note | Evidence |
|---|---|---|---|
| Rusher | partial | objective: its aggression fit takes runner, hunter and escort slots, and it makes the commander aggressive; vehicle bias (Ghost, Chopper, Mongoose, ram x1.5, retreat x0.7), its equipment list and Firefight CLEANER: open | brain/director.py:Director.assign_roles, role_slots; brain/coach.py:STYLE_OF |
| Camper | partial | the camping fit on defender and hold slots, cover posts near the flag, camo for the approach; tanks / Gauss and parking, its item list (cover, trip mine, sentry, drop shield, regenerator), Firefight ANCHOR: open | brain/director.py:Director.role_slots; brain/bot.py:Bot.decide; brain/equipment.py:Kit.plan |
| Flanker | partial | camo pickups and camo ambushes; Ghost / Hornet and rear-quarter approaches, ESCORT / ROTATOR / Neutral Flag preference, jammer / hologram / jetpack preference, Firefight PP: open | brain/bot.py:Bot.best_item; brain/equipment.py:Kit.plan |
| Sniper | partial | camo pickups, camping; the coach's sniper role prefers a mid slot; Banshee / Gauss seat preference, RING, long-lane ANCHOR, KOTH sniper: open | brain/bot.py:Bot.best_item; brain/director.py:ROLE_FIT |
| Driver (new) | open | not in PERSONALITIES; vehicles are crewed by distance | brain/profiles.py:PERSONALITIES; brain/director.py:Director.crew_orders |
| Pilot (new) | open | not in PERSONALITIES | brain/profiles.py:PERSONALITIES |
| Tanker (new) | open | not in PERSONALITIES | brain/profiles.py:PERSONALITIES |
| Support (new) | open | not in PERSONALITIES; gun seats go to the nearest free bot, not a preference | brain/profiles.py:PERSONALITIES; brain/director.py:Director.vehicle_orders |

## Part 4. The coach

### COACH-01 to COACH-12

| Rule | Status | Note | Evidence |
|---|---|---|---|
| COACH-01 advisory only | done | answers pass the validator, then reach the bots only as the director's plan, tempo, roles and orders; posture moves only through tempo within the score rules; no aim, reaction or survival field | brain/coach.py:validate; brain/director.py:Director.coach_apply, coach_posture |
| COACH-02 optional at every level | done | off, offline, slow or silent: the director plays its own plans; requests run on a thread, one in flight per team, nothing waits; warm-up retried every 30 s | brain/coach.py:Coach.ask, Coach._warm, Coach.ready; brain/director.py:Director.coach_on |
| COACH-03 cadence | partial | first ask at 5 s (staggered by team), then 30 / 20 / 10 / 5 s by plan age, events, the lead and the match end, at once on a big moment (objective event, phase, near wipe, lead change); not by tier (20 / 30 / 60 s / never); no power-weapon-in-15-s, vehicle-spawn or lives-under-3 triggers; advice lasts two periods, orders 5-20 s, not a 20 s default | brain/director.py:Director.coach_period, coach_ask, big_moment, coach_apply |
| COACH-04 bounded authority | partial | tempo moves the team posture (pressure >= 0.7, stall <= 0.25, priorities +-0.15), never inside the player's hard score states; roles for live bots only (V3), at most 3 changes a minute (V10); plays from the offered list (V2); orders to callouts (V4) within a 20 s run (V7); missing: the one-step posture limit, target-weight overrides, lanes, applying callouts (validated, then dropped); an unknown play, R2, staleness or more than two tripped rules discard the whole answer | brain/coach.py:validate; brain/director.py:Director.coach_posture, coach_apply |
| COACH-05 analyst memory | partial | every report carries MATCH SO FAR (score each minute, pace, where we die and kill, where the enemy is seen most, each bot's record, each play's results) and the COMMAND LOG; not the guide's tendency lines (first power weapon, vehicle lane, tower camping, early rotation, base door) | brain/director.py:Director.match_line, command_lines, state_doc |
| COACH-06 tier gating | partial | Easy-only teams: no coach (done); Easy bots on a mixed team take no orders (done); Normal orders are suggestions (V13) but a Normal team still gets plays and roles (guide: reminders only); tendencies not Legendary-only; Mixed not served at the highest living tier | brain/director.py:Director.coach_on, assign_roles; brain/coach.py:validate; tools/live_bots.py:main |
| COACH-07 validation | partial | jsonschema on every answer (V1), Ollama's `format` holds it to the schema, roles are an enum, order targets must be callouts or the mode's objectives (V4, the guide's lanes), every drop logged with its reason; an unknown play discards the whole answer (guide: ignored) | brain/coach.py:SCHEMA, validate; brain/director.py:Director.coach_take |
| COACH-08 latency tolerance | done | one request in flight per team, so no reply can follow a newer snapshot; an answer older than two periods (at least 15 s) or across a phase change is dropped (V15); timeout twice the median, 4-25 s | brain/coach.py:validate, Coach._ask, Coach.ready |
| COACH-09 model-agnostic, low temperature | partial | any Ollama model (default qwen2.5-coder:14b, fallback qwen3:4b), schema-constrained; temperature by the commander's style 0.25 / 0.3 / 0.3 / 0.5: the aggressive 0.5 is above the guide's 0.4 | brain/coach.py:STYLES, Coach.ask; brain/director.py:Director.coach_ask |
| COACH-10 kill switch | done | coach=off on the BOTS panel (also off in free for all and Firefight); three failures in a row rest that team's coach 60 s or switch every commander to the small model, then it retries (softer than the guide's off) | tools/live_bots.py:main; brain/coach.py:Coach._result |
| COACH-11 scoring the coach | partial | every sent, applied and discarded answer logged in full with reasons; each play's runs, seconds, kills, deaths and score change tallied and fed back each ask; no 30 s result window, no cross-match down-weighting | brain/director.py:Director.command_close, match_line, coach_take; tools/live_bots.py:coach_report |
| COACH-12 determinism for testing | done | coach off: the director's own plans, every bot and director on a seeded RNG (the simulator is reproducible); offline tests of V1-V16, the score rules and the link against a fake Ollama | brain/sim.py:Sim; tools/test_coach.py |

### 4.4 What the coach must never do

| Rule | Status | Note | Evidence |
|---|---|---|---|
| change aim, reaction, strafe, jumps, tracker, memory | done | no such field in the schema | brain/coach.py:SCHEMA |
| DESPERATE unless the engine already says AGGRESSIVE / DESPERATE | done | the coach's tempo tops out at 0.7; all_in comes only from the score rules, which the coach cannot move | brain/director.py:Director.coach_posture, HARD_STATES |
| a ram on a tank, Wraith, Elephant or Armor-Locked man | done | no ram or vehicle verb in ORDERS; Bot.ram_ok refuses them anyway | brain/coach.py:ORDERS; brain/bot.py:Bot.ram_ok |
| a carrier ordered to fight, drop the objective, take a forbidden seat | done | the carrier is taken out before orders apply and always runs home; returners keep their job (V9) | brain/director.py:Director.assign_roles; brain/coach.py:validate |
| Armor Lock in Infection, a splatter on Armor Lock, a hologram shot | done | no equipment or target verbs; orders naming an enemy are dropped (V5) | brain/coach.py:ORDERS, validate |
| more than one SCORER or CARRIER, zero DISARMERS after a plant | partial | the coach's contest_hill puts the whole team in the hill (more than one scorer); Assault is not coached, so no disarmer rule exists | brain/director.py:Director.role_slots, COACH_UNKNOWN |
| positions not in the map's node list | done | order targets must be a callout or the mode's objective (V4) | brain/coach.py:validate |

### Other coach sections

| Section | Status | Note | Evidence |
|---|---|---|---|
| 4.2 transport (snapshot, advice) | partial | guide 10's text report (callouts, roster with tiers, score, timers, enemy beliefs, events, match so far) and answer schema; no JSON snapshot, no vehicles, no allowed lanes, no ttl / posture / lanes / target_weights in the answer | brain/director.py:Director.state_doc; brain/coach.py:SCHEMA |
| 4.3 what the coach is good for, by brain | partial | objective brain: plays, tempo, roles, timer-triggered orders (V6); vehicle, equipment, Firefight brains: nothing (no lines in the report; Firefight, Invasion, Assault, Territories not coached) | brain/director.py:Director.state_doc, coach_ask, COACH_UNKNOWN |
| 4.5 system prompt | partial | guide 10's prompt with a per-mode addendum, the commander's name and style, two examples on this map's callouts: objective focus, timers, plays, roles, tempo; the never-ram / Armor Lock / DESPERATE lines are absent (those limits are structural) | brain/coach.py:SYSTEM, ADDENDA, system_prompt |
| 4.7 opponent tendencies | partial | MATCH SO FAR shows where the enemy keeps turning up and how each play went; none of the eleven tendency lines or their responses | brain/director.py:Director.match_line |

### Playbook: the PLAY-* ids

No `PLAY-*` id exists in the code. The coach's plays are guide 10's (brain/coach.py PLAYS): Slayer hold_setup,
push_pairs, rotate_power_weapon, reset_and_recharge, collapse_on_target; CTF pull_flag, defend_flag,
collapse_on_carrier, escort_carrier, return_flag, reset_and_recharge; King contest_hill, cover_hill,
reset_and_recharge; Oddball take_ball, guard_carrier, hunt_carrier, reset_and_recharge.

| Play | Status | Nearest in the code | Evidence |
|---|---|---|---|
| PLAY-BREAKOUT | open | rotate_power_weapon (two to an item due within 30 s); no opening one-bot-per-item rush | brain/coach.py:PLAYS |
| PLAY-SETUP | partial | hold_setup, cover_hill, defend_flag | brain/coach.py:PLAYS; brain/director.py:Director.slayer_slots, role_slots |
| PLAY-SPAWN-TRAP | open | none | (none) |
| PLAY-TIMER-DENY | partial | rotate_power_weapon plus an order's timer trigger (V6: moves 5 s before the item); no take-and-leave denial | brain/coach.py:validate |
| PLAY-SNIPER-HOLD | open | the sniper role (a mid slot); no spawn-exit lane hold | brain/director.py:ROLE_FIT |
| PLAY-CROSSMAP | open | the rotate verb sends one bot as a hunter; no team rotation to flip spawns | brain/director.py:VERB_ROLE |
| PLAY-TEMPO-SLOW | partial | tempo stall | brain/director.py:Director.coach_posture |
| PLAY-TEMPO-FAST | partial | tempo pressure with push_pairs / collapse_on_target / contest_hill | brain/director.py:Director.coach_posture |
| PLAY-OUTSKIRTS-RUN | partial | pull_flag / escort_carrier on the director's lane pick by threat; the coach cannot choose the lane | brain/director.py:Director.pick_route |
| PLAY-ESCORT-HOG | partial | the director's ferry (a driver with a free seat picks up our carrier on foot); not callable by the coach | brain/director.py:Director.vehicle_orders |
| PLAY-AIR-DENIAL | partial | the crew order fills an anti-air vehicle first; not callable, not tied to an enemy aircraft | brain/director.py:Director.crew_orders |
| PLAY-TANK-FIRST | partial | the Grenadier's anti-vehicle mission; not callable | brain/bot.py:Bot.vehicle_mission |
| PLAY-CHOPPER-LANE | open | none | (none) |
| PLAY-VEHICLE-BAIT | open | none | (none) |
| PLAY-HILL-SNIPE-THEN-PUSH | partial | contest_hill (all into the hill); no snipe-first step | brain/coach.py:PLAYS |
| PLAY-ROTATE-EARLY | open | none | (none) |
| PLAY-BOMB-SIEGE | open | Assault is not coached | brain/director.py:COACH_UNKNOWN |
| PLAY-STACK-DISARM | open | Assault is not coached | brain/director.py:COACH_UNKNOWN |
| PLAY-ONE-FLIP | open | Territories is not coached | brain/director.py:COACH_UNKNOWN |
| PLAY-LASTMAN-STALL | open | none | (none) |
| PLAY-FF-PACE | open | Firefight is not coached | brain/director.py:Director.coach_ask |
| PLAY-FF-HUNTER | open | Firefight is not coached | brain/director.py:Director.coach_ask |
| PLAY-FF-ROOF | open | Firefight is not coached | brain/director.py:Director.coach_ask |

## Top 12 gaps for live play

What a player would notice first, each with the change that closes it. The vehicle items assume the batches
work live (not verified yet: guide 17 compliance, the player's live observations).

1. **Easy and Normal drivers drive like Legendary.** Every vehicle decision except the dodge and the circle strafe ignores
   the tier: ram commit (18 u, RAM_THETA), the never-ram list, hatch shots, splatter and gun target choice, crew arcs.
   Change: brain/profiles.py gains a `VCRAFT` table per tier as new Profile fields (so make_profile's 0.9-1.1 applies,
   TIER-MIX-02): `ram_far` (u, the table's lengths at about 3 u each: Easy 9-12, Normal 6-9, Heroic 4.5-6, Legendary 3-6), `ram_err`
   (degrees 30 / 20 / 12 / 8), `ram_slip` (0.3 / 0.1 / 0 / 0), `weak_part` (0 / 0.3 / 0.7 / 1.0), `pick` (0-3). Bot.ram_ok
   commits only inside `s.p.ram_far` and skips the tank and Armor Lock refusals on a `ram_slip` roll (Normal: the Armor
   Lock one only); Bot.drive's splatter branch adds a per-run heading error drawn from `ram_err` to `way`; Bot.weak_point
   returns `b.pos` unless a `weak_part` roll passes (Normal only on a still target); Bot.vehicle_pick: Easy nearest,
   Normal nearest not within 10 u of an enemy tank, Heroic carrier then power-weapon holder then nearest, Legendary the
   full target_score; Easy gunners take the nearest man (Bot.crew_target). One case per tier in tools/test_vehicle_targets.py.
2. **Vehicles are left parked.** A bot takes one on its own only for a goal past VEHICLE_TRIP (35 u) with the vehicle
   inside about 14-21 u by its value (ride_score falls to 0 at 25 u); the team sends only bots with no runner or defender
   job, Normal turns down 45 % of the team's picks, Easy gets none. Change: Bot.decide uses a tier VEHICLE_TRIP (Heroic
   25 u, Legendary 20 u) and ride_score's falloff `25.0 + 15.0 * map_iq`; Director.crew_orders lets a CTF runner whose
   route is over 60 u take the transport (the ferry then runs him home); then a live check on a vehicle map with
   logs/tmp/drive_report.py.
3. **Bots never board or hijack.** Bot.think enters only empty vehicles or our team's, so a camped Scorpion or a slow
   enemy Warthog is never taken. Change: Bot.decide adds a board-enemy goal for Normal (driver under 0.5 u/s), Heroic
   (under 3 u/s) and Legendary (any; plasma pistol overcharge first when held, Halo 3 on) within 8 u with the bot behind
   the vehicle's beam; Bot.think walks to the side or rear seat point and presses Use with Reach's boarding seat (a new
   `vehicles.reach_board_seat(kind)` from the "boarding seat" flag in maps/_shapes/reach_seats.json), plain Use in Halo 2
   and 3; then the one live Reach test guide 17's boarding row is blocked on.
4. **Gunners go quiet.** A gunner fires only at a man its own eyes recognized whose score is above 0; with nobody in its
   sight it idles (only the Warthog chaingun stays spun up); a gun seat is filled only by a jobless bot within 25 u on its
   teamwork roll, never Easy; the Falcon fixes (0076364) are not live-verified. Change: Bot.drive's gunner branch, with
   no target, aims at the freshest team belief (callout or radar, under 2 s, in line of sight of the seat) and keeps
   every chaingun seat spun up on it, else watches the vehicle's travel arc; Director.vehicle_orders' 25 u becomes 35 u
   and the order is `sure=True` when a person drives; live check with logs/tmp/falcon_seats.py.
5. **Vehicles barely dodge below Legendary.** Bot.evade rolls the on-foot juke trait: Normal answers 1 rocket or tank
   barrel in 10, Heroic 6 in 10, Easy none (guide: Normal misses only rare cues, Heroic none, Easy half). Change: a `vcue`
   field in VCRAFT (0.5 / 0.9 / 1.0 / 1.0, the EMP cue 0.5 for Normal) replaces `s.p.juke` in Bot.evade's roll;
   Legendary answers a barrel 0.3 s early when it is within 20 degrees and turning toward us (its yaw change since the
   last tick).
6. **Vehicles fight to the death.** No retreat or bail at any tier (the hull read is blocked). Change: now, without the
   hull, guide 17 §4.1's `driver_shield_down` retreat for Halo 2 and 3 (the driver's shield is read): Bot.drive heads for
   the nearest teammate or our base out of the threat's line, Normal up (Easy ignores it); after one live read of a
   vehicle's body damage into the snapshot (`hull`), the retreat (0.40 armed, 0.60 transport, 0.25 Chopper) and abandon
   (0.15) thresholds by tier, and Legendary's "smoking plus explosive incoming" exit through exit_until.
7. **Bot vehicles are easy to board and to flank.** Only tanks and the Revenant back off a man on foot, at every tier
   (Easy too); a Warthog, Ghost or Banshee lets a player walk up, and no vehicle guards its blind spot. Change: Bot.drive,
   every ground kind: a man on foot inside the boarding radius (guide 17: 6 m ground = 2 u, 10 m air = 3.3 u) gets
   Normal full throttle away, Heroic the gunner's first target (crew_target) and a turn away, Legendary the Reach
   counter-board (exit, re-board) when its gunner is dead, Easy nothing; the artillery back-off gated Normal up; tanks
   (Heroic up) turn or back off to keep the nearest man out of the 50-degree overhead cone and the rear.
8. **Enemy vehicles go unanswered.** The team's picks follow a fixed order (anti-air first with no enemy aircraft up), no
   bot calls out an enemy vehicle, and only the Grenadier hunts one, so a player in a Banshee or a Scorpion is rarely
   countered. Change: Director.crew_orders reads the enemy kinds the team knows (riders in its beliefs) and orders the
   roles by them: anti-air first only while an enemy aircraft is up (the patch's hard limit), anti-vehicle first while an
   enemy tank or Gauss hog is up, else ROLE_FIRST; Legendary-led teams also pick the counter kind (VC-02); a "vehicle"
   call kind in brain/callouts.py and Director.report (a seen enemy rider) so beliefs and the coach report carry it;
   Bot.vehicle_mission open to any Heroic or Legendary bot holding an anti-vehicle gun when no Grenadier is alive.
9. **Ghosts never boost, Banshees never bomb.** Both inputs are undecoded, so rams come in slow and tanks are never hit
   from above. Change: decode the vehicle boost and secondary-fire inputs per game (the native button table, as s107 /
   s108 decoded the exits and the Falcon's vertical), add `act.boost` / `act.fire2`, boost in Bot.drive's splatter branch
   at the tier's distance (Easy on sight, Normal 9 u, Heroic 4.5-6 u, Legendary 3-6 u with a clear Terrain.vnav path),
   bomb a tank from inside its overhead cone.
10. **Normal teams play the objective like Heroic.** The director has no team tier: one Normal bot gets its team the full
    posture engine with pace, every role slot, one-scorer hill rings, power-position setups and coach plays. Change:
    `Director.team_tier(snap)` = the highest tier among living bots (TIER-MIX-03); at Normal: posture without tempo()
    and time ignored until the last 60 s, at most two hunters, two in the hill, no holds; Director.coach_take keeps only
    tempo, coaching and timer-triggered orders (reminders); coach_period 60 s at Normal, 30 s Heroic, 20 s Legendary,
    MATCH SO FAR's tendency lines for Legendary only.
11. **The coach cannot touch vehicles.** The report has no vehicle line, the schema no vehicle field, none of the patch's
    hooks or vehicle plays exist, and Invasion, Assault and Territories (the big vehicle modes) are not coached. Change:
    Director.state_doc adds `VEHICLES:` (ours: kind, driver, gunner, role; theirs seen: kind, zone, age); coach.PLAYS gains
    escort_hog, air_denial and tank_first with Director.play_ok preconditions (a free transport and our carrier on foot;
    an enemy aircraft seen; an enemy tank seen) mapped onto vehicle_orders' ferry and crew_orders' role order;
    coach.SCHEMA gains an optional `vehicle_roles` list (ESCORT, AIR_DENIAL, LANE_BLOCK, ANCHOR, TRANSPORT) that validate()
    holds to the patch's hard limits.
12. **No vehicle personalities.** Whoever is nearest drives (crew_orders, vehicle_orders): a camper flies the Banshee, a
    rusher sits in the tank; Driver, Pilot, Tanker and Support do not exist. Change: profiles.PERSONALITIES gains driver,
    pilot, tanker and support plus a `PREFERS` map by kind (rusher Ghost / Chopper / Mongoose, camper tanks / Gauss,
    flanker Ghost / Hornet, sniper Banshee / Gauss gun, driver transports, pilot aircraft, tanker tanks, support gun
    seats); Director.crew_orders' pair cost subtracts a preference bonus from the distance (for example 15 u),
    vehicle_orders' "hop on the gun" picks Support first; tools/botctl.py and the BOTS panel list the new styles.
