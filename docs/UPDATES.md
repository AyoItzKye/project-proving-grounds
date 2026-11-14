# Updates

What changed in each version. Download the newest one from the [Releases page](https://github.com/AyoItzKye/project-proving-grounds/releases/latest). Everything still broken is on the [Known bugs](KNOWN_BUGS.md) page, and every game, mode and vehicle is rated on the [bot status sheet](BOT_STATUS.pdf).

Click a version to see what it added and fixed.

<details open>
<summary><b>0.2.3</b> (November 12 to 14, 2026): Theater for Halo: CE and Halo 2 Classic, ragdolls in Halo: CE, the author's LiDAR scans in the launcher</summary>

### + Added
- <!-- build: 20261112-1342 --> **Author Provided Scans**: the mod author's own LiDAR scans of 129 maps, one zip per game, on the [LiDAR maps release](https://github.com/AyoItzKye/project-proving-grounds/releases/tag/lidar-maps) and linked from each game's folder on the [LiDAR maps page](https://github.com/AyoItzKye/project-proving-grounds/tree/main/lidar-maps). Bots start a map with what the author's scans found there: its floors, jumps, lifts, man cannons and teleporters.
- <!-- build: 20261112-1342 --> **LiDAR scans in the launcher**: open **LiDAR scans**, choose a game and press **Import** to download and add the author's scans of it, or press **Import a shared zip ...** to add a zip another player shared (one map's or a whole game's). An import adds to your own scans and never replaces them; importing the same zip twice adds nothing the second time, and a map your version does not have is skipped and named.
- <!-- build: 20261113-0039 --> **Halo 2 ragdolls in big games**: dead bodies fall as ragdolls in Halo 2 Classic games of 9 or more players too. Before, with more than 8 players every body froze in its death pose. It is part of the mod now: nothing else to run.
- <!-- build: 20261113-1500 --> **Ragdolls in Halo: CE**: dead bodies in Halo: CE multiplayer go limp and fall the way they do in Halo 2 instead of every body playing the same death animation.
  - They topple the way the hit pushed them, are thrown by explosions with their arms and legs trailing, bend only as far as a Spartan can, and come to rest on the real ground, slopes and walls.
  - A body stays where it fell until its player dies again (the **Halo: CE keep dead bodies** switch turns this off).
  - The launcher's new **Settings** card turns Halo: CE ragdolls on or off and sets how heavy the bodies fall (50% to 150%). Changes apply to a game that is already running.
- <!-- build: 20261113-1500 --> **Loading message**: when you press Play, a message at the top of MCC's window shows that Project Proving Grounds is still loading. Open Multiplayer once it closes (a lobby opened earlier has no BOTS panel).
- <!-- build: 20261114-0005 --> **Theater for Halo: CE and Halo 2 Classic**: every Halo: CE and Halo 2 Classic match is recorded and shows in MCC's own Theater (Creative > Theater) with its map picture, title, date and length. Watch it the way Halo 3's Theater works: follow any player in first person (with their HUD and gun; the mouse is a pointer there, to click the controls and the timeline) or third person (Space switches first person, third person and the free camera), fly a free camera, pause, hold **E** to fast forward, skip back or ahead with the arrow keys, and use the timeline, the controls panel (**X**), screenshots and End Film. MCC's Theater keys work, and so does a controller.

### - Fixed
- <!-- build: 20261114-0323 --> **Free for all in Halo: CE**: in a free-for-all game type every bot plays for itself, even when the lobby still has players on red and blue (bots on the same lobby team left each other alone in Rocket Slayer).
- <!-- build: 20261114-0323 --> **Halo: Reach Firefight** ([#28](https://github.com/AyoItzKye/project-proving-grounds/issues/28)): Classic Firefight takes up to 7 bot teammates, 8 players with you.
- <!-- build: 20261114-0323 --> **Firefight** ([#29](https://github.com/AyoItzKye/project-proving-grounds/issues/29)): bots no longer keep shooting at Covenant that are already dead.
- <!-- build: 20261114-0323 --> **Capture the Flag**: bots walk straight onto a flag that stands against a wall (they turned away from it a step short), and in Halo: CE and Halo 2 the mod now counts captures, so the bots know when their team is ahead.
- <!-- build: 20261113-2230 --> **Launcher layout**: Play and the tools on the left, First-time setup with Game folder, LiDAR scans and Settings on the right, both columns the same height; no more empty block beside Play.
- <!-- build: 20261113-1500 --> **Steam Deck**: the **Report bot bug** tab shows in the pause menu only (it stayed up through the whole match), and the launcher's steps for starting a match fit their box on a narrow window.
- <!-- build: 20261113-1500 --> **Halo: CE BOTS panel no longer disappears**: cycling through game types and maps in the lobby could hide the panel for a moment (the check that the lobby is on screen misread the lobby's video now and then); it now takes several misses in a row to count the lobby as gone.
- <!-- build: 20261112-2337 --> **Updates install themselves**: with **Auto-update** on, the launcher downloads a new version as soon as it loads, even while MCC runs, installs it the moment MCC is closed, and opens again on the new version. This works on the Steam Deck and Linux too (your scans, settings and recordings stay).
- <!-- build: 20261112-2117 --> **Picking up the ball in Halo 2**: bots standing on the Oddball ball now pick it up. Halo 2 takes it on a press of the action button, and they were holding it down.
- <!-- build: 20261112-2117 --> **Getting into vehicles in order**: bots take the driver's seat first, then the gun, then a passenger seat. They no longer sit on the gun or in the passenger seat of a vehicle nobody is driving (a bot carrying the objective may still wait in one for its ride).
- <!-- build: 20261112-1632 --> **Elephants**: the hull blocks the bots' sight and shots (they no longer fire at a player on the other side), bots get in by the rear ramp or the front opening and climb to the second floor from inside, and bots standing in the bay or on the deck on their way to a flag capture are no longer walked off it.
- <!-- build: 20261112-1632 --> **Capture the Flag**: after a capture the team keeps attacking (one point up, a quarter of the team defends; two points up, one more stays home). With your vehicle waiting by the enemy flag, the bots grab the flag first and the carrier then gets in; a bot carrying the flag gets in when you pull up beside it, or heads home with no ride.
- <!-- build: 20261112-1507 --> **Bots shoot the man in front of them**: a bot on its way to the flag, a gun, a vehicle or a hunt no longer walks past an enemy right in front of it, only looking at him. It shoots him and keeps going, as a player runs at the flag firing at the defender in his way. Shots it takes from in front are answered the same way.
- <!-- build: 20261112-1342 --> **Exporting a LiDAR scan**: `tools\lidar_share.py export` stopped with an error in an installed copy of the mod; it writes the zip now.

</details>

<details>
<summary><b>0.2.2</b> (November 6 to 11, 2026): Halo 2 vehicles, the Halo 4 Mantis and Banshee bombs, call bots into your vehicle, follow me and roam chat commands, Firefight bots that follow and respawn, Reach Firefight Versus and Generator Defense with Spartan and Elite bots, ODST characters for bots, an Invasion rework, Sandtrap's Elephants, Halo 2 Anniversary Forge maps</summary>

### + Added
- <!-- build: 20261112-0929 --> **Share LiDAR maps**: the new [LiDAR maps page](https://github.com/AyoItzKye/project-proving-grounds/tree/main/lidar-maps) has a folder for each game where players share their scans. `tools\lidar_share.py export <map>` packs your scan of a map into a small zip (nothing personal in it) and `tools\lidar_share.py import <zip>` adds someone else's to yours: floors add up, every jump, ride and teleporter that differs is kept, and your own scan is never replaced. Share one with the Share a LiDAR map form on the issues page.
- <!-- build: 20261112-0929 --> **ODST bots press more buttons**: they melee, throw grenades, reload, crouch and switch weapons in ODST Firefight now.
- <!-- build: 20261112-0424 --> **LiDAR Simulator**:
  - Your own Halo 3, Halo 4 and Halo 2 Anniversary Forge maps are listed with every Forge piece standing, read from the map files themselves, and the bots walk round them.
  - **Every map runs** scans every map of one game in turn, each with its Forge layouts; **Only maps not scanned yet** skips the ones already done; a stopped run picks up where it stopped (**Continue**), and **Skip to next map** moves on when one takes too long. Maps with no edge (Death Island) end once their play area is covered.
- <!-- build: 20261112-0424 --> **Halo 3 Forge maps in a match**: in a Halo 3 custom game on one of your Forge maps, the bots find its map file from the pieces standing in the match and play on its layout (its walls, ramps and blocks), not on the bare map.
- <!-- build: 20261112-0058 --> **Power spots**: bots read every map for good places to hold. An Oddball carrier goes to a room with walls round it, a roof and one or two ways in, where few players die, away from the enemy, and stays there until an enemy reaches it. A bot with a sniper rifle and no objective job takes the best overwatch near it: long sight lines, high ground, a wall at its back.
- <!-- build: 20261112-0058 --> **Territories split like a team**: two bots go for each territory to take, one holds each territory you own (two when the enemy is on it), and the spare joins the most contested one.
- <!-- build: 20261112-0058 --> **Firefight: Hunters, hammer Brutes and sword Elites**: bots back away from one that faces them while they pick off the smaller enemies, and Heroic and Legendary bots circle behind one that is busy with someone else to shoot its back.
- <!-- build: 20261112-0058 --> **CTF: a defender fetches the carrier**: when your flag carrier is far from home and nobody is driving, a defender with an empty vehicle nearby takes it, picks the carrier up and drives him home.
- <!-- build: 20261112-0058 --> **Gametype playbook**: docs/GAMETYPE_PLAYBOOK.md sums up how the bots play every game type.
- <!-- build: 20261111-2146 --> **Updates in the launcher**: the launcher checks GitHub for a new version and lists what was added and fixed since your copy (**What's new**). A segment on the Play button shows a check when you are up to date and a download arrow when a new version is out. **Auto-update** (on unless you turn it off) installs it as soon as MCC is closed.
- <!-- build: 20261111-2146 --> **Bots feel walls**: every bot compares how far it should have moved with how far it really moved. Pushing into something that stops it, it slides along it (in a fight, it strafes the other way) instead of running in place, and a dead stop is remembered for its paths.
- <!-- build: 20261111-1901 --> **Bots act on callouts**: a teammate calling out an enemy near your flag carrier, a defender's post or your stolen flag sends the bots guarding it after him.
- <!-- build: 20261111-1901 --> **Passive LiDAR**: every match you play teaches the bots the map in the background, with nothing on screen and nothing to switch on: the floor you walk, the jumps you land, the lifts, man cannons and teleporters you take, and whether each works both ways. It also learns where you stand guard near your flag and where you hold the Oddball, and the bots defend and carry from those spots. Only your own moves are recorded.
- <!-- build: 20261111-1325 --> **Crouch-jumps** ([#20](https://github.com/AyoItzKye/project-proving-grounds/issues/20)): a jump of yours that lands higher than a plain jump can reach is saved as a crouch-jump, in every game and in LiDAR mapping, and bots taking it crouch in the air the same way.
- <!-- build: 20261111-0430 --> **Each game's own rules, first part**: in Halo CE and ODST, where health never comes back by itself, a hurt bot goes for a health pack; in Halo CE the bots' motion tracker reaches as far as the game's.
- <!-- build: 20261111-0430 --> **A LiDAR how-to**: the README's Play section walks through scanning a map before your first match on it, a whole game at once, and Forge layouts.
- <!-- build: 20261108-2028 --> **Linux and Steam Deck: whether the bots loaded**: the launcher shows if the last start through Steam's launch option loaded the bots, why not if it didn't, and the exact launch option to paste when the bots have never loaded.
- <!-- build: 20261108-1250 --> **Halo 3: ODST bots with their own looks** ([#15](https://github.com/AyoItzKye/project-proving-grounds/issues/15)): each bot plays as its own ODST (The Rookie, Mickey, Dutch, Romeo, Buck, Sgt. Johnson or Dare; with Modern also Bug-splattered Buck and Injured Romeo), with or without the helmet, in its own two colours. The bot editor has Halo 3: ODST with a 3D view holding the silenced SMG, and the re-roll can choose helmets on, off, or a mix. Bots no longer take on your character.
- <!-- build: 20261108-1120 --> **8 players in ODST Firefight**: your ODST list holds up to 7 bots, all on your team.
- <!-- build: 20261108-0430 --> **Chat commands for your bots**: type **follow me** in the game's chat and your teammate bots squad up with you, a few steps behind, in any mode; type **roam** and each picks a spot of its own out of the open (covered rooms near the team, kept a while) instead. A message over the game confirms each one. Only these two commands are picked up; anything else you type is dropped at once and never kept.
- <!-- build: 20261108-0430 --> **Generator Defense**: Spartan bots guard the generators, one beside each, and lock one down (holding Use at it) when it takes damage or a squad is on it, never for a Grunt or two and never two locks within 10 seconds; Elite bots shoot the generators that are open, never a locked one, and wait out a lock by hunting.
- <!-- build: 20261108-0230 --> **Firefight bots**: the BOTS tile and panel in the Reach and ODST Firefight lobbies, next to START, with Firefight's own bot list (your 16-player list is kept as it is). Teammates stay a few steps behind you and fight what comes; while you're down they hold a safe spot nearby.
  - **Reach: Firefight Versus and Generator Defense**: the list has a Spartan team and an Elite team, up to 4 each, 8 players in all with you (MCC's custom Firefight). Bots on the Elite team play as Elites beside the Covenant, and at each turn they swap sides with the Spartans as the game does. A fifth bot on a side is refused, with a message saying why.
  - **ODST** keeps its own list of bots on your team.
- <!-- build: 20261108-0230 --> **Bots that know the Covenant**: in Firefight bots tell every enemy apart (Grunt, Jackal sniper, Elite Ultra, Hunter, Brute Chieftain and the rest) and shoot the most dangerous first: a fuel rod Grunt before an Elite, an Engineer before anything, a Hunter that is right on them over all. In Versus a player Elite is worth a life, so Spartans go for one when the team's lives run low.
  - Spartan bots fall back sooner as the team's shared lives run out. Elite bots never trade their life: they hunt the Spartan who is alone or out of shields, move with the biggest Covenant squad, back off to recharge, and late in a turn with the Spartans low they hang back and run the clock.
- <!-- build: 20261107-1945 --> **Halo 2 vehicles**: bots get into vehicles in Halo 2. They drive Warthogs, Ghosts and Scorpions, fly Banshees, and man Warthog chainguns and gauss guns, firing Ghost and Banshee bolts and Scorpion shells (seen in real matches on Coagulation and Containment).
- <!-- build: 20261107-1945 --> **Halo 2 boosts and the Scorpion's machine gun**: on the right click, as players use it. Ghosts, Spectres, Banshees and Wraiths boost on open stretches (the Wraith in short bursts), and Ghosts and Wraiths also boost into a player close ahead; the Scorpion's driver uses its machine gun on players on foot close by.
- <!-- build: 20261107-1530 --> **Banshee bombs in Halo 4**: bots switch to the bomb like a second weapon, drop it with the main trigger and switch back, the way players do it (five bombs in a five-minute match).
- <!-- build: 20261107-1400 --> **Halo 4, the Mantis**: bots get in, walk it, fire its machine gun, stomp anyone and any vehicle beside it, and fire its rockets the way a player holds them: a short hold at a soldier for one or two rockets, a long hold at a vehicle to lock on and fire a full salvo (seen in matches on Forge Island).
- <!-- build: 20261107-0100 --> **Aiming at the head**: in Reach and Halo 4 bots aim where an enemy's head really is, as it moves when he strafes and crouches. Their aim is as good as before, just aimed at the right spot.
- <!-- build: 20261107-0100 --> **DMR over the assault rifle** (Reach, Halo 4): a bot with a loaded DMR uses it at every range, never drops a DMR for an assault rifle, and gives up the assault rifle for a DMR.
- <!-- build: 20261107-0100 --> **LiDAR mode** records where people and bots drive and fly, and the LiDAR Viewer shows it (V).
- <!-- build: 20261106-2300 --> **Call a bot into your vehicle**: aim at a teammate bot and press the horn (crouch) while driving, and that bot gets in (Halo 3, Reach, Halo 2 Anniversary, Halo 4). Stopping next to a bot still calls the nearest one.
- <!-- build: 20261106-2300 --> **Aircraft pick up bots**: land an aircraft next to teammate bots and they get in, both of a Falcon's gunner seats too. Bots flying one do the same for their teammates.
- **Observer**: the game list shows games only. A game with bug reports has a flag, and a **Bug reports** section lists each report with its time; click one to jump to that moment.
- **A real player's guide**: **Read the guide** in the launcher opens a searchable guide in the mod's own window.
- **The launcher** in the Proving Grounds art's colours, with the sign as the app icon.
- **Flight heights from the map**: aircraft pick their attack and travel heights from the ground under them; painting airspace is optional.

### - Fixed
- <!-- build: 20261112-1306 --> **Firefight** ([#12](https://github.com/AyoItzKye/project-proving-grounds/issues/12), [#18](https://github.com/AyoItzKye/project-proving-grounds/issues/18)):
  - Bots respawn the way you do: after the same wait, at the same spawn point, each respawn using one of your team's shared lives. This works on the Elite side too, and after a turn swap each bot respawns on its new side.
  - Bots join on Installation 04 and Reach's DLC Firefight maps, and every bot you asked for joins even if you open the pause menu while they do.
  - Teammates stay with you: on foot rather than taking vehicles across the map, no running off for the sniper or rockets every wave, and they hold your position while you respawn. After **follow me** they stay beside you through the waves; after **roam** each one fights from its own covered spot near you.
  - Reach Generator Defense: the bots read the generators again; each Spartan bot keeps its own generator for the whole match, goes back to it after respawning, and locks it down whenever needed.
  - A bot out of ammo picks up a dropped gun, Covenant weapons included. Bots melee only enemies right in front of them (they used to hit teammates), and on the Elite side they fight beside the Covenant.
  - A match's bots no longer keep running into the next match after Unearthed or Installation 04, and the BOTS tile no longer covers the last stat on the post-game screen.
- <!-- build: 20261112-0833 --> **Capture the Flag**:
  - With both flags home about a quarter of the team defends and the rest attack; when your flag is taken, half go after it and half keep attacking (One Flag: everyone goes after it), and nobody guards an empty stand.
  - Runners keep going for the flag while both flags are home, instead of being switched to other jobs and walking back (most noticeable on large maps such as Sandtrap).
  - When two attack waves in a row fail to gather, the attackers go for the flag on their own; on High Ground they now capture it.
  - Doors that only a switch opens (High Ground's gate, Orbital's large doors) count as walls while shut, and a runner beside the enemy flag with a teammate nearby takes the flag instead of fighting on.
  - Flag carriers and vehicles ([#16](https://github.com/AyoItzKye/project-proving-grounds/issues/16)): a bot driving a flag carrier drives him home, a bot carrier stays in its seat until it is home and gets into a teammate's vehicle (yours too) when one is right beside it, and escorts far from their carrier head straight for him.
  - Halo 3 map variants with moved flag stands (such as a saved Sandtrap layout) are played as CTF, not Slayer.
  - On Narrows and seven other maps the bots reach the flag stand and the hill; learned out-of-bounds spots next to them had kept the bots a few steps short.
- <!-- build: 20261112-0424 --> **Weapons**: bots on an objective job pick up a gun only when they are out of ammo, when it lies on their way, or when it is a power weapon close by; away from the objective they still take a better gun a few steps off. They no longer trade a sniper rifle that still has rounds for another gun, reload only when they need to, and a gun picked up at the wrong moment no longer stops them for the rest of the match.
- <!-- build: 20261112-0058 --> **No bot ignores the objective**: personalities still decide how a bot fights, but none of them cares less about the objective than an average player.
- <!-- build: 20261112-0424 --> **Legendary sharper, Normal as before**: Legendary bots aim a little tighter and follow a moving target a little faster; Normal bots play exactly as they did before this version.
- <!-- build: 20261111-2343 --> **Oddball**:
  - A bot near the loose ball picks it up before anything else.
  - Enemy bots go straight for the ball carrier in every lobby, two teams or eight, fighting only the players in their way instead of wandering off to guns and vehicles.
  - Teammates guard their carrier (yours or a bot's) from anywhere on the map, and nobody guarding or hunting a carrier leaves for a power weapon or a vehicle while the ball is held.
  - With three teams or more, the bots hunting the carrier are no longer drawn into fights with the other teams.
  - On maps nobody has played Oddball on yet, carriers pick a covered spot with ways out.
- <!-- build: 20261111-2146 --> **Shooting through walls**: bots fire only when the bullet itself has a line to the part of you they aim at (your head, when only your head shows over cover). They no longer learn see-through spots in solid walls from hits landed as someone went round a corner, and spots learned that way before are dropped.
- <!-- build: 20261111-2146 --> **Vehicles**:
  - Gunners aim from the gun itself, in Halo 2 too and on slopes in every game (Halo 2 gunners now hit with 43% of their fire instead of 26% on Coagulation), keep firing through brief swings off target, and a side gun (the Falcon's) shoots only at targets on its own side. A bot mans your Warthog's gun when you drive.
  - Bots are no longer sent to drive Mongooses or Elephants (a Mongoose only to cross the map); at most two Warthogs get crews, one to attack and one to defend, plus one Ghost.
  - A bot that drives a Ghost into a group fights from it instead of getting out.
  - While the team pushes the objective, bots still get into your landed aircraft and its guns, and a free power vehicle such as a Banshee still gets a driver.
  - Halo 2 vehicles on their side or roof are left alone.
  - Aircraft: bots take empty Banshees, set down near the objective and get out instead of circling, stay under the map's ceiling and fly over the Spire instead of into it. Falcon pilots wait up to 20 seconds for their gunners, and nobody jumps out in mid-air. Halo 3 and Halo 4 Banshees no longer use the second trigger as if it were the bomb.
  - Bots let a jetpack refill before flying again.
- <!-- build: 20261111-2146 --> **Steam Deck and Linux look**: the desktop icon shows the Project Proving Grounds sign, and the pages use the Deck's own font so text stays in its boxes (the Observer's stats table no longer runs past its panel).
- <!-- build: 20261111-1901 --> **Scores in games of three teams or more**: every team's score is read (only two were), so the bots know who is winning.
- <!-- build: 20261111-1737 --> **LiDAR Simulator**: it no longer stops while its own "Simulate every map?" question is open, and an empty Forge canvas is listed as nothing to scan instead of failing.
- <!-- build: 20261111-1325 --> **Man cannons and gravity lifts**: bots ride every lift and man cannon when it is the quickest way, flag carriers included. They enter a man cannon from its back and run straight through, never try to go down a one-way lift from its top end, and learn the rides you take in Halo 2 Anniversary and Halo 4.
- <!-- build: 20261111-0430 --> **Sandtrap's Elephants**: bots go round an Elephant instead of running into its side, and flag carriers score on its second floor: up the ramp, then a crouch-jump onto the deck or the stairs, or in by the tire wells and the jumps at the back and front. A flag stand on an Elephant that drives off is followed where it goes.
- <!-- build: 20261111-0430 --> **Respawn countdown beeps** ([#22](https://github.com/AyoItzKye/project-proving-grounds/issues/22)): in Reach and ODST you no longer hear every bot's respawn countdown, only your own.
- <!-- build: 20261111-0430 --> **Halo 2 Anniversary Forge maps** ([#23](https://github.com/AyoItzKye/project-proving-grounds/issues/23)): bots join layouts built on Skyward and the other Forge maps, walking the layout's own pieces (they refused to join before).
- <!-- build: 20261111-0430 --> **Halo CE pickup messages** ([#21](https://github.com/AyoItzKye/project-proving-grounds/issues/21)): a bot picking up grenades, a power-up or a gun no longer shows you its pickup message or plays its pickup sound.
- <!-- build: 20261111-0430 --> **ODST weapons** ([#17](https://github.com/AyoItzKye/project-proving-grounds/issues/17)): bots know which guns they hold and which lie around, so they switch to their SMG up close, see dropped guns, and know Firefight's sniper rifle and rocket launcher in their weapon boxes.
- <!-- build: 20261111-0430 --> **Invasion objectives**: attackers running to an objective being taken keep going when someone shoots them from across the map; only a shooter within about 25 units turns them.
- <!-- build: 20261111-0430 --> **Stuck bots**: a bot hopping against a ledge, rocking back and forth at a step, or unable to reach an enemy vehicle now counts as stuck and works its way out, or gives up after a few seconds.
- <!-- build: 20261110-0940 --> **Reach Stockpile on Boardwalk**: bots now see the flags and where to take them (they saw none, and matches ended 0-0). The same goes for any Reach map variant whose file leaves out a mode's places.
- <!-- build: 20261110-0940 --> **Broken map files**: two saves at the same moment no longer leave a map's learned file broken, and a broken one no longer stops the next match from starting (it's set aside and learned again).
- <!-- build: 20261108-2028 --> **Tool windows close their tool**: closing the LiDAR Viewer, LiDAR Simulator, Observer or Paint the nav window now ends that tool instead of leaving it running unseen (the Simulator saves the map it was on first).
- <!-- build: 20261108-1955 --> **Theater with bots** in Halo 3, ODST, Reach, Halo 2 Anniversary and Halo 4: films of bot matches play with the bots in them instead of crashing or stopping.
- <!-- build: 20261108-1639 --> **BOTS panel moving on its own**: after a match the panel could run through its options by itself as if an arrow key were held down; a key let go while the match was ending is no longer taken as still held.
- <!-- build: 20261108-1610 --> **ODST bots in the editor hold the silenced SMG properly**: in both hands across the body like the other games' bots, tucked against the chest, with the left hand fully on the front grip.
- <!-- build: 20261107-2240 --> **The BOTS panel**: opening a bot's profile no longer stops the game with an error box; a controller's stick resting a little off centre no longer scrolls the panel's lists by itself (only a real push moves them); closing it with Esc no longer backs you out of the lobby, and the BOTS tile no longer shows on top of the post-game scoreboard.
- <!-- build: 20261107-1945 --> **Halo 2 Containment**: bots never started there (the map's name could not be read), and in Capture the Flag the bots stopped on the first moment of the match.
- <!-- build: 20261107-0230 --> **Halo: Reach Invasion**:
  - Attackers take and hold the territories from inside them, and shoot on the way in instead of stopping to fight far from the objective.
  - The core carrier no longer drops the core by meleeing, and a dropped core is picked up again at once.
  - On Spire the attackers climb to the core and spread over every way up it (both grav lifts and the three man cannons) in phase 3 and during their all-out pushes, instead of all queuing for one lift, and no longer stop for guns on the core run. Bots know the man cannons only appear in phase 3 and that the grav lifts only reach the top in phase 3.
  - A bot sent to a man cannon walks onto its pad and stays there until it launches.
  - Banshees fly the spire closer and lower with real attack runs instead of creeping around it, stay under the map's ceiling, and make bomb runs into the phase 2 objective rooms.
  - Bots no longer get stuck on Boneyard's stairs, plank and walkway ([#4](https://github.com/AyoItzKye/project-proving-grounds/issues/4)) or in the rock on the way to Spire's B.
  - Both teams play with the same brain (team 2 was always thinking last).
- <!-- build: 20261107-0100 --> **Breakpoint**: bots on the bridge see, and shoot at, players on the tower ledge.
- <!-- build: 20261106-2300 --> **Grenades**: bots no longer throw a grenade where a teammate (or you) is standing or about to walk.
- <!-- build: 20261106-2300 --> **Bug reports**: a report saves where you were when you pressed Save, and reports no longer fail to file now and then.
- <!-- build: 20261106-2300 --> **Halo 4 Flood and Infection**:
  - Human bots shoot the magnum at a Flood on its way in, switch to the shotgun before it gets close, and hold their ground with it instead of walking into the sword or sprinting around it with their backs turned. Against enemies with guns nothing changes.
  - A bot that loses sight of a Flood or zombie for a moment keeps fighting him instead of walking back to its spot.
  - Human bots hide in places people actually play (on Blood Cavern they crowded against a wall trying to reach a floor nobody can get to), and no longer get stuck on its upper walkway on the way to the hiding spot by the back lift.
  - Survivors shoot the Flood instead of hiding behind the hardlight shield; it comes out only as a short block when reloading (then a melee), when swarmed, or when cornered.
- **Halo 3 trip mines**: bots see thrown equipment (trip mines, bubble shields, regenerators and the rest) and route around an enemy trip mine instead of walking into it ([#9](https://github.com/AyoItzKye/project-proving-grounds/issues/9)).
- **Halo: Reach weapon pickups**: bots see and pick up the weapons placed on a Forge creation ([#11](https://github.com/AyoItzKye/project-proving-grounds/issues/11)), and a dropped gun that isn't on one of the map's weapon spots, when their own guns run dry.
- **Halo 2 Anniversary**: bots pick up the Assault bomb, which needs Use held ([#7](https://github.com/AyoItzKye/project-proving-grounds/issues/7)), and the enemy flag in CTF again.
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
