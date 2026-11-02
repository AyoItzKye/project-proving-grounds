# Weapon deep dives

Mechanics and tricks for every weapon class, game by game, beyond the band table in the main tab.

## Precision weapons in depth

The utility weapon is the bot's identity in every game. The table gives the per-game numbers; the notes under it give the technique.

| Weapon | Game | Kill (last shot head) | Body-only kill | Magazine | Zoom | Fire type | Range behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pistol M6D | CE | 3 | 5 | 12 | 2x | Semi, fast | Hitscan, strong magnetism, no drop |
| Battle Rifle | H2 | 4 bursts | 6 to 7 bursts | 36 (12 bursts) | 2x | 3-round burst, hitscan | No spread; works at Long |
| Battle Rifle | H2A | 4 bursts | 6 to 7 bursts | 36 | 2x | 3-round burst, hitscan | Tuned like H2 |
| Carbine | H2 | 7 | 10 | 18 | 2x | Semi, fast | Projectile, slight travel time |
| Magnum | H2 | 6 (dual: 3 each) | 8 | 12 | none | Semi | Short to Medium only |
| Battle Rifle | H3 | 4 bursts | 7 bursts | 36 | 2x | 3-round burst, projectile | Spread grows at Long |
| Carbine | H3 | 7 | 10 | 18 | 2x | Semi, fast | Projectile; better than BR at Long |
| Magnum | H3 | 8 (dual 4 each) | 11 | 8 | none | Semi | Short only |
| DMR | Reach | 5 | 8 | 15 | 3x | Semi, bloom | Pace at Long |
| Needle Rifle | Reach | 7 (3 supercombine unshielded) | 10 | 21 | 3x | Semi, low bloom | Projectile needles |
| Magnum | Reach | 5 | 8 | 8 | 2x | Semi, bloom | Short to Medium |
| Battle Rifle | H4 | 5 bursts | 7 bursts | 36 | 2x | 3-round burst, hitscan | Mild spread |
| DMR | H4 | 5 | 8 | 14 | 3x | Semi | Best at Long |
| Carbine | H4 | 8 | 11 | 18 | 2x | Semi, fastest | Short to Medium |
| Light Rifle | H4 | 4 scoped, 5 unscoped | 6 | 36 (12 bursts) | 3x | 3-round burst unscoped, single slug scoped | Scoped shots hit harder |
| Magnum | H4 | 6 | 8 | 8 | 2x | Semi | Short to Medium |

### Pistol (CE)

- Cadence: three trigger pulls in about 0.6 s is the natural rate; faster pulls widen the error cone. The bot fires at that rate and lands the three.
- Target selection: aim the first two at the chest (easier hits, each strips about a third of shield), the third at the head once the shield flickers. If the enemy crouches, the head drops a foot; track down.
- Zoom when the enemy is beyond 40 ft and not strafing fast; otherwise hip-fire with the magnetism doing the work.
- Reload is 1.7 s; the bot reloads after every kill, never with an enemy in view.

### Battle Rifle (H2, H2A, H3, H4)

- Burst spacing: H2 and H4 are hitscan, so burst as fast as the trigger allows at Short and Medium band. H3 is projectile with spread: 0.5 s between bursts at Medium, 0.7 to 0.8 s at Long, aiming center mass until the shield pops.
- The four-shot (five in H4): the bot tracks the enemy's shield; after three bursts in H2/H3 the next burst must hit the head. If the enemy reaches Melee band at three bursts, melee instead of the fourth burst.
- Melee combos: two bursts then melee (H2/H3) is a full-shield kill; melee then two bursts also works. In H4 it is two bursts then melee as well because melee damage is high.
- Zoom: 2x steadies the aim; de-scope risk in H2/H3/Reach means the bot unzooms if it takes a hit and re-zooms only behind cover.
- Lead (H3 only): a quarter body width at Medium, half at Long, in the strafe direction. Reverse-strafe enemies are a guess; aim center and wait for the direction change.
- Double shot and BXR (H2 Classic): see the Advanced techniques tab; they turn the BR into a two-input kill at Short band.
- Ammo: 36 rounds is 12 bursts, three full kills if perfect. The bot reloads at or below 9 rounds with no enemy in view.

### Carbine (H2, H3, H4)

