# Game mode playbooks

Every multiplayer and Firefight mode in MCC, written as what the bot values, which roles the team fills, how the match is played in phases, and where it goes wrong. The main tab's section 8 is the summary; this is the full version.

## Slayer family

Slayer is the simplest mode and the hardest to play well, because there is no objective to hide behind: every death is a point for the enemy, so the bot's life is worth exactly one kill. Team Slayer is won by map control, trades that favor the team, and spawn control; FFA is won by picking fights nobody else is in.

### Scoring and win conditions

| Variant | Score limit (typical) | Time limit | Notes |
| --- | --- | --- | --- |
| Team Slayer 4v4 | 50 kills (CE, H2, H3, Reach); 600 points (H4, 10 per kill) | 10 to 15 min | H4 counts assists and medals toward the score |
| MLG and HCS Team Slayer | 50 kills | 12 min | No radar, BR start, timed power weapons |
| Team Doubles 2v2 | 25 kills | 10 min | Small maps; one death is 4 percent of the game |
| BTB Slayer 8v8 | 100 kills (H2, H3); 1000 points (H4) | 15 to 20 min | Vehicles decide it |
| FFA (Lone Wolves, Rumble Pit) | 25 kills | 10 min | Only the top player wins; second place is a loss |
| SWAT | 50 kills | 10 min | No shields, no radar, BR or magnum; one head shot kills |
| Team Snipers | 50 kills | 10 min | Sniper only, no radar; body shots take two |
| Shotty Snipers | 50 kills | 10 min | Shotgun plus sniper; CQB and Long band only |
| Fiesta | 50 kills | 10 min | Random weapons every spawn; play the weapon you have |
| Juggernaut, Regicide | see section 5 |  | Slayer variants with a marked target |

### Team Slayer: roles for a four-bot team

- Anchor (Defender or Support style): holds the team's strongest position with a precision weapon, never pushes, calls enemy positions. Spawn anchor as well: teammates buddy-spawn next to this bot (see the Mechanics tab).
- Slayer (Slayer style): takes the first power weapon, fights the mid, takes the trades at even shields.
- Support (Support style): shadows the Slayer at Medium band, team shoots every target, throws the grenades.
- Floater (Rusher or Sniper style depending on the map): rotates between the second power weapon, the flank, and the powerup; punishes isolated enemies.

### Phases

1. Opening (0 to 30 s): the team moves as a unit to the nearest power position and sends the Slayer and Support to the first power weapon with a grenade thrown onto it. Nobody crosses the mid alone. On BR-start maps the opening fight is a team shot across mid; on AR-start maps it is a rush to the BR spawns first.
2. Control (30 s to first big swing): hold two adjacent power positions, rotate as a pair, count timers. Take fights only two-on-one. A kill on an isolated enemy is followed by a group push to the next position, never by a solo chase.
3. Lead management: up by 5 or more, the team stops pushing; it holds positions and lets the enemy come. Down by 5 or more, the team groups as four and pushes one side with grenades first; it accepts even trades because trades shrink the gap when the leading team is forced to re-take ground.
4. Closing (last 5 kills or last 60 s): leading, hide and hold; trailing, all-in as four with every power weapon fired.

### Spawn control in Team Slayer

- The team that holds the middle and the enemy's strongest position forces the enemy to spawn in the weakest third of the map; after a double kill, two bots move toward the predicted spawn cluster and pre-aim the exits while two hold.
- Do not spawn trap from inside the enemy's spawn zone: standing in it pushes spawns elsewhere and splits the team. Trap from the edges, 40 to 60 ft from the cluster, with sightlines on the exits.
- A bot that just died should wait for teammates to spawn near it (7-second buddy spawn window) before moving; two bots spawning together is stronger than one bot running to the team.

### FFA

- Third-party rule: never start a fight; find a fight already in progress and shoot the winner after they finish (both are weak). The bot that fires first in a 1v1 in FFA usually dies to the third player.
- Movement: travel the map's edge, not the center; hold a corner that sees one lane, and move after each kill because the victim respawns knowing where the bot was.
- Weapons: a precision weapon and a CQB weapon; power weapons are worth more in FFA because nobody team shoots.
- Score: the bot plays to be first, not to have a good ratio; when second with 20 s left, it pushes the leader.

### Team Doubles

- Two bots never split by more than Short band; every fight is two-on-one or it is not taken.
- One bot holds, the other takes the timers; they swap when the holder's shield drops.
- Lockout, Midship, Guardian, The Pit and Countdown Doubles are won by holding the top and letting the enemy pair come up.

### BTB Slayer

- Two crews of two in vehicles (hog driver and gunner; Ghost or tank with an escort), two bots on anti-vehicle (laser or rockets from the base), two snipers on the base tops, two roamers for the mid power weapons.
- Nobody walks the open mid; infantry moves along the walls and caves. Kills on vehicle crews are worth two points and a vehicle.
- The laser bot never leaves the base lane; losing the laser loses the vehicle war.

### SWAT

- One head shot kills and there is no shield, so every peek is a coin flip decided by who is pre-aimed. The bot pre-aims head height at every corner, never sprints into a sightline, and shoots the instant the head appears.
- Hold corners, not lanes: a bot in a lane dies to anyone who turns a corner into it; a bot at the corner shoots whoever turns.
- Crouch and jump are both bad: crouching drops the head to a predictable spot; jumping makes it predictable in the air. Strafe only.
- Team shoot does nothing (one shot kills), so the team spreads to cover more corners rather than grouping; stay within Medium band of one teammate to trade.
- SWAT Magnums: the same at Short band; at Long band the magnum misses, so close distance through cover.

### Team Snipers

- Snipers only, usually no radar and body shots take two. The bot holds Long sightlines with a head-height edge, moves after every shot, and never crosses a lane in the open.
- Close fights: a no-scope body shot then a melee kills; the bot facing an enemy at Short band does not scope.
- The team covers four different lanes, not the same one; callouts replace team shots.
- De-scope discipline: one body shot de-scopes the enemy sniper, which is often better than waiting for a head shot.

