# Guide 17 compliance: every rule of the vehicle guide against the code

the player's guide `docs/research/17-vehicle-tactics-guide.md` (Fable: "follow this ... for greater context")
rule by rule. Status: **done** (coded and tested offline, commit), **live** (also seen working in a match), **partial**
(what is missing is named), **open** (not coded yet; the batch it is in), **blocked** (what is missing to code it).
Blocked is not "not applicable": it names the read, input or tag value still needed. The guide's "Proposed" values
are the defaults; numbers measured live replace them where noted.

Updated (HEAD after the crew batches). Order of work: the player's three live observations first
(gunners not shooting, the bot that kept missing, vehicles not used), then the decision architecture (§4), then the
per-vehicle tactics and avoid lists of every game, then each game's objective rules.

## Bot Implementation Layer

| Rule | Status | Where / what is missing |
|---|---|---|
| §1 where the numbers live | partial | Reach tag numbers are the guide's (§2); vehicles.VEHICLES speeds are rough. CE/H2/H3/ODST/H4 vitality, speeds and projectile speeds: **blocked** on extracting them with the mod tools (guide §1, §5) |
| §2 Reach vitality / weapons / materials / TTK | partial | used for the role table and the gunners' guns; the TTK matrix as killability in target scoring: open (§4.2 batch) |
| §3 per-vehicle operating model (inputs, crew, cues) | partial | crews and seats by kind (vehicles.VEHICLES, REACH_SEATS, TURRETS); Reach variants from the gun on the body (0076364); human cues: below per vehicle |
| §4.1 state machine IDLE/PATROL/ACQUIRE/ENGAGE | partial | PATROL: a role's vehicle drives where it is needed (crew batch); ENGAGE_GUN by role (vehicles.STRATEGY); ENGAGE_RAM: splatter (d < 18 u, a man on foot without an anti-vehicle gun) |
| §4.1 EVADE | partial | the artillery role backs off a man within BOARD_D; rockets, barrels, EMP cues: open (§4.6 batch) |
| §4.1 RETREAT / ABANDON, thresholds 0.40 / 0.60 / 0.25 / 0.15 | **blocked** | needs the vehicle's hull fraction: the object's body damage (Reach units +0x128, LiveReach.ai_units) is not verified on vehicle objects; one live read while a vehicle is shot |
| §4.1 RETREAT on driver_shield_down (H2/H3) | done | Halo 2 and 3, a ground vehicle's driver with his shield broken and a man in view drives to the nearest teammate on foot, else our base, 4 s at a time, never firing; Normal and up, off in shieldless games and on a ferry (Bot.drive, test_vehicle_threats 12) |
| §4.1 OBJECTIVE hook | partial | ferry (carrier pickup), honks, give_seat (director); the per-game rules: below |
| §4.1 boarding_alert_radius 6 m ground / 10 m air | done | artillery backs off at 6 u (Bot.drive); light vehicles 2 u, aircraft 3.3 u while hovering (under 3 u/s; an attack run passes low over its man): full throttle away from a man on foot in view or on the radar under 1 s, never the man being run down (Bot.evade, test_vehicle_threats 11) |
| §4.1 sensor / weapon ranges | partial | per-kind fighting ranges (STRATEGY rng); the Falcon's set to its side guns' reach (8-18 u, 0076364) |
| §4.2 target scoring | done | vehicles.target_score via Bot.vehicle_pick for every armed seat: base_threat x objective_weight (carrier 2, in the hill 1.5, by our flag 1.3) x killability (1 / Reach TTK; other games by Reach's ratios) x angle_factor (forward guns: 0.5 past 90 degrees; a tank's 50-degree overhead cone and the Chopper's rear 0.2) (targets batch); a seat takes the man its gunner's view is on (0076364) |
| §4.2 exposure term | partial | not subtracted: its scale against the other terms is not given (a Scorpion lane, a rocket spawn, a Banshee overhead); the threats answer those (Bot.evade) |
| §4.2 per-vehicle multipliers | done | Banshee (and Sabre / Seraph) air x2, Gauss vehicles x1.5 men x0.5, Ghost / Chopper inside a run x1.5, Wraith mortar still targets x1.5 running men x0.4; transports none (targets batch) |
| Reach / Halo 4 rocket hog: "hold fire on ground targets" | done | score 0 for men on foot there; CE's anti-armour rocket hog still shoots them (targets batch) |
| §4.2 transports score every target 0 | done | an unarmed driver with no gun manned runs a man down or goes on with its trip (0076364) |
| §4.3 ram commit: theta | done | Bot.ram_ok: a vehicle with its own gun commits within vehicles.RAM_THETA of its nose (Warthog 20, Ghost 12, Chopper 8, Mongoose 15 degrees); one without a gun turns onto him (ram batch) |
| §4.3 ram commit: v_min, path clear | partial | not gated: the kinds' speeds are rough (vehicles.VEHICLES); boost: **blocked** (no vehicle boost input decoded) |
| §4.3 aim_point lead | done | lead by the man's velocity (Bot.drive splatter) |
| §4.3 abort on a sidestep | done | a man 1+ u off the nose within 5 u: on through 1.5 s (ram batch) |
| §4.3 post_hit 1.5 s | done | on at full throttle beside nobody (ram batch) |
| §4.3 vehicle-vs-vehicle table | done | vehicles.RAM_VEHICLES from Halo 2 on (Warthog / Gauss: Ghost, Mongoose, Prowler, Gungoose; Chopper also Warthogs, Choppers, a Hornet); never tanks, the Elephant, the Mantis; CE none (ram batch) |
| §4.3 Armor Lock hard no-ram (also REACH-CTF-04, KOTH-02, ASS-02, H4-REG-03) | done | ram_ok; never within 1.5 u of him (evade) (ram batch) |
| rocket hog and transport hog never ram (CE / H3 / Reach profiles) | done | STRATEGY splatter off (ram batch) |
| §4.4 hitscan / slow-projectile lead | done | Aim.step by the seat's gun (vehicles.gunner_gun, STRATEGY gun) |
| §4.4 lobbed mortar arc | **blocked** | muzzle speed and gravity scale from the projectile tags (guide §5) |
| §4.4 chaingun pre-spin | done | 2 s on where the man went out of sight (0076364) |
| §4.4 Banshee bomb per game | **blocked** | the secondary-weapon input in a vehicle is not decoded |
| §4.4 Scorpion overhead blind cone | open | §4.6 batch |
| §4.4 weak-part aiming: a tank's back hatch | done | cannon, rocket, mortar and gauss shots at a tank's rear (0.8 u behind its middle) when behind its beam (Bot.weak_point, targets batch) |
| §4.4 weak-part aiming: the Ghost's gas tank, the Warthog's glass | open | where they sit on the models is not measured |
| §4.5 driver keeps the gunner's arc | done | Falcon: the manned side to the gun's target; Warthog: side-on circle (0076364) |
| §4.5 gunner reports target lost / reloading | open | |
| §4.5 tank gunner (H3 / ODST coax): the hull and 10 m first | done | x10 inside 3.3 u (targets batch) |
| §4.5 passengers: own gun at the crew's target, none while carrying | done | 0076364 |
| §4.5 transport waits 8 s, pickup_request within 40 m | partial | a driver just in waits up to 8 s while a teammate on foot (person or bot) runs to it from within 8 u or stands at its door (3 s), and 6 s for a gunner the director called (Bot.crew_coming, 5bb662d, test_vehicle_crew 6g); a bot's pickup request: open |
| §4.6 rocket (a vehicle killer aimed at us within 40 u) | done | out of his line (a car turns across it, a hover vehicle slides across it nose kept), an aircraft also dives (Bot.evade, ram batch). The lock-on tone itself: **blocked** (no sound or lock read); the aim at us stands in for it |
| §4.6 Scorpion / Wraith barrel within 10 degrees | done | out of its line; an aircraft climbs over it (Bot.evade); breaking line of sight behind cover: open |
| §4.6 Plasma Pistol / Grenade Launcher | partial | full throttle away inside 15 m (5 u), Halo 3 on (Bot.evade); the charge glow is not read (any holder counts); exit on the far side when EMP'd: **blocked** (no EMP'd state read) |
| §4.6 boarder inside the alert radius | partial | artillery backs off; light vehicles and aircraft accelerate away, by the tier's reaction and juke roll (Bot.evade); a man farther off with no vehicle killer is run down; the tank gunner on boarders and the Reach counter-board (exit, re-board): open |
| §4.6 hull below retreat, smoking | **blocked** | the hull read (§4.1) |
| §4.6 Armor Lock glow | done | no ram, away inside 1.5 u (ram batch) |
| §4.6 tanks hold, Easy never dodges | done | tanks duel; a threat is answered after the tier's reaction, by its juke trait |
| §4.7 vehicle selection by role, objective bias | done | director.crew_orders (crew batch) |

