# 06: Blood Gulch callouts (Halo CE on MCC)

Research date: 2026-10-21. Map: `levels\test\bloodgulch`. Purpose: a named-area vocabulary for each team's AI director ("one at Red port", "flag's at Sunny").

Source keys like [HP] or [QL B5Hr 7:04] are listed in section 9 with full URLs. YouTube timestamps are approximate (start of the caption window) and caption text is machine transcription, so quotes from comms videos are approximate. Coordinates are Halo world units from the project's own extraction of the stock scenario and BSP ([LOC]), not from community sources.

## How this was researched

- Wikis: Halopedia, Halo Fandom, StrategyWiki (read through its MediaWiki API because the page returned 403), Wikipedia, Red vs. Blue wiki, Halo Stunting wiki.
- Articles and blogs: GamesRadar (Edge), durinsbane blog, Inverse, Shacknews, note.com.
- Forums: a 2004 Bungie.net CTF thread (read). Neoseeker and GameFAQs returned 403 (only search snippets used). Reddit blocks this research tool; a few comments were recovered through the Pullpush archive.
- YouTube: a 2012 Halo PC clan callout video (frames read), trick videos (descriptions), and auto-captions of 29 Halo 1 Big Team Battle (BTB) MCC matchmaking videos with team voice comms (channel Quiet Leviathan, about 2025 to 2026), plus one Halo 2 Coagulation BTB comms video. Name counts below ("17 of 29 videos") come from those captions.
- Local ground truth: `maps\bloodgulch\objects.json` and `heightmap.npz` (from the HEK `bloodgulch.scenario` and BSP), and the sky tag exported with H1EK `tool.exe export-tag-to-xml` (sun direction).
- No MLG or HCS callout sheet for Blood Gulch was found. The living callout set is the MCC Halo 1 BTB community's, and it matches the 2012 clan video and 2004 forum vocabulary.

## 1. Key findings

1. Players name the two long canyon walls by light. The north-east wall (caves, Red's teleporter exit, overshield) is the **dark side**. The south-west wall (the ridge over Red base, Blue's teleporter exit) is the **light side** or **sunny side**. This matches the sky tag sun direction (yaw 10, pitch 40) [LSR 0:44] [QL, 17 and 13 of 29 videos] [BN04] [LOC].
2. Teleporters are called **portal** or **port**. They are one-way, from each base roof to the middle. Red's exit is on the dark side next to a cave mouth. Blue's exit is on the light side [QL] [HS] [DB] [LOC].
3. Core community names: top / front / back + color, portal exit, Hamburger Hill (Big Hill), water cave, OS cave, high cave, Sunny (ridge), tree, front hill, Camp hill, Batcave [QL] [LSR].
4. The map is asymmetric. Red has the ridge on its light side (Sunny) and the hill in its back corner (Camp hill, Sniper Rock). Blue has the cave nearest its base (Batcave) and the crevice behind it (cubby). Sources disagree on which team "benefits" from the ledge and the tunnel, but they agree on the geography [HP] [HF] [WP] [GR].
5. In the stock tag, the default vehicle set is 1 Warthog and 1 Rocket Warthog per team, both behind the base [LOC] [SW].

## 2. Master table

Height: ground = field level; high = raised ledge, hill or cliff; roof = base roof; inside = under a roof or ceiling (base interior or cave).

