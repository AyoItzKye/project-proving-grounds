# 00 - Research Summary and Recommended Build Plan

Date: 2026-10-21. MCC build on this PC: `2025.08.16.178512.1-Release` (Steam, `<Steam library>\steamapps\common\Halo The Master Chief Collection`).
Scope: PvP bots for all six MCC games (CE, H2 Classic, H2A MP, H3, ODST, Reach, H4), Slayer first (combat) then CTF (objective brain), with a per-team AI director acting as team comms. Offline / anti-cheat-disabled only.

The five detailed reports (every claim sourced, unverified items marked):

| File | Track |
|---|---|
| `01-human-like-bot-behavior.md` | How shipped and academic bots were made human-like (Halo Infinite, Bungie AI, Quake III, UT BotPrize, CS, TF2, Killzone, F.E.A.R.), aim/perception models with numbers, team director patterns, how to measure humanness |
| `02-halo-ai-engine-and-map-data.md` | Halo AI engine per game: pathfinding, firing positions, objectives/tasks, character tags, MP bipeds, flags, scoring, HaloScript, networking, existing bot mods |
| `03-mcc-modding-pipeline.md` | Official editing kits, mod loading (ModManifest, ModInfo.json, Excession), build/test loop per game, debugging, legal, pitfalls, local install audit, first-day checklist |
| `04-runtime-and-reverse-engineering.md` | MCC internals (shell vs game DLLs), input hook, HaloScript command channel, memory reading, player-slot bots, update breakage, safety |
| `05-how-humans-play-halo.md` | Real Halo play per game: movement tech, shots-to-kill, shields, timers, spawns, CTF rules and roles, casual vs pro habits, bot behavior checklist by tier and personality |

---

## 1. The things we did not know going in (most important first)

1. **Engine AI ("actor bots") cannot do several core human things, and tags cannot fix it.** In the H3 engine family, AI never reloads, cannot shoot while jumping (so no real jump shots), cannot melee while moving, and cannot move while throwing grenades (02 s.Hard blockers, from c20). The Reach "Spartan Team" mod also had bots spamming melee. Actor bots are good soldiers, not convincing players.
2. **Actor bots cannot carry the CTF flag or score on the scoreboard natively, as far as anyone has documented.** No source shows AI picking up or capturing a flag, or AI kills counting in Slayer, in any game. Only H4 has script functions to change MP score (`adjust_team_score`). CTF with actor bots needs scripted fakes.
3. **There is a second kind of bot: a "player bot" in a real player slot.** MCC asks the shell for each local player's controller input through one function (`input_update`). The community splitscreen mod AlphaRing already hooks it for all six games. A bot that writes that input is a real player: scoreboard row, flag carrying, scoring, real player movement (jump shots, crouch-jumps, sprint, armor abilities), works in H2 Classic and H4. Cost: at most 4 local players (1 human + 3 bots), each renders a splitscreen view, and we must write our own perception, navigation and aim.
4. **Navigation: yes, we need a navmesh, and it differs per game.**
   - Actor bots: CE builds pathfinding automatically and keeps it in MP maps. H2 builds it from collision. H3, ODST and Reach need a sealed level, placed hints (jump, climb, hoist, cookie cutters) and Sapien "Generate all pathfinding data". H4 unknown. Teleporters, man cannons and gravity lifts have no documented AI support (script workarounds).
   - Player bots: the engine pathfinder is not exposed, so we build our own navmesh from each map's collision geometry (from the kit's source tags) with a standard navmesh library, plus hand-placed links for jumps, lifts, teleporters and man cannons.
