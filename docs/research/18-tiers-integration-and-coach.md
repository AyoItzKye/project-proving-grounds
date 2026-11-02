# Halo MCC Bots: Difficulty Tiers, On-Foot Integration, and the Optional Ollama Coach

Fourth file in the set. It binds the other three (`halo_mcc_vehicle_tactics_and_objectives.md`, `halo_mcc_objective_logic_brains.md`, `halo_mcc_equipment_powerups_brain.md`) to the on-foot combat brain that already exists in four difficulties, and defines an optional LLM coach layer (Ollama) that can sit on top. Nothing in this file requires the coach; every brain runs deterministically without it.

**Status tags:** **Rule** (how the game works, sourced), **Source** (a competitive practice reported by a guide, pro, or coach), **Proposed** (design for this mod, untested).

**ID formats:** `INT-NN` integration, `TIER-<BRAIN>-NN` difficulty, `COACH-NN` coach layer, `PLAY-<NAME>` playbook entries.

---

## Part 1. Integration contract with the on-foot combat brain

### 1.1 Layering

```
                 +------------------------------+
   optional ---> |  COACH (Ollama relayer)      |  advisory only; validated; expires
                 +------------------------------+
                               |
                 +------------------------------+
                 |  OBJECTIVE BRAIN (per mode)  |  posture, roles, goals, target weights, vehicle requests
                 +------------------------------+
                        |                 |
         +------------------------+  +-----------------------------+
         |  EQUIPMENT BRAIN       |  |  VEHICLE BRAIN              |
         |  pickups, abilities    |  |  driving, gunnery, ramming, |
         |  triggers, counters    |  |  boarding, threat response  |
         +------------------------+  +-----------------------------+
                        |                 |
                 +------------------------------+
                 |  ON-FOOT COMBAT BRAIN (yours) |  aim, reaction, strafe, jump, cover, tracker, grenades, melee
                 |  Easy / Normal / Heroic /     |
                 |  Legendary / Mixed            |
                 +------------------------------+
```

The on-foot brain is the base. The three module brains feed it inputs; it owns the frame-to-frame execution. The coach feeds the objective brain only.

### 1.2 What the modules send down to the on-foot brain (Proposed)

| Field | Type | Meaning | On-foot brain behavior |
|---|---|---|---|
| `posture` | enum AGGRESSIVE / BALANCED / CONSERVATIVE / DESPERATE | from the objective brain's posture engine (objective file Part 0.2) | scales engagement acceptance, push rate, grenade spend, cover usage (see 1.4) |
| `role` | string (CARRIER, ESCORT, DEFENDER, ANCHOR, SCORER, HUNTER, ...) | current job | selects movement profile and the conflict rule in 1.3 |
| `goal` | {pos, stance} | where to be; HOLD / PUSH / FLANK / RETREAT / CAMP | pathfinding target plus stance modifiers (HOLD = crouch and pre-aim, PUSH = sprint-capable, FLANK = avoid known sightlines) |
| `target_weights` | map entity -> float | multipliers for target selection | multiplies the on-foot brain's own threat scoring; never replaces it |
| `fire_discipline` | enum FREE / ADVANTAGE_ONLY / HOLD | from posture and role | FREE = fight anything; ADVANTAGE_ONLY = only with first shot, height, or numbers; HOLD = do not initiate (carriers, camo stalkers) |
| `grenade_budget` | int 0..N | grenades this role may throw before the next objective event | prevents escorts wasting grenades the plant needs |
| `vehicle_request` | enum role | from vehicle file 4.7 | on-foot brain routes to the vehicle and hands control to the vehicle brain on entry |
| `equipment_hint` | {item, trigger_set} | which equipment/ability triggers are enabled this life | on-foot brain fires the ability when a listed trigger is met |
| `callouts_in` | list | enemy carrier, enemy power weapon, enemy vehicle, predicted spawns | populates the on-foot brain's memory as if seen (subject to tier memory limits) |

### 1.3 Precedence when the layers disagree (Proposed)