| Callout (short form) | Also called | Where it is (landmark description) | Height | Source(s) | Confidence |
|---|---|---|---|---|---|
| Red base | Red; "Blood Gulch Outpost Number One", "Outpost 1-B" (RvB) | Bunker at the south-east end of the canyon; flag stand inside at (95.7, -159.4) | inside | [HP] [WP] [LSR 0:00] [RVB] [LOC] | High |
| Blue base | Blue; "Blood Gulch Outpost Alpha", "Outpost 1-A" (RvB) | Bunker at the north-west end; flag stand inside at (40.2, -79.1), 97.6 units from Red's flag | inside | [HP] [WP] [LSR 0:30] [RVB] [LOC] | High |
| Top red / Top blue | "top of their base", "on top of our base", "red top", roof | Base roof (z about 1.7): teleporter pad, sniper rifle, health pack, frag grenades, pistol, Banshee (PC/MCC) | roof | [QL _Hsn 2:09] [QL B5Hr 12:47] [QL JgAu 9:03] [HP] [DB] [LOC] | High |
| Front door / Back door | "front", "back entrance/exit", "out the back door" | The ground-level doorways into the flag room. Front faces the field, back faces the end wall. Which way each door faces is UNVERIFIED | ground / inside | [BN04] [QL B5Hr 2:37, 12:47] [GR] [HS] | Medium |
| Hole | "drop down the hole" | Opening in the roof over the flag room | roof | [BN04] [LOC] | Medium |
| Ramp | "sloping paths to the roof", "the opposite ramp" | Ramps up the outside of each base to the roof. Count and sides UNVERIFIED for CE | ground to roof | [GR] [QL mUix 9:22] | Medium |
| Front red / Front blue | "front of their base", "in front of our base", "red front", "front side" | Open ground on the field side of each base, out to about 12 units (front rocks) | ground | [QL _Hsn 2:05] [QL B5Hr 8:09] [QL T3Px 4:13] [LOC] | High |
| Back red / Back blue | "back of their base", "behind base", "back center", "back left / back right of their base" | Ground between each base and its end wall; default Warthog and Rocket Warthog spawns | ground | [QL, "back red" in 11 of 29 videos] [QL T3Px 8:40] [LOC] | High |
| Red tele / Blue tele | tele, teleporter, portal (entrance) | Pad on each roof, about 4 units from the flag toward mid: Red (95.6, -155.5), Blue (40.1, -82.9) | roof | [HP] [WP] [BN04] [LOC] | High |
| Red port | "red portal", "red portal exit", "red port", "their/our portal exit", "the red team's teleporter in the middle" | Exit of Red's teleporter: dark side, just Red-ward of mid at (82.8, -114.5), exit faces west, in shadow. The Water cave mouth is right behind it (east); rocket launcher 16 units south-west | ground | [QL 0JzF 6:30] [QL 8zD3 1:51] [QL j88d 6:04] [BN04] [DB] [HP] [LOC] | High |
| Blue port | "blue portal (exit)", "blue teleporter exit", "Blue Portal exit node" | Exit of Blue's teleporter: light side, Blue-ward of mid at (43.8, -126.2), exit faces east, sunlit, with a gradual cliff (Blue cliff) beside it | ground | [QL _Hsn 4:07] [QL QjsC 1:42] [HS] [BN04] [DB] [LOC] | High |
| Mid | middle, mid map, center, "no-man's land" | Open field halfway between the bases, around (67.3, -119.8) | ground | [LSR 0:42] [QL, "mid" in 12 of 29 videos] [GR] [LOC] | High |
| Camo | "middle power up", "camo middle", "center powerup" | Active camouflage at (59.0, -116.9), on the south slope of a low hump (top (61.0, -110.1), z 2.4); 7 units Blue-ward and 6 units light-ward of mid | ground | [QL B5Hr 3:01, 3:26] [QL QjsC 0:55] [HF image "centerpowerup"] [LOC] | High |
| Rockets | "middle rockets", "RL", rocket launcher | Rocket launcher on a small mound at (72.6, -126.3), 8 units Red-ward of mid; tag respawn field 90 s; the PC port added a third bush next to it | ground | [QL T3Px 6:06, 6:31] [BN04] [HP] [LOC] | High |
| Big Hill | "Hamburger Hill", "Hamburger", "Hamburg (Hill)", "BH", "the large hill next to the red team's teleporter" | Tallest hill in the field, top at (72.8, -103.6), z 4.1; dark side, just Blue-ward of mid. Red port is 15 units south-east and the Batcave bulge is to the north | high | [LSR 0:38] [HS] [HP] [QL, 17 of 29 videos: B5Hr 1:05, 8zD3 1:51, JgAu 12:22, bkT- 3:01] [QLc 9:31] | Medium-High (Hamburger = Big Hill is inferred from context) |
| Fuel rod | "fuel rod rock" | Fuel rod gun (PC/MCC only) at (63.0, -136.5): light side, 11 units Red-ward of mid, at the foot of Sunny | ground | [SW] [DB] [HF] [QL T3Px 10:36] [LOC] | High (spawn); Medium (name) |
| Dark side | dark, "dark side red/blue", "dark red", "dark corner", darkness | The north-east wall and the strip of field along it (caves, Red port, OS) | ground | [LSR 0:44] [QL, 13 of 29 videos: _Hsn 3:12, ovBt 0:52] [BN04] [HS "Dark Small Pillar"] [LOC sun] | High |
| Light side | light, "sunny side", "light side red/blue", "lightside wall", "light cliff" | The south-west wall and the strip along it (ridge over Red base, Blue port) | ground | [LSR 0:44] [QL, 17 of 29 videos] [BN04] [HS "Bright Small Pillar"] [LOC] | High |
| Water cave | water, "the cave", "their/our water cave", "front water cave" | Cave mouth right behind Red port to the east (about x 88 to 93, y -114 to -120). The floor climbs from z 1 to 3 into the cave system that leads to the OS pocket and the tunnel | inside | [QL, 8 of 29 videos: 0JzF 6:30, lzqu 7:20, B5Hr 1:05, T3Px 6:06, mUix 13:49, dreytz 10:12] [SWC] [HFH] [LOC] | Medium |
| OS cave | "OS caves", "overshield cave", "OB cave", "power up cave", "the caves" | Low pocket at the east end of the dark-side cave system: overshield at (109.1, -108.3, z 2.1) under a ceiling; flamethrower (PC/MCC) at (103.8, -109.1) | inside | [LSR 0:08] [BN04] [QL B5Hr 11:17] [QL JgAu 1:23] [QL T3Px 4:03, 6:42] [SW] [LOC] | High |
| Tunnel | tunnels, "tunnel opening", "high tunnel", "high cave" (match UNVERIFIED) | North-south tunnel at about x 96 to 100, y -96 to -112, floor z 4 to 5 under a low ceiling. It opens north into a bay at about (92, -98) and south into the OS pocket and Water cave | inside / high | [WP] [GR] [HP] [BN04] [QL 8zD3 2:43] [QL JgAu 6:49] [QL vxob 3:46] [LOC] | Low (name match); High (tunnel exists) |
| Batcave | "Batcave", "blue caves", "Blue Base Cave", "cave systems to the left of the Blue base", "tunnel blue" | Dark-side wall bulge nearest Blue base: low mouth near (63, -85); a raised cave at x 76 to 80, y -64 to -78 (z 5 to 6) with plasma grenades at (74.6, -78.3); a ledge at (70.4, -88), z 5.6, with a pistol | inside / high | [LSR 0:22] [HS] [HP] [DB] [HF images] [LOC] | Medium |
| Dark cliff / High cliff | "dark side cliff", "dark hill", "high cliff", "Hi cliff" | A sniper perch on the dark-side wall. Exact spot UNVERIFIED | high | [QL vxob 3:46, 10:16] [QL JgAu 2:12, 9:20] [QLc 1:01] | Low |
| Cliff above Blue caves | "Highest Cliff" | Top of the cliff above the blue caves; trick only (three-player Warthog stack) | high (trick) | [HS] | Medium |
| Sunny | "Sunny Ridge", "Sunnyside Ridge/Cliff", "Sunny Side (Hill)", "Sunny-Hill Cliff", "light side ridge", "our/their ridge", "the ridge", "Red Cliff", "ledge near Red Base", "the cliff overlooking red base", "red cliffs", "top Sunny" / "bottom Sunny" | Ridge on the light-side wall overlooking Red base. A path climbs from the field near (42, -145), z 2, to an overhung ledge at x 55 to 62, y -149 to -156, z about 6 (pistol, plasma grenades). A terrace then runs south to (62, -179), z 4.5. Red base is 36 units east-south-east | high | [LSR 0:50] [QL T3Px 7:00, 11:17] [QL B5Hr 4:35, 7:04] [QL _Hsn 3:20] [QL hWPE 7:21] [QL mUix 13:06] [QL Iwxm 2:48] [HP] [WP] [GR] [DB] [HF image] [LOC] | Medium-High |
| Blue cliff | "the little cliff thing on Blue", "Blue sniper cliff", "gradual cliff beside the Blue Portal exit", "light cliff" | Raised shelf on the light-side wall in Blue's half (x 20 to 39, y -100 to -124, z about 2.6), next to Blue port. A trick-only high ledge sits above it at (16, -102), z about 13 | high | [QL Iwxm 5:15] [QL hbao 0:20] [SL] [HS] [LOC] | Low (name); High (geometry) |
| Red tree / Blue tree | "the tree", "tree at red", "Red Base Tree", "Blue Base Tree" | Lone tree in front of each base. Red's dead tree is at (80.7, -149.5), 18 units from Red base toward mid and the light side. Blue's white-bark tree is at (39.1, -96.0), 17 units from Blue base toward mid | ground | [HS] [QL 0JzF 4:23, 5:15] [QL vxob 12:19] [LOC] | Medium-High |
| Front hill (Red / Blue) | "Red Base Small Hill (SH)", "Blue Base Small Hill (Blue Base SH)", "front hill", "their front hill", "Blue hill" | Low hill beside each tree: Red top at (80.0, -141.6), z 2.2; Blue top at (46.8, -95.3), z 1.6 | ground | [LSR 0:34, 0:58] [QL T3Px 2:13, 7:29] [SL] [LOC] | Medium |
| Front rock | "the rock in front of red base", "small rock near the base (there's one for each base)", "their left side rock in front of their base" | Boulders 9 to 14 units from each base. Red: (85.2, -158.8) and (85.8, -150.1). Blue: (37.9, -88.7) and (49.0, -81.4) | ground | [RD1] [RD4] [BN04] [QL T3Px 7:41] [LOC] | Medium |
| Camp hill | "'Camp' Hill", "the hill behind red base", "large hill with some rocks behind the red base", "the hill in the back", "sniper spot in the very back corner" | Hill in the back dark-side corner behind Red base. The slope covers x 106 to 129, y -169 to -187; top about (120, -183), z 6.7; drivable by Warthog | high | [LSR 1:06] [HP] [HPT] [BN04] [RD1] [HF image "redhill"] [LOC] | Medium |
| Sniper Rock | "Sniping Rock", "the rock near the red base that's pointy", "rock formation you could back up into with the banshee", "the ghost trick to get up onto the rocks" | Pointed rock formation on or next to Camp hill. Its top is reached with Warthog-gunner, Ghost or Banshee tricks | high (trick) | [SW] [HPT] [NS] [AS] [RD2] [RD3] | Medium (name); Low (exact spot) |
| Cubby | "cubbie hole", "small crevice behind the Blue base", "great sniper point behind your base", "back blue in the dark corner", hiding spot | Overhang and crevice along the back wall behind Blue base (x 14 to 55, y -50 to -65, floor z about 3). Blue's Scorpions spawn just in front of it | inside / high | [HP] [BN04] [QL ovBt 0:52] [HF images] [LOC] | Medium |

Names found but not placed (UNVERIFIED): "Big Pillar", "Hallway", "Sniper Point" [HS]; "the peg" (on the light side ridge) [QL B5Hr 7:09]; "right side bridge" [QL 0JzF 9:07, likely caption error].

