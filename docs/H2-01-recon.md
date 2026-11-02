# H2-01 - Halo 2 Classic (halo2.dll, MCC 1.3528) recon for player bots

Status CDT: Halo 2 bots play hands-free (botcore s27): the BOTS tile shows in the
H2 lobby, botcore starts the brain when an H2 match ticks, play.py reads the map and variant and
adds bots. Verified: FFA (8 players), Team Slayer 4v4, CTF Classic with captures (Blue 2 Red 1,
docs/evidence/2026-10-22_h2_ctf_captures.jpg), carnage report kills.
Ghidra project ghidra\mcc_1_3528 has halo2.dll analysed (ghidra\decompile_dll.bat
halo2.dll <out.c> <addr>...). Live reads: `HB_GAME_DLL=halo2.dll python -I tools\memread.py arrays`.

## Data arrays (Blam, like CE but a different header)
Header: name[32], +0x20 max (s32), +0x24 element size (s32), +0x28 flags, +0x2C signature
'@t@d', +0x3C first unused index / count, +0x40 live count, +0x48 data offset from the header
(s64), +0x50 in-use bitmask offset (s64). Element starts with its salt (s16); handle =
salt << 16 | index.
- players: global pointer halo2+0xE80A28, 16 x 0x224.
- object (headers): global halo2+0x18B7398, 2048 x 0xC; entry +8 = offset into the object pool.
  Object address = ((pool + 0x57) & ~0xF) + offset, pool = [halo2+0x18B7360]
  (FUN_18076b320). Biped: +0x64 position, +0x70 forward, +0x7C up.
