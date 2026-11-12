# LiDAR maps: share your scans

Every match you play teaches the bots a map (Passive LiDAR), and the LiDAR Simulator maps one on purpose. The floor you
walk, the jumps you land, the lifts and man cannons you ride, the teleporters you take: each PC keeps its own scan.
Here players share theirs, so a map you have never played can start with what other people found on it: the jump
nobody's bot would try, the drop that is safe, the ledge you can crouch-jump onto.

| Game | Author Provided Scans | Shared scans |
|---|---|---|
| Halo: Combat Evolved | [18 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-ce.zip) | [halo-ce](halo-ce/) |
| Halo 2 | [25 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-2.zip) | [halo-2](halo-2/) |
| Halo 2 Anniversary | [7 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-2-anniversary.zip) | [halo-2-anniversary](halo-2-anniversary/) |
| Halo 3 | [22 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-3.zip) | [halo-3](halo-3/) |
| Halo 3: ODST | [8 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-3-odst.zip) | [halo-3-odst](halo-3-odst/) |
| Halo: Reach | [28 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-reach.zip) | [halo-reach](halo-reach/) |
| Halo 4 | [21 maps (zip)](https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-halo-4.zip) | [halo-4](halo-4/) |

**Author Provided Scans** are the mod author's own scans of every map they have mapped, one zip per game (all of them
on [the LiDAR maps release](https://github.com/AyoItzKye/project-proving-grounds/releases/tag/lidar-maps)).

## Use a scan

In the launcher, open **LiDAR scans**:

- **Author Provided Scans**: choose the game and press **Import**. The launcher downloads that game's zip and adds it.
- **Import a shared zip ...**: choose a zip you downloaded (an author zip from the table above, or a player's scan
  from a game's folder).

Or from a command prompt in the mod's folder:

```
python\python.exe tools\lidar_share.py fetch halo-3
python\python.exe tools\lidar_share.py import "<the downloaded zip>"
```

A scan is added to your own scan of that map, never in place of it: floors add up, and every jump, ride and teleporter
that differs from yours is kept, even two jumps from nearly the same spot (people take them at different angles).
Your scan before the import is kept beside it (`maps\<map>\lidar.json.before-import-<date>`), so you can go back.
Importing the same zip twice adds nothing the second time.

## Share your scan

1. See which maps you have scanned:

   ```
   python\python.exe tools\lidar_share.py list
   ```

2. Export one (the map's folder name from the list):

   ```
   python\python.exe tools\lidar_share.py export h3_construct
   ```

   The zip is written to the `lidar-share` folder in the mod's folder.
3. [Share a LiDAR map](https://github.com/AyoItzKye/project-proving-grounds/issues/new?template=lidar_map.yml): pick
   the game, name the map, and attach the zip. Shared scans are checked and added to the game's folder here.

What is in a zip: the map's scan (`lidar.json`: floors, jumps, rides, teleporters, cover, where guns lie) and a
`manifest.json` (the map, the game, the version that made it, how many minutes of play it holds). Nothing about you:
people in it are "human", bots are "bot", no names, no folders, and the export checks for anything private before it
writes the zip.

A scan only fits the map it was made on, in this mod's versions from 0.2.2 on. Forge layouts are not shared yet.
