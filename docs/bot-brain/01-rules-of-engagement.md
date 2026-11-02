# Halo MCC PvP Bot Brain: Rules of Engagement

2026 · @Kye

## 1. How to use this guide

This is the brain for PvP bots across every Master Chief Collection title: Halo: Combat Evolved, Halo 2 (Classic and Anniversary), Halo 3, Halo 3: ODST (Firefight only), Halo: Reach and Halo 4. It is written as rules, not code. Each rule is a condition the bot can sense, followed by the behavior it should take, so a scripting agent can translate it directly into decision logic.

Sections 2 to 9 are the knowledge book (what is true about the games). Sections 10 to 13 are the bot brain (what to do about it). When a scenario in sections 11 to 12 names a weapon, map or mode, the facts behind it live in the matching knowledge section.

### Range model

All range words in this guide use one fixed scale. Halo maps measure distance in world units (WU); one WU is 10 feet (about 3 m), and a Spartan stands roughly 7 feet tall, so a player model is a handy ruler.

| Band | Feet | World units | What it feels like |
| --- | --- | --- | --- |
| Melee | 0 to 8 ft | 0 to 0.8 WU | Arm's reach; melee and sword lunge connect |
| Short | 8 to 40 ft | 0.8 to 4 WU | Across a room; shotgun, SMG, mauler, grenade bounce territory |
| Medium | 40 to 120 ft | 4 to 12 WU | Across a courtyard; rifle and precision weapon sweet spot |
| Long | 120 to 300 ft | 12 to 30 WU | Across a map; sniper, beam rifle, laser, scoped rifles only |
| Extreme | 300 ft and up | 30 WU and up | Map edge to map edge; sniper rifles and vehicle cannons only |

A scripting agent can tune the exact cutoffs per map, but every rule below assumes these five bands. If the engine exposes distance in WU, convert once and keep the band names.

### Rule format

Every scenario is written as: **Situation** (what the bot senses) → **Decision** (what it does) → **Why** (the game fact that justifies it). The Why line is there so the scripting agent can generalize to nearby cases rather than hard-coding one line per scenario.

### Confidence of the facts

Weapon ranges, time-to-kill and spawn timers come from the official games as shipped in MCC, the Halo wikis and competitive community guides linked in section 13. Where a number is a community estimate rather than a published value it is marked approximate. Spawn timers vary by playlist and custom game settings, so treat them as defaults the scripting agent should read from the game variant when possible.

## 2. Universal combat fundamentals

Every MCC title runs on the same core loop: strip the shield, then land the killing hit, while using movement, cover and grenades to make the enemy miss. A bot that understands this loop plays acceptably in any of the six games before it learns a single weapon stat.

### Shields and health

- Every Spartan has an energy shield layer over a health layer. The shield absorbs damage first, then recharges on its own after a few seconds without taking damage (about 4 to 5 seconds delay, then roughly 2 to 3 seconds to refill, varying by game).
- Halo CE, Halo 3: ODST and Halo: Reach have visible health bars under the shield that do not fully regenerate on their own (CE and Reach use health packs; Reach regenerates partially). Halo 2, Halo 3 and Halo 4 regenerate everything once the shield recharge finishes.
- A headshot from a precision weapon kills instantly once the shield is gone. The whole game of Halo gunfights is: break shield, then one headshot. That is why precision weapons (pistol, BR, DMR, carbine, light rifle, needle rifle) are the backbone of competitive play.
- Melee does massive damage: two melees kill a full-shield player in every game; one melee kills an unshielded player; a melee from behind (assassination/beatdown) is an instant kill.

### The shots-to-kill table the bot must know

These are the standard utility weapon kill counts on a full-shield, full-health enemy. The bot should track its own damage dealt so it knows when the enemy is one headshot from death.

| Game | Utility weapon | Shots to kill (last shot headshot) | Body shots only | Approx. perfect kill time |
| --- | --- | --- | --- | --- |
| Halo CE | Pistol (M6D) | 3 | 5 | 0.6 s |
| Halo 2 / H2A | Battle Rifle (3-round burst) | 4 bursts | 6 to 7 bursts | 1.4 s |
| Halo 3 | Battle Rifle | 4 bursts | 7 bursts | 1.5 s |
| Halo 3 | Carbine | 7 | 10 | 1.4 s |
| Reach | DMR | 5 | 8 | 1.6 s (approximate) |
| Reach | Needle Rifle | 7 (or 3 supercombine when unshielded) | 10 | 1.4 s |
| Reach | Magnum | 5 | 8 | 1.3 s |
| Halo 4 | BR | 5 bursts | 7 bursts | 1.6 s |
| Halo 4 | DMR | 5 | 8 | 1.6 s |
| Halo 4 | Carbine | 8 | 11 | 1.5 s |
| Halo 4 | Light Rifle (scoped) | 4 | 6 | 1.5 s |

The bot should also know that one grenade plus one melee, one grenade plus one precision headshot, or one melee plus roughly half a magazine of automatic fire are all kill combinations. These combos are faster than shooting alone and should be preferred at short range.

### Movement and strafing

- Never stand still while shooting. Strafe left and right in short, irregular bursts (change direction every 0.3 to 0.8 seconds) so the enemy's reticle has to chase. Predictable rhythm is worse than standing still against a good player.
- Crouching lowers the head and, in every game but CE, removes the bot from enemy motion trackers when moving slowly. Crouch-strafing mid-fight dodges headshots; crouching in corners hides from radar.
- Jumping mid-fight is usually bad: the bot becomes a predictable airborne target and loses strafe control. Jump only to reach cover, to dodge a rocket or grenade, or to break line of sight over an obstacle.
- Peek and retreat: fire from a corner, step back out of sight while the shield recharges, re-peek. A bot that never backs out of a losing trade feeds kills.

### Grenades

- Frag grenades bounce; plasma grenades stick to players and vehicles; spike grenades (Halo 3) stick and spray; firebombs (Halo 3) burn an area; Halo 4 pulse grenades drain shields in an area.
- Grenade damage falls off with distance: a frag landing within about 5 feet strips a full shield; a direct stick is a kill. Two grenades thrown at the same spot kill a full-shield player.
- Throw grenades where the enemy is going, not where they are: bounce frags off walls into rooms, pre-nade doorways, and throw at the likely cover spot when an enemy retreats.
- Grenades are the best answer to campers and corners. Before entering a room known to be held, throw a grenade in first.
- Pick up grenades from dead players and grenade spawns constantly; a bot with no grenades has lost a third of its damage.

### Melee

- Melee lunges forward a short distance; it connects at the Melee band and slightly beyond when lunging.
- Melee from behind, or while the enemy is crouching or distracted, is an instant kill in every title (assassination).
- The strongest short-range combo is shoot then melee: land enough shots to drop shields, then melee once. Or melee first, then one headshot.
- Melee trades: if both players melee at the same moment with equal shields, both die or both survive depending on the game. A bot should avoid melee trades when its shield is lower than the enemy's.

### Radar (motion tracker)

- The motion tracker shows moving enemies within about 25 m (Halo 3 default) in a circle at the bottom-left of the HUD. Crouched enemies and stationary enemies do not appear.
- Treat a red dot as a confirmed enemy at that bearing. If a dot disappears without a kill, assume the enemy crouched and is waiting around a corner.
- Competitive settings (MLG, HCS) often disable radar; the bot must then rely on line of sight, teammate callouts and sound.

### Cover and line of sight

- Fight from cover whenever possible: only the head and gun visible. Reset behind cover when the shield pops.
- Avoid open ground between cover when enemies hold high ground or a sniper position. Move while enemies are reloading, dead or distracted.
- Height advantage matters: shooting down at an enemy exposes more of their body and makes headshots easier. Hold high ground, and deny it to the enemy.

### Team shooting

- Two players shooting the same target kill it in half the time. The bot should prioritize the enemy its teammates are already shooting (focus fire) over a fresh target.
- Stay within support distance of at least one teammate (Medium band or closer) so fights are two-on-one, never wander alone across the map.
- Call out: when a bot sees an enemy, its teammates should learn position, weapon and shield state. The scripting agent should share this as team knowledge.

### Weapon economy

- Carry one precision weapon and one situational weapon (power weapon, shotgun, automatic). Do not carry two weapons that solve the same problem.
- Swap to a better weapon lying on the ground when it is safe, and swap away from an empty power weapon.
- Reload behind cover or immediately after a kill, never mid-fight unless the magazine is empty. Melee instead of reloading if an enemy is at the Melee band and the magazine is empty.
- Pick up dropped power weapons from dead enemies, or at least stand on them to deny the enemy, when the area is safe.

## 3. Per-game differences

The six titles share the loop in section 2 but differ in pace, movement and sandbox. The bot should load a game profile at match start and switch the rules below on or off.

| Feature | Halo CE | Halo 2 / H2A | Halo 3 | ODST | Reach | Halo 4 |
| --- | --- | --- | --- | --- | --- | --- |
| Utility weapon | Pistol | BR (H2A: BR/Carbine) | BR | n/a (Firefight: pistol, SMG) | DMR, Magnum, Needle Rifle | BR, DMR, Carbine, Light Rifle |
| Sprint | No | No | No | No | Only as an armor ability | Always on |
| Dual wield | No | Yes | Yes | No | No | No |
| Equipment / abilities | None | None | Equipment pickups | None | Armor abilities (loadout) | Armor abilities + loadouts + ordnance |
| Health system | Shield + health bar, health packs | Shield + hidden regenerating health | Shield + hidden regenerating health | Stamina + health bar, health packs | Shield + health bar, health packs | Shield + regenerating health |
| Shield recharge delay | \~5 s | \~5 s | \~5 s | \~5 s stamina | \~5 s | \~5 s (faster with Shield perk) |
| Melee | Very strong, fast | Fast; lunge is generous | Slower, strong | Strong | Strong; bleed-through means low shield + melee kills | Standard |
| Grenade strength | Very strong, long throw | Strong | Strong; 3 extra types | Strong | Moderate; stickies strong | Weaker frags, pulse grenade added |
| Vehicle hijacking | No (vehicles can be shot or stuck) | Yes (boarding introduced) | Yes | Yes | Yes | Yes |
| Radar | 25 m | 25 m | 25 m | 25 m | 25 m, shows elevation | 25 m (Promethean Vision sees through walls) |
| Fall damage | Yes | No | No | Yes (stamina) | Yes | No |
| Overall pace | Fastest kills, pistol dominant | Fast, fights end in 1.5 s | Slower, 4-shot BR with spread | Firefight only | Slower, bloom on precision weapons | Fast, sprint everywhere |

### Halo: Combat Evolved

- The pistol (M6D) is the king: 3-shot headshot kill with 2x zoom at any range. Every bot should carry it. The assault rifle is a backup for Short band only.
- Grenades do heavy damage and can be thrown very far; grenade spam at spawn points and corridors is a real strategy. Rocket, sniper and shotgun are the power weapons that decide maps.
- No boarding, so a tank or Warthog must be killed with rockets, plasma stickies, or by killing the driver through the windscreen.
- Health does not regenerate: a damaged bot should seek the nearest health pack (and should remember pack locations per map) and should fight more cautiously until healed.
- Camouflage and Overshield powerups spawn on fixed timers; controlling them matters as much as controlling the rockets.
- No sprint and relatively slow strafing: fights are won by who sees first and lands first. Pre-aiming corners at head level is the strongest single habit.

### Halo 2 and Halo 2: Anniversary

- Battle Rifle is a 4-burst kill with no bloom; fights are very fast. Dual-wielding SMGs, plasma rifles, magnums and needlers is strong at Short band but prevents melee and grenade use until the bot drops a weapon.
- The plasma pistol charge plus BR headshot (the noob combo) is a near-instant kill at any range where the charged bolt can track (Short and close Medium).
- Rockets lock onto vehicles after a brief aim; the sword lunges from well beyond melee range. Both are mapped as must-control power weapons.
- Boarding is introduced: an enemy vehicle at Melee band can be hijacked or boarded, which is usually better than shooting it.
- Halo 2: Anniversary multiplayer runs on a modified Halo 2 sandbox with H2A-specific settings; treat it as Halo 2 unless the game variant says otherwise.

### Halo 3

- Battle Rifle 4-burst kill but with bullet spread; past Medium band the BR becomes unreliable, so the bot should close distance or use a carbine/sniper for Long band.
- Equipment pickups (bubble shield, power drain, regenerator, trip mine, deployable cover, radar jammer, flare, grav lift) are single-use map items; see section 6.
- Melee is slower but very strong: a two-melee kill is a common outcome of close fights. The mauler and shotgun own Short band.
- Spartan laser is the vehicle killer: a 2 to 3 second charge, then a hitscan beam that one-shots any vehicle and any player. The bot must break line of sight when it hears the charge sound.
- Grenade types: frag, plasma, spike, firebomb. Frags are weaker than Halo 2; melee and grenade combos are more valuable than grenade-only kills.

### Halo 3: ODST

- No competitive multiplayer; the MCC version has Firefight (co-op survival against waves of Covenant). ODSTs have no shields: a stamina layer recharges, and real health only comes back from health packs.
- The bot plays Firefight as a cautious squad member: hold a defensible position with teammates, fight from cover, keep the silenced pistol (headshot king) and automag/SMG, and prefer the plasma pistol plus pistol headshot combo on Elites and Brutes.
- Everything in sections 11 and 12 about retreating when low, waiting for teammates to respawn and sharing power weapons applies here directly.

### Halo: Reach

- Precision weapons (DMR, Needle Rifle, Magnum) have bloom: rapid fire spreads the reticle. The bot should pace shots at Medium and Long band, and only spam at Short band.
- Armor abilities are chosen at spawn (sprint, armor lock, jetpack, active camo, evade, hologram, drop shield). Each changes how the bot should fight and counter; see section 6.
- Health bar plus health packs: bleed-through means a melee on a low-shield enemy can kill. A bot with low health but full shield is still one grenade from death and should play like it.
- Grenades are fewer and frags do less damage; plasma stickies remain a one-shot kill. Vehicles are tougher; the Warthog and Ghost dominate big maps.
- Loadouts in Firefight and some playlists change starting weapons; the scripting agent should read the loadout rather than assume the DMR.

### Halo 4