- No "update client queues" array (CE's local input queue); H2 has "simulation view" and
  "simulation distributed view" arrays (the H2 network simulation).

## Player datum (0x224)
+0x00 salt, +0x06 flags (bit 1 = created without a machine, see below), +0x08 player
identifier (u64), +0x10 (for machine-less players: [[halo2+0x15FE008]+8]), +0x14 machine
identifier (u64), +0x1C machine index (s16), +0x1E controller index, +0x20 (int), +0x2C unit
handle, +0x3C current configuration (name first, 16 wchar), +0xC0 desired configuration
(0x84 bytes, copied from the creation config +0x18).

## Player creation
- datum helpers: FUN_18067b6d0(array, index) = datum_new_at_index; FUN_18067b9f0(array, index)
  = get by absolute index; FUN_18067b9a0(array, handle) = get by handle; FUN_18067b040/
  FUN_18067b050 = iterator new / next.
- FUN_18069d2c0(index, config*) = player_new_at_index: datum_new_at_index, FUN_18069dce0
  (initialise from config), counters, FUN_1808668e0 / FUN_1806109f0 / FUN_180690e40 (engine
  notifications) unless config[1] is set.
- config struct (stride 0xD4 in the session's player table at [halo2+0xE80A78]+0xAC4, which
  FUN_1806a5de0 walks at game start): +0 valid (1), +1 "no machine" flag, +2 controller (u16,
  0xFFFF none), +4 int (-1 none), +8 machine identifier (u64), +0x10 player identifier (u64),
  +0x18 configuration (0x84 bytes; name first).
- FUN_1808b10e0 is the network "player add/update" message handler: it builds that config from
  the message and calls player_new_at_index; with the no-machine flag it uses machine 0xFFFF
  and controller -1. Plan: call FUN_18069d2c0 from the game thread with the flag set and a copy
  of player 0's configuration (+0xC0) with a new name and identifier, then check the scoreboard
  and whether the engine spawns a biped (as CE did).

## Input (found, live)
- Game tick FUN_1806a72a0: FUN_180865b20(1, &actions) fills a local action set (the simulation's
  update), then players update FUN_1806a3910(&actions). actions +4 bit 0 = valid, +8 = bitmask of
  players with an action, +0x100 + absolute player index * 0x60 = that player's action.
- unit_control = FUN_1808f5800(unit, control*): copies control into the unit (+0x150 flags 8 bytes,
  +0x158, +0x15C desired facing, +0x168 aiming, +0x18C looking, +0x1B0, +0x1BC throttle forward,
  +0x1C0 throttle left, +0x1C4 trigger, +0x1C8, +0x1CC/+0x1D0, +0x228 weapon, +0x251 grenade...).
  Found with native/watch.cpp (hardware write breakpoint on the biped's +0x1BC while holding W).
- Action (0x60), decoded live with tools/h2_action_probe.py (botcore copies player 0's action):
  +0x00 button flags (jump 0x6, fire 0x008C0100), +0x08 yaw, +0x0C pitch (radians), +0x10 throttle
  forward, +0x14 throttle left, +0x18 / +0x1C triggers (1.0 when firing), +0x20 low byte action
  (0x3 while E held, rest 0x0041FE00), +0x24.. weapon/grenade slots (0xFF = none), +0x30.. -1s.
- botcore (native/h2.cpp) hooks FUN_1806a3910 (60 calls a second) and can write bot actions there.

## H2 player bots work (verified live on Lockout)
The matches ended because the cloned configuration put the bot on player 0's team: in free for
all that leaves one team, and the game ends. Configuration +0x7C = team (byte). With a different
team the bot joins, appears on the scoreboard (docs/evidence/2026-10-22_first_h2_bot.jpg), spawns
a biped and is driven by the action hook: strafing 2.9 units in 1.5 s, turning to the asked yaw,
jumping. Config used: valid 1, no-machine 0, host machine identifier (player 0 +0x14),
controller and user index 1..3, a made-up player identifier, player 0's configuration with a new
name and team. (The three earlier tries, no-machine, unknown machine and host machine, all had
the same team; only the team mattered.)
Test command: botctl ADD_BOT with cmd_arg = machine | team << 8 | 1 << 24 (bit 24 = for H2).
## Action layout (all fields; network decoder FUN_1808abf70 names them, ghidra/h2_actdec.c)
+0x00 control-flags (u64; jump 0x6, fire 0x008C0000 held + 0x100 on the press tick), +0x08 yaw,
+0x0C pitch, +0x10 throttle-x (forward), +0x14 throttle-y (left), +0x18 trigger, +0x1C
secondary-trigger, +0x20 action-flags (E: 0x301 on the press tick, 0x201 held, 0x41FE03 once held
long; "hold E to pick up"), +0x24 weapon-set-identifier (s16), +0x26 primary-weapon-index,
+0x27 secondary-weapon-index, +0x28 grenade-index, +0x2A zoom-level (-1 none), +0x2C
interaction-type (s16: 0 none, 1 weapon pickup, 4..6 seats with +0x2E seat index, 7 = pickup
too), +0x2E pickup flags / seat index, +0x30 interaction-object, +0x34 melee-target-unit,
+0x38.. aim assist (FUN_1807583d0).
- The client computes the interaction (which weapon / seat) and sends it in the action; the host
  only applies it. botcore s26 does that for bots: with E held it finds the loose weapon (object
  type 2, no parent) within 1.5 units and sends type 1 + its handle (verified: bot took the sniper
  on Lockout). Weapon switch: +0x26 = slot. +0x24..+0x27 come from the bot's own unit (+0x224).
- Player 0's action is the template for the rest; its melee target (often the bot itself) and
  interaction are cleared, zoom set to -1.

## Live reader (brain/live.py LiveH2)
Player +0x2C unit, +0x3C name, +0xB8 team (current configuration +0x7C). Object +0 tag, +0x14
parent, +0x64 position, +0x70 body forward. Unit +0x168 aiming vector, +0xEC health (fraction
of 45), +0xF0 shield (fraction of 70), +0x224 weapon set / +0x226 primary weapon index, +0x22C
4 weapon handles. Weapon +0x22E reserve ammo, +0x230 magazine (s16). Tag names: [halo2+0x15E4B68]
= int32 offsets by tag index into the names buffer at [halo2+0x15E4B78]; tag 0 is the scenario
(scenarios\multi\lockout\lockout).

## Map data (tools/h2_export.py, all 25 MP maps in maps/h2_<map>)
From the H2EK kit (Steam, tags extracted from H2EK.7z with its 7zr; tool.exe needs an empty
data\ folder): scenario + structure BSP to XML, collision BSP (surfaces walk their edge rings)
plus every instanced geometry placement (scale, forward/left/up, position) to OBJ, then the CE
pipeline (heightmap.py, gen_zones.py). Floors more than 16 below the lowest player object are
ignored (Lockout's pit). Not yet in the nav: crates and scenery (Lockout's power modules), H2
location_names callouts, the CTF flag owner team, the game variant (teams vs FFA: play.py
--teams), H2 jump physics (gap jumps off for H2 maps).

## Variant, map name, CTF
- Variant: halo2+0xE71CD0, same layout as halo2\game_variants\*.bin: +0x04 name (wchar, e.g.
  $ctf_classic), +0x44 engine (1 CTF, 2 Slayer, 3 Oddball, 4 King), +0x48 flags (bit 0 teams),
  +0x50 score to win. Verified with FFA, Team Play on, CTF. (Seven copies exist; this one is read
  by engine code.)
- Map name: the tag scenarios\multi\..\<n>\<n> in the tag names buffer (tag 0 is the scenario
  on some loads and globals\globals on others); the table fills a moment after spawn (play.py
  retries).
- CTF flag: weapon objects\weapons\multiplayerlaglag, owner team s16 at object +0xDC (-1 on
  other weapons; +0x182 too). Carried = in a unit's 4 weapon slots. Halo 2 does not switch to a
  picked-up weapon by itself: the client asks for the slot (action +0x26), so a carrier's brain
  selects the flag slot (bot.choose_weapon); without that the carrier stood on the capture spot
  holding the SMG and never scored. Capture point = the team's flag spawn ("CTF flag return").

## Brain changes for H2 (all games)
Edge guard (bot.edge_guard): never step, strafe, juke or jump toward ground that is a fall to
death (no floor within 4 below and the column's lowest surface far below), and in the air steer
back over solid ground or to a planned jump's landing. Goal commitment (+0.2 to the current
goal, not for camping) stops item/objective flip-flopping. Map points snap to reachable floors.
Result on Lockout: 0 falls in 3 minutes (was 8), all deaths from combat.

Safety: botcore's H2 hook only runs commands marked for H2 (cmd_arg bit 24), and the brain starts
only when the CE tick runs, so an H2 match is never touched.
