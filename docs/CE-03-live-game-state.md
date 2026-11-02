# CE-03 - Live game state and player creation (MCC 1.3528, halo1.dll)

Date: 2026-10-22, about 01:15. MCC running Halo CE Blood Gulch Team Slayer, anti-cheat off.
Read-only memory reads (tools/memread.py, tools/memdump.py) plus Ghidra decompilation
(ghidra/decompile.bat + scripts/DecompileAt.java).

## Data arrays (Blam "d@t@" tables) found live
`python -I tools\memread.py arrays` lists 59. Key ones (max, element size):
players 16 x 0xC20, object 2048 x 0xC (headers), flag 2 x 0x16BC (CTF), actor 256 x 0x66C,
encounter 128, update client queues 16 x 0x38, update server queues 16 x 0x90 (per-machine
player action queues, as in the decomp's player_queues_new.c), hs globals, hs thread.

Header layout (MCC halo1): name[32] | +0x20 max (s16) | +0x22 element size (s16) | +0x24 valid |
+0x28 '@t@d' | +0x2C next/last index | +0x30 live count (s16), next salt (s16) |
+0x34 data offset **relative to the header** (s32; 0x38 for players). Element 0 starts with its salt.

## players entry (0xC20 bytes), fields seen
| Offset | Field |
|---|---|
| +0x00 | salt (s16) |
| +0x1B | local player index (byte; -1 remote) |
| +0x20 | name, UTF-16, 15 chars |
| +0x40 | service tag (8 bytes, e.g. "K21") |
| +0x4C | 1 after creation |
| +0x64 | unit object handle (index low 16, salt high 16); NONE = -1 |
| +0x68, +0x6C, +0x7C | other handles (dead unit, ...), NONE on creation |
| +0x84 | copy of the network player record (0x4C bytes: name, tag, appearance) |
| +0xD4 | speed multiplier, 1.0 |

## Objects
Object header array (12-byte entries): +0 salt, +3 type, +6 size, +8 offset (s32).
Object address = [halo1.dll+0x2D9CDF8] + 0x34 + offset (from the game's own lookup at
halo1+0xB389A4). Biped: +0x18 position (3 floats), +0x24 velocity, +0x30 forward, +0x3C up,
+0x5C bounding sphere centre, radius after it, +0x7E the player player salt.
Live check: the player's biped at (37.43, -68.11, 0.26), Blue back, facing (0.24, -0.97, 0).

## player_new found
`halo1.dll+0xACF984` (FUN_180acf984) = `player_new(machine_index, player_index, short local_index,
network_player *np)`: player_index -1 takes a free slot; copies the name (+0x20), service tag
(+0x40), np (+0x84, 0x4C bytes); sets the NONE handles and speed 1.0; ends with
`FUN_180acf3e4(machine_index, player)` (machine_add_player). A sibling variant without the
network-simulation join loop is at +0xACFCA0. Players table pointer global: halo1+0x1C40480.

## Native stage 0 in MCC
`native\bin\inject.exe` loaded botcore.dll into the running game; the shared-memory heartbeat ran
at about 30 Hz and the DLL found halo1.dll. (botcore.log is held open by the DLL; read status
from shared memory, or switch the log to a shared-read open.)

## Stage 1: game-thread tick hook + a real bot player
MinHook on halo1+0xB6667C (game tick). The ADD_BOT command calls player_new (+0xACFCA0) as
(machine 1, -1, -1, record copied from player 0 +0x84 with a new name). The bot spawns, gets a biped
and shows on the scoreboard (docs/evidence/2026-10-22_first_bot_player_scoreboard.jpg).

## Stage 2: bot input (verified)
Per-tick update: FUN_180aaf7d0 calls players_update_before_game by mode global halo1+0x2B236E0
(word): 1 = client (FUN_180ad102c), 0/2/3 = host (FUN_180ad0720). A local custom game is mode 2.
Host path: FUN_180b66af8(actions[16] x 0x30, acks[16] x 0x10) fills one action per live player,
in players-array order, from the "update client queues" data array (16 x 56, only local players
live). So a bot's slot is left empty. botcore hooks it and writes each bot's action after it.
Action (0x30): +0 unit control flags (units.h bits: crouch 0, jump 1, action 6, melee 7,
reload 10, fire 11, grenade 13; 0x4D0 are press-only), +4 yaw, +8 pitch (absolute radians),
+0xC throttle forward, +0x10 throttle left, +0x14 primary trigger, +0x19 weapon (byte),
+0x1A grenade, +0x1C zoom, +0x20.. MCC extras (left as the game set them).
Client path (not used here): a player with no local controller (bitmask at [halo1+0x2EA2D90]+0xD8+index)
reads its network queue at player +0x8F0, else the last action at +0x914 when +0x910 = 1.
Verified live: forward 2 s moved the bot 4.3 units (CE run speed), strafe +1 at yaw 0 moved -y,
jump lifted z 0.08 -> 0.55, the game rate-limits turning. tools/live_walk.py walked the bot from
Red base to Blue base on brain/terrain.py paths and stopped in sight 12.5 units from the player.
Biped: +0x9C health, +0xA0 shield (fractions of 75), +0x2D8 held weapon handle.
Teams: Bot 1 (machine 1) joined Blue against the player's Red.

## Stage 3: full bots (verified live)
- Player: +0x20 name (16 wchar), +0x48 (np[0x14], 0 for all), +0x4C team (0 red, 1 blue; player_new
  writes 1, we write the wanted team right after), +0x50 action object, +0x54 action result
  (6 = swap for weapon), +0x64 unit. +0x1B local player index (-1 for bots).
- Biped: +0x234 aiming vector (snaps to the action's facing at once), +0x240 looking vector (head,
  ~320 deg/s), +0x30 body forward; +0x9C health, +0xA0 shield (fractions of 75); +0x2D3 current
  weapon slot (int8; +0x2D5 the slot asked, from the action's +0x19;: an int16 at +0x2D2 read 256 on slot 1);
  +0x2D8 weapon inventory (4 handles); unit control flags at +0x1D8.
- Positions are at the feet; shots come from the eye (0.62 standing): the brain aims from eye().
- Tags: [halo1+0x2D9CE10] = tag header mapped at virtual 0x50000000; +0 tag array (0x20 each:
  class, +0xC id, +0x10 path ptr). Object +0 = tag id. Weapon names from the path.
- Object types: 0 biped, 1 vehicle, 2 weapon, 3 equipment, 6 scenery. Weapon +0x74 owner team
  (flags). Object +0x54 location (leaf, cluster): -1 when held in an inventory.
- Game mode global halo1+0x2B236E0 (2 = host). Game engine (variant) struct [halo1+0x2E9F820];
  +0xC0 allow_pick_up (CTF: halo1+0xBA7088, refuses your own team's flag unless moved).
- Pickups: players_update_after_game (+0xAD1530) calls examine_nearby_objects (+0xAD474C) for every
  player each tick: objects_in_sphere then examine_nearby_item (+0xAD4E28): ammo, powerups, then
  can_use_weapon (+0xB09624), should_autopick (+0xAD4D84), add_weapon_to_inventory (+0xB08F3C).
  Swapping a weapon needs action held = unit control bit 14 (swap) besides bit 6 (action, press-only).
  The CTF flag autopicks (it does not count toward the weapon limit) into a free slot.
- Action +0x19 desired weapon slot (char): our hook must write -1, else the slot default kept
  forcing slot 0 (a bot with the flag kept switching back to the rifle).
- MCC unloads and reloads halo1.dll at every match (same base address, fresh code): hooks vanish;
  botcore re-hooks when its own jump bytes are gone.

## Next
1. Team and name per bot at creation (record +0x84 holds team; find it), many bots.
2. Live brain loop: brain/live.py snapshot -> Bot.think -> botctl.act at 30 Hz.
3. Weapon/ammo fields; damage events for the director (deaths, kills).