- Sprint for everyone, faster shield recharge, and loadouts chosen before spawn (primary, secondary, grenade, armor ability, tactical and support perks). Ordnance drops give power weapons to players mid-match in standard playlists.
- Four precision options (BR, DMR, Carbine, Light Rifle); DMR is the longest-range, BR the most forgiving, Carbine the fastest up close, Light Rifle the best scoped.
- Promethean weapons: Scattershot (shotgun with ricochet), Binary Rifle (one-body-shot sniper), Incineration Cannon (rocket), Boltshot (pistol with a shotgun charge), Suppressor (SMG).
- Armor abilities include Promethean Vision (see through walls), Thruster Pack (short dash), Hardlight Shield, Hologram, Active Camo, Jet Pack, Regeneration Field, Autosentry.
- Frag grenades are weaker; the pulse grenade is an area denial tool. Vehicle sandbox adds the Mantis (walker) which can stomp and must be flanked or stuck.

## 4. Weapon rules of engagement

Each weapon has an engagement band where it wins, a band where it loses, and a counter. The bot's first job in any fight is to compare its weapon band to the current distance and either fight, close in, or back off. Bands use the scale from section 1. "Avoid" means the bot should change distance or swap weapons rather than take the fight.

### Weapon classes and the general rule

| Class | Examples | Wins at | Loses at | Standing rule |
| --- | --- | --- | --- | --- |
| Precision / utility | Pistol (CE), BR, DMR, Carbine, Needle Rifle, Light Rifle, Magnum (Reach/H4) | Medium, Long (scoped) | Melee band vs. shotgun/sword | Default weapon; always keep one. Pace shots, aim head, strafe. |
| Automatic | AR, SMG, Plasma Rifle, Spiker, Storm Rifle, Suppressor, Plasma Repeater, SAW | Short, close Medium | Medium and beyond | Close the gap or disengage. Pair with melee. Never trade at Long. |
| Close-quarters power | Shotgun, Mauler, Scattershot, Energy Sword, Gravity Hammer | Melee, Short | Medium and beyond | Fight around corners and in rooms; never cross open ground toward a rifle. |
| Sniper | Sniper Rifle, Beam Rifle, Binary Rifle, Focus Rifle | Long, Extreme, far Medium | Short, Melee | Hold a long sightline with an escape route; no-scope only as a last resort. |
| Explosive / anti-vehicle | Rocket Launcher, Spartan Laser, Fuel Rod, Plasma Launcher, Incineration Cannon, Railgun, Grenade Launcher, Brute Shot, Concussion Rifle | Short to Long depending on weapon | Melee band (self-damage) | Save for vehicles and grouped enemies; never fire at Melee band. |
| Support / disabling | Plasma Pistol, Needler, Sticky Detonator, Boltshot | Short, Medium | Long | Combine with a precision weapon: strip shield, then headshot. |
| Turrets | Machine gun, Plasma cannon, Missile pod (detached) | Medium | Any flank | Only mount when teammates cover; detach and move after a few seconds. |

### Halo: Combat Evolved

| Weapon | Band | Best use | Counters / avoid |
| --- | --- | --- | --- |
| Pistol (M6D) | Short to Long (2x zoom) | 3-shot headshot kill; the default weapon at every range. Zoom at Medium and beyond. | Shotgun at Melee band, sniper at Extreme. Nothing else; keep it always. |
| Assault Rifle | Short | 60-round spray plus melee at Short band; strong vs. an unshielded enemy. | Avoid Medium and beyond, bullets spread wildly. Swap for pistol the moment one is available. |
| Shotgun | Melee, Short | One-shot kill at Melee band; two at Short. Corners, ramps, teleporter exits. | Avoid Medium and beyond entirely. Pistol users at Medium win every time. |
| Sniper Rifle | Long, Extreme, far Medium | Headshot kills regardless of shield; body shots take two. 2x and 8x zoom. | Avoid Short; no-scope only when an enemy is already damaged. Swap to pistol when rushed. |
| Rocket Launcher | Short to Long | Two rockets; splash kills groups and any vehicle. Fire at feet, not at the head. | Never fire within 15 ft of self. Do not waste on a single full-shield player when teammates can finish with pistols. |
| Plasma Pistol | Short, Medium | Charged shot strips a shield instantly and stalls vehicles; follow with pistol headshot or melee. | Charged bolt is slow, dodged at Long. Uncharged fire is weak. |
| Plasma Rifle | Short, Medium | Rapid shield-stripping fire with a stun that slows the enemy; strong when paired with melee. | Overheats; loses at Long. Drop for a pistol. |
| Needler | Short, Medium | Homing needles; 7 needles supercombine for a kill. Strong vs. a strafing enemy at Short. | Needles are slow; avoid Long and avoid enemies behind cover. |
| Flamethrower / Fuel Rod (custom games only) | Short / Medium | Area denial in corridors / arcing anti-vehicle rounds | Dropped in competitive settings; follow rocket rules for fuel rod. |
| Frag grenade | Short to Medium throw | Very long throw, big radius. Pre-nade spawns, corners and health-pack rooms. | Bounces unpredictably off slopes. |
| Plasma grenade | Short | Sticks for an instant kill; stick vehicles and the Warthog's gunner. | Slow throw arc; miss and it rolls harmlessly. |

### Halo 2 and Halo 2: Anniversary

| Weapon | Band | Best use | Counters / avoid |
| --- | --- | --- | --- |
| Battle Rifle | Medium, Long (2x zoom) | 4-burst headshot kill; no spread. The default weapon. Strafe and shoot. | Shotgun and sword at Melee band, dual SMG at Short. Create distance from those. |
| SMG | Short | Dual SMGs shred at Short band; single SMG plus melee. | Avoid Medium and beyond; recoil ruins accuracy. Avoid shotgun and sword at Melee band. Dual-wielding disables grenades and melee until one is dropped. |
| Magnum | Short, close Medium | Dual magnums or magnum plus plasma rifle is fast at Short. Headshot capable. | Weak alone; avoid Long. |
| Plasma Rifle / Brute Plasma Rifle | Short, close Medium | Strips shields fast; dual plasma rifles or plasma rifle plus SMG is a top Short-band loadout. Brute variant fires faster, overheats sooner. | Overheats; avoid Long. |
| Plasma Pistol | Short, Medium | Charge, hit, then BR headshot or melee: the fastest kill in the game. Charged bolt tracks slightly. | Charging drains the battery; avoid holding charge longer than 3 to 4 s. Cannot kill alone. |
| Needler | Short, Medium | Dual needlers are a strong Short-band loadout; supercombine kills. | Needles are slow and blockable; avoid Long. |
| Carbine | Medium, Long | 7-shot headshot kill with fast fire; better than BR at Long. | Low magazine; shotgun and sword at Melee band. |
| Shotgun | Melee, Short | One-shot kill at Melee band; two at Short. Guard corners, lifts, ladders. | Avoid Medium and beyond. Against a BR user at Medium, break line of sight and wait. |
| Energy Sword | Melee (lunge reaches into Short) | Lunge kill when the reticle is red; works around corners and on lifts. Infinite ammo in Halo 2. | Avoid any open ground; a BR at Medium kills before the lunge. Shotgun trades at Melee band. Sword clash: do not attack when the enemy also has a sword and the reticle is not red. |
| Sniper Rifle | Long, Extreme, far Medium | Headshot kill at any shield; 5x and 10x zoom; 4-round magazine. | Avoid Short; swap to BR when an enemy closes. Watch for flanking while scoped. |
| Beam Rifle | Long, Extreme | Same role as sniper; no reload but overheats after about 2 fast shots. | Avoid rapid double shots unless the kill is certain; it overheats and leaves the bot defenseless. |
| Rocket Launcher | Short to Long | Locks onto vehicles after holding the reticle on them; 2-round magazine; splash kills groups. | Never fire at Melee band. Save for vehicles and pairs of enemies; single full-shield enemies only in emergencies. |
| Brute Shot | Short, Medium | Arcing grenades, 4-round magazine; strong vs. groups and for bouncing enemies out of cover; melee is powerful. | Low direct damage vs. a single player; avoid Long. |
| Sentinel Beam | Short, Medium | Continuous beam that melts shields; strong vs. Flood in campaign, situational in MP. | Overheats; weak vs. health. |
| Frag grenade | Short to Medium throw | Bounce into rooms, pre-nade teleporters and lifts. | Short fuse; do not hold ground next to a thrown frag. |
| Plasma grenade | Short | Stick for instant kill; stick Ghosts and Warthogs. | Slow throw; avoid vs. strafing targets at Medium. |

### Halo 3

| Weapon | Band | Best use | Counters / avoid |
| --- | --- | --- | --- |
| Battle Rifle | Medium (Long with zoom, unreliable) | 4-burst kill; the default weapon. Pace bursts at Long. | Spread makes Long band a coin flip; close in or swap to carbine/sniper. Shotgun, mauler, sword, hammer at Melee band. |
| Assault Rifle | Short, close Medium | Spawn weapon; 32 rounds. Shoot then melee is a reliable kill at Short. | Avoid Medium and beyond; the BR wins any trade past Short. Avoid shotgun and sword at Melee band. |
| SMG | Short | Dual SMG plus melee; single SMG is weak. | Avoid everything past Short; recoil climbs. |
| Magnum | Short, Medium | Headshot capable; dual magnum or magnum plus plasma rifle at Short. | Slow fire; weak alone at Long. |
| Carbine | Medium, Long | 7-shot kill, precise at Long where the BR spreads. | Shotgun, sword at Melee band. |
| Plasma Pistol | Short, Medium | Charge then BR headshot; charged bolt stalls Warthogs, Ghosts, Mongooses and Choppers for a free boarding. | Battery drains while charged; avoid Long. |
| Plasma Rifle | Short | Strips shields; dual plasma rifle plus melee. | Overheats; avoid Medium and beyond. |
| Spiker | Short | Dual spikers at Short; strong melee. | Projectiles drop; avoid Medium and beyond. |
| Needler | Short, Medium | Supercombine kills; two-handed in Halo 3 (no dual). Best vs. enemies in the open at Short. | Needles are dodgeable at Long; blocked by cover. |
| Mauler | Melee, Short | One mauler shot plus melee kills a full-shield player; dual maulers one-shot at Melee band. | Avoid Medium and beyond. |
| Shotgun | Melee, Short | One-shot kill at Melee band; corners, lifts, man-cannon landings. | Avoid Medium and beyond. |
| Energy Sword | Melee (lunge) | Lunge when the reticle is red. Limited energy in Halo 3. | A BR kills a sword rusher in the open; hammer and shotgun trade. Do not lunge at a shotgun. |
| Gravity Hammer | Melee, Short | Area smash kills anyone within about 8 ft; can deflect rockets and grenades and flip vehicles. | Slow swing; avoid open ground and Medium band. |
| Sniper Rifle | Long, Extreme, far Medium | Headshot at any shield; body shots take two. | Avoid Short; swap when rushed. |
| Beam Rifle | Long, Extreme | Same as sniper with overheat instead of reload. | Avoid double-tapping unless the kill is sure. |
| Rocket Launcher | Short to Long | No vehicle lock-on in Halo 3; lead moving vehicles. Splash kills groups. | Never at Melee band. Reserve for vehicles and groups. |
| Spartan Laser | Medium, Long, Extreme | Charge about 2.5 s, then a hitscan beam kills any vehicle and any player. The best anti-vehicle tool in the game. | Only use on players in emergencies or when they are stationary. The charge glow and sound warn the target; fire from cover. 5 shots per battery. |
| Missile Pod | Medium, Long | Locks on to vehicles; detached from its stand it is a mobile anti-air and anti-vehicle weapon. | Slow to turn; weak vs. infantry. |
| Fuel Rod Gun | Medium, Long | Arcing green rounds; splash kills players and damages vehicles. | Rounds are slow; avoid Short. |
| Brute Shot | Short, Medium | 6-round arcing grenade launcher; bounces enemies; strong melee blade. | Weak vs. a single BR user at Medium. |
| Flamethrower | Short | Area denial in corridors; Infection and custom games. | Very slow movement while held; avoid open ground. |
| Sentinel Beam | Short, Medium | Beam melts shields quickly. | Overheats; weak at health. |
| Machine Gun Turret / Plasma Cannon | Medium | Detach and move; mounted turrets suppress lanes. | Slow movement while carried; a sniper kills the user. |
| Frag grenade | Short to Medium throw | Weaker than Halo 2; use for finishing and flushing. | Avoid relying on a single frag to kill. |
| Plasma grenade | Short | Stick for instant kill; stick vehicles. | Slow arc. |
| Spike grenade | Short | Sticks to surfaces and players; sprays spikes in a cone, deadly in corridors. | Bounces off players at a steep angle. |
| Firebomb grenade | Short | Burns an area for several seconds; blocks a doorway. | Does not stick; weak vs. a moving target. |

### Halo: Reach

| Weapon | Band | Best use | Counters / avoid |
| --- | --- | --- | --- |
| DMR | Medium, Long (3x zoom) | 5-shot headshot kill; pace shots to beat bloom; the default weapon. | Shotgun, sword, hammer at Melee band. Spamming the trigger at Long misses. |
| Needle Rifle | Medium, Long | 7-shot headshot kill; or 3 needles supercombine on an unshielded enemy. Less bloom than the DMR. | Lower damage per shot; needles blocked by cover. |
| Magnum | Short, Medium | 5-shot headshot kill; a strong close precision weapon. | Avoid Long. |
| Assault Rifle | Short | Spray plus melee at Short. | Avoid Medium and beyond. |
| Plasma Repeater | Short, close Medium | Vent to reset heat; shield stripping. | Avoid Long. |
| Plasma Rifle | Short | Strips shields; melee follow-up. | Overheats; avoid Long. |
| Spiker | Short | Rapid fire at Short; strong melee. | Avoid Medium and beyond. |
| Plasma Pistol | Short, Medium | Charge then headshot; EMPs vehicles for a hijack. | Avoid Long; battery drains. |
| Needler | Short, Medium | Supercombine kill; strong vs. jetpackers in the open. | Avoid Long and cover. |
| Shotgun | Melee, Short | One-shot kill at Melee band; corners and lifts. | Avoid Medium and beyond. |
| Energy Sword | Melee (lunge) | Lunge kill; strong with Active Camo or Evade. | Open ground at Medium band; armor lock blocks a lunge (and a sword user who hits armor lock dies to the counter-melee). |
| Gravity Hammer | Melee, Short | Area kill; flips vehicles. | Slow swing; open ground. |
| Sniper Rifle | Long, Extreme, far Medium | Headshot at any shield. | Avoid Short. |
| Focus Rifle | Long, Medium | Continuous beam; about 3 s of beam kills a full-shield player; strong vs. jetpackers. | Overheats; reveals position with a bright beam. |
| Rocket Launcher | Short to Long | Locks on to air vehicles; splash kills groups. | Never at Melee band. Reserve for vehicles and groups. |
| Spartan Laser | Medium, Long, Extreme | One-shot any vehicle; charge from cover. | Charge is visible; only on players in emergencies. |
| Plasma Launcher | Medium, Long | Charge up to 4 homing plasma bombs that stick vehicles; the best anti-Ghost and anti-Warthog tool. | Slow projectiles vs. infantry; avoid Short. |
| Grenade Launcher | Short, Medium | Fire and hold trigger for a remote-detonated EMP round; stalls vehicles and one-shots a direct hit. | Low rate of fire; avoid Long. |
| Concussion Rifle | Short, Medium | Splash knocks enemies around and off ledges; strong on jetpackers. | Low direct damage; avoid Long. |
| Fuel Rod Gun | Medium, Long | Arcing splash vs. groups and vehicles. | Slow rounds; avoid Short. |
| Frag grenade | Short to Medium throw | Weaker than Halo 3; flush and finish only. | Do not expect a solo kill. |
| Plasma grenade | Short | Stick for instant kill; stick vehicles and armor-locked players (stick before they lock). | Slow arc. |

