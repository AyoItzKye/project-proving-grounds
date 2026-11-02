# Halo MCC Equipment, Power-Ups, and Armor Abilities: Mechanics and Bot Logic

Third file in the set. `halo_mcc_vehicle_tactics_and_objectives.md` is the vehicle and combat brain; `halo_mcc_objective_logic_brains.md` is the per-gametype objective brain. This file covers every pickup, deployable, and armor ability a bot can use or has to counter, in every MCC title: CE and Halo 2 power-ups, Halo 3 equipment, Reach armor abilities, Halo 4 armor abilities with tactical and support packages, plus health packs and custom power-ups.

**Status tags**
- **Rule:** How the item works, from Halopedia, Fandom, the Halo 3 and Reach strategy wikis, and MCC guides. Numbers are quoted where a source gives them; durations vary by game and gametype settings.
- **Source:** A tactic reported by a wiki, guide, or community thread.
- **Proposed:** Bot logic written for this mod. Tune in testing.

**File set:** file 3 of 4. Tier scaling, on-foot integration, and coach hooks for this brain are in `halo_mcc_bot_tiers_integration_and_coach.md` and in the patch section at the end of this file.

**Rule ID format:** `EQ-<ITEM>-NN` for item logic, `EQP-NN` for the universal pickup policy.

---

## Part 0. Availability matrix

| Item | CE | Halo 2 / H2A | Halo 3 | ODST | Reach | Halo 4 |
|---|---|---|---|---|---|---|
| Overshield (pickup) | Yes, 3x | Yes, 3x | Yes, 2x | no MP | Forge pickup only (3x) | Ordnance / Forge (2x) |
| Active Camo (pickup) | Yes, 45 s | Yes, 45 s (H2A 45 s) | Yes, 30 s | no MP | Forge pickup only (30 s) | Ordnance / Forge |
| Custom Powerup | no | no | Forge, traits set by gametype | no | Forge, traits by gametype | Forge |
| Speed Boost / Damage Boost | no | H2A Speed Boost | no | no | no | Ordnance (45 s / 30 s) |
| Health packs | Yes (health bar) | no (no health bar) | no | Yes (stamina plus health) | Yes (health bar) | no |
| Halo 3 equipment (8 MP items) | no | no | Yes | Brute-only (AI uses it against you) | no | no |
| Reach armor abilities (7) | no | no | no | no | Yes | no |
| Halo 4 armor abilities (8), packages | no | no | no | no | no | Yes |
| Sprint as a free ability | no | no | no | no | AA slot | Always on |
| VISR (night vision, enemy outlines) | no | no | no | Yes | no | no |
| Flashlight | Yes | Yes (campaign) | no | no | no | no |

Sources: Halopedia Power-up, Equipment, Armor abilities, Active camouflage, and Overshield pages; Fandom Equipment page; Halo Diehards MCC abilities guide.

---

## Part 1. Universal pickup policy (Proposed)

These rules sit under every item section and are inherited by every objective brain.