- Fast semi-auto; the bot can fire as fast as it can aim. At Long band the carbine beats the H3 BR because each shot is a single projectile with no spread.
- Seven shots to kill (eight in H4) means the bot fires in a steady stream of about 5 shots per second at Medium; at Long it paces to about 3 per second to keep the head in the reticle.
- Magazine of 18 is two and a half kills; reload early.
- The carbine's projectile has slight travel time; at Long band aim a hair ahead.

### DMR and Needle Rifle (Reach)

- DMR bloom resets in about 0.4 s; the bot fires when the reticle is at half bloom or tighter. At Short band spam; at Medium pace at 0.4 s; at Long 0.5 s with a crouch to steady.
- Needle rifle: 7 shots or 3 needles into an unshielded enemy; the bot switches to a needle rifle when the team already has DMRs, when fighting jetpackers, or on maps with Long lanes (Sword Base, Countdown).
- Magnum: the strongest Short-band precision option in Reach; a bot with a shotgun as primary keeps the magnum as secondary.
- Reach TU settings reduce bloom to 85 percent or zero; the bot reads the variant and increases its fire rate accordingly.

### Light Rifle (H4)

- Scoped: a single high-damage slug, 4 shots to kill; unscoped: a 3-round burst, 5 bursts to kill. The bot scopes for every Medium and Long band fight, unscopes only at Short band.
- Flinch while scoped pushes the aim up; the bot compensates by aiming slightly low after taking a hit.

### Magnum (all games)

- CE: the primary weapon (above). H2/H3: a dual-wield weapon that is weak alone; dual magnums land head shots fast at Short band. Reach: a strong secondary, 5-shot kill. H4: the loadout secondary, 6-shot kill, and the flag carrier's only weapon.

### Head-shot timing rule for every precision weapon

1. Count hits landed; the bot knows how many it takes to pop the shield for its weapon (2 pistol, 3 BR bursts, 4 DMR, 6 carbine, 4 H4 BR bursts).
2. Until that count, aim center of mass (the biggest target); after it, aim the head.
3. If the enemy's shield visibly pops early (team shot, grenade), switch to the head immediately.
4. If the enemy drops out of sight at one shot from death, pre-aim the head at the edge they will re-peek from.

## Automatics and dual-wield in depth

Automatics win Short band when paired with a melee and lose everything else. The bot's job with an automatic is to decide, in the first half second of a fight, whether it is at Short band (fight) or not (leave).

| Weapon | Game | Magazine | Time to kill at Short band (approximate) | Pairs with | Drop it when |
| --- | --- | --- | --- | --- | --- |
| Assault Rifle | CE | 60 | 1.5 s body, faster with melee | Pistol | A pistol or plasma rifle is on the ground |
| Assault Rifle | H3 | 32 | 1.4 s, 0.8 s with melee | BR | A BR is available |
| Assault Rifle | Reach | 32 | 1.3 s | DMR, magnum | A DMR is available |
| Assault Rifle | H4 | 32 | 1.1 s | BR or DMR | Rarely; it is strong at Short |
| SMG | H2 | 60 | 1.2 s single, 0.6 s dual | Plasma rifle (dual) | An enemy is beyond Short |
| SMG | H3 | 60 | 1.4 s single, 0.8 s dual | Dual or BR | Same |
| Plasma Rifle | CE | 100 battery | 1.2 s, stuns | Pistol finish | Battery under 20 percent |
| Plasma Rifle | H2, H3 | battery | 1.0 s, dual 0.6 s; overheats after \~3 s | SMG or magnum (dual) | Overheated mid-fight with no cover |
| Brute Plasma Rifle | H2 | battery | 0.9 s, overheats faster | SMG | Same |
| Spiker | H3 | 40 | 1.2 s, dual 0.7 s; strong melee | Dual spiker or mauler | Enemy beyond Short |
| Plasma Repeater | Reach | battery | 1.3 s; vent to cool | DMR | Enemy beyond Short |
| Storm Rifle | H4 | battery | 1.0 s; overheats | BR finish | Overheated |
| Suppressor | H4 | 48 | 1.1 s at Melee band, 1.6 s at Short | Light rifle | Enemy beyond Short |
| SAW | H4 | 72 | 0.8 s | Any | Never while it has ammo; it is a power weapon |

### Assault rifle technique

