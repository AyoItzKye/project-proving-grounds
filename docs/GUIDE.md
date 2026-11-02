# Player's guide

Everything beyond the [README](../README.md): the team directors, the Data collector and the Observer, sharing games,
LiDAR mapping, map features and reporting problems. Command lines below run from the install folder (the launcher's
**Open the install folder**) with the bundled Python: `python\python.exe -I tools\<tool>.py ...`.

## Team directors

Every team of bots has its own director: code that knows only what its own team knows (where teammates are, what they
saw and heard, the score and the clock). It speaks map callouts to the team, hands out roles every 2 seconds (CTF:
runner, escort, defender, hunter; Slayer: map control and hunters; each mode its own), pulls bots back to defend after
a death near the flag, and sets the team's play by the score and the clock: careful when the enemy is about to win, all
in when behind late. Nothing shows over the game: every decision is in `logs\brain.txt` and in the Observer's event
feed.

## Data collector and the Observer

Turn on **Data collector** in the BOTS panel and play. It records your movement and aim, your shots, guns and equipment, all read
from the game itself (your keyboard, mouse and controller are never recorded), on this PC only
(`logs\collect_<map>_<date>-<time>.jsonl`).

Open the **Observer** from the launcher and pick a game: a live one shows LIVE. Scrub the timeline and click a bot to
see what it saw, thought, was told and did. The **You** section shows your numbers beside the bots' (by difficulty,
measured the same way):

- **Aim**: seconds from an enemy coming into view to your aim on them (and to your first shot); how often you were
  already aimed where they came from. **Hit**: from being shot to your aim on someone.
- **Fights** a minute alive, how long they last, the time between them and from a spawn to the first.
- **Speed**, time standing still, sideways speed in fights, jumps.
- **Positioning**: the zones you spend time in, fight distance and height, who aims first when you and an enemy see
  each other, how much of the time an enemy has you in view. **Show where you were on the map** draws it.
- **Accuracy**: firing time on a body, damage dealt, kills; your guns, shots, switches, pickups and equipment uses.

Games recorded without the Data collector still get positions, aim, pace and positioning from the bots' recording
(4 times a second, without your shots). The **Crosshairs** layer draws your line of sight to what your crosshair is on: red on a
player, gold on a vehicle, white on the ground or a wall. Click yourself on the map to see what your crosshair is on,
what you ride and which gun. Text versions: `tools\observer.py you <trace file>` and
`tools\observer.py at <trace file> <seconds>`.

The Observer keeps the last 10 matches.

## Share a game

In the Observer, pick a game and press **Export game**. It saves one zip (a copy also goes to `logs\exports`) with
everything recorded in that game:

- `manifest.json`: the game, map, modes, score and length; every player marked **human** or **bot** (bots with their
  difficulty and play style); every file inside and the format of each row.
- `trace.jsonl`: everyone 4 times a second, every bot every tick (position, aim, goal, buttons), every bot decision
  with its scores and callouts.
- `collect.jsonl`: the Data collector's recording when it was on.
- `carnage_report.xml`: MCC's own post-game numbers when they belong to this game; the Observer's objective and player
  analyses.

Gamertags, clan tags and service tags become Player 1, Player 2 ..., Xbox ids are always removed and your Windows
user folder in any path becomes `<home>`; tick **Keep names** to keep the names. **Import** opens a zip someone shared.
Command line: `tools\match_export.py <trace file>`.

## LiDAR mapping

Bots play better on a map they have mapped. No scans ship with the mod: each PC maps its own.

### LiDAR mode (in a match)

Tick **LiDAR mode** in the BOTS panel and start any match: up to 16 players, all bots on your team, nobody fights.
The bots walk every floor, measure heights and jumps, and record where they fall. Open the **LiDAR Viewer** to watch
in 3D: bots are white dots, you are gold, every step colours the floor by height, a jump or fall is a white trail that
turns magenta only if the bot lands and is still alive 5 seconds later, and a red cross marks each deadly edge.

**Maps list** (L, or the button): one button per game, then a picture button per map with its real name and scan
status (runs, floor cells, when it was last updated; LIVE on the one being scanned now). Click any map to see its
stored scan. **Remove** on a scanned map deletes that map's scan to start it over (it asks first); the files move to
`backups\lidar`, and copying one back into `maps\<map>` restores it.