## the player's live observations

| Observation | Status |
|---|---|
| "the gunners in the falcon weren't shooting at anything" | done offline (0076364): turret trigger window, the pilot turns the manned side to the target; live check pending |
| "the bot kept missing" | done offline (0076364): the Falcon pilot fired with no gun; live check pending |
| | done offline (crew batch): vehicles picked by role from up to 45 u, a role's driver keeps the vehicle working; live check pending |

## Per-vehicle tactics and avoid lists

Every game's "AI tactics (Proposed)" and "Avoid" bullets per vehicle (CE 408-562, H2 668-930, H3 1056-1425, ODST
1573-1861, Reach 1969-2448, H4 2597-2869): open as a whole (the doctrine batch: one table by kind with each game's
differences, read by target scoring, the threat responses and the patrol). Already covered in part: Wraith / Scorpion
hold range and back off boarders (artillery), Ghost and Warthog run men down, Banshee attack runs low and travels high,
the Grenadier hunts vehicles with explosives (vehicle_mission).

## Theft and boarding (every game)

| Rule | Status |
|---|---|
| boarding an enemy vehicle (H2 onward; Reach boarding seats in reach_seats.json) | **blocked** | a live test of Reach's enter-seat interaction on an enemy vehicle's boarding seat |
| CE: no boarding, Warthog and Scorpion indestructible | done (nothing boards in CE; the Grenadier's anti-vehicle mission is about crews) |
| EMP with the plasma pistol overcharge | partial | the plasma pistol counts as anti-vehicle (ANTI_VEHICLE); aiming its overcharge at an engine: open |

## Objective rules

All open unless named (the objective batch), by game: CE 16 (CTF-01..05, PUR-01..03, DEF-01..02, KOTH-01..04,
ODD-01..02), Halo 2 21 (CTF-01..05, PUR-01..03, DEF-01..02, ASS-01..06, KOTH-01..03, ODD-01..02), Halo 3 38
(CTF-01..08, PUR-01..06, DEF-01..05, ODD-01..04, ASS-01..09, KOTH-01..06), ODST 9 (OBJ-01..03, FF-01..06), Reach 23
(CTF-01..04, PUR-01..03, DEF-01..02, INV-01..03, HH-01..03, KOTH-01..02, ASS-01..02, ODD-01), Halo 4 19 (CTF-01..04,
PUR-01..03, DEF-01..02, ODD-01..03, REG-01..03, KOTH-01..03).

Partial now: the carrier ride (H2-CTF-01, H3-CTF-01: director ferry picks up our carrier on foot and runs him home;
not REACH-INV-01: the Invasion core is carried as a turret, its carrier cannot ride), the one scorer on the hill (CE/H2/H3/H4-KOTH-01: the hill holder stays inside it; the rest
fan out by role slots), the Armor Lock no-ram rules (REACH-CTF-04, KOTH-02, ASS-02, H4-REG-03) with §4.3.

##: the guide's new Patch section

The guide gained (uncommitted in the working tree) a file-set note at the top and, at its end, "Patch: Difficulty tiers
and optional coach hooks (vehicle brain)": guide 18's §2.1 tier scaling and seven coach hooks. Rows for the patch only;
each tier row has its full entry in docs/research/18-tiers-compliance.md (TIER-VEH-nn). Audit only, no code changed.

| Rule | Status | Where / what is missing |
|---|---|---|
| tiers: reaction to vehicle threats (TIER-VEH-01) | partial | Bot.evade waits the tier's reaction, then answers by the on-foot juke roll (Easy never, Normal 1 in 10, Heroic 6 in 10, Legendary all); no barrel prediction; lock tone and EMP glow not readable |
| tiers: ram commit precision (02) | partial | the ram is done (§4.3 rows above); commit distance and heading error are the same for every tier (Bot.ram_ok, vehicles.RAM_THETA) |
| tiers: never-ram list (03) | partial | every tier respects it (the Legendary row); Easy's and Normal's slips are not modelled (Bot.ram_ok) |
| tiers: gunnery lead (04) | partial | one lead factor for every tier (Aim.step, profiles.HANDS lead): the player's equal-hands rule against the table's tiered error, the player to decide |
| tiers: weak-part aiming (05) | partial | Bot.weak_point at every tier (the Legendary row); gas tank and glass still open (§4.4) |
| tiers: boarding as attacker (06) | **blocked** | as the boarding row above: the live Reach enter-seat test on an enemy vehicle (Bot.think enters only empty or our vehicles) |
| tiers: boarding defense (07) | partial | the artillery kinds back off a man inside BOARD_D at every tier, Easy too; light vehicles and aircraft drive away from a man inside 2 u (3.3 u) by the juke roll: Easy never, Normal 1 in 10, Heroic 6 in 10, Legendary always (Bot.evade); the gunner on boarders (Heroic) and the counter-board (Legendary): open |
| tiers: retreat thresholds (08) | **blocked** | the hull read (§4.1); the Halo 2 / 3 shield-down retreat runs Normal and up, Easy fights to the death |
| tiers: vehicle selection (09) | partial | Easy rides by vehicles.ride_score, the rest take director.crew_orders' picks by role on their teamwork roll; counter-vehicle awareness: open |
| tiers: blind-spot awareness (10) | open | only our own shot's score knows the cones (vehicles.target_score); no vehicle guards its own |
| tiers: boost timing (11) | **blocked** | no vehicle boost input decoded |
| tiers: crew coordination (12) | partial | full §4.5 coordination at every tier (Bot.crew_target, Bot.drive) |
| tiers: air evasion (14) | partial | dives, climbs and break-offs at every tier, juke-gated (Bot.evade); trick rolls on the lock tone: **blocked** (no lock read) |
| tiers: per-bot 10 percent variance | partial | profile values only (profiles.make_profile); the vehicle constants (18 u ram reach, RAM_THETA, BOARD_D, evade ranges) are shared by every bot |
| personalities bias the vehicle claimed and how it is used (guide 18 Part 3) | open | crew_orders, vehicle_orders and honk_orders pick by distance; no Driver, Pilot, Tanker or Support (profiles.PERSONALITIES); the Grenadier's anti-vehicle mission is the only personality hook (Bot.vehicle_mission) |
| no coach: the vehicle brain runs unchanged | done | the vehicle brain reads nothing from the coach; coach off or offline changes nothing in Bot.drive |
| COACH-VEH-lane | open | no lane in the coach's schema (brain/coach.py SCHEMA); orders go to callouts on foot only (director VERB_ROLE has no vehicle verb); no infantry-only lane marks in the map data |
| COACH-VEH-role | open | no seated-bot roles in coach.ROLES, the crew roles are the director's own (vehicles.ROLES); its hard limits hold without it: the carrier always runs home (director.assign_roles), nothing rams tanks or Armor Lock (Bot.ram_ok) |
| COACH-VEH-target_weight | open | no target weights in the schema; its hard limits stand: a gun that cannot hurt the target scores 0 (vehicles.target_score), the exposure term is still not coded (§4.2 exposure row) |
| COACH-VEH-retreat_threshold | **blocked** | no retreat threshold exists until the hull read (§4.1) |
| COACH-VEH-spawn_request | open | crew_orders' role order is fixed by mode (vehicles.ROLE_FIRST, ROLE_ORDER); anti-air is always first, so the hard limit holds, but not because an enemy aircraft is up |
| COACH-VEH-bait | open | no bait placement, trip mine or Armor Lock lane (EQ-MINE-03, EQ-LOCK-06) |
| COACH-VEH-air_mode | open | one air role (STRATEGY "air", Banshee x2 against aircraft in target_score); no AIR_DENIAL, GROUND_SUPPORT, CARRIER_COVER or HILL_BOMB mode; the forced AIR_DENIAL: open |
| coach plays touching this brain | open | none is callable: PLAY-ESCORT-HOG is the director's ferry (vehicle_orders), PLAY-AIR-DENIAL its anti-air-first crew order, PLAY-TANK-FIRST the Grenadier's mission; PLAY-CHOPPER-LANE, PLAY-VEHICLE-BAIT and PLAY-FF-ROOF do not exist (coach.PLAYS has no vehicle play) |
