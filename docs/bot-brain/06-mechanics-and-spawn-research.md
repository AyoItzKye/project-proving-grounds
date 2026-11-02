# Mechanics and spawn research

Numbers pulled from the editing-kit tags and tested community research that the first pass did not have: exact player speeds and shield timings, the Halo 3 damage model, the Halo 3 spawn-weighting system, competitive settings conventions and the engine's own range bands. Each section ends with the rules a bot should take from it.

## Player stats from the editing-kit tags

These are the multiplayer biped values Halopedia reads from each game's editing kit ([Spartan (multiplayer)](<https://www.halopedia.org/Spartan_(multiplayer)>)). They replace the approximate recharge times in the main tab.

| Game | Run speed (WU/s) | Sprint | Jump velocity (WU/s) | Shield | Shield delay / recharge | Health | Health delay / recharge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Halo CE | 2.25 | none | 2.1 | 75 | 6 s / 4 s | 75 | no regeneration (health packs) |
| Halo 2 | 2.25 | none | 3.08 | 70 | 5 s / 2 s | 45 | 10 s / 5 s |
| Halo 3 | 2.25 | none | 3.08 | 70 | 5 s / 2 s | 45 | 10 s / 5 s |
| Halo: Reach | 2.2 | 1.623x (3.57 WU/s), armor ability | 2.3 | 70 | 6 s / 3 s | 45 | 4 s / 9 s, regenerates only to the next third (100, 66.6, 33.3 percent) |
| Halo 4 | 2.2 | 1.65x (3.63 WU/s), always available | 2.36 x 1.29 (3.04 WU/s) | 70 | 6 s / 2 s | 45 | 4 s / 6 s |
| H2A multiplayer | 2.3 | none by default | 2.34 x 1.29 (3.02 WU/s) | 70 | 5 s / 2 s | 45 | 10 s / 5 s |

