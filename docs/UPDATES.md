# Updates

What changed in each version. Download the newest one from the [Releases page](https://github.com/AyoItzKye/project-proving-grounds/releases/latest). Everything still broken is on the [Known bugs](KNOWN_BUGS.md) page, and every game, mode and vehicle is rated on the [bot status sheet](BOT_STATUS.pdf).

Click a version to see what it added and fixed.

<details open>
<summary><b>0.2.3</b> (November 12, 2026): Author Provided Scans and LiDAR scan import in the launcher</summary>

### + Added
- <!-- build: 20261112-1342 --> **Author Provided Scans**: the mod author's own LiDAR scans of 129 maps, one zip per game, on the [LiDAR maps release](https://github.com/AyoItzKye/project-proving-grounds/releases/tag/lidar-maps) and linked from each game's folder on the [LiDAR maps page](../lidar-maps/). Bots start a map with what the author's scans found there: its floors, jumps, lifts, man cannons and teleporters.
- <!-- build: 20261112-1342 --> **LiDAR scans in the launcher**: open **LiDAR scans**, choose a game and press **Import** to download and add the author's scans of it, or press **Import a shared zip ...** to add a zip another player shared (one map's or a whole game's). An import adds to your own scans and never replaces them; importing the same zip twice adds nothing the second time, and a map your version does not have is skipped and named.

### - Fixed
- <!-- build: 20261112-1342 --> **Exporting a LiDAR scan**: `tools\lidar_share.py export` stopped with an error in an installed copy of the mod; it writes the zip now.

</details>

<details>
<summary><b>0.2.2</b> (November 6 to 11, 2026): Halo 2 vehicles, the Halo 4 Mantis and Banshee bombs, call bots into your vehicle, follow me and roam chat commands, Firefight bots that follow and respawn, Reach Firefight Versus and Generator Defense with Spartan and Elite bots, ODST characters for bots, an Invasion rework, Sandtrap's Elephants, Halo 2 Anniversary Forge maps</summary>

### + Added
- <!-- build: 20261112-0929 --> **Share LiDAR maps**: the new [LiDAR maps page](../lidar-maps/) has a folder for each game where players share their scans. `tools\lidar_share.py export <map>` packs your scan of a map into a small zip (nothing personal in it) and `tools\lidar_share.py import <zip>` adds someone else's to yours: floors add up, every jump, ride and teleporter that differs is kept, and your own scan is never replaced. Share one with the Share a LiDAR map form on the issues page.
- <!-- build: 20261112-0929 --> **ODST bots press more buttons**: they melee, throw grenades, reload, crouch and switch weapons in ODST Firefight now.
- <!-- build: 20261112-0424 --> **Halo 4 and Halo 2 Anniversary Forge maps in the LiDAR Simulator**: your own Halo 4 and Halo 2 Anniversary Forge maps are listed in the LiDAR Simulator with every Forge piece standing, read from the map files themselves, Halo 2 Anniversary's stone platforms included, and the bots walk round them.
- <!-- build: 20261112-0424 --> **Halo 3 Forge maps in a match**: in a Halo 3 custom game on one of your Forge maps, the bots find its map file from the pieces standing in the match and play on its layout (its walls, ramps and blocks), not on the bare map.
- <!-- build: 20261112-0058 --> **Power spots**: bots read every map for good places to hold. An Oddball carrier goes to a room with walls round it, a roof and one or two ways in, where few players die, away from the enemy, and stays there until an enemy reaches it. A bot with a sniper rifle and no objective job takes the best overwatch near it: long sight lines, high ground, a wall at its back.
- <!-- build: 20261112-0058 --> **Territories split like a team**: two bots go for each territory to take, one holds each territory you own (two when the enemy is on it), and the spare joins the most contested one.
- <!-- build: 20261112-0058 --> **Firefight: Hunters, hammer Brutes and sword Elites**: bots back away from one that faces them while they pick off the smaller enemies, and Heroic and Legendary bots circle behind one that is busy with someone else to shoot its back.
- <!-- build: 20261112-0058 --> **CTF: a defender fetches the carrier**: when your flag carrier is far from home and nobody is driving, a defender with an empty vehicle nearby takes it, picks the carrier up and drives him home.
- <!-- build: 20261112-0058 --> **Halo 3 Forge maps in the LiDAR Simulator**: your own Halo 3 Forge maps are listed in the LiDAR Simulator with their Forge pieces standing (walls, ramps and blocks), and the bots walk round them.
- <!-- build: 20261112-0058 --> **Gametype playbook**: docs/GAMETYPE_PLAYBOOK.md sums up how the bots play every game type.
- <!-- build: 20261111-2146 --> **Auto-update installs updates**: **Auto-update** is on unless you turn it off. The launcher looks for a new version every 30 minutes while it is open and installs it as soon as MCC is closed.
- <!-- build: 20261111-2146 --> **Update button on Play**: a small segment on the Play button shows a check when you are up to date (click it to check again) or a download arrow when a new version is out (click it to install).
- <!-- build: 20261111-2146 --> **LiDAR Simulator: Only maps not scanned yet**: tick it before **Every map** to scan just the maps the simulator has never scanned.
- <!-- build: 20261111-2146 --> **Bots feel walls**: every bot compares how far it should have moved with how far it really moved. Pushing into something that stops it, it slides along it (in a fight, it strafes the other way) instead of running in place, and a dead stop is remembered for its paths.
- <!-- build: 20261111-1901 --> **Bots act on callouts**: a teammate calling out an enemy near your flag carrier, a defender's post or your stolen flag sends the bots guarding it after him.
- <!-- build: 20261111-1901 --> **Defenders hold where you defend**: Passive LiDAR also learns where you stand guard near your flag, and the bots defend from those spots on that map.
- <!-- build: 20261111-1737 --> **LiDAR Simulator: Continue and Skip to next map**: a stopped Every map run goes on from where it stopped (the button reads Continue, with the maps left; **Start over from the first map** begins again), and **Skip to next map** saves the map running now and moves on when one takes too long.
- <!-- build: 20261111-1737 --> **Ball carriers hold where you hold the ball**: in Oddball, Passive LiDAR also learns the spots people hold the ball, and a bot carrying it goes to the one held longest that no enemy is on.
- <!-- build: 20261111-1325 --> **Passive LiDAR**: every match you play teaches the bots the map in the background, with nothing on screen and nothing to switch on: the floor you walk, the jumps you land, the lifts and man cannons you ride and the teleporters you take, and whether each one works both ways. Only your own moves are recorded; the bots play as usual.
- <!-- build: 20261111-1325 --> **Crouch-jumps in every game**: a jump of yours that landed higher than a plain jump can reach was a crouch-jump, so the bots crouch in the air on it too, in every game (before, only Halo 2 Anniversary and Halo 4 told the mod when you crouched).
- <!-- build: 20261111-0430 --> **LiDAR Simulator, one game at a time**: set **Every map runs** to a game and press **Every map** to scan every map of that game in turn, each with its Forge layouts. Maps with no edge to them (Death Island) end once their play area is covered instead of mapping empty ground for hours.
- <!-- build: 20261111-0430 --> **Crouch-jumps** ([#20](https://github.com/AyoItzKye/project-proving-grounds/issues/20)): a jump you land during LiDAR mapping with crouch held near its top is saved as a crouch-jump, and bots taking it crouch in the air the same way. Plain jumps stay plain.
- <!-- build: 20261111-0430 --> **Each game's own rules, first part**: in Halo CE and ODST, where health never comes back by itself, a hurt bot goes for a health pack; in Halo CE the bots' motion tracker reaches as far as the game's.
- <!-- build: 20261111-0430 --> **A LiDAR how-to**: the README's Play section walks through scanning a map before your first match on it, a whole game at once, and Forge layouts.
- <!-- build: 20261108-2028 --> **Linux and Steam Deck: whether the bots loaded**: the launcher shows if the last start through Steam's launch option loaded the bots, why not if it didn't, and the exact launch option to paste when the bots have never loaded.
- <!-- build: 20261108-1250 --> **ODST bots in the editor hold the silenced SMG**: the 3D view of your ODST bots, Dare too, shows them with ODST's silenced SMG instead of the assault rifle.
- <!-- build: 20261108-1120 --> **Dare in Halo 3: ODST**: bots can play as Dare, with her helmet on or off, in Firefight, as the other ODST characters do. Pick her in the bot editor, whose 3D view shows her own model. Bots no longer take on your character either: while you played Dare, every bot became Dare too.
- <!-- build: 20261108-1120 --> **8 players in ODST Firefight**: your ODST list holds up to 7 bots, all on your team.
- <!-- build: 20261108-1120 --> **ODST helmets in the re-roll**: choose helmets on, helmets off, or a mix with the share of bots that take theirs off. The Rookie always keeps his helmet and Sgt. Johnson never wears one.
- <!-- build: 20261108-0430 --> **Chat commands for your bots**: type **follow me** in the game's chat and your teammate bots squad up with you, a few steps behind, in any mode; type **roam** and each picks a spot of its own out of the open (covered rooms near the team, kept a while) instead. A message over the game confirms each one. Only these two commands are picked up; anything else you type is dropped at once and never kept.
- <!-- build: 20261108-0430 --> **Generator Defense**: Spartan bots guard the generators, one beside each, and lock one down (holding Use at it) when it takes damage or a squad is on it, never for a Grunt or two and never two locks within 10 seconds; Elite bots shoot the generators that are open, never a locked one, and wait out a lock by hunting.
- <!-- build: 20261108-0230 --> **Firefight bots**: the BOTS tile and panel in the Reach and ODST Firefight lobbies, next to START, with Firefight's own bot list (your 16-player list is kept as it is). Teammates stay a few steps behind you and fight what comes; while you're down they hold a safe spot nearby.
  - **Reach: Firefight Versus and Generator Defense**: the list has a Spartan team and an Elite team, up to 4 each, 8 players in all with you (MCC's custom Firefight). Bots on the Elite team play as Elites beside the Covenant, and at each turn they swap sides with the Spartans as the game does. A fifth bot on a side is refused, with a message saying why.
  - **ODST** keeps its own list of bots on your team.
- <!-- build: 20261108-0230 --> **Bots that know the Covenant**: in Firefight bots tell every enemy apart (Grunt, Jackal sniper, Elite Ultra, Hunter, Brute Chieftain and the rest) and shoot the most dangerous first: a fuel rod Grunt before an Elite, an Engineer before anything, a Hunter that is right on them over all. In Versus a player Elite is worth a life, so Spartans go for one when the team's lives run low.
  - Spartan bots fall back sooner as the team's shared lives run out. Elite bots never trade their life: they hunt the Spartan who is alone or out of shields, move with the biggest Covenant squad, back off to recharge, and late in a turn with the Spartans low they hang back and run the clock.
- <!-- build: 20261108-0230 --> **Halo 3: ODST bots with their own looks** ([#15](https://github.com/AyoItzKye/project-proving-grounds/issues/15)): each bot plays as its own ODST, The Rookie, Mickey, Dutch, Romeo, Buck or Sgt. Johnson (with Modern also Bug-splattered Buck and Injured Romeo), with or without the helmet, in its own two colours. The bot profile editor has Halo 3: ODST with a 3D view of the bot to pick its character, helmet and colours.
- <!-- build: 20261107-1945 --> **Halo 2 vehicles**: bots get into vehicles in Halo 2. They drive Warthogs, Ghosts and Scorpions, fly Banshees, and man Warthog chainguns and gauss guns, firing Ghost and Banshee bolts and Scorpion shells (seen in real matches on Coagulation and Containment).
- <!-- build: 20261107-1945 --> **Halo 2 boosts and the Scorpion's machine gun**: on the right click, as players use it. Ghosts, Spectres, Banshees and Wraiths boost on open stretches (the Wraith in short bursts), and Ghosts and Wraiths also boost into a player close ahead; the Scorpion's driver uses its machine gun on players on foot close by.
- <!-- build: 20261107-1530 --> **Banshee bombs in Halo 4**: bots switch to the bomb like a second weapon, drop it with the main trigger and switch back, the way players do it (five bombs in a five-minute match).
- <!-- build: 20261107-1400 --> **Halo 4, the Mantis**: bots get in, walk it, fire its machine gun, stomp anyone and any vehicle beside it, and fire its rockets the way a player holds them: a short hold at a soldier for one or two rockets, a long hold at a vehicle to lock on and fire a full salvo (seen in matches on Forge Island).
- <!-- build: 20261107-0100 --> **Aiming at the head**: in Reach and Halo 4 bots aim where an enemy's head really is, as it moves when he strafes and crouches. Their aim is as good as before, just aimed at the right spot.
- <!-- build: 20261107-0100 --> **DMR over the assault rifle** (Reach, Halo 4): a bot with a loaded DMR uses it at every range, never drops a DMR for an assault rifle, and gives up the assault rifle for a DMR.
- <!-- build: 20261107-0100 --> **LiDAR mode** records where people and bots drive and fly, and the LiDAR Viewer shows it (V).
- <!-- build: 20261106-2300 --> **Call a bot into your vehicle**: aim at a teammate bot and press the horn (crouch) while driving, and that bot gets in (Halo 3, Reach, Halo 2 Anniversary, Halo 4). Stopping next to a bot still calls the nearest one.
- <!-- build: 20261106-2300 --> **Aircraft pick up bots**: land an aircraft next to teammate bots and they get in, both of a Falcon's gunner seats too. Bots flying one do the same for their teammates.
- <!-- build: 20261106-2300 --> **The launcher's What's new**: when an update is out, it lists everything added and fixed since the copy you have, same-day updates of a version included.
- **Update check in the launcher**: it checks GitHub for a new version (at most every 6 hours, or with **Check**), shows when it last checked, and tells you when one is out. **Auto-update** is off unless you turn it on; nothing is ever installed without it or the **Update** button.
- **Observer**: the game list shows games only. A game with bug reports has a flag, and a **Bug reports** section lists each report with its time; click one to jump to that moment.
- **A real player's guide**: **Read the guide** in the launcher opens a searchable guide in the mod's own window.
- **The launcher** in the Proving Grounds art's colours, with the sign as the app icon.
- **Flight heights from the map**: aircraft pick their attack and travel heights from the ground under them; painting airspace is optional.

### - Fixed
- <!-- build: 20261112-1306 --> **Firefight teammates stay with you**: in ODST and Reach Firefight, the bots following you no longer run off for the sniper or rockets across the map and turn back at every wave; they take guns near you, and hold where you were while you respawn.
- <!-- build: 20261112-0929 --> **Reach Generator Defense** ([#18](https://github.com/AyoItzKye/project-proving-grounds/issues/18)): the bots read the generators again, take their posts at them and lock them down (the last two updates had them play plain Firefight). The same fix brings back the Forge pieces of Reach map variants and the bots' read of Firefight enemies' ranks.
- <!-- build: 20261112-0833 --> **High Ground CTF**: the base's gate counts as a wall while it is shut (bots kept walking into it and both teams piled up in front of it), and a flag runner close to the enemy flag with a teammate beside it goes for the flag instead of fighting on. The same goes for every Halo 3 door that only a switch opens, such as Orbital's large doors.
- <!-- build: 20261112-0424 --> **A better gun close by is taken again**: away from their objective, bots pick up a better gun lying a few steps off again (in the last version they walked past it); next to the objective they still stay on the job.
- <!-- build: 20261112-0424 --> **CTF attacks that never got going**: when two attack waves in a row never gather (their meeting spot keeps getting fought over, as on High Ground), the attackers stop waiting for waves for a minute and go for the flag on their own. On High Ground they now reach the flag and capture it.
- <!-- build: 20261112-0058 --> **Objective first**: bots on an objective job (carrying, guarding, escorting, hunting the carrier, taking a zone) no longer walk off for a gun next to the objective. They take a gun only when out of ammo, when it lies on their way, or when it is a power weapon close by.
- <!-- build: 20261112-0058 --> **No bot ignores the objective**: personalities still decide how a bot fights, but none of them cares less about the objective than an average player.
- <!-- build: 20261112-0424 --> **Legendary sharper, Normal as before**: Legendary bots aim a little tighter and follow a moving target a little faster; Normal bots play exactly as they did before this version.
- <!-- build: 20261111-2343 --> **Oddball, teammates guard the carrier from anywhere**: a teammate far from your team's ball carrier (yours or a bot's) heads straight back to him, past guns, vehicles and radar dots, and nobody guarding or hunting a carrier is sent off for a power weapon while the ball is held.
- <!-- build: 20261111-2259 --> **Oddball, the ball and its carrier first**: a bot near the loose ball picks it up before anything else (a man at arm's length aside). Bots hunting the carrier go straight at him in every lobby, two teams or eight, fighting only men who are right on them or shooting them, and no longer walk off to guns or far-away vehicles. Every carrier's teammates, a bot carrier's too, stay with him instead of chasing fights and guns.
- <!-- build: 20261111-2146 --> **Shooting through walls**: bots fire only when the bullet itself has a line to the part of you they aim at (your head, when only your head shows over cover). They no longer learn see-through spots in solid walls from hits landed as someone went round a corner, and spots learned that way before are dropped.
- <!-- build: 20261111-2146 --> **Oddball: the carrier is the target**: enemy bots go after the ball carrier in every lobby, fighting his teammates in their way, instead of wandering off to guns and vehicles. Your teammates watching over you stay near you.
- <!-- build: 20261111-2146 --> **Vehicle gunners keep firing**: a gunner holds the trigger down while you are roughly in its sights, through brief swings off you, and aims a mounted gun twice as steadily as a hand gun.
- <!-- build: 20261111-2146 --> **Steam Deck and Linux look**: the desktop icon shows the Project Proving Grounds sign, and the pages use the Deck's own font so text stays in its boxes (the Observer's stats table no longer runs past its panel).
- <!-- build: 20261111-1901 --> **Ghosts**: a bot that drives a Ghost into a group fights from it instead of getting out among them.
- <!-- build: 20261111-1901 --> **Scores in games of three teams or more**: every team's score is read (only two were), so the bots know who is winning.
- <!-- build: 20261111-1901 --> **Ball carriers on maps nobody has played Oddball on yet**: they pick a covered spot with ways out, not just the one farthest from the enemy.
- <!-- build: 20261111-1737 --> **Hunters go for the ball carrier**: in Oddball and King of the Hill with three teams or more, bots sent after the ball carrier no longer get drawn into fights with the other teams, and teammates escorting a carrier no longer ride off in vehicles.
- <!-- build: 20261111-1737 --> **Capture the Flag team splits**: with both flags home about a quarter of the team defends and the rest attack; when your flag is taken, half go after it and half keep attacking (One Flag: everyone goes after it), and nobody guards an empty stand.
- <!-- build: 20261111-1737 --> **Vehicles**: bots no longer get sent to drive Mongooses or Elephants; a bot rides a Mongoose only to cross the map. At most two Warthogs get crews (one for the attack, one for the defence) and one Ghost.
- <!-- build: 20261111-1737 --> **Halo 3 CTF on saved map variants**: a variant whose flag stands moved (for example a saved Sandtrap layout) played as Slayer; the bots now find its flag.
- <!-- build: 20261111-1737 --> **LiDAR Simulator**: it no longer stops while its own "Simulate every map?" question is open, and an empty Forge canvas is listed as nothing to scan instead of failing.
- <!-- build: 20261111-1325 --> **Capture the Flag: runners turning back**: bots sent for the enemy flag kept being switched to other jobs (a gathering point, a vehicle's crew, a teammate taking their place after a death) and walked back toward their own base, most on big maps like Sandtrap. A runner now keeps going for the flag while both flags are home.
- <!-- build: 20261111-1325 --> **Lifts and man cannons in Halo 2 Anniversary and Halo 4**: rides you take on them are now learned for the bots (they were left out because nobody presses jump on a man cannon).
- <!-- build: 20261111-0430 --> **Sandtrap's Elephants**: bots go round an Elephant instead of running into its side, and flag carriers score on its second floor: up the ramp, then a crouch-jump onto the deck or the stairs, or in by the tire wells and the jumps at the back and front. A flag stand on an Elephant that drives off is followed where it goes.
- <!-- build: 20261111-0430 --> **Flag carriers and vehicles** ([#16](https://github.com/AyoItzKye/project-proving-grounds/issues/16)): a bot driving with a flag carrier aboard (you or a bot) drives the carrier home instead of getting out, a bot carrier that gets into a seat stays in until it's home, and a bot carrier gets into a teammate's vehicle, yours too, when it's right beside it. Escorts far from their flag carrier head straight for the carrier.
- <!-- build: 20261111-0430 --> **Respawn countdown beeps** ([#22](https://github.com/AyoItzKye/project-proving-grounds/issues/22)): in Reach and ODST you no longer hear every bot's respawn countdown, only your own.
- <!-- build: 20261111-0430 --> **Halo 2 Anniversary Forge maps** ([#23](https://github.com/AyoItzKye/project-proving-grounds/issues/23)): bots join layouts built on Skyward and the other Forge maps, walking the layout's own pieces (they refused to join before).
- <!-- build: 20261111-0430 --> **Halo CE pickup messages** ([#21](https://github.com/AyoItzKye/project-proving-grounds/issues/21)): a bot picking up grenades, a power-up or a gun no longer shows you its pickup message or plays its pickup sound.
- <!-- build: 20261111-0430 --> **ODST weapons** ([#17](https://github.com/AyoItzKye/project-proving-grounds/issues/17)): bots know which guns they hold and which lie around, so they switch to their SMG up close, see dropped guns, and know Firefight's sniper rifle and rocket launcher in their weapon boxes.
- <!-- build: 20261111-0430 --> **Invasion objectives**: attackers running to an objective being taken keep going when someone shoots them from across the map; only a shooter within about 25 units turns them.
- <!-- build: 20261111-0430 --> **Aircraft under a ceiling**: pilots no longer pull up into the top of the map (Spire's peak), bobbing against it.
- <!-- build: 20261111-0430 --> **Vehicle gunners**: a side gun (the Falcon's) shoots only targets on its own side, and the chaingun keeps firing where an enemy just ducked out of sight.
- <!-- build: 20261111-0430 --> **Bots stuck hopping at a ledge**: a bot hopping in place against a lip now counts as stuck and works its way out (Halo CE bots hopped at one for half a minute).
- <!-- build: 20261111-0430 --> **A gun gone mid-read**: a gun picked up or despawned while the bots read it no longer stops them for the match.
- <!-- build: 20261110-0940 --> **Bots reach the flag and the hill**: on Narrows and seven other maps, spots the bots had learned as out of bounds next to a flag stand or hill kept them a few steps short of it, so they never picked up the flag. On maps whose deadly falls the bots already know, those learned spots are gone and no new ones are learned.
- <!-- build: 20261110-0940 --> **Reach Stockpile on Boardwalk**: bots now see the flags and where to take them (they saw none, and matches ended 0-0). The same goes for any Reach map variant whose file leaves out a mode's places.
- <!-- build: 20261110-0940 --> **Broken map files**: two saves at the same moment no longer leave a map's learned file broken, and a broken one no longer stops the next match from starting (it's set aside and learned again).
- <!-- build: 20261108-2338 --> **Man cannons: in from the back, straight through**: bots go into a man cannon only through its entrance at the back (Narrows' cannons are a short lane between two fins) instead of pushing at a fin from the walkways beside it, run straight through without stopping or hopping at the foot, fly on toward the landing for the whole throw instead of braking halfway across, and keep using the cannon after a ride (a ride counted as a missed jump and kept them off it for a minute). Flag carriers take it too; bots walk the long way round only when the lane is jammed with players.
- <!-- build: 20261108-2217 --> **Bots ride man cannons and lifts**: bots take a man cannon that throws them across the map (Narrows) when it's the quick way to where they're going, from both bases, and they ride every lift and man cannon, flag carriers too, even when an enemy watches the exit; they still never walk into the exit end of a one-way lift.
- <!-- build: 20261108-2028 --> **Tool windows close their tool**: closing the LiDAR Viewer, LiDAR Simulator, Observer or Paint the nav window now ends that tool instead of leaving it running unseen (the Simulator saves the map it was on first).
- <!-- build: 20261108-1955 --> **Theater with bots in Halo 3, ODST, Halo 2 Anniversary and Halo 4**: films of bot matches play with the bots in them instead of crashing or stopping; the bots weren't added into the film by mistake any more.
- <!-- build: 20261108-1639 --> **BOTS panel moving on its own**: after a match the panel could run through its options by itself as if an arrow key were held down; a key let go while the match was ending is no longer taken as still held.
- <!-- build: 20261108-1610 --> **ODST bots' left hand on the SMG**: in the editor the left hand now sits higher and fully on the SMG's foregrip.
- <!-- build: 20261108-1540 --> **ODST bots in the editor hold the SMG tucked in**: the silenced SMG sits against the chest instead of out in front, and the left hand wraps the foregrip instead of sitting just behind it.
- <!-- build: 20261108-1445 --> **ODST bots in the editor hold the silenced SMG in both hands**: across the body like the other games' bots, the muzzle down toward the left knee, the left hand round the gun's front grip with the elbow bent; the last update had them holding it in one hand.
- <!-- build: 20261108-1320 --> **ODST bots in the editor**: they hold the silenced SMG in the right hand with the left arm at their side; the left arm went through the chest in the last update.
- <!-- build: 20261108-0930 --> **Follow me and roam hold up in Firefight**: after **follow me** your bots stay beside you through Covenant waves instead of running off for plasma pistols or to chase a Wraith, and one never parks a few metres off when its spot beside you is blocked. After **roam** each bot fights from its own covered spot instead of stepping into the open, keeps that spot when a teammate dies, and picks covered spots close to you instead of rooms across the map.
- <!-- build: 20261108-0930 --> **Bots stuck boarding**: a bot that cannot get to an enemy vehicle (one parked below a ledge, say) gives up on it after a few seconds instead of standing over it.
- <!-- build: 20261108-0645 --> **Generator Defense guards stay on their generator**: each Spartan bot now keeps its own generator for the whole match (they used to swap generators every time one died), comes back at the respawn spot nearest its generator and walks straight to it, and locks a generator down every time it is needed (only the first lock of a match went through before).
- <!-- build: 20261108-0430 --> **Bots stuck by a step**: a bot rocking back and forth at one spot on its way somewhere now counts as stuck and works its way out.
- <!-- build: 20261108-0230 --> **Firefight respawns on the Elite side** ([#12](https://github.com/AyoItzKye/project-proving-grounds/issues/12)): bots on the Elite side never came back after dying; they now respawn after the Elites' longer wait, at the Elites' spawn, and after a turn swap each bot respawns on its new side.
- <!-- build: 20261107-2240 --> **The BOTS panel**: opening a bot's profile no longer stops the game with an error box; a controller's stick resting a little off centre no longer scrolls the panel's lists by itself (only a real push moves them); closing it with Esc no longer backs you out of the lobby, and the BOTS tile no longer shows on top of the post-game scoreboard.
- <!-- build: 20261107-2115 --> **The update notes**: each version is now one list of what was added and one of what was fixed, here, on the Releases page and in the launcher's What's new, instead of a separate dated note for every update.
- <!-- build: 20261107-1945 --> **Halo 2 Containment**: bots never started there (the map's name could not be read), and in Capture the Flag the bots stopped on the first moment of the match.
- <!-- build: 20261107-2145 --> **Halo 2 vehicles on their side**: bots now see when a Halo 2 vehicle is on its side or roof and leave it alone, and a vehicle that lets a bot in and puts it straight back out is left alone for a while too.
- <!-- build: 20261107-1530 --> **Halo 3 and Halo 4 Banshees** no longer press the second trigger as if it were the bomb.
- <!-- build: 20261107-1200 --> **Theater with bots in Halo 4**: films of bot matches play with their bots instead of crashing as the bots join (a 12-minute Forge Island film matched its match's score at every point checked). Theater with bots now works in Reach and Halo 4.
- <!-- build: 20261107-0230 --> **Halo: Reach Invasion**:
  - Attackers take and hold the territories from inside them, and shoot on the way in instead of stopping to fight far from the objective.
  - The core carrier no longer drops the core by meleeing, and a dropped core is picked up again at once.
  - On Spire the attackers climb to the core and spread over every way up it (both grav lifts and the three man cannons) in phase 3 and during their all-out pushes, instead of all queuing for one lift, and no longer stop for guns on the core run. Bots know the man cannons only appear in phase 3 and that the grav lifts only reach the top in phase 3.
  - A bot sent to a man cannon walks onto its pad and stays there until it launches.
  - Banshees fly the spire closer and lower with real attack runs instead of creeping around it, stay under the map's ceiling, and make bomb runs into the phase 2 objective rooms.
  - Bots no longer get stuck on Boneyard's stairs, plank and walkway ([#4](https://github.com/AyoItzKye/project-proving-grounds/issues/4)) or in the rock on the way to Spire's B.
  - Both teams play with the same brain (team 2 was always thinking last).
- <!-- build: 20261107-0230 --> **Aircraft landing**: a bot flying to the objective sets down where there is room near it (within about 10 units) and gets out, instead of circling over Spire's top.
- <!-- build: 20261107-0100 --> **Falcons**: bots no longer jump out in mid-air or when you take the gun. A bot pilot that lands to pick up a gunner waits for him (up to 20 seconds) and waits a moment when you stand next to it, fetches gunners, stays under the map's kill ceiling, and flies onto the top of Spire from outside instead of up under it.
- <!-- build: 20261107-0100 --> **Vehicles during a push**: while the team pushes the objective together, bots still get into your landed aircraft and its guns, a free power vehicle (like a Banshee) still gets a driver, and empty guns still get gunners.
- <!-- build: 20261107-0100 --> **Snipers and reloads**: bots no longer trade a sniper rifle that still has rounds for another gun, and reload magazines they had only seen part empty.
- <!-- build: 20261107-0100 --> **Breakpoint**: bots on the bridge see, and shoot at, players on the tower ledge.
- <!-- build: 20261107-0100 --> **Bots joining**: all the bots you asked for join even if you open the pause menu while they do (Halo 3: ODST Firefight had one of three).
- <!-- build: 20261107-2145 --> **Warthog gunners** aim from the gun itself, in Halo 2 too and on slopes in every game, so their shots no longer drift to one side of the target or over it (Halo 2 gunners hit with 43% of their firing instead of 26% in matches on Coagulation). A bot mans your Warthog's gun when you drive.
- <!-- build: 20261106-2300 --> **Grenades**: bots no longer throw a grenade where a teammate (or you) is standing or about to walk.
- <!-- build: 20261106-2300 --> **Bug reports**: a report saves where you were when you pressed Save, and reports no longer fail to file now and then.
- <!-- build: 20261106-2300 --> **Halo 4 Flood and Infection**:
  - Human bots shoot the magnum at a Flood on its way in, switch to the shotgun before it gets close, and hold their ground with it instead of walking into the sword or sprinting around it with their backs turned. Against enemies with guns nothing changes.
  - A bot that loses sight of a Flood or zombie for a moment keeps fighting him instead of walking back to its spot.
  - Human bots hide in places people actually play (on Blood Cavern they crowded against a wall trying to reach a floor nobody can get to), and no longer get stuck on its upper walkway on the way to the hiding spot by the back lift.
  - Survivors shoot the Flood instead of hiding behind the hardlight shield; it comes out only as a short block when reloading (then a melee), when swarmed, or when cornered.
- <!-- build: 20261106-1840 --> **Gravity lifts**: bots no longer try to go down a lift from its top end (Blood Cavern's back lift, and the low lifts on Halo 2 Anniversary's Lockout and Reach's Ivory Tower).
- <!-- build: 20261106-1440 --> **Firefight** ([#12](https://github.com/AyoItzKye/project-proving-grounds/issues/12)):
  - Bots respawn when they die, the same way you do: after the same wait, at the same spawn point, and each respawn uses one of your team's shared lives.
  - Bots join on Installation 04 and Reach's DLC Firefight maps.
  - A bot that runs out of ammo goes for a dropped gun, a Covenant one included; Reach bots read how many rounds they have left.
  - Bots only melee when an enemy is right in front of them (they used to swing at the air and hit teammates).
  - Your teammates stay on foot with you instead of taking vehicles across the map, and on the Elite side bots fight beside the Covenant instead of shooting them.
  - After a match on Unearthed or Installation 04, that match's bot brain no longer keeps running into the next one.
  - The BOTS tile no longer covers the last stat on the Firefight post-game screen.
- **Halo 3 trip mines**: bots see thrown equipment (trip mines, bubble shields, regenerators and the rest) and route around an enemy trip mine instead of walking into it ([#9](https://github.com/AyoItzKye/project-proving-grounds/issues/9)).
- **Halo: Reach weapon pickups**: bots see and pick up the weapons placed on a Forge creation ([#11](https://github.com/AyoItzKye/project-proving-grounds/issues/11)), and a dropped gun that isn't on one of the map's weapon spots, when their own guns run dry.
- **Halo 2 Anniversary**: bots pick up the Assault bomb, which needs Use held ([#7](https://github.com/AyoItzKye/project-proving-grounds/issues/7)), and the enemy flag in CTF again.
- **Vehicles**: bots take empty Banshees, and aircraft climb over the Spire instead of flying into its side.
- **Jetpacks**: bots let them refill before flying again.
- **Paint the nav**: works in an installed copy, and opens a map straight away.
- **LiDAR Viewer and Simulator**: the Viewer shows maps you mapped in the Simulator, with its controls grouped and a map's Forge layouts in one drop-down; the Simulator no longer cuts maps short at Max speed ([#8](https://github.com/AyoItzKye/project-proving-grounds/issues/8)) and starts bots inside Forge creations ([#10](https://github.com/AyoItzKye/project-proving-grounds/issues/10)).
- **Windows**: windows the launcher opens come to the front instead of opening behind it.
- **In-game UI**: the BOTS tile and the **Report bot bug** button are placed correctly at every resolution, not just ultrawide.

</details>

<details>
<summary><b>0.2.1</b> (November 2026): melee weapons, Infection and Flood, wrecks, LiDAR, Theater, a new launcher</summary>

### + Added
- **Energy sword and gravity hammer**: bots lunge the moment the reticle turns red and get kills with them in Halo 3, Reach and Halo 4. Sword fights: Normal bots and up follow a clash with a quick melee.
- **Infection and Flood**: survivors hold rooms with few entrances in small groups; zombies hunt, wait at corners, then rally and charge together. Halo 4 Flood is read as Flood and Flood use their thrusters; survivors dodge lunges. ([#3](https://github.com/AyoItzKye/project-proving-grounds/issues/3))
- **Choose which MCC to use**: the launcher's Game folder setting lets you pick any copy of MCC or go back to the one Steam installed. ([#1](https://github.com/AyoItzKye/project-proving-grounds/issues/1))
- **Boarding**: bots board a distracted enemy Scorpion or Wraith from the front and beat the driver out.
- **Windows and fences**: bots see enemies through glass and fences, shoot through fences, railings and glass that breaks, and walk around bulletproof glass instead of firing into it.
- **Kill zones from the maps**: bots stay out of each map's kill zones and "return to the battlefield" areas, on foot, in vehicles and in the air.
- **Race and Regicide**: played as their own modes (Halo: CE and Reach Race, Halo 4 Regicide) instead of as Slayer.
- **LiDAR**: the Viewer and the Simulator are separate windows (the Viewer shows your LiDAR match live). A LiDAR run visits every gametype objective on the map, rides lifts and man cannons, and a director sends bots to the parts of the map not mapped yet.
- **Observer**: keeps your newest 5 games (a Keep game button saves one for good) and trims long recordings to the last 15 minutes, both changeable in Recording settings. It also lists games recorded by another copy of the mod.
- **A redesigned launcher**: status at a glance, a big Play button, a tools grid, everything fits the window.
- **Linux and Steam Deck**: a first installer for Linux and SteamOS (through Proton), as its own download.
- **Legendary bots walk in on their target** instead of strafing in place (Heroic half the time); sniper rifles and launchers are unchanged.

### - Fixed
- Bots no longer get into destroyed vehicles in Halo 2 Anniversary, Halo 3, Reach and Halo 4.
- Halo 4 Flood's first round no longer ends right away.
- Infection zombies no longer walk off to pick up guns, ride Mongooses or hide from far-off shotguns; Flood no longer spawn with DMRs; sides no longer mix up after the first round; Infection and Flood no longer give bots custom loadouts.
- Reach Theater films of bot matches play again (films are now kept in one place for every copy of the mod).
- Observer, LiDAR Viewer and Paint the nav open every time, not just once.
- The Observer's game list is no longer empty when the games were recorded by the other copy of the mod.
- Bots stop walking into the same ledge or wall over and over (a route that dropped through a ledge's own floor; Halo 4's height read).
- Bots no longer drop into pits they cannot climb out of (Construct's lift wells) when following LiDAR routes.
- Banshee and other aircraft pilots fire through their attack runs instead of pulling up at every building.
- King of the Hill in Halo 3 keeps the hill when you stand in it (the game hides the hill marker from you there).

</details>

<details>
<summary><b>0.2.0</b> (November 2, 2026): own app window, no key logging, setup fixes</summary>

### + Added
- Repair and Uninstall buttons in the launcher.
- The launcher and the tools open in the mod's own window instead of Microsoft Edge: no browser profile, no account sign-in, no synced extensions.

### - Fixed
- The first-time setup works when some MCC games are not installed or MCC's menu art is missing, and finds MCC in the right Steam library.
- No console windows flash while the launcher or the setup runs.
- The Data collector no longer records any keys or controller buttons, only what the game itself knows (positions, aim, guns, rounds, equipment). Exports leave out the keys 0.1.0 recorded.
- The installer makes clear that the Windows Security exclusion is required.

</details>

<details>
<summary><b>0.1.0</b> (November 1, 2026): the first release</summary>

### + Added
- Bots in Halo: CE, Halo 2 Classic and Anniversary, Halo 3, Halo: Reach and Halo 4 custom games, plus Reach and ODST Firefight.
- Slayer, CTF and objective modes, vehicles, equipment and armor abilities, team directors with callouts, five difficulties, seven play styles and up to 15 bots.
- The launcher, the Observer and LiDAR mapping.

</details>