## 3. Map layout facts

### 3.1 Frame and ends

- World frame: +x is "east" and +y is "north" on a top-down view. Halo has no in-game compass, so these words are only for this document.
- Blue flag: (40.24, -79.12, -0.10), at the **north-west** end. Red flag: (95.69, -159.45, -0.10), at the **south-east** end. They are 97.6 units apart; mid is at (67.97, -119.28) [LOC].
- Wikipedia and GamesRadar describe a box canyon enclosed on all sides, with a base at each end and "undulating landscape" between [WP] [GR].
- Light versus dark: the sky tag's single sun light has direction (yaw 10, pitch 40), so the sun stands over the north-east wall [LOC]. That wall's face points away from the sun and shades the ground at its foot (the dark side). The south-west wall faces the sun (the light side). This matches three things:
  - the 2004 forum ("Red: ... Your tele is in the dark", "red also has the lightside wall to snipe from") [BN04];
  - Halo Fandom screenshots (Red teleporter exit in shadow, Blue exit in sun) [HF];
  - the 2012 clan video's "DARK" and "LIGHT" labels [LSR 0:44].
  The yaw axis convention (measured from +x toward +y) is assumed; it is UNVERIFIED but consistent with all three.

### 3.2 Bases (identical structures)

- Two levels: inside (the flag room, floor z about -0.3) and the roof (z about 1.7). A hole in the roof drops into the flag room [BN04] [LOC].
- Each base has "two entrances, an open ceiling and sloping paths to the roof" [GR] [WP]. The stunting wiki says "four entrances" (it may be counting ramp tops) [HS]. The coarse heightmap hints that the ground-level openings are on the bases' east and west faces, but this is UNVERIFIED (check in game) [LOC].
- Inside: 2 shotguns, an assault rifle and a plasma rifle around the flag stand.
- Roof: teleporter pad (on the field side, about 4 units from the flag), sniper rifle, health pack, 4 frag grenades, a pistol, and a Banshee on PC/MCC [LOC] [HP] [DB].
- Stunting names for the roof crenellations: "Bright Small Pillar" and "Dark Small Pillar" [HS].
- RvB's base tour ("there's a ramp over here, there's another one on the other side ... it's got a basement") describes the Halo 2 base, not CE [RVB 1-A].

### 3.3 Teleporters

| Teleporter | Entrance (roof) | Exit | Exit faces | Exit surroundings |
|---|---|---|---|---|
| Red (id 0) | (95.58, -155.45, 1.81) | (82.83, -114.53, 0.70) | 177 deg (west) | Dark side; Water cave mouth 6 to 10 units east; Big Hill 15 units north-west; rocket launcher 15.6 units south-west; Rocket Warthog spawn beside it in all-vehicle sets |
| Blue (id 1) | (40.06, -82.92, 1.82) | (43.80, -126.23, 0.24) | -9 deg (east) | Light side; Blue cliff shelf just west; Sunny's north-west foot about 15 to 20 units south; rocket launcher 28.8 units east; Rocket Warthog spawn beside it in all-vehicle sets |

Source for the table: [LOC].

- The teleporters are one-way, from the roof to mid. Wikis say each "will transport players to the center field" [HP] [HF].
- The exits are actually on opposite walls. The blog: "Blue's teleporter sends them close to the ledge looking over red base and red's teleporter sends them close to a cave system" [DB].
- 2004 forum: "red team is the better one only because there teleporter is right next to the rocket launcher" [BN04], which the data supports.
- Blocking: "it is possible to block the teleporters (especially in Blood Gulch) with a vehicle or by simply standing on them" [TP]. In CE, a player standing on the receiver can be telefragged when someone uses the sender [TF]. BTB comms use "block their portal", "Portal's blocked", "Portal's open" and "He's opening red portal" [QL JgAu 0:01, 5:05, 6:49] [QL 0JzF 6:30].
- Exit pads give a quick vehicle getaway with the flag: "Park a Warthog/Ghost/Banshee (Halo PC and Halo: The Master Chief Collection only) at the relevant teleporter, walk into the enemy base, grab the flag, run through the teleporter and drive/fly away for a quick escape." [HP]

### 3.4 Item spawns (stock scenario, all flagged "all games")

| Item | Location | Coordinates (x, y, z) | Callout | Tag spawn field |
|---|---|---|---|---|
| Shotgun x2 per base | Inside, beside the flag | Red (97.55, -159.52), (93.52, -159.40); Blue (38.16, -79.22), (42.03, -79.22); z -0.29 | Red/Blue base | 0 |
| Assault rifle, plasma rifle | Inside | Red AR (95.57, -158.29), PR (95.57, -160.76); Blue AR (40.13, -77.84), PR (40.16, -80.35) | Red/Blue base | 0 |
| Sniper rifle x1 per base | Roof | Red (92.48, -156.41, 1.70); Blue (43.19, -82.22, 1.70) | Top red/blue | 120 |
| Health pack x1 per base | Roof | Red (98.71, -156.40); Blue (36.90, -82.29) | Top red/blue | 0 |
| Frag grenades x4 per base | Roof | Red (95.6, -157.4); Blue (40.1, -81.0) | Top | 0 |
| Pistol x1 per base | Roof | Red (95.37, -161.11); Blue (40.16, -77.70) | Top | 0 |
| Rocket launcher | Mid mound | (72.60, -126.34, 1.18) | Rockets | 90 |
| Active camouflage | Mid hump | (59.00, -116.86, 1.84) | Camo | 0 |
| Overshield | Cave pocket | (109.06, -108.28, 2.06) | OS | 0 |
| Flamethrower (PC/MCC) | Cave pocket | (103.77, -109.09, 1.75) | OS cave | 0 |
| Fuel rod gun (PC/MCC) | Light side, Red half | (62.97, -136.52, 1.96) | Fuel rod | 0 |
| Plasma grenades x4 | Sunny ledge | (62.2, -155.4, 5.9) | Sunny | 0 |
| Plasma grenades x4 | Batcave raised cave | (74.6, -78.3, 5.7) | Batcave | 0 |
| Pistol | Sunny ledge | (57.76, -150.00, 5.75) | Sunny | 0 |
| Pistol | Batcave ledge | (69.83, -88.17, 5.66) | Batcave | 0 |

Source: [LOC].

- The spawn field is in seconds, with 0 meaning the item's default (H1 tag convention, UNVERIFIED).
- A 90 s rocket cycle fits BTB talk of "the six minute Rockets, the 4 minute 30 second ones" [QL JgAu 10:35].
- Sources that place items:
  - "The sniper rifle spawns on the top of each base near the teleporter. The rocket launcher is in the middle of the map. While the shotgun spawns inside of both bases." [DB]
  - "sniper rifle (usually found on top of either bases)" [HP]
  - "The caves contain a Flamethrower and there is a Fuel Rod Gun in the center of the map" (PC/Mac) [SW]

### 3.5 Vehicle spawns (stock scenario; team 0 = Red, 1 = Blue)

All placements allow CTF, KOTH, Oddball and Slayer. Only the two "default" spawns per team are used by the Default vehicle set; the other placements fill in when a variant asks for more or other types [LOC].

