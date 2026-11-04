# Updates

What changed in each version. Download the newest one from the [Releases page](https://github.com/AyoItzKye/project-proving-grounds/releases/latest). What is still broken is on the [Known bugs](KNOWN_BUGS.md) page.

## Being tested for the next version

These are done but still being tested, so they are not in a download yet:

- **Choose which MCC to use.** The launcher gets a Game folder row: pick any copy of MCC (handy if you keep more than one), or go back to the one Steam installed. ([#1](https://github.com/AyoItzKye/project-proving-grounds/issues/1))
- **Invasion on any Reach map.** Invasion was only recognized on Spire, Boneyard and Breakpoint, so on Forge and custom maps the bots played Slayer. Now it is detected everywhere and bots respawn in each phase's zone. Carrying the bomb and core and taking the zones on Forge maps comes later (the mod can't read Forge labels yet). ([#2](https://github.com/AyoItzKye/project-proving-grounds/issues/2))
- **Walls that come and go.** Forge pieces that appear and disappear between phases or rounds are walls only while they stand, so bots stop walking into them.
- **No more getting into wrecks.** Bots can tell a destroyed vehicle from a working one, in every game except Halo: CE (where multiplayer vehicles can't be destroyed).
- **Boarding and the Plasma Launcher.** Bots board a distracted tank from the front and melee the driver, and hold a Plasma Launcher lock on a vehicle before firing.
- **LiDAR.** The LiDAR Viewer and the LiDAR Simulator are now separate windows, so the Viewer shows your LiDAR match live. A LiDAR run now also visits every gametype objective on the map (flag stands, hills, bomb and ball spawns, territories, Invasion zones and more) so the bots learn the way to each one.
- **Tools open again.** Observer, LiDAR Viewer and Paint the nav open every time, not just once.
- **Linux and Steam Deck.** A first installer for Linux and SteamOS (through Proton).

## 0.2.0 (November 2, 2026)

- The launcher and the tools open in the mod's own window instead of Microsoft Edge: no browser profile, no account sign-in, no synced extensions.
- No console windows flash while the launcher or the setup runs.
- The Data collector no longer records any keys or controller buttons, only what the game itself knows (positions, aim, guns, rounds, equipment). Exports leave out the keys 0.1.0 recorded.
- The first-time setup works when some MCC games are not installed or MCC's menu art is missing, and finds MCC in the right Steam library.
- Repair and Uninstall buttons in the launcher.
- The installer makes clear that the Windows Security exclusion is required.

## 0.1.0 (November 1, 2026)

The first release: bots in Halo: CE, Halo 2 Classic and Anniversary, Halo 3, Halo: Reach and Halo 4 custom games, plus Reach and ODST Firefight. Slayer, CTF and objective modes, vehicles, equipment and armor abilities, team directors with callouts, five difficulties, seven play styles, up to 15 bots, the launcher, the Observer, and LiDAR mapping.