Every jump you land that beats walking (and survive for 5 seconds after landing) is saved for the map; LiDAR bots go
and try it, and from the next match every bot uses it (Easy bots too: to get around, never as a fighting trick). A
notice shows in the game when a jump of yours is learned, and again when bots have done it twice. Crouch spots work
the same way (Halo 2 Anniversary and Halo 4): floor you walk crouched is marked and every bot crouches there.

**Called jumps.** A LiDAR bot only learns a jump it called: before jumping it says where it will land, worked out from
the game's run speed, jump and gravity over the map's level data, and it only calls jumps whose small misses it would
survive. If it lands on the call and lives 5 seconds, the jump is open to every bot; a miss does not count, and a jump
missed twice is not called again. Your own jumps always count. Every jump is judged two-way (a gap bots use both ways)
or one-way (a drop with no way back up); a recorded jump is a way in, not a detour: a bot only takes it when it is the
best way to where it is going.

The paint spreads a little around every player over connected floor, and where it meets a wall the wall is painted
solid: bots backing off from a losing fight head for a wall that shields them. Glass and other see-through surfaces
are never counted as walls (Halo 2 Anniversary, Halo 4, ODST; the other games' level files carry no material names).

### LiDAR Simulator (no game needed)

The **LiDAR Simulator** in the launcher runs the same bots on a map's level data and shows them in the 3D view: 16 bots
map the floor and call jumps, 8 aircraft fly the air over the walked floor up to the map's ceiling. Its **Simulator**
panel (bottom right):

- **Pick a map**: the Maps list opens; click a map's picture (or its **Simulate** button). Forge layouts the bots have
  played on are listed under their map. Picking another map while one runs stops it (what it mapped is saved).
- **Every map**: all of them in turn, each saved when it finishes.
- **Speed**: 1x (real time) to 16x, or **Max** (as fast as this PC runs it). The panel shows the speed actually
  reached: big maps with 16 bots and 8 aircraft run slower than asked on most PCs.
- **Pause** / **Resume** and **Stop** (it saves what was mapped).
- **Click spots to cover** (or C): click the map where the bots should go first; the 3 nearest bots go to each spot
  (pink ring), green once a bot got there, a red cross when no bot found a way within 2 minutes. **Clear spots**
  removes them.

A map runs until nothing new turns up for 45 seconds (6 simulated minutes at most); run it again to add to its scan.
Jumps the bots land go into the map's LiDAR data, where bots in real matches try them and stop using ones that fail
in the game. Command line: `tools\lidar_sim.py --open [maps...] [--all] [--speed 4]`. The simulator only
knows the level data, so it cannot find floor the data lacks or steps the game lets you walk up; LiDAR mode in a match
fills those in. Its jump physics is each game's own (gravity and jump speed measured from recorded matches, run speeds
and fall damage from the official editing kits).

## Map features

Every map's weapons, powerups, vehicles, objective points (flags and their returns, hills, balls, territories, bombs
and goals) and usable things (teleporters, man cannons, gravity lifts, switches, doors, shields) are on its LiDAR map
with names (M in the 3D view). In Halo 3, Reach, Halo 4 and Halo 2 Anniversary the brain also reads every gameplay
object as it plays: armor abilities and equipment, teleporters (and which sender leads to which receiver, once someone
goes through), man cannons, lifts, power-ups, weapon and vehicle spawns, spawn points and kill / safe zones. LiDAR bots
in a real match ride each man cannon and lift nobody has ridden yet: where it throws them becomes a path every bot can
use.

## Report a problem

Press **F9** in a match with bots on to save a bug report: the moment is kept with the recording around it in
`logs\bug_reports\<date-time>`, and a note you type goes with it. Attach that folder (or the Observer's export of the
game) to an issue on the project's GitHub page and say what you expected to happen.

## Where things are

| Folder in the install | What |
|---|---|
| `maps\<map>` | each map's knowledge (callouts, positions, objects), its LiDAR scan and what the bots learned there |
| `logs` | the brain's log, recordings, bug reports, exports |
| `native\bin` | the mod (botcore.dll, inject.exe), the BOTS panel's settings and pictures, the 3D bots |
| `python` | the bundled Python |
| `tools` | the launcher, the tools and the map tools |