| Team | Vehicle | Coordinates | Callout area |
|---|---|---|---|
| Red | Warthog (default) | (86.83, -172.54) | Red back |
| Red | Rocket Warthog (default) | (101.94, -170.44) | Red back |
| Red | Warthog | (102.31, -144.63); (64.18, -176.80, z 3.96) | Dark red; Sunny south terrace |
| Red | Rocket Warthog | (78.21, -152.91); (81.62, -116.05) | Red front (light side); at Red port |
| Red | Ghost x4 | (104.69, -149.32), (82.22, -153.99), (89.71, -170.67), (107.87, -168.08) | Around Red base |
| Red | Scorpion x3 | (97.12, -173.13), (92.91, -173.54); (112.28, -132.78) | Red back; Dark red |
| Red | Banshee | (95.60, -162.31, 1.78) | Top red |
| Blue | Warthog (default) | (46.34, -64.70) | Blue back |
| Blue | Rocket Warthog (default) | (33.63, -65.57) | Blue back |
| Blue | Warthog | (28.86, -90.76); (65.85, -70.30, z 1.69) | Light blue; Dark blue below Batcave |
| Blue | Rocket Warthog | (50.65, -87.79); (41.70, -128.66) | Blue front (dark side); at Blue port |
| Blue | Ghost x4 | (26.99, -86.83), (52.56, -90.08), (51.58, -74.86), (28.86, -67.25) | Around Blue base |
| Blue | Scorpion x3 | (42.18, -65.02), (38.04, -64.95); (24.30, -105.93, z 2.45) | Blue back by the Cubby; Blue cliff |
| Blue | Banshee | (40.17, -76.40, 1.78) | Top blue |

- This matches StrategyWiki: "In the standard Blood Gulch layout, each team has two Warthogs - one with a machine gun and one with a rocket launcher" [SW].
- Rocket Warthogs and Banshees are PC/MCC only [SW] [HF].
- MCC's matchmaking variant file `halo1\hopper_game_variants\h1_arena_ctf_bloodgulch.bin` exists in the local install. It was not parsed; check its vehicle set in game.

### 3.6 Caves, ridges and hills (measured from the heightmap)

Method: cells with a ceiling at least 2 units above the floor are caves, base interiors or overhangs; raised walkable patches are ledges and hills [LOC].

- **Dark-side cave system (north-east wall):**
  - Batcave bulge near Blue: overhangs from x 64 to 86, y -75 to -96, floor z 1.5 to 11, plus a raised cave at x 76 to 82, y -64 to -74, z about 5.8.
  - Tunnel: x 89 to 110, y -89 to -111, floor z about 3.8, ceiling about 2.4 units above.
  - Water cave: x 88 to 103, y -108 to -119, floor z 1.6 to 6.4, mouth next to Red port.
  - OS pocket: x 100 to 112, y -104 to -114, floor z 1 to 2.
- **Light-side ridge (south-west wall, Red half):** a walkable patch of 237 square units spanning x 39 to 74, y -140 to -182, z 2.2 to 6.8, with an overhung ledge at x 51 to 62, y -149 to -164 (z about 6) and a higher overhung ledge at x 56 to 60, y -170 to -183 (z about 7.5).
- **Light-side shelf (Blue half):** 166 square units spanning x 20 to 39, y -100 to -124, z 2.2 to 3.2; a small alcove at (19, -103), z 2.7; a high ledge at (16, -102), z about 13.
- **Behind Blue base:** a raised strip along the back wall (x 12 to 81, y -51 to -66, z 2 to 6) with a long overhang (the Cubby) at x 13 to 55, y -50 to -65.
- **Behind Red base:** Camp hill (x 106 to 129, y -169 to -187, z up to 7); a thin crevice along the back wall (x 71 to 96, y -179 to -183, z about 2.3); a high shelf (x 98 to 112, y -181 to -190, z about 13, trick height).
- **Field hills:** Big Hill (72.8, -103.6) z 4.1; Red front hill (80.0, -141.6) z 2.2; Blue front hill (46.8, -95.3) z 1.6; camo hump (61.0, -110.1) z 2.4; rocket mound (72.5, -126.6) z 1.2.
- Players note the hills are big: "The hills in Blood Gulch are very tall. You can hide multiple Scorpion tanks between the hills." [RD5]

### 3.7 KOTH hills and oddball spawns (useful anchors)

KOTH hill ids in the tag and the callout each sits in [LOC]:

| Hill id | Center (x, y, z) | Callout |
|---|---|---|
| 0 | (67.1, -119.8, 0.2) | Mid |
| 1 | (70.2, -88.0, 5.6) | Batcave ledge |
| 4 | (62.0, -179.2, 4.5) | Sunny terrace (south) |
| 5 | Red roof ring | Top red |
| 6 | Blue roof ring | Top blue |
| 7 | (60.8, -150.9, 6.2) | Top Sunny ledge |
| 9 | (96.9, -95.3, 4.3) | Tunnel north mouth |
| 11 | (120.0, -183.2, 6.7) | Camp hill |
| 12 | (99.8, -111.6, 4.2) | Tunnel by the OS |
| 15 | (68.9, -95.0, 1.7) | Big Hill north foot / Batcave mouth |

Oddball spawns [LOC]: (47.0, -111.4) light side between Blue tree and Blue port; (73.4, -103.3, z 4.1) top of Big Hill; (92.9, -118.5, z 3.3) inside the Water cave; (95.5, -152.5) Red front; (120.0, -183.4) Camp hill; (62.6, -167.8) Sunny terrace; (45.3, -151.1) Sunny's north-west end; (40.2, -86.6) Blue front; (76.3, -76.9, z 5.7) Batcave.

### 3.8 Xbox versus PC/MCC

- The PC/Mac version adds a Flamethrower (caves), a Fuel Rod Gun (center), and optional Rocket Warthogs and a Banshee at each base [SW]. The Halo Fandom infobox marks these as "PC, iMac, and Xbox One only" (Xbox One = MCC) [HF].
- Gearbox's PC port added a third bush next to the rocket launcher spawn, fixed a floating bush, and smoothed "a few small, steep inclines near blue base's teleporter exit" [HP].

### 3.9 Schematic (generated from the heightmap; not to scale)

Blue is top-left and Red is bottom-right. `#` = cliff or steep wall, `:` = raised ground (z 1.5 or more), `.` = low ground. Labels are placed at each callout anchor; Rport/Bport = Red/Blue port, Rtree/Btree = trees, Rback/Bback = behind the bases.

```
              ######
        ####:::########     ####
        ##::::::::::::#############
    ####::Cubby.:::::::::###::::###
    #:::::..........:::::.:::::::##
  ##:::::...Bback.........::::::::::#
 ##::::.....................:::::::::#
 ##:::........................:::::::##
 #:::::.......##.:#...........:::#::
 ##::::.......BLUE:.........Bat cave
 ###::::......#:#:#.Dark blue.:#
  ###:::.....................###:       ##
 #Light blue................################:
###:#:::...................########:::::####:::
#####:::::.....Btree.......:##.::::::::::::::#
#######::::::.................::::::::::::Tunnel
 ######:::::::..............Big Hill:::.::##    #
  #####:::::::::..........:::::::::::....#      #:OS
    ##Blue cliff:........:::::::::::....:##  :#: ::
      #######::::........:::::::...Rport:####:: ::
        ######:::.......Camo............Water########
           ###::.............Mid........:::::#############
          ####:.Bport....................:::::::##########
          #:##:..............Rockets...........:::::..####
          #####.............::.........................####
            ####........Fuel rod................:......######
            ####::........::::....::::.......Dark red.#####
            ####::::..............:::.................####
            ####:::::::::::.......Rtree...............###
            ######:::::##:##..........................###
               #    ####Sunny:........................###
                      #######::...........#:::#......#####
                       #####:::...........:RED:......#####
                        ###::::...........#::##.....#######
                         ##:::Light red..............########
                          #:::...............Rback...:########
                          #:::::.....................::::::###
                         #:::::::....................::::::::#
                         ##::########::::##########:Camp hill#
                          #####             ##:######:#::####
                                             ##############
```

## 4. Area notes and evidence

### Light side, dark side

