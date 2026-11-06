# Updates

What changed in each version. Download the newest one from the [Releases page](https://github.com/AyoItzKye/project-proving-grounds/releases/latest). Everything still broken is on the [Known bugs](KNOWN_BUGS.md) page, and every game, mode and vehicle is rated on the [bot status sheet](BOT_STATUS.pdf).

Click a version to see what changed since the one before it.

<details open>
<summary><b>0.2.2 s165</b> (November 6, 2026): Invasion rework, vehicles fixed, Firefight bots panel, launcher updates</summary>

### New
- **Update check in the launcher**: it checks GitHub for a new version (at most every 6 hours, or with **Check**), shows when it last checked, and tells you when one is out. **Auto-update** is off unless you turn it on; nothing is ever installed without it or the **Update** button.
- **Firefight**: the BOTS tile and panel now show in the Reach and ODST Firefight lobbies, with up to 3 bots (Firefight holds 4 players). Teammates follow you, and while you're down they hold a safe spot nearby instead of running into the open.
- **Observer**: the game list shows games only. A game with bug reports has a flag, and a **Bug reports** section lists each report with its time; click one to jump to that moment.
- **A real player's guide**: **Read the guide** in the launcher opens a searchable guide in the mod's own window.
- **The launcher** in the Proving Grounds art's colours, with the sign as the app icon.
- **Flight heights from the map**: aircraft pick their attack and travel heights from the ground under them; painting airspace is optional.

### Fixed
- **Invasion**:
  - Attackers take and hold the territories from inside them, and shoot on the way in instead of stopping to fight far from the objective.
  - The core carrier no longer drops the core by meleeing, and a dropped core is picked up again at once.
  - Attackers climb the Spire to the core.
  - Bots no longer get stuck on Boneyard's stairs, plank and walkway ([#4](https://github.com/AyoItzKye/project-proving-grounds/issues/4)) or in the rock on the way to Spire's B.
  - Both teams play with the same brain (team 2 was always thinking last).
- **Vehicles**:
  - Bots take empty Banshees.
  - A bot mans your Warthog's gun when you drive.
  - Falcon pilots fetch gunners and stay under the map's kill ceiling.
  - Aircraft climb over the Spire instead of flying into its side.
- **Halo 4 Flood**: survivors shoot the Flood instead of hiding behind the hardlight shield. The shield comes out only as a short block when reloading (then a melee), when swarmed, or when cornered.
- **Jetpacks**: bots let them refill before flying again.
- **Paint the nav**: works in an installed copy, and opens a map straight away.
- **LiDAR Viewer**: shows maps you mapped in the Simulator. Its controls are grouped, and a map's Forge layouts are in one drop-down.
- **LiDAR Simulator**: maps are no longer cut short at Max speed ([#8](https://github.com/AyoItzKye/project-proving-grounds/issues/8)), and bots start inside Forge creations ([#10](https://github.com/AyoItzKye/project-proving-grounds/issues/10)).
- **Windows**: windows the launcher opens now come to the front instead of opening behind it.
- **In-game UI**: the BOTS tile and the **Report bot bug** button are placed correctly at every resolution, not just ultrawide.

### Known problems in this version
- **Invasion** is still not fully right: on Boneyard the first attack loses most rounds, and custom Forge Invasion maps aren't played ([#2](https://github.com/AyoItzKye/project-proving-grounds/issues/2)).
- The [Known bugs](KNOWN_BUGS.md) page lists every open report from GitHub with its status.

</details>

<details>
<summary><b>0.2.1</b> (November 2026): melee weapons, Infection and Flood, wrecks, LiDAR, Theater, a new launcher</summary>

### New
- **Energy sword and gravity hammer**: bots lunge the moment the reticle turns red and get kills with them in Halo 3, Reach and Halo 4. Sword fights: Normal bots and up follow a clash with a quick melee.
- **Infection and Flood**: survivors hold rooms with few entrances in small groups; zombies hunt, wait at corners, then rally and charge together. Halo 4 Flood is read as Flood and Flood use their thrusters; survivors dodge lunges. ([#3](https://github.com/AyoItzKye/project-proving-grounds/issues/3))
- **Choose which MCC to use**: the launcher's Game folder setting lets you pick any copy of MCC or go back to the one Steam installed. ([#1](https://github.com/AyoItzKye/project-proving-grounds/issues/1))
- **Boarding**: bots board a distracted enemy Scorpion or Wraith from the front and beat the driver out.
- **Windows and fences**: bots see enemies through glass and fences, shoot through fences, railings and glass that breaks, and walk around bulletproof glass instead of firing into it.
- **Kill zones from the maps**: bots stay out of each map's kill zones and "return to the battlefield" areas, on foot, in vehicles and in the air.
- **Race and Regicide**: played as their own modes (Halo: CE and Reach Race, Halo 4 Regicide) instead of as Slayer.
- **LiDAR**: the Viewer and the Simulator are separate windows (the Viewer shows your LiDAR match live). A LiDAR run visits every gametype objective on the map, rides lifts and man cannons, and a director sends bots to the parts of the map not mapped yet.
- **Observer**: keeps your newest 5 games (a Keep game button saves one for good) and trims long recordings to the last 15 minutes, both changeable in Recording settings. It also lists games recorded by another copy of the mod.
- **A redesigned launcher**: status at a glance, a big Play button, a tools grid, everything fits the window.
- **Linux and Steam Deck**: a first installer for Linux and SteamOS (through Proton), as its own download.

### Fixed
- Bots no longer get into destroyed vehicles in Halo 2 Anniversary, Halo 3, Reach and Halo 4.
- Halo 4 Flood's first round no longer ends right away.
- Infection zombies no longer walk off to pick up guns, ride Mongooses or hide from far-off shotguns; Flood no longer spawn with DMRs; sides no longer mix up after the first round.
- Reach Theater films of bot matches play again (films are now kept in one place for every copy of the mod).
- Observer, LiDAR Viewer and Paint the nav open every time, not just once.
- The Observer's game list is no longer empty when the games were recorded by the other copy of the mod.
- Bots stop walking into the same ledge or wall over and over (a route that dropped through a ledge's own floor; Halo 4's height read).
- Bots no longer drop into pits they cannot climb out of (Construct's lift wells) when following LiDAR routes.
- Banshee and other aircraft pilots fire through their attack runs instead of pulling up at every building.
- King of the Hill in Halo 3 keeps the hill when you stand in it (the game hides the hill marker from you there).

### Changed
- Legendary bots walk in on their target instead of strafing in place (Heroic half the time); sniper rifles and launchers are unchanged.
- Infection and Flood no longer give bots custom loadouts.

### Known problems in this version
- **Reach Invasion does not play properly**: bots do not push the objectives, get stuck on Boneyard's stairs ([#4](https://github.com/AyoItzKye/project-proving-grounds/issues/4)), and custom Forge Invasion maps are not played ([#2](https://github.com/AyoItzKye/project-proving-grounds/issues/2)). Being fixed first.
- Bots cannot use the gate terminal on High Ground ([#5](https://github.com/AyoItzKye/project-proving-grounds/issues/5)).
- Theater with bots still only works in Reach.
- The Linux and Steam Deck installer has not been tried on a real Steam Deck yet.
- The full list is on the [Known bugs](KNOWN_BUGS.md) page.

</details>

<details>
<summary><b>0.2.0</b> (November 2, 2026): own app window, no key logging, setup fixes</summary>

### New
- Repair and Uninstall buttons in the launcher.

### Fixed
- The first-time setup works when some MCC games are not installed or MCC's menu art is missing, and finds MCC in the right Steam library.
- No console windows flash while the launcher or the setup runs.

### Changed
- The launcher and the tools open in the mod's own window instead of Microsoft Edge: no browser profile, no account sign-in, no synced extensions.
- The Data collector no longer records any keys or controller buttons, only what the game itself knows (positions, aim, guns, rounds, equipment). Exports leave out the keys 0.1.0 recorded.
- The installer makes clear that the Windows Security exclusion is required.

</details>

<details>
<summary><b>0.1.0</b> (November 1, 2026): the first release</summary>

Bots in Halo: CE, Halo 2 Classic and Anniversary, Halo 3, Halo: Reach and Halo 4 custom games, plus Reach and ODST Firefight. Slayer, CTF and objective modes, vehicles, equipment and armor abilities, team directors with callouts, five difficulties, seven play styles, up to 15 bots, the launcher, the Observer, and LiDAR mapping.

</details>
