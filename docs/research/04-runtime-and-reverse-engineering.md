# 04 - Runtime layer and reverse engineering (fallback / augment track)

Research date: 2026-10-21. Scope: what a runtime layer (external process, injected DLL, or virtual input) could add on top of the Editing Kit plan (tags + HaloScript) for offline PvP bots in all six MCC games.

Ground rules for this document:

- Strictly offline, Easy Anti-Cheat (EAC) disabled. Nothing here is for matchmaking, and nothing here touches or bypasses EAC. EAC bypass was not researched.
- Every non-obvious claim has a source URL. Claims I could not confirm from a primary source are marked **UNVERIFIED**. My own inferences are labelled as inference.
- "Build" means the MCC executable file version (for example `1.3528.0.0`).

---

## 1. Key findings (short version)

1. **MCC has a clean seam between the UE4 shell and each game DLL, and the community has mapped it.** Each game DLL (`halo1.dll`, `halo2.dll`, `halo3.dll`, `halo3odst.dll`, `haloreach.dll`, `halo4.dll`) exposes a game-engine interface to the shell, and the shell hands each game a "game manager" callback object. The community has documented both (libmcc, AlphaRing, HaloCheckpointManager). Two methods on these interfaces matter most for bots:
   - `i_game_manager::input_update(player, s_input_state*)`: the game asks the shell for each local player's controller state every frame. AlphaRing hooks it to give local players 2 to 4 their own gamepads. A bot layer can fill in this struct directly ([AlphaRing mcc_impl_1.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/mcc_impl_1.cpp), [libmcc input.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/input/input.h)).
   - `i_game_engine::post_command("HS: ...")` (HCM calls it `execute_command`): runs a HaloScript expression inside the running game. HCM's in-game command console works this way ([libmcc game_engine.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/game/game_engine.h), [HCM GameEngineFunctions.cpp](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/GameEngineFunctions.cpp)).
