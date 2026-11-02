# Project Proving Grounds

PvP bots for **Halo: The Master Chief Collection** on PC. Bots join your offline custom games as real players on the
scoreboard: they move, aim, strafe, jump-shot, take power weapons, drive and fly vehicles, play the objective, and
talk to their team through each team's own director (map callouts). Four difficulties plus Scaling, which follows
your own results, and seven play styles.

Games: Halo: Combat Evolved, Halo 2 (Classic and Anniversary), Halo 3, Halo: Reach and Halo 4 custom games, and
Reach and ODST Firefight (bots fill your team). Up to 15 bots: the game holds 16 players.

> Offline custom games only, with Easy Anti-Cheat off. The mod refuses to run with anti-cheat on and never touches
> matchmaking, Xbox network or Steam online services.

## Install

1. Check the [system requirements](#system-requirements).
2. Download **ProjectProvingGrounds-Setup-&lt;version&gt;.exe** from this project's **Releases** page (on the right of
   the GitHub page).
3. Run it. Windows may say "Windows protected your PC": the installer is not code-signed. Click **More info**, then
   **Run anyway**.
4. The installer asks where to install (your user folder; no administrator rights needed) and offers two options:
   - a desktop shortcut;
   - **adding the mod's folder to Windows Security's exclusions** (off unless you tick it; asks for administrator
     permission). The mod loads into MCC with a small injector, the kind of program antivirus tools are suspicious
     of. Without the exclusion Windows Security may delete it; the launcher tells you if it does.
5. At the end the launcher opens and runs the **first-time setup** (a few minutes): it builds the 3D bots, emblems,
   effects and map pictures from your own copy of the game. None of the game's files ship with the mod.

Optional download on the same Releases page: **human-play-data-&lt;version&gt;.zip**, recorded matches of people
and bots for anyone who wants to study how they play ([docs/HUMAN_DATA.md](docs/HUMAN_DATA.md)).

## Play

1. Open **Project Proving Grounds** from the Start Menu and press **Play**. Steam asks how to start MCC: choose the
   option with **anti-cheat off**.
2. In MCC: **Multiplayer > Custom Multiplayer >** Halo: CE, Halo 2: Classic, Halo 2: Anniversary, Halo 3, Halo:
   Reach or Halo 4. For bot teammates against the Covenant: **Firefight > Halo: Reach Custom Firefight** or **Halo 3:
   ODST Custom Firefight**.
3. Next to START there is a **BOTS** tile (or press **B**). It opens the BOTS panel, the exact bots that join your
   next match, by team:
   - **Quick setup**: how many teams (2 to 8; Halo CE has 2), how many bots on each, difficulty and play style, then
     **Make N bots**.
   - Move a bot by dragging it to another team, with **Ctrl+Left / Right**, or right-click it > **Move to**. **+ Add
     bot** on a team, **+ Add team** for another.
   - Pick a bot to set its name, difficulty and play style. **Del** removes it. **Balance teams**, **Shuffle teams**,
     **New names**, **Difficulty for everyone**, **Remove all**.
   - **Spectate (no body)**: join with no body and fly a free camera (WASD or the left stick, mouse to look, Space up,
     Ctrl or C down, Shift fast; not in Halo 2 Anniversary yet).
   - **Settings**: each bot's profile with its 3D look, emblem and clan tag; re-roll them.
4. Pick a map and game type, then START. The bots join a few seconds after the match loads.

## Difficulty

| | Easy | Normal | Heroic | Legendary |
|---|---|---|---|---|
| Reaction | a little slower than a person | a person's | faster | fastest |
| Movement | rarely strafes, jumps only to get around | strafes often, jumps sometimes | strafes almost always, jump shots | always, jukes |
| Plan | none: wanders in Slayer, straight at the objective otherwise | the team's | the team's | the team's |
| Routes and power weapons | straight at the objective; a gun only if it sees one | some lanes, some weapons | sneaky routes, knows the spawns | hard spots, times every respawn |
| Equipment and armor abilities | never | when it should | and to bait | every trick |
| Awareness | looks where it walks | keeps known threats in view | checks flanks and radar | keeps threats in mind longest |
| Teamwork | its own way | sometimes groups up | team shots | full focus fire |
| Head shots (precision guns) | chest two shots in three | head half the time once your shield pops | nearly always | always |

Every difficulty aims with the same hands; reaction and how a bot plays make the difference.

**Scaling** gives every bot Legendary's play with hands set by one skill level that follows your results: after each
game it moves toward the level where you and the bots come out even. It shows as a percentage of a skilled player
(100%) and tops out at 1800%. The panel's **Advanced** tab locks it, shows each setting and keeps custom profiles.

## Play styles

- **Rusher**: pushes fights and hunts people down; never camps.
- **Camper**: holds power spots and defends; waits longer, crouches at its post.
- **Objective**: takes the flag, hill or ball, and skips far fights while it does.
- **Grenadier**: opens most fights with a grenade and makes enemy vehicles its job (rockets, lasers, plasma pistols,
  sticks).