- 2012 Halo PC clan video "Bloodgulch Call-Outs" (lsrclan): the camera flies the map with on-screen callouts. The order is Red Base, OS Caves, Batcave, Blue Base, Blue Base Small Hill, Big Hill, Mid, then "DARK" and "LIGHT" written on the two halves of the canyon, then Sunny-Hill Cliff, Red Base Small Hill, "Camp" Hill [LSR].
- MCC BTB KOTH comms: "Front red. Front red." then "Top red. Top red." then "Sniping top blue." then "Light side red. Dark red." then "Dark side red. One near Sunnyside Cliff." [QL _Hsn 2:05 to 3:20].
- 2004: "red also has the lightside wall to snipe from and view the whole map", "use darkness to enter blue base unseen" [BN04].

### Portals

- "Portaling for rockets ... Portal exit." [QL B5Hr 0:07]
- "Water cave. He's opening red portal. Ghost red portal." [QL 0JzF 6:30]
- "Sniping blue portal exit." [QL _Hsn 4:07]
- The stunting wiki uses "Portal" and "Blue Portal exit node" [HS].
- 2004 forum: "Red: You've got a RL near tele. Your tele is in the dark, surrounded by hills all around. Blue's is MUCH more exposed." [BN04]

### Big Hill / Hamburger Hill

- "Once you get better at sniping, try sniping on the large hill next to the red team's teleporter in the middle of the map." [HP]
- 2012 clan label "BIG HILL (BH)" [LSR 0:38]. Stunting caption: "Ghost Shroom on the Big Hill" [HS].
- BTB comms name it in 17 of 29 videos:
  - "There's a ghost going to our water cave. No, he's behind Hamburg now. He's not cave yet. Going to beat him to the OS." [QL B5Hr 1:05]
  - "They're over hamburger hill on the little lip. You'll be fine at red port, but they're coming over hamburger hill slightly to the left." [QL 8zD3 1:51]
  - "they're pushing Hamburger Hill full force ... they're all pushing up mid map" [QL JgAu 12:22]
- The Halo 2 Coagulation BTB comms use "Hamburger Hill" too [QLc 9:31].
- Placement is inferred: next to Red port, between the Water cave and mid. This fits only the Big Hill.

### Water cave, OS cave, tunnel, high cave

- "go through the caves and exit with the overshield" [BN04]. Clan label "OS CAVES" [LSR 0:08].
- BTB comms:
  - "ghost is going water cave right now he's going for OS" [QL lzqu 7:20]
  - "coming out of power up cave he has OS" [QL JgAu 1:23]
  - "there's a ghost in the ... overshield cave" [QL T3Px 4:03]
  - "in OB cave ... got the OB cave guy" [QL T3Px 6:42]
  - "Outside water cave on the rock." [QL QjsC 2:15]
- The Blood Gulch BSP has no water shader; its shader list has no water entry [LOC: `bloodgulch.scenario_structure_bsp` strings]. The name probably carries over from the remakes:
  - Coagulation: "The caves are most easily accessed from the red base's teleporter ... Inside the caves is a small stream of water ... The caves eventually connect to a shadowy cliff which lead to the left of the blue base" [SWC].
  - Hemorrhage: "the entrance to the cave with water in it. The other exit to that cave leads to the exit of Red Base's teleporter" [HFH].
  - The same BTB players use "water cave" on Coagulation [QLc 5:27]. Whether MCC's Anniversary visuals add water to the CE cave is UNVERIFIED.
- Tunnels:
  - "Blue team ... has more immediate access to a tunnel system running along the sides the map, but needs to watch for ambushes from the caves, which can disgorge a Red Team to their door." [GR]
  - "blue: you've got easy tunnel networks to get to red", "You can use the tunnel opening to annoy red ppl, esp. those teleporting." [BN04]
- "High cave" (3 videos) and "high tunnel" are heard but not placed:
  - [QL JgAu 6:49]
  - "sniper in their high tunnel" [QL 8zD3 2:43]
  - "He's going to be in high cave" [QL vxob 3:46]

### Batcave (Blue's cave)

- Clan label "BATCAVE" over a cave interior, followed by a view of Blue base from the dark-side wall [LSR 0:22 to 0:28].
- "Have both Warthogs go through the cave systems to the left of the Blue base" [HP]. "There are cave systems to the left if you're at blue base and to the right if you're at red base." [DB]
- Stunting wiki: "Drive a Hog into the Blue Base Cave" (the Cliff Above Blue Caves stunt) [HS].

### Sunny (the ridge over Red base)

- "Blue Team has the advantage of utilizing a ledge near Red Base which is an ideal spot for sniping" [HP]. "A ridge overlooks the Red Base" [GR]. "Red team having access to a ridge" [WP].
- "There is also a ledge that looks over red base to its left. This is a good sniping spot for spawn killing." [DB]
- Clan label "SUNNY-HILL CLIFF" on the sandy path up the light-side cliff toward Red base [LSR 0:50].
- BTB comms:
  - "two on their Sunny, their Sunny Ridge ... sniper on their Sunny Ridge ... hiding behind the ledge" [QL T3Px 7:00]
  - "Sunnyside Ridge. Below Sunny. He's down low on Sunny." [QL hWPE 7:21]
  - "top sunny and bottom sunny" [QL mUix 13:06]
  - "Ghost on light side ridge." [QL B5Hr 7:04]
  - [QL Iwxm 2:48]

### Camp hill and Sniper Rock

- "If you are in the Red Team, there is a large hill with some rocks for defense behind the red base. One tactic is driving a rocket hog up there and keep shooting rockets at the blue base's roof." [HP]
- "You need to drive a warthog up the hill in the back, and then snipe while your up there. You also have a rock to hide behind" [HPT].
- Neoseeker (search snippet only): "look for the rock near the red base thats pointy and use the gunner to get in it" [NS].
- Banshee method: "go up to the side of the rock, back up ... get out once you feel you can make it onto the rock" [AS]. StrategyWiki: "send one guy to take Sniper Rock" [SW].
- 2004, advice to Blue: "use their own snniper spot in the very back cornor to annoy them" [BN04].
- Clan label "'CAMP' HILL" on a shaded hill with a pointed rock against the back wall [LSR 1:06]. Halo Fandom's "redhill" screenshot shows the same hill behind Red base's vehicle spawns [HF].
- Reddit: [RD1]

### Trees, front hills, front rocks

- Stunting wiki: "Red Base Tree" (nick "Tree"), "Blue Base Tree" [HS].
- BTB comms: "There's a couple at the tree right there." [QL 0JzF 4:23]; "Behind the tree at red." [QL 0JzF 5:15]; "Drop sniper by the tree. See that right side of our base." [QL vxob 12:19]
- Clan labels: "BLUE BASE SMALL HILL (BLUE BASE SH)" and "RED BASE SMALL HILL (SH)", each with its tree in frame [LSR 0:34, 0:58].
- 2004 Warthog trick: "Charge towards a small rock near the base (there's one for each base)" [BN04].

### Cubby (behind Blue base)

- "You can hide in a small crevice behind the Blue base with a sniper rifle to take out enemies from behind." [HP]
- 2004: "You have a great sniper poinit behind your base", "go inside the cubbie hole in ghost behind their base" [BN04]. BTB: "tanks back blue in the dark corner" [QL ovBt 0:52].

## 5. Remakes and Red vs. Blue

