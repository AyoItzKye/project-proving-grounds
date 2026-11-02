# Advanced techniques by game

The moves that separate a bot that follows rules from one that plays like a person. Every technique is written as what to do, when, and the game fact behind it.

## Halo: Combat Evolved

CE is the fastest-killing Halo: a 3-shot pistol, long grenade throws, no sprint and health packs. The bot that wins CE is the one that sees first, shoots at head height first, and never walks a lane an enemy pistol can see.

### Pistol mechanics

- Rate of fire: the pistol can fire as fast as the trigger is pulled, but accuracy drops if shots are spammed faster than about 0.2 s apart. Fire at the natural cadence (roughly 3 shots in 0.6 s) and the three-shot kill lands.
- Zoom (2x) does not change bullet spread; it only steadies aim. Zoom at Medium and Long band; stay unzoomed at Short because zoom narrows the field of view and loses a strafing target.
- Bullet magnetism and auto-aim are strong in CE: shots near the head count as head shots at Medium band. The bot can aim at the upper chest at Long band and still land head shots.
- Damage: body shots do about a third of a shield each; the third shot to the head kills. If the first two shots were body shots, the third must be a head shot or a fourth and fifth shot are needed.
- The kill time of 0.6 s means the first player to land a shot has a huge edge; pre-aiming at head height on every corner is the single most important CE habit.

### Grenades in CE

- Frag throw range is about 60 to 70 ft on flat ground; plasma grenades go slightly less far. The bot can and should throw from Long band onto known camping spots and spawn points.
- Grenade damage: a frag landing within 5 ft strips a full shield; within 2 ft it kills a full-shield player outright. Two frags at once kill anywhere within about 8 ft.
- Grenade launching: a grenade thrown onto an enemy's feet at Short band followed by one pistol shot is a kill. A grenade thrown at a pair of enemies pushing a doorway is usually a double shield strip.
- Grenade jumping: throw a frag at the bot's own feet and jump as it explodes; the blast launches the bot to ledges a normal jump cannot reach (Damnation, Prisoner, Hang 'Em High have classic grenade-jump spots). It costs about half the shield; only do it with a full shield and no enemy in sight.
- Bouncing: frags skip off floors with a low throw; throw at the ground 10 ft in front of a doorway to skip it inside without arcing high into a ceiling.

### Movement in CE

- No sprint and a slow strafe: fights are decided by positioning before they start. Crouch-jumping (jump then crouch at the apex) adds reach for ledges on every CE map.
- Crouching does not hide the bot from radar in CE (it does in every later game). Radar shows all moving and stationary players within range, so the bot cannot rely on crouch ambushes; it relies on height and corners instead.
- Fall damage exists: dropping more than about two player heights pops the shield. Do not drop from Prisoner's top level or Damnation's top to escape unless the alternative is death.
- Ladders: the bot is defenseless while climbing. Grenade the top of a ladder before climbing; shoot anyone on a ladder.

### Health packs

- Health is 8 segments and does not regenerate. One segment left means a single body shot or a grenade tick kills even with a full shield.
- The bot keeps a map of health pack locations and distances. After any fight that cost health, it routes to the nearest pack through covered paths before re-engaging.
- Deny health: standing on an enemy's nearest health pack when the enemy is wounded is a strong defensive play on Chill Out, Prisoner and Damnation.

### Powerups

- Active camo lasts about 45 s; the bot is nearly invisible while still and shimmering while moving. Camo plus a pistol at Medium band or camo plus a shotgun at a corner. Firing does not remove camo in CE, so the bot can keep shooting.
- Overshield gives a triple shield that slowly decays. Take overshield and rush rockets or the enemy's power position.
- Both powerups respawn on fixed timers (about 60 s on most maps); contest them like weapons.

### Spawning in CE

- Spawns are influenced by teammates: a bot tends to respawn near living teammates and away from enemies. A team that holds one side of the map keeps spawning there.
- Spawn killing: on Chill Out and Prisoner, a team that holds the top with grenades can throw onto the enemy's spawn points repeatedly. The bot should learn spawn points per map and nade them when the enemy team is dead and no better play exists.

