# Original vs Modern Experience: what MCC added to each game, and the armor effects

Corrected (docs/HANDOFF_armor_oct28.md, from the maps' customization tables and the kits' Armory tags): Reach's
18 shoulders were all in the 2010 Armory (MCC added none), its plain UA/Base Security and UA/Multi-Threat chests are
MCC's; Halo 4's FORERUNNER and RICOCHET_ALT ids are the original Prefect and Ricochet HMTM, only the Olympus helmet and
the effects are MCC's; Halo 3's bytes are table indices, not MCC's item numbers. Where this file differs, that one holds.

2026 (evening). For the Settings tab's re-roll (named PvP Bots Mod until) (the player: "Original Experience or Modern Experience where
original is only the content that was in the original games for armor and colors and stuff, then Modern experiences
takes full advantage of all customizations at hand, gun camos, stuff not originally in or customizable in game etc.
Remember just because it has a modification slot in game doesnt mean it was original, like in Halo 3 ... only
chest and up, no legs"; "add a check for special armor effects (Flaming head in Halo 3, Lightning armor effect in
reach, etc)").

Original = the player's list, docs/research/13-original-customization.md (maps/_looks/original_content.json).
Modern = everything MCC offers today. This file is the Modern side, from MCC's own data on this PC (MCC 1.3528):

- `Data/UI/unlockdb.xml`: every item MCC gates, named `eUnlockItemId_CUSTOMIZATION_<game>_<slot>_<name>`
  (sorted into original / MCC addition by tools/original_vs_mcc.py -> maps/_looks/mcc_items.json)
- `Data/UI/playercustomization.xml`: the item ids MCC's menus use per game (Reach: 189 items in 9 slots)
- `MCC-Win64-Shipping.exe`: the per-game fields MCC saves for a player (strings near 0x32A1618): primary,
  secondary, tertiary colour, ServiceTag, PlayerModelPermutation, UseEliteModel, Helmet, LeftShoulder,
  RightShoulder, Chest, Arms, Legs, Wrist, Utility, Knees, Backpack, VisorColor, SpartanArmorEffect,
  EliteArmorEffect, EliteArmor, Elite helmet / chest / shoulders / arms / legs, Voice, SpartanBody, poses, emblem,
  and weapon and vehicle skins (SkinsObject[] / SkinsSkin[])

## Per game

| Game | Original (the player's list) | MCC adds (Modern only) | Armor effects |
|---|---|---|---|
| CE | one armor colour (18) | visor colours (31), weapon skins (56), vehicle skins (33), lobby poses | none |
| Halo 2 | Spartan or Elite, primary + secondary colour (18), emblem | lobby poses only (nothing seen in a match) | none |
| H2A | 3 Spartan + 3 Elite sets, worn whole (2014 launch) | 77 Spartan pieces (mixing since 2020), visor colours (17), weapon skins (25), poses | none |
| Halo 3 | helmet, left and right shoulder, chest (12 Spartan sets, 5 Elite); 3 colours from 30; emblem; service tag | arms, legs, backpack, techsuit slots; "H3E" pieces (29 helmets, 29 chests, 29 legs, 29 + 29 shoulders, 24 arms, 8 backpacks, 13 techsuits; 7 for each Elite slot); 19 more helmets, 17 + 17 shoulders, 7 chests, 7 arms, 7 legs, 18 backpacks; visor colours (58); weapon skins (101); vehicle skins (52) | Flaming Head: the Bungie staff chest (original, staff only; MCC gives it to everyone) |
| ODST | 7 Firefight characters, helmet on / off, 2 colours, emblem | injured Romeo and bug-splattered Buck variants (4 items) | none |
| Reach | all 168 original items (helmets with attachments, shoulders, chest, wrist, utility, knee guards, visor, effects, Elite armor, Firefight voice) | Belos, Blackguard, Drengr, GRD, Mariner helmets (26 with variants); Condemned chest and 5 "RoboArm" chests; Mjolnir Mk V and UA/Base Security shoulders (left + right); Vacuum Flask utility; poses | 7 Spartan (Birthday Party, Heart Attack, Pestilence, Inclement Weather (the lightning), Legendary flaming helmet (promo), Eternal blue flames (staff), none) + the same 7 for Elites |
| Halo 4 | full per-piece armor, 44 skins, visor, stance, emblem (with its DLC and promo sets) | armor effects (7), 3 helmets and 1 of each other piece, weapon skins (34), poses | 7 MCC-added effects: Modern only |

## How the re-roll's two switches map (decided here; the player can change it)

- Original: the player's list with its promo / DLC and staff items (they were in the original games, rare in real
  lobbies); a slot the original game did not have stays at its default (Halo 3 arms, legs, backpack: none; CE visor:
  default), never a copy of the player's.
- Modern: everything MCC offers, including MCC-only slots and items (weapon skins once decoded).
- Armor effects: None = every effect slot at "none" in every game
  (Reach slot 8; Halo 3 never chest 13, the Flaming Head; Halo 4 effect none). Rare / Common / Frequent = about 1 in
  10, 1 in 3, 2 in 3 of the bots wear one (brain/looks.py EFFECT_CHANCE; my picks): Reach's original 7 in either
  mode, Halo 3's Flaming Head in either mode, Halo 4's only in Modern (MCC added them).

## Where it stands

| Game | Bots' own look | Original filter | Effects switch |
|---|---|---|---|
| Reach | rolled from the game's own Armory (s74), Elite armor (s76), colours over the roll (+0x49 / +0x4A, 0-29, s100, live) | partly: the game's own Armory (logged live, s78) holds 21 helmets, the original count, so MCC's season helmets never appear; shoulders and chest are single items with 18 variants each and do not split cleanly into original / MCC yet | done: seen live |
| Halo 3 | Spartans done, decoded live (maps/_looks/h3.json), visor +0x6C (1-58, Modern) live; Elites: 3 armor bytes rolled from the 5 original sets, piece names not confirmed, MCC's Elite additions not decoded | done: original sets on helmet, shoulders and chest; arms, legs, undersuit (techsuit), backpack default: none of them existed in the original Halo 3 | done: the Flaming Head is chest 13 (and the Katana chest 11, not MCC's old list numbers) |
| CE | done: colour (maps/_looks/ce.json) | nothing MCC-added is in the record | none |
| Halo 2 | done: Spartan or Elite, colours (maps/_looks/h2.json) | nothing MCC-added shows in a match | none |
| ODST | colours only; character not identified (bots keep the player's); 4 players at most (more crashed it) | to do | none |
| Halo 4 | armor from the game's own Armory with its equip logic (s84); colours (+0x49 / +0x4A, 0-29) and visor (+0x4B, 0-16) over the roll, live (s99); skins: the variants the roll picks | to do | none or purple flames (only values verified), Modern only |
| H2A | original sets (region bytes; the catalog lists one variant per slot), colours (+0x49 / +0x4A, 0-29), Spartan set (+0x4C; Elites pending), live | Original whole sets, Modern mixes the 3 | none |

To decode a game's look: find which configuration bytes hold each piece (tools/look_probe.py steps one byte per
bot and photographs them; Reach only so far), then write maps/_looks/<game>.json. Needs a live MCC session per game.