- `INT-01` **Carrier rule.** If `role` is CARRIER (flag, bomb, ball, core, skulls), the objective brain wins every conflict: the on-foot brain does not initiate fights, does not stop to pick up weapons, and only fights when `CTF-MULTI-05` / `ODD-CORE-04` / `ASS-MULTI-06` says drop-and-fight.
- `INT-02` **Survival rule.** If the on-foot brain reports `shields_down AND enemy_in_los`, it may override `goal` for up to 4 s to reach cover, except for CARRIER (who keeps moving toward the escort) and except in DESPERATE posture.
- `INT-03` **Vehicle handoff.** Once seated, the vehicle brain owns the bot; the on-foot brain resumes on exit. The vehicle brain's threat responses (vehicle file 4.6) outrank `goal` while seated; `role` still applies (an ESCORT driver drives escort patterns).
- `INT-04` **Equipment triggers.** Ability triggers (equipment file) fire inside the on-foot brain's tick, but the equipment brain's hard rules win over habit: never Armor Lock in Infection, never ram a locked target, never fire from camo unless the first burst kills.
- `INT-05` **Target weights are multipliers, not orders.** The on-foot brain still refuses a target it cannot hit; a weight of 2.0 on an unreachable carrier changes pathing (via `goal`), not aim.
- `INT-06` **Posture caps the on-foot brain's aggression, not its skill.** Reaction time, aim, strafing, and jumping stay at the bot's tier regardless of posture; posture only changes which fights the bot accepts and where it stands.
- `INT-07` **Coach outputs never reach the on-foot brain directly.** They are consumed by the objective brain, validated, and expressed through the fields in 1.2.
- `INT-08` **Tick rates.** On-foot brain: per frame. Vehicle brain: per frame while seated. Objective brain: every 0.5 s. Equipment brain: on trigger events plus every 0.5 s. Coach: every 15 to 30 s plus events (Part 4).

### 1.4 How posture maps onto your on-foot settings (Proposed)

Your tiers already define cover use, backing off, strafing, and tracker use. Posture modulates them within the tier's ceiling, never above it:

| Posture | Engagement acceptance | Cover and back-off | Grenades | Movement profile |
|---|---|---|---|---|
| AGGRESSIVE | accepts even fights and some 1v2 at close range | uses cover only when `shields_down` | spends freely on pushes | sprint between covers; shorter peeks |
| BALANCED | accepts fights with first shot, height, or numbers | tier default | tier default | tier default |
| CONSERVATIVE | accepts only clear advantage; prefers range | backs off earlier (at 50 percent shields instead of 0) | saves one for defense | holds; relocates only to deny timers |
| DESPERATE | ignores K/D; objective only | none except CARRIER | all on the objective approach | straight lines to the objective |

An Easy bot in CONSERVATIVE posture still "fights in the open" because that is its tier ceiling; the posture only stops it from pushing. A Legendary bot in AGGRESSIVE still uses cover on `shields_down` because the table caps aggression at "cover only when shields down," not "never."

---

## Part 2. Difficulty tiers for the vehicle, objective, equipment, and Firefight brains

Mirrors your four tiers plus Mixed. The reaction numbers below reuse your base reaction times (Easy 0.28 s, Normal 0.22 s, Heroic 0.19 s, Legendary 0.15 s) and the "remembers an enemy" windows (4 / 6 / 8 / 10 s). Every bot's numbers vary by up to 10 percent, as in your spec, so no two Heroic drivers ram at the same commit distance. Personalities change *what a bot likes to do* in these brains too (Part 3), not how well it executes.

### 2.1 Vehicle brain tiers