### Weapon-specific CE tricks

- Shotgun: fires 15 pellets with a wide spread; a one-shot kill out to about 10 ft, two shots to about 20 ft. Pump animation can be cancelled by switching weapons and back, making the second shot faster.
- Sniper: no bullet drop, hitscan; 2x and 8x zoom. No-scope at Short band is viable because of magnetism; one body shot then one melee kills.
- Rockets: two in a magazine, large splash. Fire at the floor next to an enemy's feet; a direct hit is unnecessary. Against a Warthog aim at the ground under the gunner.
- Plasma rifle: the stun slows an enemy who takes sustained fire, which makes them easier to pistol. Plasma rifle to strip the shield then one pistol head shot is a fast kill.
- Needler: 7 needles to supercombine; strong against an enemy in the open who is strafing, since needles track. Useless against cover.
- Assault rifle: 60 rounds, large spread; only for finishing an unshielded enemy at Short band or for a melee setup. Drop it for a pistol or a plasma rifle whenever one is found.

## Halo 2 and Halo 2: Anniversary

Halo 2 Classic in MCC keeps the original engine, so the button combos and physics exploits of 2004 still work. H2A multiplayer is a separate sandbox on the Halo 4 engine with Halo 2 tuning; most of the combos below do not work in H2A, but the positioning and weapon logic do.

### Button combos (Halo 2 Classic only)

These cancel animations to kill faster. A Veteran or higher bot uses them; lower tiers should not.

| Combo | Inputs (default layout) | Effect | When the bot uses it |
| --- | --- | --- | --- |
| BXR | Melee (B), reload (X) to cancel the melee recovery, fire (R) | A melee followed by an instant BR burst; kills a full-shield enemy at Melee band in about 0.5 s | Any Melee-band fight with a BR; faster than two melees |
| BXB | Melee, reload cancel, melee | Two melees almost at once | Melee band with an empty or non-precision weapon |
| Double shot (RRX) | Fire, fire again during the burst, reload to cancel | Two BR bursts in the time of one | Any BR duel at Short or Medium band; cuts the 4-burst kill to two trigger pulls |
| Quad shot | Double shot chained with a weapon switch cancel | Four bursts almost at once | Elite and Pro tiers only; risky if mistimed |
| YY (weapon switch cancel) | Switch weapons twice quickly | Cancels reload, melee or scope-out animations | After every reload start when an enemy appears; after a melee that missed |
| Sword cancel | Lunge (R) then switch weapons (Y) before the lunge connects | The lunge motion continues but the swing is cancelled; the bot flies toward the target | Used as sword flying (below) and to close distance without committing |

### Sword flying and sword lunges

- The sword reticle turns red at about 20 to 25 ft on a visible enemy; the lunge then covers that distance instantly. Lunge range is longer than the shotgun's one-shot range, so a sword that sees the enemy first usually wins.
- Sword flying: with a sword and a second weapon, aim at an enemy at the edge of the red reticle, press lunge and immediately switch weapons; the bot is thrown toward the target without swinging. Chaining this across a map lets a bot cross Midship or Lockout in two lunges. Enemies in vehicles or at odd heights give long flights.
- Sword clash: two sword lunges meeting cancel each other. The bot should not lunge into an enemy who is already lunging; sidestep and lunge after their swing.
- Sword versus shotgun: the shotgun one-shot reaches about 12 ft; the sword lunge about 22 ft. A sword that gets the red reticle first wins; a shotgun around a corner at Melee band wins. The bot with the sword avoids corners it cannot see around and uses lifts, where the shotgun user cannot aim up quickly.

### Dual wield combos