2. **"Player bots" in real player slots are proven for local splitscreen.** AlphaRing adds up to 4 local players in all six games, including multiplayer custom games ([AlphaRing](https://github.com/WinterSquire/AlphaRing), [release 1.0.61 notes](https://github.com/WinterSquire/AlphaRing/releases)). A bot that drives one of those slots is a real player. It shows on the scoreboard, carries flags, scores, and uses real player movement. The ceiling is 4 local players in total (1 human + 3 bots) ([libmcc k_local_player_count via AlphaRing player_manager.h](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/player_manager.h), [libmcc player_control.h `input_states[4]`](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/game/player_control.h)).
3. **More than 4 player bots needs fake network machines.** That is deep, per-game reverse engineering. It has been done only where the whole engine source or client is controlled: the halo-64 decomp bots (`player_new` on a fake machine) ([n64_bots.c](https://github.com/JackTulli/halo-64/blob/HEAD/port/n64/game/n64_bots.c)). No one has published this for MCC itself.
4. **Engine-state documentation exists for all six DLLs, but it is uneven and tied to specific builds.** HaloCheckpointManager (MIT licence) has a per-build offset database with player datum, object tables, biped fields and more for all six games across 13 MCC builds up to `1.3528.0.0` ([InternalPointerData.xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)). libmcc has the deepest Halo 3 structs (player control, game engine globals, player configuration). I found no public MCC documentation of CTF/flag state or of the AI actor struct layout.
5. **Updates break offsets, but vtable layouts have been stable.** HCM lists data offsets per build, but marks the engine function-table slots (`execute_command` at `+0x48`) as `Version="All"` ([InternalPointerData.xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)). AlphaRing broke on an early-2025 Steam build ([issue list](https://github.com/WinterSquire/AlphaRing/issues)). It was fixed in the community fork for `1.3528.0.0` in Sept 2025 ([wouter51/AlphaRing releases](https://github.com/wouter51/AlphaRing/releases)). The original repo was archived in May 2026 ([AlphaRing](https://github.com/WinterSquire/AlphaRing)).
6. **Driving a virtual gamepad (ViGEm) is possible but pointless here.** Stock MCC on PC has no splitscreen, so a virtual pad can only replace the human's own slot. With a splitscreen hook in place, you can write `s_input_state` directly, with no driver. ViGEmBus is also retired: archived Nov 2023 with no further updates ([Nefarius EOL](https://docs.nefarius.at/projects/ViGEm/End-of-Life/)).

**Recommendation in one line:** keep tags + HaloScript as the primary plan. Add a small, optional, offline-only DLL with three features, built on the version-stable interfaces above: (1) up to 3 "player bots" in local splitscreen slots, driven by a bot brain through `input_update`; (2) a HaloScript command channel through `post_command` for an external director; (3) read-only game-state access through a versioned offset file with signature fallback. Prototype on Halo 3 first. Details are in section 7.

---

## 2. How MCC is put together (as revealed by runtime tools)

- **Shell plus game DLLs.** The process is `MCC-Win64-Shipping.exe`. The Microsoft Store build uses `MCC-Win64-Shipping-WinStore.exe` or `MCCWinStore-Win64-Shipping.exe` ([MCC_autosplitter.asl](https://github.com/Burnt-o/MCC_autosplitter/blob/HEAD/MCC_autosplitter.asl)). Each title is a separate DLL: `halo1.dll`, `halo2.dll`, `halo3.dll`, `halo3odst.dll`, `haloreach.dll`, `halo4.dll` ([HCM InternalPointerData.xml module list](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)). libmcc also has a `groundhog` module, which is the Halo 2 Anniversary multiplayer engine ([libmcc tree](https://github.com/SpringContingency/libmcc)).
- **`i_game_engine` (game DLL to shell).** Its vtable includes `initialize_graphics`, `initialize_game(i_game_manager*, s_game_options*)`, `post_message(e_game_message, param)` and `post_command(const char* = "HS: ")`. Known messages include pause, resume, quit, `boot_player` and `team_change(XUID, team)` ([libmcc game_engine.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/game/game_engine.h)). HCM's version of the same interface names the slots `free`, `render_init`, `game_start`, `set_event` and `execute_command`, with offsets valid for all builds ([InternalPointerData.xml, gameEngineCommonFunctionTableFields](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml), [GameEngineDetail.h](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/GameEngineDetail.h)). HCM credits AlphaRing for the original reverse engineering (same file).
- **`i_game_manager` (shell to game DLL).** The vtable includes `signal_end_frame(swapchain)`, `local_user_get_profile(xuid)`, `input_update(local_player, s_input_state*)`, `input_set_rumble`, `local_user_get_player(xuid*, name, size, local_player)` and `local_user_get_gamepad_mapping`. AlphaRing swaps this vtable to add local players, fake XUIDs and names, and per-player input ([AlphaRing mcc_impl_1.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/mcc_impl_1.cpp), [player_manager.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/player_manager.cpp)).
- **Input struct.** libmcc defines gamepad buttons, abstract buttons (triggers, bumpers, sticks, ABXY) and a gamepad state that AlphaRing builds from `XINPUT_STATE` ([libmcc input.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/input/input.h), [mcc_impl_1.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/mcc_impl_1.cpp)). Only local player 0 can use keyboard and mouse in AlphaRing (same file).
- **No retail console.** The developer console exists in the mod tools' Sapien and Standalone builds and in Custom Edition ([c20 developer console](https://c20.reclaimers.net/general/developer-console/)). Retail MCC players report no console ([Steam discussion](https://steamcommunity.com/app/976730/discussions/0/3423312514208633453)). HCM adds one through `execute_command` and hooks the HaloScript print output to show results ([HCM CommandConsoleManager.cpp](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/CommandConsoleManager.cpp)).
- **Game state uses datum arrays.** Fixed-size tables are addressed by a 32-bit handle: a 16-bit index plus a 16-bit salt ([The Tech of Halo 2 slides](https://www.jmeiners.com/shamans/papers/engine/the_tech_of_halo_2.pdf), [c20 H1 game state](https://c20.reclaimers.net/h1/engine/game-state/)). H1 in MCC changed some game-state layout in season 7, so saves from before then are invalid ([c20 H1EK comparison](https://c20.reclaimers.net/h1/h1-ek/)).

---

## 3. Existing tools and what they reveal

| Tool | What it is | What it reveals / proves for us | Status / licence | Source |
|---|---|---|---|---|
| AlphaRing (WinterSquire) | Proxy DLL (`WTSAPI32.dll` in `mcc\binaries\win64`), ImGui menu, splitscreen in all six games, Halo 3 camera tool and object browser | Hooks the `i_game_manager` vtable; per-player XInput; fake local users. Proves real extra player slots in MP custom games. Steam and WinStore offset tables | Archived May 2026; last release 1.0.132 (Mar 2025); no licence file | [repo](https://github.com/WinterSquire/AlphaRing), [releases](https://github.com/WinterSquire/AlphaRing/releases), [wtsapi32.dll.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/main/wtsapi32.dll.cpp) |
| AlphaRing fork (wouter51) | Rebuild for MCC `1.3528.0.0`, Steam only | Shows that updates break it and that a fix means re-deriving offsets | Release Sept 18 2025; no licence | [releases](https://github.com/wouter51/AlphaRing/releases), [issue 126](https://github.com/WinterSquire/AlphaRing/issues/126) |
| libmcc (SpringContingency) | Header-only C++ library of MCC runtime and cache structures | `i_game_engine` and `i_game_manager` interfaces; H3 `s_player_control_globals` (4 input states, unit index); H3 `s_game_engine_globals` (team masks, `statborg_gamestate_index`, map variant); H3 player configuration (name, team, XUID); per-module RVA tables, some with byte signatures | Active Nov 2025; no licence | [repo](https://github.com/SpringContingency/libmcc), [halo3 native.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/native.h) |
| HaloCheckpointManager (Burnt-o) | Practice tool: external C# app, internal DLL, IPC DLL | Per-build pointer database for all six games: `playerDatum`, `objectMetaDataTable`, `objectDataTable`, biped, vehicle and physics fields, `playerViewAngle`, the engine function table. HaloScript console via `execute_command`. AI freeze, input blocking, teleport | MIT; active Sept 2025; supports builds 2094 to 3528 | [repo](https://github.com/Burnt-o/HaloCheckpointManager), [InternalPointerData.xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml), [InterprocService.cs](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMExternal/Services/Interproc/Impl/InterprocService.cs) |
| MCC_autosplitter (Burnt-o / Cambid) | LiveSplit ASL script | External, read-only `DeepPointer` reads: menu, load and pause state, game indicator, IGT, H1 tick counter, BSP, level name, coordinates. A hand-written offset block per build (2094 to 3528) | No licence; Jan 2026 | [MCC_autosplitter.asl](https://github.com/Burnt-o/MCC_autosplitter/blob/HEAD/MCC_autosplitter.asl) |
| mcc-splitter-asr (Scaless) | Rust/WASM port of the same splitter | The same reads done cross-platform through LiveSplit ASR | MIT; Jan 2026 | [repo](https://github.com/Scaless/mcc-splitter-asr) |
| Halo-MCC-VR (pancreations) | OpenXR VR mod for H3 (later Reach, ODST) | Another injected runtime mod; launches through the official EAC-off mode and warns against use with anti-cheat on | GitHub repo now 404; release pages mirrored | [newreleases mirror](https://newreleases.io/project/github/pancreations/Halo-MCC-VR/release/v0.1-alpha) |
| Assembly (XboxChaos) | Map editor with live "poke" to running memory | Community-documented MCC PC support for live edits | Details for current MCC builds UNVERIFIED | [Halopedia Modding](https://www.halopedia.org/Modding), [consolemods H3](https://consolemods.org/wiki/Xbox_360:Game_Modding/Halo_3) |
| MCC Mod Manager | Modpack installer with backups; applies Assembly patches | File-level only | 2022 | [repo](https://github.com/executionByFork/MCC_Mod_Manager) |
| halo3_hook, Halo-3-MCC-DLL-Editor | Byte patches to `halo3.dll` | Small offset-patch tools; an example of how fragile hard-coded patches are | 2021 to 2023 | [halo3_hook](https://github.com/Krevil/halo3_hook), [DLL editor](https://github.com/Apoxied/Halo-3-MCC-DLL-Editor) |
| "Rooms - Slayer Bots with Gamertags" | Workshop mod: AI bots with fake gamertags and unique armour, shared lives, spawns away from sight lines | Shows the tag/script ceiling: names are faked; no real scoreboard rows are claimed | Workshop | [item 3516800855](https://steamcommunity.com/sharedfiles/filedetails/?id=3516800855) |
| "Standoff AI Battlefield" | Workshop H3 Forge/AI war map | Needed an update after the MCC patch of Sept 17 2025 (an example of breakage) | Workshop | [item 2951237541](https://steamcommunity.com/sharedfiles/filedetails/?id=2951237541) |
| halo-64 (decomp port) | Halo CE decomp on N64 with up to 15 bots | Reference design: bots are real players created with `player_new` on a fake machine. Their per-tick actions are injected where network actions are dequeued, then applied by `players_update_before_game` and `unit_control` like a human's. They use Halo's own pathfinding | CC0 | [n64_bots.c](https://github.com/JackTulli/halo-64/blob/HEAD/port/n64/game/n64_bots.c), [README](https://github.com/JackTulli/halo-64) |
| Decompilations | Halo CE (halo-ce-universal, halo-re/halo, punpckhdq/halo), Halo 2 (halo2-decompiled), Reach (ChimpsAtSea/Reach, 360 tag-debug build) | Source-level names and structs for the original engines; good for understanding MCC DLLs but not offset-compatible | Various | [halo-ce-universal (as cited by halo-64)](https://github.com/cybersecurity/halo-ce-universal), [halo-re/halo](https://github.com/halo-re/halo), [punpckhdq/halo](https://github.com/punpckhdq/halo), [halo2-decompiled](https://github.com/kirklandsig/halo2-decompiled), [ChimpsAtSea/Reach](https://github.com/ChimpsAtSea/Reach) |
| Older PC-engine projects | ElDorito (Halo Online), Project Cartographer (H2 Vista), OpenSauce (CE / H2V), SAPP (CE server) | Prior art for player and object table access, server-side scripting and (Cartographer) multiplayer additions on related engines | Mixed | [ElDorito](https://github.com/ElDewrito/ElDorito), [cartographer](https://github.com/pnill/cartographer), [OpenSauce mirror](https://github.com/MirisWisdom/OpenSauce), [SAPP docs](https://halo-sapp.readthedocs.io/en/latest/scripting/game.html) |
| Reclaimer (Python) | Tag/map structure library | Mostly Halo 1 data files; not a runtime tool | PyPI | [reclaimer](https://pypi.python.org/pypi/reclaimer/1.7.5) |

Not covered in this pass: Blamite and the Infinite Runtime Tagviewer. I did not verify any MCC runtime support for either (**UNVERIFIED**). I found no public "MCC player bot" project that drives real player slots in MCC itself.

**Splitscreen on PC:** MCC on PC has never shipped official splitscreen. At launch, 343 said PC splitscreen "is tricky" and they were still evaluating ([Shacknews](https://shacknews.com/article/116768/does-halo-ce-mcc-have-splitscreen-on-pc)). It is available only through mods like AlphaRing. Nucleus Co-op is also mentioned by players (**UNVERIFIED** for current builds).

---

## 4. Engine internals: what is documented per DLL

Legend: Y = public data found; P = partial; N = nothing public found.

| Item | halo1.dll | halo2.dll | halo3.dll | halo3odst.dll | haloreach.dll | halo4.dll | Main sources |
|---|---|---|---|---|---|---|---|
| Player datum / player table pointer | Y | Y | Y | Y | Y | Y | HCM `playerDatum` per build ([xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)) |
| Player configuration (name, team, XUID) | P | P | Y | N | N | N | libmcc H3 `s_player_configuration` ([players.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/game/players.h)) |
| Object table (header, data, salt, type) | Y | Y | Y | Y | Y | Y | HCM `objectMetaDataTable`, `objectDataTable`, `nextObjectSalt`, `objectTypeOffset` |
| Biped / unit fields (position, velocity, health, shields, team, weapon, vehicle) | Y | Y | Y | Y | Y | Y | HCM `bipedDataFields`. H1 also has `movementInput` and `crouchJumpInput` |
| Player control / unit control | P | N | Y | N | N | N | libmcc H3 `s_player_control_globals` (4 input states; output holds `unit_index`; inner layout still opaque `char data[0x78]`) ([player_control.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/game/player_control.h)) |
| Per-local-player input entry point | Y | Y | Y | Y | Y | Y | `i_game_manager::input_update` (shell level, shared by all games) ([AlphaRing](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/mcc_impl_1.cpp)) |
| HaloScript command execution | Y | Y | Y | Y | Y | Y | `post_command` / `execute_command` ([libmcc](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/game/game_engine.h), [HCM](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/GameEngineFunctions.cpp)) |
| Game engine globals (teams, mode) | N | N | P | N | N | N | libmcc H3 `s_game_engine_globals` (team masks, lives, `statborg_gamestate_index`, map variant, game type accessor) ([game_engine.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/game/game_engine.h)) |
| Scores / statborg contents | N | N | P (index only) | N | N | N | same |
| CTF flag / objective state | N | N | N | N | N | N | not found (**UNVERIFIED** whether anyone has it privately) |
| AI actor struct | P (H1 concepts) | N | N | N | N | N | c20 explains AI behaviour from the tag side, not memory layout ([c20 H1 AI](https://c20.reclaimers.net/h1/engine/ai/)). HCM has `AIFreeze` hooks for all games ([HCM tree](https://github.com/Burnt-o/HaloCheckpointManager)) |
| Netcode model | Y (concepts) | P | P | N | N | N | c20: H1 netcode does not sync AI ([c20 netcode](https://c20.reclaimers.net/h1/engine/netcode/), [c20 sync](https://c20.reclaimers.net/h1/guides/multiplayer/synchronization)). |

Notes:

- Offsets move between builds. Example: the H2 `playerDatum` module offset is `0xE7F5E4` in 1.3385 and `0xE805E4` in 1.3528. The H1 `objectMetaDataTable` stayed at `0x1C42248` from 1.3272 through 1.3528 ([InternalPointerData.xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)).
- The decomps give real struct names for players, units, `player_action` and the action queues ([n64_bots.c](https://github.com/JackTulli/halo-64/blob/HEAD/port/n64/game/n64_bots.c)). How closely the MCC 64-bit layouts match the Xbox originals is **UNVERIFIED**. The MCC H1 game-state layout is known to have changed ([c20 H1EK](https://c20.reclaimers.net/h1/h1-ek/)).

---

## 5. Approach comparison

### (a) Tags + HaloScript only (primary plan, covered by other tracks)
- Feasibility: high. Shipped examples exist (Workshop AI maps).
- Unlocks: AI actors fighting in MP maps, fake names (dialogue or HUD tricks), script-driven objectives.
- Limits found here: actors are not players, so no real scoreboard rows, no real flag carrying, no player movement tech.
- Breakage on updates: low to medium. Workshop mods sometimes need rebuilds after patches ([Standoff](https://steamcommunity.com/sharedfiles/filedetails/?id=2951237541)).
- Offline: official, EAC-off workshop path.

### (b) Tags + HaloScript + external process (read memory, send commands)
- Reading: proven and simple. LiveSplit-style `ReadProcessMemory` with pointer chains per build ([MCC_autosplitter.asl](https://github.com/Burnt-o/MCC_autosplitter/blob/HEAD/MCC_autosplitter.asl)).
- Writing commands: there is no retail console. Getting HaloScript in needs code inside the process that calls `post_command` on the game thread. In practice, (b) is a small (d) plus an IPC channel. HCM uses this pattern: an external app plus an internal DLL linked by a shared-memory IPC DLL ([InterprocService.cs](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMExternal/Services/Interproc/Impl/InterprocService.cs)).
- Unlocks: a smarter "team director" in any language (Python, or a local LLM) that reads positions and scores and issues `ai_*` / `cs_*` / object commands. It still controls actors only, so no scoreboard rows.
- Breakage: data offsets per build (medium). The command vtable slot has been stable (`execute_command` at `+0x48`, all builds) ([HCM xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)).
- Latency and throughput of `post_command`: commands go through an SList queue ([libmcc](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/game/game_engine.h)). The per-tick cost and limits are **UNVERIFIED**.

### (c) Player bots in real player slots
- **(c1) Virtual controller (ViGEm/XInput):** stock MCC on PC has one local player, so a virtual pad can only drive the human's slot. With AlphaRing installed, extra local players read `XInputGetState(index)` ([mcc_impl_1.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/mcc_impl_1.cpp)). So a ViGEm pad should work as a bot "controller" with no code changes (inference, **UNVERIFIED** in testing). ViGEmBus is retired: it still works but gets no updates ([EOL](https://docs.nefarius.at/projects/ViGEm/End-of-Life/), [repo](https://github.com/nefarius/ViGEmBus)). Downsides: a kernel driver, an extra layer of lag, and gamepad-only aim (aim assist applies, which may actually help).
- **(c2) Direct input injection:** hook `i_game_manager::input_update` and fill `s_input_state` from the bot brain each frame. This is the same hook AlphaRing already uses. No driver and frame-exact. The brain can still "think in gamepad terms" so the bots move like human players.
- Unlocks: everything that players get for free. Scoreboard rows (names via `local_user_get_player`), flag and bomb carrying, scoring, respawn rules, team assignment (`team_change` message) ([libmcc](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/game/game_engine.h)), and real player physics (jump, crouch-jump, sprint or armour abilities where the game has them). The Workshop "Slayer Bots" author notes that actor bots using player bipeds cannot sprint or sidestep the way players do ([search summary of item 3516800855](https://steamcommunity.com/sharedfiles/filedetails/?id=3516800855); the exact quote is **UNVERIFIED**). It also works in H2C and H4 MP, because bots are players, not actors.
- Limits: at most 4 local players (1 human + 3 bots, so 2v2 or 1v3 at most). Each local player gets a rendered splitscreen view (performance cost, screen clutter). Hiding or minimising bot views needs render hooks. AlphaRing already hooks per-game `render_player_view` ([AlphaRing tree](https://github.com/WinterSquire/AlphaRing), [libmcc render_player_view headers](https://github.com/SpringContingency/libmcc)), but whether bot views can be culled safely is **UNVERIFIED**. The bot brain still needs perception (state reads) and navigation. halo-64 uses Halo's own path code ([n64_bots.c](https://github.com/JackTulli/halo-64/blob/HEAD/port/n64/game/n64_bots.c)). Calling MCC's internal pathfinding needs reverse engineering (**UNVERIFIED** effort). The fallback is a navgraph baked from editing-kit data.
- **(c3) More than 4 bots through fake network machines:** the halo-64 pattern (`player_new` per fake machine, inject actions at network dequeue). This needs per-DLL reverse engineering of the session and simulation layers, which in MCC sit behind the UE4 shell and Xbox Live session code. No public MCC work found. Highest effort and highest breakage risk.

### (d) DLL hooking (the delivery vehicle for b and c)
- Proven loaders: a proxy DLL in `mcc\binaries\win64` (AlphaRing ships as `WTSAPI32.dll` and forwards exports to System32) ([wtsapi32.dll.cpp](https://github.com/WinterSquire/AlphaRing/blob/dev/src/main/wtsapi32.dll.cpp)), or an external injector plus internal DLL (HCM) ([HCM repo](https://github.com/Burnt-o/HaloCheckpointManager)). HCM's exact injection API was not checked (**UNVERIFIED**).
- Hooking libraries in use: SafetyHook (HCM; BSL-1.0) ([HCM README](https://github.com/Burnt-o/HaloCheckpointManager), [safetyhook](https://github.com/cursey/safetyhook)). AlphaRing uses its own vtable, patch and inline hook managers with the HDE64 disassembler ([AlphaRing tree](https://github.com/WinterSquire/AlphaRing)).
- Unlocks: all of the above, plus an in-game ImGui overlay (the AlphaRing and HCM pattern), for example a custom scoreboard overlay that lists actor bots alongside players. That is a cheap way to give (a)-style bots "scoreboard entries" without touching game code.

### Comparison table

| Approach | Real scoreboard rows | Flag/bomb carry | Real player movement | Bot count | Games | Effort (rough estimate) | Breakage risk on MCC update | Offline safety notes |
|---|---|---|---|---|---|---|---|---|
| (a) Tags + HS | No (fake names only) | Scripted workaround only | No (actor movement) | Up to the actor and engine limits | H1, H2A?, H3, ODST, Reach | Medium (other tracks) | Low-medium (rebuild maps) | Official EAC-off path |
| (b) + external brain via memory read + `post_command` | No (an overlay can fake it) | Scripted | No | Same as (a) | All six (command path is shell-level) | Medium: small DLL + IPC + versioned offsets | Medium (data offsets); vtable slot stable so far | Needs injection; EAC-off only |
| (c1) Virtual gamepad + splitscreen mod | Yes | Yes | Yes | 3 max | All six (AlphaRing) | Low-medium (on top of AlphaRing) but driver-based | Medium-high (depends on the AlphaRing fork staying current; it broke once already) | Kernel driver (retired); EAC-off only |
| (c2) `input_update` injection | Yes | Yes | Yes | 3 max | All six | Medium (hook is known; brain + perception + nav is the real work) | Medium (one shell vtable plus game-manager pointer per build; Steam and WinStore differ) | EAC-off only |
| (c3) Fake network players | Yes | Yes | Yes | Up to MP cap (16) | Per game, one at a time | Very high (deep RE per DLL) | High | EAC-off only; must block real joins |
| (d) Overlay scoreboard only | Visual only | n/a | n/a | n/a | All six | Low | Low-medium (D3D11 present hook) | EAC-off only |

---

## 6. Practical notes

### 6.1 DLL loading with EAC off
- Official EAC-off mode: launch "Halo: MCC Anti-Cheat Disabled". Matchmaking is unavailable, file modding is allowed, and the game can still go online for invite custom games and campaign. Back up core files first ([Halo Waypoint support](https://support.halowaypoint.com/hc/en-us/articles/360037475251-How-to-Launch-Halo-The-Master-Chief-Collection-with-Easy-Anti-Cheat-EAC-Disabled); the page returned HTTP 403 to my fetcher, so this content comes from search-engine extracts).
- Proxy DLL: drop it in `Halo The Master Chief Collection\MCC\Binaries\Win64\`. The DLL must be named exactly `WTSAPI32.dll` ([wouter51 release](https://github.com/wouter51/AlphaRing/releases)). Risk: it also loads when the game starts with EAC on. Users report startup errors in that case and are told to remove the DLL before EAC-on play ([Steam discussion via search summary](https://steamcommunity.com/app/976730/discussions/0/1752394282893280375), **UNVERIFIED** detail).
- Steam Workshop cannot ship custom DLLs, so manual setup is required (search-engine extract of a Workshop discussion, [link](https://steamcommunity.com/workshop/filedetails/discussion/2908094235/3768982992496208007), **UNVERIFIED**).
- Microsoft Store / Game Pass builds have different executable names and offsets, and are harder to mod ([MCC_autosplitter.asl](https://github.com/Burnt-o/MCC_autosplitter/blob/HEAD/MCC_autosplitter.asl), [AlphaRing mcc_offset.h](https://github.com/WinterSquire/AlphaRing/blob/dev/src/mcc/mcc_offset.h)). Target Steam first.

### 6.2 How updates break things
- Builds seen in community data: 1.2094, 2448 (S7), 2645 (S8), 2862, 2904, 2969, 3073, 3251, 3272, 3385, 3495, 3498, 3528 ([HCM xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml), [MCC_autosplitter.asl](https://github.com/Burnt-o/MCC_autosplitter/blob/HEAD/MCC_autosplitter.asl)). The latest PC patch I could confirm is Sept 17 2025 ([Pure Xbox](https://www.purexbox.com/news/2025/09/halo-the-master-chief-collection-gets-surprise-update-on-xbox-and-pc)). A March 2026 Exchange update was reported by one secondary source ([rutab.net](https://rutab.net/b/video-games/2026/03/02/halo-the-master-chief-collection-poluchila-neozhidannoe-obnovlenie.html), **UNVERIFIED**, build number unknown).
- What moves: global data RVAs (player datum, object tables, game-manager pointer) and function RVAs. What has stayed put: vtable slot layouts (`execute_command +0x48` marked "All" by HCM), and many struct field offsets. HCM keeps some fields marked "All" for H1 bipeds, with a comment to double-check older patches ([HCM xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)).
- Real incidents: AlphaRing "MCC Hook Failed to Initialize" after a Feb/Mar 2025 Steam update ([issues](https://github.com/WinterSquire/AlphaRing/issues)), fixed in a fork six months later ([wouter51](https://github.com/wouter51/AlphaRing/releases)). Workshop AI maps also needed updates after the Sept 2025 patch ([Standoff](https://steamcommunity.com/sharedfiles/filedetails/?id=2951237541)).

### 6.3 Signature scanning
- libmcc's offset table can attach an AOB pattern to an entry. Example: `c_network_session::can_accept_any_join_request` in `halo3.dll` with pattern `33 D2 F6 81 E4 41 00 00 01 74 ?? 44 8A 81 E4 41 00 00` ([halo3 native.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/native.h)).
- HCM is mostly a hand-curated table per build, with notes on the scan patterns used to re-find entries (for example the H2 `playerDatum` note "scan nw `4c 8d 43 14 89 4b 04`") ([HCM xml](https://github.com/Burnt-o/HaloCheckpointManager/blob/HEAD/HCMInternal/InternalPointerData.xml)).
- Suggested layering for our DLL (inference):
  1. Per-build table, keyed by file version and storefront, kept in a data file (the HCM XML approach).
  2. Signature scan fallback for unknown builds.
  3. Anchor on vtables where possible (interfaces outlive data RVAs).
  4. Validate before use: datum-array header sanity checks. Blam data arrays carry a name string and a max count. That this holds in the 64-bit MCC builds is **UNVERIFIED**.
  5. Fail closed: if any check fails, disable the runtime layer and fall back to pure tags + HS.

### 6.4 Safety (keep it separate from online play)
- Never research, ship or suggest anything that loads with EAC on. Prefer an **injector launcher** over a proxy DLL left in the game folder, so EAC-on launches are never contaminated (inference based on the proxy behaviour above).
- Refuse to start if an EAC process or service is present, if the game was not started by our launcher in EAC-off mode, or if the session has remote players (inference). In Halo 3, libmcc exposes `c_network_session::can_accept_any_join_request`, which is a candidate hook for blocking joins entirely ([halo3 native.h](https://github.com/SpringContingency/libmcc/blob/HEAD/include/libmcc/module/halo3/native.h)).
- EAC-off sessions can still go online for invite custom games ([Waypoint support](https://support.halowaypoint.com/hc/en-us/articles/360037475251-How-to-Launch-Halo-The-Master-Chief-Collection-with-Easy-Anti-Cheat-EAC-Disabled)). The bot layer should hard-block that rather than rely on user discipline.
- Licensing: HCM is MIT, halo-64 is CC0, SafetyHook is BSL-1.0. AlphaRing, its forks and libmcc publish no licence, so treat them as reference only. Do not copy their code without the author's permission ([licence data via GitHub API for each repo above](https://github.com/Burnt-o/HaloCheckpointManager)).

---

## 7. Recommendation

1. **Keep (a) tags + HaloScript as the main product.** It is official, survives updates best, and covers bulk bots.
2. **Build one optional runtime DLL, offline-only, in this order:**
   1. **Command channel (b):** an external "director" process talks to the DLL over shared memory (HCM pattern). The DLL calls `post_command("HS: ...")` on the game thread. Read-only state (players, objects, bipeds) comes from a versioned offset file seeded from HCM's MIT-licensed data, with signature fallback and fail-closed checks. This adds a smarter team brain to tag-based actors in every title without new engine reverse engineering.
   2. **Player bots (c2):** hook `i_game_manager::input_update` (the AlphaRing technique, re-implemented under our own licence) to add up to 3 local "player bots" fed by the brain. This is the only proven route to real scoreboard rows, real flag carrying, real player movement, and bots in Halo 2 Classic and Halo 4 MP. Skip ViGEm (c1): direct injection is simpler and has no driver.
   3. **Overlay scoreboard (d):** cheap. Lists actor bots next to players for modes where (c2) slots are full.
3. **Do not plan on (c3) fake network players for MCC.** It is possible in principle (halo-64), but it is an open-ended per-game reverse-engineering project with the highest breakage risk. Revisit only if a public MCC session RE appears.
4. **Prototype on Halo 3 on Steam build 1.3528** (best documented: libmcc player control and game engine globals, AlphaRing H3 object browser, HCM coverage). Then Halo 1 (HCM plus decomp knowledge). Then Reach, ODST, H2, H4.
5. **Budget for MCC patches:** keep the runtime layer optional, so a patch only disables the extras, never the core mod.