| Behavior | Easy | Normal | Heroic | Legendary |
|---|---|---|---|---|
| Reaction to vehicle threats (barrel on us, lock tone, boarder, EMP charge) | 0.28 s plus a 50 percent chance to miss the cue entirely | 0.22 s, misses rare cues (EMP charge glow) | 0.19 s, all cues | 0.15 s, all cues, predicts barrel alignment 0.3 s early |
| Ram commit precision (vehicle file 4.3) | commits early (3 to 4 Scorpion lengths), heading error up to 30 deg; often misses | commits at 2 to 3 lengths, error 20 deg | 1.5 to 2 lengths, error 12 deg | 1 to 2 lengths, error 8 deg; leads the splatter |
| Never-ram list (tanks, Armor Lock) | ignores it 30 percent of the time (drives into tanks) | respects tanks; forgets Armor Lock sometimes | respects both | respects both and uses Armor Lock glow as area-denial awareness |
| Gunnery lead on slow projectiles | no lead | lead with 30 percent error | lead with 10 percent error | lead with 5 percent error; walks bursts |
| Weak-part aiming (rear hatch, gas tank) | never | sometimes when stationary | usually | always when the angle exists |
| Boarding (as attacker) | only unoccupied vehicles | boards stopped vehicles | boards slow-moving vehicles; EMP first when available | boards anything per the Quick Reference procedure; counter-board timing |
| Boarding defense (as driver) | does not react to boarders | accelerates away if it notices | gunner engages boarders; driver turns away | Reach counter-board (exit and re-board) when gunner is dead |
| Retreat and abandon thresholds | ignores them (fights to death) | uses retreat threshold | uses retreat and abandon | uses both plus "smoking plus incoming explosive" exit rule |
| Vehicle selection at spawn | takes the nearest vehicle regardless of role | takes a role but with wrong counters sometimes | role by vehicle file 4.7 | role plus counter-vehicle awareness (`VC-02`) |
| Blind spots (tank overhead cone, Chopper rear) | unaware | aware when attacked from there | repositions pre-emptively | drives to deny the angle before the enemy takes it |
| Boost timing (Ghost, Chopper, Wraith) | boosts on sight | boosts at 3 lengths | boosts at 1.5 to 2 lengths | boosts at 1 to 2 lengths with wall checks |
| Crew coordination | gunner shoots whatever it sees | driver tries to keep the gunner's arc on target | full coordination (vehicle file 4.5) | full plus passenger objective rules |
| Splatter target choice | nearest enemy | nearest enemy not near a tank | carrier > power weapon holder > nearest | objective-weighted, avoids spawn-flip kills (`SP-01`) |
| Air (Banshee, Hornet, Falcon) | flies level, dives late | basic swoops | swoops and trick rolls on lock tone | full evasion, rear-quarter attacks, overhead tank bombing |

### 2.2 Objective brain tiers

| Behavior | Easy | Normal | Heroic | Legendary |
|---|---|---|---|---|
| Posture engine | always BALANCED (ignores score and time) | reads score; ignores time until the last 60 s | full engine | full engine plus `closing` pace projection |
| Roles | everyone is a SLAYER or a RUNNER (no escorts, no anchors) | basic roles, no ROTATOR | all roles | all roles, dynamic reassignment every 0.5 s |
| Power-weapon and power-up timers (`PW-01`) | none | tracks timers 50 percent of the time | tracks all; arrives early sometimes | tracks all; arrives 10 s early; denies in CONSERVATIVE |
| Spawn control (`SP-01`) | none | none | avoids obvious spawn-flip kills | full spawn-weight awareness (Source: Team Liquid "highest weighted spawn" rule) |
| Carrier memory (last seen enemy carrier) | 4 s | 6 s | 8 s | 10 s plus route prediction |
| Callouts (team plan, focus fire) | none | some ("they have tank") | most (carrier, weapons, vehicles) | all, including predicted spawns and "one shot" status (Source: MLG communication fundamentals) |
| Time-low branches (losing/winning scenarios) | never | only the last 60 s | yes | yes, with the enemy's scoring pace |
| Lives-limited behavior (Elimination) | plays as normal Slayer | groups loosely | full `SLAY-ELIM` formation | full plus last-man stalling |
| Hill/territory discipline (one scorer, ring outside) | everyone stands in the hill | two in the hill | one scorer, ring outside | one scorer, ring plus vehicle anchor, grenades timed to pushes |
| Setups and traps (Source: MLG "setup to teamshot and trap") | none | none | basic crossfire setups | full setups, breakout rushes, cross-map rotations |
| Map knowledge (routes, lanes, hold spots) | runs straight at the objective | some | mostly | full |
| Coach availability (Part 4) | none | reminders only | plays | plays plus opponent tendencies |

### 2.3 Equipment brain tiers

| Behavior | Easy | Normal | Heroic | Legendary |
|---|---|---|---|---|
| Pickup timing (`EQP-04`) | takes power-ups when stumbled on | heads for them when nearby | pre-positions sometimes | pre-positions 5 s early; denial pickups |
| Pickup routing (`EQP-06`) | keeps whatever it grabs | gives overshield to carriers sometimes | routes by role | routes by role and posture |
| Equipment/ability triggers enabled | 1 or 2 basic triggers per item (bubble when shields down, lock when stuck) | half the trigger list | full list | full list plus counters (grenade timed to lock expiry, Grav Lift under a bubble) |
| Hologram detection (`EQ-HOLO-05`) | shoots every hologram | shoots most | holds fire after 1.5 s of straight walking | holds fire and watches the corner it came from |
| Camo detection | only when hit | shimmer at close range | shimmer plus radar jam tell | all cues plus Promethean Vision use |
| Armor Lock use | only for stuck grenades | plus incoming explosives | full trigger list | full list plus EMP exit timing and body-blocks |
| Halo 4 loadout packages | default loadout | role-appropriate ability | role loadouts (`EQ-PKG-01`) | role plus posture adjustments and ordnance choice order |