| Source | Names | Notes |
|---|---|---|
| Coagulation (Halo 2) official Territories | Hill, Red Base, Blue Base, Rocky Area, Cave, Forest Area | Territory names per [HPC]. Mapping to Blood Gulch spots UNVERIFIED except bases, Hill (Big Hill) and Cave |
| Coagulation community | "Sniper Ledge" (alcove above blue base), "hills near the Overshield", Rocks, Caves, Center | [HPC] [SWC]. In H2 the overshield is at the Rocks and the camo is in the water caves, so power-up callouts do not carry over |
| Coagulation BTB comms (2026) | dark side red/blue, front red, high cliff, high cave, water cave, Hamburger Hill, Sunny side cliff, light side rocks, blue portal exit, top blue | Same vocabulary as Halo 1 BTB [QLc 0:13 to 9:31] |
| Hemorrhage (Reach, Forge World) | HUD location names are Forge World regions ("The Canyon" and others), not sub-areas | [HPFW]. Layout notes: water cave right of Red base whose other exit is Red's teleporter exit; "sniping cliff" left of Red base leading to Blue's teleporter; large open hill behind Red base [HFH]; "the ridge leading to Red Base", "Entrance of the cave" [HPH] |
| Bloodline (Halo 2 Anniversary in MCC) | Firebase Blue, Firebase Red, Landslide, Cliff Path, Cavern, Ridge, Tunnel, Hill, River Bed, UNSC Training Bunker | In-game location names [HPB]. Man cannons replace teleporters; a central bunker is added. Mapping UNVERIFIED beyond bases and bunker |
| Halo Infinite community remake | "Coagulation" (a recreation of the original canyon; "blood" is word-filtered) | [HW] [PG]. No callout list found |
| Halo 5 | Basin (inspired by Blood Gulch and Valhalla); "Blue vs Red 2003" Grifball court | [HF]. No Blood Gulch callouts found |
| Halo Wars | "Blood Gulch" RTS map | Not applicable |
| Red vs. Blue | Blood Gulch Outpost Alpha / Outpost 1-A (Blue base); Blood Gulch Outpost Number One / Outpost 1-B (Red base); Underground Caves (fictional cavern under the canyon); nicknames "Useless Backwater Canyon", "Box Canyon in the Middle of Nowhere" | [RVB]. Show names, not gameplay callouts |

## 6. Callout conventions that apply

- **Color and our/their.**
  - BTB players mix both styles: "top red", "red port", "dark side blue", and also "our ridge", "their portal exit", "their water cave" [QL].
  - "Symmetrical maps are usually color coded ... Color, in fact, remains one of the most common types of adjectives used in callouts." [INV]
  - A pro-callout guide uses "our base or the blue base ... top blue ... our flag" [SHY].
- **Top / bottom / high / low.**
  - BTB: "top red", "top of their base", "top sunny" / "bottom sunny", "below Sunny", "high cave", "high cliff", "Red Cliff lower" [QL _Hsn, mUix, hWPE, JgAu, Iwxm].
  - Newer Halo comms number stacked levels (P1, P2, P3) [SHY].
- **Light / dark instead of left / right.** Left and right flip with the speaker's facing. The guide warns: "if you're going to use the left and right calls, just try to remember the context" [SHY]. Blood Gulch's light/dark split is absolute, which is why the community uses it.
- **Health calls** (counts across 29 Halo 1 BTB videos [QL]):
  - "one shot" 62 times, "he's one" 16, "weak" 18, "absolute" 7, "one bar" 2, "half shield" 1, "no shield" 1, "cracked" 0.
  - "Absolute is essentially one shot, but maybe even more than just his shields gone"; [SHY].
  - Reach death-marker style: "One-Shot" or "One" at my X; "Snipe Down" means the sniper is on the ground; "Sniper" without "down" means the enemy holds it [SHK].
- **Flag status:**
  - "pull" (taking the flag, 15 uses), "relay" (handing it off, 10 uses) [QL].
  - "flag's down our front door", "flag's down in water cave", "Flag at our portal exit", "Going out the back door with flag", [QL JgAu 12:16] [QL mUix 13:49] [QL B5Hr].
  - Announcer lines heard in captions: "Red team has the flag", "Blue team flag return", "red team score" [QL].
- **Power items and timers:** "Rockets down", "middle rockets", "OS" / "OB", "Camo's still up", "sniper down in our cave", "They have sniper on top of their base", "six minute Rockets" [QL B5Hr, T3Px, JgAu].
- **Portal control:** "block the portal" (7 uses), "block their portal" (6), "Portal's open" (4), "Portal's blocked" (3) [QL].
- **Discipline words:** "quiet" (18), "on me" (12), "heard" (10), "clear" (10), "behind you" (9) [QL].
- **Why short names:**
  - "The callouts that stick tend to be short, immediately recognizable, and, if possible, similar to previous Halo games. The best ones require the minimum amount of brain processing power to reference and recall." Ensslin calls this the "principle of least effort" [INV].
  - Players clip long names: "Hamburger" or "Hamburg" for Hamburger Hill, "Sunny", "port", "OS" / "OB" [QL].
  - Order and brevity: "1_Where, 2_How many, 3_What weapon they have, 4_Who it is"; "prefixes are unnecessary"; call out "as soon as possible" [NOTE]. BTB comms usually lead with the count: "two on our ridge", "three on Hamburger Hill" [QL].

## 7. Conflicts and unverified items

1. **Ledge and tunnel advantage.** Halopedia: Blue uses the ledge near Red base and Red uses the tunnel [HP]. Halo Fandom says the reverse [HF]. Wikipedia and GamesRadar: Red has the ridge, Blue has the tunnel system [WP] [GR]. The geography is not in dispute: ridge on the light side by Red, caves on the dark side starting by Blue.
2. **Overshield location.** The blog says "The overshield and active camo both spawn near the rocket launcher" [DB]. The tag has the overshield in the dark-side cave, 41 units from the rockets [LOC], which matches [BN04] [LSR] [QL]. Use the tag.
3. **Sniper spawn.** A Halopedia gallery caption reads "The cliff overlooking red base, with the sniper rifle spawn" [HP]. The tag and two text sources put the snipers on the roofs [LOC] [HP] [DB]; the screenshot probably shows the roof spawn from the cliff.
4. **Teleporter destination.** Wikis say "center field" [HP] [HF]; the exits are actually on opposite walls near mid [DB] [LOC].
5. **Base entrances.** "Two entrances" [GR] [WP] versus "four entrances" [HS]. Door bearings are UNVERIFIED.
6. **"Water cave" with no water** in the CE BSP; the name is probably from Coagulation/Hemorrhage (section 4).
7. **"High cave", "high cliff", "dark cliff", "the peg", "Big Pillar", "Hallway", "Sniper Point":** heard or listed but not placed.
8. **"Red hill" is ambiguous.** Halo Fandom's "redhill" image is the hill behind Red base (Camp hill) [HF], while the clan's "Red Base Small Hill" is the hill in front [LSR]. Do not use "Red hill".
9. **Secret ledge above a cave:** the video description says the cave "closest to the blue base", the narration says "closest to the red base" [AC]. Trick-only; ignore for bots.
10. **Sun direction:** the yaw convention is assumed (section 3.1).
11. **"Hamburger Hill = Big Hill"** and **"Water cave = the cave at Red port"** are inferred from comms context plus geometry, not stated by any source.
12. **One transcript can be read as putting "Sunny" by Blue** [QL mUix 7:38]. Most uses and the 2012 clan video place it at Red [LSR] [QL T3Px] [QL _Hsn].

## 8. Recommended callout set

Design rules:
- One or two syllables. Color prefix wherever a place exists on both sides.
- Community names where they exist, so human teammates recognize them.
- Light/dark instead of left/right. No two names that sound alike: say "Camp hill" in full so it is not confused with "Camo".

Anchors are proposals from the measured data [LOC]; check each in game.

### 8.1 Places