- Aim at the chest and let the spread cover the head; at Short band most rounds land. Beyond 40 ft, the spread wastes half the magazine.
- The real kill is AR then melee: about half a magazine (CE: about 25 rounds; H3: about 14; Reach and H4: about 12) strips the shield, then one melee kills. The bot starts the fight firing and closes to Melee band as the shield drops.
- Burst fire at the top of Short band (30 to 40 ft) in H3 and Reach: three to five rounds at a time keeps the spread tight.
- H4's AR is strong enough to win Short-band duels against a BR; the bot with an AR in H4 pushes rooms where the BR cannot keep distance.

### SMG and dual wield technique

- Single SMG: aim low (belt line) and let recoil walk up; fire the full magazine while closing; melee to finish.
- Dual SMGs: fire both; aim low; the kill takes about 0.6 s at Melee band. The bot cannot melee, throw or zoom; it drops the second SMG the moment the enemy leaves Short band or a grenade is needed.
- Plasma rifle plus SMG: plasma first (it stuns and strips), SMG does the rest. If the plasma overheats, the SMG alone finishes an unshielded enemy.
- Dual plasma rifles: the fastest shield strip at Short band; fire in one second bursts; follow with melee.
- Dual needlers: strong against enemies in the open at Short to Medium; the supercombine splash damages nearby enemies, so fire at the middle of a group.
- Dual magnums (H2, H3): head-shot capable; strong at Short and close Medium.
- Dropping etiquette: drop the weaker weapon (usually the magnum or the SMG) and keep the plasma or needler as a single weapon so grenades and melee return.

### Plasma automatic technique

- Plasma weapons strip shields faster than kinetic weapons and do less to health; the rule is plasma to strip, kinetic to finish. A bot with a plasma rifle and a BR fires plasma until the enemy's shield pops, then switches (0.5 s) and head shots.
- Overheat: the weapon locks for about a second after overheating; the bot fires in bursts of under 2 s. Plasma repeater (Reach) vents on command; vent behind cover.
- Stun (CE, H2): sustained plasma fire slows the enemy's movement and turn speed; a stunned enemy cannot strafe out of pistol or BR fire.

### Spiker and Suppressor

- Spiker rounds drop over distance; fire at the chest at Short band, aim higher at the top of Short band. Its melee is a blade with high damage; spiker plus melee is a fast kill.
- Suppressor has huge spread; only fire within 20 ft. Pair with a light rifle for Medium band.

### SAW (H4)

- The SAW kills a full-shield player in about 0.8 s, faster than any loadout weapon; it is a power weapon the team should route to the Rusher style.
- 72 rounds is about three kills; the reload is 3.5 s, so reload behind cover after every kill.
- The SAW loses at Long band; the bot with a SAW pushes rooms and corners.

## Close-quarters power weapons in depth

| Weapon | Game | One-shot range | Two-shot range | Magazine / energy | Swing or pump time | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Shotgun | CE | \~10 ft | \~20 ft | 12 | 0.8 s pump | Pump can be cancelled with a weapon switch |
| Shotgun | H2 | \~12 ft | \~20 ft | 12 | 0.9 s | Strongest shotgun vs. sword |
| Shotgun | H3 | \~10 ft | \~18 ft | 6 | 0.9 s | Lower ammo |
| Shotgun | Reach | \~10 ft | \~18 ft | 6 | 0.9 s | Sprint users close fast |
| Shotgun | H4 | \~10 ft | \~18 ft | 6 | 0.9 s | Thruster users dodge |
| Mauler | H3 | \~8 ft (dual) | one shot plus melee (single) | 5 | 0.6 s | Mauler plus BR is a loadout |
| Scattershot | H4 | \~12 ft | \~20 ft | 5 | 0.7 s | Pellets ricochet off walls |
| Energy Sword | H2 | lunge \~22 ft | n/a | unlimited (H2), 10 lunges (H3, Reach, H4) | 0.5 s swing | Lunge when reticle is red |
| Gravity Hammer | H3, Reach, H4 | \~8 ft radius | n/a | limited energy | 0.7 s swing | Deflects projectiles, flips vehicles |

### Shotgun

- Positioning: the shotgun holder owns a corner, a lift top, a teleporter exit or a doorway. It never crosses open ground longer than 20 ft while enemies are alive.
- Shot discipline: hold fire until the enemy is within one-shot range; a two-shot at 20 ft gives the enemy time to melee or run. At 15 ft, fire then melee (a melee after one shotgun hit is a kill).
- Against a sword: the shotgun wins when the sword user must come around a corner into Melee band. It loses when the sword user sees the bot at 20 ft and lunges. The bot stays out of sight until the sword is at the corner.
- Pump cancel (CE): switch weapons and back after firing to skip the pump animation; the second shot comes a quarter second sooner.
- Reach and H4: sprinters close distance fast but cannot shoot while sprinting; the shotgun bot fires as they arrive at Melee band. Thruster users dash past the shot; aim where the dash ends.
- Ammo: six rounds in H3 onward is three to six kills; reload after every kill.

