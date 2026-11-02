# Halo MCC – Original Player Customization by Game

2026 · @Kye

(/ .md. The
machine-readable version for code is maps/_looks/original_content.json; brain/looks.py reads it.)

## How to use this list

Everything below is customization that existed in each game's original release (Halo 2: Anniversary = its 2014 MCC launch), so it is safe for a "true to the game" bot mode. Anything not listed here is MCC-added and belongs in the "MCC content" mode.

Tags used on items:

- **\[Default\]** – unlocked from the start in the original game.
- **\[Unlock\]** – earned in normal play (achievements, rank, skulls, credits).
- **\[Promo/DLC\]** – original content gated behind a pre-order, special edition, DLC pack or website tie-in. Original, but rare in real lobbies.
- **\[Staff\]** – original content limited to Bungie employees or hand-picked players. Original, but almost nobody had it.

Suggested modes: *Strict original* = Default + Unlock; *Original + exclusives* = adds Promo/DLC and Staff. When a bot rolls an item that the current mode excludes, fall back to the game's default model, the same way MCC shows default Mark VI when cosmetics are turned off.

## Halo: Combat Evolved

Original CE has exactly one customization option: a single armor color on a fixed Spartan model ([Halopedia](<https://www.halopedia.org/Armor_customization_(Halo:_Combat_Evolved)>)).

| Category | Original content |
| --- | --- |
| Species | Spartan only (no Elites in multiplayer) |
| Armor model | One fixed Mark V model; no helmets, shoulders or other pieces |
| Armor color | One color for the whole suit; no secondary or tertiary color. Undersuit and parts of the bracers/greaves always stay black |
| Color list (18, all \[Default\]) | Black, Red, Blue, Gray, Yellow, Green, Pink, Purple, Cyan, Cobalt, Orange, Teal, Sage, Brown, Tan, Maroon, Salmon, White |
| Visor | Default visor only |
| Emblems | None (introduced in Halo 2) |
| Weapon / vehicle skins | None |

MCC briefly used different names for five colors (Grey, Light Blue, Lapis Lazuli, Forest Green, Cherry) before reverting to the names above; match on the color, not the label.

## Halo 2 (Classic)

Original Halo 2 adds a species choice, a second armor color and emblems, but still no armor pieces ([Halopedia: Emblems](https://www.halopedia.org/Emblems)).

| Category | Original content |
| --- | --- |
| Species | Spartan or Elite \[Default\]; one fixed model each, no Elite ranks/variants to pick |
| Armor model | Fixed; no helmets, shoulders or other pieces |
| Primary color | 18 colors \[Default\] |
| Secondary color | Same 18 colors \[Default\] |
| Color names (from memory, verify) | White, Steel, Red, Orange, Gold, Olive, Green, Sage, Cyan, Teal, Cobalt, Blue, Violet, Purple, Pink, Crimson, Brown, Tan |
| Emblem | 64 foregrounds, 32 backgrounds; foreground primary + secondary color from the 18 colors. The emblem background takes its two colors from the armor's primary and secondary colors |
| Emblem placement | Shown on both shoulders and the back in game |
| Visor | Default only |
| Weapon / vehicle skins | None |

The emblem counts (64 / 32 / 18 colors) are sourced; the color names are not, so confirm them against the in-game list before hard-coding.

## Halo 2: Anniversary (2014 MCC launch)

H2A multiplayer was built for MCC, so "original" here means the 2014 launch: six pre-made armor sets, all free, with no piece mixing ([Halopedia](<https://www.halopedia.org/Armor_customization_(Halo_2:_Anniversary)>)).

| Category | Original (launch) content |
| --- | --- |
| Species | Spartan or Elite \[Default\] |
| Spartan armor sets | Mark VI, Centurion, Hoplite – all \[Default\] |
| Elite armor sets | Combat, Outrider, Invader – all \[Default\] |
| Piece mixing | None at launch: each set is worn whole (helmet, chest, shoulders/arms, forearms, legs all from one set) |
| Armor colors | Primary and secondary (exact palette not confirmed) |
| Weapon skins | H2A has weapon skins; which ones shipped at launch is not confirmed |

For a strict launch look, give each bot one complete set; mixing pieces across sets is a later MCC feature (Series 3, 2020).

## Halo 3

Original Halo 3 has 17 armor sets (12 Spartan, 5 Elite) split into helmet, chest and shoulders, plus 30 colors ([Halopedia](<https://www.halopedia.org/Armor_customization_(Halo_3)>)). Several Spartan sets are helmet-only or chest-only; a slot with no piece in that set uses Mark VI.

**Spartan armor (original unlock per piece)**

| Set | Helmet | Chest | Shoulders |
| --- | --- | --- | --- |
| Mark VI | Default | Default | Default |
| CQB | Default | Default | Default |
| EVA | Unlock: campaign complete on Normal+ | Unlock: beat Tsavo Highway on Normal+ | Unlock: beat The Ark on Normal+ |
| EOD | Unlock: campaign complete on Legendary | Unlock: Tsavo Highway on Legendary | Unlock: The Ark on Legendary |
| Hayabusa | Unlock: all 13 skulls | Unlock: 5 skulls | Unlock: 9 skulls |
| Scout | Unlock: *Used Car Salesman* | Unlock: *Too Close to the Sun* | Unlock: *Mongoose Mowdown* |
| Security | Unlock: 1,000 Gamerscore | – (helmet adds a small chest antenna) | Unlock: 750 Gamerscore |
| Mark V | Unlock: rank Sergeant (*UNSC Spartan*) | – | – |
| ODST | Unlock: rank Private (*Spartan Graduate*) | – | – |
| Rogue | Unlock: rank Lieutenant (*Spartan Officer*) | – | – |
| Katana | – | Unlock: 49 achievements or 1,000 Gamerscore (Hayabusa chest with sword) | – |
| Recon | Staff: granted by Bungie (later via Vidmaster challenges) | same | same |
| Bungie ("Flaming Head") | – | Staff: Bungie employees only (EOD-style chest + flaming head effect) | – |

**Elite armor (original unlock per piece)**

| Set | Helmet | Chest | Shoulders |
| --- | --- | --- | --- |
| Combat | Default | Default | Default |
| Assault | Default | Default | Default |
| Flight | Unlock: campaign complete on Heroic+ | Unlock: Tsavo Highway on Heroic+ | Unlock: The Ark on Heroic+ |
| Ascetic | Unlock: *Steppin' Razor* | Unlock: *Up Close and Personal* | Unlock: *Overkill* |
| Commando | Unlock: *Overkill* | Unlock: *Triple Kill* | Unlock: *Killing Frenzy* (auto-unlocked for everyone in Title Update 1, so effectively Default) |

**Other original options**

| Category | Original content |
| --- | --- |
| Species | Spartan or Elite \[Default\] |
| Piece mixing | Free mix of helmet / chest / shoulders within a species |
| Colors | 30-color palette for primary, secondary and detail colors |
| Emblem | Foreground, background, and their colors (emblem shown on the right shoulder) |
| Service Tag | 4-character tag |
| Not in original | Visor colors, forearms, legs, techsuits, back accessories, weapon/vehicle skins |

MCC unlocks all of the above for everyone, including Recon and the Bungie flaming head, so in "strict original" mode you may want to keep Recon and Flaming Head rare or off.

## Halo 3: ODST (Firefight)

Original ODST customization is a choice of seven Firefight characters, each with a fixed look, plus two colors, an emblem and a helmet toggle ([Halopedia](<https://www.halopedia.org/Armor_customization_(Halo_3:_ODST)>)).

| Character | Original unlock | Helmet on/off |
| --- | --- | --- |
| The Rookie | Default | Helmet always on (cannot remove) |
| Romeo | Unlock: *NMPD HQ* achievement | Toggle |
| Dutch | Unlock: *Uplift Reserve* achievement | Toggle |
| Mickey | Unlock: *Kizingo Boulevard* achievement | Toggle |
| Buck | Unlock: *Tayari Plaza* achievement | Toggle |
| Dare | Unlock: *Campaign Complete: Legendary* achievement | Toggle (her secondary color colors her whole helmet) |
| Sgt. Avery Johnson | Promo/DLC: pre-order bonus | No helmet (cannot wear one) |

| Category | Original content |
| --- | --- |
| Primary color | Colors the chestplate |
| Secondary color | Colors the shoulder pad and helmet decals |
| Tertiary color | None (that slot is used for skin tone) |
| Emblem | Shown large on the chestplate |
| Service Tag | 4-character tag |
| Helmet toggle | Free toggle at any time; no gameplay effect |

Not original (MCC-only): Injured Romeo, Bug-splattered Buck, and helmetless versions as separate unlock items.

## Halo: Reach

Original Reach has ten Spartan slots bought with credits (cR) and gated by rank, plus whole-set Elite armor chosen by rank ([2011 Halopedia armory snapshot](https://halopedia.org/Special:MobileDiff/933428); slot checks from [Halopedia chest list](<https://www.halopedia.org/Armor_customization_(Halo:_Reach)/Chest>) and [Assault attachments](https://www.halopedia.org/Armor_accessories/Assault)). Costs below are the original Xbox 360 prices; everything not marked Promo/Staff was obtainable in normal play.

**Helmets and helmet attachments** (each helmet = base + two attachment variants)

| Helmet | Original unlock | Attachments (original unlock) |
| --- | --- | --- |
| Mark V \[B\] | Default | UA (Recruit, 750 cR); UA/HUL (Corporal, 1,500 cR) |
| CQC | Default | CBRN (Recruit, 750 cR); UA/HUL (Corporal, 1,500 cR) |
| ODST | Recruit, 2,000 cR | UA/CNM (Corporal, 1,000 cR); CBRN/HUL (Sergeant, 500 cR) |
| HAZOP | Recruit, 7,000 cR | CBRN/HUL (Sergeant, 2,000 cR); CNM-I (Captain, 1,000 cR) |
| EOD | Sergeant, 15,000 cR | CNM (Sergeant, 5,000 cR); UA/HUL (Sergeant, 3,000 cR) |
| Operator | Sergeant, 7,000 cR | UA/HUL (Sergeant, 2,000 cR); CNM (Sergeant, 1,000 cR) |
| Air Assault | Warrant Officer, 15,000 cR | UA/CNM (WO, 7,500 cR); FC-I (WO, 5,000 cR) |
| Grenadier | Warrant Officer, 25,000 cR | UA (WO, 5,000 cR); UA/FC (WO, 2,000 cR) |
| Scout | Captain, 40,000 cR | HU/RS (Captain, 5,000 cR); CBRN/CNM (Captain, 5,000 cR) |
| EVA | Major, 30,000 cR | CNM (Major, 7,000 cR); UA/HUL\[3\] (Lt. Colonel, 15,000 cR) |
| JFO | Lt. Colonel, 60,000 cR | HUL-I (Lt. Col, 20,000 cR); UA (Lt. Col, 10,000 cR) |
| Mark V | Lt. Colonel, 130,000 cR | CNM (Lt. Col, 10,000 cR); UA (Lt. Col, 15,000 cR) |
| Commando | Commander, 85,000 cR | CBRN/CNM (Commander, 40,000 cR); UA/FC-I\[2\] (Commander, 40,000 cR) |
| EVA\[C\] | Commander, 120,000 cR (needs EVA) | CNM (Commander, 25,000 cR); UA/HUL\[3\] (Commander, 140,000 cR) |
| Pilot | Commander, 90,000 cR | HUL\[3\] (Commander, 25,000 cR); UA/HUL\[3\] (Commander, 55,000 cR); Haunted (Inheritor rank, all helmets bought) |
| Recon | Colonel, 100,000 cR | HUL (Colonel, 75,000 cR); UA/HUL(3) \[Promo: pre-order / release-day code\] |
| GUNGNIR | Brigadier, 250,000 cR | HU/RS (Brigadier, 125,000 cR); CBRN (Mythic, 400,000 cR) |
| Mark VI | Brigadier, 300,000 cR | FC-I\[2\] (Brigadier, 75,000 cR); UA/HUL-I (Brigadier, 75,000 cR) |
| Security | General, 250,000 cR | UA/HUL (General, 200,000 cR); CBRN/CNM (Legend, 200,000 cR) |
| CQB | Promo: free Halo Waypoint download | HU/RS/CNM; UA/HUL (same Waypoint download) |
| Military Police | Promo: free Halo Waypoint download | CBRN/HU/RS; HU/RS/CNM (same Waypoint download) |

**Shoulders** (left and right picked separately)

| Shoulder | Original unlock |
| --- | --- |
| Default (Mark V \[B\]) | Default |
| FJ/PARA | Recruit, 250 cR |
| HAZOP | Recruit, 500 cR |
| JFO | Recruit, 1,000 cR |
| Recon | Corporal, 1,500 cR |
| EVA | 3,000 cR |
| Jump Jet | 5,000 cR |
| GUNGNIR | 8,000 cR |
| CQC | Lt. Colonel, 20,000 cR |
| ODST | Captain, 25,000 cR |
| Operator | Commander, 28,000 cR |
| Commando | Commander, 40,000 cR |
| Grenadier | Colonel, 65,000 cR |
| Security | Left: General, 70,000 cR / Right: General, 275,000 cR |
| Sniper | Left: Brigadier, 80,000 cR / Right: Brigadier, 75,000 cR |
| UA/Multi-Threat (listed under "Mk V" in the 2011 table; verify name) | Left: Brigadier, 100,000 cR / Right: Brigadier, 80,000 cR |

**Chest**

| Chest | Original unlock |
| --- | --- |
| Default | Default |
| UA/Counterassault | 600 cR |
| HP/HALO | Recruit, 600 cR |
| UA/ODST | Warrant Officer, 750 cR |
| Tactical/LRP | Recruit, 1,000 cR |
| Tactical/Recon | Warrant Officer, 1,500 cR |
| UA/Multi-Threat | 2,000 cR (see note) |
| Collar/Grenadier | Captain, 4,000 cR |
| Tactical/Patrol | Major, 4,000 cR |
| HP/Parafoil | Colonel, 8,000 cR |
| Collar/Breacher | Lt. Colonel, 8,000 cR |
| UA/Base Security | Major, 12,000 cR (see note) |
| Assault/Commando | Colonel, 12,000 cR |
| Assault/Sapper | Commander, 14,000 cR |
| Collar/Grenadier \[UA\] | General, 40,000 cR |
| Collar/Breacher \[R\] | Lt. Colonel, 75,000 cR (needs Collar/Breacher) |
| HP/Parafoil \[R\] | Brigadier, 175,000 cR (needs HP/Parafoil) |
| Assault/Sapper \[R\] | General, 250,000 cR (needs Assault/Sapper) |
| UA/Multi-Threat \[W\] | Promo: pre-order only |
| UA/Base Security \[W\] | Promo: free Halo Waypoint download |

Note: today's Halopedia says the plain UA/Multi-Threat and UA/Base Security models (no grenades) were unused in Reach and first appeared in MCC, while the 2011 armory lists both as buyable. Check which models your MCC build maps to these names before tagging them original.

**Wrist, utility, knee guards**

| Slot | Item | Original unlock |
| --- | --- | --- |
| Wrist | Default | Default |
| Wrist | UA/Buckler | 5,000 cR |
| Wrist | UA/Bracer | 10,000 cR |
| Wrist | Tactical/TACPAD | Major, 50,000 cR |
| Wrist | Tactical/UGPS | Lt. Colonel, 80,000 cR |
| Wrist | Assault/Breacher | Colonel, 200,000 cR |
| Utility | Default | Default |
| Utility | UA/Chobham | 30,000 cR (needs Tactical/Hard Case) |
| Utility | Tactical/Hard Case | Captain, 40,000 cR |
| Utility | UA/NxRA | Major, 40,000 cR (needs Tactical/Hard Case) |
| Utility | Tactical/Trauma Kit | Lt. Colonel, 60,000 cR (needs Tactical/Hard Case) |
| Utility | Tactical/Soft Case | Colonel, 100,000 cR |
| Knee guards | Default | Default |
| Knee guards | FJ/PARA | 10,000 cR |
| Knee guards | GUNGNIR | Captain, 25,000 cR |
| Knee guards | Grenadier | Lt. Colonel, 45,000 cR |

**Visors, armor effects, Firefight voices**

| Category | Item | Original unlock |
| --- | --- | --- |
| Visor | Default | Default |
| Visor | Silver | Sergeant, 35,000 cR |
| Visor | Blue | Warrant Officer, 50,000 cR |
| Visor | Black | Lt. Colonel, 100,000 cR |
| Visor | Gold | Colonel, 250,000 cR |
| Armor effect | Birthday Party | 200,000 cR |
| Armor effect | Heart Attack | 300,000 cR |
| Armor effect | Pestilence | 1,000,000 cR |
| Armor effect | Inclement Weather | 2,000,000 cR |
| Armor effect | Legendary (Flaming Helmet) | Promo: Legendary Edition |
| Armor effect | Eternal (blue flames) | Staff: Bungie employees only |
| Firefight voice | Noble Six | Default |
| Firefight voice | GySgt Stacker | 5,000 cR |
| Firefight voice | Jorge, Jun, Emile, Kat | 10,000 cR each |
| Firefight voice | Auntie Dot, GySgt Buck | 15,000 cR each |
| Firefight voice | Carter, SgtMaj Johnson, Cortana | 100,000 cR each |
| Firefight voice | John S-117 | 150,000 cR |

**Elite armor** (whole sets only, no piece mixing)

| Set | Original unlock |
| --- | --- |
| Minor | Default |
| Spec Ops | Corporal |
| Ranger | Sergeant |
| Ultra | Warrant Officer |
| Zealot | Captain |
| General | Major |
| Field Marshal | Lt. Colonel |
| Officer | Promo: Limited / Legendary Edition |

**Other original options**: Spartan or Elite (Elites mainly in Invasion and custom games), male or female Spartan, primary and secondary colors, emblem, 4-character Service Tag.

Not original (MCC-only): AKIS and Mariner helmets and their attachments (incl. Mister Chief, OPTREX), the robot-arm "\[R\]" chests added in Series 5, EXO/TSCS and GRD supplemental armor, and Fractures helmets (Belos, Blackguard, Drengr).

## Halo 4

Original Halo 4 is Spartan-only: helmet, chest, left and right shoulders, forearms, legs, visor, per-piece armor skins and a stance ([Halopedia](<https://www.halopedia.org/Armor_customization_(Halo_4)>); set list from [Halopedia template](https://www.halopedia.org/Template:Armor/Permutation/H4)). Armor effects did not exist in original Halo 4.

**Armor sets (helmet unlock shown; chest and shoulders use the same set names)**

| Set | Original unlock (helmet) |
| --- | --- |
| Recruit | Default |
| Warrior | SR-8 |
| Air Assault | SR-11 |
| Soldier | SR-15 |
| Aviator | SR-17 |
| Defender | SR-24 |
| Recon | SR-26 |
| EVA | SR-27 |
| War Master | SR-37 |
| Scout | SR-38 |
| Orbital | SR-41 |
| Infiltrator | SR-42 |
| HAZOP | SR-43 |
| EOD | SR-45 |
| Oceanic | SR-47 |
| Enforcer | SR-50 |
| Wetwork, Operator, Pioneer, Pathfinder, Engineer, Stalker, Rogue, Tracker | Specialization level 4 (chest at level 2) |
| Vanguard | Forerunner Destroyer commendation |
| CIO | Spartan Slayer commendation |
| Venator | Assassin commendation |
| GUNGNIR | Slayer Victory commendation |
| Commando | Dominion Victory commendation |
| Ranger | Combat Opportunity commendation |
| Protector | UNSC Loadout Mastery commendation |
| Mark VI | Legend commendation |
| Raider | Promo: Halo Waypoint Classified (Requiem Archive I) |
| Deadeye | Promo: pre-order (Best Buy / Play.com) |
| Locus | Promo: pre-order (MightyApe / HMV) |
| Scanner, Strider | DLC: War Games Map Pass |
| FOTUS | Promo: Halo 4 Limited Edition console |
| Mark V, ODST, Prefect | DLC: Infinity Armor Pack / Champions Bundle |
| Ricochet | DLC: Bullseye Pack / Champions Bundle |

Specialization armor (Wetwork, Operator, etc.) unlocks by leveling that Specialization; how Specializations themselves were opened (rank vs. War Games Map Pass) was not checked here, so verify before deciding whether to tag them Unlock or DLC.

**Forearms and legs** (separate slots): Contoured, GV-09 Locking, Inner-plated, LG-50 Bulk, Outer-plated, Over-locking, RG-63 Counter, Twin-plated, XG-89 Narrow, XV-27 Shifting. Per-item unlocks were not checked; all ten are original.

**Armor skins** (each skin belongs to one set; helmet-skin unlocks shown)

| Source | Skins |
| --- | --- |
| Unlock: commendations | MTRX, VERG, ZNTH, BOND, CTRL, SURG, BRCH, PRML, APEX, AEON, TRAC, SHDW, TRBL, CNVG, FRCT, STRK, DRFT |
| Unlock: specialization level 9 (chest at 7) | SHRD, SRFC, ADPT, CORE, EDGE, CRSH, FCUS, ADRT |
| Promo: Limited Edition | PRME |
| Promo: retailer pre-orders | FRST (GameStop), CRCT (Walmart), WEB (Amazon), RPTR (Best Buy), PULS (Microsoft) |
| Promo: Waypoint / codes / figures | VISN, RUSH (Waypoint Classified), DSTT (Requiem Archive II), SWFT (Section 3 code), TOXC, RUIN, RFCT (McFarlane figure codes) |
| DLC: Champions Bundle / Bullseye Pack | CLMN, PYTN, SLID, TRCR, BYNT, HMTM |

**Other original options**

| Category | Original content |
| --- | --- |
| Species | Spartan only (no Elites in multiplayer) |
| Colors | Primary and secondary armor colors |
| Visor colors | Several visor colors existed in the original (full list not captured here) |
| Stance, emblem, Service Tag | Yes (Spartan ID) |
| Weapon skins | Yes (loadout weapon skins) |

Not original (MCC-only): Keystone helmet, armor effects in Halo 4 (Pestilence, Birthday Party, Eternal, etc.), and MCC-exclusive weapon skins such as Pixel, Maw, Edgework and the Magnum Blood skin.

## Exclusives and open questions

These original items were promo-, DLC- or staff-gated, so most real lobbies never saw them; they are the ones to toggle separately.

| Game | Item | Gate |
| --- | --- | --- |
| Halo 3 | Recon (helmet, chest, shoulders) | Staff: Bungie-granted, later Vidmaster |
| Halo 3 | Bungie "Flaming Head" | Staff: Bungie employees |
| Halo 3: ODST | Sgt. Johnson | Promo: pre-order |
| Halo: Reach | Eternal armor effect | Staff: Bungie employees |
| Halo: Reach | Legendary (Flaming Helmet) effect | Promo: Legendary Edition |
| Halo: Reach | Elite Officer | Promo: Limited / Legendary Edition |
| Halo: Reach | Recon UA/HUL(3) attachment | Promo: pre-order / release day |
| Halo: Reach | CQB and Military Police helmets, UA/Base Security \[W\] | Promo: Halo Waypoint |
| Halo: Reach | UA/Multi-Threat \[W\] | Promo: pre-order |
| Halo 4 | FOTUS | Promo: Limited Edition console |
| Halo 4 | Deadeye, Locus, Raider + retailer/figure skins | Promo: pre-orders, Waypoint, codes |
| Halo 4 | Scanner, Strider | DLC: War Games Map Pass |
| Halo 4 | Mark V, ODST, Prefect, Ricochet + Champions skins | DLC: Infinity Armor Pack / Bullseye Pack / Champions Bundle |

Open questions to settle in-game or from MCC data before hard-coding:

- Halo 2 color names (count of 18 is sourced, names are from memory).
- Halo 3 and Halo 4 color and visor name lists (counts or existence only here).
- Halo 2: Anniversary launch color palette and launch weapon skins.
- Reach UA/Multi-Threat and UA/Base Security: which MCC model IDs match the original buyable chests.
- Reach "UA/Multi-Threat" shoulder naming (listed as "Mk V" left/right in the 2011 table).

**Sources (pages opened)**: [CE armor customization](<https://www.halopedia.org/Armor_customization_(Halo:_Combat_Evolved)>) · [H2A armor customization](<https://www.halopedia.org/Armor_customization_(Halo_2:_Anniversary)>) · [H3 armor customization](<https://www.halopedia.org/Armor_customization_(Halo_3)>) · [H3 armor template](https://www.halopedia.org/Template:Armor/Permutation/H3) · [ODST armor customization](<https://www.halopedia.org/Armor_customization_(Halo_3:_ODST)>) · [Reach armory, July 2011 revision](https://halopedia.org/Special:MobileDiff/933428) · [H4 armor customization](<https://www.halopedia.org/Armor_customization_(Halo_4)>) · [H4 armor template](https://www.halopedia.org/Template:Armor/Permutation/H4)
