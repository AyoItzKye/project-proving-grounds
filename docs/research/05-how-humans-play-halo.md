# 05 - How Humans Play Halo Multiplayer (MCC: CE, 2, 3, ODST, Reach, 4)

Research for PvP bots that must read as real players in Slayer and CTF, plus a per-team "AI director" acting as team comms.

Conventions in this document:
- Every non-obvious claim has a source URL in brackets.
- **UNVERIFIED** = from community memory, forum anecdote, or my own inference; test in-game before encoding as a hard rule.
- **DERIVED** = arithmetic I did from sourced numbers.
- Many numbers come from Halopedia (a fan wiki) and some of its own entries are marked "citation needed". Treat wiki numbers as strong defaults, not ground truth. The bot project should verify every timer and damage value against the actual MCC build (tag data or in-game stopwatch tests).

---

## 0. Scope note: which games have PvP in MCC

- Halo 3: ODST in MCC is campaign plus Firefight; Firefight arrived later and the original ODST PvP disc was just Halo 3 multiplayer [https://en.wikipedia.org/wiki/Halo_3:_ODST]. Whether MCC's ODST entry has any PvP maps is **UNVERIFIED**; treat ODST PvP as "Halo 3 rules" until confirmed.
- Halo 2 in MCC has two multiplayer flavors: Halo 2 Classic and Halo 2 Anniversary (H2A), which use different sandboxes. Button combos matter for Classic only (section 1.5).
- Reach in MCC runs the Title Update (TU) rules in almost all modes [https://halopedia.org/Halo:_Reach_Title_Update].

---

## 1. Movement tech

### 1.1 Base movement numbers (world units per second)

| Game | Run speed | Jump velocity | Notes | Source |
|---|---|---|---|---|
| CE | 2.25 wu/s forward; 2.0 backward and side strafe | 2.1 wu/s | CE engine reference lists side strafe slower than forward | [https://www.halopedia.org/Master_Chief_(gameplay)], [https://nikon.bungie.org/misc/hek_tutorial/references/general/halo_player_stats.html] |
| Halo 2 | 2.25 | 3.08 | | [https://www.halopedia.org/Master_Chief_(gameplay)] |
| Halo 3 | 2.25 | 3.08 | MLG v8 settings ran 110% speed | [https://halopedia.org/Spartan_(multiplayer)], [https://www.halopedia.org/MLG_(playlist)] |
| ODST (Rookie) | 1.85 | 2.6 | Campaign character, not PvP | [https://halopedia.org/ODST_(player_character)] |
| Reach Spartan | 2.2 | not given | Sprint = 1.623x run | [https://halopedia.org/Spartan_(multiplayer)] |
| Reach Elite | 2.6 | 2.65 | Sprint = 1.4x run (3.64 wu/s) | [https://halopedia.org/Elite_(multiplayer)] |
| Halo 4 | not found | not found | Sprint permanent on left stick click; competitive (Throwdown) ran 110% speed | [https://www.gamespot.com/articles/the-evolution-of-halo-4s-multiplayer/1100-6372279/], [https://mp1st.com/news/halo-4-team-throwdown-playlist-full-details] |

Bot implication: jump arcs differ hugely between CE (2.1) and H2/H3 (3.08). A jump-height model tuned for H3 will look wrong in CE. Read speeds from the engine at runtime rather than hardcoding.

### 1.2 Strafing

- **What strafing is for:** dodging fire in close and mid-range fights, being unpredictable, while still returning fire. A Bungie-forum guide breaks a good strafe into: assess the fight (can I win it?), be unpredictable, keep returning fire [https://www.bungie.net/en-US/Forums/Post/1480128].
- **CE strafe:** CE movement is widely described as near-instant acceleration with little momentum, so the dodge value comes from rapid, unpredictable direction changes rather than momentum tricks. **UNVERIFIED** (community description; no primary source found). Side strafe is slightly slower than forward run (2.0 vs 2.25) [https://nikon.bungie.org/misc/hek_tutorial/references/general/halo_player_stats.html].
- **H2/H3 "strafe acceleration":** players describe H2/H3 strafing as having more ramp-up than CE, which makes long strafes more readable and short "AD-AD" taps less effective. **UNVERIFIED**; measure the acceleration curve in-engine.
- **Strafe while aiming:** experienced players strafe only as hard as they can still keep the reticle on target. Burst and semi-auto weapons punish over-strafing more than automatics [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/movement-mastery] (Halo 5 guide, principle applies). Moving while firing the H2 BR fires the burst at different angles, reducing accuracy [https://www.halopedia.org/H2:Battle_Rifle].
- **Crouch strafing:** bobbing crouch during a fight changes head height and throws off headshots [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/movement-mastery].

Human strafe pattern model (for bots, based on the above plus common play; **UNVERIFIED** as numbers):
- Low skill: strafes in long, regular sweeps, or stands still and shoots ("standing still while shooting makes you an easy target" is a top beginner mistake [https://sportskeeda.com/esports/top-5-tips-newcomers-improve-gameplay-halo-infinite]).
- Mid skill: alternates directions on a semi-regular rhythm (0.3 to 0.8 s per leg), occasional jump.
- High skill: irregular leg lengths, mixes crouch and jump, strafes toward cover, uses strafe to "peek" so only part of the body is exposed.

### 1.3 Jumping, crouch-jumping, crouching

- **Crouch-jump:** jump, then crouch in midair; the hitbox shrinks so feet clear a ledge that a plain jump would clip. It does not add height, it lifts the feet [https://www.halopedia.org/Crouch_jumping]. Repeated crouch/uncrouch in air can add hang time [https://www.halopedia.org/Crouch_jumping]. Standard way humans reach higher ledges in every Halo.
- **Reach "spring jump":** land crouched, then jump while releasing crouch; a Steam user estimates 5 to 15% more air and says it does not work in CE to H3 or ODST [https://steamcommunity.com/app/976730/discussions/0/2921102177244094642]. **UNVERIFIED** magnitude.
- **Crouch to hide from radar (CE):** in CE multiplayer you do not appear on enemy motion trackers while crouched (still or moving) or while standing still [https://www.halopedia.org/Motion_tracker]. In later games, crouch-walking also keeps you off radar; **UNVERIFIED per game**, but it is how H2, H3 and Reach players stalk (well-known community behavior).
- **Crouch to hide name / deny hitmarkers:** players crouch behind cover so their name tag or shield flare is not visible. **UNVERIFIED** as a mechanic (name tags appear when the reticle is over a visible player); the behavior of crouching behind low cover is real and common.
- **Jump shots:** jumping in a mid-range duel changes head height and breaks the opponent's headshot line; overused by low/mid players, used sparingly by high players because it makes your path predictable in the air. **UNVERIFIED** (general community knowledge).
- **Grenade jumping:** explosions boost you; in H3, crouch-jumping while firing a rocket below yourself avoids death; frags give a higher boost than plasmas [https://www.halopedia.org/Explosive_jumping]. Rare in normal matchmaking; low priority for bots except as a "trick" personality.
- **Tricks and jumps:** every competitive map has known trick jumps (for example, crouch-jumping from below Lockout's sniper spawn onto the ramp landing [https://www.halopedia.org/Lockout]). These should be stored per map as navmesh "jump links" with a required technique tag (plain, crouch, sprint-jump, grenade).

### 1.4 Peeking corners

- High players shoot first by pre-aiming the head/chest line before rounding a corner [https://ru.steelseries.com/blog/5-tips-improve-any-fps-102], and landing the first shot is a real edge; if you get hit first, back off and recharge [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/choose-your-battles].
- The "strafe peek" (strafe out, shoot, strafe back to cover) lets a player trade shots while only partly exposed, and their shields can start recharging the moment they break line of sight. **UNVERIFIED** (general FPS/Halo practice).

### 1.5 Halo 2 button combos (Classic only)

| Combo | Effect | Source |
|---|---|---|
| BXR | Melee, then reload-cancel (X), then fire: cancels the end of the melee animation so the shot comes out immediately. Classic use: melee plus BR burst or sniper shot | [https://www.halopedia.org/BXR], [https://www.halopedia.org/H2:Battle_Rifle] |
| Double Shot | Skips the delay between BR bursts | [https://www.halopedia.org/H2:Battle_Rifle] |
| BXB | Double melee in quick succession | [https://www.halopedia.org/Button_combo] |
| X after melee/grenade | Cancels melee and grenade timers (off-host) | [https://www.halopedia.org/Button_combo] |
| YY (double weapon switch) | Cancels reload/melee animation; can fire sooner | [https://www.halopedia.org/Button_combo] |
| Overheat reset | Overheating a plasma weapon resets shoot/melee/grenade timers, allowing quick double grenades | [https://www.halopedia.org/Button_combo] |

MCC status:
- Halo 2 Classic in MCC was shipped untouched apart from 60 fps and 1080p; combos were expected to work [https://mp1st.com/news/learn-every-classic-halo-2-button-glitch-master-chief-collection-arrives].
- H2A multiplayer: combos not expected; a Steam user says they only work in Classic [https://steamcommunity.com/app/976730/discussions/0/3581993633008438327]. Other users report inconsistent multiplayer timing [https://steamcommunity.com/app/976730/discussions/0/4203492762813859359]. **UNVERIFIED**, test in the current build.
- Bungie considered button glitching cheating "by the letter of the law" [https://www.halopedia.org/Button_combo]; button combos were removed in Halo 3 [https://www.halopedia.org/H2:Battle_Rifle], and Halo 3's own BXB-style double melee was patched out in February 2008 [https://www.halopedia.org/Button_combo].
- Bot recommendation: only "veteran H2 Classic" personalities use BXR, and not perfectly (humans botch them). If the BR is BXR'd incorrectly it fires only one or two bullets [https://www.halopedia.org/BXR].

### 1.6 Reach armor abilities (base values; TU changes noted)

| Ability | Duration | Recharge | Human use | Source |
|---|---|---|---|---|
| Sprint | about 4 s | not given | Rotate between positions, escape, close distance for a melee; cannot fire while sprinting | [https://www.halopedia.org/Armor_ability] |
| Jet Pack | while held, drains faster when sustained | not given | Reach high ground, dodge grenades/vehicles, vertical flanks | [https://www.halopedia.org/Armor_ability] |
| Armor Lock | max 5 s | 3 s delay, then 11 s | Block a melee or rocket, stop a vehicle, stall for teammates; cannot move. TU: damage taken drains AA energy, nearby grenade ends lock, does not save from a plasma stick | [https://www.halopedia.org/Armor_ability], [https://halopedia.org/Halo:_Reach_Title_Update] |
| Active Camo | 15 s | 15 s from empty | Camping power spots, sniping; fades while running; jams radar with false dots within 25 m. TU cut duration "substantially" (exact value **UNVERIFIED**) | [https://www.halopedia.org/Armor_ability], [https://halopedia.org/Halo:_Reach_Title_Update] |
| Evade | 2 evades per charge | 4 s | Dodge out of a duel or grenade, break lock-ons | [https://www.halopedia.org/Armor_ability] |
| Drop Shield | 15 s or until 3/4 meter | new one 20 s later | Heal self/allies mid-fight, block shots | [https://www.halopedia.org/Armor_ability] |
| Hologram | 10 s life | 7 s | Bait: send decoy down a lane to draw fire and reveal enemies | [https://www.halopedia.org/Armor_ability] |

MLG Reach v6 placed Jet Pack and Evade as map pickups (respawn 34 s after holder death) and made Sprint the start ability on Sprint gametypes [https://www.halopedia.org/MLG_(playlist)].

Reach health detail: health regenerates "to the nearest 1/3"; beyond that you need a health pack [https://shacknews.com/article/65493/a-beginners-guide-to-halo]. Humans visibly detour to health packs after a fight.

### 1.7 Halo 4 loadouts, sprint, thruster

- Sprint is permanent [https://www.gamespot.com/articles/the-evolution-of-halo-4s-multiplayer/1100-6372279/].
- Loadout parts: primary (AR default, BR, DMR, Storm Rifle, Carbine, Suppressor, Lightrifle), secondary (Magnum, Plasma Pistol, Boltshot), grenades (Frag, Plasma, Pulse), armor ability (Promethean Vision, Thruster Pack, Jet Pack, Hologram, Hardlight Shield, Active Camo, Autosentry, Regeneration Field), tactical package (Shielding, Mobility, Resupply, AA Efficiency, Grenadier, Firepower, Requisition, Wheelman, Fast Track, Resistor), support upgrade (Ammo, Dexterity, Sensor, Awareness, Explosives, Ordnance Priority, Stability, Gunner, Stealth, Nemesis, Drop Recon, Recharge, Survivor) [https://www.halopedia.org/H4:Loadout].
- MCC ranked playlists force premade loadouts [https://www.halopedia.org/H4:Loadout].
- Thruster Pack launches you several feet horizontally [https://www.gamespot.com/articles/the-evolution-of-halo-4s-multiplayer/1100-6372279/]; humans use it to dodge into cover or out of a sword/shotgun lunge.
- Ordnance: map ordnance on rotations, plus personal ordnance earned by medals filling a meter [https://www.gamespot.com/articles/the-evolution-of-halo-4s-multiplayer/1100-6372279/]. Instant respawn option exists in Slayer [same source].
- Throwdown (competitive) BR start: BR, 2 frags, Resupply; personal ordnance on d-pad (Thruster, Hologram, Hardlight Shield); 110% speed, 200% overshield; railgun, sniper and sword on 2-minute timers [https://mp1st.com/news/halo-4-team-throwdown-playlist-full-details].

---

## 2. Gunplay

### 2.1 Utility weapon shots-to-kill (STK) and kill times

| Game | Weapon | STK on full-shield player | Mechanics | Optimal kill time | Source |
|---|---|---|---|---|---|
| CE | M6D Pistol | 3 (2 body to pop shields, head on 3rd); 5 body | 75 shield points; pistol can strip shields in 3 shots, a 3rd shot to head still kills due to engine behavior. RoF about 3.33/s (tick rounding). Spread only grows while trigger held; tapping keeps it accurate | about 0.6 s (DERIVED: 2 intervals at 3.33/s) | [https://www.halopedia.org/CE:Pistol], [https://almarsguides.com/computer/games/halomasterchiefcollection/misc/lists/weapontiers/halocecampaign/] |
| H2 Classic | BR55 | 4 bursts if no bullets miss | Burst weapon; moving while firing spreads the burst. BXR and double shot raised its effective power | **UNVERIFIED** | [https://www.halopedia.org/H2:Battle_Rifle] |
| H3 | BR55HB | 4 bursts (last bullet a headshot) | 70 shields; 12 bullets = 72 damage, the last third of a bullet bleeds into the head. BR is not hitscan in H3. Spread: bullet 1 off 0 to 0.15 deg, bullet 3 up to 0.38 deg | **UNVERIFIED** (no sourced RoF) | [https://giantbomb.com/wiki/Concepts/Four_Shot], [https://www.halopedia.org/Headshots], [https://halo.bungie.org/bwu/index.html?item=182] |
| H3 | BR combo | 2 bursts + melee ("bang-bang-whack") | Melee finishes the weakened shield | | [https://giantbomb.com/wiki/Concepts/Four_Shot] |
| Reach | M392 DMR | 5 (last to head) | Shields break on 4th shot; TU gives melee bleedthrough so 3 DMR + melee kills (**UNVERIFIED** count, Giant Bomb overview). Bloom: pause for reticle to contract at range, fire as fast as possible point-blank. TU 85% bloom default; Zero Bloom in MLG | depends on pacing | [https://www.halopedia.org/M392], [https://halopedia.org/Halo:_Reach_Title_Update] |
| Reach | Magnum (TU) | 4 minimum with bleedthrough under ZB | | | [https://halopedia.org/Halo:_Reach_Title_Update] |
| Reach | Needle Rifle (TU) | 6 minimum | Removed from TU Slayer Pro loadouts | | [https://halopedia.org/Halo:_Reach_Title_Update] |
| H4 (launch) | BR85 | 5 bursts (13 bullets) | Hitscan, no bloom, vertical recoil | | [https://www.halopedia.org/BR85HB_SR_Battle_Rifle] |
| H4 (post Turbo update, likely MCC) | BR85 | 4 bursts (11 bullets, last head) | Fire rate slowed to match DMR | | [https://www.halopedia.org/BR85HB_SR_Battle_Rifle], [https://mp1st.com/news/halo-4-current-state-of-weapon-tuning-primaries-tweaked-to-compete-with-dmr] |
| H4 | DMR | kill time kept unchanged in tuning; exact STK **UNVERIFIED** (commonly 5) | | | [https://mp1st.com/news/halo-4-current-state-of-weapon-tuning-primaries-tweaked-to-compete-with-dmr] |
| H4 | Carbine | 7 after tuning | | | [same] |

Which H4 tuning MCC uses: **UNVERIFIED**; assume post-Turbo and verify.

### 2.2 Shields, health and bleedthrough

| Game | Shields / health | Recharge delay | Full recharge | Bleedthrough | Source |
|---|---|---|---|---|---|
| CE | 75 / 75 (citation needed) | 5 s after last hit | 4 s | Pistol 3rd-shot headshot kills even when that shot only empties shields (engine quirk) | [https://www.halopedia.org/Energy_shielding], [https://www.halopedia.org/CE:Pistol] |
| Halo 2 | not given | 4.25 s | 1.75 s | Generally said to have none for headshots (shield must be fully down). **UNVERIFIED** | [https://www.halopedia.org/Energy_shielding] |
| Halo 3 | 70 / 45 (citation needed) | 5 s | 2 s | Yes: overflow carries into health; sniper round about 80 damage, 70 to shield, 10 to body | [https://www.halopedia.org/Energy_shielding], [https://www.halopedia.org/Headshots] |
| Reach (vanilla) | Elites more shield, less health than Spartans | not given | not given | No (except sniper); melee on low shield only emptied shield | [https://www.halopedia.org/Headshots], [https://halopedia.org/Halo:_Reach_Title_Update] |
| Reach (TU, MCC default) | | | | Small bleedthrough restored for weapons and melee | [https://halopedia.org/Halo:_Reach_Title_Update] |
| Halo 4 | no health bar shown | not given | not given | **UNVERIFIED** | [https://www.halopedia.org/Energy_shielding] |

General rule (all games): headshots instantly kill unshielded targets but do no extra damage to shields [https://www.halopedia.org/Headshots]. So humans body-shot until the pop, then aim for the head. Players usually land 3 chest bursts then aim up for the 4th [https://giantbomb.com/wiki/Concepts/Four_Shot]. Bots should do the same: aim center-mass while shielded, raise to head when the shield pops (visible pop effect is the cue humans use).

Sniper rifles: sniper headshot kills through shields in H3 (bleedthrough) and Reach (sniper exception) [https://www.halopedia.org/Headshots]. CE sniper does 101 damage per shot, fires 2 rounds/s, 4-round magazine, zoom 2x to 10x in MCC [https://www.halopedia.org/CE:Sniper_Rifle]. H2 sniper: 45 damage "x2 vs shields", 0.5 s recovery [https://www.halopedia.org/H2:Sniper_Rifle]. One-shot headshot on full shields in CE and H2 is **UNVERIFIED** here (widely believed true).

### 2.3 Melee rules per game

| Game | Rule | Source |
|---|---|---|
| CE | No lunge. Standing melee takes 75% of shields; running melee removes all shields; jumping melee removes all shields plus one health bar. Two players running into each other with melee: kill. Simultaneous melee trade deaths go to "The Guardians" | [https://www.halopedia.org/Melee] |
| H2 | Lunge added, range shorter than CE. Stationary melee weakest (some weapons 6 to kill), running about half shields (3), jumping almost all (2). Melee while dual-wielding drops the left weapon | [https://www.halopedia.org/Melee] |
| H3 | Two melees to the body kill a normally shielded player. After title update, two unshielded players melee-trading both die. Assassination from behind = one-hit | [https://www.halopedia.org/Melee] |
| Reach | Weaker melee than earlier games; MLG v6 ran 75% melee damage. "Clang" when melees meet (both bounce). Hold melee from behind for an assassination animation (40+ animations; stealable). TU adds melee bleedthrough | [https://www.halopedia.org/Melee], [https://www.halopedia.org/MLG_(playlist)], [https://halopedia.org/Halo:_Reach_Title_Update] |
| H4 | Melee and assassinations return; details not sourced | [https://www.halopedia.org/Melee] |

Shoot-then-melee is the classic Halo close-range finish: whittle shields to near zero, then melee [https://stories.pcgamer.com/halo-infinite-multiplayer-guide/index.html]. Players with a shotgun or sword hunt corners [https://shacknews.com/article/65493/a-beginners-guide-to-halo].

Assassination behavior: in Reach and H4, holding melee for an animation is a deliberate "style" or taunt choice; humans sometimes get killed mid-animation. Good personality hook.

### 2.4 Grenades and combos

- **Grenade openers:** throw grenades where enemies are likely to be, or just before a push, to pop shields before the headshot; do not throw them without a target [https://primagames.com/?p=20998] (H4 Haven guide).
- **Spawn grenades:** after a kill, learn where the enemy respawns and pre-throw grenades there [https://primagames.com/?p=20998].
- **Death grenade:** instead of a hopeless retreat, throw a "lucky grenade" or dump damage before dying so teammates can finish [https://shacknews.com/article/65493/a-beginners-guide-to-halo].
- **Noob combo:** overcharged Plasma Pistol strips shields, then BR headshot (H2) or any finisher [https://www.halopedia.org/H2:Battle_Rifle], [https://giantbomb.com/wiki/Concepts/Four_Shot].
- **Plasma stick:** a stuck plasma grenade is a kill; Reach and H3 have medals and achievements for sticking the flag carrier [https://www.halopedia.org/Capture_the_Flag]. Armor Lock does not save a stuck player in TU Reach [https://halopedia.org/Halo:_Reach_Title_Update].
- **Panic grenade:** low-skill humans throw grenades at their own feet or in close duels when they are losing. **UNVERIFIED** (common observation); great "human" tell for bots.

### 2.5 Power weapon handling

- Rockets travel slowly; use close to medium range, switch to BR at long range [https://futurefive.com.au/story/halo-3-9-t-op-tips].
- Give the sniper to your best sniper; carry one long-range and one short-range weapon [https://shacknews.com/article/65493/a-beginners-guide-to-halo].
- With a sniper or DMR, take high ground overlooking the map; with shotgun or sword, hunt corners [https://shacknews.com/article/65493/a-beginners-guide-to-halo].
- Power weapon holders are high-priority callouts ("Sniper" means enemy holds it; "Snipe down" means it is on the ground) [https://shacknews.com/article/65493/a-beginners-guide-to-halo].

---

## 3. Map control and macro

### 3.1 Power weapon and powerup timers

**Halo 3, MCC matchmaking (community stopwatch test, 2015)** [https://www.bungie.net/Ne/Forums/Post/106060001?page=0]:
- All maps: Power Drain, Regen, Bubble Shield 1:00; Overshield and Camo 3:00; BRs/Carbines 15 to 30 s.
- Pick-up rule: stand still for a full second when picking up a weapon or you "dirty" it and delay the next spawn.

| H3 map | Sniper | Rockets | Other |
|---|---|---|---|
| Assembly | 3:00 | 2:00 | Hammer 3:00, Sword 2:30, Shotgun 3:00 |
| Blackout | 3:00 | | Sword 2:30, Shotgun 3:00 |
| Citadel | 3:00 | 2:00 | Shotgun 3:00 |
| Cold Storage | 2:00 | 2:00 | Shotgun 2:00 |
| Construct | 3:00 | | Laser 2:00, Sword 3:00 |
| Epitaph | | 2:00 | Hammer 3:00, Shotgun 2:00 |
| Foundry | 1:30 | 1:30 | Shotgun 2:00 |
| Ghost Town | 2:00 | 3:30 | Shotgun 3:00 |
| Guardian | 3:00 | | Hammer 3:00, Shotgun 3:00 |
| Heretic | | | Sword 3:00, Shotgun 2:00 |
| High Ground | 1:30 | 2:00 | Laser 2:00, Shotgun 1:30 |
| Isolation | 3:00 | 3:00 | Shotgun 0:30 |
| Last Resort | 2:00 | | Laser 2:00, Shotgun 1:30 |
| Narrows | 2:30 | 3:00 | Shotgun 2:00 |
| Orbital | 2:00 | 2:00 | Mauler 2:00 |
| The Pit | 2:00 | 3:00 | Sword 2:00, Shotgun 2:00 |
| Snowbound | 2:30 | | Laser 2:30, Shotgun 3:00 |
| Standoff | | 3:00 | Laser 3:00 |

**MLG settings (fixed drop-spawn timers)** [https://www.halopedia.org/MLG_(playlist)]:

| Item | H3 MLG v8 | Reach MLG v6 |
|---|---|---|
| Start | BR + 2 frags, no radar, 110% speed, 110% damage, 90% shield recharge | DMR + 2 frags, no radar, 110% jump, 150% gravity, 75% melee, 110%/120% speed |
| Sniper | 150 s drop | 118 s drop |
| Rockets | 180 s drop | 178 s drop |
| Powerups | all at 120 s | all at 120 s |
| Other | BR 10 s, frags 10 s, plasmas 30 s, PP 60 s, Carbine 90 s, Mauler 150 s | GL 118 s, PP 90 s, Shotgun 90 s, DMR 10 s, Needle Rifle 60 s, Magnum 60 s, nades 30 s, health pack 30 s |

Older H3 MLG announcement: rockets 3:00, snipers 2:30 constant timers; OS and camo every 2:00 after pickup [https://xboxaddict.com/news/9003/MLG-Playlist-is-Live-in-Halo-3.html].

**Halo 2:** power weapons like the sniper did not respawn while someone on the map held them, so there was no fixed timer to call [https://rampancy.net/comment/14611]. **UNVERIFIED** for H2 in MCC; H2A likely uses timers.

**Halo CE:** timer apps exist for CE sniper, rockets, OS and camo [https://mwm.ai/apps/vaders-timer-for-halo-1/912269452] but values were not found. CE camo lasts 45 s; H2 camo 45 s; H3 camo 30 s [https://www.halopedia.org/Active_camouflage]. CE per-map timers: **UNVERIFIED**, read from map tags.

**Halo 4:** ordnance on rotations and personal ordnance; Throwdown ran railgun, sniper, sword on 2:00 timers [https://mp1st.com/news/halo-4-team-throwdown-playlist-full-details].

Bot implication: drop-spawn and fixed timers are the whole point of "timing" in competitive Halo, because they make players converge on known spots at known times [https://www.halopedia.org/MLG_(playlist)]. The AI director should keep a per-match timer table, and individual bots should "know" it imperfectly by skill tier (section 7).

### 3.2 Spawns

**Halo 3 spawn logic (community testing, fyrewulff)** [https://halo.bungie.org/misc/fyrewulff_spawnsystem]:
- All spawn points start at a base weight of 1000.
- Positive: near your flag; a teammate on or near the spawn in the last 7 s (stronger if they just spawned, the "buddy spawn", strongest effect); your territory; initial team spawn area.
- Negative: enemy on or near the spawn in the last 7 s; teammate died near it in last 7 s; you spawned and died there within 7 s.
- Spawns ignore geometry and line of sight; a player is a sphere that influences spawns through walls.
- Standing in a spawn zone does not block enemies there if other spawns are available, and does not pull teammates there.

**Halo CE:** distance is the main factor; each spawn gets a percentage based on distance [https://halomaps.haloman30.com/index.cfm%3Fpage=topic&topicID=48897]. **UNVERIFIED** details.

**Spawn trapping / spawn pressure:** learn where opponents spawn after you kill them and pre-aim or pre-grenade there [https://primagames.com/?p=20998]. Bots exploiting a spawn system perfectly would feel unfair; only high-tier bots should do it, and with some error.

### 3.3 Positions, setups, rotations, trades

- **Hot spots / choke points:** high-traffic areas both teams contest [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/terminology] (page 403 to fetch; content via search snippet).
- **Power position hold:** put two players on the dominant high ground to pin enemies, others flank (H4 Haven example) [https://primagames.com/?p=20998]. Teams ahead switch to defensive holds; in Slayer, hold a defensible spot and keep line of sight with teammates [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/terminology].
- **Rotation:** H2 Midship "rotary" tactic: two pairs circle the outer ring in the same direction; pair a short-range with a long-range player [https://www.strategywiki.org/wiki/Halo_2/Midship].
- **Bait:** move forward to draw enemies out, then fall back to a position teammates hold [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/terminology]. Reach Hologram is purpose-built bait [https://www.halopedia.org/Armor_ability].
- **Retreat to recharge:** if the opponent hits first, retreat to let shields recharge [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/choose-your-battles]; running away "can sometimes be the best course of action" [https://shacknews.com/article/65493/a-beginners-guide-to-halo].
- **Chase or not:** chasing a weak enemy is often worth it because an escaped enemy recharges; do not follow them back toward their allies [https://gamerguides.com/halo-infinite/guide/multiplayer/getting-started/managing-and-capitalizing-on-ttk].
- **Team shot:** two or more players shooting the same target collapses kill time (two BRs can kill in roughly half the time). Explicit sourced definition not found; concept is core competitive Halo. **UNVERIFIED** wording.
- **Trading:** when a teammate dies, the next player immediately kills the weakened killer ("trade"), so the exchange is 1 for 1. Definition **UNVERIFIED** (no primary source found), but it is the reason good teams stay within a few meters of each other's sightlines.
- **Setup:** before a power weapon or powerup timer, the team positions around the spawn location 10 to 20 s early with sightlines on it. **UNVERIFIED** (no primary source found); timers make this possible [https://www.halopedia.org/MLG_(playlist)].

### 3.4 Known camping spots

- Lockout (H2): Sniper Tower, BR Tower, Library, Lift, Elbow; the first and second floors of Sniper Tower are the hottest area; the room below sniper is informally the "death chamber"; with a rifle, attack from BR tower [https://www.halopedia.org/Lockout], [https://www.halopedia.org/Talk:Lockout].
- Sniper tracking: a well-known Lockout match commentary notes the enemy sniper vanished from usual spots and turned up on BR tower, showing the value of tracking where the sniper is [https://halo.bungie.org/gameplay/stratguide/movies/ogre1_41-0.html].
- Bot implication: each map needs a hand-authored "spots" table: power positions, sniper perches, camp corners (shotgun/sword), health-pack detours (Reach), trick jumps. Casual human campers sit in exactly these well-known spots, so bots should too.

### 3.5 Communication and callouts

- Short calls with a location name: "One shot S2" = enemy with no shields on sniper tower second floor [https://shortlist.com/news/how-to-play-halo-like-a-pro].
- Reach death-marker callouts: "One" / "One-shot" at my X = enemy one shot from death where I died; "Snipe down" = sniper on the ground there; "Sniper" (no "down") = enemy holds it [https://shacknews.com/article/65493/a-beginners-guide-to-halo].
- Call where, who, and what weapon each enemy has [https://futurefive.com.au/story/halo-3-9-t-op-tips].
- Shield-state calls only mean something relative to the game's rules: newer titles stopped bleedthrough, older ones carry it [https://stories.pcgamer.com/halo-infinite-multiplayer-guide/index.html].
- "Cracked" (shield partly down) is used in Halo and Valorant comms; Halo-specific source not found [https://metabot.gg/en/valorant/guides/valorant-communication-callouts-guide]. Common Halo vocabulary (**UNVERIFIED** as formal standard): "cracked", "popped", "one shot", "he's weak/low", "full shields", "rockets up in 10", "camo taken", "two top mid", "on me", "pushing", "falling back", "flag's out/flag taken", "flag at mid", "carrier going left".

---

## 4. Capture the Flag

### 4.1 Flag rules per game

| Rule | CE | H2 (Classic / H2A) | H3 | Reach | H4 |
|---|---|---|---|---|---|
| Carrier can shoot | No | No | No | No | Yes: flag in left hand, M6H magnum in right (firing implied) |
| Flag melee one-hit kills full shields | No | Yes (default) | Yes (except overshield) | Yes (default) | Yes (default) |
| Voluntary drop | Yes (general rule) | Yes | Yes | Yes | No, cannot drop |
| Flag juggling | **UNVERIFIED** | Yes: jump, grab, drop before landing; slightly faster than carrying but reveals flag | **UNVERIFIED** | Killed: normal run speed returns only 1 s after dropping | Not possible |
| Carrier speed | **UNVERIFIED** | Slow walk; passenger seats only | Normal except Tank Flag variant (slow, tough) | **UNVERIFIED** | **UNVERIFIED** |
| Own flag home to score | Yes in base CTF ("must have your own flag") | Yes in Classic and H2A | Required in standard Multi Flag (inferred); "may capture when away" per Halopedia variant text, conflict | **UNVERIFIED** | No longer required |
| Return | Touch return in MCC CE gametypes that enable it | Touch return ("return on pickup") in H2A | Timed countdown; friendlies standing near speed it up | Timed; friendlies near speed it up (general rule) | Standing on flag does not speed return; timer shown in navpoint |

Sources: [https://www.halopedia.org/Capture_the_Flag], [https://www.halopedia.org/Flag], [https://www.halopedia.org/Flag_dropping], [https://www.halopedia.org/Multi_Flag_CTF], [https://www.halopedia.org/Flag_Returned], [https://halo.bungie.org/halobulletins/65] (H4 bulletin, quoted via search snippet; direct fetch failed).

General rules across games: dropped flag starts a return countdown; enemies picking it up again, even briefly, reset the countdown; CTF respawn timers are usually longer than Slayer; default score limit 3 [https://www.halopedia.org/Capture_the_Flag]. Flag carriers cannot pick up weapons in H2/H3 [https://www.halopedia.org/Multi_Flag_CTF]. In H3, sticking someone then grabbing the flag before the grenade pops credits a Flag Kill [https://www.halopedia.org/Flag].

Carrier waypoint visibility per game: **UNVERIFIED**; navpoints commonly appear in objective modes [https://www.halopedia.org/Navigation_point]. The bot must read this from the gametype settings at runtime.

### 4.2 Roles

Halopedia strategy and community practice:
- **Flag runner / puller:** grabs the flag. Learn enemy positions first, take unexpected routes, ideally after wiping the enemy team so the base is empty [https://www.halopedia.org/Capture_the_Flag].
- **Escort:** covers the runner; carrier should communicate so teammates can cover or give rides [https://www.halopedia.org/Capture_the_Flag].
- **Carrier behavior:** vary the route, avoid exposed lines where snipers can hit you; drop the flag to kill a lone pursuer instead of dying with it [https://www.halopedia.org/Capture_the_Flag]. In H2, juggle on open stretches if no one is watching.
- **Flag defender:** stay near base but not clumped (grenades), keep line of sight on the flag while hidden; park vehicles over the flag or in doorways [https://www.halopedia.org/Capture_the_Flag].
- **Sniper / midfield slayer:** safe sniper perch; help pushes; target Warthog gunners and power weapon users [https://www.halopedia.org/Capture_the_Flag].
- **Big-team vehicle play:** Blood Gulch: keep two on defense, one in a gunner Warthog sent for the flag; or "run in, grab, get in a Warthog"; avoid Scorpion runs (too slow); guard the enemy teleporters [https://strategywiki.org/wiki/Halo:_Combat_Evolved/Blood_Gulch].
- **Play to strengths:** best sniper gets the sniper, defensive players guard the flag, bad drivers take the turret [https://shacknews.com/article/65493/a-beginners-guide-to-halo].

### 4.3 When to push vs stall (director heuristics; **UNVERIFIED**, design inference from the above)

- Push for the flag right after a team wipe or a numbers advantage (enemy respawn timers are longer in CTF [https://www.halopedia.org/Capture_the_Flag]).
- Stall when your own flag is taken and "flag at home to score" is on: hold the enemy flag somewhere safe, hunt their carrier, then cap.
- In H4, the carrier has a magnum and cannot drop, and your flag need not be home, so pure speed runs are stronger.
- Defending a dropped flag: in games where friendlies speed up the return, stand on it; in H4 that does nothing [https://www.halopedia.org/Capture_the_Flag].

---

## 5. How average (not pro) players behave

### 5.1 Skill data

- Halo Reach study, 3.2 million players over 7 months, TrueSkill: the most matches per week (64+) gave the biggest total skill gain; per match, 4 to 8 matches a week was most efficient; a 30-day break costs about 10 matches to recover [https://www.brown.edu/news/2017-02-27/gameskill]. Individual habit differences were stronger than differences between skill levels [https://jeffhuang.com/papers/MasterMaker_TOPICS17.pdf].
- Rank distribution (Halo Infinite, closest available): Bronze 1.1%, Silver 5.9%, Gold 22.5%, Platinum 36.7%, Diamond 26.5%, Onyx 7.3% [https://www.gfinityesports.com/halo-infinite/ranked-distributions/]. MCC distribution not found. Use this shape as a prior: most of the lobby is "mid".
- KD ranges: no reliable aggregate found. One H3 profile: 1.57 KD over 455 games, 13% of kills with the BR [https://www.neogaf.com/threads/the-halo-3-beta-thread.154012/post-6687636] (single anecdote). Bot target **UNVERIFIED** suggestion: match-level KD spread roughly 0.5 to 2.0 in a balanced lobby, mean near 1.0 by construction.
- Accuracy: no official Halo per-weapon average accuracy found. **UNVERIFIED** starting point for tuning: low tier 25 to 35% shots-hit with utility rifles, mid 35 to 45%, high 45 to 55%+; calibrate against recorded human MCC games.
- Reaction time: simple visual reaction for adults is about 200 to 250 ms; gamers somewhat faster, test-dependent [https://lam2.mzbusiness.com/is-200ms-reaction-time-good.html]. Choice reaction (identify enemy, decide, aim) is slower than simple reaction; bots should add perception plus decision delay, not just one number.

### 5.2 Common casual habits (low/mid)

Sourced:
- Standing still while shooting [https://sportskeeda.com/esports/top-5-tips-newcomers-improve-gameplay-halo-infinite].
- Reloading between fights instead of switching weapons when empty; reloading after every shot [https://sportskeeda.com/esports/top-5-tips-newcomers-improve-gameplay-halo-infinite], [https://ru.steelseries.com/blog/5-tips-improve-any-fps-102].
- Rushing in to close distance [https://ru.steelseries.com/blog/5-tips-improve-any-fps-102].
- Fighting fights they cannot win, or retreating pointlessly instead of dumping damage [https://shacknews.com/article/65493/a-beginners-guide-to-halo].
- Everyone rushing the center at match start (343 designed H4 ordnance around this) [https://www.gamespot.com/articles/the-evolution-of-halo-4s-multiplayer/1100-6372279/].
- Grudges: humans chase a specific opponent even against their own interest; the BotPrize-winning UT2004 bot copied this and was rated 52% human vs 40% for actual humans [https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/].
- Teabagging: crouching repeatedly over a corpse; Halo is the game most associated with it and Halo 2 online made it mainstream [https://www.halopedia.org/Teabagging], [https://knowyourmeme.com/memes/teabagging]. Some hardcore players dislike it [https://www.improbable.com/2018/12/31/virtual-reality-teabagging-a-scholarly-analysis].

**UNVERIFIED** (common observation, encode as tunable probabilities):
- Ignoring the radar, getting shot in the back; not looking up.
- Panic grenades at close range, sometimes self-killing.
- Overextending after a kill (walking into the enemy's spawn alone).
- Revenge seeking: going straight back to the place they died.
- Looking at teammates, following the nearest teammate, crowding power weapons.
- Hesitation: a beat of indecision on first contact, especially when surprised; turning the wrong way first when shot from behind.
- Spray-and-pray with automatics at range; scoping with BR at close range.
- Fixed favorite routes and favorite weapons.
- Picking up every new weapon they walk over, including worse ones.
- Hunting medals or kills in objective modes instead of playing the flag.
- Jumping a lot during duels; jumping off ledges for no reason.
- Emote-like actions: melee-tapping a teammate, crouch "hello", looking at the sky after death, walking in circles in pregame.

### 5.3 What separates high players (sourced where possible)

- Pick engagements, shoot first, back off when hit first [https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/choose-your-battles].
- Pop shields with body shots, then headshot [https://giantbomb.com/wiki/Concepts/Four_Shot], [https://primagames.com/eguides/halo-5-guardians-eguide/arena].
- Track the enemy sniper's location [https://halo.bungie.org/gameplay/stratguide/movies/ogre1_41-0.html].
- Know timers and spawn rules; dropped-weapon callouts.
- Consistency: elite players form stable personal habits [https://jeffhuang.com/papers/MasterMaker_TOPICS17.pdf]. A bot "personality" should be consistent within a match, not re-randomized each fight.

### 5.4 What makes an opponent feel human

- Imperfect aim: perfect aim reads as a bot; constrain accuracy so fast motion and long distance reduce it [https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/].
- Irrational pursuit and grudges [same source].
- Mirroring the opponent rather than playing optimally (UT^2 strategy) [https://gamesbeat.com/unreal-bots-pass-turing-test/].
- Replaying recorded human paths for navigation (UT^2) [https://nn.cs.utexas.edu/downloads/slides/schrum.cec2011ws.pdf].
- 343's Halo Infinite bots: first versions did not feel like players; the team watched internal matches and added how Halo players react by "jumping or strafing in specific ways"; bots must feel "fair and balanced" because players can tell when bots cheat [https://www.gameinformer.com/preview/2021/11/15/how-halo-infinites-bots-became-so-ruthless-and-helped-343-develop-multiplayer].
- Fairness tells to avoid: tracking through walls, reacting to unseen players, instant 180 turns onto targets behind, perfect timer knowledge with zero map presence, never missing the 4th-shot headshot.

---

## 6. Per-game differences that matter to bots

### 6.1 Radar / motion tracker

| Game | Rule | Source |
|---|---|---|
| CE | Not shown while crouched (moving or still) or standing still | [https://www.halopedia.org/Motion_tracker] |
| H2 | Tracker plane tilts with view pitch (shows above/below); disabled shows an X | [https://www.halopedia.org/Motion_tracker] |
| H3 | Range settable 15/25/50/75/150 m; speaking enemies glow on tracker (Xbox Live voice) | [https://www.halopedia.org/Motion_tracker] |
| Reach | Shows location name; Active Camo jams with false dots within 25 m | [https://www.halopedia.org/Motion_tracker], [https://www.halopedia.org/Armor_ability] |
| H4 | Camo jammer shows neutral contacts in a tighter group, no false hostiles | [https://www.halopedia.org/Armor_ability] |
| MLG H3 / Reach | Motion tracker disabled | [https://www.halopedia.org/MLG_(playlist)] |

Default ranges and "what speed shows you" for H2 to H4: **UNVERIFIED** (commonly 25 m; crouch/walk hides, sprint/firing shows). Read from gametype settings at runtime. Bots must only "see" radar blips that a human with that game's tracker could see.

### 6.2 Aim assist (bots have none; need an equivalent)

- **Auto-aim / bullet magnetism:** bends shot trajectory toward a target when the reticle is close and inside the "red reticle range"; reticle turns red [https://www.halopedia.org/Aim_assist].
- **Magnetism / friction:** slows turn rate near a target and partly tracks strafing; controller only, mouse and keyboard not affected; per-weapon radius, smaller when zoomed, fades with distance; some games have a weaker outer ring [https://halopedia.org/Magnetism], [https://www.halopedia.org/Aim_assist].
- Bot equivalent: model aim error as a function of target angular velocity, distance, own movement, and zoom; then give "controller-personality" bots a small corrective pull and turn-slowdown inside a radius, and "mouse-personality" bots no friction but faster raw flicks with overshoot. Hits must still pass the game's real hit detection (H3 BR is not hitscan; projectile travel matters [https://halo.bungie.org/bwu/index.html?item=182]).
- CE MCC PC note: a user claims CE inaccuracy roughly doubles at high framerate [https://steamcommunity.com/app/976730/discussions/0/2266941647855136959]. **UNVERIFIED**.

### 6.3 Quick per-game cheat sheet

| | CE | H2 | H3 | Reach (TU) | H4 |
|---|---|---|---|---|---|
| Utility | Pistol 3sk | BR 4sk | BR 4sk | DMR 5sk | BR 4sk (post-Turbo) / DMR |
| Shield delay / refill | 5 s / 4 s | 4.25 s / 1.75 s | 5 s / 2 s | not found | not found |
| Bleedthrough | quirk on pistol 3rd shot | **UNVERIFIED** none | yes | small (TU) | **UNVERIFIED** |
| Melee | no lunge, running/jumping matters | lunge, run/jump matter, combos (Classic) | 2-hit kill, bang-bang-whack | weak, clang, assassinations | assassinations |
| Movement extras | crouch hides radar | button combos | equipment (bubble, regen, power drain) | armor abilities, sprint, health packs | sprint always, loadouts, thruster, ordnance |
| Camo | 45 s | 45 s | 30 s | AA 15 s | AA |
| Flag | no shoot, no one-hit melee, own flag home | slow walk, juggling, touch return (H2A) | one-hit melee, timed return | no juggling (1 s rule) | magnum, cannot drop, own flag not needed |

---

## 7. Behaviors to encode in bots

Checklist. Every item should be a tunable parameter, sampled once per bot per match (consistency), with small per-engagement noise.

### 7.1 Universal (all tiers)

- [ ] Perception delay before reacting to a newly visible enemy (base about 200 to 300 ms plus decision time; longer when surprised from behind) [https://lam2.mzbusiness.com/is-200ms-reaction-time-good.html].
- [ ] No knowledge a human could not have: line of sight, radar per game rules, sounds, callouts from teammates, kill feed.
- [ ] Aim error scaling with target speed, distance, own movement; no perfect tracking [https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/].
- [ ] Body shots until shield pop, then head; per-game STK table from section 2.1.
- [ ] Shoot-then-melee finish inside melee range when the target is low.
- [ ] Retreat to recharge when shields are popped and the duel is lost; per-game recharge delay from section 2.2.
- [ ] Respect fire-rate and bloom: Reach DMR pacing by range; CE pistol tap-fire.
- [ ] Jump links per map with technique tag (plain, crouch-jump, sprint-jump).
- [ ] Use only the input actions a human could do in that game (no H2 combos outside H2 Classic).
- [ ] Teammate awareness: look at teammates sometimes, follow nearby ones, avoid team-killing; occasional accidental friendly fire grenade (low tier).

### 7.2 Low tier ("casual", most of a public lobby)

- [ ] Accuracy low (start 25 to 35%, UNVERIFIED); slow, overshooting flicks; frequent full misses on the head shot.
- [ ] Long regular strafes or standing still while shooting.
- [ ] Reload after every fight, sometimes mid-fight; rarely switch to secondary.
- [ ] Rush center at match start; ignore timers entirely; grab whatever weapon is near.
- [ ] Ignore radar often; slow to turn when shot from behind (sometimes turn the wrong way first).
- [ ] Panic grenade at close range (high probability when losing a duel).
- [ ] Chase kills and revenge-seek; overextend after a kill.
- [ ] Rarely retreat; fight to the death or flee too late.
- [ ] Jump a lot during fights; scope in at close range.
- [ ] CTF: wanders, slays instead of playing objective, rarely escorts, sometimes walks the flag down the most direct exposed path.
- [ ] Comms (if the director gives them voice/pings): few, late, vague ("he's over there").

### 7.3 Mid tier

- [ ] Accuracy medium (35 to 45%, UNVERIFIED); decent body shots, inconsistent head follow-up.
- [ ] Semi-regular strafe rhythm with some jumps and crouches.
- [ ] Knows main power weapon spots and roughly when they come up (timer error of plus or minus 15 to 30 s).
- [ ] Uses grenades to open fights sometimes; some plasma stick attempts.
- [ ] Retreats when shields pop about half the time.
- [ ] Uses common power positions and camping spots; camps with shotgun/sword at known corners.
- [ ] Some team shooting when near teammates; some trading.
- [ ] CTF: takes a role when told by the director; will escort and defend; occasionally juggles in H2.
- [ ] Comms: basic callouts ("one shot top mid", "sniper's on BR tower").

### 7.4 High tier ("competitive")

- [ ] Accuracy high (45 to 55%+, UNVERIFIED); reliable 4th-shot headshots; pacing per weapon and game; still misses under pressure and while moving.
- [ ] Irregular strafe legs, crouch-strafe, strafe-peeks; pre-aims corners at head height; shoots first.
- [ ] Precise timers (plus or minus a few seconds); sets up on spawns 10 to 20 s before; avoids "dirtying" by standing still a second on pickup (H3) [https://www.bungie.net/Ne/Forums/Post/106060001?page=0].
- [ ] Grenade openers before pushes; spawn grenades; death grenades.
- [ ] Disengages to recharge, re-peeks from a different angle.
- [ ] Holds power positions; rotates; trades; plays for team shots; baits.
- [ ] Spawn awareness (H3 7-second influence window, buddy spawns); some spawn pressure, never a perfect spawn trap.
- [ ] Reach: correct AA use (Armor Lock vs sword/rockets, Evade out of duels, Jet Pack to high ground, Hologram baits, Drop Shield to win a 1v1 recharge).
- [ ] H4: sprint discipline (sprint between fights, not into them), Thruster dodge, ordnance choice.
- [ ] H2 Classic veterans: BXR and double shot with a botch rate.
- [ ] CTF: clears the base before pulling, varies routes, drops flag to kill a lone pursuer (where allowed), juggles in H2 when safe, defender holds sightline on stand while hidden.
- [ ] Comms: precise, short, location-coded ("one shot S2", "two top mid, cracked", "rockets 10 seconds", "flag going left lift").

### 7.5 Personality types (orthogonal to tier)

- [ ] **Slayer / Rusher:** aggressive, close range, shoot-melee, overextends, revenge-seeks.
- [ ] **Camper:** sits in a known power position or corner for long periods; leaves only to grab a weapon; crouches to hide from radar (CE crouch rule, other games crouch-walk).
- [ ] **Sniper:** goes for the sniper every spawn, perches high, repositions after each shot (high tier) or stays put (low tier).
- [ ] **Support / Teammate:** follows teammates, plays for team shots, calls out, picks up the turret instead of driving.
- [ ] **Objective player:** CTF runner or defender first, slaying second.
- [ ] **Weapon collector:** detours to every weapon, hoards power weapons, defends them.
- [ ] **Trickster:** trick jumps, grenade jumps, assassination animations, H2 combos.
- [ ] **Show-off / Toxic:** teabags after kills (probability by tier and score; more after revenge kills or multikills), crouch-taunts, melee taps on corpses, occasional "betrayal" by accident. Should be rare and a lobby-level setting, since some players dislike it.
- [ ] **Grudge holder:** picks a nemesis (the last player to kill it) and hunts them against its own interest [https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/].
- [ ] **Nervous:** hesitates at contact, panic grenades, retreats too early, jumpy aim.
- [ ] **Mirror:** copies the opponent's style (strafe if they strafe, camp if they camp) [https://gamesbeat.com/unreal-bots-pass-turing-test/].

### 7.6 AI director (team comms) behaviors

- [ ] Maintains the timer table (per game, per map, per gametype) and announces "up in 30/10" calls to teammates; accuracy of what it shares limited by team skill.
- [ ] Assigns CTF roles (runner, escort, defender, midfield/sniper) based on bot personality and current score/state.
- [ ] Converts individual bots' sightings into callouts using a per-map callout name table (Lockout: Sniper Tower, BR Tower, Library, Lift, Elbow [https://www.halopedia.org/Lockout]); calls shield state ("cracked", "one shot") and weapon ("has sniper").
- [ ] Shares only what teammates actually saw (no omniscience); callouts age out in a few seconds.
- [ ] Decides push vs hold vs stall from score, numbers advantage, enemy respawn timers (longer in CTF [https://www.halopedia.org/Capture_the_Flag]), and flag state rules per game (section 4.1).
- [ ] Coordinates setups before timers and trades/team shots in fights for mid and high teams; low teams get weak or ignored director calls (humans ignore comms too).
- [ ] Picks rotations (e.g. H2 Midship rotary with short/long pairing [https://www.strategywiki.org/wiki/Halo_2/Midship]).

---

## 8. Open items to verify in the MCC build

1. Per-game run/strafe acceleration curves (CE vs H2 vs H3) by in-engine measurement.
2. H2 Classic vs H2A button combo behavior in current MCC.
3. Shield/health values and recharge for Reach and H4 in MCC.
4. H4 BR/DMR tuning in MCC (launch vs post-Turbo).
5. CE and H2 per-map weapon and powerup timers, and whether H2 Classic still uses "no respawn while held".
6. Per-game flag rules: carrier speed, waypoint visibility, return type, flag-at-home default, CE/H3 juggling.
7. Default motion tracker range and movement thresholds per game.
8. Real accuracy, KD and reaction distributions from recorded human MCC matches (theater files) to replace the UNVERIFIED tier numbers.