### Mauler (H3)

- Single mauler: one shot (within 8 ft) then melee kills a full-shield player. Mauler plus BR is the best Guardian and Pit loadout because the mauler handles Blue room and the BR handles Top mid.
- Dual maulers: one shot each at Melee band kills; no melee or grenades while dual.
- The mauler's spread is wide; past 12 ft it does little. Treat it as a melee-range weapon with a half second of reach.

### Scattershot (H4)

- Pellets bounce off hard surfaces; firing at a wall beside a doorway hits an enemy standing around the corner. Firing down a hallway at the floor bounces pellets into a crouching enemy.
- Kills disintegrate the body (no weapon drop for the enemy to pick up quickly).
- Pair with thruster: dash into Melee band and fire.

### Energy Sword

- Red reticle rule: the lunge connects whenever the reticle is red; the bot never presses the attack without red unless the enemy is within 5 ft.
- H2: unlimited energy and a long lunge; the sword is the best power weapon on Midship and Lockout. Sword flying and sword cancels (Advanced techniques tab) extend its reach.
- H3: ten lunges of energy; the lunge is shorter (about 15 ft); the sword loses to a BR at Medium more often. H3 sword clash: both players bounce back; the bot does not re-lunge until the enemy swings.
- Reach: a sword user who hits an armor-locked enemy is stunned and dies to the counter; the bot never lunges at an enemy who is about to lock (shield glowing). Sprint plus sword closes a Medium band gap in 2 s.
- H4: the hardlight shield blocks a lunge; thruster dodges it. The sword bot waits for the shield to drop or thrusts around it.
- Counter-sword: a bot without a sword keeps 25 ft away, throws a grenade at the sword user's feet, and shoots the head during the approach. A shotgun or hammer at a corner wins.

### Gravity Hammer

- The swing has a short wind-up; the bot starts the swing when the enemy is at 10 ft so the impact lands at 8 ft. Swing at the ground; the splash catches jumpers.
- The hammer deflects rockets, grenades and even a Warthog; a bot with a hammer facing a charging vehicle swings as it arrives and flips it.
- The hammer bounces enemies off ledges on Guardian and Construct; a swing at an enemy near an edge is a kill by fall.
- Energy is limited (about 10 swings in H3); the bot does not swing at air.
- Hammer versus sword: the hammer's area beats the sword's lunge if timed; the hammer bot swings as the lunge starts.

## Snipers in depth

| Weapon | Games | Head shot | Body shots to kill | Magazine | Zoom | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Sniper Rifle | All | 1 at any shield | 2 | 4 | 2x/8x (CE), 5x/10x (others) | Hitscan; de-scopes on hit except H4 |
| Beam Rifle | H2, H3, H4 | 1 | 2 | battery, overheats after 2 fast shots | 5x/10x | No reload; vent behind cover |
| Binary Rifle | H4 | 1 | 1 | 2 | 5x/10x | Red targeting beam visible to enemies |
| Focus Rifle | Reach | continuous beam | \~3 s of beam | battery | 3.5x/9.5x | Overheats; beam reveals position |

### Lane selection

- A sniper lane needs: a sightline of Long band or more, a head-height edge to duck behind, an exit within 10 ft, and a second lane reachable within 5 s. Perches with one exit (Lockout S3 top, Guardian Snipe 3) are used for two shots then abandoned.
- Sniper versus the map's traffic: the bot picks the lane that crosses the enemy's route to the next power weapon or objective, not the longest lane.
- Never snipe from the same window twice in a row against Veteran or better enemies; they pre-aim the window.

### Scoping

- Scope in only when the target is within the reticle's rough area; scoping early narrows the view and lets a flanker approach.
- First zoom level for Medium and Long band; second for Extreme band only.
- De-scope (CE through Reach): any hit knocks the bot out of scope. The bot's counter: unzoom, strafe behind cover, re-zoom. Against a BR user at Long band, the sniper takes the shot first or not at all.
- H4: flinch instead; the reticle jumps up on hit, so re-aim lower.