### 2.4 Firefight brain tiers

| Behavior | Easy | Normal | Heroic | Legendary |
|---|---|---|---|---|
| Hold position choice (`FF-POS-01`) | fights wherever it spawns | moves to a reasonable hold | roofed, high, single-approach holds | holds plus a planned second hold and resupply routes |
| Lives management (`FF-LIFE-01`) | ignores the pool | conservative under 3 lives | full posture by pool | full plus bonus-round aggression and respawn delay |
| Wave reading (`FF-WAVE-01`) | none | reads the drop sometimes | sets weights from the drop | sets weights and calls the composition |
| Three-enemy pacing (`FF-WAVE-02`) | kills everything | kills everything | leaves harmless stragglers to reload | deliberately paces drops |
| Enemy procedures | headshots Grunts; everything else is a body-shot fight | noob combo on Elites; shoots Hunter backs when exposed | full procedures (Jackal hand/foot, Hunter two-bot, Engineer first) | full procedures plus the Hunter line-up trick and skull adaptations |
| Vehicle hijacks | none | takes a parked Ghost | hijacks Ghosts and Choppers | hijacks and runs lanes, retreats on Wraith drops |
| Skull adaptation (`FF-WAVE-05`) | none | Catch only | most | all |

### 2.5 Mixed and variance (Proposed)

- `TIER-MIX-01` Mixed assigns tiers to bots in rotation (Heroic, Normal, Legendary, Easy) exactly as your on-foot spec does; a bot's module tiers always equal its on-foot tier, so a Legendary driver is also a Legendary shooter. A bot pinned to a tier in the bot list keeps it in all four brains.
- `TIER-MIX-02` Variance: every numeric value in the tier tables (commit distance, lead error, pre-position seconds, memory window) is multiplied by a per-bot factor drawn once at spawn from 0.90 to 1.10, matching your 10 percent rule.
- `TIER-MIX-03` A team's objective brain runs at the tier of its **highest-tier living bot** for timers, posture, and callouts (a Legendary bot on the team "leads"); individual bots still execute at their own tier. This is how a Mixed team gets a plan without the Easy bots suddenly playing like pros.

---

## Part 3. Personalities in these brains (Proposed)

Your personalities (rusher, camper, flanker, sniper, and so on) change preference, not execution. Here is how each biases the module brains, plus four vehicle-flavored personalities worth adding.

| Personality | Vehicle brain bias | Objective brain bias | Equipment bias | Firefight bias |
|---|---|---|---|---|
| Rusher | prefers Ghost, Chopper, Mongoose; ram weight x1.5; retreat threshold x0.7 | volunteers for RUNNER, HUNTER, first contest of a hill | overshield, Speed Boost, Thruster, Evade | CLEANER role; hijacks Ghosts |
| Camper | prefers tanks and Gauss; parks | DEFENDER, ANCHOR, SCORER | Deployable Cover, Trip Mine, Autosentry, Drop Shield, Regenerator | ANCHOR role; never leaves the hold |
| Flanker | prefers Ghost and Hornet; approaches from rear quarters | ESCORT, ROTATOR, Neutral Flag intercepts | camo, Radar Jammer, Hologram, Jetpack | PP role (flanks Hunters with camo) |
| Sniper | prefers Banshee cannons and the Gauss seat | RING, long-lane ANCHOR, KOTH sniper (`KOTH-STATIC-06`) | camo, Awareness/Stability packages, Deployable Cover | ANCHOR with precision; Jackal sniper priority |
| **Driver** (new) | always claims the transport or escort hog; crew coordination x1.2 | DRIVER role, carrier pickup routes | Wheelman, Hardlight Shield for exiting under fire | runs the Chopper/Ghost lanes |
| **Pilot** (new) | always claims aircraft; swoop and rear-quarter attack bias | AIR role, carrier cover, hill bombing | Jetpack when no aircraft | Banshee pilot shots, Hornet transport |
| **Tanker** (new) | claims Scorpion/Wraith; holds lanes; never chases | ANCHOR, arm-site blocker, hill anchor | Deployable Cover near the tank | Wraith/Scorpion counter-fire from the hold |
| **Support** (new) | gunner seats over driver seats | ESCORT, BODYGUARD, DISARMER, ARMER | Regenerator, Drop Shield, Regeneration Field, bubble | HEAVY/medic; Drop Shield between waves |

