# H3-01 - Halo 3 (halo3.dll, MCC 1.3528): real player bots

Status CDT: Halo 3 bots play Team Slayer hands-free (botcore s35): the BOTS tile shows
in the H3 lobby, botcore starts the brain when the H3 players update ticks, play.py adds 7 bots
(4v4 on Construct), they spawn, respawn, move on the H3 nav, fire and score
(docs/evidence/2026-10-22_h3_team_slayer.jpg). Not yet: the variant (FFA vs teams; play.py
--ffa), CTF flags, crates in the nav, weapon names from tag names (placements instead).

## Engine globals: thread-local storage
Halo 3 keeps engine globals in TLS: the game thread's block for halo3.dll
(TEB +0x58 ThreadLocalStoragePointer [halo3 _tls_index = 60]; tools/tls.py lists every thread's).
A new match runs on a new game thread. Block +0x10 players header, +0x38 object header array,
+0x48 game globals (+0x200: 16 player configurations of 0xB8 bytes, the players a match is made
of), +0x40 machines/players globals, +0x110 local player mapping. (tls+0x008 actor,
+0x050 squad, +0x060 effect ... named arrays: see the dump in the log.)
Array header (name[32]): +0x20 max, +0x24 element size, +0x28 flags, +0x2C '@t@d', +0x40 count,
+0x48 data pointer (absolute), +0x50 in-use bitmask pointer. The arrays live in a 2 GB region
(three game-state copies 5 MB apart).

## Players (16 x 0x2F8)
+0x00 salt, +0x04 flags (bit 0: present / may spawn, bit 1: no machine, bit 3: just joined),
+0x08 player identifier, +0x14 machine identifier (6 bytes), +0x1A machine index, +0x1C
controller, +0x20 user, +0x28 unit, +0x4C position, +0x58 configuration (0xA0, copied from the
creation config +0x18; name first), +0xF0 team (int), +0xF8 desired configuration, +0x1A0
respawn delay, +0x1B0 ticks dead.

## Objects
Header entries 0x18: +0 salt, +2 flags, +3 type (0 biped, 2 weapon ...), +0x10 object address.
Object +0 tag, +0x08 next sibling, +0x0C first child, +0x10 parent, +0x50 position, +0x5C
forward. Unit +0xEC/+0xF0 max health 45 / shield 70, +0xF4 health, +0xF8 shield (fractions),
+0x1A0.. aiming vectors (+0x1AC used), +0x1F4 throttle forward, +0x260 weapon set / +0x262
primary / +0x263 secondary index, +0x268 4 weapon handles. Weapon +0x23A magazine.

## Input
players update FUN_1800e444c(actions) (halo3+0xE444C, game thread, every tick): actions +8 =
bitmask, +0x10 + index * 0x88 = each player's action; FUN_1800e8dd8 builds unit control from it,
unit_control FUN_180350ed4. Found with native/watch.cpp (hardware write breakpoint on the
biped's throttle while holding W). Action (decoded live, tools/h2_action_record.py):
+0x08 control flags (jump 0x2, fire 0x00080040), +0x10 yaw, +0x14 pitch, +0x18 throttle
forward, +0x1C throttle left, +0x30 trigger, +0x38 1.0 on jump, +0x40 action flags (E: 1 held,
3 held long), +0x44 weapon set / +0x46 primary / +0x47 secondary index (unit +0x260), +0x4A zoom,
+0x4C interaction type, +0x50 interaction object, +0x54.. targets, +0x80 input history.
The H2 action behind an 8-byte prefix.

## Player creation
player_new_at_index FUN_1800e20dc(index, config, 0) (halo3+0xE20DC; found by a write breakpoint
on the players count across a match start, native/watch.cpp now arms new threads). Init
FUN_1800e2928, configuration copy FUN_1800e2370. Config (0xB8): +0 valid, +1 no machine, +2
controller (s16), +4 user, +8 machine identifier (int + short), +0x10 player identifier, +0x18
configuration (name +0x18 and +0x90, team int +0xB0). What each choice did (all verified):
- player 0's team: free for all has one team left, the match ends at once (as in H2).
- host machine: the bot becomes a local user, Halo 3 splits the screen for it.
- no machine (+1 = 1): shown greyed, counted as gone, its team loses.
- unknown machine identifier (botcore default): machine index -1, no local user, not flagged;
  it joins ("SpartanBot joined the game") but never spawns until flags bit 0 is set. The spawn
  loop in FUN_1800e444c spawns players with bit 0 set, bit 1 clear and no unit; the session
  clears bit 0 for unknown machines between ticks, so botcore sets it every tick (s35): bots
  spawn and respawn.

## Live reader, map data
brain/live.py LiveH3 (TLS via tools/tls.py). Halo 3 keeps no tag names in memory: weapons are
named by matching loose weapon objects to the map's placements (objects.json), which also names
the starting weapons (same tag). Map name: cache header at halo3+0x20A9058 ('daeh') +0xE0
scenario path. tools/h3_export.py: H3EK (tags extracted with bin\x64\7zr): tool.exe
export-structure-mesh-obj levels\multi\<m>\<m> (stdout, CE kit OBJ axes; 120 of 137 Construct
spawns on a floor), export-tag-to-xml of the scenario (multiplayer content as objects with
multiplayer data: owner team defender 0 / attacker 1, spawn time; crates ctf_flag_spawn_point,
teleporters; scenery respawn_point).