- `EQP-01` **Timer tracking.** From the moment a power-up or power weapon is taken, the brain starts its respawn timer. Rule values: CE power-ups respawn in 1:00 by default, with map exceptions (Blood Gulch middle 3:00, Chill Out 2:00, Danger Canyon bottom mid 3:00, Hang 'Em High top mid 3:00, Ice Fields bottom mid 3:00, Rat Race 1:30, Chiron middle OS 0:45) per the Halo 1 Guide and the Steam CE spawn-time guide. Halo 2, 3, Reach, and Halo 4 timers are per-map and set by the gametype's "Powerups on Map" and "Weapon Respawn Time" settings; read them from the variant, default around 60 to 120 s.
- `EQP-02` **Pickup order when several spawn together.** Source (Halo 1 Guide, 4v4): Rockets first, Camo second, Overshield third; split the team one per item with the fourth supporting rockets. Generalize: power weapon > camo > overshield > custom powerup, unless the objective brain overrides (CTF runner wants overshield, sniper wants camo).
- `EQP-03` **Denial beats use.** In CONSERVATIVE posture (objective brain P-06/P-09), the bot nearest a power-up takes it at spawn even if it has no use for it. An unused overshield in our hands is better than a used one in theirs.
- `EQP-04` **Pre-position, do not fight on top of it.** Be at the spawn 5 s early behind cover; take it the frame it spawns; leave. A bot standing on a power-up spawn is standing where every enemy is looking.
- `EQP-05` **Quick camo clock.** Source (Halo 1 Guide): pick camo up the second it spawns so the game clock reads a round number when it expires; the brain does this with an internal timer instead, but the principle holds: take it on spawn, not late, so its full duration lines up with the next push.
- `EQP-06` **Carrier routing.** Objective carriers (flag, bomb, ball) get overshield; stealth roles (flag sneak, bomb plant, sniper) get camo; power weapon holders get neither unless no one else is near.
- `EQP-07` **Never two power-ups on one bot** unless the second is pure denial. Spread value so one death does not lose both.
- `EQP-08` **Equipment and armor abilities are never used "to see what happens."** Every activation below has a trigger condition. If no trigger is met, the bot holds the item (Halo 3) or lets the ability sit at full charge (Reach, Halo 4).
- `EQP-09` **Enemy item detection.** The brain reads enemy glows and sounds: overshield shimmer and the pickup sound, camo shimmer and radar jam, armor lock glow, drop shield dome, hologram walk pattern (straight line, no strafe, no weapon raise), jetpack sound, bubble shield dome, regenerator mist, power drain hum, trip mine beep, flare flash. Each has a counter rule below.
- `EQP-10` **Pick-up-on-death.** A dead enemy's equipment (Halo 3) stays on the ground; a bot passing within 4 m takes it if its own slot is empty.

---

## Part 2. Power-ups

### 2.1 Overshield

**Rule**
- CE, Halo 2, Reach pickup: shields to 300 percent (two extra layers). Halo 3, Halo 4 ordnance: 200 percent (one extra layer). Halopedia Power-up page; Fandom Overshield.
- Charging takes about 3 s after pickup; during the charge the user is briefly invulnerable (Fandom; Halo Diehards says 1 to 2 s in Halo 2). In CE the pickup is instant-on with the same charge-up glow.
- In multiplayer the overshield decays over time without damage. CE: drops to half power after 45 s and is gone after another 45 s (Halo 1 Guide). Halo 2 and 3 decay on similar schedules (not sourced to the second; the brain measures it in testing).
- A charged Plasma Pistol shot strips the entire overshield and the base shield with it (Halo Diehards CE; Fandom). Power Drain (Halo 3) and the Armor Lock EMP burst (Reach) do the same.
- The user glows, which negates camo and draws attention (Fandom). Assassinations and melee from behind still kill an overshielded player in games with assassination animations; a two-hit melee still works because melee bypasses layers on the back.
- Black Eye skull (campaign/Firefight): melee restores shields; some skull combinations give overshield from melee (Fandom).

**Bot use (Proposed)**
- `EQ-OS-01` Who takes it: the bot about to do the riskiest thing. Priority: objective carrier about to cross the open > the pusher leading a 2v2 into a power position > the bot about to steal a vehicle > anyone else.
- `EQ-OS-02` Use it immediately. Decay means every second not fighting is a second wasted. The bot's posture goes AGGRESSIVE for the decay window: first 20 s it accepts 1v2 fights at close range (3x shields in CE and Halo 2 survive roughly three times the damage, so a 1v2 at close range is a favorable trade); after the first decay step it drops back to BALANCED.
- `EQ-OS-03` Charge-up invulnerability: the 1 to 3 s charge is a free window. If an enemy is within melee range of the pickup, the bot takes it and melees during the charge rather than backing off.
- `EQ-OS-04` Overshield and camo together: never. The glow shows through camo.
- `EQ-OS-05` Flag/bomb/ball carriers: overshield plus the route with the most enemies, not the fewest; the shield is there to be spent.
- `EQ-OS-06` Vehicles: an overshielded driver in an open vehicle (Warthog, Mongoose, Ghost) survives one more volley; in Halo 2 and 3 where vehicle damage bleeds to the occupant, overshield on the driver is effectively vehicle health. Route the overshield to the driver of the escort hog in CTF.

**Against an enemy overshield (Proposed)**
- `EQ-OS-07` Do not duel it with a precision weapon in the first 20 s. Back off, let decay work, re-engage at 45 s or when it has taken damage.
- `EQ-OS-08` Plasma Pistol overcharge removes it in one shot, then a headshot. The noob combo is the answer in every game that has a Plasma Pistol.
- `EQ-OS-09` Power Drain (Halo 3) thrown at the overshield bot's feet strips it and everyone near it.
- `EQ-OS-10` Stick it. A plasma grenade attached does 350 (Reach tags); three layers of 100 do not stop a stuck grenade plus a body shot.
- `EQ-OS-11` Melee from behind and assassinations ignore the extra layers' value because they land as a kill or near-kill anyway; a bot behind an overshielded enemy melees.
- `EQ-OS-12` Vehicle splatters kill through overshield (collision damage vs energy_shield_thin is x1 and splatter damage is far above 300); a Ghost or Warthog bot treats an overshielded enemy as a normal splatter target.

### 2.2 Active Camouflage (pickup)

**Rule**
- Duration: CE 45 s, Halo 2 and H2A 45 s, Halo 3 30 s, Reach Forge pickup 30 s (Halopedia Active camouflage; Power-up page). Cloaking takes about 3 s to complete after pickup (Halo 1 Guide).
- Fully invisible when standing still or walking; moving fast, shooting, meleeing, taking damage, or holding an energy sword (CE "intimidating thing to see," Halo Diehards) reveals a shimmer. In Halo 2 and 3 the cloak breaks visibly when firing and returns after.
- Camo users still show on the motion tracker if they move faster than walking speed (Rule across games), and in Reach and Halo 4 the camo armor ability also jams radar (see Part 4 and Part 5).
- Overshield glow and the flag/bomb/ball glow show through camo. A flag carrier in camo is visible by the flag.

**Bot use (Proposed)**
- `EQ-CAMO-01` Who takes it: the bot whose role is stealth or range: sniper, flag sneak (`REACH-CTF-03` active camo sneak on Standoff), bomb planter, Oddball thief, Juggernaut hunter, Infection last-man.
- `EQ-CAMO-02` Movement under camo: crouch-walk only. The combat brain caps speed at crouch speed for the duration; sprinting or jumping is forbidden unless escaping.
- `EQ-CAMO-03` No firing until the shot is a kill. One burst breaks the cloak; the bot fires only when the first burst finishes the target (headshot ready on an unshielded enemy, sniper shot, shotgun inside 5 m, sword lunge) or when assassinating. In SWAT every shot is a kill, so camo is used for position, not for the shot.
- `EQ-CAMO-04` Radar discipline: in games where radar is on, the bot walks so it does not blip; it approaches from the enemy's rear 90-degree arc.
- `EQ-CAMO-05` Camo plus sword or shotgun is the strongest combination on small maps: the brain routes camo to the sword holder if one exists.
- `EQ-CAMO-06` Objective use: flag room entry (`CTF-ONE-04` back door), Oddball hold-spot entry, hill contest (an invisible contester stops the enemy clock without being shot), Territories capture (crouch in the territory invisible for the full timer), Assault plant (plant invisible, then defend).
- `EQ-CAMO-07` Camo does not carry objectives well: the flag glow shows. A camo bot grabs the flag only when the carry is short (under 10 s); otherwise it kills the defenders and lets a teammate carry.

**Against an enemy camo (Proposed)**
- `EQ-CAMO-08` Detection: shimmer at movement, radar blip when they run, footsteps, weapon-raise animation, the flag glow, grenades stuck to them, and any splash damage (a frag at a doorway reveals a shimmer). The combat brain raises "shimmer sensitivity" and listens for footsteps when the enemy camo timer is known to be active.
- `EQ-CAMO-09` Counter-position: back to a wall, radar on, shotgun or sword out, grenade thrown at every corner you must pass.
- `EQ-CAMO-10` Spray the area: automatic fire into a suspected shimmer breaks the cloak on hit (damage shows them).
- `EQ-CAMO-11` Wait it out: 30 to 45 s; a bot that cannot find the camo enemy holds a defensible corner until the timer expires.
- `EQ-CAMO-12` Promethean Vision (Halo 4) shows camo users through walls; the Halo 4 counter-camo bot equips it.

### 2.3 Custom Powerup (Halo 3, Reach, Halo 4 Forge)

**Rule**
- Traits are set by the gametype's Custom Powerup Traits block (duration plus any base-player-trait: damage, resistance, speed, camo, infinite ammo, etc.). Default effect is a speed boost (Halopedia Power-up).

**Bot use**
- `EQ-CUST-01` The brain reads the trait block at match start and maps it to the nearest existing item logic: speed -> treat as Speed Boost (2.4); damage -> Damage Boost (2.4); resistance or shield multiplier -> Overshield (2.1); camo -> Camo (2.2); infinite ammo -> route to the power weapon holder; vehicle use or movement changes -> route to the objective carrier.

### 2.4 Speed Boost and Damage Boost (Halo 4 ordnance, H2A Speed Boost)

**Rule**
- Speed Boost: movement, reload, and weapon switch twice as fast for 45 s; blue tint and glow (Fandom; Halopedia).
- Damage Boost: +100 percent damage per shot for 30 s, including vehicle-mounted weapons; red glow; the screen darkens and the FOV narrows (Halopedia). Also granted to the Regicide King after 60 s as King.
- Both come from personal ordnance in Infinity Slayer and from Forge placement; H2A has Speed Boost on some maps.

**Bot use (Proposed)**
- `EQ-SPD-01` Speed Boost goes to: a flag or ball carrier (carrier speed penalties are multiplied back up), a hill rotator in Crazy King, a Headhunter skull runner, or the Juggernaut hunter. Twice-as-fast reload also makes a shotgun or sniper bot deadly; second choice is the power weapon holder.
- `EQ-SPD-02` While boosted, the bot takes the long route around fights rather than through them; the boost is for position, and the blue glow draws fire.
- `EQ-DMG-01` Damage Boost goes to: the Gauss gunner or tank gunner if one is up (vehicle weapons double: a Gauss hit at 400 collision one-shots a Banshee and two-shots a Warthog hull; a Scorpion shell at 668 direct one-shots every light vehicle through any hull material), otherwise the bot holding a precision weapon in a lane with the most traffic.
- `EQ-DMG-02` Damage Boost and grenades: blast radii increase (Halopedia); the bot throws grenades at groups and doorways during the 30 s.
- `EQ-DMG-03` The darkened screen and narrower FOV mean the boosted bot plays mid-range in open lanes, not corners, because its peripheral awareness is reduced; a teammate covers its flanks.
- `EQ-DMG-04` Against a boosted enemy (red glow): do not trade shots; break line of sight for 30 s or kill it with a vehicle or stick. A Damage-Boosted BR kills in two bursts; the only safe fight is the one it cannot see.

### 2.5 Health packs (CE, ODST, Reach)

**Rule**
- CE: health bar under shields; health packs restore it fully; no health regen. ODST: no shields, a stamina layer that regenerates plus a health bar that only health packs restore. Reach: health bar with regeneration only up to the current segment; health packs restore fully (Reach tags: Spartan body recharge fraction 1 with a 6 s delay, but in campaign/Firefight only "segments" regen; multiplayer regen is full).
- Drop Shield (Reach AA) regenerates health inside it, which saves health packs in Firefight (Fandom AA tips).

**Bot use (Proposed)**
- `EQ-HP-01` The brain maps every health pack and tracks which are taken. A bot under 50 percent health routes past the nearest pack between fights, never during one.
- `EQ-HP-02` Do not take a pack at full health (it does nothing and denies a teammate). Exception: denial in Elimination.
- `EQ-HP-03` ODST: stamina (the red screen) regenerates on its own; health does not. The bot distinguishes: red screen fading = wait in cover; health bar segments gone = find a pack or a Drop Shield equivalent (ODST has none; packs only).
- `EQ-HP-04` Firefight: packs are a shared resource; the HEAVY and ANCHOR get first call, and a Drop Shield user pulls teammates into the dome before anyone spends a pack.

---

## Part 3. Halo 3 equipment

**Rule facts (Halopedia Equipment; StrategyWiki Halo 3/Equipment; Halo Diehards):** single-use, one carried at a time (power-ups do not count against the slot), activated with a button, deployed at the player's feet or a short toss forward. Multiplayer set: Bubble Shield, Power Drain, Trip Mine, Regenerator, Deployable Cover, Radar Jammer, Flare, Gravity Lift. Campaign-only: Invincibility (from Chieftains), Cloaking (from Stalkers and some map spots), Auto-Turret. Flare and Radar Jammer were pulled from Halo 3 matchmaking (Radar Jammer because of a double-jump glitch) but exist in MCC custom games. ODST: equipment exists but only Brutes use it. Equipment can be "equipment-jumped" with Power Drain, Radar Jammer, and Flare by deploying at the top of a jump against a wall (Halopedia glitch note).

### 3.1 Bubble Shield

**Rule:** a dome that blocks all weapon fire and grenades in and out for about 20 s; players and vehicles walk and drive through it (Halopedia Z-4190). A Grav Lift thrown under the generator lifts the shield away; a Power Drain or Radar Jammer tossed at the generator knocks it over and rolls it; a Regenerator inside only affects people inside; a Power Drain inside is contained inside (Halopedia). A Bubble Shield can be thrown over an active Power Drain to protect teammates from it (Halo Diehards).

**Bot use (Proposed)**
- `EQ-BUBBLE-01` Triggers: (a) a teammate's shields are down and an enemy has line of sight; (b) a flag/bomb grab under fire (`H3-CTF-07` bubble before the grab); (c) a rocket, laser, or tank shell is incoming at a group; (d) a bomb arm or disarm in Halo 3 (the 5 s disarm or the 15 s fuse hold); (e) reviving the team's shields in a hold position between pushes.
- `EQ-BUBBLE-02` Placement: at the feet of the player who needs it, slightly toward the enemy so the dome edge covers the approach; never in a doorway the team needs to shoot through.
- `EQ-BUBBLE-03` Behavior inside: nobody fires out (it cannot); shields recharge; the moment shields are full the group exits together on the side away from the enemy or throws grenades out as the dome drops.
- `EQ-BUBBLE-04` Expect melee: enemies walk in. The bot inside holds the shotgun, sword, or a melee stance facing the enemy side; a bot with a Power Drain throws it inside its own bubble if the enemy walks in (contained drain strips only the people inside; use when our bot can step out first).
- `EQ-BUBBLE-05` Vehicles drive through it: a bubble is not cover from a Warthog ram or a Ghost splatter; the bot inside watches for vehicles and steps out the far side.

**Against an enemy bubble (Proposed)**
- `EQ-BUBBLE-06` Walk in and melee. The enemy inside cannot shoot out either, so the first melee or shotgun blast inside wins; approach from the side opposite their facing.
- `EQ-BUBBLE-07` Throw a grenade to land as the dome expires (20 s from deployment; the brain counts), or Grav Lift the generator out, or Power Drain the generator to roll the bubble off them (Halopedia).
- `EQ-BUBBLE-08` Drive a vehicle through it: the occupants are splatter targets with no way to shoot the vehicle first.
- `EQ-BUBBLE-09` Flag/bomb carriers inside a bubble: wait at the exits; they must leave to score.

### 3.2 Power Drain

**Rule:** a blue field that strips all energy shields in range, including the user's, and shuts down vehicle engines nearby; roughly 6.5 s (Halopedia Power drain); it can be destroyed by shooting it. It also acts as the Halo 3 EMP for boarding (vehicle file Quick Reference).

**Bot use (Proposed)**
- `EQ-DRAIN-01` Triggers: (a) an enemy vehicle is inside 10 m and we want to board it (`H3` EMP boarding); (b) two or more enemies are grouped within 6 m (hill, flag stand, bomb site, bubble); (c) an overshielded enemy; (d) a doorway the enemy must push through (throw it as they commit); (e) a Scorpion or Wraith parked within throwing range (engine off, then board from the rear).
- `EQ-DRAIN-02` Throw-and-shoot: the drain strips shields for 6.5 s; the bot and its teammates fire into the field with headshot weapons; the thrower keeps its own distance so it is not drained (the field strips the user too).
- `EQ-DRAIN-03` Hill and territory clear: thrown into a contested hill, it makes every enemy inside a headshot; the SCORER steps out first.
- `EQ-DRAIN-04` Vehicle stop: a Warthog or Ghost that drives into the field stalls; a bot with a Power Drain is an anti-vehicle role in Big Team and holds it for the enemy tank or hog.
- `EQ-DRAIN-05` Defensive: thrown at your own feet when an enemy with a sword or shotgun is about to reach you removes their shields before the melee trade (you lose yours too, but you have the gun up first).

**Against an enemy drain (Proposed)**
- `EQ-DRAIN-06` Leave the field immediately; do not fight inside it. Shoot the drain (it can be destroyed) if leaving is not possible.
- `EQ-DRAIN-07` Vehicles: a driver that hears the hum reverses; if stalled, the crew exits on the far side and the gunner (if the turret still works) covers.
- `EQ-DRAIN-08` A Bubble Shield over the drain protects the team from it (Halo Diehards); if both items are on the team, the drain is countered by throwing the bubble on it.

### 3.3 Trip Mine

**Rule:** a proximity mine triggered by player or vehicle proximity or weapon fire; it can be placed on vehicles; crouch-walking passes it without triggering (Halo Diehards). It beeps and glows, so it is visible to anyone looking.

**Bot use (Proposed)**
- `EQ-MINE-01` Vehicle lanes: place it on the Warthog's road at a corner where the driver cannot see it until too late; a mine kills a Warthog and its crew.
- `EQ-MINE-02` Chokepoints the enemy must sprint through: flag room back door, bomb site entrance, hill ring entrance, teleporter exits, man-cannon landings.
- `EQ-MINE-03` On a vehicle: stick it to an enemy Warthog or Mongoose that is parked (it detonates when driven) or to a vehicle you are about to let the enemy steal (vehicle bait).
- `EQ-MINE-04` Bomb and flag defense: a mine on the arm site or flag stand forces the enemy to shoot it first, which gives the defender the first shot.
- `EQ-MINE-05` Never place it where our own vehicles route.

**Against an enemy mine (Proposed)**
- `EQ-MINE-06` Shoot it from range (it detonates on weapon fire) or crouch past it. The combat brain adds the mine's position to the pathfinder as a cost until it is cleared.
- `EQ-MINE-07` Vehicles: the driver slows and the gunner shoots it; a mine on a corner at speed is unavoidable, so vehicle bots treat known mine lanes as blocked.

### 3.4 Regenerator

**Rule:** a green mist that recharges the shields of anyone inside it (doubles the recharge rate per one community guide); both teams benefit if both are inside.

**Bot use (Proposed)**
- `EQ-REGEN-01` Triggers: holding a position under sustained fire (hill, flag room, bomb fuse), or after a fight when the group needs shields back before the next push.
- `EQ-REGEN-02` Deploy behind cover, not in a doorway; the mist is visible and tells the enemy where you are.
- `EQ-REGEN-03` Never deploy where the enemy can also stand in it; if an enemy enters, fight them at the edge where only our side benefits, or leave.
- `EQ-REGEN-04` Sword and shotgun users love a regenerator: constant shields in a melee fight. Route the regenerator to the close-range bot in a hold.

### 3.5 Deployable Cover

**Rule:** a solid energy wall (like a Covenant stationary shield but larger); cannot be walked through; blocks shots; can be destroyed with enough damage.

**Bot use (Proposed)**
- `EQ-COVER-01` Triggers: a sniper needs a window on open ground; a bomb carrier needs cover during the arm; a flag stand needs a wall facing the main approach; a hill needs an extra wall.
- `EQ-COVER-02` Place it to split a sightline, not to block a doorway the team needs; placed across a doorway it is a door the enemy must destroy, which buys 3 to 5 s and makes noise.
- `EQ-COVER-03` Vehicle use: a cover wall stops Warthog rams in a narrow lane; place it where a vehicle would otherwise splatter the defenders.

**Against enemy cover:** `EQ-COVER-04` Grenade over it or destroy it with the tank or a Spartan Laser; a Grav Lift under the base lifts it like a bubble.

### 3.6 Radar Jammer

**Rule:** floods every motion tracker in range, including ours, with false red dots; useful when entering a base in objective modes (Halo Diehards); pulled from Halo 3 matchmaking, present in MCC customs.

**Bot use (Proposed)**
- `EQ-JAM-01` Triggers: entering an enemy base in CTF, Assault, or One Flag; a flag/bomb push where the enemy relies on radar at a chokepoint.
- `EQ-JAM-02` Throw it ahead of the push so the enemy's radar fills before our real dots arrive; our bots ignore radar for the jammer's duration and rely on line of sight.

**Against:** `EQ-JAM-03` When our radar fills with dots, the brain treats radar as unavailable and switches to SWAT-style corner discipline (`SLAY-SWAT-02`) until it clears; expect a push from the direction the jammer landed.

### 3.7 Flare

**Rule:** a flash that blinds everyone in range who is looking at it, user included, for a few seconds; pulled from Halo 3 matchmaking, present in MCC customs.

**Bot use (Proposed)**
- `EQ-FLARE-01` Throw it around a corner you are about to push and look away (the brain turns the camera 180 degrees for the flash frame), then push.
- `EQ-FLARE-02` Escape tool: a carrier under fire drops it between itself and the chaser.

**Against:** `EQ-FLARE-03` Look away from the flare source immediately (the brain snaps the view to the floor behind the bot), back into cover, and spray the lane the flare came from.

### 3.8 Gravity Lift (portable)

**Rule:** a mini man-cannon that lifts infantry and vehicles; lifts a Bubble Shield generator or Deployable Cover off its spot (Halopedia).

**Bot use (Proposed)**
- `EQ-LIFT-01` Movement: reach a sniper perch or flag route the enemy does not expect; the brain's pathfinder adds lift-reachable nodes when the bot carries one.
- `EQ-LIFT-02` Counter-equipment: thrown under an enemy bubble or cover to remove it.
- `EQ-LIFT-03` Vehicle launch: a Warthog or Mongoose driven over a lift jumps a wall or a gap; a flag carrier's hog can skip a chokepoint.
- `EQ-LIFT-04` Anti-vehicle: placed in a lane, it flips a Warthog that drives over it at speed; the crew lands stunned.

### 3.9 Campaign-only: Invincibility, Cloaking, Auto-Turret (Halo 3 campaign and ODST Brutes)

- `EQ-INV-01` Invincibility (Chieftain drop): the bot uses it only to cross a lethal field (Hunter pair, Wraith lane) or to push a Chieftain with a hammer; it lasts a few seconds. In Firefight (ODST) the Chieftain's own invincibility is the trigger for `FF-BRUTE-04`: back off until it ends.
- `EQ-CLOAK-01` Cloaking (Stalker drop): short camo on demand; use for assassination approaches on Brutes (Halo 3 campaign has Brute assassination-style backsmacks).
- `EQ-TURRET-01` Auto-Turret: weak; place it covering a doorway behind the team's hold so it fires at flankers; it is a distraction more than a kill.
- `EQ-BRUTEEQ-01` ODST Brutes use Bubble Shields, Power Drains, Trip Mines, Flares, and Deployable Cover against the player. The FF brain reacts: a Brute bubble means walk in and melee or wait it out; a Brute Power Drain means leave its radius (ODST has no shields, but it still stalls vehicles); a Brute trip mine is a mine lane; a Brute flare means look away.

---

## Part 4. Halo: Reach armor abilities

**Rule facts (Halopedia Armor abilities; Fandom Armor Ability; Reach guides):** reusable with a cooldown; chosen from loadouts at spawn (loadouts are set by the gametype: Spartan tier loadouts and Elite loadouts); custom games can change cooldowns and whether abilities work while carrying objectives; campaign starts each level with Sprint. Seven abilities: Sprint, Jetpack, Armor Lock, Active Camo, Hologram, Evade (Elites by default in MP, Spartans in some variants), Drop Shield. Key numbers: Active Camo up to 15 s per activation per Halopedia's ability page (30 s as a Forge pickup; Neoseeker says standing still stretches the ability's meter to 30 to 60 s because the meter drains with movement); Armor Lock up to 5 s (Halopedia; one community guide says about 6); Jetpack about 6 s of fuel, better in bursts (community guide); Evade two rolls per charge (community guide); Hologram walks to the aimed point and stands there with a finite life; Drop Shield has health and dies if destroyed, and damaging it does not shorten its timer unless it is destroyed (Halopedia).

