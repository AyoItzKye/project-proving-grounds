# Halo MCC Objective Logic Brains

Companion to `halo_mcc_vehicle_tactics_and_objectives.md`. That file is the **combat and vehicle brain** (how a bot fights, drives, rams, boards). This file is the **objective brain**: one swappable module per gametype that tells the bots *what to be doing and why* at every moment, including when they are losing, when time is short, when enemy vehicles are up, and when lives are limited. The combat brain stays loaded underneath; the objective brain sets its priorities.

**Status tags**
- **Rule:** How the gametype actually works (from Halopedia's custom-game settings pages, gametype pages, and MCC playlist notes).
- **Source:** A tactic reported by a wiki, guide, or community thread.
- **Proposed:** Logic written for this mod. Tune in testing.

**File set:** file 2 of 4. See `halo_mcc_bot_tiers_integration_and_coach.md` for how these brains scale by difficulty, how they feed the on-foot combat brain, and how the optional Ollama coach can call plays built from the rule IDs here.

**Rule ID format:** `FAMILY-SUBSET-NN` (e.g. `SLAY-SWAT-03`, `CTF-ONE-07`, `FF-HUNTER-02`). Cross-references to the vehicle file use its IDs (`H3-PUR-04`, `REACH-INV-01`, etc.).

---

## Part 0. Brain architecture and the universal posture engine

### 0.1 How a brain plugs in

Every objective brain exposes the same interface so they can be hot-swapped per gametype:

```
INPUTS (polled every 0.5 s)
  score.us, score.them, score.limit, score.leader (FFA)
  time.elapsed, time.limit, time.remaining, round.index, round.count, sudden_death.active
  lives.us, lives.them (if limited), teammates.alive, enemies.alive (if known)
  objective.state        (gametype-specific struct: flag positions, hill location, bomb carrier, territories owned, etc.)
  map.power_weapons[]    (name, spawn_pos, respawn_timer, last_seen_holder)
  map.powerups[]         (overshield, camo, custom powerup, timers)
  map.vehicles[]         (type, pos, occupied_by_team, health)
  enemy.vehicles_active[] (type, last_pos, threat_level from vehicle brain)
  traits                 (shields on/off, radar on/off, starting weapons, speed, lives per round, carrier traits)
  bots.us[]              (id, pos, loadout, health, role, vehicle)

OUTPUTS (every 0.5 s)
  posture               : AGGRESSIVE | BALANCED | CONSERVATIVE | DESPERATE
  role[bot]             : one of the roles the brain defines (CARRIER, ESCORT, SLAYER, ANCHOR, HUNTER, ...)
  goal[bot]             : world position or entity to move toward, plus a stance (HOLD, PUSH, FLANK, RETREAT, CAMP)
  target_weights[bot]   : multipliers fed into the combat brain's target scoring (carrier 2.0, hill occupant 1.5, ...)
  vehicle_request[bot]  : which vehicle role to claim at spawn (feeds vehicle file 4.7)
  comms[]               : callouts the bots share (enemy carrier position, power weapon timer, "they have tank")
```

The combat brain owns aim, movement micro, grenade use, melee, boarding, driving. The objective brain owns *where*, *who*, and *how hard*.

### 0.2 Universal posture engine (Proposed)

Compute every tick:

```
margin      = (score.us - score.them) / score.limit           (team modes; FFA uses leader gap)
time_frac   = time.remaining / time.limit                     (1.0 at start, 0 at end; 1.0 if no limit)
closing     = points the enemy needs / points-per-minute they have been scoring over the last 2 minutes
            = minutes until the enemy wins at their current pace
our_closing = same for us

POSTURE RULES (first match wins)
P-01  lives limited AND lives.us <= 1 per bot            -> CONSERVATIVE (DESPERATE if also behind)
P-02  sudden_death.active AND we are behind              -> DESPERATE (all-in on the objective; nothing else matters)
P-03  sudden_death.active AND we are ahead               -> CONSERVATIVE (deny; do not chase)
P-04  margin <= -0.30 AND time_frac < 0.25               -> DESPERATE
P-05  margin <= -0.15 AND time_frac < 0.50               -> AGGRESSIVE (we must make plays now)
P-06  margin >= +0.30 AND time_frac < 0.40               -> CONSERVATIVE (slow the game; trade time for safety)
P-07  margin >= +0.15                                    -> BALANCED, leaning to map control
P-08  closing < 2.0 minutes AND we are behind            -> AGGRESSIVE (the enemy is about to close it out)
P-09  closing < 2.0 minutes AND we are ahead             -> CONSERVATIVE (slow attrition: hold power positions, do not feed)
P-10  default                                            -> BALANCED
```

What each posture changes (feeds the combat brain):

| Posture | Engagement range | Push rate | Grenade use | Vehicle use | Respawn behavior | Power weapon priority |
|---|---|---|---|---|---|---|
| AGGRESSIVE | engage at mid-to-close, accept 50/50 fights | push objective immediately on spawn | spam on objective, use all | take every vehicle, ram freely | spawn and go, no regroup wait | contest every spawn even under fire |
| BALANCED | engage with advantage (height, numbers, first shot) | push in pairs | normal | normal | regroup with nearest teammate within 10 s | contest when safe |
| CONSERVATIVE | engage only with clear advantage, prefer long range | hold positions, push only to reset objective | save one grenade for defense | vehicles stay near our side; no deep rams | wait for 2 teammates, then move | deny by timing (be there before spawn), do not fight over it |
| DESPERATE | ignore kill/death; objective only | everyone pushes the objective now | all on objective approach | every vehicle goes at the objective | spawn nearest objective and go | only if directly on the path |

### 0.3 Universal modules every brain inherits

**Power weapon control (Source: standard competitive practice; timers are Rule values per map)**
- `PW-01` Track every power weapon's respawn timer from the moment it is picked up (weapon respawn time is a game setting; default map timers are typically 60 to 180 s). Assign one bot to be at the spawn 10 s before it is up when posture is BALANCED or better.
- `PW-02` A bot holding a power weapon does not carry the objective (flag, bomb, ball) unless posture is DESPERATE. The weapon stays with a SLAYER or ANCHOR role.
- `PW-03` When losing a power weapon (holder dies), the brain broadcasts its position so the nearest bot retrieves it before the enemy does; retrieval beats any non-objective task.
- `PW-04` CONSERVATIVE posture: deny weapons rather than use them. A bot takes the rockets and stays at the base rather than hunting.

**Power-up control**
- `PU-01` Overshield goes to the bot who will contest the objective next (carrier in CTF, hill pusher in KOTH, juggernaut hunter).
- `PU-02` Active Camo goes to the bot with the longest-range or stealthiest role (sniper, flag sneak, bomb plant).
- `PU-03` Custom powerup: read its traits from the gametype; route it by the same logic.

**Spawn control (Source: competitive Halo fundamentals)**
- `SP-01` In team modes, bots avoid killing an enemy in a position that would spawn the enemy team behind our objective carrier or on top of our flag. The combat brain exposes "spawn influence zones" per map; the objective brain adds a 0.5 multiplier to targets whose death would flip enemy spawns onto our objective.
- `SP-02` On spawn, a bot checks `role` before moving. Carrier escorts spawn and move to the carrier; anchors spawn and move to the anchor point; slayers spawn and move to the nearest teammate.

**Vehicle control (links to the vehicle file)**
- `VC-01` At spawn, request the role from vehicle file section 4.7. The objective brain overrides the default: transport-heavy for CTF and Assault, anti-vehicle-heavy for KOTH and Territories, anti-air-first whenever `enemy.vehicles_active` contains any aircraft.
- `VC-02` An enemy vehicle on the field raises the weight of the matching counter in the next spawn selection: enemy Banshee -> our rocket hog, Hornet, Banshee, or anti-air infantry weapon; enemy tank -> our Gauss, Chopper (Halo 3 only, for interception, never for ramming tanks), rockets, laser, or EMP plus boarders; enemy Warthog swarm -> Chopper, Ghost, or Gauss.
- `VC-03` CONSERVATIVE posture keeps vehicles on our half of the map as mobile turrets; DESPERATE sends everything at the objective.

**Callouts (Proposed)** every brain broadcasts: enemy carrier position every 2 s, enemy power weapon holder, enemy vehicle spawns, hill moves, territory flips, lives remaining.

---

## Part 1. Slayer family

### 1.1 Which variants share a brain

| Same brain as plain Slayer (differences are only weapon starts or scoring) | Needs its own subset brain |
|---|---|
| Slayer, Team Slayer, Slayer BR, Slayer DMR, Team BR, Legendary Slayer, Classic Slayer, Slayer Pro (Reach: DMR start, no radar in some variants; H2A: BR start), Elite Slayer, Infinity Slayer (Halo 4: loadouts and ordnance drops; add module 1.7), Big Team Slayer (add vehicle module), Multi-Team | SWAT and SWAT Magnums and SWAT Arsenal and ShWATguns (no shields, no radar), Snipers and Team Snipers, Rockets, Swords, Fiesta, Phantoms and Team Phantoms (active camo), Elimination and Duel and Phantom Elimination (limited lives), Regicide (Halo 4 FFA with king), Endurance (CE: health does not regenerate between kills) |

**Rule facts:** Halo 2 and Halo 3 Team Slayer default 25 kills (50 in Team SWAT playlists); Halo 4 Infinity Slayer uses points, not kills. Slayer Pro in Reach is DMR start with no Armor Abilities except Sprint in most playlists (treat as plain Slayer with a long-range bias). Elimination = one life per round (lives per round = 1).

### 1.2 Core Slayer brain (team)

**Roles:** 1 ANCHOR (holds the power position with the best sightlines), 1 or 2 SLAYERS (push as a pair), 1 ROTATOR (controls power weapon and power-up spawns, flexes to whichever fight is going our way). In 8v8 Big Team, add 2 VEHICLE roles and 1 SNIPER.

**Opening (first 30 s)**
- `SLAY-CORE-01` Split: ROTATOR runs to the nearest power weapon spawn; ANCHOR takes the high ground nearest our spawn; SLAYERS move together toward the map's central power position.
- `SLAY-CORE-02` Source (competitive fundamentals): the team that holds the power position with the most sightlines wins slayer at even skill. The ANCHOR never leaves it without a replacement arriving first.

**Mid-game**
- `SLAY-CORE-03` Hold power points. Bots do not chase kills off the power position. Target weight: any enemy approaching our power position 1.5, any enemy inside the enemy's own power position 0.6 (do not push into their setup).
- `SLAY-CORE-04` Pick up power weapons on their timers (PW-01). The ROTATOR owns this.
- `SLAY-CORE-05` Trade control: when a SLAYER dies, the other SLAYER falls back to the ANCHOR rather than fighting alone. Lone fights are only accepted in AGGRESSIVE or DESPERATE posture.
- `SLAY-CORE-06` Shields down -> break line of sight and let them recharge (Halo 3 recharge starts after about 5 s; Reach after 6 s per the tag values in the vehicle file). The combat brain does this; the objective brain only confirms by lowering that bot's push rate to 0 for 6 s.
- `SLAY-CORE-07` Numbers advantage: if we have 2+ more alive than the enemy, posture temporarily becomes AGGRESSIVE for 15 s and all bots push the enemy spawn side to take map control before they respawn.

**Losing-team scenarios**
- `SLAY-CORE-08` Enemy closing on victory (P-08): stop holding; the ANCHOR becomes a SLAYER; all three push together through one lane with grenades first. The only way to win a losing slayer game is to win a multi-kill fight, and that needs numbers in one place.
- `SLAY-CORE-09` Enemy holds the power position and we are behind: do not feed one at a time. Group at a spawn, throw every grenade onto the position, push as three the instant the grenades land.
- `SLAY-CORE-10` Enemy has a power weapon and we are behind: a single bot baits it from max range while the others flank; the bait's goal is to make the holder fire and waste ammo, not to win the duel.

**Winning-team scenarios**
- `SLAY-CORE-11` Ahead with time low (P-06/P-09): play conservatively. Hold the power position, deny power weapons by timing, never cross the middle. Slow the game. Source: this is the standard "slow attrition" close-out.
- `SLAY-CORE-12` Ahead and enemy is forcing fights at our position: let them come; grenades on their approach, fall back one step at a time so they always fight uphill.

**Vehicle Slayer (Big Team)**
- `SLAY-BTB-01` Vehicle roles come first on spawn (VC-01). If the enemy tank is up, two bots on anti-vehicle before anything else.
- `SLAY-BTB-02` Vehicles farm infantry away from the enemy's power weapon spawns; the vehicle file's splatter and gunnery rules apply.
- `SLAY-BTB-03` Losing with time low: send every vehicle at the enemy spawn area together (one hard push), infantry follows for the clean-up kills.

### 1.3 SWAT subset (SWAT, SWAT Magnums, SWAT Arsenal, ShWATguns)

**Rule facts (Halopedia and Fandom):** no shields, no motion tracker, precision starting weapons (BR and Magnum in Halo 3; DMR or Magnum in Reach; BR or DMR in Halo 4). One headshot kills. Halo 3 playlist: 50 kills to win. ShWATguns = shotguns, timing-based.

**What changes versus Slayer:** no shield means no "back off and recharge" loop, no radar means no pre-aim from the tracker, and every first shot wins. Vehicles are usually off the map or lethal to use (an exposed driver dies to one headshot).

- `SLAY-SWAT-01` Aim level: the combat brain's default reticle height becomes head height at all times, and it leads shots at range in Halo 3 (Source: TL.net SWAT guide, Halo 3 requires leading at distance).
- `SLAY-SWAT-02` First shot wins: a bot never enters a sightline it has not pre-aimed. Movement is corner-to-corner, with the reticle on the far corner before the body arrives.
- `SLAY-SWAT-03` No melee duels. Source (Neoseeker Halo 3): one melee does not kill in Halo 3 SWAT. In Halo 4 SWAT a melee does kill (Halo Infinite guide notes a single melee kills without shields; verify per MCC game). Default: melee only when the enemy is inside 2 m and already facing away.
- `SLAY-SWAT-04` Pairs always. Source (Neoseeker): travel in pairs, check corners, call out positions. Role split: two pairs, each pair covers a lane; no lone anchor.
- `SLAY-SWAT-05` Reload discipline: reload only below 3 rounds or when fully out of sight (Source: NamuWiki SWAT tips); a reloading bot in a sightline is a dead bot.
- `SLAY-SWAT-06` Jump discipline: Halo 3 pros jump constantly to move the head (Source: TL.net); the combat brain enables "strafe-jump while being aimed at" only in Halo 3 and Halo 2, and disables jumping while crossing an open sightline in Reach and Halo 4 where the descend is slow.
- `SLAY-SWAT-07` No camping: with no radar the enemy can walk up behind a camper (Source: Fandom). Bots relocate after every 2 kills from the same spot.
- `SLAY-SWAT-08` Assassinations are easier with no radar (Source: Fandom); a bot that finds itself behind an enemy inside 3 m melees instead of shooting (guaranteed kill with no risk of a missed headshot).
- `SLAY-SWAT-09` Losing with time low: there is no "push through grenades" because grenades are usually off in SWAT. Instead: all four bots take one lane together and chain-peek, each bot stepping out one at a time so the enemy is always shooting at the previous peeker. Accept the trades; four-on-one peeks win.
- `SLAY-SWAT-10` Winning with time low: hold two overlapping sightlines on the enemy's spawn-side exits and never move. In SWAT a held crossfire is close to unbeatable.
- `SLAY-SWAT-11` SWAT Magnums: shorter effective range; the whole team's engagement range drops by 30 percent and lanes are chosen for short sightlines.
- `SLAY-SWAT-12` ShWATguns: shotgun timing; bots hold corners and fire only inside one-shot range, never chase in the open.
- `SLAY-SWAT-13` SWAT objective variants (SWAT CTF, SWAT Crazy King exist in MCC playlists): load the objective brain for that mode and overlay SWAT-01 through -08 as combat modifiers; carrier escorts form a moving corner-check formation around the carrier.

### 1.4 Snipers subset (Snipers, Team Snipers, Sniperfight)

- `SLAY-SNIPE-01` The whole team spreads to the two or three longest sightlines and never bunches; a sniper duel is decided by who is seen second.
- `SLAY-SNIPE-02` No-scope only inside 10 m; otherwise scope, but scope only after confirming no enemy inside 15 m (the scoped bot is blind to flanks).
- `SLAY-SNIPE-03` Relocate after every kill or every two shots revealed by tracer.
- `SLAY-SNIPE-04` Losing with time low: abandon long lanes, push through interior routes as a group to force close-range no-scope and melee fights where the enemy's sightline advantage is gone.
- `SLAY-SNIPE-05` Winning with time low: hold the longest lanes from maximum range, do not peek, do not relocate toward the enemy.

### 1.5 Rockets, Swords, Fiesta, Phantoms, Endurance

- `SLAY-ROCK-01` Rockets: never fire inside 8 m of your own position (self-kill). Hold high ground; rockets fired down are safer. Jump-shot when being rocketed (airborne splash is reduced).
- `SLAY-SWORD-01` Swords: lunge range is the only range. Bots hold corners and lunge first. Never approach head-on in the open; two swords clash and the first lunge usually wins.
- `SLAY-FIESTA-01` Fiesta: random weapons each spawn. On spawn, the brain classifies the loadout (power, precision, close, trash) and assigns the bot a range band for the life; a bot with trash weapons plays support and scavenges drops.
- `SLAY-PHANT-01` Phantoms (everyone has active camo): radar is useless; bots hold still at chokepoints (camo breaks on movement and fire), fire only on confirmed silhouettes, and move at walking speed. Winning posture: stay still. Losing posture: move together so each bot's shimmer covers the others.
- `SLAY-ENDUR-01` Endurance (CE: health does not regenerate between lives): every engagement is evaluated on current health, not shields; a damaged bot goes CONSERVATIVE on its own even if the team is AGGRESSIVE.

### 1.6 Elimination / Duel / one-life subset

**Rule:** lives per round = 1 (or a small number); a round ends when one team is wiped.

- `SLAY-ELIM-01` Posture starts CONSERVATIVE regardless of score. No lone pushes ever.
- `SLAY-ELIM-02` Formation: all bots within 15 m of each other, one lead, two covering, one rear. Movement is leapfrog: the lead moves only when both coverers have sightlines on its next position.
- `SLAY-ELIM-03` Every engagement must be a 2-on-1 or better. A bot that is alone backs off to the group even if it is winning.
- `SLAY-ELIM-04` Grenades are opening moves, not reactions: throw to flush, then shoot the flush.
- `SLAY-ELIM-05` Numbers matter more than position: when we outnumber (3 v 2), the team rotates to cut the map in half and pins the enemy pair against an edge. When we are outnumbered, retreat to the tightest defensible interior with a single approach and hold it; make the enemy come to us.
- `SLAY-ELIM-06` Last bot alive: never fights fair. It hides, uses the radar (if on) to pick fights only against a single approaching enemy, and makes the round time out if the round can end on time.
- `SLAY-ELIM-07` Power weapons matter twice as much because they cannot be picked back up by respawners; the team moves as a group to the rocket or sniper spawn first.
- `SLAY-ELIM-08` Phantom Elimination (camo, one life): hold still at a chokepoint; the first mover dies.

### 1.7 Regicide and Infinity Slayer (Halo 4) modules

- `SLAY-REG-01` Regicide (FFA; the leader is the King with a growing bounty; Source Halopedia): bounty value drives the target weight: King 2.0 plus 0.1 per bounty tier. The brain avoids being King when close to the leader's score by not killing weak targets when within 2 points of the lead and a stronger player is nearby (being King draws every gun).
- `SLAY-REG-02` When our bot is King: hold a corner with a single approach, use the Overshield the King earns after 20 s, and only fight when the attacker is alone.
- `SLAY-REG-03` Infinity Slayer (loadouts, ordnance): the brain picks a loadout per role (precision for ANCHOR, close for SLAYER, EMP/plasma for anti-vehicle) and calls ordnance on the power position the moment it is earned; a bot never calls ordnance into a contested area.

---

## Part 2. King of the Hill family

### 2.1 Variants and which share a brain

| Variant | Rule facts | Brain |
|---|---|---|
| King / King of the Hill (FFA or team) | Hill is static. CE: 2 minutes control; Halo 2: 2 minutes; Halo 3: 100 points, 1 point per second on hill; Reach: 150 points | KOTH-STATIC |
| Team King | Halo 2: 1 minute uncontested control; Halo 3 Team King 150, "Team Control" scoring where the hill must be uncontested; Halo 3 default On Hill 1, Uncontested Control 0 | KOTH-STATIC with `uncontested` flag |
| Crazy King / Team Crazy King | Hill moves. CE: every minute; Halo 2 Crazy King; Halo 3 default Hill Movement 30 s, random order; Reach default "Crazy Random King", 30 s | KOTH-MOVING |
| Mosh Pit (Halo 3) | Single unmoving hill; everyone inside is tougher (On Hill Traits) | KOTH-STATIC with `hill_traits` |
| Phantom King (CE, H2A) | Everyone has active camo, hill does not move | KOTH-STATIC with camo overlay (Phantoms rules from 1.5) |
| Kill from the Hill (H2A) | Points for kills while inside the hill | KOTH-STATIC with `kill_scoring` |
| King Pro (CE) | King with pro settings | KOTH-STATIC |
| Reach: hill can be placed on a vehicle | Halopedia | KOTH-VEHICLE overlay |

Scoring detail that drives the logic: Halo 3's "Uncontested Control" means an enemy inside the hill stops your score even if you outnumber them. Halo 2 Team King is uncontested control only. Reach and most Halo 3 variants give 1 point per second per team while any teammate is inside and no enemy is (team control), not per player.

### 2.2 Roles

- **SCORER** (1): the only bot that stands in the hill. Everyone else keeps the hill clear.
- **RING** (2): hold the two best positions that overlook the hill's approaches, outside the ring. Source (Halopedia KOTH): one scores, the rest fan out and defend.
- **ROAMER** (1): controls the power weapon and intercepts enemies before they reach the ring; becomes the next SCORER if the current one dies.
- Big Team: add **VEHICLE** roles per vehicle file (tank or Warthog parked outside the ring covering the main approach: `H3-KOTH-02`, `REACH-KOTH-02`).

### 2.3 Static hill logic

**We hold the hill**
- `KOTH-STATIC-01` Only the SCORER enters. Two bots in the hill is one extra death to a grenade for zero extra points (team control scoring).
- `KOTH-STATIC-02` SCORER stands on the edge of the ring farthest from the main enemy approach, crouched behind any cover inside the ring, and keeps the reticle on the approach.
- `KOTH-STATIC-03` RING bots never fire into the hill while the SCORER is in it unless the enemy is already inside (then the hill is contested and not scoring anyway, so clearing it is the priority).
- `KOTH-STATIC-04` Enemy enters the hill: the hill stops scoring. RING and ROAMER throw grenades into the hill (the SCORER steps out of the ring for the grenades if the enemy is inside), then push in. SCORER re-enters the instant it is clear.
- `KOTH-STATIC-05` SCORER dies: ROAMER becomes SCORER and moves in; a RING bot becomes ROAMER. The hill must never be empty for more than the respawn time.

**Enemy holds the hill**
- `KOTH-STATIC-06` Snipe from distance first. Source (user spec and standard play): the enemy scorer is a stationary target. Any bot with a precision or power weapon takes the longest sightline onto the ring and shoots the scorer before anyone pushes. A dead scorer stops their clock.
- `KOTH-STATIC-07` Contest beats clear. If we cannot kill them, one bot entering the ring stops their score (team control scoring). In DESPERATE posture a bot runs into the ring to die if that is what it takes to stop the clock while the others set up.
- `KOTH-STATIC-08` Use vehicles to take the objective. Big Team: a Warthog or Ghost drives through the ring to splatter the scorer, then exits (`H3-KOTH-06` Chopper sweep); a Scorpion or Wraith shells the ring from outside; a Banshee bombs the ring from above where tanks cannot reach it. Vehicles do not park inside the ring; infantry scores.
- `KOTH-STATIC-09` Grenade the hill before every push. Three grenades into a ring force the scorer out or kill them; the push goes in on the explosions.
- `KOTH-STATIC-10` Never push one at a time. A lone pusher dies to the RING players. Minimum two, ideally three, with the fourth sniping.

**Posture scenarios**
- `KOTH-STATIC-11` We are ahead and time is low: the SCORER does not have to score; it only has to keep the enemy from scoring. Move the SCORER to the ring's edge and the RING bots to overlapping sightlines on every entrance; posture CONSERVATIVE; nobody leaves the hill area for power weapons.
- `KOTH-STATIC-12` We are behind and time is low: `closing` tells us how many seconds they need. If they need fewer seconds than remain, every bot goes DESPERATE on the ring: constant contest, constant grenades, vehicles rammed through it.
- `KOTH-STATIC-13` Uncontested scoring variants (Halo 2 Team King, Halo 3 Team King): contesting is worth exactly as much as clearing. A bot that cannot win the hill still runs into it.
- `KOTH-STATIC-14` Mosh Pit (tougher inside): the hill is also the safest place to fight. The SCORER fights from inside; attackers must enter to kill it, so the RING collapses tighter around the hill.
- `KOTH-STATIC-15` Kill from the Hill (H2A): kills only count inside the hill, so the SCORER role becomes two bots that both stand inside and shoot out; RING feeds them targets by pushing enemies toward the hill rather than killing them outside it.

### 2.4 Moving hill (Crazy King) logic

- `KOTH-MOVING-01` Know the order. Halo 3 default order is random, but some playlists use a fixed sequence; the brain records the sequence seen in the first cycle and predicts from then on (Hill Movement Order setting).
- `KOTH-MOVING-02` Timing: with a 30 s move timer, send the ROAMER toward the next likely hill at T-10 s. The first team in the new hill scores first and spawns the fight on its terms. Source: `CE-KOTH-03`, `H2-KOTH-03`, `H3-KOTH-04` in the vehicle file.
- `KOTH-MOVING-03` Do not over-commit to a hill that is about to move. If the hill will move in under 8 s and we do not hold it, nobody pushes it; everyone rotates toward the next one.
- `KOTH-MOVING-04` Vehicles are the rotation tool. Ghost and Mongoose reposition fastest; a Ghost bot's job in Crazy King is to be first to every new hill, contest it, and get out when infantry arrives.
- `KOTH-MOVING-05` Ahead with time low: rotate early to every hill and hold its edge; never fight for the current hill after the halfway point of its timer.
- `KOTH-MOVING-06` Behind with time low: skip the current hill entirely if the enemy holds it strongly; set up on the next one with everyone and take the full 30 s there.

### 2.5 Vehicle hill (Reach)

- `KOTH-VEH-01` The hill is on a vehicle: the SCORER drives it (or rides it); the ESCORT keeps enemies off it. The driver never stops in the open and never leaves the vehicle while scoring.
- `KOTH-VEH-02` Enemy holds the vehicle hill: EMP it (Plasma Pistol overcharge) so it stops, then board; a stopped hill vehicle is a stationary target for everyone else.

---

## Part 3. Oddball family

### 3.1 Variants

| Variant | Rule facts | Brain |
|---|---|---|
| Oddball (FFA) / Team Ball / Team Oddball | Hold the ball to score; carrier cannot fire; ball melee is lethal (Halo 2 default "Massive"); carrier moves slow (Halo 2 "Slow With Ball"; Reach carrier speed 75 percent, passenger-only vehicle use) | ODD-CORE |
| Lowball | Points for the player who has held the ball the least (Halo 3) / Lowball hold time 30 s (H2A) | ODD-LOW |
| Ninjaball (Halo 3) | Carrier is fast and fragile | ODD-CORE with `fast_fragile` |
| Rocketball, Swordball, Fiesta ball | Weapon starts; carrier rules unchanged | ODD-CORE |
| Hot Potato (Reach) | Ball is a bomb; fuse 30 s; pass it before it goes | ODD-POTATO |
| Reverse Tag / Accumulate (CE) | Reverse Tag: everyone hunts the carrier; Accumulate: hold multiple balls (Rule from CE gametype list; detailed scoring not verified) | ODD-CORE |
| Keepaway (Halo 5) | Not in MCC | none |

### 3.2 Roles

- **CARRIER** (1): holds the ball, does not fight, moves between pre-planned hold spots.
- **BODYGUARD** (1): within 5 m of the carrier at all times; fights anything that reaches melee range (`H4-ODD-03`: carriers have one-hit melee, so the bodyguard keeps enemies off the carrier's back and lets the carrier melee anyone who gets in front).
- **RING** (2): hold the approaches to the hold spot, same geometry as KOTH.

### 3.3 Core logic

**Hold spots (Proposed, computed per map)**
- `ODD-CORE-01` A hold spot scores on: single approach (weight 3), cover from long sightlines (2), elevation (2), escape route to a second hold spot within 20 m (2), distance from enemy spawn (1). The brain picks the top three and the carrier rotates between them only when forced.
- `ODD-CORE-02` The carrier never stands in a hallway or on a path; always a corner, a room, or a ledge with the approach visible to the RING.

**We have the ball**
- `ODD-CORE-03` Carrier dies: the ball drops where it died. The BODYGUARD becomes the carrier only if it can pick up and reach cover within 3 s; otherwise the team clears the area first. Picking up in the open is how the ball is lost twice.
- `ODD-CORE-04` Carrier under attack with no bodyguard: drop the ball behind cover, kill the attacker, pick the ball back up (same logic as the Halo 2 Assault carrier rule, `H2-ASS-04`).
- `ODD-CORE-05` Vehicle use: carrier is passenger-only in Reach; in Halo 3 the carrier can ride any passenger seat (`H3-ASS` bomb rules apply to the ball by analogy). A carrier in a Warthog bed is only safe on open maps with an escort hog; indoors, stay on foot.
- `ODD-CORE-06` Carrier melee: lethal one-hit. If an enemy comes around the carrier's corner alone, the carrier steps in and melees rather than running.

**Enemy has the ball**
- `ODD-CORE-07` Find it: the ball indicator (Halo 2 "Always On", Halo 3 Ball Indicator enabled) shows the carrier. All bots converge on the indicator's approach, not on the indicator; the carrier is in a corner, and the fight is at the door.
- `ODD-CORE-08` Kill the bodyguard first; the carrier cannot shoot. Target weights: bodyguard 1.8, ring 1.2, carrier 1.5 (only when the carrier is reachable without crossing the bodyguard).
- `ODD-CORE-09` Grenades into the hold spot before entering; the carrier cannot escape quickly (slow with ball).
- `ODD-CORE-10` Vehicle pursuit (Big Team): a carrier moving between hold spots in the open is the best splatter target in the game (slow, cannot shoot); vehicle file ram rules apply with the carrier weight 2.0.

**Posture scenarios**
- `ODD-CORE-11` Ahead with time low: hold the single best spot and do not rotate; collapse the RING to within 10 m; nobody chases a dropped ball into the open.
- `ODD-CORE-12` Behind with time low: the ball must change hands. All four push the hold spot together with grenades; the first bot to touch the ball sprints it away in the opposite direction while the other three stand in the doorway and die if needed to buy the carrier 10 s.
- `ODD-CORE-13` Ninjaball (fast, fragile carrier): the carrier keeps moving; hold spots are replaced by a loop around the map with the RING chasing in a chain behind it.
- `ODD-CORE-14` Lowball (score for holding least): invert everything. The team's goal is to touch the ball briefly and drop it on an enemy; bots never hold it; the "carrier" grabs, runs 3 s toward the enemy, drops it in their path, and leaves. Rings camp the ball's spawn to kill enemies forced to pick it up.
- `ODD-CORE-15` Hot Potato (Reach): the carrier walks toward the nearest enemy and drops or throws the ball at them before the fuse (30 s default) expires; no hold spots; the team pushes to force the enemy to catch it.

---

## Part 4. Capture the Flag family

### 4.1 Variants and shared brains

| Variant | Rule facts | Brain |
|---|---|---|
| Multi Flag CTF / CTF (two flags) | Each team has a flag; 3 captures to win (Halo 2 and 3 default); Flag at Home to Score off by default in Halo 2 and 3, on by default in Reach; flag return time 15 s (Halo 3 and Reach), flag reset 30 s | CTF-MULTI |
| One Flag CTF / 1 Flag CTF Fast / One Flag Classic | Asymmetric rounds; one team attacks the single flag, the other defends; Halo 3: 4 rounds; sudden death if the flag is out when time expires | CTF-ONE |
| Neutral Flag CTF | One flag in the middle; capture to your own base (H2A and Reach) | CTF-NEUTRAL |
| Classic CTF / Warlock Classic CTF / CTF Classic (Halo 2) | Flag must be at home to score; return time is instant-touch in some classic variants | CTF-MULTI with `flag_at_home` |
| CTF Pro / Iron CTF (CE) | CE: Iron CTF uses limited settings; CE has no instant-kill flag (flag damage is low) and no boarding | CTF-MULTI with CE overlays |
| Tank Flag (Halo 3) | Carrier very tough, very slow | CTF-MULTI with `tank_carrier` |
| Attrition Flag (Halo 3) | Limited lives per round (Attrition) | CTF-MULTI with 1.6 Elimination overlay |
| Gungoose CTF (H2A) | Use a Gungoose to steal and score | CTF-VEHICLE |
| Vehicle CTF (Halo 4 setting) | Carrier can drive | CTF-VEHICLE |
| SWAT 2 Flag / SWAT CTF | SWAT traits on CTF | CTF-MULTI with SWAT overlay (1.3) |
| Invasion phase 3 (Reach) | Core carried to a Pelican/extraction point, passenger-only vehicle use, 30 s core return | see Part 8 |

Carrier traits that change behavior: Reach carrier speed is 75 percent, passenger-only vehicles, and a 1 s "flag carrier cooldown" after dropping; Halo 2 "Slow With Flag" on by default; flag hit damage "Massive" (one-hit melee); Halo 4 flag carriers auto-pull a pistol and cannot drop the flag unless the setting allows (Halo 4 rule: flag cannot be dropped at will in default Halo 4 CTF; flagnum pistol), which changes the "drop and fight" rule below.

### 4.2 Roles

- **RUNNER** (1): grabs and carries.
- **ESCORT** (1 or 2): within 8 m of the runner, in front on the way in and behind on the way out.
- **DEFENDER** (1): never leaves our flag room unless our flag is taken (then becomes a HUNTER).
- **HUNTER** (floating): chases the enemy carrier when our flag is out.
- Big Team: **DRIVER** and **GUNNER** for the escort hog; **AIR** for Banshee/Hornet carrier cover; **ANCHOR** for tank at base.

### 4.3 Multi Flag brain

**Phase A: flags home, no carrier active**
- `CTF-MULTI-01` Default stance by posture: BALANCED = 1 defender, 1 runner, 2 escorts pushing as a unit toward the enemy flag along the route with the most cover. CONSERVATIVE = 2 defenders, 1 runner, 1 escort. AGGRESSIVE = 1 defender, 3 on the push. DESPERATE = 0 defenders, 4 on the push.
- `CTF-MULTI-02` Power weapons before the push (PW-01). A rocket or sniper in the escort's hands is what gets the runner out of the enemy base.
- `CTF-MULTI-03` Vehicles: the escort hog carries runner (passenger bed) plus gunner; it drives to within 25 m of the enemy flag, drops the runner, and circles (`H2-CTF-02` cram rule, `REACH-CTF-02` keep the vehicle gunning and moving).

**Phase B: we grab their flag**
- `CTF-MULTI-04` Route choice: never the center (`H3-CTF-05` outskirts route). The brain pre-computes two return routes per map and the runner picks the one with no enemy on radar and no enemy vehicle on its lane.
- `CTF-MULTI-05` Runner never fights. If engaged with an escort present, keep moving; the escort fights. If engaged alone: drop the flag behind cover, fight, re-grab (`REACH-CTF-01`). Halo 4 default: the flag cannot be dropped; the runner uses the flagnum pistol and keeps moving to the nearest escort instead.
- `CTF-MULTI-06` Flag juggling (Source: standard Halo technique, works in CE through Reach): throwing the flag forward and re-grabbing moves it faster than carrying when the runner is unescorted and unpressured; the brain enables juggling only when no enemy is on radar within 20 m, because a juggling runner is helpless mid-throw.
- `CTF-MULTI-07` Vehicle return: in Halo 3 the runner rides as a passenger; a Warthog return is the fastest capture on open maps. The gunner faces rear. Never take a Mongoose through a lane an enemy vehicle controls.
- `CTF-MULTI-08` Flag at home to score (Classic and Reach default): if our flag is out, the runner does NOT run into our base to wait; it holds the enemy flag in a safe spot near our base while the HUNTER returns ours (this denies the enemy a capture and keeps ours ready).
- `CTF-MULTI-09` Flag return mechanics: Halo 3 and Reach return the flag 15 s after it is dropped with no enemy touching it; touch-return exists in some variants. A dropped enemy flag near their base should be picked up again within 15 s or it goes home; a dropped enemy flag near our base can be left on the ground as bait while the escorts hold the angle on it.

**Phase C: enemy grabs our flag**
- `CTF-MULTI-10` DEFENDER calls it. Every bot not escorting our own carrier becomes a HUNTER. Target weight on the enemy carrier 2.0, on their escorts 1.5.
- `CTF-MULTI-11` Intercept, do not chase. The carrier is slow (75 percent speed in Reach, "Slow With Flag" in Halo 2). Hunters move to cut off the carrier's route to their base, not to where the carrier is now. The brain predicts the route from the carrier's heading and the two known return routes.
- `CTF-MULTI-12` Vehicle intercept: `H3-PUR-04` Chopper, `H2-PUR-01` rocket lock, `REACH-PUR-02` Banshee fuel rod on a carrier hog, and the universal "head-on Warthog ram kills a Ghost" rule. A carrier in a vehicle dies to a flipped vehicle; aim at the vehicle, not the carrier.
- `CTF-MULTI-13` Return priority: once the carrier is dead the flag sits on the ground; in Reach and Halo 3 it returns after 15 s untouched, or instantly on touch in touch-return variants. One bot touches it; the rest hold the enemy off that bot.
- `CTF-MULTI-14` Both flags out: the team with the better position wins the standoff. If ours is closer to home than theirs is to their home, HUNT first; if theirs is closer, ESCORT first and let the DEFENDER stall.

**Posture scenarios**
- `CTF-MULTI-15` Ahead 2-0 or more with time low: posture CONSERVATIVE; 2 defenders plus the tank or Warthog parked over our flag (`H3-DEF-01`, `H3-DEF-04` Elephant wall); the other two hold the enemy flag in a safe place if they can get it, otherwise they hold mid and never cross.
- `CTF-MULTI-16` Behind with time low: DESPERATE. 0 defenders. Everyone goes for their flag; the runner grabs and the other three stand between the runner and every enemy. If sudden death is enabled, the capture only needs to be in progress when time expires to extend the game; the brain uses the last 20 s to get a touch on the flag no matter what.
- `CTF-MULTI-17` Enemy tank or Wraith is up and we are behind: the escort group cannot cross the map. Two bots go anti-vehicle first (EMP plus board or rockets); the runner waits at the edge of the tank's lane and goes only when the tank is dead or disabled.
- `CTF-MULTI-18` Enemy Banshee is up: the runner never rides in a Warthog or Mongoose (fuel rod flips them); on foot under cover, and the anti-air role spawns first (VC-02).
- `CTF-MULTI-19` Tank Flag: the runner is tough and slow; the escorts' job is to kill everything in front of it rather than protect it; the Chopper is the enemy's best counter (`H3-PUR-06`), so the escorts kill Choppers first.
- `CTF-MULTI-20` Attrition Flag (limited lives): overlay 1.6; the runner never goes unless two escorts are alive.
- `CTF-MULTI-21` CE CTF: no boarding, flag does low damage, vehicles indestructible in MP; the `CE-CTF-01` through `CE-CTF-05` Blood Gulch tactics apply (enter-grab-leave in a hog, teleporter parking).

### 4.4 One Flag brain (asymmetric rounds)

**Attacking round**
- `CTF-ONE-01` There is no defender role. All four attack; roles become RUNNER plus 3 ESCORTS. The enemy knows exactly where we are going, so the attack is about speed and overload, not stealth.
- `CTF-ONE-02` Timing rounds: Halo 3 One Flag has a per-round time limit. The brain tracks round time; a capture started late is worth a sudden-death extension (if enabled), so the final push is timed to have the runner touching the flag at T-15 s at the latest.
- `CTF-ONE-03` Grab and go pattern: ESCORTS enter the flag room first and clear; the RUNNER enters only on the "clear" callout; two escorts leave before the runner to hold the exit, one escorts from behind.
- `CTF-ONE-04` Back door first (`H3-CTF-08`): the flag room's secondary entrance is the attack entrance; the main entrance gets a decoy (one bot firing from range to pull defenders).
- `CTF-ONE-05` Vehicle attack: the Warthog drives into the base to draw fire and absorb the defenders' grenades (`H3-CTF-03` Warthog havoc), the runner comes on foot behind it. If the map gives the attackers a tank or Wraith, it shells the flag room doorway from outside before the push.
- `CTF-ONE-06` Losing the round (no capture, time low): if the flag is out of its base, keep it out at all costs; a flag that is out when time expires triggers sudden death in most One Flag variants. Hide the carrier in the farthest corner and stack all three escorts on the approach.

**Defending round**
- `CTF-ONE-07` 2 inside the flag room (one on the flag, one on the back door), 1 on the main entrance overlook, 1 ROAMER who controls the power weapon and warns of the vehicle push.
- `CTF-ONE-08` The flag room is a kill box: grenades at the door, melee on anyone who gets to the flag. Defenders never leave the room to chase; the ROAMER does the chasing.
- `CTF-ONE-09` Carrier escapes: every defender hunts. Slow carrier, known destination; intercept the exit route, not the carrier. Return on touch if the variant allows; otherwise guard the dropped flag for 15 s until it returns.
- `CTF-ONE-10` Round-score logic: if we have already captured in our attacking round and the enemy has not, the defending round is CONSERVATIVE from the first second; if the enemy out-captured us, DESPERATE defense means we accept losing players to kill the carrier (spawn and run straight at the carrier).

### 4.5 Neutral Flag brain

- `CTF-NEUT-01` The flag starts in the middle. The first 15 s are a slayer fight for mid with grenades; the runner hangs back until two enemies are dead.
- `CTF-NEUT-02` Capture is to OUR base, so the return route is the same every time and the enemy knows it; the escort holds the route's chokepoint in advance, before the grab.
- `CTF-NEUT-03` Enemy grabs it: they are running toward THEIR base; the intercept point is between mid and their base, and our defender (if any) is useless at our base, so there is no defender role in Neutral Flag.
- `CTF-NEUT-04` Dropped mid flag: leave it as bait when we hold the better position; take it when we hold mid.

### 4.6 Vehicle CTF brain (Gungoose CTF, Halo 4 Vehicle CTF)

- `CTF-VEH-01` The carrier can drive (Halo 4 setting) or the vehicle itself steals the flag (Gungoose CTF). The runner is a driver; the escorts are the other vehicles. Everything in the vehicle file's pursuit and ram sections applies to both sides at once.
- `CTF-VEH-02` The flag stand is approached at speed and left at speed; no stopping. Gungoose CTF: the Gungoose drives through the flag; the escort Gungoose rams any enemy Gungoose head-on (a Mongoose-class ram only kills at full speed and square contact).
- `CTF-VEH-03` Counter: splatter kills in Vehicle CTF are the primary defense; the defender vehicle parks at the flag with its nose on the approach lane (`H3-DEF-03` road block).

---

## Part 5. Assault, Ricochet, and Grifball family

### 5.1 Variants

| Variant | Rule facts | Brain |
|---|---|---|
| Assault / Multi Bomb | Each team has a bomb to plant at the enemy arm site; 3 detonations to win; Halo 2 arm time 5 s with Sticky Arming (arm progress passes to a teammate in the circle if the carrier dies); Halo 3 default arm time instant, disarm 5 s, fuse 15 s, bomb reset 30 s; Reach arm 5 s, fuse 10 s, disarm 5 s | ASS-MULTI |
| One Bomb / One Bomb Fast / Single Bomb | Asymmetric rounds, attackers plant, defenders disarm | ASS-ONE |
| Neutral Bomb | One bomb in the middle; plant at the enemy base | ASS-NEUTRAL |
| Attrition Bomb (Halo 3) | Limited lives | ASS-MULTI with 1.6 overlay |
| Blast Resort (Halo 2/H2A), Half-Time Assault (H2A) | Variant settings; same core | ASS-MULTI |
| Grifball | Bomb variant: everyone has Gravity Hammer and Energy Sword; carrier is slow; arm instantly at the enemy goal; one life per carrier death resets | GRIF |
| Ricochet (H2A, Halo 4) | Ball; carry it into the enemy goal for 50 (Halo 4) or throw it in for less (20); Halo 4 default; ball resets on score; variants Half-Time, Quickochet, Multi-Team | RICO |

Carrier rules that matter: the bomb carrier can ride any passenger seat but not gunner (Halo 3, Halopedia), can stand on a tank and ride it, cannot fire, has a one-hit melee ("Massive" bomb hit damage), and while hidden the bomb disappears from view except that an enemy aiming at a vehicle carrying it sees a red icon. Dropping the bomb to hide it is a mistake: it respawns and the enemy will likely get it (Halopedia).

### 5.2 Roles

- **CARRIER**, **ARMER** (a second bot that stays inside the arm circle so Sticky Arming continues if the carrier dies; Halo 2), **ESCORT** (1 or 2), **DEFENDER** (1, at our arm site, because the enemy bomb is coming to it), **DISARMER** (any bot within 10 m of our arm site when the enemy plants).

### 5.3 Multi Bomb brain

**Planting**
- `ASS-MULTI-01` The arm site is known; the enemy will be there. The push is a siege, not a sneak: grenades on the site, then vehicles into the site to draw fire (`H2-ASS-05` drop-off vehicle, `H2-ASS-06` Scorpion blocks the arm site entrance), then the carrier.
- `ASS-MULTI-02` Halo 2 Sticky Arming: the ARMER enters the circle with the carrier. If the carrier dies mid-arm, the ARMER's presence keeps the arm timer running; the next bot picks up the bomb and finishes. Two bodies in the circle is correct in Halo 2; in Halo 3 (instant arm) one is enough and the second stays at the door.
- `ASS-MULTI-03` Halo 3 instant arm: the carrier touches the site and the fuse (15 s) starts; the whole team's job for 15 s is to keep every enemy off the bomb (disarm takes 5 s and more disarmers disarm faster, Halopedia). Stand on the bomb; melee anyone who reaches it; throw grenades on the bomb if an enemy is on it and no teammate is.
- `ASS-MULTI-04` Reach 5 s arm, 10 s fuse: the carrier needs 5 uninterrupted seconds; the escorts enter first and hold the circle clear for the arm, then the fuse.
- `ASS-MULTI-05` Carrier rides a vehicle: passenger seat only; on a tank, stand on top (`H3-ASS-02`) only when the tank is not under fire.
- `ASS-MULTI-06` Carrier attacked without escort: drop, fight, re-grab (`H2-ASS-04`). Never hide the bomb.
- `ASS-MULTI-07` Camo and Overshield on the carrier when available (PU-01, PU-02); Halopedia notes One Bomb maps usually have Active Camo somewhere.

**Defending our site**
- `ASS-MULTI-08` The DEFENDER stays within 10 m of our arm site at all times. The moment the enemy bomb is picked up (indicator), the DEFENDER calls it and the nearest two become DISARMERS.
- `ASS-MULTI-09` Enemy plants: everyone alive goes to the bomb. Disarm time 5 s and faster with more players; three bots on the bomb disarm it before the fuse on almost any setting. Kill the carrier only if they are standing on the bomb; otherwise ignore them and disarm.
- `ASS-MULTI-10` Vehicle defense: the tank parks facing the arm site entrance; a Warthog gunner covers the circle; the Elephant parks across the arm site on Sandtrap (`H3-DEF-04`).

**Posture**
- `ASS-MULTI-11` Ahead with time low: 2 DEFENDERS, 1 DISARMER standing on our site, 1 roaming; the bomb carrier role is not assigned. Deny the enemy bomb spawn by killing anyone who approaches their own bomb if it is on our half.
- `ASS-MULTI-12` Behind with time low: DESPERATE; 0 defenders; carrier plus 3 escorts on the enemy site; the plant goes in no matter how many enemies are there, because a planted bomb at time expiry forces the disarm fight and may extend the round.
- `ASS-MULTI-13` Enemy tank is up and we must plant: EMP it (Plasma Pistol overcharge) and board; a boarded tank parked at their arm site is the best shield the carrier can have.

### 5.4 One Bomb brain

- `ASS-ONE-01` Attacking: no defender; 4 on the push; Halopedia tactic on Sandtrap: move the enemy Elephant to the tower with the bomb, defend it, hop on with the bomb (`H3-ASS-05`); the Elephant then drives the bomb to the site (`H3-ASS-08`).
- `ASS-ONE-02` Attack timing: plant as early as possible to leave fuse time; if the round time will expire before a plant, keep the bomb out of its reset spot (a bomb left untouched resets after 30 s; the carrier holds it moving).
- `ASS-ONE-03` Defending: 3 inside or on the arm site, 1 ROAMER at the chokepoint the carrier must pass. Kill box rules from `CTF-ONE-08`. The disarm is faster with more players, so defenders stack the site, not the approaches.
- `ASS-ONE-04` Round score logic as `CTF-ONE-10`.

### 5.5 Neutral Bomb brain

- `ASS-NEUT-01` Mid fight first (as `CTF-NEUT-01`); the bomb goes to the ENEMY site, so the push route is known and the enemy defends their own site; there is a DEFENDER role here because the enemy can also carry the neutral bomb to our site.
- `ASS-NEUT-02` Whoever picks up the bomb pulls the whole map toward one site; the brain's posture goes AGGRESSIVE for the carrying team and the enemy's best response is to contest mid for the reset, so our DEFENDER moves up to mid when we carry.

### 5.6 Grifball brain

- `GRIF-01` Everyone has a Hammer and a Sword; the bomb carrier is slow and the arm is instant at the goal. Formation: carrier in the middle of a diamond, two hammer bots in front clearing, one behind.
- `GRIF-02` Hammer timing: a hammer swing has a wind-up; bots swing at predicted position; a sword lunge beats a late hammer, so bots carrying the sword lunge enemies who have just swung.
- `GRIF-03` Never cluster four bots in one spot: one hammer kills all four. Keep 4 m spacing except for the carrier's front guard.
- `GRIF-04` Enemy carrier: ignore everyone else; hammer the carrier. Carrier melee is lethal, so approach from the side, never the front.
- `GRIF-05` Behind with time low: the carrier runs it straight with no formation; three hammer bots sprint ahead to body-block.

### 5.7 Ricochet brain

- `RICO-01` Carrying the ball into the goal scores more than throwing it (Halo 4: 50 for a carry, 20 for a throw; default values from Halopedia's Halo 4 rules, verify H2A). Carry when the lane is clear; throw when it is not.
- `RICO-02` Throws can be intercepted (Interception medal); the thrower aims high and short so the ball lands in the goal, not through a defender's path.
- `RICO-03` Passing: a bot under pressure throws the ball to the nearest teammate who has a clear lane to the goal rather than fighting (Long Bomb and Nice Catch medals exist, so passing is a designed play).
- `RICO-04` Defense: one GOALKEEPER stands in the goal mouth and body-blocks thrown balls (Rejection, Goal Keeper medals); the others play the slayer game at mid.
- `RICO-05` Behind with time low: throw from max range at every opportunity (20 points beats 0) and keep a bot in the enemy's half to catch rebounds.

---

## Part 6. Territories, Dominion, and Extraction family

### 6.1 Variants

| Variant | Rule facts (Halopedia Territories page and custom-game settings) | Brain |
|---|---|---|
| Territories (Halo 2) | 4 territories (configurable 1 to 4); contest time 5 s, control time 5 s; score to win 5 minutes of control | TERR-SYM |
| 3 Plots (Halo 2, H2A) | 3 territories; earn 3 minutes control by owning a majority | TERR-SYM with `majority` |
| Land Grab (Halo 2, 3, Reach, H2A) | Every territory is up for grabs; locks once captured (Halo 3: 3 rounds; H2A: 1000 points) | TERR-LOCK |
| Gold Rush / Control Issues / Contention / Lockdown (Halo 2, H2A) | Named presets: Gold Rush is pistol/shotgun, 150 points, 4 rounds; the others vary lock and scoring; read from the gametype | TERR-SYM or TERR-LOCK by settings |
| Territories (Halo 3, Reach asymmetric) | One team defends all territories, the other captures; Halo 3: 4 rounds, capture time 30 s, lock after capture on by default, one-sided on by default; Reach default 5 territories, 30 s capture, asymmetric | TERR-ASYM |
| Flag Rally (Halo 3) | Territories do not lock; hold what you can until the round ends | TERR-SYM |
| Dominion (Halo 4, 6v6) | 3 bases; capture, fortify (0 points), resupply every 25 s for 10 points; base gives ordnance and vehicles each supply cycle; capturing all three puts the enemy into Last Stand (sudden death, red markers, kill them all to win); score limit 400 by default; Lockdown variant has no turrets or shield doors and no last stand | DOM |
| Extraction (Halo 4, 5v5) | Arm a beacon at a site; defend it while it extracts; the enemy can convert an armed beacon to their side; new sites open over time; score per extraction | EXTR |

### 6.2 Roles

- **CAPPER** (stands in the territory for the capture timer), **GUARD** (holds the capped territory's approach), **ROTATOR** (moves between territories to contest), **VEHICLE** roles (Big Team: a tank or Warthog parked at the most contested territory is worth a player).

### 6.3 Symmetric Territories (Halo 2, 3 Plots, Flag Rally)

- `TERR-SYM-01` Majority math: with 3 territories you need 2; with 4 you need 3. The brain picks the two (or three) territories closest to our spawn and the one in the middle; it never splits across the map.
- `TERR-SYM-02` Capturing takes an uninterrupted stay (Halo 2: contest 5 s then control 5 s; Halo 3 30 s). The CAPPER crouches in the territory out of sightlines; the GUARD stands outside it, because an enemy entering the territory contests it (Halo 2 contest timer) and stops the capture.
- `TERR-SYM-03` Control time accrues while you hold the majority; losing one territory stops the clock. Therefore the ROTATOR never leaves the majority set undefended to chase a fourth.
- `TERR-SYM-04` Enemy contests one of ours: the ROTATOR and the GUARD of the nearest territory converge; grenades into the territory first (an enemy inside is standing still to capture).
- `TERR-SYM-05` Flag Rally (no lock): the game is continuous; roles rotate; the brain caps whichever territory is currently undefended and immediately leaves a GUARD.
- `TERR-SYM-06` Vehicles: Warthog gunner parked at the middle territory; Ghost ROTATOR between the outer ones (fastest contest); tank parked on the approach of whichever territory the enemy pushes most.
- `TERR-SYM-07` Ahead with time low: hold the majority only; abandon any attempt at a third/fourth; CAPPERS become GUARDS at the edge of their territories.
- `TERR-SYM-08` Behind with time low: flip one territory, not all. Pick the enemy territory with the weakest guard (fewest enemies seen in the last 30 s) and send three; a single flip breaks their majority and stops their clock.

### 6.4 Land Grab (lock after capture)

- `TERR-LOCK-01` Locked territories cannot be retaken; the whole game is a race for the uncaptured ones. On round start every bot sprints to a different territory; vehicles go to the farthest ones.
- `TERR-LOCK-02` A contested capture is a waste; if an enemy is inside with you, kill them or leave for an uncontested territory. The brain reassigns a CAPPER who has been contested for more than 10 s to the next nearest open territory.
- `TERR-LOCK-03` Once a majority is locked, the remaining territories are irrelevant to winning the round; posture flips to slayer-style CONSERVATIVE to run out the round time (if scoring is per round) or to a full push for the rest (if scoring is per territory, H2A 1000 points).

### 6.5 Asymmetric Territories (Halo 3, Reach)

**Defending (all territories start ours)**
- `TERR-ASYM-01` One GUARD per territory, on the approach, not inside. Capture takes 30 s; a GUARD who sees a capper has 30 s to interrupt it; entering the territory contests it and resets the timer in most settings.
- `TERR-ASYM-02` Lock after capture is on by default in Halo 3: a lost territory is lost for the round. Defense is therefore worth more than offense; a guard never leaves a territory to help another unless its own is empty of enemies.
- `TERR-ASYM-03` Vehicles park on the territories farthest from the attackers' spawn (the ones that take longest to reinforce).
- `TERR-ASYM-04` Round-score logic: defend to deny; if the attackers captured N in their attacking round, we only need to capture N+1 in ours, so the defending posture is CONSERVATIVE unless they captured everything.

**Attacking**
- `TERR-ASYM-05` Attack in a sequence, not at once: take the territory nearest our spawn with all four, lock it, then move to the next. Splitting four bots over five territories captures none.
- `TERR-ASYM-06` Vehicle entry: a Warthog delivers two cappers and circles; a tank shells the guard position for 30 s while the capture runs.
- `TERR-ASYM-07` Time low and capture count behind: pick the territory whose guard just died (spawn gap) and go.

### 6.6 Dominion (Halo 4)

- `DOM-01` Two of three (Source: Halo 4 developer commentary via Halopedia): consistently controlling two bases wins. The brain designates our two: the one nearest our spawn and whichever of the other two has the better vehicle or ordnance drop for our composition.
- `DOM-02` Resupply is the score (10 points per 25 s cycle per base held; fortify is 0). Holding a base through resupply cycles is the whole game; a base lost just before a resupply is worth capturing back before the next cycle.
- `DOM-03` Fortify only when safe: fortifying adds turrets and shield doors (not in Lockdown) and takes a bot out of the fight; one bot fortifies while three guard.
- `DOM-04` Base ordnance and vehicles spawn on supply cycles; the brain puts the VEHICLE role at the base that spawns the vehicle 5 s before the cycle.
- `DOM-05` Three-base capture triggers Last Stand: the enemy is marked and must be killed. Only attempt the third base when the enemy is down players and the score margin is not already winning; a failed third-base push loses the second base.
- `DOM-06` In Last Stand against us: scatter, never regroup (grouped markers die to one ordnance); each bot runs for a base to recapture it, which ends Last Stand.
- `DOM-07` Ahead with time low: hold two bases, fortify both, do not push the third.
- `DOM-08` Behind with time low: capture the enemy's weakest base right after their resupply (their bots leave to fight after collecting) and hold it through at least two cycles.

### 6.7 Extraction (Halo 4)

- `EXTR-01` A site is open; arm the beacon (short arm), then defend it through the extraction timer. Two bots at the beacon, two on the approach. Conversion by the enemy is the only way to lose an armed site, so the beacon itself is the thing to guard, not the site perimeter.
- `EXTR-02` Enemy arms first: convert, don't kill. A bot converting the beacon flips it to our side; killing the defenders without converting leaves it theirs. Convert Stopped medal exists, so expect the enemy to shoot converters: the converter needs a bodyguard.
- `EXTR-03` New sites open over time; the ROAMER moves to the next site before it opens, so we arm first.
- `EXTR-04` Ahead with time low: convert nothing; defend the current beacon until it extracts; stall at the next site.
- `EXTR-05` Behind with time low: contest every beacon with a converter plus two guards; an extraction in progress for the enemy must be converted or the game is over.

---

## Part 7. Juggernaut, VIP, Infection, Headhunter, Stockpile

### 7.1 Juggernaut family

**Rule facts:** one Juggernaut versus everyone; Halo 3 default 10 points, takedown 1 point, kill as Juggernaut 1 point, next Juggernaut is the killer, 3 s delay, Goal Zones off by default (Mad Dash turns them on: the Juggernaut scores by reaching goal zones). Reach Juggernaut: 150 points, Juggernaut has 200 percent damage resistance, 2x overshields with no recharge, 300 percent melee, Gravity Hammer, infinite ammo, 150 percent speed and jump, 10 s safe time; kill 5 points, Juggernaut kill 10 points. Halo 2 Juggernaut: extra damage, infinite ammo, overshield. Variants: 2 on 1, 3 on 1 (Halo 2 fixed teams), Ninjanaut (fast invisible Juggernaut), Phantom Fodder (everyone else has camo), Dreadnaut (tough), Multi-naut, Nauticide, Juggernaut Elimination.

**As a hunter (not the Juggernaut)**
- `JUG-01` The Juggernaut is a shared target: all hunters converge, but from different directions; a Gravity Hammer Juggernaut kills clumped hunters in one swing.
- `JUG-02` Range beats melee: hunters never close inside hammer range; precision fire from 3 angles brings down overshields that do not recharge (Reach).
- `JUG-03` Last hit matters: the killer becomes the next Juggernaut (Halo 3 default). The brain decides whether we WANT to be Juggernaut: in point-race variants where the Juggernaut scores kills (Reach 10 per kill), yes; in Mad Dash the Juggernaut scores by running goals, yes if we are fast; otherwise let a teammate (FFA) or the weakest enemy take it.
- `JUG-04` Safe time (Reach 10 s): do not waste ammo on a freshly spawned Juggernaut during its safe period; set up angles instead.
- `JUG-05` Phantom Fodder (hunters have camo): hunters stand still at the Juggernaut's likely path and fire only when it passes; moving breaks camo.

**As the Juggernaut**
- `JUG-06` Pick fights at chokepoints where only one hunter can approach at a time; never cross open ground where three angles can fire.
- `JUG-07` Hammer timing: swing at the predicted position; hunters strafe, so swing where they will be. Infinite ammo means spraying at range between hammer kills is free.
- `JUG-08` Mad Dash: the goal zone is the objective; the Juggernaut moves zone to zone along the route with the fewest sightlines and does not stop to fight.
- `JUG-09` Ninjanaut (fast, invisible): never engage head-on; approach from behind, melee, and move; hunters cannot track a moving camo at speed.
- `JUG-10` Overshield management: Reach overshields do not recharge; retreat to break contact when the shield bar is under a quarter and let hunters come one at a time.

### 7.2 VIP family (Halo 3)

**Rule facts:** VIP, One Sided VIP, Escort (VIP must reach goal areas), Influential VIP (VIP proximity traits boost teammates near it); 10 points; next VIP on next death by default; VIP Death End Round off by default.

- `VIP-01` The VIP never leads. Formation: two in front, VIP in the middle, one behind; the VIP holds the best weapon the team has if VIP traits boost damage, otherwise the VIP carries nothing that draws it into fights.
- `VIP-02` Enemy VIP is worth the round: target weight 3.0; everything else 1.0; hunters sacrifice to kill it.
- `VIP-03` Escort (goal areas): the VIP's route is planned to the goal with escorts clearing ahead; the VIP moves only when the next 20 m is clear; vehicles carry the VIP as a passenger on open maps.
- `VIP-04` Influential VIP: the proximity traits make teammates stronger near the VIP, so the team stays inside the influence radius and fights as a blob; the VIP stands in the center.
- `VIP-05` One Sided VIP: the defending team's VIP never leaves the safest room; attackers run the One Flag attack pattern (`CTF-ONE-01` to -05) at the VIP's room.

### 7.3 Infection and Flood family

**Rule facts:** Halo 3 Infection: starting zombies 25 percent, next zombie is the winner; Alpha Zombie (alphas are stronger), Save One Bullet (survivors have limited ammo), Hide and Seek. Reach Infection: 1 starting zombie, 5 rounds, 4 minutes each, zombies have Evade, higher speed, lower gravity, no shields (headshots kill them), survivors who commit suicide become zombies; Safe Havens (haven zones protect survivors, timer moves them). H2A: Infection, Cadre, Flight, Hunted. Halo 4 Flood: Flood players have energy shields, so headshots do not one-shot; Flood have claws (melee), infected count rises; last man gets traits.

**As a survivor**
- `INF-SURV-01` Group and hold (Source: Fandom and Halopedia): survivors who regroup in one defensible spot with a single approach survive; lone survivors die. The brain picks the spot by the ODD-CORE-01 hold-spot scorer with "single approach" weighted 5.
- `INF-SURV-02` Ammo is the clock (Source: Halopedia): conserve; headshots use less ammo than body shots; body shots use less than missing. Bots fire only on zombies inside their weapon's reliable range; shotgun inside 8 m, precision at range.
- `INF-SURV-03` Fire discipline by role: two bots shoot the approach, one watches the flank/back, one reloads at all times (staggered reloads so there is never a moment with everyone reloading).
- `INF-SURV-04` Headshots kill Reach zombies instantly (no shields); Halo 4 Flood have shields, so Flood need two shots or a shotgun; the brain reads `traits.zombie_shields` and sets the time-to-kill expectation.
- `INF-SURV-05` Never Armor Lock (Source: Halopedia): it just delays the infection and lets the pack arrive. Jetpack is the escape ability (Fandom): fly up and headshot down.
- `INF-SURV-06` Bait tactic (Source: Halopedia): one survivor stands slightly forward to pull zombies into the group's crossfire. Use only when four or more survivors are alive.
- `INF-SURV-07` Safe Havens: the haven moves on a timer; the group moves between havens as one, never splitting; the move is timed to arrive 5 s before the old haven expires.
- `INF-SURV-08` Last man standing: the last survivor gets buffs (Last Man traits). It stops holding and starts running loops with the buffed speed, firing backwards at the lead zombie; standing still as last man is how rounds end.
- `INF-SURV-09` Save One Bullet (limited ammo): no shots outside 10 m; melee is free; the group forms a melee wall with guns held for the alphas.
- `INF-SURV-10` Time low (round ends on time with survivors winning): hold, do not peek, do not chase a zombie; survival at the timer is the win.

**As a zombie**
- `INF-ZOMB-01` Zombies win by overload. Never attack one at a time; the pack gathers out of sightline and rushes together from two sides.
- `INF-ZOMB-02` Reach zombies: Evade and low gravity close distance fast but jumping slows the approach (Halopedia); the brain disables jumping for zombies except to reach ledges.
- `INF-ZOMB-03` Target the reloading survivor or the one facing away; survivors' fire discipline has gaps and the pack times the rush to a reload.
- `INF-ZOMB-04` Alpha Zombie: alphas lead; normals follow 2 s behind so the survivors' first volley hits the tough alpha.
- `INF-ZOMB-05` Flood (Halo 4): shields mean the Flood can absorb one precision shot; the Flood rush straight at the last survivor's spot rather than flanking, because the shield makes the frontal rush survivable.
- `INF-ZOMB-06` Hide and Seek: zombies search the map in a sweep pattern, splitting the map in halves, calling out any survivor seen; survivors in this variant hide rather than hold.

### 7.4 Headhunter (Reach)

**Rule facts:** kills drop skulls; deposit at a drop point to score; drop points move every 30 s by default (2 points on the map); 25 points to win; "Allow Instant Win" on by default (a large single deposit can win); the max-skull carrier gets traits; 8 minute limit; FFA by default, teams optional.

- `HH-01` Skulls are only worth something deposited; a bot carrying 3 or more skulls stops hunting and goes to the active drop point by the safest route (vehicle file `REACH-HH-01`, `REACH-HH-02`).
- `HH-02` Killing a carrier drops all their skulls: the highest-value target is the enemy with the most skulls; target weight = 1.0 + 0.3 per skull carried.
- `HH-03` Drop point timing: the point moves on 30 s; a bot that cannot reach the current point in time heads to where the next point will spawn (recorded order, as `KOTH-MOVING-01`).
- `HH-04` Instant win: if a bot holds enough skulls to win on deposit, the whole team (team variant) escorts it; in FFA the bot stops fighting entirely and sprints.
- `HH-05` Vehicles: a Mongoose or Warthog on the drop point route with a skull-carrying passenger is the fastest deposit; the ram rules apply to enemy carriers in the open.

### 7.5 Stockpile (Reach)

**Rule facts:** 4 flags spawn at random locations; carry them to your team's stockpile; every 60 s (collection time) flags in the stockpiles are collected for points (10 to win); flags can be stolen out of the enemy stockpile before collection (Lock Flags in Stockpiles off by default); carrier speed 75 percent, passenger-only vehicles.

- `STOCK-01` The collection timer is everything. Flags only count at the tick. The brain tracks the 60 s cycle; flags are moved to our stockpile to arrive before the tick, and the team guards the stockpile for the last 15 s before each tick.
- `STOCK-02` Stealing beats collecting: in the last 15 s before a tick, a bot that can pull a flag out of the enemy stockpile denies them a point and may add one for us; raids are timed to T-15 s.
- `STOCK-03` Roles: 2 RUNNERS (one per flag spawn side), 1 STOCKPILE GUARD (at our pile, especially before ticks), 1 RAIDER (at theirs before ticks). Vehicles carry runners as passengers to far flag spawns.
- `STOCK-04` Flag juggling (throw-and-grab) is faster than carrying at 75 percent speed when unpressured.
- `STOCK-05` Ahead with time low: all four guard our stockpile through each tick; no raids.
- `STOCK-06` Behind with time low: every flag on the map is targeted at once, and the raid at T-15 s uses two bots.

---

## Part 8. Invasion, Invasion Slayer, Generator Defense (PvP), Race

### 8.1 Invasion (Reach, 6v6)

**Rule facts (custom-game Invasion settings and Halopedia):** attackers default Elites; 3 phases, each 4 minutes; phase 1 and 2 objectives default Territories (capture one of two points), phase 3 default CTF (the core); offense respawn timer 20 s, defense 7 s; core return time 30 s; core carrier is passenger-only in vehicles; 2 rounds (teams swap); phase 1 has no vehicles and only part of the map; loadouts and vehicles unlock with each phase; mutual spawning (spawn on a living fireteam partner); Spire: carry the core to the top of the Spire then to a Pelican on the beach; Boneyard: core to the dropship area. Loss condition for attackers: fail any phase within 4 minutes.

**Attacking**
- `INV-ATK-01` Fireteams of two spawn on each other; a bot never dies in a place its partner cannot safely spawn (SP-01 style check); when a partner is alive in cover, the dead bot waits for the partner to be out of combat before spawning on them.
- `INV-ATK-02` Phase 1 (no vehicles): two territory points, capture one. Split 4 on the closer point and 2 as a decoy at the far one; swap if the defenders overcommit to the decoy.
- `INV-ATK-03` Phase 2: vehicles unlock. The VEHICLE roles take the Ghost/Wraith (Elites) or Warthog/Scorpion (Spartans) the instant the phase changes (`REACH-INV-03`), before the defenders can.
- `INV-ATK-04` Phase 3 (core): the core is a flag with passenger-only vehicle rules and a 30 s return. Carry route: on Spire, Falcon to the top, then down to the beach Pelican (`REACH-INV-01`); on Boneyard, Warthog or Wraith escort across the yard. Drop-and-fight is allowed (core returns in 30 s, not instantly).
  - **Correction: the core is carried as a turret, not a flag.** Its carrier cannot ride any vehicle, not even as a passenger, so there is no Falcon or Warthog carry: the carrier goes on foot (Spire: off the top onto a heat vent, then the beach), and vehicles move the escorts and the attackers who go for the core, never the carrier. Code: no Invasion ferry (director.vehicle_orders ferries only in CTF, Assault and Stockpile); any press with the core in hand drops it (Reach).
- `INV-ATK-05` Time per phase is 4 minutes: at T-60 s of any phase, posture goes DESPERATE; everyone on the objective, no respawn waiting, no vehicle farming.
- `INV-ATK-06` Loadout choice per phase: phase 1 plasma pistol plus needle rifle (shield pop and headshot); phase 2 add EMP for vehicles; phase 3 sword or shotgun for the core room fight.

**Defending**
- `INV-DEF-01` 7 s defense respawn is the advantage: defenders fight aggressively because they are back fast; attackers wait 20 s.
- `INV-DEF-02` Phase 1: one fireteam on each territory point, both points contested by standing in them (an attacker inside contests the capture).
- `INV-DEF-03` Phase 2: deny the attacker vehicles by holding their spawn points at the phase change; a Spartan with the Spartan Laser or a Plasma Launcher at the vehicle spawn ends the attack.
- `INV-DEF-04` Phase 3: the core room is a kill box (`CTF-ONE-08`); if the core gets out, intercept the route to the extraction point (Spire top and beach; Boneyard dropship); the 30 s return timer means a dropped core needs 30 s of denial, so stand on it.
- `INV-DEF-05` Time logic: every second spent contesting is a second off the attackers' 4 minutes; defenders in DESPERATE posture (attackers close to completing with little time) throw bodies at the objective because respawns are 7 s.

### 8.2 Invasion Slayer

- `INV-SLAY-01` Slayer with phases and unlocks: same loadout/vehicle timing as INV-ATK-03; the brain is SLAY-CORE with vehicle unlock events treated as power-weapon spawns (be there first).

### 8.3 Generator Defense (Reach PvP, 3 Spartans vs 3 Elites with Covenant NPC support)

- `GEN-DEF-01` Defending Spartans: 1 to 3 generators; lockdown a generator (30 s active, then cooldown) when the Elites push it, which makes it invulnerable; stagger lockdowns so one generator is always locked while the other is under cover of the team.
- `GEN-DEF-02` Attacking Elites: push one generator with all three plus NPC support; split only to bait a lockdown, then hit the other.
- `GEN-DEF-03` Weapon caches drop evenly for both sides; the ROAMER on each side takes the nearest cache at its drop.
- `GEN-DEF-04` Crashsite (solo score attack, one generator, one life, infinite-ammo DMR): stay on the generator, headshot priority, lockdown on every Hunter or Chieftain wave.

### 8.4 Race, Rally, Rocket Race, Gungoose Gauntlet, Velocity

- `RACE-01` Race: checkpoints in order; the bot drives the shortest valid line, uses boost on straights, brakes before corners, and never rams unless the rules give points for kills (Rocket Race does).
- `RACE-02` Rally: checkpoints in any order; the brain solves the shortest tour and drives it.
- `RACE-03` Rocket Race (Mongoose driver plus rocket passenger): the passenger fires at enemy Mongooses on straights; the driver avoids being in a straight line behind an enemy passenger.
- `RACE-04` Gungoose Gauntlet and Velocity (H2A): the driver fires the Gungoose LMGs at the Mongoose ahead; keep the vehicle on all four wheels (a flipped Mongoose loses the race).

---

## Part 9. Firefight brain (ODST and Reach)

Firefight is the one brain where the enemy is scripted AI rather than players, so the objective brain and the combat brain both change: the objective is survival through sets while spending lives wisely, and the combat rules are per enemy type.

### 9.1 Structure (Rule)

- **Waves, rounds, sets:** five waves make a round; three rounds make a set; a bonus round follows each set (ODST and Reach, Halopedia and Fandom). Reach's variant editor documentation (DavidJCobb): each round is one Initial Wave, three Main Waves, and one Boss Wave; every wave except the round's last ends when all but three enemies are dead; the last wave of a round ends when every enemy is dead; the bonus wave does not end when its enemies die.
- **Lives:** a shared pool (ODST 7 shared lives in classic Firefight; Reach matchmaking 10 lives with a 15 minute limit per the Reach guide; customs vary). Bonus rounds do not spend pool lives: a bot killed in a bonus round is out until the next set (AlteredGamer). Reach bonus round: all AI die automatically at its end.
- **Skulls:** ODST turns skulls on by round and set: Tough Luck, Catch, Black Eye by round; Tilt, Famine, Mythic by set; Iron on the bonus round; the bonus round has all skulls on and is all Grunts (Fandom). Reach matchmaking turns on skulls after each round (Mythic after round 1, Cloud after round 2 in one listed variant), customizable.
- **Difficulty:** Reach Firefight matchmaking defaults to Heroic.
- **Drops:** Phantoms deliver waves; on Reach bonus rounds a damaged dropship may spill its cargo. Phantoms drop Ghosts on Mombasa Streets (ODST); Wraiths and Choppers appear in later waves and on vehicle-capable maps.
- **Score multiplier:** rises with rounds survived and skulls; dying resets streak-based bonuses.

### 9.2 Firefight objective brain

**Roles:** ANCHOR (holds the defensive position with a precision weapon), CLEANER (close-range weapon, kills what reaches the position), PP (Plasma Pistol carrier for shield stripping and vehicle EMP), HEAVY (power weapon or ordnance user; also the designated Hunter-killer).

**Position**
- `FF-POS-01` Pick a hold with high ground, a roof (Wraith mortar immunity: the roofed main building on Lost Platoon, Steam guide), a single ground approach, and an escape route. Source (GameFAQs Reach thread): elevated platforms and stairs beat alcoves, because alcoves get grenade-cornered.
- `FF-POS-02` Move between two holds when the current one is grenade-saturated or a Wraith has the angle; never hold a position a dropship lands next to.
- `FF-POS-03` Weapon and ammo caches: the brain maps drop positions and routes one bot to resupply between waves only (the three-enemy rule means a wave "ends" with three alive; resupply then).

**Lives management (Proposed)**
- `FF-LIFE-01` Posture by pool: lives >= 6 BALANCED; 3 to 5 CONSERVATIVE; 1 to 2 DESPERATE-defensive (nobody leaves the hold for anything; no resupply runs; no vehicle hijacks except from inside the hold).
- `FF-LIFE-02` A bot never spends a life for score; kills are free, deaths are not. The HEAVY only fires ordnance when it kills 3+ or a boss.
- `FF-LIFE-03` Bonus rounds do not use the pool: play them aggressively for score and for the extra lives they award in ODST; a death there is cheap.
- `FF-LIFE-04` Revive-by-respawn timing: dead bots respawn at the hold; if the hold is overrun, the brain delays respawn (if the mode allows) until the living bots have moved to the second hold, so new lives do not spawn into a hammer.

**Wave logic**
- `FF-WAVE-01` Identify the wave composition from the Phantom drop (callouts: "Chieftain with Hammer at the garage", Steam guide); set target weights before the enemies arrive: Engineer 3.0 (shields everyone near it), Chieftain 2.5, Hunter pair 2.0 (but only when the HEAVY is ready), Elite Ultra/General 2.0, Jackal sniper 1.8 (Needle Rifle and Focus Rifle one-shot threat), Brute 1.5, Skirmisher 1.3, Grunt with Fuel Rod 1.5, other Grunts 0.8, Drones 1.0.
- `FF-WAVE-02` Three-enemy rule: a wave advances when three or fewer enemies remain. If the three remaining are harmless (Grunts hiding), leave them alive deliberately to delay the next drop while the team reloads and repositions; kill them only when ready.
- `FF-WAVE-03` Last wave of the round must be cleared completely; sweep in pairs; do not leave a Grunt in a corner.
- `FF-WAVE-04` Boss wave: the HEAVY and PP stay back; ANCHOR and CLEANER hold the approach; nobody pushes a boss wave.
- `FF-WAVE-05` Skull adaptation: Catch (more grenades): keep moving, never stand in a doorway, listen for the "I'll stick you" tell (GameFAQs) and strafe; Tilt (shields take more ballistic, body takes more plasma): PP strips shields, then ballistic headshots; Famine (less ammo in drops): melee Grunts, conserve; Black Eye (shields recharge only on melee): CLEANER melees a Grunt to recharge; Mythic (double enemy health): double the time-to-kill in all decisions; Tough Luck (enemies dodge): aim for bodies, not grenades; Iron (bonus: death ends the round for you): hold back.

**Vehicles in Firefight**
- `FF-VEH-01` Hijack the Ghost the Phantom drops (Mombasa Streets) and the Choppers on Lost Platoon: a hijacked Chopper on Lost Platoon is "incredibly powerful" (Steam guide). Vehicle file rules `ODST-FF-01` to `-06` apply; the vehicle bot runs lanes and returns to the hold whenever a Wraith is dropped.
- `FF-VEH-02` Wraith dropped: never fight it in the open; the PP EMPs it (Reach: overcharge; ODST: no EMP, so use rockets, Spartan Laser, or board from the rear and melee/grenade); Lost Platoon's roofed building blocks the mortar.
- `FF-VEH-03` Banshee (Reach Firefight maps): the ANCHOR with a precision weapon shoots the pilot; a Plasma Launcher lock-on or rocket is the HEAVY's job; everyone else stays under the roof.
- `FF-VEH-04` Hornet on Lost Platoon: pilot plus two riders farm from the air but land at the hold before boss waves.

### 9.3 Enemy-handling combat logic (per type)

Health and shield numbers are Reach campaign tag values (Steam guide "Halo Reach Statistics"; Normal values, Legendary in parentheses). Material: Grunts, Jackals, Skirmishers, Brutes are soft_organic_flesh (full damage from bullets and plasma); Elites are hard_metal_thin body with energy_shield_thin shields; Hunter armor is hard_metal_thick (sniper does full, DMR half, plasma 12.5 percent), their hand shield is hard_metal_solid (plasma 6 percent, bullet_slow 12.5 percent), their flesh is soft_organic. A charged Plasma Pistol (200 emp damage, x1 on energy_shield_thin) pops any Reach infantry shield in one shot (community confirms it drops Elite Ultra shields on any stock difficulty); ODST and Halo 3 behave the same.

**Grunts (Minor 40 HP, Major/Heavy 50, Spec-Ops/Ultra 60; Ultra helmet 10 percent)**
- `FF-GRUNT-01` One precision headshot kills (Steam guide, GameFAQs). Ultras: shoot the helmet off first (helmet vitality is 10 percent of HP, so one body shot strips it), then headshot.
- `FF-GRUNT-02` Fuel Rod and Plasma Launcher Grunts are priority targets; stay behind cover with distance to dodge the projectile (Steam guide).
- `FF-GRUNT-03` Grunts flee when their leader dies and come back; kill the Elite or Brute leading the squad first and the Grunts scatter for free headshots.
- `FF-GRUNT-04` Suicide Grunts (two lit grenades, screaming): shoot them at range before they reach 10 m; never melee them.
- `FF-GRUNT-05` Grunt Birthday Party plus Cowbell (ODST): a Grunt headshot's confetti explosion kills nearby Grunts (GameFAQs); when both skulls are on, headshot the Grunt in the middle of the group.

**Jackals (Minor 40, Major 60, Sniper 40; shield on the left arm) and Skirmishers (60 to 95, Commando/Champion carry Hologram)**
- `FF-JACKAL-01` Shield Jackal procedure (GameFAQs ODST threads, Steam guide): shoot the exposed weapon hand or the left foot poking out below the shield; the Jackal flinches and opens the shield; headshot in that window. Alternative: shoot the slit on the shield's side to make it whiplash (GameFAQs bujufaq).
- `FF-JACKAL-02` Headshot opportunity: a Jackal aiming at someone else exposes its head (Steam guide); the bot not being targeted takes the shot.
- `FF-JACKAL-03` Plasma Pistol overcharge disables the shield gauntlet (ODST notes "if you take a charged plasma pistol burst and shoot them, their armor falls off"); after the overcharge, headshot.
- `FF-JACKAL-04` Jackal Snipers (Needle Rifle, Focus Rifle, Beam Rifle in Halo 3/ODST): highest infantry threat at range; they do not have shields; kill them first with the ANCHOR's precision weapon from cover, and move after every two shots because they return fire on the shooter.
- `FF-JACKAL-05` Skirmishers: fast, flank, no shields, Hologram on Commandos and Champions; do not shoot the first silhouette that appears from an odd angle (hologram); shoot the one that shoots back. Prioritize Focus Rifle Skirmishers.

**Elites (Minor 70 HP / 75 shield; Major 85/75; Ultra 90/135; Zealot 90/135; General 90/175; Field Marshal 110/185; Bob 135/185; Spec-Ops 60/60 with camo)**
- `FF-ELITE-01` Noob combo (Steam guide, community): PP overcharge strips the shield in one hit on any rank; follow immediately with a headshot (DMR, Magnum, Needle Rifle). The PP bot and the ANCHOR pair on every Elite. Without the PP: a full DMR magazine (15 x 17.5 = 262) drops a General's 175 shield with rounds to spare; Elite shields recharge after 8 s, so sustained fire from two bots.
- `FF-ELITE-02` Needle Rifle supercombine (3 needles) and Needler supercombine (6) kill through the body after shields drop; a Needler is the CLEANER's anti-Elite tool at close range.
- `FF-ELITE-03` Sword and Spec-Ops camo Elites: the CLEANER holds the shotgun; radar watch; shoot the shimmer; never let a sword Elite reach 5 m (lunge).
- `FF-ELITE-04` Armor Lock Elites (Ultra, Zealot, General, Field Marshal): when one locks, stop firing, back off, and resume when the lock ends; stick a grenade next to it so it detonates as the lock ends.
- `FF-ELITE-05` Rangers (jetpack): shoot them in the air with precision weapons; they have standard Minor stats and are easy headshots while hovering.

**Brutes (Minor 100 HP, Captain 150, Chieftain 200 HP / 100 shield; helmet 20 percent of HP; melee 50)**
- `FF-BRUTE-01` Halo 3/ODST Brutes have shields (power armor); PP overcharge strips it, then two or three headshots knock the helmet off and the next headshot kills (GameFAQs: "PP him then shoot him with a headshot a couple of times; eventually his helmet falls off"). Reach Brutes: no shields except the Chieftain; shoot the helmet off (20 percent of HP in body damage) then headshot.
- `FF-BRUTE-02` Berserk: an unshielded or helmetless Brute charges to melee (50 damage per hit, two hits kill a Spartan through full shield plus health); back-pedal while headshotting, never let it close; a Brute berserking at the CLEANER is the ANCHOR's shot.
- `FF-BRUTE-03` Catch skull Brutes: wait for the grenade-ready animation, strafe, throw back (GameFAQs).
- `FF-BRUTE-04` Chieftain with Gravity Hammer: plasma to drop the 100 shield (PP overcharge), then stick or power weapon (GameFAQs); it has temporary invincibility when it activates armor; splatter it before the invincibility triggers if a vehicle is available (`ODST-FF-02`); otherwise keep 15 m away and kite around cover.
- `FF-BRUTE-05` Chieftain with Fuel Rod or Plasma Launcher: cover and distance; approach while weaving, close only with a vehicle (`ODST-FF-03`) or with the HEAVY's rockets.
- `FF-BRUTE-06` Brute jump-pack (ODST): shoot in the air; they land stunned for a second.

**Hunters (250 HP, Legendary 500; back armor 50 percent of HP; always in pairs; no shields, PP does nothing)**
- `FF-HUNTER-01` The orange flesh is the only target that matters: back and neck (Halopedia, GameFAQs). The armor is hard_metal_thick (sniper full damage, DMR half, plasma almost nothing); the hand shield is hard_metal_solid (ignore it; sticky grenades do not attach to it, Steam guide).
- `FF-HUNTER-02` Two-bot procedure (Halopedia ODST Firefight): bot A stands in front and holds its attention from 10 to 15 m with cheap fire (plasma pistol or SMG, Halopedia says waste nothing valuable); bot B circles to the back and sticks a plasma or spike grenade on the exposed back plate (Steam guide: "removing the armored back is your opening move"), then shoots the orange worm-flesh with ballistic weapons or rockets. One rocket to exposed flesh (200 collision + 240 explosion_large at x1) kills a Normal Hunter outright; four sniper rounds (80 x1 on flesh) kill it; a Reach Legendary Hunter takes twice that.
- `FF-HUNTER-03` Melee baiting: when the Hunter charges to melee, jump back; it exposes its back on the follow-through; melee the orange back repeatedly (Halopedia) if no gun is available; this is the CLEANER's fallback.
- `FF-HUNTER-04` Pair trick: line the two Hunters up so the rear Hunter's fuel rod hits the front one (Halopedia ODST). The ANCHOR positions itself so both Hunters are on one line.
- `FF-HUNTER-05` Never fight Hunters in the open with the pool low: with lives at DESPERATE, hold the roof; Hunters cannot climb and will eventually turn their backs while chasing another bot.
- `FF-HUNTER-06` Bonus-round Hunters (Reach): sniper from maximum range into the back flesh; a solo player can kill 4 to 6 with a sniper in the bonus round (GameFAQs).

**Drones (15 to 45 HP, red/Ultra Drones shielded in ODST)**
- `FF-DRONE-01` Fast fliers with low HP: automatic weapons (SMG, AR, Plasma Rifle) rather than precision; fire at the swarm's approach path; they are weak to one headshot but hard to headshot (GameFAQs: most players just SMG them).
- `FF-DRONE-02` Landed Drones gain shields (ODST): shoot them in the air before they land.
- `FF-DRONE-03` Drones target the exposed bot; the group fights with backs to a wall so Drones can only approach from the front.

**Engineers (75 HP, helmet 5 percent; grants a flat 50 shield to all nearby enemies; explode when killed)**
- `FF-ENG-01` First target in every wave they appear in (Steam guide): a PP overcharge or a Needler supercombine kills one instantly (community: "a plasma pistol overcharge can one-shot the floating Engineers" in ODST); otherwise precision fire at the sac.
- `FF-ENG-02` The explosion on death damages nearby enemies; kill it while it floats over a squad.
- `FF-ENG-03` Until the Engineer dies, every enemy near it has an extra 50 shield: do not spend ordnance on shielded Grunts; kill the Engineer and the shields vanish.

**Vehicle enemies in Firefight**
- `FF-VEHENEMY-01` Ghost: EMP and hijack (Reach), or board from behind (ODST); a hijacked Ghost is worth more alive than dead (FF-VEH-01).
- `FF-VEHENEMY-02` Wraith: FF-VEH-02; from the roof, rockets or laser into the rear hatch (brittle_mech, 3x explosion damage per the vehicle file matrix); Reach Wraith 600 HP solid hull: a rocket to the hull does 220, to the hatch does 1200; aim at the hatch or do not fire.
- `FF-VEHENEMY-03` Banshee: FF-VEH-03; the pilot's legs (Halo 3/ODST) or the canopy gap (ODST sniper) kill the pilot and leave a free Banshee for the team.
- `FF-VEHENEMY-04` Phantom (2000 HP solid hull, chin gun 200 HP): do not try to kill it; shoot the chin gun off (it has its own health pool) if it is firing on the hold, and kill the troops as they drop from the bay in a line.

### 9.4 Firefight variants

- `FF-VAR-01` Gruntpocalypse (Score Attack): all Grunts; headshot streaks; the team stands in the open at range because nothing can hurt it at distance except Fuel Rod Grunts (FF-GRUNT-02).
- `FF-VAR-02` Rocketfight / Sniperfight: infinite rockets or snipers; FF-POS-01 roofs matter more (Wraith counters); rockets are fired at Hunters' backs and Chieftains, snipers at every head.
- `FF-VAR-03` Generator Defense (PvE version, Reach): defend four generators across six waves; lock a generator (30 s, then cooldown) when a Hunter or Chieftain wave targets it; the team splits two and two across the two nearest generators and abandons the far ones (Halo Reach guide lists 6 waves; the Firefight PvE variant defends generators from Covenant waves).
- `FF-VAR-04` Crashsite: one generator, one life, infinite DMR: stand on the generator, lockdown on every boss wave, headshot discipline only.
- `FF-VAR-05` Limited (ODST matchmaking) and Arcade/Firefight Versus (Reach, Spartans vs player Elites with NPC waves): in Versus the player Elites are the real threat; apply the SLAY-CORE rules to them and the FF rules to the NPCs; the Elites' posture engine runs the Juggernaut-hunter logic in reverse (they are the hunters of the Spartan hold).

---

## Part 10. Cross-mode scenario index

Quick lookup for "what do we do when…" across every brain:

| Scenario | Rule(s) |
|---|---|
| We are losing and time is almost up | P-04, SLAY-CORE-08/09, KOTH-STATIC-12, ODD-CORE-12, CTF-MULTI-16, ASS-MULTI-12, TERR-SYM-08, DOM-08, EXTR-05, STOCK-06, INV-ATK-05 |
| We are winning and time is almost up | P-06/P-09, SLAY-CORE-11, SLAY-SWAT-10, KOTH-STATIC-11, ODD-CORE-11, CTF-MULTI-15, ASS-MULTI-11, TERR-SYM-07, DOM-07, EXTR-04, STOCK-05 |
| Enemy has a tank or Wraith up | VC-02, CTF-MULTI-17, ASS-MULTI-13, SLAY-BTB-01, FF-VEH-02, vehicle file Quick Reference tank procedure |
| Enemy has a Banshee or Hornet up | VC-02, CTF-MULTI-18, FF-VEH-03, vehicle file anti-air rules |
| Enemy carrier is loose (flag, bomb, ball, core, skulls) | CTF-MULTI-10 to -13, ODD-CORE-07 to -10, ASS-MULTI-08/09, INV-DEF-04, HH-02 |
| Our carrier is attacked alone | CTF-MULTI-05, ODD-CORE-04, ASS-MULTI-06, INV-ATK-04 |
| Enemy holds the hill or territory | KOTH-STATIC-06 to -10, TERR-SYM-04/08, TERR-ASYM-05 to -07 |
| One life left / limited lives | P-01, SLAY-ELIM-01 to -08, CTF-MULTI-20, FF-LIFE-01 |
| No shields or no radar | SLAY-SWAT-01 to -13 |
| Everyone is invisible | SLAY-PHANT-01, JUG-05, KOTH Phantom King overlay |
| Power weapon just spawned or is about to | PW-01 to PW-04 |
| Numbers advantage right now | SLAY-CORE-07, SLAY-ELIM-05 |
| Sudden death | P-02/P-03, CTF-ONE-06, ASS-MULTI-12 |
| Hunter pair in Firefight | FF-HUNTER-01 to -06 |
| Shield Jackal in Firefight | FF-JACKAL-01 to -03 |
| Engineer over a squad | FF-ENG-01 to -03 |
| Chieftain with Hammer | FF-BRUTE-04 |
| Lives pool under 3 in Firefight | FF-LIFE-01, FF-HUNTER-05 |

## Part 11. What is sourced and what is not

- Gametype rules, defaults, timers, and variant lists come from Halopedia's custom-game settings pages for CE, Halo 2, Halo 3, Reach, and H2A, plus Halopedia gametype pages (Territories, Dominion, Extraction, Juggernaut, Headhunter, Infection, Invasion, Generator Defense, Team SWAT) and MCC playlist notes. Halo 4's default gametype list is a stub on Halopedia; Halo 4 variants here are the ones confirmed by other pages (Dominion, Extraction, Ricochet, Regicide, Flood, Infinity Slayer, Vehicle CTF setting).
- Tactics marked Source come from Halopedia and Fandom gametype pages, the TL.net and Neoseeker SWAT guides, GameFAQs ODST and Reach Firefight threads, the Steam ODST Firefight guide, the Steam Reach enemy-weakness guide, and the Reach statistics guide (enemy HP and shields, damage multipliers).
- Everything tagged Proposed (the posture engine, role splits, target weights, thresholds, hold-spot scoring, the IF/THEN scenario rules) is design logic written for this mod and has not been tested in-game. The numbers are starting values.
- Ricochet scoring, Halo 4 flag-drop rules, Halo 2 Reverse Tag and Accumulate scoring, H2A variant presets (Cadre, Flight, Hunted, Nauticide, Incursion), and ODST Firefight life counts should be verified in the MCC gametype menus before coding against them.

---

## Patch: Difficulty tiers and optional coach hooks (objective brain)

**Difficulty tiers.** `halo_mcc_bot_tiers_integration_and_coach.md` Part 2.2 scales this file by tier: Easy ignores the posture engine, timers, spawn control, roles, and time-low branches and simply runs at the objective; Normal reads score but not time until the last 60 s and tracks timers half the time; Heroic runs the full engine and roles; Legendary adds pace projection, spawn weighting, setups, and predicted-spawn callouts. In Mixed, the team's objective brain runs at the tier of its highest-tier living bot while each bot executes at its own tier (`TIER-MIX-03`). Personalities bias role volunteering (Part 3).

**Integration.** The on-foot combat brain consumes `posture`, `role`, `goal`, `target_weights`, `fire_discipline`, `grenade_budget`, `vehicle_request`, `equipment_hint`, and `callouts_in` (addendum Part 1.2) with the precedence rules in Part 1.3: carriers never initiate fights, shields-down survival may override `goal` for 4 s, seated bots belong to the vehicle brain, posture caps aggression but never skill.

**Optional coach.** The coach's only entry point into the bot stack is this brain. Every 20 to 60 s (by tier) and on events, it may send an advice message that the relayer validates (addendum Part 4.2) and this brain applies through the fields above. Hooks:

| Hook | Allowed | Hard limits that always win |
|---|---|---|
| `COACH-OBJ-posture` | one step from the engine's value (BALANCED -> AGGRESSIVE or CONSERVATIVE; AGGRESSIVE -> DESPERATE) | DESPERATE only if the engine is at AGGRESSIVE or DESPERATE; P-01 (one life) and P-02/P-03 (sudden death) cannot be overridden |
| `COACH-OBJ-roles` | reassign among living bots within the mode's role list | one CARRIER, one SCORER per hill, at least one DISARMER when the enemy has planted, DEFENDER count never below the posture's minimum in CONSERVATIVE |
| `COACH-OBJ-play` | any `PLAY-*` from the addendum's playbook | plays are bundles of existing rule IDs; a play cannot add a rule this file does not contain |
| `COACH-OBJ-tempo` | SLOW / NORMAL / FAST | maps to push rate and respawn-regroup only; never to reaction or aim |
| `COACH-OBJ-lanes` | per-bot lane from the map's enumerated list | carriers use only routes flagged carrier-safe for the current enemy vehicle set |
| `COACH-OBJ-target_weights` | 0.5 to 2.5 per entity | carrier weight floor 1.5 when an enemy carrier is loose |
| `COACH-OBJ-callouts` | free text injected into `callouts_in` | subject to the bot's tier memory window (4/6/8/10 s) |
| `COACH-OBJ-timer_focus` | name a power weapon, power-up, or vehicle spawn to pre-position for | `PW-01` early-arrival time is capped by tier (Legendary 10 s, Heroic 5 s, Normal 0) |

**Scenario index additions for the coach:** every row of Part 10 lists the deterministic rules; the coach can only choose among them earlier, sequence them into a play, or switch between branches when its tendency log says the enemy's pattern makes one branch better. It cannot invent a branch.
