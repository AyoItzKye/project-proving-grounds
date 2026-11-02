# 03 - MCC Modding Pipeline (official kits, loading, workflow, debugging, policy)

Research date: 2026-10-21. MCC build on disk: `2025.08.16.178512.1-Release`.
Scope: Halo CE, 2 (classic and H2A MP), 3, ODST, Reach, 4 on Steam PC, anti-cheat (EAC) off, offline / host-only use.

Conventions:
- Every non-obvious claim carries a source URL. "LOCAL" means verified by reading the player's install (read-only).
- **UNVERIFIED** marks anything not confirmed by a primary source or by local inspection.
- Effort numbers are my estimates, not sourced facts.

---

## 0. Executive summary

1. There are 7 official editing kits (one per engine, including a separate H2A MP kit) plus one uploader (Excession). All kits are Steam "Tools" apps. All but the CE kit require owning that game on Steam. Sources: https://c20.reclaimers.net/general/mod-tools/ , https://www.techradar.com/news/halo-2-and-halo-3-finally-get-official-mod-tools-on-pc
2. The kits ship with the **stock source tags for the stock maps**, including MP scenarios. LOCAL: the Reach kit tag list has every Reach MP, Firefight and campaign scenario, and the CE kit has all CE MP scenarios under `levels\test\...`. So we can open a stock MP map in Sapien, add AI data, and recompile. We do not need to rebuild maps from scratch.
3. Mods load only with EAC disabled. MCC reads `%USERPROFILE%\AppData\LocalLow\MCC\Config\ModManifest.txt`. Each line is a root folder. MCC scans each immediate subfolder for a `ModInfo.json`, and each mod may target only one engine. Sources: Dec 2022 patch notes (https://steamdb.info/patchnotes/9367265 , seen via search snippet; the page itself returned 403 to my fetcher), https://www.halowaypoint.com/news/halo-mcc-december-2022-update
4. Excession (Steam app 1695795) writes `ModInfo.json` plus per-map JSON and uploads to the Workshop. A local mod folder works without uploading. Sources: https://learn.microsoft.com/en-us/halo-master-chief-collection/excession/setup/folderstructure , https://c20.reclaimers.net/general/mod-tools/excession/
5. The tag-test "Standalone" builds are the fast-iteration loop: they load tags directly, have a full console, AI debug draw, and hot tag reload. They have **no networking**, and final testing must be done in retail MCC with a built `.map`. Sources: https://c20.reclaimers.net/h3/h3-ek/h3-standalone-build/ , https://c20.reclaimers.net/hr/hr-ek/hr-standalone-build/
6. Game-type scripting (Megalo, via MegaloEdit) exists only in the Reach, H4 and H2A MP kits. Sources: https://c20.reclaimers.net/hr/hr-ek/ , https://c20.reclaimers.net/h4/h4-ek/ , https://c20.reclaimers.net/h2amp/h2amp-ek/ . CE, H2 classic, H3 and ODST have no game-type scripting. Their only scripting is the scenario's HaloScript.
7. Biggest technical risk for this project: MP netcode in several engines does not sync AI. Halo 1 MP does not sync AI at all (https://c20.reclaimers.net/h1/guides/multiplayer/synchronization/). Host-only offline play avoids the sync problem, but whether AI can spawn at all in an MP game type must be tested per engine.
8. Legal: mods must be free (no selling, no paid access, ads only via YouTube/Twitch), may only use assets from retail MCC, and must carry the Game Content Usage Rules notice. The mod tools EULA bars using the tools for "commercial, non-profit, or revenue-generating activities". Sources: https://www.halowaypoint.com/news/mccs-eula-the-faq , https://www.xbox.com/en-US/developers/rules , https://store.steampowered.com/eula/1695794_eula_0

---

## 1. Official editing kits

### 1.1 Kit table

App IDs and download sizes are LOCAL (from `<Steam library>\steamapps\appmanifest_*.acf`) unless a URL is given.

| Kit (Steam name) | App ID | Folder | Download size | Main executables | Ownership needed |
|---|---|---|---|---|---|
| Halo: CE Mod Tools - MCC | 1532190 | `HCEEK` | 1.06 GB (on disk 1.07 GB, `HCEEK.7z` 1.03 GB) | guerilla.exe, sapien.exe, tool.exe, halo_tag_test.exe (LOCAL) | No, free to everyone (https://www.pcgamer.com/uk/halo-combat-evolved-gets-a-full-suite-of-mod-tools-in-the-master-chief-collection) |
| Halo 2 Mod Tools - MCC | 1613450 | `H2EK` | 5.70 GB | Guerilla, Sapien, Tool, standalone `halo2_tag_test` (https://c20.reclaimers.net/h2/tools/h2-ek/ , https://c20.reclaimers.net/general/mod-tools/) | Yes, H2A on Steam |
| Halo 2 Anniversary MP Mod Tools - MCC | 1695790 | `H2AMPEK` | not yet known (queued, 0 bytes) | Foundation, Sapien, Tool, MegaloEdit, Standalone, TagWatcher, Tag Mover; play builds (https://c20.reclaimers.net/h2amp/h2amp-ek/) | Yes (UNVERIFIED which DLC) |
| Halo 3 Mod Tools - MCC | 1695791 | `H3EK` | 7.54 GB | Guerilla, Sapien, Tool, tool_fast, halo3_tag_test, ManagedBlam, calc_lm_farm_local.py (https://c20.reclaimers.net/h3/h3-ek/ , https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview) | Yes, H3 |
| Halo 3: ODST Mod Tools - MCC | 1695794 | `H3ODSTEK` | 7.34 GB | Same family as H3EK, plus play builds of Sapien/Standalone/Guerilla (July 2023) (https://c20.reclaimers.net/h3odst/h3odst-ek/) | Yes, ODST |
| Halo: Reach Mod Tools - MCC | 1695793 | `HREK` | 7.03 GB (on disk 7.14 GB; `HREK.7z` 6.85 GB) | Foundation.exe, MegaloEdit.exe, ProjectChooser.exe, sapien.exe, sapien_play.exe, reach_tag_test.exe, reach_tag_play.exe, tool.exe, tool_fast.exe, bin\ManagedBlam.dll, bin\ManagedMegalo.dll (LOCAL) | Yes, Reach (https://c20.reclaimers.net/hr/hr-ek/) |
| Halo 4 Mod Tools - MCC | 1695792 | `H4EK` | 9.84 GB | Foundation, Sapien, Tool, MegaloEdit, Standalone, TagWatcher, Tag Mover; play builds (https://c20.reclaimers.net/h4/h4-ek/) | Yes, H4 (UNVERIFIED, c20 page silent) |
| Halo MCC Mod Uploader (Excession) | 1695795 | n/a | n/a | Excession | Owners of MCC on Steam (https://c20.reclaimers.net/general/mod-tools/excession/ , https://www.halowaypoint.com/news/halo-mcc-december-2022-update) |

Notes:
- "Foundation for H2A" in our brief is right: H2A MP uses the Reach/H4 style toolchain (Foundation tag editor, GR2 models, MegaloEdit). c20 says its tools are "closest to Halo 4's tools" (https://c20.reclaimers.net/h2amp/h2amp-ek/).
- Reach, H4 and H2A MP replace Guerilla with **Foundation**. They also use GR2 (Granny) as the model format instead of ASS/JMS (https://c20.reclaimers.net/hr/hr-ek/).
- Build flavors: `*_tag_test` is the AI-debug-capable test build. `*_play` builds were added in July 2023 (https://c20.reclaimers.net/h3odst/h3odst-ek/ , https://c20.reclaimers.net/h4/h4-ek/). Exactly what `_play` drops compared to `_tag_test` is UNVERIFIED. It is probably faster and has fewer asserts.
- Kit versions: LOCAL `HCEEK\build_tag.txt` and `HREK\build_tag.txt` both read `2023.07.17.176677.1-QFE1`. The last changelog entries are July 2023 (H2/H3/ODST/HR/H4) and February 2024 (H1, H2A MP) (https://c20.reclaimers.net/h1/h1-ek/ , https://c20.reclaimers.net/h2amp/h2amp-ek/). c20 says "Steam updates are unlikely now that development has halted" (https://c20.reclaimers.net/general/mod-tools/).

### 1.2 Install and tag extraction (all kits)

From https://c20.reclaimers.net/general/mod-tools/ and LOCAL readmes:
1. Install the kit from the Steam Library "Tools" section. The Windows Store version of MCC is unsupported.
2. Steam > right-click the kit > Manage > Browse local files.
3. Run `<KIT> (Extract).bat`. LOCAL content: `.\bin\x64\7zr.exe x .\HREK.7z`. This creates the `tags\` and `data\` folders, which hold the stock tags, HaloScript sources and shader sources.
   - LOCAL `README_MODDING.txt`: "The tools installer does not automatically extract files, to avoid future tool updates overwriting any content you may have made changes to."
4. Optional: add the kit folders to Windows Defender exclusions so Sapien and Standalone load faster (c20).
5. H3/ODST/Reach: copy the game's `fmod` folder from the MCC install into the kit, or Sapien/Standalone will have no sound (https://c20.reclaimers.net/h3/h3-ek/ , https://c20.reclaimers.net/hr/hr-ek/hr-standalone-build/).
6. H2: after updates, delete `shader_cache` and refresh the shader templates (https://c20.reclaimers.net/h2/tools/h2-ek/).
7. Updating: back up any modified stock tags, then re-run the extract and replace all. Updates refresh the `.7z` and never touch `tags\` directly (c20).

Folder layout (https://c20.reclaimers.net/general/mod-tools/ , https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview):
- `data\` holds source assets and `.hsc` scripts and mirrors `tags\`.
- `tags\` holds the stock tags plus our own.
- `maps\` is created by Tool when the first map is built.
- H1A-EK and H2-EK accept `-tags_dir`, `-data_dir` and `-game_root_dir` to point at another tag set. H3-EK does not (c20). For the Reach and later kits this is UNVERIFIED.

### 1.3 Stock MP source content (LOCAL, from `bin\!public_tags.txt`)

- HCEEK (11,538 tags): MP scenarios `levels\test\{beavercreek, bloodgulch, boardingaction, carousel, chillout, damnation, dangercanyon, deathisland, gephyrophobia, hangemhigh, icefields, infinity, longest, prisoner, putput, ratrace, sidewinder, timberland, wizard}`, plus campaign `a10`..`d40` and `levels\test\tutorial`.
- HREK (62,017 tags): MP `levels\multi\{20_sword_slayer, 30_settlement, 35_island, 45_aftship, 45_launch_station, 50_panopticon, 52_ivory_tower, 70_boneyard, forge_halo, dlc\dlc_invasion, dlc\dlc_medium, dlc\dlc_slayer}`, `levels\dlc\{cex_*, condemned, trainingpreserve, ff_unearthed}`, all `levels\firefight\ff*`, all `levels\solo\m*`, and `levels\test\box`. The stock lightmap tags ship too (`*_faux_lightmap.scenario_lightmap`, `scenario_lightmap_bsp_data`, `scenario_structure_lighting_info`). An AI-only edit therefore should not require a relight. This is UNVERIFIED in practice, but the same reasoning applies to H3, where the March 2022 update added lighting info (https://c20.reclaimers.net/h3/h3-ek/).
- 149 `.character` / `.style` tags ship in HREK (LOCAL). These are the AI "brain" and behavior-set tags we would clone for bots.
- H2/H3/ODST/H4/H2AMP tag lists: not checked yet (kits still downloading).

### 1.4 Known limitations per kit (what is NOT possible)

| Kit | Limitation | Source |
|---|---|---|
| All | No engine source code. No new HaloScript functions. You cannot declare new scripts or globals from the console | https://c20.reclaimers.net/general/developer-console/ |
| All | Standalone/tag_test builds behave differently from retail. Final tests must use cache files in MCC | https://c20.reclaimers.net/h3/h3-ek/h3-standalone-build/ , https://c20.reclaimers.net/h1/h1-ek/h1-standalone-build/ |
| H1 | Standalone has no networking (it does load MP scenarios and game variants). H1A maps are not compatible with Custom Edition. "Some AI behaves differently than in cache builds" | https://c20.reclaimers.net/h1/h1-ek/h1-standalone-build/ , https://c20.reclaimers.net/h1/h1-ek/ |
| H1 | MP netcode does not sync AI, manually controlled devices or scripted events | https://c20.reclaimers.net/h1/guides/multiplayer/synchronization/ |
| H2 | No resource sharing. PRT simulation tool not included. Tag moving is manual. MCC applies runtime MP balance tag patches that Sapien/Standalone do not show | https://c20.reclaimers.net/h2/tools/h2-ek/ , https://c20.reclaimers.net/h2/ |
| H2 | The H2EK targets the H2 classic engine. H2A MP maps (`groundhog\maps\ca_*`) need the separate H2AMPEK. Classic-only assets can be invisible or broken in Anniversary graphics mode | https://c20.reclaimers.net/h2amp/h2amp-ek/ ; Nexus author reports summarized in search (UNVERIFIED) |
| H3/ODST | No resource sharing. Single-threaded lightmapping broken (use the multi-process script). Forging objects in Standalone crashes | https://c20.reclaimers.net/h3/h3-ek/ , https://c20.reclaimers.net/h3odst/h3odst-ek/ |
| H3/ODST/HR | Standalone has "no network functionality", is "meant for single-player maps", and the UI cannot load every map | https://c20.reclaimers.net/h3/h3-ek/h3-standalone-build/ , https://c20.reclaimers.net/hr/hr-ek/hr-standalone-build/ |
| HR | Stock tags lack import info, so stock source assets cannot be re-extracted that way. Single-process lightmapping broken | https://c20.reclaimers.net/hr/hr-ek/ , https://c20.reclaimers.net/hr/hr-ek/hr-tool/ |
| H4 / H2AMP | Limitations not documented on c20 (UNVERIFIED) | https://c20.reclaimers.net/h4/h4-ek/ |
| H3/ODST/H2 | Guerilla shows red text and greyed folders for all tags. This is cosmetic and harmless | https://c20.reclaimers.net/h3/h3-ek/ |

---

## 2. How mods are loaded in MCC

### 2.1 Discovery
- `ModManifest.txt` lives in `%USERPROFILE%\AppData\LocalLow\MCC\Config\` (LOCAL path confirmed). Each line is a directory. MCC enumerates each directory's **immediate** subfolders and reads their `ModInfo.json`. This only happens in EAC-bypass mode. "Each individual mod may only target a single engine." Sources: Dec 2022 patch notes (https://steamdb.info/patchnotes/9367265 , via search snippet), https://www.halowaypoint.com/news/halo-mcc-december-2022-update
- Steam Workshop subscriptions are picked up on the next EAC-off launch. Items downloaded while MCC is running are not detected until relaunch (https://support.halowaypoint.com/hc/en-us/articles/28916975982868-How-to-Download-and-Play-Mods-for-Halo-The-Master-Chief-Collection-via-the-Steam-Workshop , via search summary; the page returned 403 to my fetcher).
- Launch: Steam Play > "Play Halo: MCC Anti-Cheat Disabled (Mods and Limited Services)". Matchmaking is blocked in this mode (https://support.halowaypoint.com/hc/en-us/articles/360037475251-How-to-Launch-Halo-The-Master-Chief-Collection-with-Easy-Anti-Cheat-EAC-Disabled).

### 2.2 Mod package format (Excession)
From https://learn.microsoft.com/en-us/halo-master-chief-collection/excession/setup/folderstructure and the pages linked from it:
- Layout: `<root folder>\<mod folder>\`. Excession (and MCC) only find mod folders **one level** below a root folder.
- `maps\` holds our compiled `.map` files. Excession does not copy them in for you.
- `images\` holds PNG images (thumbnail, large image, loading screen ~1920x1080). They must be inside the mod folder (https://learn.microsoft.com/en-us/halo-master-chief-collection/excession/creatingmodpackage/specifyingproperties).
- `ModInfo.json` is always created by Excession and identifies the mod. MP mods also get a `multiplayer\` folder with one JSON per map.
- The full field schema of `ModInfo.json` is **UNVERIFIED**: no public schema was found. Plan: let Excession generate it once, then read and diff it.
- Per map you set a "Scenario File Name": the scenario tag path relative to `tags\`, no extension (example `levels/my_campaign/my_campaign_map1`). Excession does **not** validate this path or check that the `.map` exists. During upload it ships the whole mod folder unchecked.
- The Mod Folder cannot be changed after the mod is created (https://learn.microsoft.com/en-us/halo-master-chief-collection/excession/creatingmodpackage/creatinghome).
- MP map properties: Allow Saved Films, Max Teams (overall or per game type), and an imported `multiplayer_object_types.bin`. **If that file is empty or missing, only the Infection game variant is available on the map.** That is a classic first-timer trap (specifyingproperties page above).
- Excession can link Game Variant files and set campaign/Firefight insertion points. Zone set IDs are numbers for H3/ODST and text for the other games (same page).
- Excession must have Steam running to upload. The preview image must be 1 MB or less (https://learn.microsoft.com/en-us/halo-master-chief-collection/excession/uploading/uploadinghome).
- Since Dec 2022, Excession auto-tags items by engine and SP/MP, logs missing map files, and hides invalid content in the MCC UI. Gamepad preset mods were added in July 2023 (https://c20.reclaimers.net/general/mod-tools/excession/).

### 2.3 How a modded map appears, and multiplayer
- Modded MP maps appear in Custom Games map selection when MCC runs EAC-off. Everyone in a lobby needs the same mod. Sources disagree on whether the Custom Game Browser works with EAC off; invites are the reliable route (search summary of Steam discussions, **UNVERIFIED**). For our offline, host-only use case this does not matter.
- The exact UI path (for example a "Mods" filter in the map picker) is **UNVERIFIED**. Check in-game on day 1.

### 2.4 Map variants vs game variants vs map files
- Map variants (`.mvar`) are Forge layouts on top of a base map. LOCAL: stock ones live in `<MCC>\haloreach\map_variants\*.mvar`; the user's own live in `%USERPROFILE%\AppData\LocalLow\MCC\LocalFiles\<xuid>\HaloReach\Map\*.mvar` (also `Halo2A\Map`).
- Game variants (`.bin`) are rule sets. LOCAL: `<MCC>\haloreach\game_variants\*_054.bin` and others.
- AI data (squads, zones, firing positions, pathfinding, objectives) lives in the scenario tag. It therefore has to be compiled into a `.map` file. A Forge map variant cannot carry it (**UNVERIFIED**, but MCC Forge has no AI placement as far as I found).
- **Edit shipped maps or make copies?** Make copies. Open the stock scenario from the kit's `tags\`, "save as" to our own path (for example `levels\multi\bots\30_settlement_bots\...`), build our own `.map`, and ship it in a mod folder. Excession gives each map a generated Map GUID (specifyingproperties page). The older pre-2022 method was to overwrite stock `.map` files in the install, because "MCC currently doesn't look for any new maps" (2020: https://steamcommunity.com/app/976730/discussions/0/1752402219403362124). Avoid it: a Steam verify or update reverts it, and it risks breaking EAC-on play. Whether a mod map may reuse the exact stock scenario path without conflicts is **UNVERIFIED**, which is another reason to rename.

### 2.5 New game-variant scripting
- Reach, H4 and H2A MP: yes, via **MegaloEdit** (Megalo game-type scripting). LOCAL: `HREK\MegaloEdit.exe` and `bin\ManagedMegalo.dll`. July 2023 changes added temporaries, `begin` actions and several backported H4 actions. MegaloEdit can compile a script or directory from the command line (https://c20.reclaimers.net/hr/hr-ek/). Tags `megalo_string_id_table` and `megalogamengine_sounds` exist (https://c20.reclaimers.net/hr/tags/megalo_string_id_table).
- CE, H2 classic, H3, ODST: no game-type scripting in the kits. Game variants there are settings only. Custom logic must go in scenario HaloScript (`.hsc` in `data\`), which also runs in MP. H1 MP scripts ran only for the host until the February 2024 fix (https://c20.reclaimers.net/h1/h1-ek/).

---

## 3. Per-game workflow: open MP scenario, add AI, compile, test, iterate

### 3.1 Generic loop (all engines)
1. Extract the kit (1.2). Copy the stock MP scenario to our own tag path.
2. Sapien: open the scenario. Add character/style references, AI zones, areas and firing positions, then squads (and in H3+, objectives/tasks). Generate pathfinding (where the engine needs it) and add hints for jumps, ladders and teleporters.
3. Quick test in Standalone (`*_tag_test`): it loads tags directly, so there is no compile step, and tags hot-reload on save (https://c20.reclaimers.net/hr/hr-ek/hr-standalone-build/).
4. Build the cache: `tool build-cache-file <scenario> <platform>` writes `maps\<name>.map`.
5. Copy the `.map` into the mod folder's `maps\` and set up the mod in Excession (local only, no upload). Make sure the root folder is listed in `ModManifest.txt`.
6. Launch MCC EAC-off > Custom Games > our map > a game type that the map's object types allow.
7. Iterate. Most AI tuning (character tags, firing positions) can be done in Standalone. Do a retail build only for checkpoints.

### 3.2 Halo CE (HCEEK)
- AI model: `actor` / `actor_variant` tags and encounters with firing positions in Sapien. Pathfinding is computed directly on collision BSP surfaces in H1 (https://learn.microsoft.com/en-us/halo-master-chief-collection/h2/ai/aipathfinding , which contrasts H1 with H2).
- Build: LOCAL `HCEEK\build_all.bat` uses `tool build-cache-file levels\a10\a10 remastered read_write 1`, i.e. `<scenario> <classic|remastered> <resource map usage> <log tag loads>`. c20 shows a `classic` example: `tool -tags_dir hek_tags build-cache-file levels\test\tutorial\tutorial classic` (https://c20.reclaimers.net/general/mod-tools/). Tool can target "classic" or "remastered" mode (https://c20.reclaimers.net/h1/h1-ek/).
- Test: `halo_tag_test.exe -windowed`, then the console commands `game_variant slayer` and `map_name levels\test\bloodgulch\bloodgulch`. Put them in `init.txt` to auto-run. Standalone **does** load MP scenarios and game modes, but not over a network (https://c20.reclaimers.net/h1/h1-ek/h1-standalone-build/). (The 2021 launch note said Standalone would not load MP levels; c20 is newer.)
- Logs go to the `reports` folder (for example `debug.txt`). `-verbose` adds Tool logging. `-noassert` speeds up lightmaps (https://c20.reclaimers.net/h1/h1-ek/).
- Lightmaps are only needed after a geometry change: `tool lightmaps <scenario> <bsp> <quality> <stop>`. That is the legacy syntax; confirm it for H1A on day 1 (UNVERIFIED).

### 3.3 Halo 2 classic (H2EK)
- AI model: character tags, zones, areas, firing positions (about 6 per zone), squads (https://learn.microsoft.com/en-us/halo-master-chief-collection/h2/guides/guidebasicai). Sapien includes AI and can generate pathfinding (https://c20.reclaimers.net/h2/tools/h2-ek/).
- Debug draw: `ai_render_sectors 1`, `ai_render_sector_bsps 1`, `ai_render_user_hints 1`, `ai_render_hints 1`, and the Sapien hierarchy entry "structure data > pathfinding debug" (left/right click sets the path start/end) (https://c20.reclaimers.net/h2/engine/pathfinding).
- Standalone: `halo2_tag_test` (https://c20.reclaimers.net/general/mod-tools/).
- Build command syntax for H2: UNVERIFIED. Check `tool` with no arguments on day 1.

### 3.4 Halo 2 Anniversary MP (H2AMPEK)
- Foundation-based, closest to the H4 tools. Has a `build-cache-file-custom` command (https://c20.reclaimers.net/h2amp/h2amp-ek/). The AI workflow is probably like Reach/H4 (UNVERIFIED). The stock MP maps are `groundhog\maps\ca_*.map` (LOCAL).
- Whether AI runs in H2A MP game types is UNVERIFIED and is a top research item.

### 3.5 Halo 3 / ODST (H3EK, H3ODSTEK)
- AI model: character + style tags, squads (fireteams with starting positions), objectives/tasks, zones/areas/firing positions. Pathfinding comes from Sapien "Scenarios > Generate all pathfinding data". Regenerate after any hint or firing-position change. A yellow triangle means no pathfinding; a green triangle means no valid objective/task/zone (https://c20.reclaimers.net/h3/engine/ai/ , https://c20.reclaimers.net/h3/engine/pathfinding/).
- Build: `tool_fast build-cache-file levels\multi\riverworld\riverworld x64` (https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview). c20 lists `pc` as the default platform and says `use-fmod-data` is on by default (https://c20.reclaimers.net/h3/h3-ek/h3-tool/ , https://c20.reclaimers.net/h3/h3-ek/). Resolve the `x64` vs `pc` discrepancy by running `tool_fast build-cache-file` with no arguments (UNVERIFIED which is current).
- Lightmaps (only needed after geometry changes): `python calc_lm_farm_local.py "levels\multi\riverworld\riverworld" riverworld medium all`. It uses 100% of all logical CPUs (https://c20.reclaimers.net/h3/h3-ek/h3-tool/).
- Test: `halo3_tag_test.exe` with `game_start <scenario>` in `init.txt`. Home opens the debug menu; add our own entries in `bin\debug_menu_user_init.txt`. F1-F6 are AI hotkeys (F6 erases AI spawned by `ai_place`). Sapien runs `editor_init.txt` at startup (https://c20.reclaimers.net/h3/h3-ek/h3-standalone-build/ , https://c20.reclaimers.net/h3/h3-ek/h3-sapien/).
- Whether Standalone can run an MP game type: c20 says it is "meant for single-player maps" (no network). LOCAL: the Reach tag_test binary contains `game_multiplayer` and `game_variant` strings, so a `game_multiplayer <type>` before `game_start` may work (UNVERIFIED, test on day 1).
- ODST: Firefight maps launch from the Standalone main menu (Sept 2022) (https://c20.reclaimers.net/h3odst/h3odst-ek/). ODST has no competitive MP maps in MCC (LOCAL: `halo3odst\maps` has only campaign/Firefight maps), so ODST "PvP" would mean Firefight or campaign spaces.

### 3.6 Reach (HREK)
- Same AI model as H3 (squads, objectives, zones), with Foundation as the tag editor.
- Build: `tool build-cache-file "levels\multi\30_settlement\30_settlement" pc` (https://c20.reclaimers.net/hr/hr-ek/hr-tool/). LOCAL `HREK\BuildMapsSharedOptimizedPlusSharedSounds.ps1` is the stock full-rebuild script (shared.map plus per-language); we will not need it for single mod maps.
- Lightmaps: `python calc_lm_farm_local.py "levels\multi\30_settlement\30_settlement" 30_settlement medium all`. Valid qualities include `direct_only`, `draft`, `low`, `medium`, `high`, `super`. Single-process `faux_lightmap` is broken (https://c20.reclaimers.net/hr/hr-ek/hr-tool/). LOCAL: the script calls `tool_fast faux_farm_<stage>`.
- Test: `reach_tag_test.exe` with `init.txt` containing `game_start levels\solo\m20\m20`. Stock scenarios load from the debug menu. Ctrl+C toggles deathless; `cheat_all_weapons` (https://c20.reclaimers.net/hr/hr-ek/hr-standalone-build/).
- Reach AI syncs in co-op Firefight in retail, so Reach is the most promising engine for AI in a networked game (Firefight netcode). Whether AI spawns in Reach MP game types (Slayer etc.) is UNVERIFIED.

### 3.7 Halo 4 (H4EK)
- Evolution of the Reach tools: Foundation, MegaloEdit, TagWatcher, Tag Mover, play builds (https://c20.reclaimers.net/h4/h4-ek/). The workflow is probably the same as Reach (UNVERIFIED).
- Spartan Ops / Firefight-style maps (`ff*` in `halo4\maps`, LOCAL) are a fallback test bed.

### 3.8 Fast iteration tips
- Keep Standalone open: tag edits reload live, and big edits reset the map (c20 standalone pages).
- Use `init.txt` / `editor_init.txt` / `debug_menu_user_init.txt` to script repeatable test setups (spawn squads, toggle debug draw, set game variant).
- Only rebuild `.map` and relaunch MCC for milestone checks. MCC must be restarted to pick up new or changed mods (Workshop note above; for local mods, assume the same, UNVERIFIED).
- Osoyoos is a community launcher that wraps tool commands (https://c20.reclaimers.net/general/mod-tools/). It is optional.

---

## 4. Shared vs per-game work

### 4.1 Reusable across games
- Design concepts: bot roles, combat loop, map coverage patterns (firing-position grids, hint placement for jumps, ladders and teleporters), test plans, telemetry schema.
- **ManagedBlam** automation for H3, ODST, Reach and H4: C# (.NET Framework 4.8) or Python via pythonnet (Python confirmed only for Reach and later). It can read and write tag fields and create blocks and tags. Example: open `scnr`, `AddElement()` to the zones block, `Save()`. Saving takes about 1 s. In H3, field indices shift with hidden fields, so select fields by name. You must call `ManagedBlamSystem.InitializeProject(...)` and disable High Entropy ASLR (https://c20.reclaimers.net/general/mod-tools/managed-blam/). This is how we can auto-generate firing positions and squads across many maps instead of clicking them in Sapien.
  - One code base is possible, but each kit has its own DLL and tag layouts, so we need a per-game field map.
- Python lightmap/build scripts and batch files (same pattern in H3/ODST/HR).
- Megalo knowledge between Reach, H4 and H2A MP.

### 4.2 Must be redone per game
- Character/style tags and AI tuning: different tag definitions per engine (H1 `actor`/`actor_variant`, H2 `character`, H3+ `character` + `style` + objectives).
- AI placement per map: zones, firing positions, squads, objectives, hints.
- HaloScript: dialects differ per engine (https://c20.reclaimers.net/general/developer-console/ notes each game has its own functions).
- Pathfinding generation and validation per map.
- Excession packaging: one mod per engine at minimum.
- H1 and H2 have no ManagedBlam (it ships only with post-H2 kits). Automation there needs community tools (UNVERIFIED which work with H1A/H2 MCC tags) or manual Sapien work.

### 4.3 Effort estimate (my estimate, not sourced)
| Item | First map in an engine | Each additional map, same engine |
|---|---|---|
| Learn the kit, build an unmodified stock MP map, load it in MCC | 1-2 days | n/a |
| Bot character/style tags and base behavior | 2-5 days | ~0 (reuse) |
| AI placement: zones, firing positions, squads, objectives, hints, pathfinding | 1-2 days manual | 0.5-1 day manual; ~2-4 h with ManagedBlam scripts |
| Spawn/respawn and scoring glue (HaloScript or Megalo) | 2-4 days | 0.5 day |
| Build, MCC test, fix loop | 1 day | 0.5 day |
| **Total** | **~1-2 weeks per engine** | **~1-2 days per map** (manual), less with automation |

The engines most likely to need extra time are H2 classic, H2A MP and H4, because MP AI may not work at all there (sections 0 and 3).

---

## 5. Debugging and telemetry

### 5.1 In tag builds (Sapien and Standalone)
- Console with `~`. Tab completion, history, `help <function>`, `cls`. You cannot declare new scripts or globals in the console (https://c20.reclaimers.net/general/developer-console/).
- Debug menu: Home. Add custom items in `bin\debug_menu_user_init.txt`. Do not edit the stock `debug_menu_init.txt`, which updates overwrite (https://c20.reclaimers.net/hr/hr-ek/hr-standalone-build/).
- AI debug draw (confirmed names):
  - Reach (LOCAL, `HREK\bin\debug_menu_init.txt`): `ai_render_behavior_stack_all`, `ai_render_command_scripts`, `ai_render_dialogue_records`, `ai_render_non_walkable_sectors`, `ai_render_object_hints`, `ai_render_object_hints_all`, `ai_render_orders`, `ai_render_paths`, `ai_render_paths_avoided`, `ai_render_paths_destination`, `ai_render_paths_text`, `ai_render_sector_bsps`. LOCAL: `reach_tag_test.exe` contains 193 distinct `ai_render_*` strings and many `ai_debug_*` globals (for example `ai_debug_path`, `ai_debug_combat_status`, `ai_debug_perception_data`, `ai_debug_invisible_player`, `ai_debug_ignore_player`, `ai_debug_dump_behavior_tree`).
  - Reach scripting reference: `ai_render_paths_all`, `ai_render_evaluations_shading_all`, `ai_lines`, `auto_graph <quantity>`, `breakpoint`, `core_save` / `core_load`, and `ai_dialogue_log_dump <name>`, which writes a CSV file (https://c20.reclaimers.net/hr/engine/scripting/).
  - H3: `ai_render_all_actors` (needed for the others), `ai_render_behavior_stack`, `ai_render_tracked_props`, `ai_render_targets`, `ai_render_shooting`, `ai_render_status_flags`, `ai_debug_emotions` (https://c20.reclaimers.net/h3/engine/ai/).
  - H2: `ai_render_sectors`, `ai_render_sector_bsps`, `ai_render_hints`, `ai_render_user_hints` (https://c20.reclaimers.net/h2/engine/pathfinding).
  - H1 (LOCAL, `HCEEK\bin\debug_menu_init.txt`): `ai_render_paths`, `ai_debug_invisible_player`, `ai_erase_all`. c20 says Standalone exposes all `ai_render_*` and `ai_debug_*` globals (https://c20.reclaimers.net/h1/h1-ek/h1-standalone-build/).
- Logs: Tool and Standalone write to `reports\` (for example `debug.txt`) (https://c20.reclaimers.net/h1/h1-ek/ ; for H3, "Reports are now contained within the reports folder", https://c20.reclaimers.net/h3/h3-ek/).
- HaloScript `print`: works in tag builds. Whether it outputs anything in retail cache builds is **UNVERIFIED** (it is likely compiled out).

### 5.2 In retail MCC (EAC off)
- No developer console in retail (UNVERIFIED; c20 does not say). LOCAL: `MCC\Binaries\Win64\debug.log` exists but is 0 bytes.
- Built-in data: post-game carnage report on screen; Theater/saved films in H3 and later (Excession has an "Allow Saved Films" flag per map).
- Reading game state for our analysis:
  - DLL injection works with EAC off. AlphaRing loads a DLL from `mcc\binaries\win64` and adds split-screen, an H3 camera tool and an H3 object browser (https://github.com/WinterSquire/AlphaRing). This proves a custom DLL can read engine memory for telemetry. Expect breakage after MCC updates; AlphaRing broke after an update in 2025 (search summary of r/halomods, UNVERIFIED).
  - Assembly can poke and read cache data in real time (https://c20.reclaimers.net/h3/). Its MCC-PC memory support for the current build is UNVERIFIED.
  - Within the game: Megalo (Reach/H4/H2A MP) can track scores and stats in-game but cannot write files (UNVERIFIED). HaloScript can count events in tag builds.
- Recommendation: do AI behavior analysis in `*_tag_test` with debug draw, `auto_graph` and `ai_dialogue_log_dump`. For match-level telemetry in retail, plan an external read-only memory reader (EAC off). Treat it as a separate track because offsets change with every MCC update.

---

## 6. Legal and policy

Not legal advice; summarized from primary sources.
- **MCC EULA FAQ** (https://www.halowaypoint.com/news/mccs-eula-the-faq):
  - Selling mods or being paid for them: "At this time no".
  - "Anything contained within MCC is allowed to be used for modding efforts", but "Only the assets contained within the retail version of MCC are allowed". Assets from other 343/Microsoft titles are excluded.
  - Any legally obtained tools may be used.
  - "you are free to share your mods as you see fit" (not only on the Workshop).
  - Competing services: the FAQ points to the EULA's "Competing Service" section, which I could not retrieve (UNVERIFIED wording).
- **Mod tools EULA** (ODST kit, https://store.steampowered.com/eula/1695794_eula_0):
  - You may not "use the software for commercial, non-profit, or revenue-generating activities".
  - No reverse engineering of the tool software. No working around its technical limits.
  - No sharing, publishing or distributing "the software" itself.
  - The tools may talk to Microsoft services that collect data.
  - Provided as-is; damages capped at USD 5.
  - Each kit has its own EULA at `store.steampowered.com/eula/<appid>_eula_0`. The others are assumed similar (UNVERIFIED).
  - Implication: never redistribute kit executables, ManagedBlam, or the extracted stock tag set as a package. Ship only our `.map` files, mod metadata, and our own source code and scripts.
- **Xbox Game Content Usage Rules** (https://www.xbox.com/en-US/developers/rules):
  - Personal, non-commercial use only. You cannot charge for the mod, put it behind a paywall, or put it on a page that sells things. Ad revenue is allowed only via YouTube/Twitch programs.
  -.
  - Don't use the game's name in our mod's title in a way that implies endorsement, and don't use the game's logos in our logos.
  - Required notice: "[Name of the Microsoft Game] © Microsoft Corporation. [The title of your Item] was created under Microsoft's "Game Content Usage Rules" using assets from [Name of the Microsoft Game], and it is not endorsed by or affiliated with Microsoft."
  - Distribution grants Microsoft a broad license to our item. Microsoft may revoke permission at any time.
- **Steam Workshop:** governed by the Steam Subscriber Agreement (https://store.steampowered.com/subscriber_agreement/ ; the Workshop legal page links there, https://steamcommunity.com/workshop/workshoplegalagreement/). Specific clause details are UNVERIFIED.
- **Our position:** a free, offline / EAC-off bot mod that uses only MCC assets and the official tools fits the published rules. The open question is whether any code that reads game memory (5.2) counts as reverse engineering under the Usage Rules or the MCC EULA. Keep that tooling private and local until it has been reviewed (UNVERIFIED legal status).

---

## 7. Pitfalls first-time MCC modders hit

1. **Forgetting to extract.** The kit installs only a `.7z`. Run `<KIT> (Extract).bat` first (LOCAL readme).
2. **Disk space.** HREK alone is 7.1 GB before extraction; the extracted tags and data add more (exact extracted size UNVERIFIED; plan for 2-3x the `.7z`). All 7 kits come to about 40 GB of downloads (LOCAL appmanifests) plus extraction plus faux lightmap job folders. A: has 679 GB free (LOCAL), so space is not a constraint.
3. **Editing stock tags in place.** A later re-extract overwrites them (c20 update steps). Always save our scenarios to new paths.
4. **Infection-only MP maps.** This happens when `multiplayer_object_types.bin` is not imported in Excession (MS docs, 2.2).
5. **Wrong Scenario File Name.** It must be the tag path relative to `tags\` without extension. Excession does not validate it (MS docs).
6. **Mod folder nested too deep.** MCC and Excession look only one level under each root (MS docs).
7. **Expecting mods with EAC on.** Mods are never enumerated with EAC on (patch notes).
8. **Not restarting MCC** after subscribing or changing mods (Waypoint support).
9. **Trusting Standalone.** Its config differs from retail. AI can behave differently, and H2 MP balance patches do not apply. Always confirm in MCC (c20).
10. **Lightmapping traps.** Single-process lightmapping is broken in H3/ODST/HR; use `calc_lm_farm_local.py`. The script pins all CPUs. Running tool via Guerilla for lightmaps is broken in H3 (c20 H3/HR tool pages).
11. **No sound in Sapien/Standalone.** Copy the `fmod` folder (c20).
12. **Version drift.** The kits are frozen at 2023-07 (LOCAL build_tag) while MCC is at 2025-08 (LOCAL). MCC updates have broken mods before:
    - Official mod support broke earlier fan mods (https://www.nme.com/news/halo-the-master-chief-collection-official-mod-support-breaks-fan-mods-2979232).
    - Workshop mods stopped appearing after updates until their authors updated them (2025 discussion via search summary, UNVERIFIED).
    - DLL mods such as AlphaRing break on every patch.
    - Keep `.map` build inputs reproducible so we can rebuild quickly.
13. **Ownership.** Each kit except CE requires owning that game on Steam. The Windows Store MCC is unsupported (c20).
14. **AI in MP.** Assuming AI works in MP the way it does in campaign. H1 MP does not sync AI. H2 classic and H4 MP reportedly do not support AI actors (sources in 0.7). Test this first, per engine.
15. **ManagedBlam setup.** It needs .NET Framework 4.8 and High Entropy ASLR disabled, or it crashes (c20).
16. **Bugs go to the Joint Issue Tracker.** https://github.com/Joint-Issue-Tracker/Joint-Issue-Tracker (linked from every c20 kit page). 343 support is minimal and as-is (https://www.techradar.com/news/halo-2-and-halo-3-finally-get-official-mod-tools-on-pc).

---

## 8. What I found in the local install (read-only)

- MCC: `<Steam library>\steamapps\common\Halo The Master Chief Collection`, 136 GB, `build_tag.txt` = `2025.08.16.178512.1-Release`, Steam app 976730.
- Per-game content folders:
  - `halo1\maps` (32 files; MP maps such as bloodgulch, hangemhigh, prisoner)
  - `halo2\h2_maps_win64_dx11` (H2 classic, including MP: lockout, ascension, zanzibar, ...)
  - `groundhog\maps` (H2A MP `ca_*`)
  - `halo3\maps` (MP such as guardian, construct, riverworld)
  - `halo3odst\maps` (campaign/Firefight only)
  - `haloreach\maps` (MP, Firefight `ff*`, campaign `m*`)
  - `halo4\maps` (MP `ca_*`, `dlc*`, Spartan Ops `ff*`, campaign `m*`)
  - `game_variants`, `hopper_game_variants`, `map_variants` (H3/Reach/H4/groundhog), `halo4\spops_variants`
- User data: `%USERPROFILE%\AppData\LocalLow\MCC\`
  - `Config\ModManifest.txt` contains one line: `%APPDATA%\Vortex\halothemasterchiefcollection\mods`. **That folder does not exist** (left over from a Vortex setup). We will need to add our own root folder line; I did not change it.
  - `LocalFiles\<xuid>\HaloReach\Map\*.mvar` and `Halo2A\Map\*.mvar` hold user map variants.
  - No Workshop content folder for 976730 exists yet.
- Kits in `<Steam library>\steamapps\common\`:
  - **Installed:** `HCEEK` (1.0 GB, not yet extracted) and `HREK` (6.7 GB, not yet extracted). Both have build tag `2023.07.17.176677.1-QFE1`.
  - **Downloading:** `H2EK`, `H3EK`, `H3ODSTEK`, `H4EK` have empty folders.
  - **Queued:** `H2AMPEK`.
  - Excession (1695795) is not installed.
- Notable HREK files:
  - `Foundation.exe.config` has TagService and TagWatcher enabled.
  - `project.xml` (project "Bulgogi", display name "Omaha", alias "reach").
  - `ProjectChooser.exe`, `MegaloEdit.exe`, `bin\ManagedBlam.dll` (30.6 MB), `bin\ManagedMegalo.dll`.
  - `calc_lm_farm_local.py` (uses `tool_fast faux_farm_*`), `BuildMapsSharedOptimizedPlusSharedSounds.ps1`.
  - `bat\LevelsForModTools.txt` lists `levels\test\box\box`, `levels\ui\mainmenu\mainmenu` and the reference levels.
  - `bin\debug_menu_init.txt` (119 KB) with the AI render entries listed in 5.1.
- Notable HCEEK files: `build_all.bat` (stock build commands, platform `remastered`), `collect_tag_list.py`, `bin\debug_menu_init.txt`, `bin\!public_tags.txt` (CE MP scenarios under `levels\test\`).

---

## 9. First-day setup checklist

1. Let Steam finish H2EK, H2AMPEK, H3EK, H3ODSTEK and H4EK. Also install **Halo MCC Mod Uploader (Excession)**, app 1695795.
2. For each kit: Browse local files > run `<KIT> (Extract).bat`. Confirm `tags\` and `data\` appear. Record each `build_tag.txt`.
3. Copy `fmod` from `<MCC>\halo3`, `halo3odst` and `haloreach` into H3EK, H3ODSTEK and HREK. Check `halo4\` for an equivalent (UNVERIFIED).
4. Add the kit folders to Windows Defender exclusions.
5. Install Python 3 (for `calc_lm_farm_local.py`) and the .NET Framework 4.8 Developer Pack (for ManagedBlam).
6. Create the mod root `<project folder>\mods\` with one subfolder per engine mod (for example `reach_bots\`), each with `maps\` and `images\`.
7. In Excession: CONFIGURE > ADD FOLDER > our mods root. CREATE a test MP mod for Reach. Inspect the generated `ModInfo.json` and `multiplayer\*.json` to learn the schema.
8. With the player's OK, add our mods root as a new line in `%USERPROFILE%\AppData\LocalLow\MCC\Config\ModManifest.txt`. Back up the file first. The existing Vortex line is dead.
9. Baseline build: `tool build-cache-file "levels\multi\30_settlement\30_settlement" pc` in HREK, unmodified. Copy the `.map` to `reach_bots\maps\`, set it up in Excession (import `multiplayer_object_types.bin`), launch MCC EAC-off, and confirm it shows in Custom Games and plays Slayer.
10. Same baseline for CE: `tool build-cache-file levels\test\bloodgulch\bloodgulch remastered` (check the argument list by running `tool` with no arguments first).
11. Standalone smoke tests:
    - `halo_tag_test -windowed` with `game_variant slayer` + `map_name levels\test\bloodgulch\bloodgulch`.
    - `reach_tag_test` with `init.txt` = `game_start levels\multi\30_settlement\30_settlement`. Try `game_multiplayer slayer` first (UNVERIFIED that it works).
12. **AI-in-MP feasibility test per engine (most important):** on a renamed copy of one stock MP scenario, add one zone, about 6 firing positions, one squad with a stock character, and generate pathfinding (H3+). Then:
    - Run `ai_place <squad>` in Standalone.
    - Build and test in retail MCC under a Slayer game type.
    - Record per engine: spawns yes/no, moves yes/no, shoots players yes/no.
    - Do this for CE, H2, H2A MP, H3, Reach and H4 before deeper work.
13. Turn on debug draw (`ai_render_all_actors 1`, `ai_render_paths 1`, `ai_render_hints 1`) and save the commands into `bin\debug_menu_user_init.txt` and `editor_init.txt` for reuse.
14. Start a log of the MCC build, kit build tags, and every command that worked, so we can rebuild quickly after MCC updates.
15. Add the Game Content Usage Rules notice to the project README draft. No donations or monetization links.
