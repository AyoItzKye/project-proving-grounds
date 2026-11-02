# 09: Halo CE map callouts (all stock maps except Blood Gulch)

Research date: 2026-10-22. Purpose: a named-area vocabulary per map so the bots can speak MLG-style callouts ("one top OS, popped", "two red 3", "he's going camo"). Blood Gulch is in `06-blood-gulch-callouts.md`.

Source keys like [RR 7:16] or [QL 9/21] are listed in the last section with full URLs. YouTube timestamps are approximate (start of the caption window) and caption text is machine transcription, so spellings of slang names are approximate. [LOC] means the project's own extraction of the stock scenario (`maps\<map>\objects.json`), not a community source.

## How this was researched

- Callout guide videos (auto-captions read in full): Reaper Rising's "Halo CE Callouts Guide" (20 min, covers Hang 'Em High, Damnation, Derelict, Prisoner, Battle Creek, Chill Out); Missingno Wilder's "Callouts Halo 1" series (Hang 'Em High, Damnation, Prisoner, Chill Out, Derelict, Battle Creek) and "Breakdown with Spawns" videos (Wizard, Rat Race); Team Beyond "Beyond the Map" (xClicked, 2014, Prisoner and Chill Out); a Boarding Action MCC comms video (GamersDon'tDie, map identified from the thumbnail).
- Grenade-trick guides, whose trick titles are written in callout names: Okom's Steam guide (MCC PC), halonades.com (via the Wayback Machine; the domain is now parked), and the Halo1guide YouTube channel.
- Competitive and general guides: Zyos's Steam "Halo CE: Multiplayer Guide" (2020, LAN/2v2 player), Halopedia strategy sections, Bungie.net hints quoted on Halopedia.
- Team comms: auto-captions of 107 Halo 1 MCC Big Team Battle videos with voice comms from the Quiet Leviathan channel (the same channel used for Blood Gulch). Counts like [QL 11/21] mean "phrase heard in 11 of the 21 captioned videos for that map". This is the main source for the PC/BTB maps.
- Not readable from here: the halo-multiplayer-guide.fandom.com wiki (Cloudflare 403; its Prisoner, Battle Creek, Rat Race and Derelict pages were seen only through search-engine summaries, marked [HMG] and treated as unverified), halo1guide.com (domain no longer resolves), the official MCC Multiplayer Map Book (2014 print book that has callout overheads for every CE map; no text copy found), Reddit, and the LSR clan "Ratrace Callouts" video (no captions; storyboard frames too small to read).
- Remake names: Halopedia lists the in-game HUD location names for the Halo: Reach Anniversary remakes (High Noon, Penance, Solitary, Battle Canyon, Ridgeline). Those are listed per map as "do not use".

## 1. Key findings

1. Arena maps (the original Xbox 2v2/4v4 set: Hang 'Em High, Damnation, Prisoner, Chill Out, Derelict, Battle Creek) have a stable, well attested callout set. Two independent full-map callout videos (Reaper Rising and Missingno Wilder) agree on most names, and grenade-trick guides use the same names. Prisoner and Chill Out have a third full video (Beyond the Map, 2014).
2. Most names are "what is there": the weapon or power-up that spawns at a spot (rockets, sniper, OS or OV, camo, shotgun or shotties, PR, needles, pistol, nades), plus top / bottom / front / back / inside, plus a side word. Missingno says this directly for Chill Out, Derelict and Battle Creek [MW-CO 0:20] [MW-DER 0:35] [MW-BC 0:17]. A bot can therefore anchor most callouts on spawn items from `objects.json`.
3. Side words on arena maps are often colors of the lighting, not teams. Prisoner "red 1/2/3" is the red-lit side [MW-PRI 1:06] [BTM-PRI 0:43]; Chill Out "pink" is the pink camo room; Derelict "gold" (or "yellow") vs "green" are wall colors [RR 13:17]; Damnation "red" is the red-lit bottom and "green" the top. On Damnation the scenario disagrees with the names: the bottom flag stand next to the plasma pistol ("bottom red", "red flag") is the team-index-1 (blue) CTF flag, and the team-0 (red) flag is at the top [LOC]. Do not map Damnation "red" callouts to the red team's base.
4. Boarding Action callouts are ship color + floor number ("red 4 left", "blue 5 snipe"). The floor numbers are painted on the walls [HP-BA] [GDD] [QL 10/10].
5. BTB maps (Sidewinder, Timberland, Ice Fields, Death Island, Danger Canyon) have no callout guides; names come from comms counts. Common BTB patterns: top / bottom / front + red/blue for bases, "<color> portal", "top mid" / "bottom mid", "sniper spawn", "fuel rod", plus a few map-specific names: Sidewinder "keyhole", "red/blue rockets", "power-up tunnel"; Timberland "sniper hill", "dark side / light side"; Ice Fields "ice cave"; Death Island "top portal", "Banshee portal", "shade portal"; Danger Canyon "middle tunnel", "middle room".
6. Thin or none: Wizard (only "dark camo / light camo" plus spawn words), Longest (only grenade-trick names), Rat Race (a few names from one breakdown video), Gephyrophobia, Infinity (only "the pipes"), Chiron TL-34 (none). Suggested descriptive names are given for these and marked "suggested".
7. Many attested names are crude (for example on Hang 'Em High and Chill Out). They are listed once per map as "crude variants" so the bot can understand them, but should not be voiced.
8. Callout grammar from Reaper Rising (the only source that teaches it): where and how many first ("two red one"), then how weak ("full", "weak", "one shot", "popped", "absolute", or hit count), then power-up or power weapon ("with camo", "has OV", "killed camo", "burned camo"), then direction ("going top shotgun", "falling down to sniper"), then spawn reads ("spawning his teammate top OV"), hedged guesses with. Other words: "traded", "fresh" (both enemies dead, expect random spawns), "bombing <place>" (grenade spam), "random" (stand where the partner gets a random spawn) [RR 0:25-3:20] [ZY].

## 2. Coverage summary

| Map (folder) | Coverage | Best sources |
|---|---|---|
| Hang 'Em High (hangemhigh) | Well covered | RR, MW-HEH, Okom, halonades, Halo1guide, Zyos, Halopedia, QL 15 videos |
| Damnation (damnation) | Well covered | RR, MW-DAM, Halopedia layout section, halonades, Okom, Halo1guide |
| Prisoner (prisoner) | Well covered | RR, MW-PRI, BTM-PRI, halonades, Okom, HMG (unverified) |
| Chill Out (chillout) | Well covered | RR, MW-CO, BTM-CO, halonades, Okom, Halo1guide, Halopedia |
| Derelict (carousel) | Well covered | RR, MW-DER, halonades, Okom, Halopedia |
| Battle Creek (beavercreek) | Well covered | RR, MW-BC, halonades, Okom, Halo1guide, Halopedia, QL 4 videos |
| Boarding Action (boardingaction) | Covered (simple system) | GDD, QL 10 videos, Halopedia, Okom |
| Sidewinder (sidewinder) | Medium (comms only) | QL 21 videos, Halopedia |
| Timberland (timberland) | Medium (comms only) | QL 15 videos, Halopedia |
| Ice Fields (icefields) | Medium (comms only) | QL 11 videos, Halopedia |
| Death Island (deathisland) | Medium-thin | QL 6 videos, Halopedia |
| Danger Canyon (dangercanyon) | Medium-thin | QL 7 videos, Halopedia |
| Rat Race (ratrace) | Thin | MW-RR, Zyos, Halopedia, QL 3 videos, HMG (unverified) |
| Wizard (wizard) | Thin | Zyos, MW-WIZ, Halopedia |
| Longest (longest) | Thin | Okom, Halopedia |
| Gephyrophobia (gephyrophobia) | Thin | QL 5 videos (few names), Halopedia, Zyos |
| Infinity (infinity) | Thin | Halopedia ("the pipes") |
| Chiron TL-34 (putput) | None attested | Halopedia layout only |

Confidence in the tables: High = 3 or more independent sources, or 2 callout guides plus regular comms use. Medium = 2 sources. Low = 1 source. Suggested = not attested; a plain descriptive name proposed from the layout.

## 3. Hang 'Em High (hangemhigh)

Layout: Forerunner hall; ground floor of "tombstone" blocks, two shelters with shotguns, a central trench; ramps and bridges up to two top structures (red tower and top blue) that are the CTF bases; sniper and rocket launcher on the upper catwalks [HP-HEH]. No teleporters [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Red tower, top red, red tower ramp | The tall tower in one corner; top of it is the red CTF base; its ramp | High | [RR 9:11] [MW-HEH 2:42] [HP-HEH] [HN-HMH] [QL red tower 5/15, top red 7/15] |
| Top blue (also "pyramid", "castle") | Top structure on the blue side; blue CTF base | High | [RR 8:22] [MW-HEH 3:47] [OKOM "Top Blue Base"] [H1G "Top Blue"] [QL top blue 8/15] |
| Front blue, dark blue, top dark, top front | Area in front of and beside top blue | Medium | [RR 8:22] [MW-HEH 4:05] |
| T2, T3 | Two spots near top blue (RR shows them between front blue and the open ramp) | Low | [RR 8:37] |
| Open ramp (top open, bottom open; also "outside ramp", "big ramp") | The long uncovered ramp; top and bottom ends | High | [RR 8:37] [MW-HEH 0:01] [OKOM "Blue Open Ramp"] [QL 9/15] |
| Closed ramp (top closed, bottom closed; also "close ramp", "inside ramp") | The covered ramp | High | [RR 8:07] [MW-HEH 0:32] [QL 10/15] |
| Cuts | Spot RR shows next to bottom closed and again near bottom open | Low | [RR 8:07, 8:54] |
| Hole | Opening by blue shotgun / under the closed ramp | Low | [RR 8:07] |
| Elbow (also "long way"), catwalk elbow | Bend of the upper catwalk | Medium | [RR 8:22] [H1G "Catwalk Elbow"] |
| Catwalk(s) | Upper walkways to the sniper and top power-up | Medium-High | [RR 9:11] [MW-HEH 2:42] [HP-HEH] [QL 4/15] |
| Office (also "batter's box", "bunker"), office random, top office | Small room on the blue side next to blue pistol and the window | High | [RR 8:54] [MW-HEH 3:30] [QL office 11/15] [RR comms 4:50] |
| Window | Opening RR shows right after blue pistol | Medium | [RR 8:54] [OKOM "Sniper from Top Window"] |
| Blue pistol, blue pistol corner, random ramp | Pistol spawn on the blue side; the corner below it gives a partner a spawn on top of blue pistol | High | [RR 8:54] [MW-HEH 3:13] [ZY] [HN-HMH] [H1G] [QL 2/15] |
| Red pistol, red pistol corner | Pistol spawn on the red side | Medium-High | [RR 7:33] [MW-HEH 1:08] [RR comms 5:39] |
| Blue shotgun(s), red shotgun(s) (shotties; "shotgun gallery" in Oddball) | Shotgun spawns in the two ground shelters, one per side | High | [RR 7:01, 8:07] [MW-HEH 0:47, 2:27] [HP-HEH] [OKOM] [HN-HMH] [QL 5/15] |
| Red tombs, blue tombs (tombstones, graves) | The fields of tombstone blocks on each side of the ground floor | High | [RR 7:01, 7:49] [MW-HEH 0:32] [HP-HEH] [OKOM "Tombstone"] [H1G "Red Graves", "Blue Graves"] [QL 4/15] |
| Red field, poles | Open ground area on the red side; its posts | Low | [RR 7:01] |
| Red ramp, red ramp corner | Ramp on the red side of the ground floor | Medium | [RR 7:16] [MW-HEH 4:21] |
| Back red, back wall | Area behind the red side; the back wall | Medium-High | [RR 7:16, 9:26] [MW-HEH 2:12] [H1G "Back Red", "Back Blue"] |
| Red nose | Protrusion from the wall on the red side | Medium | [RR 7:16] [MW-HEH 1:55] |
| Red random, danger, safe | Spots on the red side that give a random spawn ("danger") or a safer one ("safe") | Medium | [RR 7:16] [MW-HEH 2:12] |
| Sweet spot | Corner below red base that is hard to shoot | Medium-High | [RR 7:33] [MW-HEH 1:24] [RR comms 4:00] |
| Pit, trench, snipe trench | The central trench | High | [RR 7:33] [MW-HEH 1:39] [HP-HEH] [QL] |
| Bottom middle | Ground center by the health pack | Low | [MW-HEH 1:39] |
| Hangman (bottom hangman, top hangman) | The central pillar ("tree"); top hangman is the sniper platform | Medium | [RR 7:49, 9:11] [MW-HEH 0:16] |
| Sniper, top snipe | Narrow high platform in the middle, reached by jumping from the high bridge | High | [HP-HEH] [RR 9:11] [MW-HEH 2:57] [OKOM] |
| TP (top power-up), top OS | Power-up on the top catwalks | High | [RR 9:11] [MW-HEH 2:42] [OKOM "Top Powerup"] [H1G "Top OS from Mid Red"] |
| Rockets | Rocket launcher on the upper catwalks (one spawn [LOC]) | High | [HP-HEH] [OKOM] [HN-HMH] |
| Camo, camo ramp, camo corner (dark corner), camo catwalk, camo random | Ground-floor camo spawn and the ramp, corner and catwalk next to it | High | [RR 7:49] [MW-HEH 0:47] [H1G "Camo Corner"] [QL dark corner 4/15] |
| Trash corner | The worst spawn on the map (RR's first stop) | Low | [RR 6:46] |
| Mid red, blue shelf | Grenade-trick spots | Low | [H1G] |
| Tunnel | Long tunnel beneath the tall-tower corner | Low | [HP-HEH] |
| Canal (bottom canal) | Ground-level spot heard in BTB comms; place unverified | Low | [QL 2/15] |

Crude variants (understand, do not voice): "butthole" (below closed ramp at PR), "gay ramp" (by top blue), "red dick" (= red nose), "shit spawn" / "shit corner" (= trash corner, red tombs) [MW-HEH] [RR 6:46].

Remakes, do not use for CE: Halo 2 Tombstone; Reach High Noon HUD names Red/Blue Bunker, Red/Blue Tunnels, Overlook, Overlook Room, Portal Overlook, Portal Footbridge, Central Area, Covered Ramp, Lower/Upper/Outer Catwalk, Trench, Overlook Footbridge, Long Ramp [HP-HN]. "Trench" happens to match CE use.

## 4. Damnation (damnation)

Layout: Covenant dam interior; one two-way teleporter; four zones: red (below the teleporter), green (top area: bottom green, top green, top shotties, top snipe), waterfall (three jump platforms on the far side), and "everything else" (OS and rockets next to each other in the pit, shotties balcony, bottom snipe). Green is reached only by the teleporter and a short tunnel from bottom snipe; camo sits on a thin plank outside green [HP-DAM layout]. Color names are lighting; see finding 3 for the flag team mismatch [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Bottom red, red flag | Bottom area at the plasma pistol spawn and the low flag stand | High | [RR 9:45] [MW-DAM 0:00] [HP-DAM] [HN-DAM "Bottom Red PP"] |
| Red random | Spot in red that gives a random spawn | Medium | [RR 10:00] [MW-DAM 0:16] |
| Computers (computer) | Noisy computer console in red that players stand on | Medium | [RR 10:00] [MW-DAM 0:16] |
| Red health, red door | Health pack in red; doorway from red out to the shotgun balcony | Medium | [RR 10:18] [MW-DAM 0:33] [HN-DAM "Red door"] |
| Red plat / red flat | Platform in red | Medium | [RR 10:18] [MW-DAM 0:33] |
| Red ramp, top red, red shelf | Ramp up from red; top of it; a ledge reached by rocket jump | Medium | [RR 10:00] [OKOM "Red Ramp", "Top Red"] [HN-DAM] [H1G "Red Shelf"] |
| Short ladder, big ladder (long ladder) | The two ladders into the pit | Medium | [RR 10:00] [HN-DAM "Long ladder", "Pit small ladder"] |
| Pit, rockets | The pit where the rocket launcher spawns | High | [RR 10:00] [MW-DAM 0:33] [HP-DAM] [HN-DAM] [OKOM] |
| OV / OS, OS jump, OS ledge | Overshield next to rockets; the jump up to it and the small platform outside | High | [RR 9:45] [MW-DAM 1:39] [HP-DAM] [HN-DAM] |
| Street (walk, sidewalk), front shotgun, bottom shotgun, shotties | The main lower balcony; two shotguns near the windows | High | [RR 10:18] [MW-DAM 0:50] [HP-DAM] |
| Elbow | Bend next to the shotgun balcony toward sniper | High | [RR 10:35] [MW-DAM 1:06] [OKOM "Camo from Elbow"] [HN-DAM] |
| Sniper, bottom snipe, low snipe (also "pipe room", "sweaty") | Lower sniper room; links shotties, PR and bottom green | High | [RR 10:35] [MW-DAM 1:06] [HP-DAM] [QL] |
| PR room | Plasma rifle room; easy to get spawn trapped in | High | [MW-DAM 1:24] [HP-DAM] [HN-DAM "PR room"] |
| Waterfall(s) | Three isolated jump platforms and planks on the far side; flank route to rockets, PR and back red | High | [RR 9:45] [MW-DAM 1:39] [HP-DAM] [QL] |
| Back red | Far end of red where the plasma pistol is (HP's use) | Medium | [HP-DAM] |
| Clinky (clanky) | Noisy metal ramp area into green | Medium | [RR 10:35] [MW-DAM 2:42] |
| Bottom green, green ramp, back green, green flat (green plat), top green, green room | The green (top) room: floor, ramp, back, platform, upper level | High | [RR 10:35] [MW-DAM 2:42] [HP-DAM] [OKOM "Green"] [QL green room] |
| Pipe | Standing on the pipe in green | Low | [RR 10:52] |
| Top shotgun, top shotties, shotgun flat | Upper shotgun spawn and its platform | Medium-High | [RR 10:52] [MW-DAM 2:09] [HP-DAM] |
| Pistol, lookout | Pistol spawn behind camo | Medium | [RR 10:52] [MW-DAM 2:09] |
| Catwalk, portal, deagle | The catwalk at the top teleporter end; "deagle" is the end where it meets the wall | Medium | [RR 11:07] [MW-DAM 1:54] |
| Top sniper, top snipe, top front green | Upper sniper spot at the front of green | Medium-High | [MW-DAM 2:25] [HP-DAM] [OKOM "Top Front Green"] |
| Teleporter / portal, top portal | The two-way teleporter; red end below, green end on top | High | [HP-DAM] [RR 11:07] [QL top portal] |
| Camo, legs 1-4 (red leg, green leg), plasmas, divots | Camo plank outside green; its four supports; the plasma grenade corner; small floor dips | Camo High; rest Low | [RR 11:07-11:24] [HP-DAM] [HN-DAM camo page] [OKOM] |
| Rocket random | Spot RR/MW call a random near front shotty | Low | [MW-DAM 2:59] |
| Boiler room | Heard in one BTB comms video; place unverified | Low | [QL 1] |

Bungie.net hint terms (not community callouts): "high teleport road", "low dam crossing", "uplink crate" [HP-DAM].

Crude variants: names for the PR room ("f** room", "gay room") [MW-DAM 1:24].

Remake, do not use: Penance (Reach Anniversary) HUD names Abyss, Lower Bridge, Cave, Teleporter Room, Teleporter Overlook, Waterfall Balcony, Observation Deck, Lower Pit, Pit Overlook, Rafters, Upper Bridge, Control Room, Ramp Hallway, Pump Room, Upper Pump Room, Pump Room Balcony [HP-PEN]. Halopedia lists no Halo 2 or Halo 3 remake of Damnation.

## 5. Prisoner (prisoner)

Layout: three-floor Forerunner prison; camo under the central pillar on the ground floor, rocket launcher above it; bridges between sides; one side red-lit [HP-PRI] [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Camo, bottom mid (bottom middle, bottom camo) | Ground floor center, under the central pillar | High | [RR 13:49] [MW-PRI 2:14] [BTM-PRI 0:08] [HP-PRI] [HMG] |
| Rockets | Center, above camo | High | [BTM-PRI 0:08] [HP-PRI] [HN-PRI] [OKOM] [HMG] |
| Doubles (twos, double doors) | Ground-floor spot with two doors | High | [RR 13:49] [MW-PRI 2:14] [BTM-PRI 0:43] |
| Triples (threes, triple doors), bottom OS, OB1 | Ground-floor spot with three doors, under the OS | High | [RR 14:06] [MW-PRI 2:31] [BTM-PRI 0:25] |
| Red 1, red 2, red 3 (red court for the whole red ground area) | Floors 1 to 3 on the red-lit side | High | [RR 13:49-15:18] [MW-PRI 0:02, 1:06] [BTM-PRI 0:43, 0:59] [HN-PRI "Red 3"] [HMG "Red 3"] |
| Red ladder | Ladder from red 1 to red 2 | Medium | [MW-PRI 0:18] [BTM-PRI 0:59] |
| Back wall 1, 2, 3 (B1, B2, B3; "back one/two/three") | The far wall side, by floor | High | [RR 13:49, 14:22, 15:35] [MW-PRI 1:41] [BTM-PRI 0:43, 0:59] [HN-PRI "BackWall"] [HMG "Backwall 2"] |
| Back whack | Spot next to red ladder where players wait to hit you from behind | Medium | [RR 14:06] [MW-PRI 0:18] |
| Elbow, bottom elbow | Corner between red and back wall, upper and lower | High | [RR 14:22] [MW-PRI 2:14] [BTM-PRI 0:43] |
| Bottom sneaky, top sneaky | Two spots RR shows past back two | Low | [RR 14:22, 15:35] |
| Blue ramp (camo ramp, back ramp) | Ground ramp on the non-red side | Medium | [RR 14:41] [BTM-PRI 0:43] |
| O2 (OV2), under OS, bottom health | Middle floor under the OS | Medium | [RR 14:41] [MW-PRI 2:46, 3:18] |
| OS ramp (OV ramp, safe ramp), bottom safe, safe corner, top safe | Ramp up to the OS; the "safe" spawn at its bottom | Medium-High | [RR 14:57] [MW-PRI 0:18, 0:34] [H1G "OS to Bottom Safe"] |
| Top OS, top OV, O3 (OB3), OS bridge, OS catwalk | The overshield on the top floor and the bridge to it | High | [RR 14:57] [MW-PRI 0:50] [BTM-PRI 1:34] [HN-PRI] [OKOM] |
| Front OV | Area in front of top OS | Low | [RR 15:18] |
| Mid bridge, red bridge | Top-floor bridge across the middle | Medium | [BTM-PRI 1:50] [MW-PRI 0:50] |
| Red sniper (red snipe) | Sniper spawn on the red side, top floor | High | [RR 15:18] [MW-PRI 3:35] [BTM-PRI 1:50] [HN-PRI "Red Snipe"] |
| Back sniper (blue sniper, back wall snipe) | Sniper spawn on the back-wall side | High | [RR 15:35] [MW-PRI 3:35] [BTM-PRI 1:50] |
| Z (Z's jump) | Grenade-jump spot RR shows next to red sniper | Medium | [RR 15:18] [MW-PRI 3:03] |
| Office, front office, window (glass; "hospital" in one region) | Top-floor room with breakable windows | High | [RR 15:18-15:35] [MW-PRI 1:24] [BTM-PRI 1:50] [HN-PRI "Office entrance"] [HMG "Windows", "Blue Windows"] |
| Top health (top HP) | Health pack on the top floor | Medium | [RR 15:35] [HN-PRI "Top HP"] |
| PR, PR1, PR2, PR ladder (blue ladder) | Plasma rifle spots and the ladder there | Medium-High | [BTM-PRI 1:16] [MW-PRI 1:58] [HN-PRI "Top PR"] |
| Red health | Health pack on the red side | Low | [MW-PRI 3:18] |
| Red tunnel, blue tunnel | Where the CTF variant puts its two overshields | Low (unverified) | [HMG] |

Crude variants: "gay jump" (= Z's jump), "shit spawn" (= trash) [MW-PRI 3:03] [RR 14:41].

Remake, do not use: Solitary (Reach Anniversary; adds lifts and walkways) HUD names Ground Floor, Ground Floor Cells, Ground Floor Viewing, Monolith, Lift Room, Lower Ramp, Observation Deck, 2nd Floor, Upper Ramp, 3rd Floor, 3rd Floor Cells, Overlook, Red Ramp, Blue Ramp, Red Loft, Blue Loft, Upper Chamber, 4th Floor, Security Platform [HP-SOL].

## 6. Chill Out (chillout)

Layout: small asymmetric set of rooms in a Covenant structure; main room with tall structures (rocket launcher on one), broken bridge room, pink room with the camo, three teleporters [HP-CO] [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Shotgun (shotties, shotgun room), pillar, shotgun ramp, top shotties | Room where the shotgun spawns; its pillar, ramp and top | High | [RR 17:33] [MW-CO 0:52] [BTM-CO 1:31] [HN-CO "Top Shotties"] [HP-CO] |
| OV / OS (OS hall; "front door") | Overshield next to the shotgun room | High | [RR 17:49] [MW-CO 0:35] [BTM-CO 1:31] [OKOM "Main Room to OS"] [HN-CO] |
| Main (main room, lobby), main pillars, bottom main | The large central room | High | [RR 17:49] [MW-CO 0:01] [BTM-CO 1:15] [OKOM] [H1G "Rockets from Main", "Pillars"] |
| Health pack, opposite | Health pack spot RR shows in main; "opposite" is across from it | Medium | [RR 17:49] [MW-CO 0:01] [HN-CO "Healthpack/OS"] |
| Dark, front dark, dark hall, dark room | Dark hallway and room off main | High | [RR 18:05] [MW-CO 2:26] [BTM-CO 1:15] |
| Spiral (spiral stairs), needles (needler), dark bridge | Spiral stair by the needler spawn | High | [RR 18:05] [MW-CO 0:52] [BTM-CO 1:46] |
| Pink, pink broken (broken bridge), pink hall, camo room (cloak room) | The pink-lit room with the broken bridge and camo; the hall by its portal | High | [RR 18:05-18:25] [MW-CO 1:24] [BTM-CO 0:58] [HP-CO "dark-pink/red colored room", "pink hallway by the portal"] [H1G "Bridge"] |
| Sniper hall, sniper room, low bridge, high bridge (needle bridge, snipe bridge) | Hall and room where the sniper spawns; the two bridge levels | Medium-High | [BTM-CO 0:42, 0:58] [MW-CO 1:39] [HP-CO "snipe room"] |
| Window | Window looking into the sniper room | High | [RR 18:25] [MW-CO 1:07] [BTM-CO 0:42] [HP-CO] |
| Elbow | Bend RR shows between pink hall and window | Low | [RR 18:25] |
| Top PR (PR2), mid PR, bottom PR (PR1), rocket ramp (PR ramp) | Plasma rifle spots and the ramp up in the rocket room | High | [RR 18:25] [MW-CO 1:39] [BTM-CO 0:25] [OKOM "Top Plasma/PR2"] [H1G "PR ramp"] |
| Rockets, top rockets, bottom rockets, rocket room, rocket pillars | Rocket launcher on the tall structure; floor under it | High | [RR 18:25-18:41] [MW-CO 1:54] [BTM-CO 0:25] [OKOM] [HP-CO] |
| Side door | Door RR shows by bottom PR | Medium-High | [RR 18:41] [MW-CO 2:10] [H1G "Side Door"] |
| Double doors (doubles), pistols | Pair of doorways from main; "pistols" right behind them | High (double doors) | [RR 18:41] [MW-CO 0:20] [BTM-CO 0:42] |
| Back door | Door from the rocket room back toward shotgun | High | [RR 19:00] [MW-CO 2:10] [BTM-CO 0:42, 1:46] |
| Zum / zom, opposite zum (main zum) | A corner and the one opposite it | Medium | [RR 18:59] [MW-CO 2:58] |
| Nade out, back wall | A corner and the back wall | Low | [RR 18:59-19:16] |
| Sticky nade | Spawn by bottom PR | Low | [MW-CO 1:54] |
| Top portal, top health pack | Teleporter exit and health pack at the sniper hall | Medium | [BTM-CO 0:42] [HP-CO] |
| Double ramp, opposite pillar | Grenade-trick spots | Low | [HN-CO] |

Crude variants: a slur name for the room by side door [MW-CO 2:26].

Remakes, do not use: Halo 3 Cold Storage; a Halo 5 remake [HP-CO]. Their names were not collected.

## 7. Derelict (carousel)

Layout: small symmetric map; four pillars support cross-shaped catwalks reached only by teleporter; upper center OS, lower center health pack; camo on the upper level between two lights, sniper opposite it before three lights; flamethrowers at side tunnel entrances [HP-DER]. Missingno: "it all looks very similar", so callouts must name the item nearby [MW-DER 1:37].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Top mid (top OS) | Upper center, overshield | High | [RR 11:40] [MW-DER 0:52] [HN-DER "Nadejump to Top mid (OS)"] [HP-DER] [HMG] |
| Catwalks ("rockets going top mid", "top mid going camo") | The cross catwalks between the corners and top mid | Medium | [RR 12:29] |
| Sniper, sniper portal, sniper cubby | Upper corner where the sniper spawns (one continuous wall piece) | High | [RR 11:40, 12:11] [MW-DER 0:18] [OKOM] [HN-DER] [HP-DER] |
| Rockets, rocket cubby, left rockets, right rockets, rocket tunnel, front rockets | Upper corner where the rocket launcher spawns | High | [RR 11:56] [MW-DER 0:18] [OKOM "Rockets Side"] [HN-DER "Catwalk rocketside"] |
| Camo, camo portal, Dorito | Upper corner with the camo (two distinct wall pieces; "Dorito" is a triangular piece) | High (camo); Low (Dorito) | [RR 11:56, 12:11] [MW-DER 0:02] [HP-DER] |
| Needles, needle cubby, left/right needles, needler portal | Upper corner where the needler spawns | Medium | [RR 12:11] [MW-DER 0:35] |
| Bottom mid | Lower center, health pack; spawn spot for a random | High | [RR 12:29] [MW-DER 0:52] [HN-DER "Camo from Bottom mid"] [HP-DER] |
| Bottom sniper, bottom sniper port, under sniper port, sniper cubby (lower) | Lower level under the sniper corner | Medium | [RR 12:29, 13:01] [MW-DER 1:22] |
| Bottom camo, bottom camo portal, under camo portal, camo cubby | Lower level under the camo corner | Medium-High | [RR 12:45-13:01] [MW-DER 1:22] [OKOM "Camo from Bottom Camo"] [HN-DER] |
| Bottom rockets | Lower level under the rockets corner | Low | [MW-DER 1:22] |
| Gold (gold corner, gold wall; also "yellow") | Lower side with gold walls: under sniper and rockets | Medium-High | [RR 12:45, 13:17] [MW-DER 0:52] [HMG "Bottom Gold"] |
| Green wall | Lower side with green walls: under camo and needles | Low | [RR 13:01, 13:33] |
| Side tunnels | Tunnels with flamethrowers at their entrances (PC) | Low | [HP-DER] |

Remake, do not use: Halo 2 Desolation [HP-DER].

## 8. Battle Creek (beavercreek)

Layout: two small bases at the ends of a canyon with a creek across the middle; a natural stone arch in the middle with the rocket launcher on top; camo in small caves by the creek; sniper ledges reached by ladder, one overlooking red base; teleporters at the back of each base; jump spots to the roofs (a boulder at red, concrete debris at blue) [HP-BC] [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Top red, top blue | Base roofs | High | [RR 15:50, 17:13] [MW-BC 0:17] [OKOM] [H1G] [QL 3/4] |
| Back red, back blue | Behind each base (teleporter side) | High | [RR 15:50, 17:13] [MW-BC 0:01] [H1G "Back Red", "Back Blue"] [QL 2/4] |
| Inside red, inside blue | Inside each base | Medium-High | [RR 16:07, 17:13] [MW-BC 0:17] |
| Front red, front blue | In front of each base | High | [RR 16:07, 16:55] [MW-BC 0:35] [QL 2/4] |
| Red needles (needle red), blue needles | Corner on the needler side of each base | High | [RR 16:07, 17:13] [MW-BC 0:01] [HN-BC "Red Needlers", "Blue Needler Corner"] |
| Red PR, blue PR | Plasma rifle side of each base | Medium | [MW-BC 0:17] [HN-BC "Blue PR"] |
| Big rock | Large boulder on the red side (the red-side marker) | Medium | [RR 16:55] [MW-BC 0:01] [HP-BC "a boulder at red base"] |
| Blue wall (big wall) | Wall on the blue side | Medium | [RR 16:07] [MW-BC 1:57] |
| Red jump, blue jump | Ledge used to jump onto each roof | Medium-High | [RR 16:07, 16:55] [HP-BC] [QL 3/4] |
| Blue rocks | Rocks in front of blue | Low | [RR 16:22] |
| Red cubby, blue cubby (blue fox) | Small alcoves by each base | Medium | [RR 16:22] [MW-BC 0:35] |
| Creek, pit | The creek across the middle | High | [RR 16:22] [MW-BC 1:08] [HP-BC] [HMG] |
| Camo (cloak) | Camo by the creek; a crouch-in cave under the water on the far side | High | [RR 16:22] [MW-BC 0:51] [HP-BC] [H1G "Rockets to Camo"] |
| H2 (H2 shotty) | Spot by the creek where Halo 2's Beaver Creek has a shotgun; a CE name that references Halo 2 | Medium | [RR 16:38] [MW-BC 1:08] |
| Light snipe (light sniper) | Lit sniper ledge above camo, overlooking red | High | [RR 17:13] [MW-BC 0:35] [H1G "Light Sniper"] [HP-BC gallery] |
| Dark snipe (dark sniper) | Shadowed sniper ledge on the other wall | High | [RR 16:38] [MW-BC 1:24] [H1G "Dark Sniper"] |
| Dark blue, light blue, dark red, light red | The dark-wall and light-wall halves of each side | Medium | [OKOM] |
| Arch, top rockets (rocket arch), bottom arch | The stone arch; rocket launcher on top; ground under it | High | [RR 16:38] [MW-BC 1:24] [HP-BC] [HMG] |
| OS | Overshield (halonades trick "Rockets from/to OS"); spot unverified | Medium | [HN-BC] [QL 3/4] |
| Big tree | Named by HMG; spot unverified | Low (unverified) | [HMG] |

Remakes, do not use: Halo 2 Beaver Creek (its "sniper tower" and the easter egg belong to it); Reach Battle Canyon HUD names East Terrain, Blue Roof, Blue Base, Blue Teleporter, South Perch, South Cave, North Cave, North Perch, West Terrain, Red Roof, Red Base, Red Teleporter, Creek, Rock Arch [HP-BCAN]. Battle Canyon "Creek" and "Rock Arch" happen to match CE use.

## 9. Boarding Action (boardingaction)

Layout: two parallel ships, five mirrored floors each, with the floor number marked on the wall; teleporters on floors 1 and 5 lead to the same spot on the other ship; a power-up in a small indent in the top right corner of each base (looking out) [HP-BA]. In the scenario the team-0 (red) flag is on the ship at x about 2 and the blue flag on the ship at x about 18 [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Red 1 ... red 5, blue 1 ... blue 5 | Ship color + floor number | High | [GDD 1:32-6:44] [QL 10/10] [HP-BA] [OKOM "Level 5"] |
| Left, right, mid / middle / center (as qualifiers: "red 4 left", "blue 4 far left", "center right blue 4") | Position along the floor, as seen by the caller | High | [GDD] [QL left/right 9/10, center/middle 8/10] |
| Red snipe, blue snipe ("blue 5 snipe") | Sniper on a top floor (sniper spawns at z about 5 [LOC]) | Medium | [QL 2/10] [GDD] [OKOM "Other team's Sniper from Level 5"] |
| Teleporter / portal | Floors 1 and 5 | High | [HP-BA] [GDD] [QL 4/10] |
| Rocket box (rocket room) | Where the rocket launchers spawn | Low-Medium | [GDD 4:29, 6:25] [QL 1/10] |
| Shotgun box | Where a shotgun spawns | Low | [GDD 5:49] |
| Tunnel ("tunnel in red five") | A passage on floor 5 | Low | [GDD 2:22] |
| Power-up corner | Suggested name for the indent with the power-up in each base's top right corner | Suggested | [HP-BA] |

Remake: none listed by Halopedia.

## 10. Sidewinder (sidewinder)

Layout: horseshoe canyon with a base at each end; two outer cliffs reached from each base by teleporter, each with a rocket launcher and a fuel rod; a tunnel network on the inner edge with four power-ups in its lower section; ice patches between the bases [HP-SW]. Scenario: rocket launchers at (-40.4, 32.6) and (39.0, 30.5), far from the bases at y about -44; overshield and camo spawns at about (-1, -43, z -3.8), low and between the bases [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Top red, top blue | Upper base / roof (sniper spawns there [LOC]) | High | [QL 12/21] |
| Bottom red, bottom blue | Lower base / ground floor | Medium-High | [QL 10/21] |
| Front red, front blue | In front of each base | Medium | [QL 6/21] |
| Red rockets, blue rockets ("red rockets portal") | The cliff ledge on each side where rockets and a fuel rod spawn, reached by teleporter; which ledge is which color is inferred from distance to each flag | Medium-High | [QL 11/21] [HP-SW] [LOC] |
| Red portal, blue portal, first portal, second portal | Teleporters; "first/second" order meaning is unverified | Medium (portal); Low (first/second) | [QL first 6/21, second 3/21] |
| Keyhole (red keyhole, blue keyhole, top keyhole, keyhole ramp) | A spot in or at the tunnel system on each side ("blue tunnel keyhole", "blue power-up tunnel on keyhole"); exact geometry unverified | Medium (heavily used, place unverified) | [QL 18/21] |
| Power-ups, power-up tunnel (red power-ups, blue power-ups) | Lower tunnel section with the four power-ups, between the bases | High | [QL 18/21, tunnel 5/21] [HP-SW] [LOC] |
| Tunnels, red tunnel, blue tunnel | The inner-edge tunnel network | Medium | [QL 2/21] [HP-SW] |
| Fuel rod | Fuel rod spawns on the cliffs | Medium | [QL 9/21] [HP-SW] |
| Ice | Frozen ponds that make Warthogs slide | Suggested | [HP-SW] |

Remake, do not use: Halo 3 Avalanche [HP-SW].

## 11. Timberland (timberland)

Layout: two two-story bases (like Sidewinder's) separated by hills, trees and a creek; overshield on an island in the creek in the middle; camo on either side and one inside the small waterfall; four snipers, two rockets, two fuel rods placed opposite each other; no teleporters [HP-TL]. Scenario: OS at (0.9, -1.2); side camos at (-26.1, 1.2) and (27.5, -0.1); non-base snipers at (-16.1, -28.0) and (17.3, 27.9) [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Sniper hill (snipe hill; red / blue sniper hill) | Hill with a sniper spawn in each half (probably the non-base sniper spawns) | High (name); Medium (exact spot) | [QL 11/15] [LOC] |
| Dark side, light side ("dark side camo") | The two long sides of the map by lighting; which side is dark is unverified | Medium | [QL dark 6/15, light 4/15] |
| Top red, top blue | Upper floor / roof of each base | High | [QL 10/15] |
| Front red, front blue | In front of each base | Medium-High | [QL 7/15] |
| Red sniper, blue sniper | Sniper spawns (base or hill) | Medium | [QL 5/15] |
| Camo (side camo, waterfall camo) | Camo on each side and in the waterfall | High | [QL 10/15] [HP-TL] |
| OS, middle (island) | Overshield on the creek island | High | [QL 6/15] [HP-TL] [LOC] |
| Creek / river | The creek across the middle | Medium | [QL 5/15] [HP-TL] |
| Waterfall | Waterfall with mist and a camo; good hiding and sniping spot | Medium | [QL 3/15] [HP-TL] |
| Fuel rod, rockets | Their spawns | Medium | [QL 4/15] [HP-TL] |
| Blue hill | A hill on the blue side | Low | [QL 2/15] |

Remake, do not use: Reach Ridgeline HUD names Upper/Lower/Outer Red Base, Red Foothill, Overlook, Red Encampment, South Ridge, River, Upper/Lower/Outer Blue Base, Blue Foothill, Waterfall Path, Blue Encampment, North Ridge [HP-RL].

## 12. Ice Fields (icefields)

Layout: a base at each end; two tunnels lead to a center bridge with the main overshield, a rocket launcher and a fuel rod; two teleporters under the bridge with camo or OS near them; small cliffs along the bridge reached by each base's teleporter; a middle rock; ice puddles [HP-IF]. Scenario: OS and rockets on the bridge top at z 9, the random power-ups at z 4 under it [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Top mid (top middle; "top middle bridge") | Top of the center bridge: OS, rockets, fuel rod | High | [QL 8/11] [HP-IF] [LOC] |
| Bottom mid (bottom middle) | Under the bridge (teleporters, random power-ups) | High | [QL 9/11] [HP-IF] [LOC] |
| Middle bridge, top bridge | The bridge itself | Medium | [QL 5/11] |
| Ice cave, ice tunnel | One of the tunnels toward the middle; which one is unverified | Medium | [QL 6/11] |
| Portal (red portal, top portal, "through portal") | Base teleporters to the cliffs, and the ones under the bridge | Medium | [QL 11/11] [HP-IF] |
| Sniper spawn | Snipers on the bridge top (z 8.7 [LOC]) | Medium | [QL 4/11] [LOC] |
| Front door | Base front entrance | Low-Medium | [QL 3/11] |
| Main hill | A hill "that leads to the top middle" | Low | [QL 2/11] |
| Middle rock | Rock island in the middle that can be climbed to snipe | Suggested | [HP-IF] |

Remake: none listed.

## 13. Death Island (deathisland)

Layout: island with a base on each side; each base has two teleporters, one to a Shade gunner outcrop and one to a platform on top with two Banshees, a Ghost and a sniper rifle; a permanently closed hatch in the center with OS, rocket launcher, shotgun, fuel rod; trees by the bases; beaches; caves [HP-DI].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Top portal (Banshee portal) | Base teleporter to the top platform with the Banshees and sniper | High | [QL top portal 6/6, Banshee portal 2/6] [HP-DI] |
| Shade portal | Base teleporter to the Shade outcrop | Medium-High | [QL 4/6] [HP-DI] |
| Portal exit, main portal | Teleporter exits | Low | [QL 2/6] |
| Top mid (top middle) | Center high ground (fuel rod "top middle"); likely the hatch | Medium | [QL 3/6] [HP-DI] |
| Beach ("our beach") | Shore by each base | Low-Medium | [QL 3/6] |
| Side tunnel | A tunnel on the side route | Low | [QL 1/6] |
| Hatch, cave | Center hatch; caves near the fuel rod spot | Suggested | [HP-DI] |

Remake: none listed.

## 14. Danger Canyon (dangercanyon)

Layout: long winding canyon with bases at the ends; a tunnel system with six ways in and out, rockets and fuel rod inside it; a central room that leads to the bridges; on the far side of the bridges a ridge with sniper, pistol, frags and an overshield; one teleporter pair [HP-DC] [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Tunnels, middle tunnel | The tunnel system; its middle part | High | [QL tunnels 7/7, middle tunnel 4/7] [HP-DC] |
| Middle room | Central room that accesses the bridges | Medium-High | [QL 3/7] [HP-DC] |
| Top mid, bottom mid | Upper and lower middle of the map | Medium | [QL 7/7, 4/7] |
| Sniper spawn (snipe spawn) | Sniper on the ridge past the bridges, and the two by the bases | Medium | [QL 4/7] [HP-DC] [LOC] |
| Middle power-ups | Random power-up low in the middle (z -7.4 [LOC]) | Low-Medium | [QL 3/7] [LOC] |
| Bridges, ridge | The middle bridges; the ridge across them (OS and sniper) | Medium | [QL bridge 2/7] [HP-DC] |
| Fuel rod, rockets | In the tunnels | Medium | [QL 6/7] [HP-DC] |

Remake: none listed.

## 15. Rat Race (ratrace)

Layout: circular map of halls with teleporters; central elevated tunnels entered by a teleporter or an inclined ramp; two drop holes from the tunnels into the enemy side, usually used with camo or OS [HP-RR]. No rockets or snipers [MW-RR 0:16].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Tunnels | The central elevated tunnels; controlling them controls partner spawns | High | [MW-RR 3:32] [ZY] [HP-RR] [QL 2/3] |
| Top (top room) | Upper area near the tunnels | Medium | [MW-RR 2:09] [HMG "Top Room"] |
| Cloak, under cloak (camo) | Camo spawn and the floor under it (camo respawns every 90 s here) | Medium | [MW-RR 1:36, 6:10] [QL 2/3] |
| OS, under overshield | Overshield spot and under it | Medium | [MW-RR 4:19-4:34] [HP-RR] |
| Shields | A spawn MW calls the worst on the map; spot unverified | Low | [MW-RR 1:21, 3:48] |
| Dark, dark portal | A dark area and its teleporter | Low | [MW-RR 3:48] |
| OS port (red port, red portal) | Teleporter by the OS | Low | [MW-RR 2:59] |
| Big ramp | The ramp up toward the tunnels (a random spawn spot at its bottom) | Low | [MW-RR 6:41] [HP-RR] |
| Dance floor | Heard in two comms videos; spot unverified | Low | [QL 2/3] |
| Portal, camo hallway, camo cave | Names on the HMG wiki, seen only through search summaries | Low (unverified) | [HMG] |

The LSR clan published a "Ratrace Callouts" video (Halo PC) that could not be read [LSR-RR].

## 16. Wizard (wizard)

Layout: circular, four-fold symmetric UNSC structure; a base at each end with the flag behind a stone slab, a ladder up, a health pack above it, grenades below; a small platform ahead of each base; a central platform; camo on a slab and OS behind a slab on the sides; four teleporters [HP-WIZ] [LOC]. Zyos: callouts are hard here because the map is symmetric [ZY].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Dark camo, light camo | The two camo spots told apart by lighting (the only reliable callouts per Zyos) | Low-Medium | [ZY] |
| Up top, top | The upper level where the power-ups are; "get up top" | Low | [MW-WIZ 0:17] |
| Portal | Teleporter (a spawn spot) | Low-Medium | [MW-WIZ 0:17] [HP-WIZ] |
| Nades (frags, plasmas) | Grenade spawn below each base (a spawn spot) | Medium | [MW-WIZ 0:33, 1:35] [HP-WIZ] |
| Ramp(s) | Ramps up to the upper level (spawn spots at the bottom) | Low | [MW-WIZ 0:33] [HP-WIZ] |
| Powerup / OS / camo | Power-ups on all four sides | Medium | [OKOM "Powerup"] [HP-WIZ] |
| Suggested: red/blue + light/dark + item | e.g. "red light camo", "blue dark OS", "red ladder", "blue portal", "mid" for the central platform | Suggested | [HP-WIZ] |

Remake, do not use: Halo 2 Warlock [HP-WIZ].

## 17. Longest (longest)

Layout: two long hallways with a base at each end; two ramps per side up to a catwalk on the interior wall; the first platform has camo or OS depending on which base is behind you; holes in the walls and floor [HP-LON]. Scenario: OS at (0.4, -14.8) and camo at (-2.2, -14.3), both at z 2.1 near the middle [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Camo, OS | The two power-up platforms | Medium | [OKOM] [HP-LON] [QL 1] |
| Bottom camo, bottom OS | Floor under each power-up | Low | [OKOM] |
| Red flag, blue flag | Flag stands at the ends | Low (generic) | [QL 1] |
| Suggested: camo side, OS side, camo ramp, OS ramp, catwalk, red hall, blue hall, wall holes | Descriptive names from the layout | Suggested | [HP-LON] |

Remake, do not use: Halo 2 Elongation [HP-LON].

## 18. Gephyrophobia (gephyrophobia)

Layout: a long bridge over a canyon between the bases; three levels (bottom floor of the bridge, top floor of the bridge, and two ledges on the canyon sides reached by teleporters in each base); a main support tower in the middle [HP-GEP]. Zyos: teleports at the back of each base lead to corridors on both sides [ZY]. Scenario: OS at the center (26.8, -72.2) high, rockets on the bridge at y -44 and -100 [LOC].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Bridge (left side bridge, right side bridge) | The bridge lanes | Medium | [QL 4/5] [HP-GEP] |
| Ledge(s) | Canyon-side ledges reached by teleporter (sniper lanes) | Medium | [QL 1/5] [HP-GEP] [ZY] |
| Top portal | Base teleporter up to the ledges | Low | [QL 1/5] |
| Bottom mid, left tunnel | Lower middle; a tunnel | Low | [QL 1/5] |
| OS | Overshields (four spawns [LOC]) | Medium | [QL 4/5] [LOC] |
| Suggested: top bridge, bottom bridge, tower (center support), red ledge, blue ledge, red portal, blue portal | Descriptive names from the layout | Suggested | [HP-GEP] |

Remake: none listed.

## 19. Infinity (infinity)

Layout: two large bases with beacon towers (red and blue beams); Banshees on top, Shades below; a smaller secondary building; four suspended bridges in the center, the top two with a rocket launcher each, the lower two with teleporters at the ends; on one route to blue a maze-like structure "commonly called 'the pipes' by players" with a flamethrower, and next to it a sniper ledge; on the other route a large hill; on the routes to red a pair of short tunnels and a raised road [HP-INF]. The three captioned BTB videos contain no usable location names [QL].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| The pipes | Maze-like structure on a route to blue base | Low-Medium | [HP-INF] |
| Suggested: red beacon, blue beacon (bases), top bridges (rockets), low bridges (teleporters), big hill, red tunnels, sniper ledge, red road | Descriptive names from Halopedia's layout | Suggested | [HP-INF] |

## 20. Chiron TL-34 (putput)

Layout: nine small chambers connected by teleporters; each teleporter sits at the end of a red hallway leading into a larger room; one teleporter exit is a hidden alcove [HP-CHI]. Scenario has 30 teleporter pairs [LOC]. No community callouts were found; Zyos calls it the worst map and says it was almost never played competitively [ZY].

| Name | Where | Confidence | Sources |
|---|---|---|---|
| Suggested: room 1 ... room 9 (or by contents: "rocket room", "shotgun room", "flag room red/blue"), red hall, alcove | Number the chambers from the teleporter graph; name by the spawn item when there is one | Suggested | [HP-CHI] [LOC] |

## 21. Sources

Callout guide videos (captions read):
- [RR] R3aperRising, "Reaper Rising's Halo CE Callouts Guide" (chapters: Hang 'Em High 6:46, Damnation 9:35, Derelict 11:42, Prisoner 13:45, Battle Creek 15:50, Chill Out 17:33): https://www.youtube.com/watch?v=AiIM3LfA3Rc
- [MW-HEH] Missingno Wilder, "Hang 'Em High Callouts Halo 1": https://www.youtube.com/watch?v=FIHLwj0oCVI
- [MW-DAM] Missingno Wilder, "Damnation Callouts Halo 1": https://www.youtube.com/watch?v=1cdR4mQ89Ms
- [MW-PRI] Missingno Wilder, "Prisoner Callouts Halo 1": https://www.youtube.com/watch?v=TMq6i4cKj-U
- [MW-CO] Missingno Wilder, "Chill Out Callouts Halo 1": https://www.youtube.com/watch?v=DGplNYlW4Bc
- [MW-DER] Missingno Wilder, "Derelict Callouts Halo 1": https://www.youtube.com/watch?v=mpdQ7eFV2TU
- [MW-BC] Missingno Wilder, "Battle Creek Callouts Halo 1": https://www.youtube.com/watch?v=7QxsU37zo3w
- [MW-WIZ] Missingno Wilder, "Wizard Breakdown with Spawns": https://www.youtube.com/watch?v=vJduMBBvVdA
- [MW-RR] Missingno Wilder, "Rat Race Breakdown with Spawns": https://www.youtube.com/watch?v=6MJpsVBXhhs
- Other Missingno Wilder spawn breakdowns (not read; same series): https://www.youtube.com/@MissingnoWilder/videos
- [BTM-PRI] Beyond Entertainment (Team Beyond, xClicked), "Prisoner Callouts - Beyond the Map": https://www.youtube.com/watch?v=syEWz68G2gE
- [BTM-CO] Beyond Entertainment, "Chillout Callouts - Beyond the Map": https://www.youtube.com/watch?v=EydsnbU_YkE
- [GDD] GamersDon'tDie, "Halo 1 MCC - call outs" (Boarding Action comms): https://www.youtube.com/watch?v=4OIXCmiVtyc
- [LSR-RR] lsrclan, "=LSR= [ST] Ratrace Callouts" (not readable): https://www.youtube.com/watch?v=9uKLu4xVLxE

Guides and trick sites:
- [OKOM] Okom, "Halo CE: Weapon & Powerup Nading/Launching spots on the most common maps" (Steam, 2021-2022): https://steamcommunity.com/sharedfiles/filedetails/?id=2360594007
- [ZY] Zyos, "Halo CE: Multiplayer Guide" (Steam, 2020): https://steamcommunity.com/sharedfiles/filedetails/?id=2013123199
- [HN-*] halonades.com (Wayback copies, 2021): index https://web.archive.org/web/2021/https://www.halonades.com/ ; HMH https://web.archive.org/web/2021/https://www.halonades.com/hmh.html ; BC https://web.archive.org/web/2021/https://www.halonades.com/bc.html ; DAM https://web.archive.org/web/2021/https://www.halonades.com/dammy---camo.html and https://web.archive.org/web/2021/https://www.halonades.com/dammy---rockets--other.html ; PRI https://web.archive.org/web/2021/https://www.halonades.com/pris.html ; CO https://web.archive.org/web/2021/https://www.halonades.com/co.html ; DER https://web.archive.org/web/2021/https://www.halonades.com/derry.html
- [H1G] Halo1guide YouTube channel (nade-trick video titles): https://www.youtube.com/@Halo1guide/videos
- [HMG] Halo Multiplayer Guide wiki (blocked; seen via search summaries only): https://halo-multiplayer-guide.fandom.com/wiki/Prisoner , https://halo-multiplayer-guide.fandom.com/wiki/Battle_Creek , https://halo-multiplayer-guide.fandom.com/wiki/Rat_Race , https://halo-multiplayer-guide.fandom.com/wiki/Derelict
- MCC Multiplayer Map Book (contents not accessible): https://www.halopedia.org/Halo:_The_Master_Chief_Collection_Multiplayer_Map_Book

Halopedia map pages:
- [HP-HEH] https://www.halopedia.org/Hang_%27Em_High ; [HP-DAM] https://www.halopedia.org/Damnation ; [HP-PRI] https://www.halopedia.org/Prisoner ; [HP-CO] https://www.halopedia.org/Chill_Out ; [HP-DER] https://www.halopedia.org/Derelict ; [HP-BC] https://www.halopedia.org/Battle_Creek ; [HP-BA] https://www.halopedia.org/Boarding_Action ; [HP-SW] https://www.halopedia.org/Sidewinder ; [HP-TL] https://www.halopedia.org/Timberland ; [HP-IF] https://www.halopedia.org/Ice_Fields ; [HP-DI] https://www.halopedia.org/Death_Island ; [HP-DC] https://www.halopedia.org/Danger_Canyon ; [HP-RR] https://www.halopedia.org/Rat_Race ; [HP-WIZ] https://www.halopedia.org/Wizard ; [HP-LON] https://www.halopedia.org/Longest ; [HP-GEP] https://www.halopedia.org/Gephyrophobia ; [HP-INF] https://www.halopedia.org/Infinity_(Halo:_Combat_Evolved_map) ; [HP-CHI] https://www.halopedia.org/Chiron_TL-34
- Remakes: [HP-HN] https://www.halopedia.org/High_Noon ; [HP-PEN] https://www.halopedia.org/Penance ; [HP-SOL] https://www.halopedia.org/Solitary ; [HP-BCAN] https://www.halopedia.org/Battle_Canyon ; [HP-RL] https://www.halopedia.org/Ridgeline

Team comms, Quiet Leviathan channel (https://www.youtube.com/channel/UCyiTZ8ooA6aqJ4HDyim98xg), captioned videos used, by map (URL = https://www.youtube.com/watch?v=<id>):
- Sidewinder (21): 3jytYYp02rY 4I9wdIFeHO4 hn68UqKCP6s sPCCTJm7W2c z3lhGb3KSu8 fmWOfOn-Kvw gNns-5bi8_U 2j9-Wk9RxZA _D_DqerKl0Y R4LTvT6gCx8 vH0HFyP9hN4 A5fdmGEqv-E fShpvkTphQE JIzpfCjJ9FY Dr6H20N8ahs r84MaOqT5Xc 6zTTCiUV3Qo r_33lOZjCO0 3LfknnL1yOA yHx9mTFBhgU l2PebC9QsMo
- Timberland (15): N1hR4ia10D8 8E2yf1jeN1Q Cqu2caEcZv4 -ZfbforLwEc PcrJY-vbqZs 2SQlWEdSqLI veUEw-EcBSo DQZXwDSpTSM W2beDleCOKQ -dpyrEQTqKI APnmZPy7ouM hGXnxqQSMaY rj7imdFiuco 08xfRRy6jSA 1KxpH6Ew3yo
- Hang 'Em High (15): nyBIkZpq20o 1aRPGxVy6bQ xhvuVsJAdnM ww7jA0Yx1lc 3UAd2LyYFBA S2rGtldHJK4 xBa58Z5qVIc D-bwVQSH7Ns D_7_W5kayLo Xa4VWEbQrcQ 4PCt84b2wqI EMAVXi7Rdyw PL09hiCchxQ Mhvr7SC22ss bej8guylzWA
- Ice Fields (11): GFyWtuQJROs M-yc5qr1USM 39l9a_9Z_Hc f2HZOzNyS_g B4vRI80RH3g m-CazQUQDkk KCU7Q-34m4I ezRJH1d-nuY fkvPR9hX7dw MePP3yMlKBM RLz6DIb5AZ0
- Boarding Action (10): oIyfZPji1r4 6ybC_KTaE2k Zmjw_1f6_AE d2JkICHqucY Gg9W3wGMVSE XuhF10Eh5xU vU3SZz4JZ94 rtvToA0IXas MkXneEaHr0A rClm_GyveVY
- Danger Canyon (7): vObF93hoYT0 HTMkrvmej0Q poaLaLfwMjc CR8iXnl0YF0 0CdIXYXuzT8 PVS63Ko1qow 00q6LHu3GoU
- Death Island (6): W-7b4qq1qbI LPNbaIT3hBo IwqcQGzDTZg FVe1ogpq07U f8-Eh1CxxmE I0yR7viVczU
- Gephyrophobia (5): a-fcZ7bSFIM DOGAVoBKbEY jhR45FFoaP4 L2-PTg-B-GU UE23-Nz5Fk4
- Battle Creek (4): 90Xe5c1cZ1k 1jfgszinikU 500TkjVuTFE OphcuJU2VmA
- Rat Race (3): Scb8vOVIKBs CaMKGiT3w2Q PqPjL0t4KJ0
- Infinity (3): WBEDeJgvWYg ePXBpIeujoo NSPoE6dWtCI
- Damnation (1): ZAlu7kGPVZQ ; Derelict (1): K1iQDF6ZTXw ; Prisoner (1): xeDHL2QVeD0 ; Longest (1): WRT2sTVXuGE

Local ground truth:
- [LOC] `<project folder>\maps\<map>\objects.json` (from the HEK scenario tags). CTF flag `id` is the team index (0 red, 1 blue; checked against Blood Gulch). Equipment lists include every gametype's placements, so one item can appear at several spots.

## 22. Open items

- Read the MCC Multiplayer Map Book callout overheads if a copy turns up; it is the only source with official callouts for every PC/BTB map.
- Place the "spot unverified" names (Sidewinder keyhole and first/second portal, Timberland dark side, Ice Fields ice cave, Rat Race shields and dance floor) by watching the matching QL video at the cited timestamps.
- Bind each name to a zone in `maps\<map>\callouts.json` using the spawn items and flags in `objects.json`, as done for Blood Gulch.