---

## Part 4. Optional Ollama coach layer

### 4.1 What the coach is, and is not

Source basis: in competitive Halo and other esports, the coach does not aim or move; the coach keeps the team on the objective, calls timers, reads the opponent's tendencies, adjusts tactics between rounds, and uses limited windows (timeouts) to change tempo or reset the plan (Source: Denial coach Elumnite,; CS coaching practice restricts coach talk to timeouts and half-time; analysts compile opponent tendency briefs). That maps cleanly onto an LLM that is slow, occasionally wrong, and optional.

- `COACH-01` **Advisory only.** The coach emits suggestions; the objective brain validates each one against a schema and against hard rules, then applies it through the fields in 1.2. The coach cannot touch aim, reaction, or any on-foot setting (`INT-07`).
- `COACH-02` **Optional at every level.** If the coach is absent, slow, malformed, or silent, the deterministic brains run exactly as written in the other three files. No brain waits on the coach. A missing coach changes nothing except the absence of the plays in 4.6.
- `COACH-03` **Cadence like a real coach.** The coach speaks at "timeouts," not every tick: on match start, every 20 s (Legendary) / 30 s (Heroic) / 60 s (Normal) / never (Easy), and on events (lead change, power weapon spawn in 15 s, objective taken or lost, vehicle spawn, lives under 3, last 60 s). Advice carries an expiry (default 20 s); stale advice is dropped.
- `COACH-04` **Bounded authority.** The coach may: set posture within one step of the engine's value (it can turn BALANCED into AGGRESSIVE, not into DESPERATE), reassign roles among living bots, set target-weight overrides between 0.5 and 2.5, choose a lane or route among the map's enumerated options, select a play from the playbook (4.6), set a tempo (SLOW / NORMAL / FAST), and add callouts. The coach may not: violate a hard rule (never-ram list, never Armor Lock in Infection, carrier does not fight), assign a dead bot, reference an entity not in the state, or exceed the numeric bounds. Invalid fields are discarded individually; the rest of the message still applies.
- `COACH-05` **Analyst memory.** Across a match the coach keeps a short opponent-tendency log (Source: analyst briefs): which power weapon the enemy takes first, which lane their vehicles use, whether they camp a tower, whether they rotate to the next hill early, which base door they attack. The log is fed back into the prompt each timeout so the coach's plays adapt (4.7).
- `COACH-06` **Tier gating.** Easy teams get no coach. Normal gets reminders only (timer and objective reminders, no plays). Heroic gets plays. Legendary gets plays plus the tendency log. In Mixed, the coach serves the team at the tier of its highest-tier living bot (`TIER-MIX-03`).

### 4.2 Transport (Proposed)

The relayer sends a compact state snapshot to Ollama and receives JSON. Suggested shapes:

**Snapshot (relayer -> coach)**
```json
{
  "game": "H3", "mode": "CTF-MULTI", "map": "Valhalla", "tier": "Heroic",
  "time": {"elapsed": 312, "limit": 900, "sudden_death": false},
  "score": {"us": 1, "them": 2, "limit": 3},
  "posture_engine": "AGGRESSIVE",
  "lives": null,
  "objective": {"our_flag": "home", "their_flag": "carried_by_us", "carrier": "bot2", "carrier_pos": "mid_rocks"},
  "bots": [
    {"id": "bot1", "role": "ESCORT", "alive": true, "pos": "mid_rocks", "loadout": "BR+AR", "vehicle": null},
    {"id": "bot2", "role": "CARRIER", "alive": true, "pos": "mid_rocks", "loadout": "flag"},
    {"id": "bot3", "role": "DEFENDER", "alive": false, "respawn_in": 3},
    {"id": "bot4", "role": "DRIVER", "alive": true, "pos": "our_base", "vehicle": "warthog"}
  ],
  "enemy": {"seen": [{"pos": "their_turret", "weapon": "sniper", "age": 4}], "vehicles": ["banshee"], "carrier": null},
  "map_timers": {"laser": 42, "sniper_red": 0, "banshee_red": 95},
  "tendencies": ["enemy sniper holds their turret", "enemy banshee bombs mid at every push"],
  "last_play": "PLAY-ESCORT-HOG", "last_play_result": "carrier_died"
}
```