5. **Objective and tactical points must be authored per map.** Firing positions (CE/H2 by hand; H3+ with zones/areas), objectives and tasks (H3+), named callout areas for the director ("Blue flag", "Top mid"), power weapon and powerup spawns with timers, camping/power positions, grenade lineups, flag stands and capture routes. This is per-map data work for every map we support.
6. **ODST has no PvP.** MCC's ODST is campaign plus Firefight (confirmed in the local install: `halo3odst\maps` holds only campaign and Firefight maps). ODST "multiplayer" was always Halo 3's. Options in section 5.
7. **Halo 2 is two games.** H2 Classic (`halo2.dll`, own kit) and H2 Anniversary MP (`groundhog`, separate H2AMP kit). One modder reports H2 Classic and H4 MP netcode cannot run AI actors at all (single source, must test). If true, those games are player-bot only.
8. **AI over the network is mostly broken.** CE AI never syncs. H3 `mp_ai_place` AI is "non-authoritative". Only ODST and Reach Firefight have proven networked AI. Plan everything as local play (one PC); online friends-only custom games are a later "maybe" for Reach.
9. **Mod tools lag the game.** Kits stopped updating in 2023-2024 while MCC is at 2025.08. Map mods sometimes need rebuilding after MCC patches; any runtime DLL breaks on patches and needs per-build offsets. The kits do ship the source files for stock MP maps, so we copy and extend stock maps instead of editing the game install.
10. **No retail console.** Testing uses the kits' Standalone/Sapien builds (full console, AI debug drawing, live tag reload, no networking). Final tests must be in MCC itself with anti-cheat off.
11. **Legal:** mods must be free, use only MCC assets, carry Microsoft's Game Content Usage Rules notice; the tools' license bars commercial and even non-profit use. No donations. Workshop cannot ship DLLs, so a runtime layer is a manual install.

## 2. What makes a bot feel human (condensed from 01 and 05)

