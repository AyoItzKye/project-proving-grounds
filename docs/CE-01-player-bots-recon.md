# CE-01 - Halo CE player bots: first reverse-engineering pass

Date: 2026-10-21. MCC 1.3528.0.0 (Steam, build tag 2025.08.16), `halo1.dll` 1.3528.0.0, 29.3 MB.
Goal: 16 real players in a Halo CE multiplayer match on one PC, where every slot but the player's is a bot driven by our code (real scoreboard rows, real flag carrying, real player movement).

## 1. What is set up

| Item | Where |
|---|---|
| Game file backup (every game DLL, `MCC\Binaries\Win64`, launcher, `LocalLow\MCC\Config`) | `backups\mcc-2025.08.16\` (237 MB) |
| Ghidra 12.1.4, JDK 21 (Temurin), ReClass.NET 1.2 | `A:\Tool Apps\RE\`, `C:\Program Files\Eclipse Adoptium\` |
| x64dbg | `%LOCALAPPDATA%\Microsoft\WinGet\Packages\x64dbg.x64dbg_...\release\x64\x64dbg.exe` |
| Ghidra project for `halo1.dll` (analysis runs from `ghidra\analyze_halo1.bat`, log `ghidra\halo1_analyze.log`) | `ghidra\mcc_1_3528` |
| Python string-xref + disassembly helper (pefile, capstone) | `tools\xref.py` |
| References (all CC0 or MIT) | `reference\halo-ce-universal` (Halo CE decompilation), `reference\halo-64` (CE bots as real players), `reference\HaloCheckpointManager` (MIT, MCC offsets per build) |

## 2. Findings

1. **A Halo CE decompilation exists and is matching quality.** `halo-ce-universal` (CC0) rebuilds the original Xbox source with Bungie's file paths and assert line numbers (for example `player_new` in `source\game\players.c:1158`). It is our map of what each function in `halo1.dll` does.
2. **Someone already made CE bots that are real players.** `halo-64` (`port\n64\game\n64_bots.c`, CC0) creates up to 15 bots with `player_new()`, each on a fake machine (machines 1 to 3, four players per machine, like remote players in a network game), gives them a name, team and colour through a `network_player` struct, and writes their stick, aim and buttons into the per-tick `player_action` stream that `players_update_before_game` applies exactly like a person's input. The game engine spawns, scores and respawns them itself. Navigation uses **Halo's own pathfinding** (`ai/path.h`), so CE player bots need no custom navmesh.
3. **A fork already lifts CE to 128 players and 128 machines** (`bnunu/halo-ce-universal`, CC0). Shows exactly which limits had to change.
4. **MCC's `halo1.dll` is not the Xbox netcode.** Its type info lists Reach-style networking: `c_network_session`, session membership, `c_simulation_game_engine_player_entity_definition`, `c_simulation_player_respawn_request_event_definition`, and even networked AI (`c_simulation_game_ai_entity_definition`, `c_simulation_networked_ai_action_event_definition`). The gameplay code (players, units, AI, game engine) matches the decompilation, but players are created from the session's membership list. So the injection point on MCC is: add fake peers and players to the host's session membership (or call the player-creation path directly), then feed their actions each tick.
5. **Every MCC game DLL has a hidden `MPBOT: ` command prefix.** In `halo1.dll` it is in the shell-command handler (function at `0x180094590`, check at `0x180095504`) right before the `HS: ` HaloScript prefix. Retail builds swallow `MPBOT: ` commands (they do nothing), which suggests 343's internal multiplayer bot test harness was compiled out. The same string is in `halo2`, `halo3`, `halo3odst`, `haloreach`, `halo4` and `groundhog`. Not checked yet whether any of them still acts on it.
6. **This build is covered by community offsets.** HaloCheckpointManager's data includes 1.3528.0.0. Player datum for Halo 1: `halo1.dll + 0x2D9CD90`, then `+0x4`.

## 3. Plan for the CE player bots

1. Finish Ghidra analysis of `halo1.dll`. Find the decomp functions by shape: `player_new` (initialises `speed_multiplier = 1.0f`, `team_index = 1`, copies an 11-character name, ends in `machine_add_player`), `players_update_before_game`, the player action queue, the session membership add path, and `game_engine` player-add.
2. Read the live player table with ReClass.NET in an anti-cheat-off custom game to confirm the player struct layout against the decomp.
3. Write the loader DLL (injected by our own launcher, only when MCC runs with anti-cheat off, refuses to run with remote players present).
4. Milestone 1: one bot player added to a local Slayer game that stands still, appears on the scoreboard and respawns.
5. Milestone 2: the bot walks and shoots from our input (port the halo-64 brain as the first, simple behaviour).
6. Milestone 3: 15 bots (16 players), teams, CTF flag carrying.
7. Then the human-like brain and team directors from `docs\research\00-RESEARCH-SUMMARY.md`.