**Advice (coach -> relayer)**
```json
{
  "ttl": 20,
  "posture": "AGGRESSIVE",
  "tempo": "FAST",
  "play": "PLAY-OUTSKIRTS-RUN",
  "roles": {"bot1": "ESCORT", "bot4": "AIR_DENIAL"},
  "lanes": {"bot2": "beach_route"},
  "target_weights": {"banshee": 2.5, "sniper_holder": 2.0},
  "callouts": ["banshee up, runner stays off the hog", "laser in 42, bot4 be at laser"],
  "note": "they bomb mid every push; take the beach and put bot4 on the laser for the banshee"
}
```

- `COACH-07` **Validation.** The relayer rejects any field that fails schema or bounds, logs it, and applies the remainder. Unknown play IDs are ignored. Lane names must match the map's enumerated lanes. Role names must be in the mode's role list.
- `COACH-08` **Latency tolerance.** If a reply arrives after its own `ttl` or after the next snapshot was sent, drop it. Typical target: under 3 s on a local model; the brains do not care if it is 10 s, they just ignore late advice.
- `COACH-09` **Model-agnostic.** The prompt in 4.5 works for any instruction-following model; keep temperature low (0.2 to 0.4) so plays are consistent.

### 4.3 What the coach is good for, by brain (Proposed)

- **Objective brain:** play selection, tempo, role reshuffles after deaths, timer discipline, reading the opponent's pattern (they always rush the same door), deciding when to slow the game out (Source: "slow attrition" close-outs) and when to breakout rush.
- **Vehicle brain:** lane assignment for drivers, which counter-vehicle to spawn next, when to bait an enemy vehicle into a lane with Armor Lock or a Chopper, whether the Banshee goes air-denial or ground-support this life.
- **Equipment brain:** who gets the next overshield/camo, whether to deny or use a power-up, which Halo 4 loadout a bot should respawn with given what the enemy is running.
- **Firefight brain:** pacing calls (leave stragglers, resupply now), hold rotation, who takes the next Hunter pair, when to spend ordnance, lives-based posture nudges.

### 4.4 What the coach must never be allowed to do

- Change aim, reaction, strafing, jumping, tracker use, or memory windows (your tier tables).
- Set DESPERATE unless the engine already computes AGGRESSIVE or DESPERATE.
- Order a ram on a tank, Wraith, Elephant, or Armor-Locked target.
- Order a carrier to fight, to drop the objective to go for a weapon, or to use a vehicle seat the mode forbids.
- Order Armor Lock in Infection, a splatter on an Armor-Locked player, or a hologram shot.
- Assign more than one SCORER to a hill, more than one CARRIER, or zero DISARMERS when the enemy has planted.
- Reference map positions that are not in the map's enumerated node list.

### 4.5 System prompt for the coach (Proposed, paste-ready)

```
You are the team coach for a squad of Halo: The Master Chief Collection bots. You do not aim or move.
You read a JSON snapshot of the match and reply with ONE JSON object of advice that expires in `ttl` seconds.
Your job, in priority order: (1) keep the team on the objective, (2) call power weapon, power-up, and vehicle
timers so a bot is there before spawn, (3) pick a play from the playbook that fits the score, time, and the
enemy's tendencies, (4) reassign roles after deaths, (5) set tempo: FAST when behind or when the enemy is
weak or on respawn, SLOW when ahead with time low or when lives are limited.
Rules you must respect: never set DESPERATE unless the engine's posture is already AGGRESSIVE or DESPERATE;
never order a ram on tanks, Wraiths, Elephants, or Armor-Locked players; never order a carrier to fight or
to drop the objective for a weapon; never order Armor Lock in Infection; one SCORER per hill, one CARRIER.
Only use role names, lane names, and play IDs that appear in the snapshot's allowed lists.
Reply with JSON only. Keep `note` under 30 words.
```

### 4.6 Playbook (plays the coach can call, each mapped to existing rule IDs)