### Shotty Snipers

- Two bands only: Melee band (shotgun) and Long band (sniper). Medium band is a death zone with either weapon. The bot holds a corner with the shotgun inside a structure and a window with the sniper outside it, and never stands in between.
- Lifts, doorways and ladders are shotgun kills; roofs and long halls are sniper kills.

### Fiesta

- The bot reads its random weapons on spawn and picks a plan: power weapon → hunt; CQB → hold a corner; precision → mid control; weak pair (plasma pistol and magnum) → the noob combo at Short band and a swap at the first corpse.
- Enemies with random weapons are unpredictable; the bot keeps distance until it sees what they hold.

### Per-game Slayer notes

- CE: pistol fights at any range; grenades at spawns; health packs matter after every fight.
- H2: 1.5 s kills mean the first shot wins; BXR and double shot at Short band; sword and shotgun control rooms.
- H3: team shot and grenade-then-shoot; equipment timing; spawn weighting as in the Mechanics tab.
- Reach: bloom pacing; armor ability counters; bleed-through makes melee on weak enemies deadly.
- H4: score counts assists, so team shooting pays twice; ordnance drops are the power weapon economy; instant respawn means kill spots are never safe.

## Capture the Flag family

CTF is the mode where kills are a means, not an end. The team that controls the route between the two flags wins; the team that chases kills loses even when it is up on the kill count.

### Rules the bot must know per game

| Rule | CE | H2 / H2A | H3 | Reach | H4 |
| --- | --- | --- | --- | --- | --- |
| Carrier can shoot | No | No | No | No | Magnum only |
| Carrier melee | Yes, strong | Yes, strong | Yes, strong | Yes | Flag hit kills unshielded |
| Carrier can drop or throw | Drop | Drop and throw (juggling) | Drop | Drop | No (default); auto pickup |
| Flag must be home to score | Yes (default) | Yes (default) | Yes (default) | Yes (default) | No (default) |
| Flag return | Touch it | Touch it | Touch it | Touch it | Auto-return timer, no touch return |
| Carrier marked on HUD | No | No | Waypoint | Waypoint | Waypoint plus carrier speed is normal |
| Dropped flag reset time | \~30 s | \~30 s | \~30 s | \~30 s | \~15 to 30 s |
| Carrier in vehicle | Passenger seats only | Passenger seats only | Passenger seats only | Passenger seats only | Passenger seats only |

### Multi Flag (both teams attack and defend)

Roles for four bots:

- Runner (Objective or Rusher style): pulls the enemy flag; uses the covered route; never fights with the flag unless cornered.
- Lead escort (Slayer style): 10 to 20 ft ahead of the runner, clears the route, calls enemies, trades its life for the runner's.
- Rear escort (Support style): 10 ft behind, faces backward, kills chasers, picks the flag up if the runner dies.
- Defender (Defender or Sniper style): holds the home flag's sightline with a sniper or BR and a shotgun corner, returns dropped flags, never leaves to chase.

For 8v8 double the escorts, add a vehicle taxi crew and a second defender with a laser or rockets at the base.

Phases:

1. Opening: the team takes the first power weapon and the mid; the defender goes home. No pull before the mid is controlled unless the enemy rushed and left their flag open.
2. Setup: the escorts stage on the enemy side of mid; the runner waits at the last cover before the enemy base until the lead escort reports the base clear or the enemy team is dead or split. The pull starts when at least two enemies are dead or more than Medium band from their flag.
3. The pull: the runner touches the flag and leaves by the route with the most cover, not the shortest. Escorts move with it. In H2, juggle on safe stretches. A pulled flag changes the enemy's spawns (flag-away zone), so expect enemies to appear near the route.
4. Home stretch: if the home flag is away, the runner waits under cover within Short band of the capture point; the defender and one escort return the home flag; the runner caps.
5. Lead management: up by one with the enemy flag at home, keep one escort home as a second defender; up by two, stop pulling and defend with three until the enemy pulls, then kill the carrier and reset.

Defense details:

- The defender sits where it sees the flag and the two most used pull routes, off radar (crouched) and behind head-height cover; it does not sit on the flag (grenades).
- When the enemy pulls, the defender shoots the carrier first (slow, cannot shoot back); teammates shoot escorts.
- Return rule: touch a dropped flag only when no enemy has a sightline on it or a teammate suppresses; otherwise hold the sightline and kill whoever touches it. In H4 flags auto-return, so defenders guard the flag until the timer runs rather than touching it.
- Reset trap: a dropped flag near the enemy's side is bait; the bot lets it reset rather than running into the enemy team.

### One Flag (asymmetric, timed rounds)

- Attack round: all four push; two escorts, a runner and a floater who takes the sniper or rockets and shoots into the base from range. The runner uses the route the defenders cannot see from their setup (High Ground pipe, Zanzibar seawall, Last Resort beach). A round is won by one capture, so the team sacrifices kill count freely.
- Defense round: all four hold the base: a sniper covering the main approach, a shotgun or sword inside the flag room, a BR at the secondary entrance, a floater with rockets or laser for vehicles. Nobody chases; a dead attacker respawns far away, a dead defender respawns inside the base.
- Time: attackers with 30 s left pull regardless of cover (a failed run and a timeout are the same); defenders with 30 s left hide the flag room with bodies and grenades.

### Neutral Flag

- One flag at mid; both teams run it to their own base. The opening fight is the whole game: the team that wins the first mid fight takes the flag and the defenders are now the chasers.
- The carrier runs home; the three others form a wall between the flag and the enemy, not around the carrier.
- If the enemy has the flag, kill the carrier and the flag resets to mid or drops where they died; two bots go for the drop, two hold.

### Speed Flag and variants

- Carrier moves at full speed and no flag-at-home rule: a pure race. Every bot is an escort or a runner; defense is killing the enemy carrier only.

### Routes, vehicles and the flag

