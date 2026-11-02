# Navigation and sight model (brain/terrain.py, tools/heightmap.py)

Built per map from the CE kit's level mesh (`tool.exe export-structure-mesh-obj`), so it matches
the real level. Rebuild a map: `python -I tools\heightmap.py maps\<map>\source\<map>_bsp.obj
maps\<map>\objects.json maps\<map> 0.25 maps\<map>\callouts.json` (all maps: tools\export_maps.py).

## heightmap.npz (0.25 unit cells)
- Grid bounds: the play area (spawns, flags, items, vehicles) plus 40 units (Death Island's ocean
  plane is 2700 units across).
- `top`, `low`: highest and lowest surface per cell.
- `floors` (4, h, w): walkable surfaces (normal z >= 0.7, 45 degrees, CE's biped maximum slope),
  stacked into levels at least 1 unit apart, lowest first (doorway, roof over it, catwalk above).
- `walls` (h, w, 4 x uint64): a 256-bin height bitmask (0.25 high, from `wall_z0` = lowest play
  object - 16) of where steep faces pass through the cell. Out-of-range heights are ignored
  (Boarding Action's mesh goes 70 units under the ships; clipping them into the top bin had
  walled every floor).

## Walk graph
- Nodes: (layer, cell) for each floor level. A node is walled off if steep faces cover both
  chest (+0.55) and head (+0.85) height above its floor (stair risers and curbs do not).
- Edges (8 neighbours, directed): climb up to 0.18 per cell (Blood Gulch's ramps climb 0.15),
  drop up to 3. Cost: length + 2 x height change + 1.5 near a wall (keeps paths centred).
- Teleporters: one-way links from every floor node within 0.75 of the pad (and up to 1.5 under
  its top: pads are raised discs) to the exit. Nav returns the pad centre when the link is the way.
- Reachability: breadth-first from every spawn. Goals elsewhere snap to the nearest reachable node;
  items on unreachable spots are skipped (maps.py sets item["reachable"]).
- Zone centres (callout spots, hunt targets) sit at real floor heights (band-aware).

## Jump graph (skilled bots: profile jump >= 0.5)
CE: jump velocity 0.07 per tick, gravity 0.003565 per tick^2 (physics.c) -> 0.69 units up, about
2.9 units of travel at run speed. Links from edge nodes (fewer than 8 walk neighbours): up to 0.6
higher within 1.25 (ledges, crates), or level/down across a real gap up to 2 units, with no wall
at chest and head height and nothing solid inside the arc. Bots run to the take-off cell and
press jump; the sim hops them.

## nav(a, b, jump=False)
Flow field (Dijkstra from the goal over the reversed graph, cached), lookahead along straight
walkable lines. From a pocket with no path (the game is more forgiving than the grid) it walks to
the nearest spot on its own level that has one. At the goal's node it stays.

## Line of sight
Eye (feet + 0.62) to chest (+0.40): blocked by a steep face at the ray's height (wall bitmask),
by the ray crossing a floor level (a slab between storeys) or going under the lowest surface.
Overhangs stay open. (The old top-surface test saw through floors on multi-storey maps.)

## Known issues
- Boarding Action: each ship's floors (2.5 apart) are not connected upward in the graph even with
  large step heights (likely the slab edges around stairwells count as walls). Bots fight on their
  floor, drop down, and cross between ships by the teleporters on floors 1 and 5.
- Hang 'Em High: the middle sniper perch is an island 3.5 above everything around it (bots skip it).
- MAX_RISE stays 0.18 per cell (a 0.43 lip stopped a live bot) although the biped tag allows 45
  degree slopes; separating slopes from lips would allow steeper ramps.