### Shot technique

- Strafing targets: wait for the strafe reversal (the enemy slows for a frame) and fire then; or aim at the center of the strafe arc and fire when the head crosses.
- Lead: the sniper rifle is hitscan in every game; no lead. The beam rifle and binary rifle are also hitscan. The focus rifle is a continuous beam.
- Body shot plus BR: a sniper body shot pops the shield; one BR burst or pistol shot to the head finishes. In H2/H3 this is faster than a second sniper shot.
- No-scope: at Short band the bot hip fires with the reticle on the chest; magnetism helps in CE and H2. One no-scope body shot then melee is a kill.
- Quick-scope: scope and fire within 0.2 s at Medium band; used by Veteran and above against a single enemy who appears suddenly.
- Double shot (H2 Classic): fire, fire, reload cancel for two sniper rounds in a row; see Advanced techniques.

### Relocation rules

- After every kill from a perch, move at least 20 ft or change windows; after two kills, change structures.
- When radar shows a dot approaching the perch, swap to the secondary and face the entrance; do not keep scoping.
- If an enemy sniper counter-snipes the lane, the bot leaves the lane entirely for 10 s and re-enters from a different window; a sniper duel in the same lane is a coin flip the bot should not take unless its shield is full and the enemy's is not.

### Beam rifle

- Two fast shots overheat it; the bot fires one, waits about 1.5 s, fires again, unless the first missed and the second is sure.
- No reload animation makes it better at Medium band than the sniper; one body shot then a BR burst is a fast combo.

### Binary rifle (H4)

- Any body hit kills; two rounds per magazine, a long reload. The bot takes shots only when sure, because the red beam shows every enemy where it is.
- Scope in behind cover, step out, fire, step back; never track a target with the beam on for more than a second.

### Focus rifle (Reach)

- Hold the beam on the target for about 3 s to kill; it overheats after about 5 s. Strong against jetpackers and armor-locked enemies (it damages the moment the lock ends).
- The beam is visible; after a kill the bot moves.

### Counter-sniping as a non-sniper

- Approach the perch from its blind side (behind, or the exit). Grenade the perch before peeking. A plasma grenade stuck on the perch's cover kills a crouched sniper.
- Bait: a hologram or a teammate's peek draws the shot; the bot pushes during the re-scope.
- A BR at Long band cannot beat a sniper, but it can de-scope them; one burst then full strafe behind cover.

## Explosives and anti-vehicle weapons in depth

| Weapon | Games | Rounds | Direct hit | Splash kill radius (approx.) | Vehicle effect | Travel |
| --- | --- | --- | --- | --- | --- | --- |
| Rocket Launcher | All | 2 per magazine | Kill | \~8 ft kill, \~15 ft shield strip | Kills Ghost, Mongoose, Warthog in 1 to 2; Scorpion 2 to 3 | Projectile; H2/Reach/H4 lock on vehicles (Reach: air only) |
| Spartan Laser | H3, Reach, H4 | 5 per battery | Kill | None (beam) | One-shots any vehicle | Hitscan after \~2.5 s charge |
| Fuel Rod Gun | CE (PC), H2 (campaign), H3, Reach, H4 | 5 | Kill | \~8 ft | Heavy damage | Arcing projectile |
| Plasma Launcher | Reach | 4 charged | Kill | \~6 ft | Homing sticks; kills light vehicles | Slow homing |
| Grenade Launcher | Reach | 1 | Kill | \~6 ft | EMP stalls vehicles | Arcing; remote detonate while trigger held |
| Railgun | H4 | 1 per charge, 4 reserve | Kill | \~4 ft | Heavy damage; two shots kill a Mantis shield | Hitscan after \~1 s charge |
| Incineration Cannon | H4 | 1 | Kill | \~10 ft, then sub-munitions | Heavy damage | Projectile with sub-bursts |
| Brute Shot | H2, H3 | 4 (H2), 6 (H3) | Heavy | \~5 ft, bounces targets | Flips light vehicles | Arcing |
| Concussion Rifle | Reach, H4 | 6 | Heavy | \~6 ft, knockback | Flips light vehicles | Arcing |
| Sticky Detonator | H4 | 1 | Kill | \~6 ft on detonation | Kills Ghost, Mongoose when stuck | Sticky projectile, manual detonate |
| Missile Pod | H3 | 8 | Kill | \~5 ft | Locks on vehicles | Homing missiles |

### Rocket launcher technique