- Plasma rifle plus SMG: the plasma rifle strips the shield and stuns, the SMG does the health damage. Best Short-band combo in the game.
- Dual plasma rifles: the fastest shield strip; overheat after about 3 s of fire, so fire in 1 s bursts.
- Dual SMGs: highest raw damage at Short band; the recoil climbs, so the bot aims at the belt line and lets the recoil walk the fire up to the head.
- Dual needlers: strong against enemies in the open at Short to Medium band; the supercombine explosion also damages nearby enemies.
- Dual magnums: strong at Short to Medium band because both can land head shots after the shield drops.
- Plasma pistol plus magnum or SMG: charge the plasma pistol, release, then the second weapon finishes; the classic noob combo without the swap.
- Dropping: pressing the secondary weapon's drop input returns melee and grenades. The bot drops the weaker weapon the moment it needs a grenade or a melee, or when an enemy reaches Medium band and the bot needs a BR.

### Super bounces (Halo 2 Classic)

- Crouching on specific seams in the geometry and then jumping launches the player to roof tops (Lockout tower tops, Ascension's upper rocks, Burial Mounds, Headlong rooftops). They are precise inputs the scripting agent can record as waypoint sequences.
- Most competitive settings treat the spots as out of bounds; a bot in a ranked setting should not use them. In casual lobbies a Pro bot may use one for a sniper position.

### Flag and bomb play

- Flag juggling: throw the flag forward and pick it up again; the throw moves it faster than carrying and briefly lets the bot shoot. The bot juggles on safe stretches and carries when enemies are near.
- The flag carrier's melee is a strong hit (two kills a full-shield player). The bomb carrier's melee is similar.
- Flag at home rule: the bot cannot score while its own flag is away in standard CTF; it waits under cover near the capture point.

### Grenades in Halo 2

- Frags are strong and bounce well; a frag through a doorway strips a shield from anyone inside.
- Plasma grenades stick players and vehicles; a stuck Ghost or Warthog is destroyed. The stick animation on a player gives them a second to melee the bot, so stick then back off.
- Grenade spam on Lockout's bottom mid, Midship's top mid and Beaver Creek's roofs is standard; throw from behind cover with the arc memorized.

### Spawn logic in Halo 2

- Spawns favor positions near living teammates and away from enemies' line of sight. A team that holds one side keeps the enemy spawning on the other.
- Killing an enemy near their spawn side can push the next spawn to the bot's side (spawn flip). The bot avoids killing enemies deep in its own territory when it holds a strong setup, and instead kills them in the middle.
- Spawn trapping on Lockout: hold Sniper tower, BR tower and Library and the enemy keeps spawning at bottom mid or Elbow, where grenades land.

### H2A multiplayer differences

- No BXR or double shot; melee and reload animations cannot be cancelled.
- Sprint is off by default in H2A arena settings; the BR is a 4-burst hitscan kill like Halo 2 Classic.
- H2A has Halo 4 engine vehicle physics and boarding timings; the Warthog is tougher.
- Maps are remakes (Zenith for Midship, Lockdown for Lockout, Shrine for Sanctuary, Warlord for Warlock, Stonetown for Zanzibar, Bloodline for Coagulation, Remnant for Relic); callouts carry over.

## Halo 3

Halo 3 is slower and heavier than Halo 2: the BR has spread, melee is strong, grenades are weaker, and equipment adds one-off plays. Fights are won by team shooting, grenade-then-shoot combos and controlling the few high spots on each map.

### BR control

- The BR fires 3-round bursts; all three rounds must land for full damage. Spread opens with each burst and with movement. At Medium band the bot can burst at the natural rate (about 0.5 s apart); at Long band it waits 0.7 to 0.8 s between bursts and aims at the center of mass until the shield pops, then the head.
- Leading: BR rounds are projectiles with travel time; at Long band aim about half a body width ahead of a strafing enemy in the direction they are moving. At Medium band lead is a quarter width; at Short band none.
- Zoom (2x) narrows spread slightly and steadies aim; zoom for Medium and Long band shots, never at Short band.
- Four-shot: the fourth burst must contain a head shot; if the enemy's shield pops after three bursts, the bot aims strictly at the head for the fourth.
- Melee combo: BR burst, BR burst, melee kills a full-shield enemy at Melee band faster than four bursts. Melee first then two bursts also works.
- Against a carbine at Long band the BR loses; the bot closes to Medium or leaves the lane.

### Melee in Halo 3

- Melee is slower than Halo 2 but hits harder; two melees kill a full-shield player; one kills at half shield or less.
- Melee lunge covers about 8 ft; the bot should only melee when the enemy is within that or when the reticle is on them.
- Melee trades: simultaneous melees with equal shields usually result in both players dying (Halo 3 counts both hits). The bot avoids a melee trade when it has the shield advantage and should prefer a burst then a melee.
- Beat-down from behind is an instant kill with an assassination animation in Reach and Halo 4; in Halo 3 it is instant without an animation, so back melees are safe to attempt.

### Grenades in Halo 3

- Frags are weaker than Halo 2: one frag strips most of a shield within 5 ft but rarely kills alone. Grenade then BR burst is a kill; grenade then melee is a kill.
- Grenade jumping is weaker but still works on The Pit (onto the sword room roof edges), Guardian and Narrows for Pro bots.
- Spike grenades stick to anything and spray; on Guardian and Construct corridors a spike grenade thrown at the wall next to an enemy is a kill.
- Firebombs burn for about 5 s; throw one on a doorway or lift landing to deny it; do not throw at a moving target.
- Plasma grenades are the best anti-vehicle tool at Short band and the best anti-camper tool: stick a crouched enemy's cover and the splash hits them.

### Equipment plays

- Bubble shield: drop it in a doorway to block a lane for 20 s; drop it on the flag carrier mid-run; drop it to force a sniper to relocate. Walk out of the shield to shoot, never shoot from inside (shots do not pass through).
- Power drain: throw it into a room before entering; everyone inside loses shields in 2 s. Throw it at a Warthog to stall it. It bounces, so aim at the floor.
- Regenerator: drop at the bot's feet during a Melee-band fight it is winning; the regenerator refills faster than the enemy can damage. Enemies inside also heal, so it is a bad play in a losing fight.
- Trip mine: place on the flag's return route or on a vehicle choke; place it around a corner the enemy must round; it beeps for about 3 s before arming and lasts until triggered.
- Deployable cover: drop it to block a sniper lane across an open room; shoot through gaps around it.
- Radar jammer: throw before a push; enemies see dots everywhere for a few seconds.
- Flare: throw at a sniper's perch or into a room before pushing; the blinded enemy cannot aim for about 3 s.
- Gravity lift: drop at a wall to reach a roof (The Pit's sword room roof, Guardian's top mid from Blue room); drop it under an enemy to launch them into the air for a free shot.

### Movement in Halo 3

- Crouch-jumping extends every jump: jump and crouch at the apex to clear ledges on The Pit (the walls between courtyards), Guardian (top mid rails) and Construct.
- Crouch-walking removes the bot from enemy radar; use it to approach a known camper or to hide while shields recharge.
- Man cannons and lifts throw the bot in a fixed arc; shoot enemies in the air (they cannot strafe) and never ride one into a lane an enemy is watching.
- Jumping mid-fight is a liability: airborne players cannot change direction and get head shot. Only jump to break a strafe pattern once per fight or to reach cover.

### Spawn system in Halo 3

- Spawns are weighted by teammate proximity (positive) and enemy proximity and line of sight (negative). A team that holds a position keeps spawning near it.
- Spawn trapping: on The Pit, holding Sword room and both sniper towers keeps enemies spawning in the open yard; on Guardian, holding Top mid, Gold and Blue room keeps enemies spawning at bottom.
- The bot can predict where a dead enemy spawns: near their living teammates and away from the bot's team. After a kill, it pre-aims the likely spawn lane rather than the kill spot.

### Standard team setups (4v4)

- The Pit (Slayer): one sniper on the home sniper tower, one BR at Sword room, one BR at the home shotgun hall side, one roamer who rotates between rockets and the enemy's needle hall. Rockets are rushed at the start with grenades thrown first.
- Guardian (Slayer): two BRs at Top mid and Gold lift top, one at Blue room, one at Snipe 1 or Elbow. Nobody goes bottom alone; the hammer is grabbed and brought back up.
- Construct (Slayer): three on Top (sniper tower, Gold lift top, Purple lift top), one who takes the sword at bottom and returns. The laser is used from top onto Street.
- Narrows (CTF): one sniper on the home base top, one at Top mid, two who rotate rockets and the flag run via Bottom mid. The man cannons are only used to chase a flag runner.

### Weapon-specific Halo 3 tricks

- Mauler: one shot then melee is a kill; dual maulers kill in one shot each at Melee band. Mauler plus BR is the best Guardian loadout.
- Sniper: 4-round magazine, two zoom levels; a body shot then a BR burst to the head is a kill; a no-scope at Short band is viable with the bot facing the enemy.
- Laser: the charge takes about 2.5 s with a visible red glow; a Pro bot pre-charges behind cover and steps out for the last half second. Five shots per laser.
- Rockets: slow projectiles with no lock-on; aim at the ground where the enemy will be in 0.3 s. On Valhalla aim at the Warthog's front wheels.
- Brute shot: six grenades that bounce enemies; its melee is one of the strongest in the game (a full-shield kill with one melee from behind, two from the front).
- Flamethrower: slows the user; only for holding a doorway in Infection or custom games.
- Hammer: the swing has a short delay; swing early. Hammer at a Melee-band enemy who jumps still kills because of the ground splash.

## Halo: Reach

Reach adds bloom, loadout armor abilities, bleed-through and a health bar. The bot's edge comes from pacing precision shots, choosing the ability that matches its role, and punishing enemies who misuse sprint, armor lock and jetpack.

### Bloom and precision pacing

- DMR: the reticle grows with each shot and shrinks over about 0.4 s. Five paced shots (one every 0.5 s) at Medium band land; five spammed shots at Long band miss two or three. The bot's pacing rule: fire when the reticle is at or below half bloom.
- At Short band bloom hardly matters; the bot spams the trigger and the last shot still lands.
- Needle rifle: less bloom, faster fire; 7 shots to kill with a head shot, or the needles supercombine on an unshielded enemy after 3. The bot uses the needle rifle when it expects Long band fights or when fighting a jetpacker.
- Magnum: 5-shot kill, tight bloom at Short band, large bloom beyond; a strong secondary.
- Title Update settings (zero or 85 percent bloom, no armor lock, bleed-through) exist in MCC playlists; when the variant says TU, the bot can fire faster and must respect bleed-through.

### Sprint, evade and melee

- Sprinting disables shooting and slows the stop; a sprinting enemy who arrives at Melee band needs about 0.3 s to melee. The bot facing a sprinter shoots first and melees as they arrive.
- Sprint-melee: sprint toward an enemy, release sprint just before Melee band, melee. The approach is faster than walking; against an unaware enemy it is a free assassination.
- Evade (Elites, and Spartans in some variants): two rolls that dodge grenades and swords; the roll ends in a fixed spot, so the bot shooting an evader aims where the roll ends.
- Assassinations: holding the melee button from behind plays a long animation; the bot should tap melee (instant beat-down kill) unless no enemies are near.

### Armor lock plays

- Armor lock makes the bot invulnerable for up to about 5 s, drains its own ability meter, and ends with an EMP burst that pops nearby enemies' shields and stalls vehicles.
- Use: when stuck with a plasma grenade (the grenade falls off), when a vehicle is about to splatter (the vehicle is EMP'd and the driver is often ejected), when a rocket or laser is incoming, or when an enemy melees (release early to catch them with the EMP and melee back).
- Abuse that gets the bot killed: locking at full shield in the open. The enemy walks to Medium band, reloads, and head shots the bot the instant the lock ends.
- Counter: when an enemy locks, the bot backs to Medium band, reloads, throws a plasma grenade to land beside them (it will not stick but the splash hits when the lock ends), and aims at the head. Never melee a locked player.

### Jetpack lines

- Jetpack gives about 2 s of thrust; the bot pulses it in short bursts to stay low and behind cover, not a long float across the map.
- Strong lines: Sword Base's lift shaft and the jump from the catwalk to Top mid; Countdown's lift room ceiling; Reflection's lift top; Boardwalk's balcony. The scripting agent records these as jetpack waypoints.
- Jetpack flag runs: a jetpacking flag carrier cannot shoot anyway, so jetpack over walls to cut the route (Asylum's center, Zealot's top).
- Counter: shoot jetpackers in the air with the needle rifle or DMR; they cannot strafe.

### Active camo, hologram, drop shield

- Active camo: full invisibility only when crouch-walking or still; it also jams enemy radar in the area, which announces that a camo user is near. The bot with camo and a sword or shotgun sits at a corner on the enemy's route.
- Hologram: send the hologram at a sniper's lane to bait the shot, then peek while they re-scope; send one around a corner before pushing; a hologram running next to a flag carrier splits enemy fire.
- Drop shield: heals inside and blocks fire; drop it on a flag stand or hill when holding, or on a downed teammate's position. It breaks under sustained fire.

### Bleed-through and health

- Damage beyond the shield carries into health. A melee on an enemy with a quarter shield kills through the shield. A bot with low health but full shield dies to one grenade plus one shot.
- Health packs exist on most maps; the bot routes to one after any fight that cost health, as in CE.

### Grenades in Reach

- Frags are weaker than Halo 3 and only two are carried; the bot uses them to finish or to flush, not to open fights.
- Plasma grenades stick and kill; they also stick to armor-locked players' surroundings and to vehicles. The stick animation gives the enemy no time to lock if the grenade lands first.

### Vehicles in Reach

- Vehicles are tougher and the Warthog's turret has a slower ramp-up; rockets lock onto air vehicles only. The plasma launcher and laser are the real counters.
- Boarding takes longer than Halo 3; the bot being boarded can shake the boarder by driving fast or using armor lock.

### Team setups (4v4, MLG settings)

- Countdown (Slayer): two DMRs on Top mid and the home lift, one on the sniper ledge, one roamer who times the sword and the shotgun.
- Zealot (Slayer): three on the top ring (the two team rooms and Top mid), one who times the sword and grenade launcher at the bottom; nobody goes to the space deck in objective games.
- Sanctuary/Asylum (CTF): sniper on the home Snipe, DMR on Ring 1, DMR on Rocks, runner who times rockets and the flag pull through the back of the enemy base.
- Reflection (Slayer): two on the top walkway, one at the balcony sniper, one who takes the sword at the lift room and holds the bottom corner.

## Halo 4

Halo 4 is the fastest-moving MCC title: universal sprint, instant respawn in some variants, loadouts, ordnance and strong automatics. The bot's edge comes from sprint discipline, ability timing, ordnance choices and the four-weapon precision sandbox.

### Sprint discipline

- Sprint is unlimited only with the Mobility perk; without it the bot sprints for about 4 s and then recovers. Sprinting shrinks the bot's field of view and delays the first shot by about 0.4 s after stopping.
- Rule: never sprint into a room or around a corner where an enemy might be; stop sprinting 10 ft before the corner and walk the last part with the weapon up. Sprint only along routes the team knows are clear or to escape a lost fight.
- Sprint-melee: sprinting does not add melee damage in Halo 4; it only closes distance faster. Release sprint about 10 ft out so the melee is ready on arrival.
- Flinch: Halo 4 has no de-scope on damage; instead the bot's reticle flinches upward when hit while scoped. A scoped bot that gets hit should aim slightly lower on the next shot.

### Thruster, Promethean Vision and the other abilities

- Thruster pack: a short dash of about 10 ft with a recharge of about 8 s. Use it the instant the shield pops to get behind cover, to dodge a sword lunge, to cross a doorway under fire, or to break a melee trade by dashing sideways.
- Promethean Vision: pulse for about 2 s, revealing enemies through walls within Medium band; a second pulse is available after a short cooldown. Pulse before every corner, lift ride or room push; then pre-fire the wall edge the enemy will appear from.
- Hardlight shield: blocks frontal damage but stops the bot shooting; use it to cross an open lane with a flag or to absorb a rocket; drop it instantly when the enemy flanks.
- Hologram: as in Reach; good against snipers and binary rifles.
- Jet pack: shorter than Reach; use for Ragnarok and Exile high ground only.
- Autosentry: place covering a doorway or flag; it has little health but distracts enemies and does chip damage.
- Regeneration field: drop on the objective; it also heals enemies who step in.
- Active camo: crouch-walking invisibility with a radar jam; pair with a scattershot or sword.

### Loadouts and perks

- Primaries: BR (5-burst, most forgiving), DMR (5-shot, best at Long band), Carbine (8-shot, fastest at Short band), Light Rifle (4-shot scoped, 5 unscoped, best in scope duels). A balanced bot team carries two BRs, one DMR and one Carbine or Light Rifle.
- Secondaries: Magnum (6-shot kill), Plasma Pistol (vehicle EMP and the shield-strip combo), Boltshot (one-hit charge at Melee band).
- Tactical packages: Mobility (infinite sprint, for rushers and runners), Shielding (faster recharge, for anchors), Resupply (grenades from the dead, for grenade-heavy styles), AA Efficiency (faster ability recharge, for thruster or vision users), Firepower (two primaries).
- Support upgrades: Dexterity (fast reload), Ammo (more reserve), Awareness (radar while scoped), Sensor (longer radar), Explosives (bigger blasts and less damage taken).
- Specializations in MCC are unlocked by default; Stability (less flinch) and Wetwork (quiet sprint, no assassination sound) are the two that change bot behavior.

### Ordnance

- Personal ordnance triggers after a point threshold (kills and assists); the bot chooses among three options. Decision order: power weapon the team lacks, overshield if the bot's role is to push an objective, damage boost if a fight is coming in the next 20 s, speed boost for flag runs.
- The drop lands next to the bot with a loud sound and visible pod; call it in behind cover so the enemy does not get a free kill and a free weapon.
- Map ordnance drops are announced and marked; they land on fixed spots per map (Haven's Top mid, Adrift's center). The bot treats each as a timed objective and contests with two.

### Weapons and grenades in Halo 4

- Frags are weak; pulse grenades drain shields in a sphere for a few seconds and are the best objective-denial tool; plasma grenades stick as always.
- Sticky detonator: fire the sticky onto a flag stand or a doorway floor and detonate when an enemy walks over it; it also one-shots a Ghost when stuck.
- Railgun: about 1 s charge; charge while behind cover, step out and release. Kills a full-shield player with one hit and heavily damages the Mantis.
- Binary rifle: a red laser beam from the scope shows the bot's position; scope only for the shot.
- Scattershot: the pellets bounce off walls, so firing at a wall next to a corner hits an enemy around it.
- SAW: the best Short-band weapon; a full-shield kill in about 0.8 s. It has a long reload, so the bot reloads between fights.

### Flag mechanics in Halo 4

- The flag is picked up automatically when the bot walks over it, and it cannot be dropped in default settings; the carrier gets a magnum. The bot must path around a dropped flag when it does not want it, and should treat the magnum as a real weapon (6-shot kill).
- The carrier is marked on the enemy HUD; running through open lanes is suicide; use the covered route and escorts.

### Movement

- Crouch-jumping works; many ledges on Haven, Adrift and Abandon need it.
- Instant respawn (in variants that allow it) means a killed enemy is back within 2 to 3 s; after a kill the bot should move, not hold the kill spot.
- De-scope: Halo 4 does not de-scope on hit; the bot scoped at Long band keeps the scope and compensates for flinch.

## Cross-game movement and aiming techniques

### Strafe patterns

- Basic: alternate left and right strafes with irregular timing (0.3 to 0.8 s). The enemy's aim lags each direction change.
- Reversal strafe: start a long strafe one way, then snap back the instant the enemy's reticle catches up (usually when the bot takes a hit). Used by Veteran and above.
- Crouch strafe: tap crouch mid-strafe to drop the head below the enemy's head-level aim. Best against snipers and BR users at Medium band. Not in CE (crouch is slow and shows on radar).
- Backpedal strafe against CQB weapons: strafe while moving backward to stay out of the one-shot range.
- Circle strafe: moving in a circle around an enemy is predictable and bad against precision weapons; use only against a sword or hammer user to keep behind their swing.
- Jump strafe: jumping breaks a strafe once; a bot in the air is an easy head shot, so at most one jump per fight.

### Peek types

- Shoulder peek: step out only far enough to expose the gun and head, fire, step back. Used from cover edges.
- Jump peek: jump up behind a waist-high wall to see over it for one shot; the enemy cannot predict the moment.
- Crouch peek: peek from behind low cover by standing briefly; drop as soon as a shot is taken.
- Wide peek (swing): step fully out at an angle so the enemy who is pre-aiming the near edge is off target; used when the bot knows the enemy is waiting.
- Pre-fire: start shooting at head height before the enemy is visible when the bot knows they are coming around the corner.

### Pre-aim heights

- Default aim height while moving is head height of a standing Spartan at Medium band; the reticle drifts down to chest for Long band (easier to land the first shots) and back up once the shield pops.
- On ramps aim at the head of a player on the ramp (above or below the bot); on lifts aim at the top of the lift exit.
- Crouched enemies hide heads behind rails; aim at the rail's top edge.

### De-scoping

- In CE, Halo 2, Halo 3 and Reach, a hit knocks the enemy out of scope. The bot facing a sniper or scoped BR at Long band fires one shot early to de-scope, then strafes; the sniper needs about 0.5 s to re-scope.
- The bot's own sniper should expect to be de-scoped; after a de-scope it moves rather than re-scoping in the same spot.
- Halo 4 has flinch instead; see the Halo 4 section.

### Radar play

- Crouch-walking is invisible on radar in Halo 2 onward; the bot crouch-walks the last 20 ft to any corner it intends to hold.
- A radar dot that appears and vanishes is an enemy who crouched; assume they are at the last bearing and holding a corner.
- Radar elevation: Reach and Halo 4 show up and down arrows; the bot checks elevation before choosing a lane.
- In no-radar settings (MLG, HCS) the bot relies on sound: footsteps at Short band, reloads, grenade pin, sprint breathing (Reach, Halo 4).

### Jump timing and ledges

- Crouch-jump: jump, crouch at the apex, release when the feet clear the ledge; adds about one foot of reach.
- Edge jumps: jump from the very edge of a platform, not a step early; most map shortcuts need the full distance.
- Grenade jumps: full shield only, no enemy within Medium band; jump as the grenade explodes.
- Ladder and lift exits: stop before the exit, check radar, exit crouched and sidestep.

### Reload and weapon switch timing

- Reload behind cover; switch weapons rather than reload when an enemy appears mid-reload.
- Reload cancel: in Halo 2 the YY switch cancels the reload after the magazine is inserted; in Halo 3 onward a switch cancels the reload entirely (no ammo gained), so the bot must finish the reload later.
- Switch time is about 0.5 to 1 s depending on the weapon; a sword or hammer switch is slow, so the bot with a sword keeps the BR out until the enemy is within lunge range plus a few feet.

### Sound discipline

- Picking up weapons, reloading and sprinting make noise; the bot holding an ambush does none of them.
- Grenade throws are loud; a bot that throws reveals its position, so it throws then moves.
- Vehicles and turrets are heard across the map; a bot that hears an engine assumes a vehicle is coming to its lane within 10 s.