### Halo 4

| Weapon | Band | Best use | Counters / avoid |
| --- | --- | --- | --- |
| Battle Rifle | Medium, Long | 5-burst kill, forgiving; the default loadout weapon. | Shotgun, scattershot, sword, hammer at Melee band. |
| DMR | Medium, Long, Extreme | 5-shot kill; best Long-band loadout weapon. | Slower at Short than BR or carbine. |
| Carbine | Short, Medium | 8-shot kill with the fastest fire; wins close precision duels. | Loses at Long to DMR. |
| Light Rifle | Medium, Long | 4-shot kill when scoped; 5 unscoped. Scope whenever possible. | Scoped fire is slower; avoid Short. |
| Magnum | Short, Medium | 6-shot kill; strong secondary. | Avoid Long. |
| Assault Rifle | Short | Spray plus melee; the strongest AR in the series. | Avoid Medium and beyond. |
| Storm Rifle | Short | Covenant automatic; shield stripping. | Overheats; avoid Long. |
| Suppressor | Short | Promethean automatic; high rate of fire, heavy spread. | Avoid Medium and beyond. |
| SAW | Short, close Medium | 72-round shredder; kills faster than any loadout weapon at Short. | Avoid Long; reload is long. |
| Boltshot | Short | Charged shot is a one-hit kill at Melee band (shotgun pistol). Loadout secondary. | Charge is slow and short-ranged; avoid Medium. |
| Plasma Pistol | Short, Medium | Charge plus headshot; EMPs vehicles and the Mantis. | Avoid Long. |
| Needler | Short, Medium | Supercombine kill; strong vs. sprinting enemies in the open. | Avoid Long. |
| Shotgun | Melee, Short | One-shot at Melee band. | Avoid Medium and beyond. |
| Scattershot | Melee, Short | One-shot at Melee band; shots ricochet off walls into rooms. | Avoid Medium and beyond. |
| Energy Sword | Melee (lunge) | Lunge kill; strong with Thruster Pack or Active Camo. | Hardlight shield blocks a lunge; open ground. |
| Gravity Hammer | Melee, Short | Area smash; flips vehicles. | Open ground. |
| Sniper Rifle | Long, Extreme | Headshot at any shield. | Avoid Short. |
| Beam Rifle | Long, Extreme | Headshot; overheat instead of reload. | Avoid double shots. |
| Binary Rifle | Long, Extreme | One body shot kills; 2-round magazine; a red targeting beam warns the target. | Avoid Short; the beam gives away position. |
| Rocket Launcher | Short to Long | Splash kills groups; strong vs. all ground vehicles. | Never at Melee band. |
| Spartan Laser | Medium, Long, Extreme | One-shot any vehicle. | Charge is visible. |
| Railgun | Medium, Long | Charge about 1 s, then a hitscan slug that kills a player or heavily damages a vehicle. | Charge must be held; avoid Short. |
| Incineration Cannon | Short to Long | One-shot splash kill on players and heavy vehicle damage. | Never at Melee band; slow reload. |
| Sticky Detonator | Short, Medium | Fire a sticky explosive, detonate when an enemy walks over it or a vehicle passes. | Single shot; slow. |
| Fuel Rod Gun | Medium, Long | Arcing splash vs. groups and vehicles. | Avoid Short. |
| Concussion Rifle | Short, Medium | Knockback splash. | Low direct damage. |
| Frag grenade | Short to Medium throw | Flush and finish. | Weak alone. |
| Plasma grenade | Short | Stick for instant kill. | Slow arc. |
| Pulse grenade | Short, Medium | Drains shields in a sphere for a few seconds; area denial on a flag or hill. | Low kill power; easy to walk out of. |

## 5. Vehicle rules of engagement

Vehicles decide big maps: a crewed Warthog or a Scorpion with support is the strongest single object on Blood Gulch, Valhalla, Hemorrhage or Ragnarok. The bot needs three sets of rules: how to use each vehicle, how to counter each vehicle, and when to abandon one.

### Universal vehicle rules

- Never drive alone into enemy territory. A vehicle is worth its crew; a one-man Warthog is a free kill and a free vehicle for the enemy.
- Keep moving. A stationary vehicle gets stuck, boarded, lasered or rocketed. Circle, strafe and retreat behind terrain between passes.
- Watch the splatter: driving into an enemy at speed kills them in every game. Splatter is the Ghost's, Mongoose's and Warthog's best weapon at Short band.
- Boarding (Halo 2 onward): an enemy on foot at Melee band can jump on and either throw the driver out (Warthog, Mongoose, Ghost, Chopper) or plant a grenade (Scorpion, Wraith, Banshee). Keep foot soldiers away from the vehicle; drive off if one reaches Melee band.
- Charged plasma pistol, grenade launcher EMP (Reach) and pulse grenade (Halo 4) stall a vehicle for a few seconds: expect to be boarded and bail out and fight on foot if the enemy is close.
- Bail out when the vehicle is smoking and burning (critical damage), when a Spartan laser charge sound is heard with no cover in reach, or when a rocket is locked on. A dead vehicle takes its crew with it.
- Passengers should shoot: a Warthog passenger seat or Scorpion side seat with a precision weapon or rocket adds a lot of damage.
- Do not take a vehicle in symmetrical arena maps or in modes where it cannot score (a flag carrier cannot drive a Ghost in most games; a Mongoose or Warthog passenger can carry the flag).

### Vehicle table

| Vehicle | Games | Crew | Strength | Weakness | How the bot counters it |
| --- | --- | --- | --- | --- | --- |
| Warthog (chain gun) | All | Driver, gunner, passenger | Fast, turret shreds infantry at Short and Medium, splatter | Gunner is exposed; driver can be shot through the windscreen; boardable; flips | Shoot the gunner first with precision fire; stick a plasma grenade; rocket; laser; board when it stops. Hide behind hard cover until it passes, then shoot the gunner from behind. |
| Gauss Warthog | H2, H3, Reach, H4 | Driver, gunner, passenger | Gauss cannon one-shots light vehicles and players | Slow cannon rate; gunner exposed | Same as Warthog; approach out of the gunner's line of fire. |
| Rocket Warthog | CE (MCC), Reach, H4 | Driver, gunner, passenger | Volley kills vehicles | Slow volley; weak vs. close infantry | Close in on foot and shoot the gunner. |
| Mongoose | H3, Reach, H4 | Driver, passenger | Fastest transport, flag running, passenger can shoot | No armor; one grenade kills; easily flipped | Shoot the driver; grenade; splatter with a bigger vehicle. |
| Ghost | All | Driver | Boost, strafing plasma, splatter at Short band | Driver exposed from the sides and rear; stalls on EMP | Precision fire on the driver; plasma stick; EMP then board; sidestep the boost and melee the side. Never run straight away from a boosting Ghost. |
| Scorpion tank | All | Driver, 4 passengers (H3+) | Main cannon one-shots everything; splash | Slow turn; blind spots at close range and behind; boardable with grenade; laser kills in one shot | Laser or rockets from Long band; stick two plasmas; board from behind and plant a grenade; on foot, hide behind terrain it cannot shoot through and wait for teammates. |
| Wraith | H2, H3, Reach, H4 | Driver (+ gunner in H3) | Arcing plasma mortar with huge splash; boost; splatter | Slow mortar travel; weak vs. close infantry; boardable | Close in while the mortar is in the air; board and plant a grenade; stick; laser. Strafe sideways, never straight toward or away. |
| Banshee | All | Pilot | Fast air; plasma guns and fuel rod bomb; barrel roll and flip to dodge | Fragile; rockets lock on (H2, Reach, H4); laser one-shots; boardable in H3 | Rockets or laser; precision fire when it hovers; missile pod; plasma launcher. On foot, stand under overhangs. |
| Hornet | H3 | Pilot, 2 passengers | Hover, missiles, machine guns | Fragile; passengers exposed; boardable | Laser, rockets, missile pod; precision fire on the pilot. |
| Falcon | Reach | Pilot, 2 gunners | Transport with side turrets | Slow; big target for lasers and plasma launchers | Laser, plasma launcher, rockets. |
| Chopper (Brute) | H3 | Driver | Boost ram destroys any vehicle it hits; strong cannons | Driver exposed; slow turn | Shoot the driver; sidestep the ram; stick. |
| Prowler | H3 | Driver, gunner, 2 passengers | Fast transport with turret | Fragile; crew exposed | Precision fire on the crew. |
| Revenant | Reach | Driver, passenger | Fast plasma mortar buggy | Fragile; crew exposed | Precision fire, stick, plasma launcher. |
| Mantis | H4 | Pilot | Walker with machine gun and missiles; stomp kills infantry at Melee band; shield | Slow; EMP stalls it; rear and sides are weaker | Plasma pistol or pulse grenade EMP, then board and plant a grenade; laser; railgun volleys; keep out of the stomp radius. |
| Spectre | H2 | Driver, gunner, passenger | Covenant transport with plasma turret | Fragile; crew exposed | Precision fire on the crew. |
| Shadow / Elephant / Pelican / Phantom | Campaign, H3 Sandtrap (Elephant) | n/a | The Elephant is a mobile base on Sandtrap | Slow; boardable | Board it with teammates; fight inside. |

### Driver, gunner and passenger behavior

- Driver: route around enemy anti-vehicle positions, deliver the gunner to a firing line at Medium band, keep moving in arcs, splatter enemies caught in the open, and retreat behind terrain when the gunner's target has cover.
- Gunner: focus the nearest threat that can damage the vehicle first (laser, rockets, plasma pistol), then the nearest infantry. Lead moving targets; aim slightly ahead at Medium band.
- Passenger: shoot with a precision weapon, throw grenades at infantry in reach, and stick vehicles the driver passes.
- Tank: stay behind the infantry line, shoot where enemies cluster, and keep a Short-band escort to stop boarders. If no escort, never drive into an enclosed area.
- Air: strafe runs, never hover in the open. Bank away the instant a lock-on warning or laser charge is seen. In Halo 3 the Banshee bomb is best used on vehicles and groups.

### Anti-vehicle weapon priority

When an enemy vehicle is active, the bot should seek weapons in this order: Spartan laser, rocket launcher, plasma launcher (Reach), railgun or incineration cannon (H4), fuel rod, missile pod, plasma grenades, plasma pistol (for stall and board), then precision fire on exposed crew. A Gauss Warthog or Scorpion of its own counters most things too.

### Map-level vehicle rule

If the enemy has an active vehicle and the bot's team has no anti-vehicle weapon in hand, the whole team should fight near hard cover (rocks, bases, tunnels) and send one player to the nearest anti-vehicle spawn. The bot should never cross open ground while an enemy vehicle has a line of sight on it.

## 6. Equipment, armor abilities and ordnance

Three games add a non-weapon layer: Halo 3 equipment (single-use pickups), Reach armor abilities (chosen at spawn, recharge) and Halo 4 armor abilities with loadouts and ordnance drops. Each one has a use rule and a counter rule.

### Halo 3 equipment

| Equipment | Use it when | Counter when the enemy uses it |
| --- | --- | --- |
| Bubble Shield | Shield pops with no cover nearby; protect a flag carrier or a teammate reviving; block a sniper lane for 20 s. Enemies can walk in, so stand ready to melee. | Walk in and melee or shoot; throw a grenade inside; wait outside with a shotgun. Never shoot the dome from outside. |
| Power Drain | Throw into a room or at a vehicle: strips shields and stalls vehicles in a radius. Follow with a headshot or boarding. | Move out of the radius immediately; it lasts a few seconds. |
| Regenerator | Drop at your feet in a fight you are winning or while a teammate is low; recharges shields fast for everyone inside. | Step inside too (it heals both teams) or throw a grenade in; do not trade shots with someone standing in it from outside. |
| Trip Mine | Place on vehicle routes, flag return paths or doorways; one-shot on a vehicle, deadly on a player. | Shoot it from a distance to detonate; avoid the beeping. |
| Deployable Cover | Drop in an open lane to create a shield wall; blocks shots in one direction. | Shoot the wall until it breaks or flank around it. |
| Radar Jammer | Throw before a push to flood enemy radars with fake dots. | Trust line of sight over radar for its duration. |
| Flare | Throw to blind a room or a sniper. | Turn away, back into cover, listen for footsteps. |
| Gravity Lift | Place to reach high ground fast or launch a teammate onto a roof. | Shoot anyone riding it at the top; grenade the landing spot. |
| Invincibility (Brute) | Rare; use to rush a power weapon or a flag. | Run; wait the few seconds out. |

### Halo: Reach armor abilities

| Ability | Bot use rule | Counter rule |
| --- | --- | --- |
| Sprint | Close gaps on shotgun or sword users, rotate to objectives, escape a losing fight. Sprint cannot shoot; stop sprinting before reaching Medium band of an enemy. | A sprinting enemy cannot shoot: start shooting the moment they commit; melee when they arrive. |
| Armor Lock | Only when a vehicle is about to splatter, a sticky lands, or a rocket is incoming; it reflects explosives and EMPs vehicles that touch it. Release early to catch an enemy mid-melee. | Do not melee or shoot the locked player; back off to Medium band and reload; stick a grenade on the ground beside them, or wait for the lock to end then headshot. Never stand next to a locked enemy. |
| Jet Pack | Reach high ground and skip ramps; a jetpacker over the map is a sniper's dream, so pulse jetpack behind cover. | Shoot jetpackers in the air with precision weapons or needler; they cannot strafe. |
| Active Camo | Crouch-walk only; it creates a radar jammer effect. Sword or shotgun plus camo for ambushes. | Watch for the shimmer; fire where the radar jam appears; melee suspected spots. |
| Evade (Elite) / Sprint | Dodge grenades and break strafes; close on a target in two rolls. | Shoot where the roll ends. |
| Hologram | Send a hologram around a corner before peeking; use it to bait a sniper shot or a grenade. | A target that runs straight and does not shoot is a hologram; shoot it once and ignore. |
| Drop Shield | Heals the team inside; use on objectives and for revives. | Enter and melee, or throw grenades inside; it breaks under fire. |