### 4.1 Sprint (Spartan default)

**Rule:** run faster for a limited time; cannot fire, melee, or throw while sprinting; weapons can be switched during sprint (Fandom).

**Bot use (Proposed)**
- `EQ-SPRINT-01` Triggers: crossing open ground between covers; rotating to a moving hill or a flag intercept point; closing on a sword or shotgun kill; escaping a losing fight by breaking line of sight; reaching a power weapon or vehicle at spawn.
- `EQ-SPRINT-02` Never sprint into a sightline you have not checked; the sprint-to-fire delay is the deadliest moment in Reach. The brain ends sprint 1 s before the next corner so the weapon is up as the bot rounds it.
- `EQ-SPRINT-03` Sprint and the sword: sprint-lunge is the standard Reach sword play; the combat brain allows a sprint directly at a target only when holding a sword or shotgun and inside 15 m.
- `EQ-SPRINT-04` Carriers: flag and ball carriers move at 75 percent and cannot sprint in most variants (abilities while carrying is a custom setting); the brain checks the setting.

### 4.2 Jetpack

**Rule:** vertical flight on a fuel meter (about 6 s continuous, longer in bursts); the user can fire while flying; fuel recharges on the ground; Jetpack users are loud and visible.

**Bot use (Proposed)**
- `EQ-JET-01` Triggers: reach a height the enemy does not hold (sniper perch, top-mid, a base roof) to shoot down; cross a gap or a vehicle lane without touching it; escape a grenade, a Wraith mortar arc, or a melee charge by going up; Infection survivor escape with headshots downward (Fandom); Wraith-hunting from above where the mortar cannot track (`REACH-PUR-03`, vehicle file Wraith notes).
- `EQ-JET-02` Bursts, not holds: the brain fires the pack in 0.5 s pulses to conserve fuel and to stay low enough to drop behind cover.
- `EQ-JET-03` Never hover in the open. A hovering Jetpack is the easiest headshot in the game. Rise, shoot one burst, drop.
- `EQ-JET-04` CTF offense: the Jetpack covers the most ground (community guide); the flag runner's escorts use it to reach the flag room from above and the runner takes the ground route; a runner with the Jetpack flies out only if the carrier-abilities setting allows it.
- `EQ-JET-05` Invasion Spire: Jetpack to the core platform and the Spire top (`REACH-INV-01` with the Falcon as the alternative).
- `EQ-JET-06` Firefight: Jetpack onto roofs and ledges for Hunter back shots and Wraith avoidance; it is the best Firefight ability with the Plasma Launcher ("jet pack plus plasma launcher," GameFAQs Reach thread).