- **Delay perception, not movement.** Bots act on what they saw a reaction time ago (CS bot model). Start medians: novice 0.45 s, average 0.30 s, strong 0.22 s, top 0.18 s (synthesized, tune against real captures).
- **Imperfect, laggy aim.** Aim re-samples the target every 0.05 to 0.30 s by tier, flicks follow Fitts' law with overshoot and 1 to 2 corrections, lead is below perfect, error spikes when the target reverses strafe. Perfect aim made bots rated *less* human (5.0 vs 6.7 in the Quake study).
- **Halo specifics:** shoot the body until the shield pops, then the head; nade-then-shoot openers; retreat to recharge shields (CE 5 s delay, H2 4.25 s, H3 5 s); beatdown and one-hit flag melee rules per game; jump shots and crouch at kill moments; power weapon and powerup timers only for experienced profiles, with error.
- **Honest information.** Each bot has its own belief store (last known positions, forgets after 4 to 10 s), sees only what its eyes and the motion tracker would show (crouch-walkers invisible). No ESP.
- **Personalities on top of skill tiers:** camper, rusher, flanker, power-weapon chaser, objective runner, support, sniper, grenade spammer, grudge holder. Grudges and revenge read strongly as human (a grudge-holding UT2004 bot was judged 52% human vs 40% for real humans).
- **Allowed mistakes, banned mistakes.** Allowed: overshoot, losing track, greed, over-chasing, wasted grenades, bad timing. Banned: getting stuck, staring at walls, jitter, the whole team taking the same route or pack-chasing one weapon (both were 343's Halo Infinite tester complaints).
- **The director must not be psychic.** It only knows what bots reported (seen, lost, killed, died at). Callouts are delayed 0.5 to 2.5 s, fuzzed ("two, maybe three"), use named areas, and expire. Some bots ignore orders sometimes (CS "rogue" chance). Voice/text callouts sell teamwork more than complex logic (F.E.A.R. lesson).
- **CTF roles:** flag runner, escort, flag defender, midfield/power control, carrier hunter; assigned by a cost function (travel, role inertia, personality fit), like Halo 3's objectives "plinko" and Killzone 3's commander.
- **Measure it.** Telemetry for bots and humans (accuracy, time-to-kill, strafe reversal timing, map-coverage heatmaps) plus blind clip reviews. Real Halo accuracy/KD numbers were not found publicly, so our own capture of the player's play becomes the reference.

## 3. Recommended architecture: hybrid, one brain

Both bot types are needed. Player bots give the human-like core the player asked for (jump shots, real flag runs, scoreboard). Actor bots fill lobbies beyond 4 players and cover games where they work.

```
                +------------------------------------+
                |  Bot Brain + Team Directors        |  external process (our code)
                |  perception delay, beliefs, aim,   |
                |  personalities, CTF roles, callouts|
                +-----------------+------------------+
                                  | shared-memory IPC
                +-----------------v------------------+
                |  Runtime DLL (offline only)        |  inside MCC, EAC off
                |  - reads game state (players,      |
                |    objects, flags, scores)         |
                |  - writes input for player bots    |
                |  - sends HaloScript commands       |
                |  - overlay: callouts, scoreboard   |
                +--------+------------------+--------+
                         |                  |
           player bots (max 3)        actor bots (engine AI)
           real player slots          via map mods from the kits:
           own navmesh per map        pathfinding, firing positions,
                                      objectives/tasks, character tags
```

- **Map mods (official kits)**: copies of stock MP maps with AI data, character/style tags tuned toward player-like behavior, AI-capable Spartan bipeds (Reach has `spartans_ai`; H3 needs a custom biped), HaloScript respawn loops and team allegiance (`mp_ai_allegiance` H3+).
- **Runtime DLL**: re-implemented ourselves (AlphaRing and libmcc have no license, so reference only; HaloCheckpointManager is MIT and its offset data can seed ours). Loaded by our own launcher, never left in the game folder, refuses to run with anti-cheat on or remote players present.
- **Brain**: one codebase for all games; per-game data files (weapons, shields, movement numbers, map annotations).

Fallback if the runtime layer proves too fragile: pure kit mod (actor bots + HaloScript director). It works, but bots will not jump shot or carry real flags.

## 4. Build order

| Phase | Work | Proves |
|---|---|---|
| 0 Setup | Finish kit downloads (H2EK, H2AMPEK, H3EK, H3ODSTEK, H4EK; CE and Reach are already installed), install Excession, run each kit's Extract, copy fmod folders, Defender exclusions, add our mods folder to `ModManifest.txt` (the current Vortex line points to a missing folder), baseline rebuild of one stock map per kit and play it in MCC | Pipeline works |
| 1 Feasibility (most important) | Per engine: add one squad + firing positions to a copied MP map, test spawn / move / shoot in MCC Slayer; test scoring and flag behavior. In parallel: runtime DLL proof on Halo 3, one extra local player slot driven by code (walk, turn, jump) | Which games get actor bots, whether player bots work on this build |
| 2 Slayer on one H3 map | Actor bots with tuned characters, respawns, teams; player bot brain v1 (navmesh from collision, perception delay, aim controller, strafe/jump-shot dance, shield retreat) | Combat feel |
| 3 Director + CTF on that map | Callout areas, belief/report flow, delayed callouts overlay, CTF roles and assignment, flag runs by player bots, scripted flag handling for actor bots | Objective brain |
| 4 Humanness pass | Telemetry, capture a skilled player's play as reference, blind clip review, tune tiers and personalities | Human-like, measured |
| 5 Port | Reach, CE, H2A, H2C, H4, then ODST per the player's choice; per-map annotation for each supported map | All games |

Honest scale: phases 0 to 1 are days; a convincing Halo 3 Slayer + CTF on one map is weeks; all six games with good map coverage is months. Each new map needs annotation work.

## 5. Decisions needed from the player

See the reply in chat (numbered questions). Topics: ODST scope, hybrid vs kit-only, 3-player-bot cap, map choice for phase 2, which kits are installed, brain language.

## 6. Open questions only testing can answer

From 02 and 05, to be settled in phase 1:
1. Do stock H2/H3/Reach/H4 MP maps in the kits already contain usable pathfinding?
2. Do actor bots work at all in H2 Classic and H4 MP (one modder says no)?
3. Does an MP game engine credit team score when an allied actor kills a player, or a player kills an actor?
4. Can Reach actors use sprint, jetpack, evade, hologram, drop shield, or only armor lock and camo?
5. Does the H3 `magic lift` jump hint let AI use gravity lifts?
6. Can extra splitscreen views for player bots be hidden or shrunk without breaking them?
7. What does `post_command` cost per tick, and is there a rate limit?
8. HaloScript limits (globals, threads) for H2 onward.