- Vehicles: the flag can ride in a Warthog passenger seat, Mongoose rear seat, Hornet or Falcon side seat, Prowler and Spectre seats. A flag taxi plus one escort vehicle is the BTB standard; the gunner shoots chasers.
- Teleporters and lifts: the flag can go through teleporters (CE, H2, H3) and lifts; man cannons launch the carrier. Teleporter exits are camped, so the escort goes first.
- Flag jumps: H2 and H3 maps have flag-carrier shortcuts (the Pit shortcut, Sanctuary's back drop, Narrows bottom mid); the scripting agent records them as carrier waypoints.

### Per-game CTF notes

- CE: no flag HUD marker and no throwing; the carrier is a slow target the sniper sees across the map; roof snipers decide Blood Gulch and Sidewinder.
- H2: juggling and the strong flag melee; Beaver Creek, Sanctuary, Zanzibar One Flag and Coagulation are the classics.
- H3: the flag waypoint shows the carrier to everyone; equipment (bubble shield on the carrier, regenerator at the stand, trip mine on the return route) is part of the plan.
- Reach: sprint and jetpack change routes; a jetpacking carrier is an easy needle rifle target; drop shields on the flag stand.
- H4: auto pickup (do not walk over it unless running), no drop, magnum for the carrier, auto-return timer; the carrier is faster than before and pushes are shorter.

## Oddball, King of the Hill, Crazy King, Headhunter, Ricochet

These are time-in-possession modes: the score ticks while the team holds a thing or a place. The bot's instinct to chase kills is wrong here; the only kills that matter are the ones that protect the hold or break the enemy's.

### Oddball

Rules: the ball carrier scores one point per second held (two balls in some H4 variants); the carrier cannot shoot; ball melee is a one-hit kill; the ball drops on death and resets after about 30 s if untouched. Score to win is usually 150 to 250 s.

Roles:

- Carrier (Objective style): hides, does not fight, melees only when touched.
- Two guards (Support and Slayer styles): form an arc 10 to 25 ft from the carrier facing the entrances; they team shoot everything that enters and throw grenades at the doorways.
- Hunter (Rusher or Sniper style): roams just outside the hold, kills approaching enemies before they reach the guards, and chases the ball when the enemy has it.

The hold:

1. Pick a hold with one or two entrances, head-height cover for the carrier, and an escape drop (Lockout Back or Library corner, Guardian Blue room back or Snipe 1 pillar, Midship base corner under the ramp, The Pit's shotgun hall end, Countdown's sniper ledge alcove, Haven's side room). Never hold in the open center.
2. The carrier crouches (off radar) in the deepest corner; the guards do not stand in the doorway (grenades) but inside, angled.
3. Ball throws: when the carrier's shield drops or two enemies are inside, the carrier throws the ball toward the deepest friendly corner or off a ledge toward teammates, then fights with the secondary weapon or dies while the guards keep the ball.
4. Reset discipline: when the hold is lost, the team does not fight for the ball in the open; it falls back to the next hold, lets the enemy pick up, then pushes the enemy hold as four with grenades first.

Breaking an enemy hold:

- Throw every grenade into the hold first (two bots, four grenades, through the doorway and over the wall); the carrier dies or moves.
- Push as two from two entrances, one bot per entrance, while the sniper or BR covers the exit the ball will be thrown to.
- Kill order: guards first if they are at the doorway, carrier first if the guards are deep; the carrier is defenseless at Medium band.
- After the ball drops, the bot nearest it picks it up only if the hold is clear; otherwise the team secures the room first.

Score rules: ahead by 60 s or more, the hunter joins the guards and nobody leaves; tied with 30 s left, the carrier runs to the safest corner and the whole team dies protecting it; behind, the carrier's team pushes as four.

### King of the Hill (Team King)

Rules: one point per second with a teammate inside the hill and no enemy inside; the hill moves on a timer (60 to 90 s) or when captured (Crazy King); hills are visible on the HUD; score to win 150 to 250.

Roles:

- King (Objective style): the one bot in the hill, crouched at the edge of the hill marker, using the hill's cover.
- Two outer guards: hold the high ground that overlooks the hill, outside grenade range of the hill, covering the approaches.
- Rotator: moves early to the next hill and holds the ground between the current and next hill.

The hold:

1. One bot inside only; the hill marker is where grenades land. The King leaves the hill when two grenades land and returns after.
2. Guards shoot from positions the hill's attackers must expose themselves to; the guards never enter the hill unless the King dies.
3. Hill timer: the rotator moves to the next hill at 10 s remaining; when the hill moves, the whole team rotates and the rotator becomes the next King.
4. Contest: if the bot cannot clear an enemy from the hill, it steps in to contest (stops the enemy's score) while teammates shoot; a contested hill scores nothing for either side.

Breaking an enemy hill: grenade the hill marker, then one bot enters to contest while three shoot; a sword or shotgun rush into a hill is strong because the hill forces a stationary target.

Crazy King and hill order: the scripting agent reads the hill sequence from the variant; the bot stages at the next hill 10 s early. In random-order variants it holds the position that sees the most hill sites.

### Headhunter (Reach)

Rules: killed players drop skulls; carry skulls to a marked drop zone to score; the zone moves; dying drops all carried skulls. Scoring favors small frequent deposits.

- Deposit at two or three skulls, never hoard; a bot with five skulls is a target for everyone.
- Kill enemies near the current zone and deposit immediately; the zone's next location is shown, so the rotator moves early.
- Hunt skull carriers first (HUD shows counts); an enemy with four skulls is worth four kills.

### Ricochet (Halo 4)

Rules: carry the ball into the enemy goal for 50 points or throw it in for 20; the carrier can throw and sprint; dying drops the ball.

- The carrier runs with two escorts and throws from Medium band when the goal is covered; a throw scores less but a dead carrier scores nothing.
- Defense: two bots at the goal line with automatics (the carrier is at Short band when it arrives); one mid to intercept throws.
- The ball resets on a timer; a loose ball near the enemy goal is thrown toward the friendly side rather than carried into four defenders.

## Assault, Territories, Dominion, Extraction, Stockpile, Invasion

These are the modes where a team must stand still at a point under fire to score: the arm, the capture, the extraction. The bot that understands that standing still is the objective also understands that everything else is about buying those seconds.

### Assault (Neutral Bomb, Multi Bomb, One Bomb)

Rules: carry the bomb to the enemy arm point and hold the arm for several seconds (about 5 s in H2, 3 to 5 s in H3, with a fuse after the arm); the carrier cannot shoot; the enemy disarms by standing in the plant radius; the bomb resets after a drop timer.

Roles: carrier (Objective), lead escort (Slayer), rear escort (Support), and a suppressor with rockets or sniper who fires into the arm point from range.

Phases:

1. Opening (Neutral Bomb): both teams race to the mid bomb; the first mid fight decides who carries. The bot does not grab the bomb until the team wins the mid; grabbing under fire feeds the enemy a kill and a reset.
2. Approach: the carrier moves behind the escorts on the covered route; the suppressor sets up on the arm point's sightline first.
3. The arm: only when two escorts are within Short band of the arm point covering the two approaches. The carrier plants; the escorts stand between the plant and the enemy, grenades in hand. If the carrier dies mid-arm, the rear escort grabs and restarts.
4. The fuse: once armed, the team holds the plant radius against disarmers; grenades on the bomb and a shotgun at Melee band are the disarm counters.

Defense (One Bomb rounds): all four at the arm point: a shotgun or sword inside the plant radius, a sniper on the approach, a BR at the second entrance, a floater who disarms. Disarm rule: the disarmer rushes the bomb with grenades thrown ahead; two disarmers from two sides beat one carrier escort.

Bomb-specific tricks: the bomb carrier's melee is strong (H2, H3); the bomb can ride passenger seats; a thrown bomb (H2) skips a gap. The arm spot is often inside a base room, so pre-nading the room is standard.

### Territories and Land Grab

Rules: capture a territory by standing inside it for a timer; a team scores for owned territories over time (Territories) or captures count once (Land Grab); some variants lock captured territories.

- Capture the nearest two first, then contest the middle; a team that spreads to all five holds none.
- Defend from the sightlines over the territory, not inside it; one bot inside to recapture, three outside.
- Owned territories are spawn anchors (Mechanics tab), so holding the two nearest home keeps the team spawning near its line.
- Land Grab: once a territory locks, leave it; race the unlocked ones.

### Dominion (Halo 4)

Rules: three bases; capture by standing at the terminal; owned bases fortify over time (turrets, shields) and spawn resupply weapons and vehicles; a team owning all three triggers a last-stand sweep for the other team; score to 400.

- Opening: two bots to the nearest base, two to the middle base. The far base is taken only after the first two are fortified.
- Fortified bases are the team's spawn and ammo; a bot defending a base uses the turret only briefly and the resupply weapon (often a rocket or laser) against vehicles.
- Losing a base: retake as a pair; a lone attacker dies to the turret. Capturing a fortified enemy base starts with killing the turret and the resupply holder.
- Last stand: the team with no bases cannot respawn; it picks off capturers from range and recaptures the least defended base; the team with all three sweeps as a group and does not let the enemy touch a terminal.

### Extraction (Halo 4)

Rules: extraction sites appear one or two at a time; a team arms a site (about 5 s), then defends it for about 30 s while it extracts for 10 points; the enemy can convert it by arming over it; score to 100.

- Arm only with two covering the approaches; the site is a KOTH hill after arming, so the team holds the sightlines around it and keeps one bot inside to re-arm.
- Converting: push the enemy's site when it is close to extracting; converting late steals the full extraction.
- Two sites at once: three bots on one, one bot slowing the enemy at the other; never split two and two.

### Stockpile (Reach)

Rules: flags spawn at random points; carry them to the team's capture zone; every 60 s the zone scores the flags inside and clears; enemies can steal flags from the zone.

- Two collectors, two defenders; collectors take the nearest flags and drop them in the zone early in the cycle; defenders hold the zone's sightlines and kill thieves.
- In the last 10 s of the cycle, nobody leaves the zone; a stolen flag at second 59 loses a point.
- Thieving: with 5 s left in the cycle, a sprint-and-grab from the enemy zone converts their point to nothing.

### Invasion (Reach)

Rules: three phases per round (capture two territories, then two more or a core objective, then carry the core to extraction); Elites attack, Spartans defend or the reverse; loadouts and vehicles unlock per phase; a phase has a time limit and the round ends when the attackers fail.

- Attackers: push one territory at a time with the whole team; the second territory of a phase falls faster once the first is captured because spawns move forward. Use phase-two vehicles (Ghost, Revenant, Warthog) to taxi and suppress; the core carrier (phase three) rides a passenger seat.
- Defenders: hold the territory that is easier to defend with three, delay the other with one; fall back when a territory falls rather than dying in it. In phase three, kill the core carrier and return the core; a core sitting still resets after a timer.
- Loadouts: attackers take sprint and armor lock (vehicles), defenders take jetpack and drop shield on open maps (Spire, Boneyard, Breakpoint).

### Shared rules for standing-still objectives

- The standing bot is defenseless; its value is the seconds, not its kills. The team's value is the seconds it buys.
- Grenades are the attacker's first move and the defender's first fear; every arm or capture starts by nading the point and ends with the point clear of grenades.
- Posture flips at the point: attackers are aggressive until the arm begins, then purely defensive; defenders are passive until the arm begins, then purely aggressive.

## Infection, Flood, Juggernaut, VIP, Regicide, Grifball, Race

Asymmetric modes give the two sides different rules; the bot needs a plan for each side, and the plan flips the moment it switches sides.

### Infection (H3, Reach) and Flood (H4)

Rules: a few players start as zombies (sword or hammer, often with camo, bonus speed and low shields); humans have shotguns and precision weapons; a human killed by a zombie becomes one; the last human standing or the round timer ends the round; several rounds per game. H4 Flood gives zombies a claw, camo and thruster, and humans a shotgun and magnum. Alpha zombies are tougher; the last man standing often gets bonus health or a waypoint.

Survivors (humans):

- Camp rule: pick a room with one entrance, or a ledge zombies must jump to (The Pit's base attic, Guardian's Snipe 3, Sandtrap's Elephant roof, Reach's Sword Base top floor). Two shotguns on the entrance at Melee band, precision weapons behind them at Medium band to shoot zombies on the approach.
- Ammo discipline: six-shot shotguns run out; the team counts ammo and moves to the next ammo spawn as a group before it hits zero, never after.
- Shooting: head shots with the magnum or BR kill a low-shield zombie in one or two; the shotgun is for Melee band only. A zombie with camo shimmers; shoot the shimmer.
- Grenades: every zombie approach gets a grenade; zombies cannot shoot, so grenades are free.
- Last man standing: move to the map's edge with the longest approach, back to a wall, and head shot everything; the bot wins the round by surviving, not by kills.
- Never split: a lone human is a zombie in 10 s.

Zombies:

- Approach from two sides at once, never in a line down the camping lane; one zombie draws the shotguns, the others lunge from the flank.
- Use camo and crouch-walking to reach Melee band; sprint (Reach) or thruster (H4) for the last 20 ft.
- Lunge timing: the sword reticle turns red at about 20 ft; the bot lunges at red, not before. Hammer zombies swing at the floor to catch jumpers.
- Baiting: a zombie standing just outside shotgun range makes humans waste ammo and grenades; after two or three wasted shots, the rush starts.
- Alpha zombie: tougher, so it leads the push and absorbs the first shotgun blast while two regulars lunge past.

### Juggernaut

Rules: one player is the Juggernaut (bonus shields, damage, sometimes speed; visible to all); only the Juggernaut scores kills (or everyone scores by killing the Juggernaut); killing the Juggernaut makes the killer the new Juggernaut.

- As Juggernaut: hunt isolated players at the map's edge; avoid the center where three enemies converge; use the bonus shield to win Short band fights and retreat the moment two enemies are in view. With a power weapon the Juggernaut is unstoppable, so grab it first.
- As a hunter: team up with the nearest player (temporary ally) on the Juggernaut, let someone else take the first melee, and finish; whoever lands the kill becomes the target, so a bot behind in score wants the kill and a bot ahead avoids it.
- Ninjanaut and other variants change the Juggernaut's traits; the scripting agent reads the traits and swaps the posture (a fast, weak Juggernaut hunts; a slow, strong one holds a corridor).

### VIP (H3)

Rules: each team has a VIP; killing the enemy VIP scores; the VIP has bonus or reduced traits and often has to reach destination points.

- The VIP plays like a flag carrier with a gun: it stays with two escorts, holds back from fights, and moves only on covered routes to destinations.
- The team's fourth bot hunts the enemy VIP with a sniper or rockets; the VIP marker shows where it is.
- Escorts with VIP proximity traits (some variants give nearby teammates bonus shields) stay within the radius.

### Regicide (H4)

Rules: FFA where the leader is the King (marked, bonus traits grow over time); killing the King is worth more; the King earns bonus points over time.

- As King: the whole lobby hunts the bot; it plays the map's edge, holds a corner with one entrance, and stays alive for the bounty; it fights only when cornered.
- As a hunter: ignore everyone but the King unless they are in the way; the King's bounty is worth several kills; approach from behind while others distract.
- Team Regicide: protect the team's King as in VIP.

### Grifball

Rules: a court with a bomb at the center; everyone has a gravity hammer and sword; carry the bomb to the enemy goal and plant it (instant); spawn killing is allowed and expected; many short rounds.

- Carrier: hop constantly (the hammer's ground splash misses jumpers), run the lane the teammates cleared, plant on arrival.
- Clearers: swing the hammer at the enemy line ahead of the carrier; a hammer swing deflects the bomb and other hammers. Swords lunge at enemies out of hammer reach.
- Defense: hold the goal line and swing when the carrier is at 10 ft; a hit sends the carrier flying and drops the bomb.
- Spawn: the team spawns near its goal; the enemy spawn kills, so the bot sprints or swings out of spawn immediately.

### Race and Rocket Race

Rules: drive through checkpoints; first to the lap count wins; Rocket Race pairs a driver with a passenger who has a rocket launcher.

- Race: the driver takes the inside line at every checkpoint, uses the e-brake on hairpins, and does not fight; a flipped vehicle costs more than a shot.
- Rocket Race: the passenger fires at the vehicle ahead and behind; the driver keeps the passenger's side facing the nearest enemy; the pair never leaves the vehicle.

### Party-mode posture rule

The scripting agent reads the variant's traits (speed, shields, damage, weapons, visibility) at load and sets the bot's style from them: fast and fragile → Rusher with hit-and-run; slow and tough → Defender holding a chokepoint; marked on everyone's HUD → Objective-carrier posture (edges, cover, no fights).

## Halo 3: ODST Firefight in depth

ODST Firefight is survival against scripted Covenant waves with a shared pool of lives, skulls that stack as the match goes on, and no shields. The bot's whole game is to spend as few lives as possible per wave, which means cover, head shots, and never leaving the squad.

### Structure

- A Set has 3 Rounds; a Round has 5 Waves; the fifth wave of each round is a Boss wave with Hunters, Chieftains or Brute packs; after every Round there is a Bonus Round of about 2 minutes with Grunts and skulls that make them explode or recharge the squad's lives.
- Lives: the squad shares a pool (7 at the start plus bonuses); a bot that dies takes one; running out ends the match. Each Round completed restores lives and each Bonus Round can earn more.
- Skulls: one skull turns on with each Round and stacks within a Set (Tough Luck, Catch, Black Eye, Fog, Famine, Mythic, Tilt, Iron and others); after a Set the skulls reset and the enemy tier increases. The bot reads the active skulls each round and changes its rules (below).
- Health: ODSTs have stamina (recharges, like a weak shield) over a health bar that only health packs refill; health packs are fixed on each map and respawn between rounds.
- Enemies: Grunts, Jackals (shields and snipers), Brutes (shielded, packs with Chieftains), Hunters (pairs), Drones (swarms), Engineers (shield nearby enemies), Elites only in some variants. Enemy tier rises every Set.

### Squad doctrine

1. One hold, one fallback: the squad picks a defensible area with one wide approach for drops, head-height cover, a health pack and an ammo crate within 30 ft, and a fallback room behind it. It fights from the hold and retreats to the fallback only when the hold is overrun or a Chieftain arrives.
2. Four lanes: each bot owns an approach; the drop pods and Phantoms land on fixed spots per map, so the lanes are known. A bot that kills everything in its lane helps the neighbor, not the far side.
3. Life economy: a bot at low health falls back to the pack before the wave ends; the squad waits for a respawning bot (respawn is at the next wave or on a timer) by holding, not pushing. Two bots alive hold; one bot alive hides and crouches until the wave timer brings the others back.
4. Target priority per wave: anything with a fuel rod or a plasma launcher first (Grunts with fuel rods kill squads), then Chieftains and Brutes with hammers at Long band, Jackal snipers before they fire twice, Hunters with rockets or laser from behind, Drones with automatics, Grunts last unless they are at Melee band (suicide Grunts in later sets).
5. Weapon economy: keep the silenced magnum or the pistol (head shots on everything small) and carry one heavy (sniper, rockets, laser, fuel rod, hammer) from the drops; swap plasma pistol in when Brutes arrive (charge plus head shot beats a shield). Reload between waves, never during a push. Scavenge dropped Covenant weapons (carbine, beam rifle, plasma rifle) when human ammo runs low; the carbine is the best Firefight head-shot weapon.
6. Grenades: a Grunt pack in a doorway is one grenade; a Brute pack is two grenades then head shots; stick Chieftains and Hunters.

### Enemy playbook

| Enemy | Kill method | Bot rule |
| --- | --- | --- |
| Grunts (regular, heavy, fuel rod) | One head shot with the pistol or carbine; melee at Melee band | Kill fuel rod Grunts at Long band first; let the rest come to the kill zone; expect suicide Grunts at Short band in late sets |
| Jackals (shield) | Shoot the hand hole, then the head; flank the open side; a plasma pistol charge pops the shield | Never trade with a Jackal line from the front; a grenade behind them kills the pack |
| Jackal snipers | Head shot first; they one-shot ODSTs with beam rifles | A sniper that fires once is dead or the bot is behind cover before the second shot |
| Brute minors and majors | Plasma pistol charge plus pistol head shot; or two carbine bursts to the head after the shield; stick them | Brutes berserk when their pack dies; back off to Medium band when they charge |
| Brute Chieftain (hammer) | Rockets, laser, sniper head shots from Long band; never melee | Retreat to the fallback and shoot; a Chieftain with Invincibility waits out the glow |
| Brute Chieftain (fuel rod or plasma cannon) | Head shots with the sniper from cover | Break line of sight every 2 s; fuel rods arc, so stand behind a ceiling |
| Hunters (pair) | Shoot the orange back after a charge; rockets, laser; a plasma pistol stuns briefly | Split the pair: one bot baits a charge, two shoot the back; never fight them in a corridor |
| Drones | Automatics and the plasma rifle; they swarm from the air | Stand under a ceiling; shoot the ones that hover |
| Engineers | Shoot them first (they shield everyone around them); a dead Engineer explodes and damages nearby enemies | A Grunt or Brute near an Engineer is immune until the Engineer dies |

### Skull rules

| Skull | Effect | Bot change |
| --- | --- | --- |
| Tough Luck | Enemies dodge grenades and fire | Head shots over grenades; fire longer bursts |
| Catch | Enemies throw more grenades and drop more | Stay behind cover, move after every kill, pick up the extra grenades |
| Black Eye | Stamina only recharges on melee kills | Melee Grunts to recharge; the squad keeps a Grunt lane open for melee |
| Fog | No motion tracker | Sound and line of sight only; tighter hold |
| Famine | Dropped weapons have half ammo | Save human ammo; scavenge more often; carbines over BRs |
| Mythic | Enemies have double health | Plasma pistol plus head shot on everything shielded; power weapons on Brutes |
| Tilt | Damage types matter more | Plasma on shields, kinetic on flesh, strictly |
| Iron | A death resets the wave (or ends the round) | Nobody takes a risk; the squad fights from the deepest fallback |
| Thunderstorm, Cowbell, Grunt Birthday Party, IWHBYD | Enemy tier up, bigger explosions, confetti, dialogue | Thunderstorm: more Majors, play as if Mythic; Cowbell: grenades and explosions push harder, keep distance from explosives |

### Bonus Rounds

- Grunts only, with skulls that make them explode on death (Cowbell plus Catch); every kill adds points and a life is restored at thresholds. The squad spreads across the open ground, melees and head shots as fast as possible, and avoids the explosions by moving between kills. A hammer or sword is the best Bonus Round weapon.

### Holds by map

| Map | Hold | Fallback | Drop lanes to watch | Notes |
| --- | --- | --- | --- | --- |
| Alpha Site | The upper plaza behind the central pillars | The interior corridor at the rear | Two Phantom drops at the front plaza, pods to the sides | Chieftains come up the main stairs; the sniper covers them from the balcony |
| Crater | The ONI building interior door line | The back rooms | Pods on the crater floor, Phantoms over the ridge | Open center is death; fight from the doorway and the roof edge |
| Crater (Night) | Same with VISR on | Same | Same | Jackal snipers on the far ridge; kill them first |
| Lost Platoon | The warehouse interior with the Warthogs outside | The rear loading bay | Phantoms drop Ghosts and Wraiths on the open ground | Vehicle wave: one bot in a Warthog gunner seat with a driver, two on rockets, one holding the door; splatter Grunts, rocket Wraiths from behind |
| Rally Point | The upper walkway behind the planters | The lower lobby | Drops at street level on both sides | Height advantage; grenades down onto the street |
| Security Zone | The raised plaza by the health pack | The ramp corridor | Pods in the lower courtyard, Phantoms by the entrance | Hunters push the ramp; rocket them from the plaza |
| Windward | The rooftop interior room | The stairwell | Phantoms on the roof pad | Drones swarm; stay inside the room and shoot out |
| Chasm Ten | The upper platform by the lift | The lower tunnel | Pods on the lower deck | Jackal snipers across the chasm; sniper duel first |
| Last Exit | The train station interior behind the pillars | The ticket hall | Phantoms on the open platform | Brute packs charge down the platform; grenades into the choke |
| Uplift Reserve | The visitor center building | The overlook ramp | Vehicles drop on the open ground | Vehicle wave like Lost Platoon; use the Warthog and the laser |

### Bot roles in Firefight (4 players)

- Marksman: sniper or carbine, head shots on everything, calls priorities.
- Heavy: rockets, laser or fuel rod for Hunters, Chieftains and vehicles; carries the plasma pistol secondary.
- Line holder: shotgun or SMG at the hold's doorway; handles Grunts and Jackals that get inside.
- Runner: the bot that fetches ammo and weapons between waves and revives the line when a bot dies; carries the hammer in Bonus Rounds.

### Failure modes to avoid

- Chasing kills into the open (one life per chase).
- Fighting Hunters in a hallway (both charge).
- Standing in the Phantom's landing lane (its turret kills on the way in).
- Spending the squad's last two lives on a Chieftain instead of waiting it out in the fallback.
- Ignoring a Jackal sniper because it is far away (it will not be far away in 5 s).

## Halo: Reach Firefight in depth

Reach Firefight keeps ODST's set, round and wave structure but adds Spartan shields, loadouts with armor abilities, Elites and Skirmishers, a Versus mode where players control the Covenant, and a Generator Defense objective. The bot plays it as a shielded ODST squad with abilities: the hold-and-fallback doctrine still wins, but armor lock, drop shields and jetpacks change where the hold can be.

### Structure and variants

| Variant | Rules | Bot posture |
| --- | --- | --- |
| Firefight (classic) | 1 Set of 3 Rounds of 5 Waves plus Bonus Round; shared lives; skulls stack per round; shields and health bar | Full doctrine below |
| Firefight Arcade | 1 Set, unlimited lives in most settings, bonus traits (damage, speed), ordnance-like weapon drops | Aggressive: lives are free, so the bot pushes for score and uses power weapons freely |
| Firefight Limited | Classic rules with limited lives and harder skulls | Maximum caution: every death matters; fallback early |
| Score Attack (solo) | One player, 1 Round, score-based; variants include Gruntpocalypse, Sniper Attack, Crash Site, Skirmigeddon, 2X Score Attack, Fiesta Attack | Solo: hold a corner with one approach; head shots; no chasing |
| Gruntpocalypse | Grunts only, waves of them, many with fuel rods and suicide charges | Head shot machine: DMR or needle rifle, kill fuel rods first, melee at Melee band, never let three Grunts get within Short band |
| Rocketfight, Sniperfight, FRG fight | Infinite power weapon ammo of one type | Fight at the weapon's band; rockets at feet, snipers from the back wall |
| Generator Defense | Attackers (Covenant AI or players) try to destroy generators; defenders hold them; generators can be locked briefly | Defenders split by generator; attackers (Versus) push one generator with all players |
| Firefight Versus | Two teams alternate: Spartans survive, Elites (players) attack with AI waves; score is kills or survival time | As Elites: coordinate with the AI wave, flank with evade and the sword; as Spartans: the usual hold |
| Firefight Doubles | Two players, Limited rules | Two-bot squad: one marksman, one line holder, always within Short band |

### Loadouts and armor abilities in Firefight

| Loadout | Weapons | Ability | When the bot picks it |
| --- | --- | --- | --- |
| Marksman | DMR, magnum | Sprint or jetpack | Default for the head-shot role; jetpack on maps with high holds (Overlook, Outpost) |
| Grenadier | Grenade launcher, AR | Armor lock | For Wraith and Ghost waves (EMP the vehicle, then plant) |
| Operator | AR, magnum | Sprint | The runner who fetches ammo and revives the line |
| Medic | Needle rifle, magnum | Drop shield | The anchor of the hold: drops the shield on the squad when a Chieftain or Hunter pair arrives |
| Airborne | DMR, magnum | Jetpack | Elevated holds; shoots down on Hunters' backs |
| Infiltrator | Shotgun, magnum | Active camo | Line holder for close waves; camo for Bonus Round melee |
| Spartan Ops style (custom) | Sniper, plasma pistol | Hologram | Baits Elites into the kill zone |

- Armor lock in Firefight: EMPs vehicles that touch it (a Ghost dies to a locked Spartan it boosts into), nullifies stickies and fuel rods, and buys 5 s for a drop shield to recharge the squad. The bot locks when a Wraith shell is in the air or a Hunter charges and there is no sidestep.
- Drop shield: the single strongest Firefight ability; it heals through the health bar and blocks fire. The Medic drops it at the hold when the squad's shields pop, not before.
- Jetpack: reaches holds the Covenant cannot easily reach (Overlook's roof, Outpost's upper building, Holdout's tower); jetpack bots shoot Hunters from above and land behind cover before the fuel runs out.
- Hologram: sends Elites into a sword lunge at nothing; Elites that lunge are head shot.
- Sprint: rotations and ammo runs; never into a wave.

### Enemy differences from ODST

| Enemy | Reach behavior | Bot rule |
| --- | --- | --- |
| Elites (Minor to Zealot, General) | Shielded, evade rolls, swords, concussion rifles, fuel rods; Generals have overcharged shields | Plasma pistol charge then DMR head shot; shoot where the evade ends; a sword Elite is a hologram target or a shotgun kill at the corner; never melee a Zealot |
| Skirmishers | Fast Jackal variants that flank and jump; needle rifles | Head shots at Medium band; they come from the side, so the flank bots watch for them; a needler wrecks them in the open |
| Grunts (incl. Ultras, fuel rod, suicide) | Fuel rod Grunts are the top threat; suicide Grunts charge with plasma grenades | Kill fuel rods at Long band first; shoot suicide Grunts before Short band; melee the rest |
| Jackals | Shields, needlers, snipers | As ODST; a plasma pistol charge drops the shield |
| Brutes | Shielded, chieftains with hammers and fuel rods, plasma launchers | Plasma pistol plus head shot; Chieftains from Long band with the sniper or laser |
| Hunters | Pairs with heavier armor; charge and fuel rod beam | Sidestep the charge, shoot the back; the Grenadier's EMP round stuns them; rockets and the laser kill |
| Engineers | Shield nearby enemies; explode on death | Kill first with a DMR head shot or the needle rifle |
| Drones (Buggers) | Swarm, hover | Needle rifle supercombines; stay under cover |
| Vehicles (Ghost, Wraith, Banshee on some maps) | Covenant drops | Grenadier EMP then plant; rockets, laser; plasma launcher if dropped |

### Squad doctrine (Reach additions)

1. The hold needs the same four things (one approach, cover, health pack, ammo) plus a drop shield spot and a jetpack escape; Reach shields let the squad hold a slightly more open position than ODST because a popped shield recharges.
2. Health bar: the shield recharges but health only comes back to the next third (Mechanics tab); the squad rotates bots to the health pack between waves and the Medic drops a shield when two bots are under half health.
3. Life economy as ODST; in Arcade the bot is aggressive but still never fights Hunters in a corridor.
4. Target priority: fuel rod Grunts, Engineers, Elite Generals and Zealots, Skirmishers on the flank, Jackal snipers, Chieftains from range, Hunters last with the heavy.
5. Weapon economy: DMR or needle rifle for heads, plasma pistol secondary, one heavy from the drops; the needle rifle supercombine kills unshielded Elites fast; the grenade launcher handles vehicles and Hunters; the sword or hammer for Bonus Rounds.
6. Bonus Round: Grunts with Cowbell-style explosions; sprint-melee chains, hammer swings, and the Infiltrator's camo for free assassinations; spread out so the explosions do not chain into the squad.

### Skulls in Reach Firefight

The ODST skull rules apply (Tough Luck, Catch, Black Eye, Fog, Famine, Mythic, Tilt, Iron, Cowbell, Thunderstorm, IWHBYD, Grunt Birthday Party), with custom skulls (red, yellow, blue) that the scripting agent reads from the variant's trait settings; Black Eye in Reach means shields recharge only on melee kills, so the squad keeps a Grunt lane open to melee for shields.

### Holds by map

| Map | Hold | Fallback | Drop lanes | Notes |
| --- | --- | --- | --- | --- |
| Beachhead | The upper structure's interior corridor | The back ramp | Phantoms over the beach, pods on the sand | Wraiths drop on the beach; the Grenadier and rockets from the upper windows |
| Corvette | The upper deck's rear doorway | The side corridors | Phantoms into the central hangar | Elites and Hunters push the ramps; jetpack to the catwalks for Hunter backs |
| Courtyard | The raised walkway over the courtyard | The interior rooms | Pods in the courtyard center | Height advantage; Skirmishers jump up the sides, flank watchers needed |
| Holdout | The tower's upper floor | The tower stairwell | Phantoms on the pad, pods around the base | Hunters climb the ramp one at a time: shoot backs from the floor above |
| Outpost | The upper building interior | The back stairs | Phantoms on the open ground, Ghosts on the road | Vehicle waves on the road; Grenadier EMP, laser if dropped |
| Overlook | The roof interior room or the balcony with the health pack | The lower corridor | Phantoms on the main road, pods on the lower level | Jackal snipers on the far cliff; Chieftains up the main stairs |
| Waterfront | The building's second floor over the market | The stairwell | Phantoms on the waterfront, Ghosts on the pier road | Open water side is a death lane; stay inside |
| Glacier | The ice cave's interior | The rear tunnel | Phantoms on the ice field, Wraith drops | Wraith shells arc; stay under the cave roof; EMP and plant |
| Unearthed | The mining building's interior | The rear bay | Vehicles drop on the road, pods by the drill | Warthog and Rocket hog available: one crew of two, two on foot in the building |
| Installation 04 (Anniversary) | The structure's interior behind the pillars | The lower ramp | Phantoms on the field | Classic Halo CE layout; the Warthog is strong against Grunts and weak against Wraiths |

### Generator Defense

- Three generators; defenders can lock a generator briefly (it becomes invulnerable for seconds, then needs a cooldown). The squad assigns one bot per generator and a floater; a bot locks its generator when two or more enemies are at Short band and shoots while it is locked.
- Attackers (Versus Elites): all three Elite players on one generator with the AI wave as cover; evade past defenders, melee the generator (or shoot it with a fuel rod); switch generators when the target is locked.
- Priority for defenders: the generator with the most enemies near it; a lost generator is not re-captured, so defend the two that remain and ignore the lost one.

### Firefight Versus (playing as Elites)

- Elites get evade, the sword, plasma rifles, needlers and a drop pod spawn; they are strong at Short band and weak to DMR head shots at Medium band. The bot flanks with the AI wave in front, evades the last 20 ft, lunges with the sword or dual plasma rifles, and dies for the kill if it costs the Spartans a life.
- Spartan lives are the score: a trade that costs the Spartans one life is a win for the Elite side.
- As Spartans in Versus, the rules are the usual hold plus: the Elite players come from the flanks, not the drop lanes, so the two flank bots face outward.