Plays are named macro-patterns from competitive Halo (Sources: Halo 3 MLG guide on breakout rushes, setups, and traps; Team Liquid on map control, spawn pressure, and sniper-held respawns; MLG timer practice: OS and camo on 2 minute post-pickup timers, rockets on 3 minute game-clock timers in Halo 3 MLG settings; weapon timers in MCC Halo 3 start 2 s after the weapon is disturbed). Each play is a bundle of posture, roles, lanes, and weights that the objective brain already understands.

| Play ID | What it is | Mapped rules | When the coach calls it |
|---|---|---|---|
| `PLAY-BREAKOUT` | Pre-planned opening rush to the power weapons and power-ups, one bot per item, fourth supports rockets | `SLAY-CORE-01`, `EQP-02`, `PW-01` | match start; after a full-team wipe |
| `PLAY-SETUP` | Take a power position with overlapping sightlines so pushes get teamshot and trapped; hold, do not chase | `SLAY-CORE-02/03`, `SLAY-SWAT-10`, `KOTH-STATIC` ring | ahead or even, power weapon in hand |
| `PLAY-SPAWN-TRAP` | Hold positions that pressure the enemy's likely spawns (highest-weighted spawn zones) so they spawn cross-map and must fight through fire to reach the objective | `SP-01`, `SLAY-CORE-07`, Team Liquid spawn weighting | numbers advantage; enemy on respawn |
| `PLAY-TIMER-DENY` | Be at the next power weapon or power-up 10 s early, take it, leave; deny rather than use | `PW-01`, `EQP-03/04` | CONSERVATIVE posture; ahead with time low |
| `PLAY-SNIPER-HOLD` | Sniper holds the lane that covers the enemy's spawn exits while the others take the objective | `SLAY-SNIPE-01`, `KOTH-STATIC-06`, Team Liquid "sniper keeps enemy on respawn" | sniper acquired; objective contest |
| `PLAY-CROSSMAP` | Rotate the whole team to the opposite side to flip spawns and catch the enemy off their setup | `SLAY-CORE-08`, `TERR-SYM-08` | behind; enemy entrenched |
| `PLAY-TEMPO-SLOW` | Slow the game: no mid crossings, deny timers, trade time for safety | `P-06/P-09`, `SLAY-CORE-11`, `CTF-MULTI-15` | ahead with time low |
| `PLAY-TEMPO-FAST` | All-in: every bot pushes one lane together behind grenades | `P-04/P-05`, `SLAY-CORE-09`, `CTF-MULTI-16`, `ASS-MULTI-12` | behind with time low; enemy weak |
| `PLAY-OUTSKIRTS-RUN` | Flag/bomb run via the outer route with escort front and rear | `H3-CTF-05`, `CTF-MULTI-04` | carrier active, mid contested |
| `PLAY-ESCORT-HOG` | Warthog delivers runner plus gunner, drops at 25 m, circles | `CTF-MULTI-03`, `H2-CTF-02` | open map, no enemy Banshee |
| `PLAY-AIR-DENIAL` | One bot or vehicle dedicated to killing the enemy aircraft before any push | `VC-02`, `CTF-MULTI-18` | enemy Banshee/Hornet up |
| `PLAY-TANK-FIRST` | Two bots EMP-and-board or rocket the enemy tank before the objective push | `CTF-MULTI-17`, `ASS-MULTI-13`, vehicle Quick Reference | enemy tank controls the lane |
| `PLAY-CHOPPER-LANE` | Halo 3: Chopper stations on the enemy vehicle road and boost-rams what commits | `H3-PUR-04`, `H3-DEF-03` | Halo 3 Big Team, enemy hogs active |
| `PLAY-VEHICLE-BAIT` | Leave a vehicle where the enemy will take it, with a trip mine or an Armor Lock bot in its lane | `EQ-MINE-03`, `EQ-LOCK-06` | Halo 3 / Reach, enemy likes to steal vehicles |
| `PLAY-HILL-SNIPE-THEN-PUSH` | Kill the enemy scorer from range, grenades into the ring, then push as three | `KOTH-STATIC-06/09/10` | enemy holds the hill |
| `PLAY-ROTATE-EARLY` | Send the fastest bot to the next hill/drop point at T-10 s | `KOTH-MOVING-02`, `HH-03` | Crazy King, Headhunter |
| `PLAY-BOMB-SIEGE` | Grenades on the site, vehicle into the site to draw fire, then the carrier | `ASS-MULTI-01` | Assault plant |
| `PLAY-STACK-DISARM` | Everyone alive on the bomb; more disarmers disarm faster | `ASS-MULTI-09` | enemy has planted |
| `PLAY-ONE-FLIP` | Flip the enemy's weakest territory to break their majority | `TERR-SYM-08`, `DOM-08` | behind in Territories/Dominion |
| `PLAY-LASTMAN-STALL` | Last bot alive hides and times out the round | `SLAY-ELIM-06`, `INF-SURV-08` | one-life modes |
| `PLAY-FF-PACE` | Leave harmless stragglers alive, resupply, reposition, then finish the wave | `FF-WAVE-02/03` | Firefight between waves |
| `PLAY-FF-HUNTER` | Designate front bot and back bot for the Hunter pair; HEAVY holds rockets for the exposed back | `FF-HUNTER-02` | Hunter wave dropped |
| `PLAY-FF-ROOF` | Whole team to the roofed hold when a Wraith drops | `FF-POS-01`, `FF-VEH-02` | Wraith on the field |