**Against an enemy Jetpack (Proposed)**
- `EQ-JET-07` Shoot it in the air with precision; it cannot dodge sideways. Target weight for airborne enemies 1.4.
- `EQ-JET-08` Its landing spot is predictable; a bot throws a grenade where it will land.
- `EQ-JET-09` Rocket lock-on works on a Jetpack user in Reach? Not reliably; use precision weapons and the Plasma Launcher.

### 4.3 Armor Lock

**Rule:** the user drops into a locked stance, invulnerable to all damage, immobile, cannot fire; up to about 5 s or until released; stuck grenades fall off on activation; releasing after a full hold emits an EMP burst that strips nearby shields and stalls nearby vehicles (Halopedia; Neoseeker; LP archive). Vehicles that collide with a locked player at speed take heavy damage or are destroyed (Fandom AA tips; Wikipedia Reach). Coming out of lock, the user is a stationary target ("a glowing target," community guide); the standard counter is to wait at range (LP archive) or to get close and lock yourself as they come out (Fandom tip). Elites in Armor Lock (Firefight, Invasion defenders) use it when under fire.

**Bot use (Proposed)**
- `EQ-LOCK-01` Triggers (any one): a plasma grenade is stuck to the bot; a rocket, laser, tank shell, Banshee bomb, or Wraith mortar is inbound and cannot be dodged; a vehicle is about to splatter the bot and it cannot clear the lane (lock destroys or heavily damages the vehicle); the bot is being shot by two or more enemies with no cover inside 3 m and teammates are 3 s from arriving; an enemy vehicle is inside 5 m and the bot wants the EMP burst to stall it for a boarder.
- `EQ-LOCK-02` Hold duration: against a stuck grenade or a single incoming projectile, release the instant the blast passes (0.5 to 1.5 s) so the bot is up before the enemy repositions. Against a vehicle, hold until it has hit or passed. Against a group, hold the full 5 s for the EMP burst only if two or more enemies are within burst range when it ends; otherwise release early and fight.
- `EQ-LOCK-03` EMP exit: when releasing a full lock with enemies in range, the bot comes out with a headshot weapon on the nearest stripped enemy; the burst also stalls a vehicle inside the radius, which is the cue for a teammate to board it.
- `EQ-LOCK-04` Never lock to wait for help that is not coming. If no teammate is within 10 s, locking just delays the death and gives the enemy a free reposition; evade or fight instead.
- `EQ-LOCK-05` Objective rules: locking drops the flag/bomb/ball (carriers cannot use abilities in default settings anyway); a carrier under fire runs, it does not lock. A defender standing on a bomb or flag can lock to block melee access for 5 s while teammates arrive (body-block).
- `EQ-LOCK-06` Vehicle bait: a bot standing in a Warthog's lane with Armor Lock ready is an anti-vehicle trap; the vehicle file's ram geometry rules forbid enemy bots from ramming a glowing target, so this also works as area denial against bot drivers.
- `EQ-LOCK-07` Never in Infection (Halopedia: never use Armor Lock in Infection; it only delays the pack).