| Callout | Covers | Anchor (x, y, z) | Basis |
|---|---|---|---|
| Red top / Blue top | Roof: tele pad, sniper, health | (95.7, -159.4, 1.7) / (40.2, -79.1, 1.7) | "top red" [QL] |
| Red base / Blue base | Inside: flag room, inner doorways | (95.7, -159.4, -0.2) / (40.2, -79.1, -0.2) | [HP] [QL] |
| Red front / Blue front | Field-side apron, front door, front rocks | (88.9, -149.6, 0) / (47.1, -89.0, 0) | "front red" [QL] |
| Red back / Blue back | Behind the base, back door, default hogs and tanks | (102.5, -169.3, 0.2) / (33.4, -69.2, 0.5) | "back red" [QL] |
| Red tree / Blue tree | Tree plus front hill | (80.5, -146.0, 1) / (42.5, -95.5, 1) | [HS] [QL] [LSR] |
| Red port / Blue port | Teleporter exit | (82.8, -114.5, 0.7) / (43.8, -126.2, 0.2) | [QL] [HS] |
| Light red / Light blue | Light-side ground near that base | (75, -166, 1) / (24, -90, 1) | "light side red" [QL] |
| Dark red / Dark blue | Dark-side ground near that base | (106, -138, 0.5) / (57, -80, 0.5) | "dark red", "dark side blue" [QL] |
| Mid | Center field | (67.3, -119.8, 0.2) | [LSR] [QL] |
| Camo | Camo spawn and its hump | (59.0, -116.9, 1.8) | "middle power up" [QL] |
| Rockets | Rocket launcher mound | (72.6, -126.3, 1.2) | "middle rockets" [QL] |
| Big Hill | Tallest field hill, next to Red port. "Hamburger" is the spoken BTB variant | (72.8, -103.6, 4.1) | [LSR] [HS] [HP] [QL] |
| Water | Cave mouth behind Red port | (92, -117, 2) | "water cave" [QL] |
| OS | Overshield pocket (and flamethrower) | (109.1, -108.3, 2.1) | "OS caves" [LSR] [QL] |
| Tunnel | Upper tunnel and its north mouth into the bay | (97.5, -101.0, 4.5) | [WP] [GR] [BN04] |
| Batcave | Blue's dark-side cave and ledge | (72, -80, 5) | [LSR] |
| Sunny | Ridge over Red base. Say "top Sunny" for the ledge above z 4.5 and "low Sunny" for the approach | (60, -152, 6) | [LSR] [QL] |
| Fuel rod | Fuel rod spawn area | (63.0, -136.5, 2.0) | [QL] [SW] |
| Blue cliff | Light-side shelf by Blue port | (30, -110, 2.6) | [QL] [SL] [HS] |
| Camp hill | Hill in Red's back corner, including Sniper Rock | (119, -179, 5) | [LSR] [HP] [BN04] |
| Cubby | Crevice and overhang behind Blue base | (31, -57, 3) | [HP] [BN04] |

That is 29 names (8 per side plus 13 shared). For coarse or uncertain fixes, the director can fall back to "light side", "dark side", "Red side" or "Blue side". This fits the fuzzy-callout design in `docs\BRAIN-DESIGN.md`.

### 8.2 Status words

- **Count:** one, two, three, "a bunch".
- **Health:** "one shot", "weak", "full".
- **Items:** "Rockets up / taken / down at X", "OS up / taken", "Camo up / taken", "snipe down at X", "has rockets / sniper / OS / camo", "Rockets in 30".
- **Vehicles:** ghost, hog, rocket hog, tank, Banshee.
- **Flag:** "flag pulled", "flag's down at X", "carrier X going Y", "relay", "flag's back".
- **Portal:** "port blocked", "port open".
- **Team:** "on me", "push", "fall back", "clear", "behind you".

### 8.3 Rendering rules for the director

- Pattern: `[count] [place][, status][, weapon]`. Examples: "Two Big Hill", "One shot, Water", "Flag's at Sunny", "Carrier Red port, going mid", "Rockets taken", "Port blocked", "Snipe down, Blue top".
- Store canonical names with colors. When speaking, sometimes swap to "our/their" ("their port", "our top"), as BTB players do; the swap rate is a design choice, not sourced.
- Never say left or right. Use light/dark for sides and top/low for height.

### 8.4 Notes for `brain\maps.py`

The current first-pass anchors differ from the measured map:
- "Red cliffs" (100, -128) lies on the dark side near the Water cave, not on the ridge; the ridge (Sunny) is at about (60, -152).
- "Mid hill" (62, -110) is the camo hump; the Big Hill is at (72.8, -103.6).
- "Blue cliffs" (36, -108) is roughly the Blue cliff shelf.

Suggest replacing them with the 8.1 anchors. Add two z rules from `heightmap.npz`: roof versus inside at the bases, and cave (ceiling present) versus hill. These are proposals only; no code was changed.

## 9. Sources

