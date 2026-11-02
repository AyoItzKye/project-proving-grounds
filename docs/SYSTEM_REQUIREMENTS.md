# System requirements

Project Proving Grounds runs next to Halo: The Master Chief Collection, so a PC needs what MCC needs for the games you
play, plus a little more for the bots. The bots' brain is a Python program that thinks for every bot 30 times a second
(a "pass") on one CPU core, so the speed of a single core matters most.

## Summary

| | Minimum | Recommended |
|---|---|---|
| Windows | Windows 10, 64-bit | Windows 11, 64-bit |
| Game | Halo: The Master Chief Collection on Steam, started with Easy Anti-Cheat off (offline custom games only) | same |
| CPU | 4 cores; one core about as fast as an Intel Core i5-8400, Core i7-4790K or AMD Ryzen 5 3600 (PassMark single-thread rating about 2,350 or more), and at least MCC's own minimum for the games you play | 6 cores or more; one core about as fast as an AMD Ryzen 5 5600X or Intel Core i5-12400 (single-thread rating about 3,300 or more) |
| Memory | 8 GB | 16 GB |
| Graphics | MCC's own minimum: DirectX 11 with feature level 11.1; NVIDIA GeForce GTS 450 or AMD Radeon HD 6850 (Halo 3 and Halo 4: GTS 450 or Radeon R7 graphics) | MCC's recommended: NVIDIA GeForce GTX 560 Ti or AMD Radeon R7 360, or better |
| Storage | the MCC games you play, plus about 2.5 GB for the mod | the same on an SSD |
| What to expect with 15 bots | about 20 passes a second on small and medium maps, about 15 on the largest | about 30 passes a second on small and medium maps, about 20 on the largest |

Fewer bots need less: the brain's work grows with the number of bots, so 8 bots take about half of what 15 do. On a
slower PC the bots keep their real speed (turning, aiming and moving are timed by the clock, not by the pass), they just
react in coarser steps. Below about 7 passes a second they start to lose time.

The graphics card does no extra work for the bots: the BOTS panel and its 3D bot view are drawn inside MCC's own frame
and are small next to the game.

## Where these numbers come from

Measured on the development PC (AMD Ryzen 7 9800X3D, PassMark single-thread rating 4,420; 32 GB; NVIDIA GeForce RTX 5080;
Windows 11), November 2026:

| Measurement | Result |
|---|---|
| Live matches, 9 bots (Reach: Forge World, Breakpoint, Powerhouse and others) | 29.4 passes a second (34 ms apart, the loop's own pacing) |
| Live match, 15 bots on Last Resort (Halo 3, medium) | 29.4 passes a second, 95% of passes within 41 ms |
| Live match, 15 bots on Boneyard (Reach, large) | 27 passes a second (37 ms apart), 95% within 77 ms |
| The brain alone in the simulator, 15 Legendary bots | 10 ms a pass on Blood Gulch, 13 on Construct and Adrift, 19 on Spire |
| The brain's memory | about 0.1 to 0.3 GB with a map loaded; its route caches then grow to a share of the PC's memory (below) |

The expectations for other CPUs are estimates: the live figures above scaled by each CPU's PassMark single-thread
rating (Ryzen 5 5600X 3,366; Core i5-12400 3,467; Ryzen 5 3600 2,557; Core i7-4790K 2,463; Core i5-8400 2,364). They
were not measured on those CPUs.

MCC's own requirements are Microsoft's, per game, on Halo Waypoint ("PC Hardware Specifications for Halo: The Master
Chief Collection"): Halo: CE, Halo 2: Anniversary and Halo: Reach list an AMD Phenom II X4 960T or Intel i3550; Halo 3
and Halo 4 an Intel Core i7-975 or AMD A12-9800 APU; all of them DirectX 11 with feature level 11.1. Only Halo: Reach
has recommended specs (AMD FX-4100 or Intel i7-870, AMD Radeon R7 360 or NVIDIA GTX 560 Ti). Microsoft lists no memory
figure. Those minimum CPUs are slower than the bots' minimum above: MCC runs on them, but the bots get fewer passes a
second than the table expects (run fewer bots there).

## Memory

The bots' route caches (distances from every spot on the map to each place a bot is heading) use at most a fifth of
the PC's memory together, 1.5 GB each at most: 8 GB PCs give them 1.6 GB, 16 GB PCs 3.2 GB, 32 GB PCs and up 6 GB. A full
cache recomputes a route when it is needed again, which costs no measurable time (Spire, 15 bots: 19.0 ms a pass
with an 8 GB PC's budget against 18.7 ms unlimited).

## Storage

| Part | Size |
|---|---|
| The mod (code, map knowledge, docs) | 26 MB |
| The map pack (height maps, top-down pictures, Forge shapes) | 490 MB |
| The map tools (bsp2obj, model2obj and their .NET runtime) | 144 MB |
| Python and its packages (numpy, scipy, Pillow), bundled | about 190 MB |
| The 3D bots of the profile view, built on install from your game files | about 470 MB |
| LiDAR scans and what the bots learn, per map you map | about 3 MB a map (360 MB for all 124 maps) |
| Recorded matches (the Observer keeps the last 10) | about 30 MB a match, 40 MB with the Data collector on |
| Total | about 2.1 GB with every map mapped; 2.5 GB leaves room |