**Against an enemy Armor Lock (Proposed)**
- `EQ-LOCK-08` Stop shooting; it wastes ammo and the enemy's shields are untouched by anything while locked. Reposition to a place where the bot has line of sight when the lock ends but is outside the EMP burst radius (keep 6 m or more).
- `EQ-LOCK-09` Grenade timing: throw a frag to detonate 0.3 s after the lock would expire (max 5 s from the activation glow); the bot counts from the activation. A plasma grenade placed at their feet (not stuck) also works because the lock does not fling un-stuck grenades.
- `EQ-LOCK-10` Close-range counter (Fandom): get close and lock yourself as they come out, so their EMP hits a locked target and they come out into your melee. The brain uses this only when the enemy is alone.
- `EQ-LOCK-11` Vehicles: never ram a locked player (vehicle file: Armor Lock is a hard no-ram). Drive around or shoot after the lock ends.
- `EQ-LOCK-12` Elites locking in Firefight: `FF-ELITE-04` (back off, resume after; stick a grenade next to it to detonate as the lock ends).

### 4.4 Active Camouflage (armor ability)

**Rule:** near-invisible while still or slow, visible when moving fast; the meter drains faster with movement (standing still can stretch it to 30 to 60 s, Neoseeker); also jams every radar in range including the user's (Fandom, GamesRadar); shooting reveals; the Forge pickup version is a 30 s power-up. Useful in no-radar gametypes because the jam does not give the user away (Fandom); useful in Generator Defense (Halopedia).