Wikis and articles
- [HP] Halopedia, Blood Gulch: https://www.halopedia.org/Blood_Gulch
- [HPT] Halopedia, Talk:Blood Gulch ("Sniping Rock" section): https://www.halopedia.org/Talk:Blood_Gulch
- [HF] Halo Fandom, Blood Gulch (infobox, strategies, gallery image names such as "Bgulch redhill", "Bgulch centerpowerup", "Bgulch tunnelblue", "Bgulch bluehidingspot"): https://halo.fandom.com/wiki/Blood_Gulch
- [SW] StrategyWiki, Halo: Combat Evolved/Blood Gulch (read via https://strategywiki.org/w/api.php): https://strategywiki.org/wiki/Halo:_Combat_Evolved/Blood_Gulch
- [WP] Wikipedia, Blood Gulch: https://en.wikipedia.org/wiki/Blood_Gulch
- [GR] GamesRadar (Edge), Revisiting Blood Gulch: https://www.gamesradar.com/blood-gulch-ins-and-outs-halos-agenda-setting-arena/
- [DB] durinsbane blog, Halo Combat Evolved Maps: Blood Gulch (2020): https://durinsbane.home.blog/2020/04/17/halo-combat-evolved-maps-blood-gulch/
- [HS] Halo Stunting wiki (Halo PC stunting community): https://halostunting.fandom.com/wiki/Cliff_Above_Blue_Caves_(Blood_Gulch), https://halostunting.fandom.com/wiki/Floating_Ghost_Platform_(Blood_Gulch), https://halostunting.fandom.com/wiki/Hog_Door_(Blood_Gulch), https://halostunting.fandom.com/wiki/Ghost_Shroom_(Blood_Gulch), https://halostunting.fandom.com/wiki/Red_Base_Tree_(Blood_Gulch), https://halostunting.fandom.com/wiki/Blue_Base_Tree_(Blood_Gulch), https://halostunting.fandom.com/wiki/Portal_(Blood_Gulch), https://halostunting.fandom.com/wiki/Big_Pillar_(Blood_Gulch), https://halostunting.fandom.com/wiki/Hallway_(Blood_Gulch), https://halostunting.fandom.com/wiki/Sniper_Point_(Blood_Gulch), https://halostunting.fandom.com/wiki/Bright_Small_Pillar_(Blood_Gulch), https://halostunting.fandom.com/wiki/Dark_Small_Pillar_(Blood_Gulch)
- [TP] Halopedia, Teleporter: https://www.halopedia.org/Teleporter
- [TF] Halopedia, Telefragging: https://www.halopedia.org/Telefragging
- [HPC] Halopedia, Coagulation: https://www.halopedia.org/Coagulation
- [SWC] StrategyWiki, Halo 2/Coagulation: https://strategywiki.org/wiki/Halo_2/Coagulation
- [HPH] Halopedia, Hemorrhage: https://www.halopedia.org/Hemorrhage
- [HFH] Halo Fandom, Forge World/Hemorrhage: https://halo.fandom.com/wiki/Forge_World/Hemorrhage
- [HPFW] Halopedia, Forge World (HUD callouts section): https://www.halopedia.org/Forge_World
- [HPB] Halopedia, Bloodline: https://www.halopedia.org/Bloodline
- [HW] Halo Waypoint, Forge Features 1: https://www.halowaypoint.com/news/forge-features-1
- [PG] Prima Games, Blood Gulch in Halo Infinite Forge: https://primagames.com/news/blood-gulch-in-halo-infinite-forge
- [RVB] Red vs. Blue wiki: https://rvb.fandom.com/wiki/Blood_Gulch, https://rvb.fandom.com/wiki/Outpost_1-A, https://rvb.fandom.com/wiki/Outpost_1-B, https://rvb.fandom.com/wiki/Underground_Caves
- [INV] Inverse, How did the language of Halo Infinite get so sterile: https://www.inverse.com/input/gaming/how-did-the-language-of-halo-infinite-get-so-sterile
- [SHK] Shacknews, A beginner's guide to Halo: https://www.shacknews.com/article/65493/a-beginners-guide-to-halo
- [NOTE] note.com, HALO Talk Episode 2 "Talk About Callouts": https://note.com/xxteroteroxx/n/n8b62c36d7f85?hl=en

Forums and Reddit
- [BN04] Bungie.net forum, "CTF blue team Blood Gulch Strategys" (June 2004): https://www.bungie.net/en/Forums/Post/9770?page=0&path=0&showBanned=0&sort=1
- [NS] Neoseeker forum, "Where is this Sniper's Rock in Blood Gulch?" (403; search snippet only): https://www.neoseeker.com/forums/1532/t397333-this-snipers-rock-in-blood-gulch/
- [RD1] https://www.reddit.com/r/halo/comments/bm86fq/got_to_play_halo_with_my_dad_for_the_first_time/emv0a6m/
- [RD2] https://www.reddit.com/r/halo/comments/x5mr2t/what_is_your_favorite_halo_ce_map/in46d7b/
- [RD3] https://www.reddit.com/r/gaming/comments/pval3t/if_you_know_you_know/he9oux0/
- [RD4] https://www.reddit.com/r/halo/comments/sryjho/finishing_up_this_painting_blood_gulch_oil_on/hwvnjqk/
- [RD5] https://www.reddit.com/r/halo/comments/tchuhf/valhalla_or_blood_gulch/i0f0t4w/
  (Reddit comments were retrieved through the Pullpush archive API, not read on reddit.com.)

YouTube (descriptions, frames, or auto-captions)
- [LSR] lsrclan, "Bloodgulch Call-Outs" (2012-12-18, Halo PC, frames read): https://www.youtube.com/watch?v=XeeXO-hrUWY
- [SL] Slatchum, "Halo: CE - Blood Gulch tricks" (2020; chapters "Blue sniper cliff climb w/ghost", "Blue hill hog bump", "Red rock hog bump over red base"): https://www.youtube.com/watch?v=kIAHtJJqvuI
- [AS] As7raios, "Blood Gulch - Getting onto the Sniper Rock" (2014): https://www.youtube.com/watch?v=Gn3ULMzzowI
- [AC] appcookie, "Halo 1 Trick (episode 36): Secret Ledge above cave in BG" (2008): https://www.youtube.com/watch?v=GADtLoBZUfQ
- [SHY] Shyway, "The ULTIMATE Pro Halo Call-out Guide" (2022, Halo Infinite; auto-captions read as machine-translated): https://www.youtube.com/watch?v=lTSFhqGMeao
- [QLc] Quiet Leviathan, "Halo 2 BTB - Team Slayer on Coagulation (Full Comms)": https://www.youtube.com/watch?v=yjEAkt8GIdg
- [QL] Quiet Leviathan, Halo 1 BTB on Blood Gulch, MCC matchmaking with comms. Cited as QL plus a 4-character ID prefix and mm:ss; add `&t=<seconds>s` to the URL to jump:
  - B5Hr https://www.youtube.com/watch?v=B5HrhZFgPe4 (CTF, Full Comms)
  - T3Px https://www.youtube.com/watch?v=T3PxTYL2450 (CTF 7v8, Full Comms)
  - JgAu https://www.youtube.com/watch?v=JgAuOUvZE_c (CTF, Partial Comms)
  - vxob https://www.youtube.com/watch?v=vxob2g7o7cA (CTF, Full Comms)
  - mUix https://www.youtube.com/watch?v=mUix-7DPchE (CTF 2v8, Partial Comms)
  - ywd2 https://www.youtube.com/watch?v=ywd21ULdXEU (CTF, Full Comms)
  - cA6x https://www.youtube.com/watch?v=cA6xenA-11Q (CTF, Partial Comms)
  - _Hsn https://www.youtube.com/watch?v=_HsnFtTlbFg (KotH, Full Comms)
  - 0JzF https://www.youtube.com/watch?v=0JzFR9zH1pI (KotH 5v8, Full Comms)
  - 8zD3 https://www.youtube.com/watch?v=8zD3xewmGGE (KotH, Full Comms)
  - QjsC https://www.youtube.com/watch?v=QjsCaMpWBM8 (KotH 5v7, Full Comms)
  - Iwxm https://www.youtube.com/watch?v=IwxmcAR4Gbg (KotH 6v6, both teams' comms)
  - 6OrB https://www.youtube.com/watch?v=6OrBUCgxDD4 (KotH)
  - pFZF https://www.youtube.com/watch?v=pFZFy8fEink (KotH)
  - 8jjt https://www.youtube.com/watch?v=8jjt_xrKgEc (KotH, Partial)
  - lzqu https://www.youtube.com/watch?v=lzquVYCA7fA (Team Slayer 4v6)
  - hWPE https://www.youtube.com/watch?v=hWPEX19C0Us (Team Slayer 5v3)
  - bkT- https://www.youtube.com/watch?v=bkT-YR0Rsu4 (Team Slayer 7v7)
  - dreytz https://www.youtube.com/watch?v=dreytz3eVPA (Team Slayer 3v6)
  - ovBt https://www.youtube.com/watch?v=ovBt6qOx_Ek (Team Slayer)
  - ZNi9 https://www.youtube.com/watch?v=ZNi9mftrjE4 (Team Slayer)
  - j88d https://www.youtube.com/watch?v=j88dtxEtnzE (Team Slayer)
  - sIMf https://www.youtube.com/watch?v=sIMf0F59zfk (Team Slayer)
  - qrbd https://www.youtube.com/watch?v=qrbdYxf_0A0 (Team Slayer)
  - hbao https://www.youtube.com/watch?v=hbaorqqe3cQ (Team Slayer, Partial)
  - MNt8 https://www.youtube.com/watch?v=MNt8QigP_Kg (Team Slayer, Partial)
  - EKsV https://www.youtube.com/watch?v=EKsVEGBYEJ8 (Team Slayer, Partial)
  - oEYW https://www.youtube.com/watch?v=oEYW_MOGD5I (Team Slayer, Partial)
  - FtaO https://www.youtube.com/watch?v=FtaOo-Ur_pY (Team Slayer, Limited)

Local data
- [LOC] `<project folder>\maps\bloodgulch\objects.json` (netgame flags, equipment, vehicles, scenery from the HEK `bloodgulch.scenario`), `maps\bloodgulch\heightmap.npz` and `maps\bloodgulch\source\bloodgulch.scenario.xml` (vehicle default flags).
- [LOC] `<Steam library>\steamapps\common\HCEEK\tags\levels\test\bloodgulch\bloodgulch.sky`, exported with `tool.exe export-tag-to-xml` (sun lens flare direction 10, 40).
- [LOC] `bloodgulch.scenario_structure_bsp` shader strings (no water shader).
