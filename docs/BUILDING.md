# Building from source

For people who want to change the bots. Players only need the installer from the Releases page (README).

## What you need

| | Needed for | Where to get it |
|---|---|---|
| Windows 10 or 11, 64-bit | everything | |
| Halo: The Master Chief Collection (Steam) | playing, the first-time setup, the map tools | Steam |
| Git | the source | git-scm.com |
| Python 3.14 (64-bit) with `requirements.txt` | the bots' brain and every tool | python.org; then `python -m pip install -r requirements.txt` |
| Visual Studio 2022 Build Tools with "Desktop development with C++" (MSVC) | the mod DLL and the injector (`native/build.bat`) | visualstudio.microsoft.com |
| The map tools (bsp2obj, model2obj) | the 3D bots, the effect sprites, rebuilding map data | the separate Proving Grounds Map Tools project (GPL-3.0): clone it beside this one and run its `build.bat` (needs the .NET 10 SDK), or copy a release's `tools\map_tools` folder |
| Inno Setup 6 | building the installer | jrsoftware.org, or `winget install JRSoftware.InnoSetup` |
| Halo's official mod kits (HREK, H3EK, H3ODSTEK, H4EK, H2AMPEK, H2EK, HCEEK) | only to rebuild map data from the games' tags | Steam (free, "Tools") |
| Ghidra 12 and a JDK 21; `requirements-dev.txt` (capstone, pefile) | only for reverse engineering MCC's DLLs (`ghidra/scripts`, tools such as `tools/disasm.py`) | ghidra-sre.org, adoptium.net |

`python -I brain/paths.py` shows what this PC has: Steam's libraries, MCC, each mod kit, Visual Studio and the map
tools. Every path is found by itself; environment variables override each one (`HB_MCC`, `HB_KIT_<NAME>`,
`HB_VCVARS`, `HB_MAP_TOOLS`, `HB_STEAM_COMMON`).

## First build

```
git clone <this repository>
cd project-proving-grounds
python -m pip install -r requirements.txt
native\build.bat
python -I tools\setup.py
python -I tools\launcher.py
```

1. The **map pack** (height maps, top-down pictures, glass masks, Forge shapes: about 490 MB) is a separate download
   on the Releases page, too big for the repository. Unzip it over the project folder (it fills `maps\`). Without it
   the bots still run, but on fewer maps and with less map knowledge.
2. `native\build.bat [tag]` builds `native\bin\botcore.dll` (or `botcore_<tag>.dll`: a new name while MCC still holds
   an older one) and `inject.exe`. The launcher loads the newest `botcore*.dll`.
3. `tools\setup.py` builds what comes from your own game files (bot profiles, map pictures, logos, 3D bots, effects,
   emblems) and switches match recording on; `--status` shows what is there.
4. `tools\launcher.py` opens the launcher. With a developer copy it uses the Python on your PATH; an installed copy
   uses its bundled `python\python.exe`.

## Tests

`python -I tools\run_tests.py` runs every `tools\test_*.py` in its own process and prints one line each; a filter
runs some (`python -I tools\run_tests.py scaling`). Each test also runs on its own (`python -I tools\test_scaling.py`)
and states what it checks at its top. Tests that need data each PC makes itself (LiDAR scans, learned files, recorded
matches, built binaries) print `SKIP` and what would enable them. The C++ panel has its own checks in `native\tests`.

## The repository

| Folder | What |
|---|---|
| `brain` | the bots' brain in Python: decisions, aim, movement, navigation, team directors, difficulty and Scaling, each game's details |
| `native` | the mod DLL (C++): hooks into each game, the shared memory with the brain, the BOTS panel (Dear ImGui), the injector; `third_party` holds Dear ImGui and MinHook |
| `tools` | the launcher, the first-time setup, the tools (Observer, LiDAR, export), the live loop (`live_bots.py`, `play.py`), map builders and every test |
| `maps` | each map's knowledge (callouts, positions, objects, features), per game tables (`_inputs`, `_looks`, `_vehicles`), the human reference (`_human`); scans and learned data are made on each PC |
| `docs` | the player's guide, these notes, system requirements, the bot-brain design (`bot-brain`) and research notes (`research`) |
| `installer` | the Inno Setup script and the icon |
| `ghidra/scripts` | Ghidra scripts used to find the games' functions and data |

How it fits together: the launcher starts MCC and injects `botcore.dll`. The DLL draws the BOTS panel and, when a
match starts, starts the brain (`tools/play.py`, which runs `tools/live_bots.py`). The brain reads the game through
shared memory and the game's own data 30 times a second, decides for every bot (`brain/bot.py`, the team directors in
`brain/director.py`) and writes each bot's controls back, which the DLL feeds to the game.

## Building a release

1. Set the version in `VERSION`.
2. `python -I tools\build_installer.py` stages the public copy (`tools/make_release.py`, which also scans it for
   private data and stops on any), the built DLL and injector, the map tools and an embeddable Python with the
   packages, and compiles `installer\ProjectProvingGrounds.iss` into
   `..\installer_build\ProjectProvingGrounds-Setup-<version>.exe`.
3. `python -I tools\make_release.py` writes the public copy and the map pack on their own (for the repository and the
   map pack download).
4. On GitHub: Releases > Draft a new release, a tag such as `v0.1.0`, attach the Setup file, the map pack zip and the
   human play data zip.

## Code style

Match the code around you. Comments say what the code does and why, in plain words; numbers carry their units and
where they came from (a measurement, a game's tag, a recorded match). Every change that touches logic comes with a
test that fails without it.
