# Known bugs (0.2.0)

What I already know is broken or buggy in this version, so you don't have to report it (but if you find something worse, or a way to make it happen every time, a [bug report](https://github.com/AyoItzKye/project-proving-grounds/issues/new?template=bug_report.yml) still helps).

For everything that works, game by game, see the [bot status sheet](BOT_STATUS.pdf). Things I simply haven't tested in a real match yet are listed there, not here.

## In every game

- **The bots only work in offline custom games with Easy Anti-Cheat off.** Started with anti-cheat on, there is no BOTS tile. This is on purpose.
- **An MCC update can break the mod** until a new version is out: the BOTS tile goes missing or bots don't join. Check the Releases page for a newer version.
- **Windows Security can delete the injector** if the exclusion was not added during install. The launcher says so when you press Play; the README's Troubleshooting section shows the fix.
- **Bots don't crouch-aim at a crouching player on a controller** in Halo: CE, Halo 2, Halo 3 and Reach: the mod can only tell you're crouching from the keyboard's crouch key there. Halo 2 Anniversary and Halo 4 read it from the game.
- **Bots don't pick up weapons off the map in Halo 2 Anniversary and Halo 4** yet. They keep their starting guns.
- **Spectate (no body)** is not available in Halo 2 Anniversary yet.
- **Big maps with many bots can stutter on slower PCs**: use fewer bots.

## Halo: CE

**Not working yet**

- **Race**: Not supported yet: bots play it as Slayer and ignore the checkpoints.

**Works, but buggy**

- **Capture the Flag**: Both teams have captured flags in real matches, but on Blood Gulch the bots rarely make it to the flag.

## Halo 2

**Not working yet**

- **Warthog**: Bots can't get into vehicles in Halo 2 yet.
- **Gauss Warthog**: Bots can't get into vehicles in Halo 2 yet.
- **Ghost**: Bots can't get into vehicles in Halo 2 yet.
- **Banshee**: Bots can't get into vehicles in Halo 2 yet; they walk right past them.
- **Wraith**: Bots can't get into vehicles in Halo 2 yet.
- **Scorpion**: Bots can't get into vehicles in Halo 2 yet.
- **Spectre**: Bots can't get into vehicles in Halo 2 yet.
- **Mounted turrets**: Bots can't use any seat in Halo 2 yet, turrets included.

**Works, but buggy**

- **Team Slayer**: Bots fight really well here (Halo 2 SWAT is my benchmark for Legendary), but they can't use vehicles yet.
- **Capture the Flag**: Bots capture flags, but sometimes a carrier can't score or one team never goes for the flag.

## Halo 2 Anniversary

**Not working yet**

- **Hornet**: Bots can't fly the Hornet yet: they can't make it climb.

**Works, but buggy**

- **Team Slayer**: Plays and scores, but bots can't pick up weapons off the map yet, and a few wander off, even into the water.
- **Capture the Flag**: Bots scored on Zenith, but they get stuck in a few spots on Coagulation.
- **Warthog**: Bots get in, drive and get out, and gunners shoot, but drivers still stall a lot.
- **Gungoose**: A bot drove it once, but never fired its guns.

## Halo 3

**Not working yet**

- **Hornet**: Bots get in but can't make it climb, so it sits on the ground.
- **Elephant**: Bots get in but almost never drive it or use its guns.

**Works, but buggy**

- **Team Slayer**: Some of my best matches with the bots have been Halo 3 Slayer. A weapon-swapping bug was just fixed and needs a recheck.
- **Capture the Flag**: Bots capture flags in shorter matches, but in longer games they don't push the flag enough.
- **Assault**: Bots have carried and armed the bomb, but results are mixed: one match ended 0-0.
- **King of the Hill**: Bots find and hold the moving hill and score, though games tend to be one-sided.
- **Warthog**: Bots drive and gunners shoot, but drivers often park and wait for a crew.
- **Mongoose**: Bots ride it a lot, but mostly park and wait.
- **Chopper**: Bots drive it hard, shoot and boost-ram, though now and then one froze in place.
- **Scorpion**: Bots drive it, but miss a lot of shots and sometimes leave the tank behind.
- **Wraith**: Bots drive and fire it; a fix to its mortar aim still needs a recheck.
- **Banshee**: Bots fly it without getting stuck, but almost never shoot from it.
- **Mounted turrets**: Bots man the turrets and fire; a fix to their aim still needs a recheck.

## Halo 3: ODST

**Not working yet**

- **Warthog**: Bots can't get into vehicles in ODST yet.
- **Mongoose**: Bots can't get into vehicles in ODST yet.
- **Ghost**: Bots can't get into vehicles in ODST yet.
- **Olifaunt**: Bots can't get into vehicles in ODST yet.
- **Mounted turrets**: Bots can't use any seat in ODST yet, turrets included.

## Halo: Reach

**Not working yet**

- **Race (Rocket Race)**: Not supported yet: bots play it as Slayer and ignore the checkpoints.
- **Scorpion**: Bots get in but spend most of the time stuck or standing still.

**Works, but buggy**

- **Capture the Flag**: Bots capture flags and it plays well, but in big games the bot teams don't push the enemy flag enough.
- **Assault**: Bots pick up and carry the bomb, but I haven't seen them score a plant in a real match yet.
- **King of the Hill**: Bots hold the hill and score, but it can feel a little slow on the objective.
- **Territories**: Bots take and hold territories on Boardwalk, Powerhouse and Boneyard; on Spire they struggle.
- **Infection**: It runs, but bots don't reliably tell zombies from humans yet.
- **Headhunter**: Bots head for the drop points, but often without any skulls to bank.
- **Invasion**: Bots take phases and deliver the core, but defending, spawning and holding zones still go wrong too often.
- **Warthog**: Bots drive and gun it, but often drive alone, use it like a taxi and miss shots.
- **Rocket Warthog**: Bots drive it and have used its gun, but they don't lock on or lead the rockets yet.
- **Transport Warthog**: Bots drive it; only the front passenger seat is handled so far.
- **Mongoose**: Bots drive it, but sit still about half the time.
- **Revenant**: Bots drive it, but get stuck on the terrain often.
- **Wraith**: Bots drive and fire it, but wait for a crew and get stuck on the terrain.
- **Banshee**: Bots fly and boost, but sometimes crash into buildings or just use it to get around.
- **Falcon**: Bots fly it, but pilots leave without their gunners, hover in place, and have flown out of bounds.
- **Sabre**: Bots can fly it, but don't use its missiles or other moves yet.
- **Seraph**: Bots can fly it, but don't use its weapons yet.
- **Mounted turrets**: Bots man the turrets and fire, but miss most shots and don't carry a turret they've ripped off.

## Halo 4

**Not working yet**

- **Regicide**: Not supported yet: bots play it as plain Slayer and don't go after the king.
- **Extraction**: Not supported yet: bots play it as Slayer and never plant at the sites.

**Works, but buggy**

- **Team Slayer (Infinity Slayer)**: Plays and scores, and bots ride vehicles, but they can't pick up weapons off the map yet.
- **Free for All**: Plays smoothly, but bots can't pick up weapons off the map yet.
- **King of the Hill**: Bots follow the moving hill, but they stand around a lot and games are one-sided.
- **Warthog**: Bots get in, drive, gun and get out, but drivers stall about half the time.
- **Ghost**: Bots drive it, but stall a lot, rarely fire and can't boost yet.

*Last updated November 1, 2026.*