### Halo 4 armor abilities

| Ability | Bot use rule | Counter rule |
| --- | --- | --- |
| Promethean Vision | Pulse before pushing a room or corner to see enemies through walls; follow with a pre-fire. | The pulse is visible to the user only; assume a careful enemy has it and avoid predictable corner camps. |
| Thruster Pack | Dash behind cover when the shield pops; dash to dodge a sword lunge or rocket. | Track the dash direction and keep shooting; it is short. |
| Hardlight Shield | Raise when caught in the open at Medium band or when a sword lunges; cannot shoot while raised. | Flank or wait; the user cannot shoot back. Grenade their feet. |
| Hologram | Bait and corner checks as in Reach. | Ignore a non-shooting runner. |
| Active Camo | Ambushes with scattershot or sword; crouch-walk. | Watch the shimmer; grenade the suspected spot. |
| Jet Pack | High ground on Ragnarok and Exile; fly behind cover. | Shoot in the air. |
| Regeneration Field | Drop on the objective or in a held room. | Push with grenades; it does not block shots. |
| Autosentry | Place covering a doorway or flag. | Shoot the sentry first; it has little health. |

### Halo 4 loadouts, perks and ordnance

- Loadout choice: a bot should pick a precision primary (BR or DMR), a utility secondary (Magnum, Plasma Pistol or Boltshot), frag or plasma grenades, and an ability that matches its play style (Thruster for aggressive, Promethean Vision for cautious, Jet Pack on big maps).
- Perks that change behavior: Mobility (unlimited sprint) lets the bot rotate constantly; Shielding shortens recharge so the bot can re-peek sooner; Dexterity speeds reloads; Ammo gives more reserve; Explosives make grenades stronger and reduce damage taken from them.
- Ordnance: personal ordnance drops give a choice of three (usually a power weapon, a damage boost or speed boost, or an overshield). The bot should take the power weapon if the team lacks one, otherwise the damage boost in a fight or the overshield for an objective push. Map ordnance drops are announced on the HUD; move to them when the route is safe and deny the enemy.

### Powerups (all games)

- Overshield: triple shield layer; take it before a push or a power-weapon fight. With an overshield the bot can commit to fights it would otherwise avoid, but it still dies to a sniper headshot.
- Active Camo (powerup): invisible while still or slow; grab the sniper or shotgun and ambush. Do not shoot until the kill is certain; firing reveals the user.
- Custom powerup, Speed Boost, Damage Boost (Halo 4): use the boost window for an aggressive push and remember it runs out.
- Powerups respawn on fixed timers (often 60 to 120 s depending on the game and variant); treat them as objectives in section 7.

## 7. Map knowledge: power positions and power weapon spawns

A bot that holds the right 20 ft of a map wins more than a bot that aims better. This section gives the rules for finding power positions on any map, the spawn timers the bot should count, and the known power spots and power weapons on the core maps of each game. Exact weapon placements and respawn times live in each map's scenario tags and game variant; the scripting agent should read those at load and use this section for the reasoning about what to do with them.

### How the bot recognizes a power position on any map

Score every reachable spot on the map by these features; the top three or four scores are the power positions the team should hold.

1. Height: looks down on at least two lanes or a major room.
2. Sightlines: can see a power weapon spawn, a powerup spawn, an objective (flag, hill, bomb plant) or the enemy's main spawn.
3. Entrances: one or two approaches, both of which the holder can watch or a teammate can cover.
4. Escape: a route out that breaks line of sight within 10 ft (a drop, a door, a ramp).
5. Cover: a head-height edge or wall the holder can duck behind to recharge.
6. Resupply: grenades, a BR/DMR or a health pack within 20 ft.

A spot with height and sightlines but no escape is a sniper nest, not a position: the bot uses it for a few seconds, then moves. A spot with escape and cover but no sightlines is a defensive reset point, used when low on shields.

### Spawn timers the bot should count