**Bot use (Proposed)**
- `EQ-RCAMO-01` All of the camo pickup rules (`EQ-CAMO-01` to `-07`) apply, plus:
- `EQ-RCAMO-02` The radar jam is a tell. When the enemy's radar fills with dots they know a camo user is near. In radar-on gametypes the bot activates camo only when already in position (crouched at the ambush spot), never while moving in, so the jam appears only when it is too late. In SWAT and other no-radar variants the jam is free and camo is activated on every approach.
- `EQ-RCAMO-03` Hold still to extend: the ambush bot stands still at a corner the enemy will pass, meter nearly frozen, and lunges/shoots when the enemy is inside 3 m.
- `EQ-RCAMO-04` Generator Defense attackers use camo to reach the generator uncontested (Halopedia tip); Invasion phase 1 attackers use it to enter a territory and start the capture unseen.
- `EQ-RCAMO-05` Firefight: camo breaks enemy AI targeting; a camo bot crosses the open to reach a Hunter's back (`FF-HUNTER-02` flanker).

**Against:** `EQ-RCAMO-06` When our radar fills with dots in a radar-on game, a camo user is within jam range: back to a wall, grenade the corners, and look for the shimmer; a hologram walked past a suspected spot draws its fire.

### 4.5 Hologram

**Rule:** a decoy that walks in a straight line to the aimed point and stands there; it mimics the user's loadout; finite lifespan; enemies shooting it reveal themselves; it does not strafe, jump, or raise its weapon. Elite Skirmisher Commandos and Champions use it in Firefight.

**Bot use (Proposed)**
- `EQ-HOLO-01` Triggers: before peeking a sightline (send the hologram across first; anyone who shoots it has revealed position and is mid-burst when the bot peeks); before entering a flag room or bomb site (draws grenades); in Regicide to distract players heading toward the King (Halopedia Regicide tip); as a fake flag runner (the hologram runs the obvious route while the real runner takes the other).
- `EQ-HOLO-02` Send it where a real player would go: along cover, toward a weapon spawn, into a doorway. A hologram sent into the open is spotted as fake.
- `EQ-HOLO-03` Follow it by 1 s and 2 m to the side; the enemy's reticle is on the hologram's head when the real bot appears.
- `EQ-HOLO-04` Sniper bait: a hologram walked across a sniper lane finds the sniper; the bot counts the tracer and pushes the sniper's position.

**Against:** `EQ-HOLO-05` Detection: straight-line walk, no strafe, no weapon raise, walks into walls, no radar blip in some versions, and it dies without a body. The combat brain holds fire on any target that has walked in a straight line for more than 1.5 s without strafing and instead watches the corner it came from; it fires only when the target changes direction or raises a weapon. Grenades at a hologram are wasted; hold them.

### 4.6 Evade (Elite default; Spartan in some variants)

**Rule:** a fast directional roll that breaks lock-ons and tracking (rockets, Plasma Launcher, Needler homing); two rolls per charge (community guide); good with the sword; Elite Firefight enemies roll constantly.

**Bot use (Proposed)**
- `EQ-EVADE-01` Triggers: rocket lock tone, Plasma Launcher bolts inbound, Needler stream (break supercombine), a grenade landing at the feet, a vehicle splatter line, a Wraith mortar arc, a sword lunge (roll sideways out of lunge range), and closing the last 5 m on a sword or shotgun kill.
- `EQ-EVADE-02` Direction: perpendicular to the threat; never roll toward the enemy unless finishing with a melee.
- `EQ-EVADE-03` Two charges: the second roll is saved for the escape; the brain never spends both on offense.
- `EQ-EVADE-04` Invasion Elites: roll between covers in the open phases; Elites with Evade are the territory contesters in phase 1.

**Against:** `EQ-EVADE-05` Rockets and homing bolts are wasted on an Elite with Evade ready; fire them when the enemy is mid-roll or has just used both charges (count rolls). Precision fire at the roll's exit point: the roll ends in a predictable spot.

### 4.7 Drop Shield

**Rule:** a dome like the Halo 3 bubble, but with health: it blocks projectiles, lets players through, regenerates the health (not just shields) of everyone inside, and dies when destroyed by enough damage; damaging it without destroying it does not shorten its life (Halopedia). Available on the Medic loadout. Saves health kits in Firefight (Fandom tip).

**Bot use (Proposed)**
- `EQ-DROP-01` Triggers: all Bubble Shield triggers (`EQ-BUBBLE-01`) plus: a teammate is low on health (not just shields) and a health pack is far; Firefight between waves to heal the team; a Wraith is shelling the hold (the dome absorbs mortar splash for its health pool).
- `EQ-DROP-02` Placement and inside-behavior as the Bubble Shield (`EQ-BUBBLE-02` to `-05`), plus: the dome has health, so a tank or Wraith kills it in a few shots; under tank fire, use it only to cross or to heal for 3 s, not to hold.
- `EQ-DROP-03` Carriers: a Drop Shield at the flag stand or bomb site is a 10 s plant/arm protector; the Medic bot escorts the carrier for this reason.

**Against:** `EQ-DROP-04` Walk in and melee (as the bubble); or destroy it with explosives and heavy weapons (it has health, unlike the Halo 3 bubble); a Wraith or Scorpion shell plus a grenade pops it. Enemies inside are healing; kill it fast or go around.

---

## Part 5. Halo 4 armor abilities and packages

**Rule facts (Halopedia Armor abilities/H4; Fandom Armor Ability; MP1st; gamerguides; GameFront unlock guide):** eight abilities chosen per loadout: Promethean Vision, Thruster Pack, Hologram, Jet Pack, Active Camo (up to 18 s, 16 s recharge from empty), Hardlight Shield (front-facing, cannot be destroyed, drains on use, user slowed and cannot fire), Autosentry (slow-firing drone, killable in a few shots), Regeneration Field (green bubble that recharges shields and, on deployment, pushes enemies away; the only ability not in campaign). Sprint is always available independent of the ability. Loadouts also carry one Tactical Package and one Support Upgrade. Personal ordnance drops supply power weapons and the Overshield, Speed Boost, and Damage Boost power-ups in Infinity Slayer. Each ability has a meter and recharge; AA Efficiency speeds the recharge.

### 5.1 Promethean Vision

**Rule:** see enemy silhouettes through walls and obstacles at short range (a "Predator" view); the world detail dims while active; a short pulse per activation with a recharge.