- **Grudge**: goes after whoever killed it last.
- **Sniper**: hangs back and defends.
- **Flanker**: plays as an all-rounder for now (side routes come with the difficulty).

## Map the maps (LiDAR)

The bots play better on a map they have mapped: every floor, height, jump and drop. No scans ship with the mod
(each PC maps its own), and bots play unmapped maps with the map pack's height data in the meantime. Two ways:

- **LiDAR Simulator** in the launcher, no game needed: **Pick a map** (or a Forge layout the bots have played on) and
  watch the bots map it from its level data. Choose the speed (1x to 16x, or Max), pause or stop it, and turn on
  **Click spots to cover** to send bots to places first. **Every map** maps them all in turn.
- **LiDAR mode** in the BOTS panel: start any match and the bots walk the whole map while you watch. Jumps you land
  that beat walking are learned and every bot uses them.

**LiDAR Viewer** shows any map's scan in 3D. Details: [docs/GUIDE.md](docs/GUIDE.md#lidar-mapping).

## Tools

All from the launcher, each in its own window:

- **Observer**: replay recorded matches, see what every bot saw, thought, was told and did, and your own numbers next
  to the bots' (aim, reaction, fights, positioning). Import and export games to share them; names are replaced and
  Xbox ids removed in exports.
- **Data collector** (a switch in the BOTS panel): records your movement, aim and keys for the Observer. Everything
  stays on your PC.
- **LiDAR Simulator** and **LiDAR Viewer**: above.
- **Paint the nav** (advanced): mark where bots may and may not walk.

The full player's guide: [docs/GUIDE.md](docs/GUIDE.md).

## System requirements

| | Minimum | Recommended |
|---|---|---|
| Windows | 10, 64-bit | 11, 64-bit |
| Game | Halo: The Master Chief Collection on Steam, Easy Anti-Cheat off | same |
| CPU | 4 cores, one core as fast as an Intel Core i5-8400 / i7-4790K or AMD Ryzen 5 3600 | 6+ cores, one core as fast as an AMD Ryzen 5 5600X or Intel Core i5-12400 |
| Memory | 8 GB | 16 GB |
| Graphics | MCC's own minimum (DirectX 11, feature level 11.1) | MCC's recommended or better |
| Storage | about 2.5 GB beside MCC | the same on an SSD |

The bots think on one CPU core, so a fast single core matters most; fewer bots need less. How these were measured,
what to expect on each, and MCC's own per-game requirements: [docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md).

## Troubleshooting

| What you see | What to do |
|---|---|
| No BOTS tile in the lobby | MCC was started with anti-cheat on: quit it and press Play again, choosing anti-cheat off. Or MCC updated since this version of the mod: check Releases for a newer one. |
| The launcher says Windows Security removed inject.exe | Reinstall and tick the Windows Security option, or add the install folder's native\bin to the exclusions yourself. |
| Bots do not join | The brain's log is logs\brain.txt in the install folder (Open the install folder in the launcher). |
| The game stutters with many bots | Use fewer bots; see the requirements. |
| Another mod (ReShade, an ASI loader ...) | The launcher lists files from other mods that can clash and offers to start without them for one session. |

## Uninstall

Windows **Settings > Apps > Installed apps > Project Proving Grounds > Uninstall**. It removes the Windows Security
exclusion if you added one and asks whether to keep your LiDAR scans, learned map data and recorded matches.

## For developers

Building from source, the repository's layout and how to run the tests: [docs/BUILDING.md](docs/BUILDING.md). How to
contribute: [CONTRIBUTING.md](CONTRIBUTING.md). How the bots think: [docs/bot-brain](docs/bot-brain) and the research
notes in [docs/research](docs/research).

## Credits

Built by the Project Proving Grounds contributors with **Claude**, Anthropic's AI model, which wrote most of the code
and documentation together with the project's author.

- [Dear ImGui](https://github.com/ocornut/imgui) (MIT) draws the BOTS panel; [MinHook](https://github.com/TsudaKageyu/minhook)
  (BSD 2-Clause) hooks the game.
- The map tools (bsp2obj, model2obj) are a separate GPL-3.0 project built on
  [Reclaimer](https://github.com/Gravemind2401/Reclaimer) by Gravemind2401 and contributors.
- CPU single-thread ratings in the requirements: PassMark.

## License

Free to use, share and change for any noncommercial purpose under the
[PolyForm Noncommercial License 1.0.0](LICENSE.md); selling it or earning money from it is not permitted. Notices and
third-party licenses: [NOTICE.md](NOTICE.md).

Halo: The Master Chief Collection © Microsoft Corporation. Project Proving Grounds was created under Microsoft's
"[Game Content Usage Rules](https://www.xbox.com/en-US/developers/rules)" using assets from Halo: The Master Chief
Collection, and it is not endorsed by or affiliated with Microsoft.