### 4.7 Opponent tendencies the coach tracks (Proposed)

The relayer appends one line per observed pattern after two or more occurrences; the coach reads them and the playbook maps the response:

| Tendency observed | Coach response |
|---|---|
| Enemy takes the same power weapon first every life | `PLAY-TIMER-DENY` on that weapon, or `PLAY-SETUP` covering its spawn |
| Enemy vehicles always use one lane | `PLAY-CHOPPER-LANE` / `PLAY-VEHICLE-BAIT` / tank parked on the lane |
| Enemy camps one tower or sniper nest | `PLAY-CROSSMAP` to flip spawns, hologram first, then push from the rear quarter |
| Enemy rushes the same base door | kill box on that door (`CTF-ONE-08`), trip mine, Autosentry, Deployable Cover |
| Enemy rotates to the next hill early | `PLAY-ROTATE-EARLY` earlier (T-15 s) with a vehicle |
| Enemy over-commits to a losing hill | let them, hold the next one (`KOTH-MOVING-06`) |
| Enemy Banshee bombs mid at every push | `PLAY-AIR-DENIAL` before any mid crossing; runner stays off vehicles |
| Enemy pushes one at a time | `PLAY-SETUP` and farm; posture BALANCED, never chase |
| Enemy groups up | grenades first, Wraith/tank splash, Power Drain, Damage Boost on the gunner |
| Enemy uses Armor Lock a lot | grenade timing to lock expiry, never ram, bait locks with a hologram |
| Enemy flag runner always takes the middle | hunters pre-position at mid instead of chasing (`CTF-MULTI-11`) |

### 4.8 Safety and evaluation (Proposed)

- `COACH-10` **Kill switch.** A config flag disables the coach; a per-match health check disables it automatically after three consecutive malformed replies.
- `COACH-11` **Scoring the coach.** Log every applied play with the match outcome and the 30 s result (objective progress, kills traded). Over many matches, plays with negative expectation get down-weighted in the prompt's "preferred plays" list. This is the only learning loop; it is offline and optional.
- `COACH-12` **Determinism for testing.** With the coach off, the brains are reproducible; test the brains first, then enable the coach and compare.

---

## Part 5. What is sourced and what is not

- Competitive practice (breakout rushes, setups that teamshot and trap, callout content including enemy health and predicted spawns, power-up timers at 2 minutes post-pickup and rockets on the game clock in Halo 3 MLG settings, sniper used to hold enemies on respawn, map control through spawn pressure and highest-weighted spawn selection) comes from the Halo 3 MLG guide (runbo.blogspot), the Bungie.net MLG thread, Team Liquid's "How to Halo," and the Steam Halo 3 spawn-time guide (MCC weapon timers start 2 s after disturbance).
- The coaching model (objective focus over timer-reading, limited communication windows, analyst tendency briefs, mid-series adjustments, tempo changes via timeouts) comes from the Denial coach interview and general esports coaching coverage (CS2 coach role articles, IESF).
- Everything in Parts 1 to 4 tagged Proposed is design written for this mod: the integration fields, precedence rules, every tier table, the personalities mapping, the coach transport, prompt, playbook mapping, and tendency responses. None of it has been tested.