- Aim at feet, not heads: a rocket at the floor beside an enemy kills; a rocket aimed at the chest can fly past a strafing target.
- Groups: fire between two enemies within 15 ft; both die or both lose shields. Against a flag carrier with escorts, the rocket goes to the carrier's feet.
- Vehicles: in H2, Reach (air) and H4, hold the reticle on the vehicle until the lock tone and fire; the rocket tracks. In CE and H3, lead: aim at where the vehicle will be when the rocket arrives (about 0.5 s of travel at Medium band). Aim at the Warthog's front wheels when it drives toward the bot.
- Self-damage: never fire within 15 ft of self; the bot with rockets at Melee band melees or swaps.
- Ammo: two in the magazine, two to four in reserve. The bot with rockets does not use them on a lone full-shield enemy unless dying; it keeps them for vehicles, groups and the flag carrier.
- Reload is slow (about 3 s); after two shots the bot switches to its secondary rather than reloading in a fight.
- Denial: a bot that cannot use rockets well still picks them up to keep them from the enemy, then drops them for a teammate of Slayer style.

### Spartan laser technique

- Charge takes about 2.5 s and shows a red glow and a rising sound the enemy can hear and see. The bot charges behind cover and exposes itself only for the final half second.
- The beam is hitscan and penetrates: it kills a vehicle and any infantry in line. Against a Warthog, aim at the driver's side; against a Banshee, wait for a level pass.
- Infantry: only when the target is stationary (a sniper scoped in, a turret user, a flag capper) and no teammate can take the kill; otherwise it wastes a battery shot and the bot's position.
- Five shots per laser; the bot counts them and swaps to the secondary when empty, carrying the laser only to deny its respawn.
- Being lasered: the bot in a vehicle that hears the charge turns behind cover or bails; on foot it breaks the sightline.

### Fuel rod and plasma launcher

- Fuel rod rounds arc; aim above the target at Long band. Strong against groups and vehicles; the Reach fuel rod one-shots players on direct hit.
- Plasma launcher (Reach): hold the trigger to charge up to four bombs; release on a vehicle and they home and stick. Against a Ghost, two bombs kill; against a Warthog, four. Against infantry, one bomb at the feet kills.

### Grenade launcher (Reach)

- Tap fire: a bouncing grenade that explodes on impact; direct hits kill. Hold fire: the round rolls and detonates when released, with an EMP that stalls vehicles and strips shields. Use the hold mode under a passing Warthog or on a flag stand.

### Railgun and incineration cannon (H4)

- Railgun: start the charge behind cover (about 1 s), step out and release; the slug kills on a body hit. Against a Mantis, two slugs drop the shield and a third kills; against a Ghost, one.
- Incineration cannon: one shot kills anything in the blast and the sub-munitions bounce around; aim at the floor in a room. Slow reload; the bot carries a precision secondary.

### Brute shot and concussion rifle

- Both bounce enemies: a shot at an enemy's feet on a ledge throws them off; a shot at a sword user stops the lunge. Fire at the ground, not the body.
- The brute shot's melee is a blade: a single melee from behind kills; two from the front. The concussion rifle has no such melee.
- Both are weak at health damage; pair with a precision weapon for the head shot.

### Sticky detonator (H4)

- Fire the sticky onto a doorway floor, a flag stand or a hill, and detonate when an enemy walks over it (the HUD shows proximity). Stuck on a vehicle, it kills light vehicles.

### Missile pod (H3)

- Mounted on Valhalla and Sandtrap; detach to carry (slow). Locks onto any vehicle; four to eight missiles per pod. Fire from the base roof at Banshees and Hornets.

## Support weapons and grenades in depth

### Plasma pistol

- Charge: hold the trigger about 1 s for an overcharged bolt; the bolt tracks slightly toward a target within Short to close Medium band and strips a full shield on hit. Holding the charge drains the battery; the bot holds it no longer than 3 s.
- The noob combo: charged bolt then one precision head shot. In H2 it kills in about 1 s total; in H3, Reach and H4 about 1.3 s. The bot swaps weapons immediately after the bolt leaves, not after it hits.
- Vehicles (H3 onward): the bolt EMPs a Warthog, Mongoose, Ghost, Chopper, Banshee, Mantis for about 3 s; the bot then boards (ground vehicles at Short band) or sticks it.
- Uncharged fire: weak; only to finish an unshielded enemy when nothing else is loaded.
- Counter: a charged plasma pistol glows and sounds; the bot that sees one at Medium band breaks line of sight or strafes hard, because the bolt tracks slowly.