**Bot use (Proposed)**
- `EQ-PV-01` Triggers: before every corner peek in a 1v1; before entering a flag room, bomb site, or hill; when radar shows a dot with no line of sight; in Flood when the survivors' hold is being approached; against camo users (it shows them).
- `EQ-PV-02` Pulse, do not hold: activate for the first 1 s, read positions, release; the dimmed world is a liability in a fight.
- `EQ-PV-03` Information share: positions seen are broadcast (the objective brain's callouts), so one PV bot informs four.
- `EQ-PV-04` Wallbang planning: it does not shoot through walls, but it tells the bot which door the enemy will come out of; pre-aim it.

**Against:** `EQ-PV-05` Assume the enemy sees you through the wall you are hiding behind if they are within 20 m; move after every stop, do not camp a corner against a known PV user, and use Stealth (support package) which hides from PV (community-reported package effect; verify).

### 5.2 Thruster Pack

**Rule:** a short horizontal burst (shorter than Reach's Evade); breaks tracking; speeds descent off an edge; recharges quickly.

**Bot use (Proposed)**
- `EQ-THRUST-01` Triggers: the same list as Evade (`EQ-EVADE-01`) with shorter distances; plus: thrust around a corner to re-peek from a new angle, thrust off a ledge to drop from a sightline, thrust into a melee range finish.
- `EQ-THRUST-02` Thrust-to-cover: the brain only thrusts when the end point has cover within 1 m of it; a thrust into open ground is a slow strafe.
- `EQ-THRUST-03` Ricochet and CTF: a thruster carrier crosses a doorway or goal line faster than a defender can react; the brain thrusts on the last 3 m to the goal.

**Against:** `EQ-THRUST-04` Aim at the exit point, not the start; a thrust is short, so the exit point is within 3 m; grenades at the exit.

### 5.3 Hardlight Shield

**Rule:** a front-facing barrier that stops most small arms and some explosives; indestructible but drains while active; the user moves and turns slowly, cannot fire, and shields do not recharge while it is up; good for blocking projectiles or waiting out an enemy's ammo before engaging (gamerguides). Promethean Watchers use it.

**Bot use (Proposed)**
- `EQ-HLS-01` Triggers: a rocket, grenade, or sniper shot is incoming from the front and there is no cover; crossing a sightline toward a teammate; closing on an enemy who is firing a long reload weapon (block, let them empty, drop the shield and shoot); covering a flag/bomb carrier from the front during a short crossing (walk backward in front of them); covering a disarm or an Extraction convert (the converter works behind the shield bot).
- `EQ-HLS-02` Never hold it in a fight with enemies on two sides; it blocks the front only, and the slowed turn makes the second enemy a free kill.
- `EQ-HLS-03` Drop it the instant the enemy reloads or looks away; the drop-to-fire time is the window.
- `EQ-HLS-04` Vehicles: a Hardlight Shield does not stop a Warthog; the bot steps aside.

**Against:** `EQ-HLS-05` Flank (it is front-only), throw grenades behind it (splash from behind hits), melee from the side, or wait for the drain; a bot facing a shield user alone holds position and waits, because the shield user cannot fire either.

### 5.4 Hologram (Halo 4)

Same rules as Reach (`EQ-HOLO-01` to `-05`). Halo 4 holograms also appear on radar as a friendly-looking dot to the enemy in some settings; the counter rule stands.

### 5.5 Jet Pack (Halo 4)

Same rules as Reach (`EQ-JET-01` to `-08`); Halo 4's pack has less fuel and a stronger landing animation, so `EQ-JET-02` bursts become 0.3 s.

### 5.6 Active Camo (Halo 4)

**Rule:** up to 18 s, 16 s recharge from empty (Halopedia); drains with movement; radar jam as in Reach. All Reach camo rules apply (`EQ-RCAMO-01` to `-06`); Promethean Vision shows camo users, so `EQ-RCAMO-02` adds: do not camp a corner against a PV user.

### 5.7 Autosentry

**Rule:** a deployable drone that fires slow energy bolts at a moderate rate and dies in a few shots; Promethean Knights use it; can be set to defend the user or hold a chokepoint.

**Bot use (Proposed)**
- `EQ-SENTRY-01` Triggers: holding a hill, flag room, bomb fuse, Dominion base, or Extraction beacon; covering a doorway behind the team; covering a reload.
- `EQ-SENTRY-02` Placement: high, in a corner, with the doorway in its arc and out of the enemy's first sightline so they take a bolt before they see it. Its value is the distraction: enemies shoot it instead of the bot.
- `EQ-SENTRY-03` Never deploy in the open or in a lane a vehicle uses.

**Against:** `EQ-SENTRY-04` Kill it with two or three precision shots from outside its range before entering, or ignore it when it faces away; its bolts are slow and strafable.

### 5.8 Regeneration Field

**Rule:** a green field that recharges the shields of everyone inside; deployment pushes enemies away (a kinetic blast); damage inside pauses the regen briefly; not available in campaign.

**Bot use (Proposed)**
- `EQ-RFIELD-01` All Regenerator triggers (`EQ-REGEN-01` to `-04`), plus: the deployment push is a melee-range escape (an enemy in melee range is shoved back; the bot shoots them as they stagger); and a Flood survivor hold uses it between rushes.
- `EQ-RFIELD-02` Dominion base defense and Extraction beacon defense: the field sits on the capture point so defenders regen while standing on the objective.

**Against:** `EQ-RFIELD-03` Do not fight inside an enemy field; pull them out with grenades or wait; a field is a stationary green marker that tells you exactly where the enemy is holding.

### 5.9 Tactical Packages and Support Upgrades (loadout modifiers)

**Rule (from the unlock guides; effects are as described by 343's loadout descriptions):**
- Tactical: Mobility (unlimited sprint), Shielding (faster shield recharge), Resupply (pick grenades off dead players), AA Efficiency (faster ability recharge), Grenadier (extra grenade), Firepower (two primary weapons), Fast Track (more XP; no gameplay effect), Requisition (re-roll ordnance choices), Wheelman (vehicle resistance to EMP and faster vehicle regen; Specialization unlock).
- Support: Ammo (more ammo), Dexterity (faster reload and weapon switch), Sensor (longer radar range), Awareness (radar while scoped), Explosives (stronger grenades, less self-damage), Ordnance Priority (ordnance earned faster), Stealth (quieter, faster assassinations, harder to see with PV), Nemesis (marks your last killer), Drop Recon (shows incoming ordnance), Gunner (turret cooldown and mobility while carrying), Stability (less flinch when hit).

**Bot loadout logic (Proposed)**
- `EQ-PKG-01` Per role: ANCHOR/sniper = Awareness + Stability + Promethean Vision or Hologram; SLAYER = Shielding + Dexterity + Thruster Pack; CARRIER/RUNNER = Mobility + Dexterity + Thruster or Jet Pack; ANTI-VEHICLE = Grenadier + Explosives + Plasma Pistol secondary; VEHICLE DRIVER = Wheelman (if unlocked) + Gunner + Hardlight Shield (for exiting under fire); STEALTH = Stealth + Sensor + Active Camo; HOLD/DEFENSE = Shielding + Ammo + Autosentry or Regeneration Field.
- `EQ-PKG-02` Posture adjustments: CONSERVATIVE favors Shielding and Ammo; DESPERATE favors Mobility, Grenadier, and Explosives; Infection/Flood survivors favor Ammo and Dexterity, Flood favor Mobility and Stealth.
- `EQ-PKG-03` Ordnance choice (Infinity Slayer): when the three-way choice appears, pick in this order: a power weapon that counters the enemy's current vehicle or power weapon > Damage Boost if a vehicle gunner or precision anchor can use it in the next 30 s > Overshield for whoever is about to push > Speed Boost for a carrier. Never call ordnance into a contested spot (`SLAY-REG-03`).

---

## Part 6. Vehicle interactions summary

| Item | Effect on vehicles | Bot rule |
|---|---|---|
| Overshield on a driver | Extra survivability in open vehicles; in Halo 2/3 where damage bleeds to occupants it is effectively hull health | `EQ-OS-06` route to the escort hog driver |
| Camo on a driver | The vehicle is still visible; useless | never |
| Power Drain (H3) | Stalls engines in radius; opens boarding | `EQ-DRAIN-01`, `-04`, `-07` |
| Trip Mine (H3) | Kills light vehicles; can be stuck to vehicles | `EQ-MINE-01`, `-03`, `-07` |
| Grav Lift (H3) | Launches vehicles; flips a hog at speed | `EQ-LIFT-03`, `-04` |
| Bubble/Drop Shield | Vehicles drive through; no protection from splatters | `EQ-BUBBLE-05`, `-08` |
| Deployable Cover (H3) | Blocks rams in narrow lanes | `EQ-COVER-03` |
| Armor Lock (Reach) | Destroys or heavily damages a vehicle that hits a locked player; EMP burst stalls vehicles; vehicle bots never ram a locked target | `EQ-LOCK-01`, `-03`, `-06`, `-11` |
| Evade/Thruster | Dodges splatter lines | `EQ-EVADE-01`, `EQ-THRUST-01` |
| Jetpack | Above tank cannon arcs; Wraith hunting; Banshee can still reach you | `EQ-JET-01` |
| Hardlight Shield (H4) | Does not stop vehicles | `EQ-HLS-04` |
| Damage Boost (H4) | Doubles vehicle weapon damage | `EQ-DMG-01` |
| Wheelman package (H4) | Resists EMP, faster vehicle regen | `EQ-PKG-01` driver loadout |
| Plasma Pistol overcharge (all from Halo 3) | The universal vehicle EMP; strips overshield | vehicle file Quick Reference, `EQ-OS-08` |

## Part 7. Gametype hooks summary

| Gametype need | Best item by game |
|---|---|
| Flag/bomb/ball carrier survival | Overshield (CE/H2/H3 pickup), Bubble Shield at the grab (H3), Drop Shield at the stand (Reach), Thruster for the last 3 m (H4), Speed Boost (H4) |
| Sneaking into a base | Camo pickup, Radar Jammer (H3), Camo AA in no-radar modes (Reach/H4), Hologram decoy first (Reach/H4) |
| Holding a hill or site | Regenerator and Deployable Cover (H3), Drop Shield (Reach), Autosentry and Regeneration Field (H4), Trip Mine at the entrance (H3) |
| Clearing a hill or site | Power Drain (H3), grenades timed to a Bubble/Drop Shield expiry, Grav Lift under their cover, Armor Lock EMP burst (Reach) |
| Anti-vehicle | Power Drain and Trip Mine (H3), Armor Lock body-block and EMP (Reach), Plasma Pistol everywhere from H3, Wheelman for our own drivers (H4) |
| Moving hills and rotations | Sprint (Reach), Mobility package (H4), Speed Boost, Jetpack over gaps |
| One-life modes | Hologram before every peek, Hardlight Shield for crossings, Promethean Vision at every corner, Armor Lock only for stuck grenades |
| Infection survivors | Jetpack escape, never Armor Lock, Drop Shield for heals, Ammo and Dexterity packages; Flood: Mobility, Stealth, Thruster |
| Firefight | Drop Shield to save packs, Jetpack plus Plasma Launcher, Camo to flank Hunters, Armor Lock for Hunter charges, Hologram to pull Jackal snipers |

## Part 8. What is sourced and what is not

Durations and mechanics come from Halopedia (Power-up, Overshield via Fandom, Active camouflage, Equipment, Z-4190 bubble shield, Power drain, Armor abilities, Armor abilities/H4), Fandom (Equipment, Armor Ability, Speed Boost, Overshield), StrategyWiki Halo 3/Equipment, the Halo 1 Guide power-up page and the Steam CE spawn-time guide (CE respawn timers and the 45 s overshield decay steps), Halo Diehards' MCC guide, Neoseeker and LP Archive Reach guides, and the Halo 4 loadout and unlock guides (MP1st, gamerguides, GameFront, Supercheats). Halo 2 and Halo 3 overshield decay timings to the second, Halo 3 equipment exact radii, Reach ability meter values, Halo 4 ability meter values, and the exact effect of the Stealth package against Promethean Vision are not published and should be measured in MCC or read from the tags. Everything tagged Proposed is untested design logic.

---

## Patch: Difficulty tiers and optional coach hooks (equipment brain)

**Difficulty tiers.** `halo_mcc_bot_tiers_integration_and_coach.md` Part 2.3 scales this file: Easy bots take power-ups when stumbled on and know one or two triggers per item; Normal heads for nearby pickups and knows half the trigger list; Heroic pre-positions sometimes, routes pickups by role, and runs the full trigger list; Legendary pre-positions 5 s early, runs denial pickups, uses every counter (grenade timed to Armor Lock expiry, Grav Lift under a bubble), detects holograms and camo by all cues, and chooses Halo 4 loadouts by role and posture. Per-bot variance and personalities (campers favor Cover, Trip Mine, Autosentry, Drop Shield; flankers favor camo, Radar Jammer, Hologram, Jetpack; supports favor Regenerator, Drop Shield, Regeneration Field) apply as in Part 3 of that file.

**Integration.** Ability triggers fire inside the on-foot brain's tick via `equipment_hint` (which triggers are enabled this life); the hard rules here (`EQ-LOCK-07` never Armor Lock in Infection, `EQ-LOCK-11` never ram a locked target, `EQ-CAMO-03` no firing from camo unless the first burst kills) outrank on-foot habit (`INT-04`).

**Optional coach.** Hooks the objective brain may pass into this brain when a coach is attached:

| Hook | Allowed | Hard limits that always win |
|---|---|---|
| `COACH-EQ-pickup_owner` | name which living bot takes the next overshield, camo, custom powerup, Speed or Damage Boost | `EQP-07` (no two power-ups on one bot unless pure denial); carriers never take camo for a long carry (`EQ-CAMO-07`) |
| `COACH-EQ-deny_or_use` | DENY or USE for the next power-up spawn | DENY forced in CONSERVATIVE posture (`EQP-03`) |
| `COACH-EQ-trigger_mask` | enable or disable specific trigger IDs for a bot this life (for example, disable `EQ-LOCK-01` vehicle-bait lock for the runner) | cannot enable a trigger above the bot's tier list; cannot disable survival triggers (stuck grenade lock, bubble on shields-down for a carrier) |
| `COACH-EQ-loadout` | Halo 4 ability plus tactical and support packages per bot (`EQ-PKG-01`) | must be unlocked and allowed by the gametype |
| `COACH-EQ-ordnance_pick` | which of the three ordnance options to take | follows `EQ-PKG-03` order unless the coach's tendency log names a specific counter (enemy tank up -> rockets over Damage Boost) |
| `COACH-EQ-decoy` | send a hologram along a named lane before a push, or seed a trip mine on a named lane | lanes must be enumerated; mines never on our own vehicle routes (`EQ-MINE-05`) |

Coach plays that touch this brain: `PLAY-TIMER-DENY`, `PLAY-VEHICLE-BAIT`, `PLAY-BREAKOUT` (power-up split), and the hologram-first entries in the tendency table (addendum Part 4.7).