Reach Elites run faster, have 79 shield and 50 health, and regenerate health fully after 7 s ([Elite (multiplayer)](<https://halopedia.org/Elite_(multiplayer)>)).

### Band crossing times at base run speed

One WU is 10 ft, so at 2.25 WU/s a Spartan covers 22.5 ft per second. Sprint in Reach and Halo 4 covers about 36 ft per second.

| Band | Distance | Time to cross on foot | Time with sprint |
| --- | --- | --- | --- |
| Melee (0 to 8 ft) | up to 0.8 WU | under 0.4 s | n/a |
| Short (8 to 40 ft) | 0.8 to 4 WU | 0.4 to 1.8 s | 0.2 to 1.1 s |
| Medium (40 to 120 ft) | 4 to 12 WU | 1.8 to 5.3 s | 1.1 to 3.3 s |
| Long (120 to 300 ft) | 12 to 30 WU | 5.3 to 13 s | 3.3 to 8 s |

### Rules the bot takes from these numbers

- A shield pops in a fight and the recharge needs 5 to 6 s of no damage plus 2 to 4 s to fill: a full reset is 7 to 10 s. A bot that retreats at a popped shield should plan to be out of the fight for that long, not re-peek at 3 s.
- Halo 2 and 3 health takes 10 s of no damage to start refilling; a bot that won a fight with no shield and low health is one body shot from death for the next 10 s even though its shield comes back in 7. It should not take a second fight inside that window.
- Reach health only comes back to the next third: a bot at 20 percent health stays at 33 percent until it finds a health pack or a drop shield. It plays the rest of the life as a one-grenade kill.
- Jump velocity in Halo 2 and 3 (3.08) is much higher than Reach (2.3); the same crouch-jump reaches ledges in Halo 3 that Reach bots must jetpack to. Map jump tables must be per game.
- At 22.5 ft per second, an enemy at the far edge of Short band reaches melee range in under 2 s; a bot with a shotgun or sword has that long to position. An enemy at Medium band takes 2 to 5 s to arrive, enough time for a BR to land a full kill.
- A sprinting enemy at the far edge of Medium band (120 ft) arrives in about 3.3 s and cannot shoot on the way: three BR bursts or four DMR shots land before they can swing. The bot stands and shoots, it does not run.
- Halo CE's 75 shield and 75 health with a 6 s delay make it the game where retreating pays least and health packs matter most; a CE bot values a health pack route over a shield reset.

## Damage model numbers

- Halo 3 players have 115 hit points: 70 shield plus 45 health; a Battle Rifle bullet does 6 damage, so 12 bullets (four bursts) total 72; eleven and two thirds strip the shield and the last bullet is the head shot ([Halopedia: Head shot](https://www.halopedia.org/Head_shot)). A sniper round does about 80: 70 to the shield and 10 to the body, which is why a head shot kills a full-shield player and a body shot does not.
- All ordinary Halo 3 melees do 70 damage, exactly the shield; the Spiker's blades do 72, the sword, hammer and assassinations more ([Halopedia Spiker page history](https://www.halopedia.org/Special:MobileDiff/911670)). A melee therefore pops a full shield and leaves 45 health, which the next melee, one head shot, or about 8 BR bullets remove.
- Halo 3 health regenerates at 9 points per second after 10 seconds without health damage; Halo 4 at 7.5 per second after 4 s; Reach at 5 per second up to the next third after 4 s, with the last third below 30 only restorable by health pack or drop shield ([Health](https://breezewiki.discard.no/halo/wiki/Health)).
- Halo 2 and later use global damage tables where each damage type (bullet fast, plasma, melee, explosion, sniper and so on) is multiplied against the target material; Halo CE carries the multipliers inside every damage effect ([Damage types](https://www.halopedia.org/Damage_types)). Plasma damage types carry a bonus against shields and a penalty against health, which is the engine reason behind the plasma-strips, kinetic-finishes rule.

### Kill arithmetic the bot can run live

With shield 70 and health 45 the bot can track an enemy's remaining hit points from the damage it and its teammates have dealt:

| Damage source (Halo 3) | Points | Effect on a full 115 |
| --- | --- | --- |
| One BR burst, all three hit | 18 | Shield 70 to 52 |
| Three BR bursts | 54 | Shield at 16 |
| Four BR bursts (last to head) | 72 | Shield gone, head shot kills |
| Melee | 70 | Shield gone, 45 health left |
| Melee plus one BR burst to the head | 70 + head shot | Kill |
| Two BR bursts plus melee | 36 + 70 = 106 | Shield gone, 9 health left; any further hit kills |
| Sniper body shot | \~80 | Shield gone, 35 health left |
| Sniper body shot plus one BR bullet to the head | 80 + head shot | Kill |

The same bookkeeping works in Halo 2, Reach and Halo 4 with their 70 and 45 pools and each weapon's per-shot damage read from its tags; the scripting agent should expose damage dealt per target so the bot knows when one head shot finishes.

### Rules the bot takes from the damage model

- Count damage, not shots: team shot damage adds up across bots, so a target hit twice by a teammate needs only two more bursts, and the bot should switch to the head earlier.
- A melee is worth exactly one shield: against a full-shield enemy at Melee band, melee first, then any single head shot wins; against an enemy with any shield damage, melee alone wins.
- Plasma on shields, kinetic on health: a plasma rifle does more than a BR to the 70 shield and less to the 45 health; the switch point is the shield pop.
- Sniper body shots are not wasted: 80 damage leaves 35 health, which one BR bullet to the head or one melee removes. A sniper who body-shots should expect a teammate to finish, or finish with a quick switch.

## Halo 3 spawn system in depth

Michael "FyreWulff" Kidder tested the Halo 3 spawn engine in a Sandbox sky-bubble lab and published the model at halo.bungie.org ([Understanding Halo 3 Spawns](https://halo.bungie.org/misc/fyrewulff_spawnsystem)); he notes the same concepts likely apply to Reach, and Halo 2's system is a simpler ancestor. The findings below are his; the bot rules are derived from them.

### How the engine picks a spawn

- Every spawn point starts at a base weight of 1000; the engine adds and subtracts influence and picks among the highest-weighted points. Starting spawns are used only for the initial spawn and for players joining in progress.
- Spawns ignore geometry, line of sight and weapon fire: a player is a sphere of influence centered on their position, and it reaches spawns through walls. Staring at a spawn does not block it; only a player or a large solid object standing on it does.
- Spawn zones (respawn areas) only enforce spawns in objective games; in Team Slayer the enemy's zone is still considered, and a team that blocks the enemy's zoned and neutral spawns will see them spawn in its own zone. Flag-at-home and flag-away zones switch on and off with the flag's state; a captured territory and a flag on its post both act as small spawn areas for their team.
- Host migration in Team Slayer usually flips the spawn zones between teams.

### The weights (his estimates, base 1000 known from a Bungie update)

| Influence | Weight | Effective distance |
| --- | --- | --- |
| Slayer spawn area for the team | +300 | the zone |
| Ally within range (stronger if they just spawned) | +500, proximity scaled | about 5 Sandbox grid tiles |
| Enemy within range | -500, proximity scaled | about 5 tiles |
| Teammate death nearby | -700, recovering +100 per second | 4 to 4.5 tiles |
| Own flag on its post | +700 | 3 to 3.5 tiles |
| Captured territory | +300 | the territory |

- The 7-second rule: a teammate who walked over or stood near a spawn in the last 7 s adds weight (the buddy spawn); an enemy near it in the last 7 s subtracts; a teammate's death near it in the last 7 s subtracts; dying within 7 s of spawning there sends the player elsewhere.
- Why players die twice in the same place: a spawn with zone and ally influence sits at 1800; one death drops it to 1100, and by the 5 s respawn it has recovered to 1300, still competitive, so the player often respawns there; a second quick death drops it to 600 and sends them away.
- Buddy spawning outweighs spawn zones: one living teammate standing near a safe cluster of spawns pulls the whole respawning team to it, even outside a marked zone. FyreWulff describes regrouping seven BTB teammates at a man cannon this way in about 10 s.
- Emergency spawns exist on every map and are used only when every normal spawn is blocked.

### Rules the bot takes from the spawn system

- Predict enemy respawns from the model, not from habit: the enemy will reappear near their living teammates, near their flag if it is home, inside their captured territories, and away from where the bot's team is standing and from where their teammates just died. After a kill, pre-aim the spawn cluster nearest the enemy's surviving players.
- Anchor spawns for the team: when the team is losing a fight, one bot should stand (alive) at a safe spawn cluster so dead teammates buddy-spawn next to it and come back as a group. This is the single strongest regroup tool in Halo 3 and likely Reach.
- Do not die twice in the same spot: a bot that just spawned and died within 7 s should expect to be sent across the map; a bot that spawned and survived 7 s will keep spawning near its team.
- Push enemy spawns with position, not fire: standing within about 5 tiles of an enemy spawn cluster removes 500 weight from it; two bots across the enemy's base drive their spawns to the far side. Grenades and bullets do nothing to spawns.
- Kill where it helps the trap: killing an enemy near their own spawn cluster adds a -700 death penalty that recovers at +100 per second, so a kill every 7 s in the same area keeps that cluster closed. Killing enemies deep in the bot's own territory opens spawns near the bot's team for the next 7 s.
- Objective games: in CTF the enemy spawns near their flag while it is home (+700) and switches to the flag-away zone when it is pulled; a flag pull moves the enemy's spawns, so the escorts should expect enemies to appear in the flag-away zone, not at the base. In Territories, capturing the enemy's territory removes their spawn anchor there.
- Spawn-blocking: a bot standing on a spawn point blocks it; a team that holds an enemy spawn cluster physically (one bot per point, as in a four-point base) forces spawns elsewhere, which is the mechanism behind spawn trapping on The Pit and Guardian.
- Halo 2 and CE: both weight spawns toward living teammates and away from enemies with simpler rules and no zones in CE; the same prediction logic applies with less certainty. Halo 4 uses an updated system with instant respawn in some variants, so the 7-second windows shrink to the respawn time.

## Competitive settings conventions

The bot should read the game variant at load and switch to competitive behavior when it sees these markers.

| Setting family | Markers | What changes for the bot |
| --- | --- | --- |
| Halo 3 MLG (v8 in MCC) | BR start, motion tracker off, weapons on fixed timers (sniper 150 s, rockets 180 s, powerups 120 s), hammer, spike grenades, flamethrower and radar jammer removed, forge-edited maps ([Halopedia MLG playlist](<https://www.halopedia.org/MLG_(playlist)>); [MLG playlist announcement](https://xboxaddict.com/news/9003/MLG-Playlist-is-Live-in-Halo-3.html)) | No radar: rely on sight, sound and callouts; count timers exactly; expect every enemy to have a BR at spawn; power-position holds matter more than weapon pickups |
| MLG movement convention | 110 percent player speed and 90 percent shield recharge were MLG conventions Bungie noted when designing Team Hardcore ([Bungie Team Hardcore post, mirrored](https://www.halo.fr/?p=718)) | Band crossing times shrink by 10 percent; shield resets take about 10 percent longer, so retreats are slightly longer |
| Halo 3 Team Hardcore | BR start, motion sensor set to allies only, 4v4 mixed objective | Radar shows teammates only; the bot uses it for grouping, never for enemy detection |
| Reach MLG (v6, zero bloom after the Title Update) | DMR start, radar off, rockets 178 s, sniper and grenade launcher 118 s, powerups 120 s, no armor lock in most variants, sprint only in some | Fire faster with zero bloom; no armor lock counters needed; sprint rules per variant |
| H2A HCS 2014 to 2015 | BR start, no secondary, flag return disabled, radar off | A dropped flag stays until carried; defenders must physically carry it home, so flag fights last longer |
| Halo 3 HCS 2019 | Community MLG-derived settings, radar off | As Halo 3 MLG |
| Halo 5 and Infinite HCS (for reference) | Motion tracker off, static weapon spawners, friendly fire on, no secondary on spawn | The same no-radar, timer-driven logic |

### Rules the bot takes from competitive settings

- Radar off is the biggest behavior switch: corner checks become sound and pre-aim checks, crouch-walking no longer hides the bot (there is nothing to hide from) but still quiets footsteps, and the hologram becomes a stronger tool.
- Friendly fire on (most competitive variants): grenades and rockets must not land on teammates; the team-shot rule still holds, but splash weapons are checked against ally positions before firing.
- Flag return disabled (H2A HCS): the defender's job becomes carrying the dropped flag back, not touching it; the flag carrier role applies to the defender too.
- Longer power weapon timers (150 to 180 s) mean each power weapon decides about a fifth of a 12-minute game; losing the sniper spawn once is survivable, losing it three times is the game.

## Red reticle range: the engine's own range band

Every Halo weapon tag carries a red reticle range (RRR): the distance within which the reticle turns red on an enemy and aim assist and bullet magnetism apply. Halopedia lists RRR per weapon and zoom level (the sniper rifle's, for example, is 0 m hip-fire in CE and Halo 2, 15.94 m in Halo 3, 22.89 m in Reach and 38.5 m in Halo 4, rising to 106.6, 63.2, 91.5 and 152.7 m at the first zoom level, and to 426.6, 141.9, 228.5 and 343.1 m at the second ([Halopedia sniper stats comparison](https://www.halopedia.org/User:Dab1001/Pitch/Stats/FPS))).

### Why this matters for the bot

- RRR is the game's definition of "in range": inside it, the bot's shots get magnetism and the reticle feedback a human relies on; outside it, hits depend on raw aim. The scripting agent should read each weapon's RRR from its tags and use it as the weapon's true Medium-to-Long boundary instead of the fixed band table where the two disagree.
- Zoom extends RRR by a large factor (about four to six times for snipers); a scoped weapon's band is the zoomed RRR, so the bot should scope whenever an enemy is beyond the hip-fire RRR and inside the zoomed one.
- RRR grows across the series (Halo 3 to Reach to Halo 4), which is why Halo 4 fights happen at longer distances than Halo 3 fights on the same remade map (Ragnarok versus Valhalla). Band cutoffs should be scaled per game from the utility weapon's RRR: Halo 3 BR hip-fire RRR for the top of Medium, DMR RRR for Reach, BR or DMR RRR for Halo 4.
- Weapons with a 0 m hip-fire RRR (CE and Halo 2 sniper) have no aim assist unscoped; a no-scope in those games is pure aim and should be reserved for Elite and Pro tiers.

### Rules the bot takes from RRR

1. In range means reticle red: the bot commits to a gunfight only when the target is inside the current weapon's RRR (hip-fire or scoped as applicable).
2. Red reticle on a sword or hammer means the lunge will connect; outside it, do not swing.
3. When the target leaves RRR mid-fight, the bot either scopes (if that brings them back inside) or breaks off; it does not keep spraying.
4. Aim-assist strength falls off at the edge of RRR; Veteran and Pro bots may fight at the edge, Recruit and Regular bots should close to two thirds of RRR before committing.