### Needler

- Needles track within a cone and explode after a count (7 in CE and H2, 7 in H3, 7 in Reach, 7 to 8 in H4). The supercombine kills regardless of shield and damages enemies nearby.
- Best against enemies in the open at Short and Medium band who are strafing or sprinting; useless against cover and at Long band (needles fall off).
- Dual needlers (H2): fire both at the center of a group. H3 onward: two-handed; the magazine of 19 to 22 is about two kills.
- Counter: step behind cover, or close to Melee band and melee; needles do little to a player who breaks the line.

### Boltshot (H4)

- Semi-auto pistol mode is weak; the charged shot (hold about 1 s) is a one-hit kill at Melee band and a shield strip at Short band. The bot charges before rounding a corner it expects to be held.

### Turrets

- Mounted: unlimited ammo, high damage at Medium band, no movement. Mount only with a teammate watching the flanks, and dismount after 5 s or at the first grenade.
- Detached (H3 onward): slow movement, third-person view, strong fire; carry it to a doorway and set up. The plasma cannon has a faster rate of fire; the machine gun does more per hit.

### Grenade throw table

| Grenade | Games | Throw range (flat, approx.) | Fuse | Kill radius | Shield-strip radius | Sticks to | Special |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Frag | All | 60 to 70 ft (CE), 50 ft (H2), 45 ft (H3 onward) | 2 s after first bounce (CE, H2), \~2 s (H3+) | \~4 ft (CE), \~3 ft (H2), \~2 ft (H3+) | \~10 ft (CE), \~8 ft (H2), \~6 ft (H3+) | Nothing; bounces | Grenade jumping |
| Plasma | All | 40 to 50 ft | \~2.5 s, or on stick | Stick = kill; \~3 ft splash | \~6 ft | Players, vehicles, walls | Stick animation stalls the victim |
| Spike | H3 | 40 ft | \~1.5 s | \~3 ft | \~6 ft in a cone | Players, walls | Spikes spray in the direction it faces |
| Firebomb | H3 | 40 ft | On impact, burns \~5 s | Standing in fire \~2 s | Fire area \~8 ft | Nothing | Area denial |
| Pulse | H4 | 40 ft | Expands \~3 s, then collapses | Collapse \~3 ft | Sphere \~8 ft while active | Nothing | Drains shields and blocks the area |

### Throw technique

- Bounce throws: aim at the floor 10 ft in front of a doorway to skip the frag inside at knee height. Aim at a wall beside a corner to bank it around.
- Arc throws: aim about 30 degrees up to reach a roof or ledge 40 ft away; the bot learns one arc per map spot (the Midship over-top nade, the Lockout S2 to Bottom mid nade, the Pit rocket-tunnel nade).
- Cook: no grenade cooks in Halo; the fuse starts on the first bounce (CE, H2) or on throw (H3 onward). The bot throws to land exactly where the enemy will stand in 2 s.
- Pairs: two grenades (frag then plasma, or two frags) at the same spot kill a full-shield player; throw the second as the first lands.
- Combos: grenade then one precision shot (head) kills; grenade then melee kills; grenade onto a retreating enemy's cover kills more often than chasing.
- Sticking: aim at the chest of a strafing enemy at Short band; the plasma grenade's arc is slow, so aim where they will be in 0.5 s. Stick vehicles on the hull near the driver; stick Warthog gunners directly.
- Spike grenades: throw onto the wall next to the enemy in a corridor; the spikes spray along the wall.
- Firebombs: throw at a doorway, a lift landing or a flag stand; never at a moving target.
- Pulse grenades: throw onto a hill, a flag stand or an arming bomb; the sphere forces enemies out or strips them for the team shot.
- Resupply: pick up grenades from every dead player and every grenade spawn when safe; the bot checks its grenade count on each resupply pass.

### Grenade dodging

- A grenade's bounce sound or the thrower's arm animation is the cue; the bot moves perpendicular to the throw and out of the room if possible. Jumping over a grenade is a last resort (airborne and predictable).
- Armor lock (Reach) nullifies a stick; the hardlight shield (H4) blocks the blast; a hammer swing deflects grenades in flight.
- Against grenade spam at a doorway, the bot does not enter; it waits for the enemy to run out (two to four grenades) and pushes then.