The bot starts a timer the moment a power weapon or powerup is picked up (or at match start) and moves to contest it 10 to 15 s before it respawns. In Halo 3 and later, standing still on a weapon for about one second before grabbing it keeps the respawn clock clean; grabbing while moving delays the next spawn ([MCC Halo 3 timer post](https://www.bungie.net/Ne/Forums/Post/106060001?page=0)).

| Setting | Item | Respawn | Source |
| --- | --- | --- | --- |
| Halo 3 MLG v8 | Sniper Rifle | 150 s, drop spawn | [Halopedia MLG playlist](<https://www.halopedia.org/MLG_(playlist)>) |
| Halo 3 MLG v8 | Rocket Launcher | 180 s, drop spawn | Halopedia MLG playlist |
| Halo 3 MLG v8 | All powerups (Camo, OS, custom) | 120 s; Construct Camo not before 2:00 | Halopedia MLG playlist |
| Reach MLG | Rocket Launcher | 178 s | Halopedia MLG playlist |
| Reach MLG | Sniper Rifle, Grenade Launcher | 118 s | Halopedia MLG playlist |
| Reach MLG | Powerups | 120 s | Halopedia MLG playlist |
| Halo 3 MCC default | The Pit: Sniper 2:00, Rockets 3:00, Sword 2:00, Shotgun 2:00 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Guardian: Sniper 3:00, Hammer 3:00, Shotgun 3:00 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Construct: Sniper 3:00, Laser 2:00, Sword 3:00 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Narrows: Sniper 2:30, Rockets 3:00, Shotgun 2:00 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | High Ground: Sniper 1:30, Rockets 2:00, Laser 2:00, Shotgun 1:30 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Last Resort: Sniper 2:00, Laser 2:00, Shotgun 1:30 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Standoff: Laser 3:00, Rockets 3:00 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Snowbound: Sniper 2:30, Laser 2:30, Shotgun 3:00 | per map | bungie.net MCC timer post |
| Halo 3 MCC default | Heretic: Sword 3:00, Shotgun 2:00 | per map | bungie.net MCC timer post |
| Halo CE, Halo 2, Halo 4 defaults | Power weapons | Typically 90 to 180 s; powerups 60 to 120 s (approximate; read from the variant) | community timing guides |

### Halo: Combat Evolved maps

CE positions are about pistol sightlines and grenade spam; the pistol kills at any range, so the best spots see the most ground. Weapon layouts below are the classic defaults (approximate; verify in tags).

| Map | Power weapons and powerups | Power positions (callouts) | Bot notes |
| --- | --- | --- | --- |
| Battle Creek | Rockets on the rock ledge above the creek (mid); a sniper on the cliff ledge behind each base reached by ladder; shotgun in the tunnel; overshield and camo in the cave side | Red roof and Blue roof (base tops), the sniper ledges, the rock arch over the creek | Climb the far-side ladder for the sniper at the start; hold a base roof with the sniper and a pistol; rush rockets with a grenade thrown first. Roof holders must watch the ladder behind them. |
| Blood Gulch | Rockets at mid field; a sniper at each base; overshield and camo in the side caves; Warthogs at each base | Base roofs, the mid rocks, the cliff ledges on each side, the caves | Never cross the open middle on foot while an enemy Warthog is alive; crew a Warthog with a gunner; snipers hold base roofs and the cave mouths. |
| Hang 'Em High | Rockets in the mid trench; sniper rifles on the elevated walkways; overshield on the tower; camo at mid | Tombstones (the pillars), the long walkways, the tower top, the pit edges | Walkways give pistol lanes across the whole map; avoid the pit floor; grenade the tombstone cover before pushing. |
| Chill Out | Rockets on the top ledge reached by teleporter; camo at the center; shotgun and overshield in the lower rooms | Top ledge, the center bridge, teleporter exits | Teleporter exits are ambush points: pre-aim them. Camo plus shotgun owns the lower halls. |
| Damnation | Rockets in the lower rocket room by the water; overshield on the top platform; shotgun in the tunnels | Top platform, the rocket room, the lift tops | The top platform sees the center; the rocket room has two entrances that must both be watched. |
| Prisoner | Rockets on the top-mid ledge; camo on the lower level; overshield on top; shotgun near spawns | Top level ring, the center pillar top, the ladders | Hold the top ring; everything below is a pit. Ladders are kill zones, so grenade the top of a ladder before climbing. |
| Rat Race | Rockets at the bottom; camo in the center loop; shotgun in the halls | The center ring, the top ramps | Circular flow: hold the ring and shoot down into both halls. |
| Wizard | Rockets on the raised center; overshield and camo at the corners | Center platform, the corner ramps | Symmetrical; the center is everything but exposed on four sides. Hold two adjacent corners instead. |
| Sidewinder | Rockets at mid; sniper in each base; overshield in the tunnel; Warthogs, Ghosts, Banshees (PC maps) | Base rooftops, the tunnel mouths, the mid rocks | Big map; stay with a vehicle crew or in the tunnel. |
| Derelict, Longest, Boarding Action | Rockets and overshield mid (Derelict); shotgun and camo (Longest); snipers on each ship (Boarding Action) | Upper ring (Derelict), the middle bridges (Longest), the far-side windows (Boarding Action) | Derelict is a vertical pistol fight; Longest is shotgun corners; Boarding Action is pure sniper lanes across the gap. |

### Halo 2 and Halo 2: Anniversary maps

| Map | Power weapons and powerups | Power positions (callouts) | Bot notes |
| --- | --- | --- | --- |
| Lockout | Sniper on the sniper tower (S2); shotgun at bottom mid; sword in the Library; overshield under the ramp (default) | Sniper tower (S1, S2, S3), BR tower (BR1, BR2, BR3), Library, Elbow, Lift | Hold S2 and BR2 together; the two towers cross-cover. Never hold Library alone (two entrances plus the lift). Bottom mid is a grenade trap. |
| Midship | Energy sword on the top-mid ring; needlers and carbine on the sides; overshield and camo per variant | Top mid (sword spawn), Pink 1 to Pink 3, Carbine side, the base ramps | Small and fast: team shoot across top mid, throw grenades over the center structure, and keep the sword holder off the lifts. |
| Beaver Creek | Sniper on the cliff path beside Blue base; magnum on the Red side; rockets on the rock walkway above the creek; glass base roofs can be broken | Red roof, Blue roof, the rock walkway, the creek tunnel, the sniper path | Hold a roof with the sniper, send one player up the rock walkway for rockets with a teammate covering, and watch the glass: a grenade through the roof kills the camper. |
| Warlock | Overshield and camo on the center platform; power items alternate | Center top, the four corner ramps | Same logic as Wizard: hold two adjacent corners and pinch the center. |
| Ascension | Sniper at the top of the dish tower; rockets on the hidden platform by the dish; Banshee; camo | Dish tower top, the big tower, the bridge, the back lift | Sniper on the tower controls the bridge; rockets counter the Banshee; the back lift is the flank. |
| Sanctuary | Sniper on each team's sniper ledge; rockets near the center ring; overshield | Ring 1 to Ring 3, Rocks, Snipe, the base tops | Mirror map: hold the ring closest to your base and the rocks; rockets decide the center. |
| Ivory Tower | Sword at the bottom lift room; rockets on the top walkway; sniper on the balcony; shotgun | Top walkway, the lift top, the balcony, the glass room | Lift rides are death traps; grenade the lift top before riding. |
| Zanzibar | Sniper on the Camp Froman nest; rockets at the wheel top; shotgun in the base; Warthog, Ghost | Camp Froman, the wheel, the base roof, the beach | Attackers use the Warthog and the beach; defenders hold the base roof and the sniper nest. |
| Coagulation | Sniper on each base top; rockets mid; overshield and camo in caves; Scorpion, Banshee, Warthog, Ghost | Base roofs, mid rocks, the caves, the cliffs | Blood Gulch rules: vehicle crews and base snipers; the tank needs an escort. |
| Headlong | Sniper on the high building; rockets; Warthog, Banshee, Ghost | The crane, the bridge building, the Ghost ramp | Asymmetric: attackers push through the street with the hog; defenders snipe from the building. |
| Turf, Elongation, Backwash, Burial Mounds, Colossus, Containment, Relic, Terminal, Waterworks, Foundation, Gemini | Varies per map (shotguns in Turf and Foundation; snipers and Wraiths on Containment, Relic, Waterworks; sword on Gemini) | Rooftops on Turf; the conveyor belts on Elongation; the big tower on Relic; the lift tops on Colossus | Apply the power-position scoring rules; Big Team maps follow the vehicle rules in section 5. |

### Halo 3 maps

| Map | Power weapons and powerups | Power positions (callouts) | Bot notes |
| --- | --- | --- | --- |
| The Pit | Rockets in the mid tunnel; a sniper at each team's sniper tower; sword at sword spawn; shotgun in shotgun hall; overshield and camo (or MLG custom OS) at the powerup spots | Sniper towers, Sword room, Green (OS) side, Needle hall, Training yard, Long hall | Open the match by rushing rockets with grenades bounced off the inside walls; the sniper holds its own tower; use sword and shotgun to flank a camping sniper ([Prima Pit guide](https://primagames.com/eguides/halo-3-odst-eguide/multiplayer/multiplayer-maps/the-pit)). |
| Guardian | Sniper on the sniper tower (S1 to S3); hammer at the bottom (Hammer); shotgun at Blue room; mauler; camo at the camo spawn | Sniper tower, Gold lift top, Blue room, Elbow, Green, the Top mid (Snipe 3) | Vertical: hold S2/S3 and Gold with a BR each; bottom (Hammer, Camo) is for flankers only. Drop down to escape, never climb into a held room. |
| Construct | Sniper on the top sniper tower; laser on the lower level; sword at bottom center; camo on top (after 2:00 in MLG) | Top mid (sniper tower), Gold lift, Purple lift, Street, Bottom mid | Top controls everything: hold top and the lift tops. The laser user should fire down into Street from top. |
| Narrows | Sniper at each base top; rockets at bottom mid under the bridge; overshield and camo at the man cannon landings | Base tops, Top mid, Bottom mid, the man cannons | Snipers trade across the bridge; rockets rush is a coin flip, so send two. Man cannon landings are predictable: pre-aim them. |
| Heretic (Midship) | Sword, shotgun | Top mid, Pink side, Carbine side | See Midship. |
| Valhalla | Laser at the mid rock; sniper at each base; missile pod; Warthog, Mongoose | Base top, Laser rock, the hills, the river caves | The laser decides the vehicles; one bot holds the laser from high ground, the rest crew the hog. |
| High Ground | Sniper in the bunker; rockets on the beach side; laser in the base; shotgun; Warthog | The bunker, the gate, the pipe tunnel, the base roof | Attackers open the gate with the switch under cover; defenders hold the bunker sniper and the roof. |
| Last Resort (Zanzibar) | Sniper at Camp Froman; laser in the base; shotgun; Warthog, Mongoose | Camp Froman, the wheel, the base roof, the beach | Same as Zanzibar; the laser from the base roof denies the hog. |
| Standoff | Laser mid; rockets mid; Warthogs | The bases, the mid rocks, the side bunkers | Open map with two hogs each: the laser carrier wins. |
| Snowbound | Sniper, laser and shotgun in and around the caves; Ghost | The caves, the base interiors, the lift | Shotgun owns the caves; the laser denies the Ghosts. |
| Sandtrap | Laser, rockets, missile pod; Elephants, Banshee, Warthog, Chopper, Prowler, Ghost | The Elephants, the mid temple, the top of the ruins | Board the Elephant as a team; the Chopper rams everything. |
| Blackout (Lockout), Citadel, Cold Storage, Ghost Town, Orbital, Assembly, Epitaph, Isolation, Rat's Nest, Avalanche, Foundry (Amplified, Onslaught), Sandbox | Per the timer table above (sniper, rockets, shotgun, hammer, laser, mauler, sword by map) | Blackout mirrors Lockout; Citadel and Assembly are tower-and-ring maps; Rat's Nest and Avalanche are vehicle loops | Apply the scoring rules; use the timer table for spawn counting. |

### Halo: Reach maps

Reach maps are drawn around sprint, jetpack and bloom; power spots are a bit further from each other than in Halo 3. Layouts are the default playlist versions (approximate; verify in tags).

| Map | Power weapons and powerups | Power positions (callouts) | Bot notes |
| --- | --- | --- | --- |
| Countdown | Sword at the bottom-mid lift room; shotgun; sniper at each team's ledge; rockets or grenade launcher per variant | Top mid (the bridge), the lifts, the two sniper ledges, Bottom mid | Watch the lifts; jetpackers over the mid are easy needler targets. |
| Zealot | Sword at the bottom; concussion rifle; grenade launcher; the low-gravity space section above | Top mid, Blue and Red rooms, the space deck | The space deck is a camping spot that the bot should avoid in objective games. |
| Reflection (Ivory Tower) | Sword at the bottom lift room; rockets on the top walkway; sniper on the balcony; shotgun | Top walkway, Lift top, the balcony, the glass room | Same as Ivory Tower; jetpack lets the bot skip the lift. |
| Sword Base | Sniper on the top ledge; sword at the top; shotgun; grenade launcher | The top floor, the long hall, the two lifts, the catwalk | Vertical with one long hall: hold the top, deny the lifts. |
| Pinnacle (Ascension) | Sniper on the tower; rockets; concussion rifle | Tower top, the big tower, the bridge | See Ascension. |
| Asylum (Sanctuary) | Sniper at each team's snipe; rockets near the center | Ring 1 to 3, Rocks, Snipe | See Sanctuary; MLG Sanctuary is the competitive version. |
| Powerhouse | Sniper; rockets at bottom mid; shotgun | The powerhouse roof, the dam, the Blue base rooftop, the creek bed | Asymmetric; the roof sees most of the map. |
| Boardwalk | Sniper on the overlook; shotgun; concussion rifle | The overlook balcony, the long street, the arcade interiors | Long street means DMR pacing. |
| Hemorrhage (Blood Gulch) | Sniper at each base; laser mid; Warthogs, Scorpion, Ghosts, Revenant, Wraith, Banshee per variant | Base roofs, the caves, the mid rocks, the cliff ledges | Plasma launcher and laser from the caves; the tank needs an escort. |
| Spire, Paradiso, Breakpoint, Tempest, Highlands | Falcons, Banshees, Warthogs, Ghosts, Revenants; lasers and rockets | The Spire top, the Paradiso center hill, the Breakpoint bases | Big Team rules from section 5. |
| Forge World variants (The Cage, Pinnacle, Paradiso, Uncaged) | Per variant | Per variant | Read tags; the scoring rules apply. |

### Halo 4 maps

Halo 4 puts most power weapons in ordnance drops, so fixed spawns matter less than in older games. The bot should listen for ordnance announcements and treat each drop as a timed objective.

| Map | Fixed power items (default) | Power positions (callouts) | Bot notes |
| --- | --- | --- | --- |
| Haven | Mid ordnance (often sword or scattershot); random side drops | Top mid (the ring), the two lifts, the side rooms, Bottom mid | Circular map: hold the top ring and the lift exits; jump down to reset. |
| Adrift | Mid ordnance (often rockets or scattershot) | The center hall, the two outer walkways, the lifts | Long sightlines down the outer walkways favor DMR. |
| Abandon | Sniper or sword at the top | The tower, the ramps, the jungle paths | Vertical with a tower: hold the tower and the ramp heads. |
| Solace | Rockets or binary rifle at mid | Top mid, the side ledges, the base balconies | Mirror map; team shoot across mid. |
| Complex | Sniper, rockets | The roof, the long hall, the courtyard | Asymmetric with a roof that sees the yard. |
| Ragnarok (Valhalla) | Laser mid; sniper at each base; Mantis, Warthog, Ghost, Banshee | Base tops, Laser rock, the hills, the river | Laser and railgun decide the Mantis fight. |
| Exile | Scorpion, Warthog, Ghost, Banshee, Mantis; rockets, laser | The center fortress, the cliff ledges, the Scorpion spawn | The tank with an escort controls the ring road. |
| Longbow, Meltdown, Vortex, Wreckage, Harvest, Shatter | Big Team vehicles and lasers | Bases and center structures | Section 5 rules. |

### Worked example: reading one map (Battle Creek / Beaver Creek)

1. Spawn: the bot is at Red base. Its first decision is the far-side sniper: climb the ladder (CE) or the ramp (Halo 2) on the far side of the map while a teammate watches the creek.
2. With the sniper: return to Red roof (CE) or the sniper path (Halo 2). From there the bot sees the creek, the rock walkway and Blue roof. It shoots anyone on Blue roof or on the walkway, and leaves the roof the moment a grenade lands on it or an enemy reaches the ladder.
3. Rockets timer: at the respawn mark the bot's teammate approaches the rock walkway from the base side, throws a grenade onto the walkway, then grabs rockets while the sniper covers.
4. CTF: a flag carrier runs the creek tunnel, not the open creek; the rocket holder covers the tunnel exit; the sniper holds the roof.

## 8. Game modes and objective logic

The mode changes what a kill is worth. In Slayer every kill is a point; in CTF a kill only matters if it moves the flag. The bot keeps one objective-weight variable per mode and lets it override pure fighting instinct.

### Score-state rules that apply to every mode

| Score state | Bot posture | Behavior |
| --- | --- | --- |
| Team far ahead (lead is more than 20 percent of the score limit) | Conservative | Hold power positions, deny power weapons, do not chase. Let the enemy come. |
| Team slightly ahead | Controlled | Keep map control; take fights only with a teammate in support. |
| Even | Standard | Normal rules; fight for the next power weapon spawn. |
| Slightly behind | Pressure | Push as a group of two or more; contest power weapons early; take trades that favor the team. |
| Far behind, time or score running out | Aggressive | Group up fully and push the objective together; accept risky plays; a loss by 10 and a loss by 15 are the same. |
| Enemy within 3 to 7 points of winning | Sneaky and conservative | Avoid open lanes, crouch off radar, group with teammates, fight only two-on-one, and deny the next power weapon. One more death can end the game. |
| Last 60 s of a timed game and the team leads | Hide and hold | Break line of sight, do not re-engage, hold the objective lead. |

### Slayer and Team Slayer

- Objective: kills. Every death gives the enemy a point, so the bot values its life exactly as much as a kill.
- Prefer two-on-one fights. Rotate as a group between the two or three power positions; never spread across the whole map.
- Control the sniper and rockets or laser on their timers; a team with both usually wins Slayer.
- Spawn awareness: killing an enemy near your side of the map pushes their spawn to the far side; killing all four at once resets them together. After a multi-kill, the whole team should move toward the enemy spawn zone together to trap them.
- When the enemy has a power weapon and the bot does not, play corners at Short band and set up melee and grenade combos; do not peek sightlines.

### Capture the Flag

- Objective: carry the enemy flag home while your own flag is at base. Kills are only useful if they clear the route.
- Role split for a four-bot team: one runner, two escorts (one ahead, one behind), one defender who stays at or near the home flag with a long-range weapon.
- Flag carrier rules: cannot shoot (can melee with the flag in most games; Halo 4 gives a magnum). Use the covered route, not the shortest. Drop the flag to fight only if an escort is dead and the enemy is at Short band; juggle (throw and re-pick) to move faster in CE/H2 when it is safe. In Halo 4 the flag auto-picks up, so the bot must avoid walking over it when it does not want it.
- Escort rules: the lead escort clears the route and calls enemies; the rear escort watches behind. If the carrier dies, the nearest escort picks the flag up immediately rather than finishing a fight.
- Defense rules: the defender holds a spot that sees the flag and the two most likely approach routes with the sniper or BR. Pull the flag back (return it) the instant it is dropped. Do not chase a dropped flag into the enemy's team.
- Lead management: when the team is up by one or two captures, keep one extra defender home and stop sending the runner until the lead shrinks or the enemy flag is safely out of base (a pulled flag is a lead on its own).
- One-flag and Neutral flag: on offense, use the full team; on defense, all four hold the base and the flag stand with power weapons.

### Oddball

- Objective: hold the ball; time in hand is the score. The ball carrier cannot shoot (ball melee is an instant kill).
- The carrier hides in a corner with one entrance that teammates can cover; never in the open. The three others form a ring at Short to Medium band and fight everything that approaches.
- When the carrier is about to die, throw the ball toward a teammate or into the team's side so the enemy must walk into fire to get it.
- Attacking the ball: throw grenades at the holder's corner first, then push as two; the ball carrier is defenseless at Medium band.
- Score rule: when ahead with a safe hold, the team never leaves the hold to chase kills.

### King of the Hill

- Objective: time with a teammate inside the hill while no enemy is inside. Only one bot needs to be inside; the rest cover the entrances from outside the hill's sightlines ([Prima MLG Halo 4 tips](https://primagames.com/news/halo-4-tips-improving-your-play)).
- Moving hills: learn the hill order from the variant; move to the next hill 10 s before it rotates; hold the ground between the current and next hill.
- Crouch inside the hill to avoid radar and grenades; stand on the edge, not the center, to use the hill's cover.
- Contesting: an enemy in the hill stops both scores; one bot enters to contest while the others clear the enemy.

### Assault and Neutral Bomb

- Objective: carry the bomb to the enemy arm point and hold the arm for a few seconds. The arm is the most vulnerable moment: the whole team must be within Short band of the carrier, covering every approach, before the arm begins.
- Disarm: a bot inside the arm radius stops the timer; rush the arm with grenades first.
- The bomb carrier follows flag-carrier rules; neutral bomb has both teams racing to one bomb, so the first fight is over the bomb spawn.

### Territories and Dominion

- Territories: capture by standing inside; defend by holding the sightlines over the territory, not the territory itself. Capture the territories closest to home first.
- Dominion (Halo 4): capture bases, which spawn resupplies and turrets. Hold two bases with two bots each; a base with a fortified turret is a defensive anchor. When a base is lost, retake it as a group.

### Extraction, Juggernaut, Infection, Grifball, Race

- Extraction (Halo 4): arm an extraction site, then defend it until it extracts; the enemy can convert it. Same logic as Assault arm plus KOTH hold.
- Juggernaut: the juggernaut has bonus shields and damage; everyone else teams on them. As the juggernaut, pick off isolated players; never fight three at once. As a hunter, stay in a group and team shoot.
- Infection: survivors hold a one-entrance room with a shotgun and precision weapons and keep the shotgun on the door; zombies rush as a group from two sides and use the sword lunge and camo. Survivors should count ammo and move before they run out.
- Grifball: four hammers and swords around a ball; the carrier hops and runs to the goal, the others swing to clear the lane. Spawn killing is normal; a hammer swing deflects the ball.
- Race: Mongoose or Warthog laps; ignore combat unless it is a kill-on-pass variant.

### Firefight (ODST and Reach)

- Objective: survive waves. The squad holds one defensible area with a single approach for Covenant drops, keeps a health pack route, and rotates who goes out for weapons.
- When a teammate is down and lives are limited, the surviving bots fall back to cover and wait for the respawn rather than pushing into the wave.
- Target priority: Hunters and Brute chieftains with power weapons from range; Elites with plasma pistol charge plus headshot; Jackals from the exposed side; Grunts last unless they carry a fuel rod.
- Skulls: when Catch (extra grenades) or Black Eye (melee to recharge) are active, the bot changes its grenade avoidance and melee aggression accordingly.

## 9. Player skill tiers and play styles

Bots should not all play the same. A skill tier sets how well the bot executes; a play style sets which rules it weights. Both are parameters the scripting agent can set per bot, so a lobby of eight bots feels like eight people.

### Skill tiers

| Tier | Aim (hit chance at Medium band, strafing target) | Reaction time | Rule usage | Typical mistakes to simulate |
| --- | --- | --- | --- | --- |
| Recruit | 30 to 40 percent; rarely headshots | 500 to 700 ms | Fights whatever it sees; ignores timers and objectives half the time | Stands still while shooting, reloads mid-fight, walks into grenades, uses the AR at Long band, chases kills off the objective |
| Regular | 45 to 55 percent; headshots after shields drop about half the time | 350 to 500 ms | Uses range bands and cover; sometimes groups up | Over-peeks, forgets to throw grenades, takes one-on-one fights at even shields |
| Veteran | 60 to 70 percent; consistent headshots | 250 to 350 ms | Full range, cover and team-shot rules; counts one power weapon timer | Occasionally pushes alone; mis-times a grenade |
| Elite | 75 to 85 percent; near-perfect kill times | 180 to 250 ms | Every rule in this guide; counts all timers; calls out | Rare; may commit too hard to map control when the score says to retreat |
| Pro | 85 to 95 percent; perfect strafes and lead | 150 to 200 ms | Everything, plus spawn manipulation and setups | Almost none; tune by capping aim to keep games fair |

Aim should degrade with distance beyond the weapon's band, with the target's strafe speed, with the bot's own movement (sprinting or jumping) and while the bot is taking damage. A Pro bot with a BR at Long band in Halo 3 should still miss sometimes because the weapon spreads; a Recruit with a shotgun at Melee band should still usually hit.

### Play styles

| Style | Weighting | Weapon preference | Position preference | Mode behavior |
| --- | --- | --- | --- | --- |
| Slayer (fragger) | Kills over objective; takes 1v1 fights at even shields; first to rush power weapons | Precision plus rockets or sniper | Power positions, mid control | Escort on CTF, outside ring on Oddball |
| Support (team shooter) | Stays within Medium band of a teammate; focuses whatever the teammate shoots; throws grenades for them | Precision plus plasma pistol or automatic | One step behind the fragger | Rear escort, hill cover |
| Sniper | Holds long sightlines; relocates after two kills or when flanked; feeds callouts | Sniper or beam rifle plus precision backup | High ground with an escape | Flag defender, Oddball long-range cover |
| Rusher (CQB) | Closes distance fast; fights in rooms and around corners; grenade then melee | Shotgun, sword, hammer, mauler, SMG, AR | Rooms, lift tops, teleporter exits | Flag runner, hill contester |
| Objective | Objective weight doubled; takes fights only when they clear the route | Precision plus whatever drops | Objective routes and flag stands | Runner or defender; ball carrier |
| Vehicle | Takes every vehicle; drives for the gunner; keeps the vehicle alive | Precision plus anti-vehicle when on foot | Vehicle lanes, repair spots | Flag taxi, territory capper |
| Defender (anchor) | Never leaves the base side; plays corners and controls one power weapon | Precision plus shotgun or sniper | One entrance rooms, base roofs | Flag defense, bomb disarm, base hold |
| Lone wolf | Flanks through the enemy side; avoids its own team; picks off isolated enemies | Precision plus camo or sword | Back routes, caves, lifts | Distraction in objective games; weakest in Slayer against a grouped team |

### Style and tier interactions the scripting agent should expect

- A Recruit Rusher dies a lot and feeds; that is fine for low-skill lobbies but should be capped to one per team in mixed lobbies.
- An Elite Sniper plus an Elite Support anchor a team; add a Rusher and an Objective bot for a balanced four.
- Lone wolf is a personality for variety, not a winning style; give it to one bot at most.
- Vehicle bots only exist on maps with vehicles; on arena maps they fall back to Slayer style.
- Style should drift with the score: a Slayer bot becomes Objective in the last minute of a close CTF game; a Rusher becomes Defender when the team is far ahead.

### Reading the enemy's style (for counter-play)

- An enemy that holds one spot and gets two kills from it is a Sniper or Defender: flank with a Rusher through the escape route, or flood the spot with grenades.
- An enemy that keeps closing distance is a Rusher: back up to Medium band, throw a grenade at the corner they must round, and team shoot.
- An enemy that always has a power weapon is a Slayer on timers: contest the next spawn 15 s early with two bots.
- An enemy that never shoots back from the flag route is an Objective runner: kill the escorts first, then the runner.

## 10. Bot brain decision framework

The bot is a priority stack evaluated every tick (about 10 times per second): survival first, then the immediate threat, then the objective, then the team, then map control, then roaming. The first level whose condition is true decides the action; lower levels only run when nothing above them fires.

&#91;embedded content: bot priority stack · 6 levels, re-evaluated every tick\]

A bot with its shield down never thinks about the flag timer; a bot with nothing in sight thinks about the next rocket spawn.

### Perception inputs the bot needs every tick

| Input | Source | Used by |
| --- | --- | --- |
| Own shield and health, as a fraction | Player state | Survive, Immediate threat, every scenario in section 11 |
| Own weapons, ammo in magazine and reserve, grenades by type | Inventory | Weapon band checks, reload timing, combo choice |
| Own position, facing, movement state (sprinting, crouching, in vehicle, carrying objective) | Player state | Everything |
| Visible enemies: position, distance band, weapon, shield state, movement, facing | Line of sight test each tick | Immediate threat, engagement scenarios |
| Last known enemy positions with a timestamp (decay after 8 s) | Memory | Pre-aim, grenade prediction, hunting |
| Radar contacts (bearing and rough distance) | Motion tracker | Corner checks, ambush detection |
| Sounds: gunfire, grenade bounce, laser charge, vehicle engine, footsteps, sword lunge | Audio events | Immediate threat, retreat triggers |
| Teammates: position, shield state, current target, role, alive or respawn timer | Team state | Team support, objective roles, grouping |
| Objective state: flag positions, ball holder, hill location and timer, bomb state, territory owners | Game state | Objective level |
| Score, score limit, time remaining | Game state | Score posture (section 8) |
| Power weapon and powerup timers, who holds each power weapon | Pickup events plus timers | Map control |
| Map data: power positions with scores, cover points, routes, chokepoints, lifts, teleporters, health packs | Pre-computed per map (section 7) | Map control, retreat, objective routing |
| Game profile: title, variant rules (radar on, sprint, loadouts, bleed-through, boarding) | Match start | Rule gating |

### Threat scoring

For each visible enemy, compute a threat score and fight the highest first:

- Base threat by weapon: power weapon in its band = 100; precision at Medium = 60; automatic or CQB at its band = 70, out of band = 20; vehicle with a gunner = 120; sniper at Long = 90.
- Multiply by proximity: Melee band 1.5, Short 1.2, Medium 1.0, Long 0.7, Extreme 0.4.
- Multiply by enemy shield: full 1.0, popped 0.6 (a weak enemy is a kill, not a threat, but is also the fastest removal).
- Multiply by facing: enemy aiming at the bot 1.3, aiming at a teammate 1.0, facing away 0.5.
- Add 40 if the enemy carries the objective (flag, ball, bomb).
- Add 30 if a teammate is already shooting this enemy (focus fire).

The bot shoots the highest score. It only switches targets when a new enemy scores at least 25 percent higher, which prevents flip-flopping between two targets and killing neither.

### Engagement decision

Given the chosen target, compare the bot's weapon band to the distance band and apply section 4:

1. In band, shield advantage or equal: fight, strafing, from cover if available.
2. In band, shield disadvantage: fight only if a teammate is supporting or the enemy is already damaged; otherwise reset behind cover and re-peek.
3. Out of band, enemy is closer than the bot's band (bot has a sniper, enemy at Short): swap weapon if the secondary fits, else retreat to the band while shooting.
4. Out of band, enemy is farther than the bot's band (bot has a shotgun, enemy at Medium): break line of sight and close through cover, or disengage to a corner and wait.
5. Enemy has a power weapon in band and the bot does not: do not take the fight; break line of sight, call it, regroup.

### Posture variable

The score-state table in section 8 and the skill tier in section 9 combine into a single posture value from 0 (hide) to 1 (all-in). Posture scales the shield threshold at which the bot retreats, the willingness to push alone, and the distance it will travel for a power weapon. Default 0.5; far ahead 0.3; far behind with time running out 0.9; enemy one kill from winning 0.2.

### State machine

The six stack levels map to seven movement states the scripting agent can implement directly: Retreat (to the nearest cover point breaking line of sight), Fight (strafe and shoot in place or from cover), Close (approach through cover to the weapon band), Hunt (move toward last known enemy position with pre-aim), Objective (route to or hold the objective per section 8), Control (route to a power position or timed pickup), and Roam (patrol route with resupply). Transitions happen whenever the stack picks a different level, with a minimum dwell of 0.5 s to avoid jitter, except that Retreat can interrupt anything instantly.

## 11. Scenario library part 1: engagement, health, grenades, melee

Each row is Situation → Decision → Why. The scripting agent should treat the Situation as the condition to test, the Decision as the action, and the Why as the generalization rule for cases not listed. Band names are from section 1; weapon facts from section 4.

### Weapon-band engagement scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Bot has an assault rifle; enemy appears at Medium band with a precision weapon | Do not trade. Break line of sight and move through cover to Short band, or swap to a precision weapon on the ground | The AR loses every Medium trade to a BR, DMR or pistol; it only wins at Short with a melee finish |
| Bot has an assault rifle; enemy at Short band with a shotgun or sword | Back off while firing, keep an obstacle between them, throw a grenade at their feet; if they keep closing and the bot's shield is full, melee as they arrive | AR damage at Short is good, but the shotgun and sword one-shot at Melee band, so the bot must stay at 10 to 30 ft |
| Bot has an assault rifle; enemy at Long band | Ignore them unless they are the objective; move to cover and reposition | AR spread makes Long band shots wasted ammo and reveals position |
| Bot has an SMG (single); enemy at Short band | Fire while closing to Melee band and finish with a melee | A single SMG needs almost a full magazine; SMG plus melee is the real kill |
| Bot has dual SMGs; enemy at Short band, no shotgun or sword | Fire both at the body, strafing; this is the fastest Short-band kill in Halo 2 | Dual SMGs shred at Short; they are the buffer weapon for rooms |
| Bot has dual SMGs; enemy at Medium band or beyond | Drop to a single weapon (or swap) and get to cover; do not fight | Dual wielding cannot zoom, melee or throw grenades, and SMG recoil misses at Medium |
| Bot has dual weapons; grenade needed or melee needed | Drop the secondary weapon (release dual wield) first | Grenades and melee are disabled while dual wielding |
| Bot has a BR or DMR; enemy at Medium band | Standard fight: strafe, zoom if the enemy is static, land body shots then the headshot | This is the weapon's band; win by accuracy and movement |
| Bot has a Halo 3 BR; enemy at Long band | Pace bursts, aim slightly ahead of strafe, prefer to close to Medium; if the enemy has a carbine or sniper, leave the sightline | Halo 3 BR spread makes Long shots unreliable; the carbine and sniper beat it there |
| Bot has a Reach DMR; enemy at Long band | Fire one shot, wait for the reticle to shrink, fire again (about 0.5 s pacing) | Bloom punishes rapid fire; paced shots land |
| Bot has a precision weapon; enemy at Melee band with a CQB weapon | Melee immediately if the enemy's shield is already weak; otherwise jump back and shoot while retreating; never reload | At Melee band the CQB weapon wins the gunfight; melee and distance are the only counters |
| Bot has a shotgun; enemy at Medium band | Do not fire; hide behind a corner the enemy must round and wait, or disengage | Shotgun pellets do little at Medium and reveal position |
| Bot has a shotgun; enemy at Short band closing | Hold fire until Melee band, fire one shot, melee if they survive | One shot at Melee band kills; shooting early wastes the one-shot |
| Bot has a shotgun; enemy at Short band retreating | Do not chase into the open; throw a grenade to cut off the retreat and return to the corner | Chasing a shotgun into a rifle lane trades the shotgun for nothing |
| Bot has a sword; reticle turns red on an enemy | Lunge immediately | Red reticle means the lunge will connect |
| Bot has a sword; enemy at Medium band in the open | Do not advance in the open; break line of sight and approach through cover, lifts or behind teammates | A BR kills a sword rusher before the lunge connects |
| Bot has a sword; enemy also has a sword at Melee band | Lunge only when reticle is red and the enemy is not mid-lunge; otherwise step back and bait their swing | Sword clashes cancel; whoever swings first into a clash loses tempo |
| Bot has a sword; enemy has a shotgun at Short band | Break line of sight; only lunge from a corner when they are reloading or facing away | Shotgun one-shots the lunge in a straight line |
| Bot has a gravity hammer; enemy at Short band | Close with a strafe and swing when within about 8 ft; swing at the ground to catch jumpers | The hammer's area hit catches anyone near the impact |
| Bot has a gravity hammer; rocket or grenade incoming | Swing at the incoming projectile | The hammer deflects explosives |
| Bot has a sniper; enemy at Long or Extreme band | Scope, wait for the strafe to pause or change direction, headshot; relocate after two shots from the same spot | Sniper kills with one headshot; staying put invites a counter-snipe or a flank |
| Bot has a sniper; enemy at Short band | Swap to the secondary weapon; if no secondary, fire one body shot then melee | A sniper body shot plus melee is a kill; scoping at Short loses |
| Bot has a sniper; enemy at Melee band | Melee first, then one no-scope body shot | Melee strips the shield; one sniper round finishes an unshielded enemy |
| Bot has a sniper; another sniper is scoped on the bot's lane | Leave the lane; re-enter from a different window after 5 s | Trading snipes with a prepared sniper is a coin flip |
| Bot has a beam rifle; two enemies in the lane | One shot each with a pause between; do not double-tap the same target unless the kill is certain | Rapid beam rifle shots overheat it, leaving the bot defenseless |
| Bot has a Spartan laser; enemy vehicle in sight at Medium band or beyond | Charge from cover, track the vehicle's lead, fire; retreat behind cover while it recharges | The laser one-shots vehicles; the charge reveals the bot, so cover matters |
| Bot has a Spartan laser; infantry enemy at Medium band, no vehicles on the map | Only fire if the enemy is stationary, the bot is behind cover, and no teammate can take the kill; otherwise swap to the secondary | The laser's 5 shots are for vehicles; infantry dodge the charge |
| Bot has a Spartan laser; infantry enemy at Short band attacking the bot | Swap to the secondary weapon immediately; if none, melee | The laser charge is too slow for Short band |
| Bot has rockets; enemy vehicle at Short to Long band | Fire at the vehicle; in Halo 2, Reach and Halo 4 hold the reticle on it until the lock tone, then fire; in CE and Halo 3 lead the vehicle | Rockets are the main anti-vehicle weapon; lock-on removes the lead guess |
| Bot has rockets; two or more enemies within 15 ft of each other | Fire at the ground between them | Splash kills a group; this is the best use of a rocket on infantry |
| Bot has rockets; one full-shield enemy at Medium band, teammates nearby | Hold the rocket; let teammates shoot and use the secondary weapon | One rocket on one enemy is a poor trade unless it saves the bot's life |
| Bot has rockets; one enemy at Short band and the bot's shield is down | Fire at their feet (emergency) | Dying with rockets gives the enemy rockets |
| Bot has rockets; enemy at Melee band | Melee or swap; never fire | Rocket self-damage kills the bot |
| Bot has a plasma pistol and a precision weapon; enemy at Short or Medium band | Charge the plasma pistol, hit, swap and headshot; if the enemy reaches Melee band after the charged hit, melee instead | Charged bolt plus headshot or melee is a near-instant kill |
| Bot has a plasma pistol; enemy Warthog, Ghost, Mongoose, Chopper, Mantis or Banshee within Medium band | Charged shot at the vehicle, then board or stick it while stalled | EMP stalls the vehicle for a few seconds |
| Bot has a needler; enemy strafing in the open at Short band | Fire the full burst while backing off | Needles track and supercombine; cover and distance are the enemy's only answers |
| Bot has a needler; enemy behind cover or at Long band | Swap or hold fire | Needles are blocked by cover and dodged at Long |
| Bot has a mauler; enemy at Short band | One shot then melee | One mauler shot plus melee kills a full-shield player |
| Bot has a Boltshot (Halo 4); enemy about to round a corner at Melee band | Hold the charge and release when they appear | The charged Boltshot is a one-hit kill at Melee band only |
| Bot has a railgun; enemy at Medium band standing still or sprinting in a line | Start the charge before peeking, release on target | The slug is hitscan once charged; charging in the open gets the bot shot |
| Bot has a Binary Rifle; enemy at Long band | One body shot; relocate after each shot | The red beam shows the position; one hit kills |
| Bot has a plasma launcher (Reach); enemy Ghost or Warthog at Medium band | Charge 3 to 4 bombs and release on the vehicle | Homing plasma sticks and kills light vehicles |
| Bot has a grenade launcher (Reach); vehicle passing | Fire and hold the trigger; release as the vehicle is over the round | Remote EMP detonation stalls the vehicle for a hijack |
| Bot has a precision weapon; enemy is jetpacking in the open | Shoot; aim the head when they hover | Airborne enemies cannot strafe |
| Bot is holding a mounted turret; a sniper or laser is on the map | Detach after at most 5 s of firing and move | Mounted turrets are stationary targets |

### Health and shield scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Shield fully popped, enemy still shooting, cover within 10 ft | Move to cover immediately (sprint, thrust or evade if available), wait for the recharge (about 5 s plus 2 to 3 s), re-peek from a different edge | One more shot or a melee kills; the recharge resets the fight |
| Shield popped, no cover within reach, enemy at Medium band with full shield | Keep shooting at the head while strafing; the only win is a lucky headshot or the enemy missing | Running in the open is a guaranteed death; shooting at least has a chance |
| Shield popped, enemy at Short band, enemy's shield also low | Melee or finish with the current magazine; do not reload | Whoever lands first wins; a reload loses the race |
| Shield popped, health low (CE, ODST, Reach), fight over | Route to the nearest health pack via covered paths before anything else | Health does not regenerate; a one-shot health state is a liability to the team |
| Attacked by two enemies, turned a corner and survived | Throw a grenade at the corner they must round, back up to the far side of the room, aim at the corner at head height | Attackers chase; the grenade and the pre-aim punish the chase |
| Attacked by two enemies, both chasing, bot has a teammate within Medium band | Run toward the teammate, not away; turn and fight once the teammate has line of sight | Two-on-two beats one-on-two; the bot's retreat baits the enemy into the teammate's fire |
| Near death, no chance of cover, enemy at Short band | Attack the weakest enemy: shoot and melee; throw a grenade at their feet if a kill is unlikely | Taking one enemy down on the way out is the best trade available |
| Near death, no chance of cover, enemy at Long band | Zigzag toward the nearest obstacle and crouch behind it | Long band gives a small window; crouching behind a low obstacle may break the snipe |
| Full shield, enemy with a popped shield visible | Push and finish: this is the highest priority target | A one-headshot enemy is a free kill if taken now |
| Full shield, bot has an overshield | Take fights it would normally avoid, including two-on-one at Medium band; still avoid snipers and rockets | Overshield roughly triples the shield but does not stop a headshot after shields drop |
| Bot's shield is recharging and a teammate calls an enemy approaching | Stay behind cover, aim the entrance, let the teammate take the first shot | Peeking at half shield loses to a full-shield enemy |
| Reach: bot's health bar is low, shield full | Play as if the shield were half: avoid melee trades and grenades | Bleed-through means a melee can kill through a full shield when health is low |
| Bot sees a health pack and is below 70 percent health (CE, Reach, ODST) | Take it unless an enemy has a sightline on it | Health packs are limited; take them when safe |
| Bot takes damage with no enemy in sight | Move perpendicular to the damage direction into cover, then check the radar and the last known enemy positions | Standing still while hit from an unknown angle is death |
| Bot hears a sniper shot nearby | Break the sightline it was in; move to a lane the sniper cannot see | The second shot comes within a second |

### Grenade scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Enemy retreats around a corner or into a doorway | Throw a frag at where they will stop (just inside the door, the first cover point) | Retreating enemies go to the nearest cover; the grenade lands as they stop |
| Enemy known to be camping a room the bot must enter | Throw a grenade in first (bounce off the far wall), then enter while it explodes | Grenades flush campers and strip shields before the gunfight |
| Enemy standing still at Short band with a popped shield | Throw a grenade and shoot; or melee if at Melee band | Grenade finishes an unshielded enemy |
| Enemy group of two or more within 15 ft of each other | Throw a grenade at the center of the group, then shoot the one who moves last | A grenade on a group strips multiple shields |
| Enemy vehicle at Short band and bot has a plasma grenade | Stick it (aim at the hull or the gunner) | A stick kills light vehicles and usually the Warthog's crew |
| Enemy sniper on a known perch within throw range | Throw a grenade onto the perch before peeking | Snipers rarely move; the grenade forces them off |
| Bot is retreating from a chaser | Drop a grenade at its own feet as it rounds a corner, then keep running | The chaser runs into the explosion |
| Enemy in armor lock (Reach) | Throw a plasma grenade so it lands beside them and shoot them the instant the lock ends; do not melee | Armor lock ends after a few seconds and the enemy is vulnerable then |
| Bot has zero grenades and passes a grenade spawn or a dead player's drop | Pick them up | Grenades are a third of the bot's damage |
| Flag or bomb is about to be picked up by an enemy | Throw a grenade onto the objective | The pickup animation and the stop make them an easy hit |
| Enemy is riding a lift or man cannon | Throw a grenade at the landing point timed to their arrival | Landing spots are fixed and predictable |
| Enemy is in a Regenerator or Drop Shield | Throw a grenade inside before pushing | The field does not stop grenades |
| Halo 3: bot has a spike grenade and an enemy is in a narrow corridor | Throw it onto the wall beside them | Spike grenades spray in a cone; corridors trap the spikes |
| Halo 3: bot holds a doorway and has a firebomb | Throw it on the doorway floor when enemies push | Fire blocks the door for several seconds |
| Halo 4: a hill or flag stand is contested | Throw a pulse grenade onto it | Pulse grenades drain shields in a sphere and deny the space |
| Grenade thrown at the bot (sound or visual) | Move away from the landing point, prefer sideways and out of the room; jump over it only if there is no exit | Grenade damage falls off with distance; a few feet is the difference between a popped shield and a death |
| Bot is about to throw while an enemy is at Melee band | Do not throw; melee | Grenades at Melee band damage the thrower |

### Melee scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Enemy at Melee band, enemy's shield at half or less | Melee once | One melee kills a half-shield player in every game |
| Enemy at Melee band, both full shield, bot has a precision weapon | Shoot two or three shots then melee (Halo 2, Halo 3) or melee then one headshot | Shoot-melee or melee-shoot is faster than two melees |
| Enemy at Melee band facing away from the bot | Melee the back (assassination) | Rear melee is an instant kill |
| Enemy at Melee band, bot's shield is lower than the enemy's | Do not melee first; back up and shoot, or throw a grenade at their feet and retreat | A melee trade favors the higher shield |
| Two enemies at Melee band | Melee the weaker one and retreat behind the other's line of fire | Two melee trades in a row loses; one kill then an exit is the best result |
| Enemy with a sword or hammer at Melee band and the bot's shield is full | Melee as they lunge if there is no escape; otherwise jump back | Meleeing a lunging sword can trade; retreat is better |
| Halo 3: bot has a mauler or shotgun at Melee band | Fire once then melee | The combo is faster than two shots |
| Reach: enemy has low health (bleed-through) | Melee even at full shield | Bleed-through lets melee damage pass to health |
| Magazine empty and enemy at Melee band | Melee, do not reload | Reload takes longer than the enemy's melee |
| Bot has the flag or ball and an enemy reaches Melee band | Melee (ball is a one-hit kill; flag melee is strong) | The objective itself is a melee weapon |

### Reload and ammo scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Magazine below a quarter, no enemy in sight | Reload now behind cover | Reloads should happen between fights |
| Magazine empty mid-fight, enemy at Medium band | Swap to the secondary weapon rather than reload | Weapon swap is faster than a reload |
| Magazine empty mid-fight, enemy at Melee band | Melee | See melee rules |
| Reserve ammo empty on the primary | Swap for any precision weapon on the ground when safe; keep an empty power weapon only to deny it, and drop it when a better weapon is available | A weapon with no ammo is dead weight |
| Power weapon has one shot left | Save it for a vehicle or a guaranteed kill; use the secondary for normal fights | The last shot is worth more than a regular kill |
| Plasma weapon overheated | Stop firing, strafe to cover, resume after the vent | Overheat locks the weapon for a second or more |
| Walking over a dropped better weapon with no enemy in sight | Swap (keeping one precision weapon) | Weapon economy rule from section 2 |

## 12. Scenario library part 2: team, objective, map control, vehicles, retreat, respawn

Same format as section 11. These scenarios sit at stack levels 3 to 6 and are where bots stop playing like individuals and start playing like a team.

### Team scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Teammate is shooting an enemy within the bot's Medium band | Shoot the same enemy (team shot) before any other target | Two shooters halve the time to kill |
| Teammate's shield is popped and the enemy is still shooting them | Shoot that enemy and move to give the teammate a cover line; throw a grenade between them | Saving a teammate is a kill denied to the enemy |
| Bot is alone and the nearest teammate is beyond Medium band | Move toward the team through cover before taking fights | Lone bots lose two-on-ones |
| Bot is alone and all teammates are dead | Hide in a defensible corner off radar (crouch) until the first teammate respawns; fight only if found | A one-versus-many pushes feeds the enemy and spawns the team far away |
| Teammate calls an enemy at a position the bot can see | Pre-aim the position at head height and move to a cover edge that sees it | Callouts turn reaction fights into first-shot fights |
| Teammate is a flag carrier or ball holder | Stay within Short band of them, facing away from them, toward the most likely threat | Escorts cover what the carrier cannot shoot |
| Teammate holds the sniper or laser | Protect their position from flankers; do not stand in their lane | Power weapon holders win games if kept alive |
| Bot picks up a power weapon but a teammate with a better aim profile (sniper style) is near | Keep it unless the team logic assigns weapons by style; then drop it for them when safe | Styles and tiers from section 9 should decide who carries what |
| Two bots approach the same dropped power weapon | The closer bot takes it; the other covers | Two bots standing on one weapon is a double kill for a grenade |
| Teammate dies at a position | Assume the killer is still there; do not walk into the same spot; approach from a different angle with a grenade first | Killers hold angles that worked |
| Enemy team is grouped (three or more within 20 ft) | Do not push; throw grenades and rockets at the group; wait for them to split | A group with team shot kills anything that peeks |
| Enemy team is split (one isolated) | Group up on the isolated one with two bots and kill them, then rotate to the next | Picking off isolated players wins Slayer |
| The team has killed all enemies at once | Move together toward the enemy spawn side and set up on the power positions near it | Spawn trapping keeps the enemy on the back foot |

### Objective scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| CTF: team is up by two captures | Keep two defenders home, hold the own flag with a sniper lane and a shotgun corner; stop sending the runner until the lead is one | The flag at home is the lead; a failed run can turn into an enemy capture |
| CTF: team is behind and the enemy flag is at their base | Push as four: two escorts, one runner, one back at Medium band shooting from high ground | A full push is the only way to break a defended flag |
| CTF: enemy flag carrier spotted | Shoot the carrier first; teammates shoot the escorts; a bot with rockets or a sniper takes the carrier | A dead carrier drops the flag and resets the run |
| CTF: own flag dropped in the open | Return it only if no enemy has a sightline on it, or a teammate suppresses; otherwise hold the sightline and kill whoever tries to pick it up | Running onto a contested flag is a death |
| CTF: bot is the carrier and an escort dies | Keep moving on the covered route; drop the flag only if an enemy is at Short band and the bot must fight | The flag moves the score; a fight with the flag down is a last resort |
| CTF: bot is the carrier with the flag at home base (own flag taken) | Wait near the capture point under cover until the own flag is returned; call for teammates to return it | Most variants require the own flag to be home to score |
| Oddball: bot has the ball and an enemy enters the room | Melee if at Melee band; otherwise throw the ball into the team's side and fight with the secondary weapon | Ball melee is a one-hit kill; a dead carrier in the open hands the ball over |
| Oddball: team is ahead and holding | No one leaves the hold; rotate shooters, keep grenades for the entrance | Holding time is the score |
| KOTH: hill is empty and no enemies in sight | One bot enters and crouches at the edge; others take the surrounding high ground | One is enough to score; more inside is more grenade damage |
| KOTH: enemy is in the hill | One bot contests by entering (stops their score) while the others kill from outside | Contesting stops enemy points instantly |
| KOTH: hill moves in 10 s | Move toward the next hill now, hold the ground between | Arriving first wins the next hill |
| Assault: bot has the bomb at the arm point | Arm only when at least two teammates are within Short band and covering the approaches; otherwise wait behind cover | The arm is long and the carrier is defenseless |
| Assault: enemy is arming | All bots rush the arm point with grenades first | The arm must be interrupted or the round is lost |
| Territories: team owns three of five | Hold the three with the sightlines; send two to contest the fourth only when the third is secure | Over-extending loses the owned territories |
| Dominion: base lost | Retake as a group of two or more; never alone | Base turrets and resupplies punish lone attackers |
| Infection: survivor with a shotgun and a door | Hold the door at Short band with teammates behind; move when ammo runs low | Zombies lunge; the door is the only kill lane |
| Infection: zombie | Approach with teammates from two sides; use camo and lunge; do not run straight down a hallway | Straight lines are shotgun lines |
| Juggernaut: bot is the juggernaut | Hunt isolated players; retreat from groups | Three-on-one loses even with bonus shields |
| Grifball: bot has the ball | Jump and run the shortest lane; teammates swing ahead | The ball carrier is faster when hopping |
| Score: enemy needs 7 or fewer kills to win | Posture 0.2: crouch off radar, group with teammates, fight only two-on-one, deny the next power weapon spawn, never cross open lanes | A few deaths end the game; map control is the only safe way to kill |
| Score: team needs 3 or fewer kills to win | Hold power positions, let the enemy come; take only trades at even or better shields | The enemy must push; defenders win pushes |
| Time: 30 s left, team leading | Break line of sight, hide, do not re-engage | A kill does nothing; a death might |
| Time: 30 s left, team behind | Posture 0.9: push together, use every power weapon, accept trades | Only kills matter now |

### Map control scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Power weapon spawns in 15 s and the team does not hold it | Send two bots to the spawn: one grabs, one covers the approach with grenades ready | Contested power weapon spawns are two-player fights |
| Power weapon spawns in 15 s and the enemy holds the area | Throw grenades onto the spawn as it appears; do not walk onto it; kill the grabber | Denying the pickup is as good as taking it |
| Powerup (OS, camo) spawning | Same as power weapon; the bot with the lowest shield takes the OS | OS on a weak bot is a reset; camo goes to the sniper or shotgun style |
| Power position empty and no threats | Move there with cover-to-cover movement and hold it facing the most likely approach | Empty power positions are free map control |
| Power position held by the enemy | Flood it with grenades from outside its sightlines, then push with two from the escape route side | Taking held ground needs grenades and numbers |
| Bot holds a power position and has been there 20 s with no enemy sighted | Check radar and the last-known-enemy list; relocate to an adjacent position if the enemy is nowhere, because they are flanking | Static holds get flanked |
| Enemy sniper on a known perch | Avoid their lanes; send a Rusher through the escape route; or trade with a sniper from a different window | Snipers control lanes; remove them from the side |
| Lift or man cannon ahead with enemies near the landing | Do not ride it; use the ramp or wait for teammates | Lift landings are pre-aimed by any decent player |
| Teleporter ahead | Throw a grenade through first if an enemy was last seen beyond; otherwise go through crouched and sidestep on exit | Teleporter exits are ambush points |
| Halo 4 ordnance drop announced | Move to it if the route is covered; grab if safe, else deny by killing the grabber | Ordnance is the Halo 4 power weapon economy |
| Enemy has every power weapon | Play corners, group, bait the rocket and laser with a hologram or a peek, then push during their reload | Power weapons have long reloads and limited ammo |

### Vehicle scenarios (on foot)

| Situation | Decision | Why |
| --- | --- | --- |
| Enemy Scorpion approaching, bot has no anti-vehicle weapon | Hide behind terrain it cannot shoot through and that it cannot drive over; move to the nearest laser or rocket spawn through cover; do not fire at it with a rifle | The tank one-shots anything it sees; rifles only reveal position |
| Enemy Scorpion at Short band with no escort, bot has a plasma grenade or a plasma pistol | Approach from behind or the side, stick it twice or EMP it, then board and plant a grenade | The tank is blind close in and behind |
| Enemy Warthog charging at the bot | Sidestep behind an obstacle, then shoot the gunner from behind the hog as it passes | Splatter is the hog's weapon; the gunner cannot turn fast enough to the rear |
| Enemy Ghost boosting at the bot | Sidestep at the last moment (evade or thrust if available), melee the side, or stick it | A boosting Ghost cannot turn; running straight is death |
| Enemy Banshee overhead | Stay under overhangs; shoot only with a laser, rockets, plasma launcher or missile pod; precision fire only when it hovers | Banshees die to lock-ons and lasers, not to rifles |
| Enemy Wraith shelling the team | Move while the mortar is airborne; close in on foot through cover and board | The mortar is slow and the Wraith is helpless at Short band |
| Enemy Mantis walking at the team | EMP with a plasma pistol or pulse grenade, then board; railgun or laser from Long band; keep 15 ft away from its stomp | The Mantis is strong frontally and slow; EMP and boarding kill it |
| Enemy vehicle stalled by EMP within Short band | Board it | Boarding is a free kill and often a free vehicle |
| Enemy vehicle flipped | Shoot or melee the crew while they climb out | Crew exiting are stationary targets |
| Friendly vehicle empty and the bot's style is Vehicle, map is Big Team | Take it with a gunner; wait up to 5 s for a teammate | A one-man hog is a gift to the enemy |
| Friendly Warthog has a driver and no gunner | Take the turret | A hog without a gunner has no damage |
| Bot is the driver and the gunner dies | Retreat to base to pick up a new gunner; do not drive on alone | See above |
| Bot is in a vehicle that is smoking | Drive behind cover and bail out; return to fight on foot | A burning vehicle explodes with the crew |
| Bot is in a vehicle and hears a laser charge or a rocket lock tone | Turn hard behind cover or bail immediately if no cover is within 2 s | The laser beam is instant; rockets lock and track |
| Bot is driving and an enemy on foot reaches Melee band | Drive away or splatter; never stop next to infantry | Stopping invites boarding |

### Retreat and reset scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Losing a fight (enemy shield higher after the first exchange) | Back out of line of sight before the next shot, recharge, re-peek from a new edge | Resetting a bad fight is free; finishing it costs a death |
| Retreating with an enemy chasing | Drop a grenade at the corner, run to the nearest teammate, turn and fight together | Chasers die to grenades and two-on-ones |
| Retreating and a lift or ladder is the only route | Take it only if the enemy is not within Medium band; otherwise fight from the base of it | Climbing exposes the back |
| Retreat path crosses an open lane with a known sniper | Crouch-walk behind low cover or take the long route | Open lanes with snipers are death |
| Retreated and recharged, enemy did not follow | Expect them around the corner; grenade the corner and re-peek at head height | Enemies who do not chase are waiting |
| Shield recharging and radar shows a dot approaching | Face the dot's approach with a grenade ready; crouch to disappear from their radar | Radar gives a few seconds of warning |

### Respawn and spawn scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Bot just respawned, team alive and holding | Move to the team through cover; pick up a precision weapon on the way | Rejoining the group is the first job |
| Bot just respawned, team all dead or dying | Hold the spawn area's best cover and wait for the next respawn; do not push | A lone fresh spawn versus a grouped enemy is another death |
| Bot just respawned next to an enemy | Fight immediately with full shield; prefer melee and grenade combos | Fresh spawns have full shields; the enemy may not |
| Bot just respawned and an enemy power weapon is being used nearby | Avoid the lane; flank through the back route | Spawn pushes into a power weapon feed |
| Enemy just respawned near a held power position | Push the spawn with two bots while they are still unarmed with grenades | Fresh spawns have no grenades or power weapons |
| Variant has respawn timers of 10 s or more | Value own life more (posture minus 0.1) | Long respawns mean each death loses more time on the objective |

### Halo 3: ODST and Firefight scenarios

| Situation | Decision | Why |
| --- | --- | --- |
| Wave begins, squad alive | Hold the chosen position: one bot on each approach, pistol and plasma pistol ready | ODSTs have no shields; cover and headshots are the whole game |
| Teammate down, lives remain | The rest fall back to cover and hold until the respawn; nobody pushes into the wave | Pushing without numbers loses lives |
| Stamina gone (red screen), health dropping | Break line of sight and wait for the stamina to recharge; use a health pack only if health is below half | Stamina recharges; health does not |
| Elite or Brute at Medium band | Plasma pistol charge, then one pistol headshot | The combo kills shielded enemies in two actions |
| Brute Chieftain with a hammer or fuel rod | Retreat to Long band; sniper, rockets or laser; never melee | Chieftains one-shot at Melee band |
| Hunters | Shoot the exposed back after they charge; use rockets or laser; keep moving around them | Hunters are only weak from behind |
| Jackals with shields | Shoot the hand, then the head; or flank the open side | The shield blocks everything frontal |
| Drop pods or Phantoms arriving | Reposition so the drop zone is in front of the squad's lines, not behind | Drops behind the squad flank it |
| Ammo low on the pistol | Swap for a Covenant carbine or plasma rifle from a dead enemy between waves | Headshot weapons are the priority |
| Bonus round or skull activation | Switch to area denial (grenades, hammer) for Grunt bonus rounds; keep melee for Black Eye | Rounds change the optimal weapon mix |

### Catch-all generalization rules

When a situation is not listed, the scripting agent applies these in order:

1. Is the bot going to die in the next second? Survive first (cover, dash, retreat).
2. Can the bot kill in the next second (enemy unshielded at the weapon's band)? Take the kill.
3. Does the mode say to be somewhere else? Go there with teammates.
4. Is a teammate fighting? Team shoot.
5. Is a timer about to pay out? Contest it with two.
6. Otherwise hold the best power position the team does not already have and watch its approaches.

## 13. Competitive habits to imitate, and sources

The difference between a good bot and a believable one is a handful of habits pros do without thinking. The scripting agent can turn each into a rule that only the Veteran tier and above runs.

### Pro habits as rules

| Habit | Rule for the bot | Where it came from |
| --- | --- | --- |
| Count every timer out loud | Keep a running clock per power weapon and powerup; be at the spawn 15 s early with a teammate | MLG settings publish exact timers (section 7); timing guides for Halo 3 competitive play stress memorizing them ([Halo 3 tips](https://futurefive.com.au/story/halo-3-9-t-op-tips)) |
| Never charge in a straight line | Any approach or retreat is a strafe, never a straight run; mix short and long strafes; backpedal-strafe against shotguns | Halo 3 strafing community guide ([bungie.net strafing guide](https://www.bungie.net/en-US/Forums/Post/1480128)) |
| Lead the shot in Halo 3 | Aim slightly ahead of a strafing target at Medium and Long band with the BR; hitscan assumptions from Halo 2 do not apply | Same Halo 3 tips article |
| Shoot then beat down | Against a half-shield enemy at Melee band, one shot then melee beats two melees | Same Halo 3 tips article |
| Rockets at close to medium range | Halo 3 rockets are slow; fire them at Short and close Medium band, not at Long | Same Halo 3 tips article |
| One player in the hill | Only one bot stands in the hill; the others cover from outside | Prima MLG Halo 4 tips ([Prima](https://primagames.com/news/halo-4-tips-improving-your-play)) |
| Power weapon holder does not run the flag | The bot with rockets or sniper escorts; a bot with a loadout weapon runs | Same Prima article |
| Set up on the next hill early | Hold ground near where the hill moves next | Same Prima article |
| Ordnance drop in cover | Call a Halo 4 ordnance drop out of sight because the drop is loud and visible | Same Prima article |
| Pick a powerup over a redundant power weapon | If the team already holds a power weapon, take the OS or damage boost from ordnance | Same Prima article |
| Grenade the rocket rush | On The Pit and similar maps, bounce grenades off interior walls at the rocket spawn as the match starts | Prima Halo 3 Pit map guide (section 7) |
| Sniper camps its own tower, flankers remove enemy snipers | The sniper holds a tower that sees the enemy's power weapon routes; a sword or shotgun bot flanks the enemy sniper | Same Pit guide |
| Keep rockets ammo out of enemy hands | On Beaver Creek, re-grab the rocket spawn every cycle even when not needed | Halo 2 strategy guide, Beaver Creek ([halo.bungie.org](https://halo.bungie.org/gameplay/stratguide/matchmaking/beavercreek.html)) and Halopedia |
| Name the map | Every position has a callout; teammates learn enemy position, weapon and shield from one call | Halo 2 competitive coaching interview ([halo.bungie.org](https://halo.bungie.org/gameplay/stratguide/articles/prodrev_consolepro.html)) |
| Fire first wins Halo 2 | Fights last under 1.5 s; the first accurate shot usually wins, so pre-aim corners and lanes | Halo 2 weapons analysis ([rampancy.net](https://rampancy.net/hpbguideh2/weapons)) |
| Precision plus one other weapon | Never carry two weapons for the same job; precision plus power or precision plus automatic | Community tier list reasoning ([almarsguides](https://almarsguides.com/computer/games/halomasterchiefcollection/misc/Lists/)) |
| Plasma strips, kinetic finishes | With a plasma weapon and a kinetic weapon, use the plasma to break the shield and the kinetic to headshot | General Halo sandbox rule, stated in the Halo Infinite tip set and true in every MCC title |
| Play the objective even when losing the kill count | A team behind in kills wins objective games by committing to the objective together | Same |

### Tuning the guide into a bot

1. Load the game profile and read the map's weapon placements, respawn timers and power positions from the scenario tags; fill the section 7 tables with real coordinates.
2. Pre-compute cover points, chokepoints, lift landings, teleporter exits and health packs per map.
3. Give each bot a tier and a style from section 9; let the style weight the stack levels in section 10.
4. Encode every scenario row in sections 11 and 12 as a condition and action; keep the Why text as a comment so later edits generalize correctly.
5. Tune by watching: a bot that dies in the open is missing a retreat or cover rule; a bot that never gets kills is missing an engagement band rule; a bot that loses CTF while winning kills is missing a score-posture rule.

### Sources consulted

- Halopedia weapon gameplay pages for shots-to-kill and red reticle ranges, for example the [Magnum gameplay page](<https://www.halopedia.org/Magnum_(gameplay)>).
- Halopedia [MLG playlist](<https://www.halopedia.org/MLG_(playlist)>) for competitive weapon and powerup respawn timers.
- bungie.net [Halo 3 MCC weapon spawn times](https://www.bungie.net/Ne/Forums/Post/106060001?page=0) for per-map default timers and the pickup-delay rule.
- Prima Games [Halo 3 The Pit map guide](https://primagames.com/eguides/halo-3-odst-eguide/multiplayer/multiplayer-maps/the-pit) and [Halo 4 MLG tips](https://primagames.com/news/halo-4-tips-improving-your-play).
- halo.bungie.org Halo 2 strategy guide: [Beaver Creek](https://halo.bungie.org/gameplay/stratguide/matchmaking/beavercreek.html) and the [Console Pro interview](https://halo.bungie.org/gameplay/stratguide/articles/prodrev_consolepro.html).
- Halopedia [Beaver Creek](https://halopedia.org/Beaver_Creek) for map layout and the rocket-control advice.
- bungie.net [Halo 3 strafing guide](https://www.bungie.net/en-US/Forums/Post/1480128).
- FutureFive [Halo 3 top tips](https://futurefive.com.au/story/halo-3-9-t-op-tips).
- rampancy.net [Halo 2 weapons analysis](https://rampancy.net/hpbguideh2/weapons).
- almarsguides [MCC weapon tier lists](https://almarsguides.com/computer/games/halomasterchiefcollection/misc/Lists/).
- Tom's Guide [Halo: Reach PC multiplayer tips](https://www.tomsguide.com/news/halo-reach-pc-multiplayer-tips) for bloom and map memorization.

Weapon and map facts not tied to a link above are from the games as shipped in MCC and long-standing community knowledge; where a number is an estimate it is marked approximate in the text.
