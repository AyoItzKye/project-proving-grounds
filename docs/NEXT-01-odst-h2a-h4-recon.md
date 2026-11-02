# NEXT-01: ODST Firefight, Halo 2 Anniversary, Halo 4 recon (-14:35 CDT)

Static + live recon only; no hooks written yet. MCC 1.3528. All three games keep their engine
globals in the game thread's TLS block, like Halo 3 and Reach (find the block whose pointer at the
offset below heads an array with "@t@d").

| | ODST (halo3odst.dll) | H2A (groundhog.dll) | H4 (halo4.dll) |
|---|---|---|---|
| TLS players array | +0x10 (sig at +0x2C, data +0x48, as H3) | +0x8 (sig +0x28, data +0x50, as Reach) | +0x8 (same) |
| TLS object array | +0x20 | +0x18 | +0x18 |
| player size | 0x418 | 0xF20 | 0xF18 |
| player unit handle | +0x28 | +0x2C | +0x2C |
| unit aim vector | +0x188 | +0x4BC (copies follow) | +0x4BC (copies follow) |
| players update | FUN_1800fea10 | FUN_180080330 | FUN_1800816d8 |
| per-player action | +0x10 + i*0x240, bitmask +8 | stride 0x108 (seen) | stride 0x108 (seen) |
| player_new_at_index | +0xFBFE4 (byte match from H3/Reach) | not found by pattern | not found by pattern |

How found: watch.dll (tools/watch_write.py) on the player's aim vector while turning the mouse;
the call stack passes through the players update (it multiplies by the player size and draws the
spawn RNG 0x19660d). ODST was also Ghidra-analysed (ghidra/halo3odst.dll_analyze.log; decompiled
ghidra/odst_pu.c). tools/find_like.py finds a known function in a sibling build by masked bytes.

ODST Firefight menu route: main menu FIREFIGHT (4th row) > HALO 3: ODST CUSTOM FIREFIGHT (4th row;
the 2nd row is MATCHMAKING, never click it) > BUILT IN MISSIONS > the START tile is the 5th tile
(an extra difficulty tile) > START. Crater (Night) loads in about 40 s.

Next, per game (the Reach recipe): record the player's action per key (h2_action_record.py needs the
action size for the game id) -> decode yaw/pitch/throttle/fire/jump/weapon index; hook the players
update; player_new_at_index with a config cloned from player 0 (unknown machine id, then the
host's machine id after creation: the server applies only its own machine's damage); per-life
counter check (H3 action +1 vs unit +0x20C, Reach +4 vs unit +0x288: look for the same check);
a Live reader; map export from the kit (H3ODSTEK, H2AMPEK, H4EK are installed).

## Halo 2 freeze (reproduced, cause not found)

Repro (14:05 CDT, s46): H2 Lockout FFA with the auto brain; after 60 s kill the brain and start
tools/live_bots.py again mid-match. Bots stop moving within a minute and never move again (0/14
for 7 minutes) while the game ticks, botcore reports no fault, the brain keeps writing actions
(seq rising) and the player can still move. Ruled out: unit flag +0x138 bit 0 (the gate in the H2
players update, FUN_1808f59b0) is set on every bot; weapon indexes look valid (01 00 00 ff);
MCC focus. Not yet checked: H2's own action validation (FUN_1806a3910 checks primary != secondary,
interaction type < 9, ...) against the bot actions actually written, and whether the killed brain
left a press-only bit latched. Workaround: do not restart the brain mid-match in Halo 2 (botcore
starts it once per match, so normal play does not hit this).

## Update (s48-s53)

- ODST: one-bot drive verified (logs/drive_odst_pass.jsonl): walk 1.92 m, turn/look 0.0 deg,
  strafe 1.6 m, jump 0.61 m, fire 24 -> 12 rounds. Look vector is unit +0x198 (not +0x188).
  LiveODST reader; full brain runs in Crater Firefight (3 teammates, 41% hits on the Covenant,
  logs/trace_odst_h100_first.jsonl). Map data: the ODST kit's mesh export does BSP 0 only and its
  BSP XML has no collision (tag resources), so tools/bsp2obj (Reclaimer's map library, GPL-3.0,
  built from downloads/reclaimer-src) exports every BSP from the game's .map; Firefight starts
  are the "survival mode" player starting locations. ODST maps: h100, sc100-sc150, l200, l300
  (sc150 zones incomplete). tools/escort_bots.py is the map-free fallback brain.
- H2A: action decoded (fire +0x0C = 2, E 0x400000, weapons +0x48), unit position +0x40 (not
  +0x44), look +0x4E0. Drive (logs/drive_h2a_pass.jsonl): walk 2 m on heading, strafe 2.72 m,
  jump 1.03 m, turn/look 0.0 deg.
- H4: same action as H2A; config TLS+0x90 +0x358 and weapons unit +0x638 verified; team byte
  config +0x140 (without it a bot in free for all ended the match). Drive (logs/drive_h4_pass.jsonl):
  walk 3.26 m, strafe 1.12 m, jump 0.5 m, turn/look 0.0 deg.
- Still to do for H2A/H4: Live readers (health/shield fields, map name), wire into play.py and the
  BOTS tile, map data (exporter agent run on).

## Halo 2 freeze: second attempt (CDT, s53) - unresolved

Test: does the freeze come from respawning, as Halo 3's did? Steps: tools/goto_lobby.py h2
--restart --start (Lockout, Slayer FFA, auto brain); after 60 s kill play.py/live_bots.py; start
tools/live_bots.py 250 --map h2_lockout --game h2 --ffa; log every bot every 5 s for 230 s.
Result: not reproduced; all 6 bots kept moving, through 2-3 respawns each. The first repro
(14:05) froze within a minute. Cause unknown; normal play starts the brain once per match.

