# 01 Human-Like FPS PvP Bot Behavior and Team Coordination

Research track for the Halo MCC PvP bot mod (offline, anti-cheat off; Halo CE, 2, 3, ODST, Reach, 4). Scope: how shipped games and research bots made FPS bots feel human, how team coordination and "director" style comms were built, and how human-likeness is measured. Every non-obvious claim has a source URL. Items I could not confirm from a primary or reliable source are marked **UNVERIFIED**.

Compiled 2026-10-21. Related tracks in this folder: `03-mcc-modding-pipeline.md`, `04-runtime-and-reverse-engineering.md`, `05-how-humans-play-halo.md` (Halo-specific human playstyle data belongs there; this file covers the general bot techniques).

---

## 0. Executive summary (the findings that matter most)

1. **Decision/reaction latency is the single biggest humanness lever.** In the Soar Quakebot study, a bot deciding every 0.10 s was rated most human (6.3/10) and was unanimously judged human on the binary test; the as-fast-as-possible bot (about 0.025 s per decision) scored 5.0 and a 0.5 s bot scored 4.3. Superhuman aim (perfect lead) *lowered* humanness from 6.7 to 5.0. Source: Laird and Duchi, "Creating Human-like Synthetic Characters with Multiple Skill Levels", AAAI 2001, https://www.qrg.northwestern.edu/Resources/aigames.org/2001/Laird.pdf
2. **Shipped bots fake reaction time by delaying perception, not by slowing aim.** Counter-Strike's bot keeps a 20-slot ring buffer of "most dangerous threat" snapshots and acts on the snapshot from `ReactionTime` seconds ago (https://github.com/rehlds/ReGameDLL_CS/blob/master/regamedll/dlls/bot/cs_bot_vision.cpp). TF2 bots must see a target continuously for 1.0 / 0.5 / 0.3 / 0.2 s (Easy / Normal / Hard / Expert) before they "recognize" it (https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/tf/bot/tf_bot_vision.cpp).
3. **Aim should be a tracking controller with sampled, laggy estimates, not a snap.** TF2/NextBot re-samples target position and velocity every 1.0 / 0.25 / 0.1 / 0.05 s by difficulty (x0.8 to 1.2 random), integrates between samples, and pauses about 0.3 s after every 100 degrees of turn to "recenter its virtual mouse on its virtual mousepad" (https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/NextBot/Player/NextBotPlayerBody.cpp). A behavior-cloned CS:GO agent independently learned the same mouse-pad pause from human data (https://arxiv.org/abs/2104.04258).
4. **Halo's own engine already contains a human-plausible miss model.** Halo CE `actor_variant` tags define "burst geometry": shots start at a random point offset left or right of the target and walk back toward it, with first-burst delay, target tracking (0 to 1) and target leading (0 to 1) knobs (https://c20.reclaimers.net/h1/tags/actor_variant/). That is a ready-made, Halo-feeling way to make misses look intentional and readable.
5. **Halo Infinite's bots (the closest prior art) were built by watching high-level internal players, layered movement first, then aim and shooting, then route selection; the stated design rule was "feel fair", no cheating.** Higher tiers used radar like humans; testers complained bots were too accurate, all took the same route at match start, and all chased the same power weapon in a pack. Sources: Kotaku https://kotaku.com/why-halo-infinite-s-bots-act-so-much-like-people-1847511140 , Game Informer https://www.gameinformer.com/preview/2021/11/15/how-halo-infinites-bots-became-so-ruthless-and-helped-343-develop-multiplayer , 343 feedback summary via Pure Xbox https://www.purexbox.com/news/2021/09/343_industries_reveals_the_key_feedback_from_halo_infinites_technical_preview
6. **Bungie's Halo 3 "Objectives" system is a direct template for the CTF director.** Designers declare a prioritized task tree with capacities; squads are "poured in at the top" and filtered to the most important unfilled tasks, using a greedy minimization of a cost function H(squad, task) (travel distance, coordination, balance). Slides: https://web.cs.wpi.edu/~rich/courses/imgd4000-d10/lectures/halo3.pdf
7. **Killzone 2/3 multiplayer bots are the best documented PvP team AI:** commander (objectives with weights and ideal bot counts) to squad (HTN, strategic area graph plus influence map that counts units and recent deaths) to individual (own perception, may ignore orders to survive). Individuals only report what they perceived: first sighting, lost track, saw a kill. Sources: https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf and https://www.guerrilla-games.com/media/News/Files/VUA07_Verweij_Hierarchically-Layered-MP-Bot_System.pdf
8. **Communication sells coordination more than coordination does.** F.E.A.R. had no complex squad behaviors at all; flanks emerged from simple "move to nearer cover" orders, and two-character dialogue convinced players the coordination was intentional (https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf). For our director, callouts are the product.
9. **Shipped team bots delay team information on purpose.** CS bots wait `1 + 2 x ReactionTime` seconds before answering a radio call (cs_bot_radio.cpp); Quake III bots schedule team chat replies `2 x random()` seconds later (https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_dmq3.c). Information delay is a proven anti-psychic device.
10. **Measure humanness with blind judges plus telemetry distributions.** BotPrize 2012 winners scored 52% humanness while real humans averaged only about 40% (https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/). Judges key on smoothness of camera and movement, goal-directedness and collision avoidance (https://arxiv.org/abs/2303.02160); map-coverage heatmaps compared with Earth mover's distance give a cheap automatic metric (https://arxiv.org/abs/2104.04258).

---

## 1. Halo Infinite's official bots (343 Industries, 2021)

Halo Infinite is the first Halo game with multiplayer bots and the closest reference to our goal.

### 1.1 Goals
- Bots were built **as teaching tools first**, so they "had to emulate player behaviors" (Tom French, multiplayer associate creative director). Source: Game Informer, https://www.gameinformer.com/preview/2021/11/15/how-halo-infinites-bots-became-so-ruthless-and-helped-343-develop-multiplayer
- **Fairness as a hard requirement:** "Halo (especially multiplayer) has this perception of fair and balanced, and our bots needed to feel fair and balanced ... Sometimes you play a game and you know the bots are cheating; you can tell." (French, same source).
- Early versions "didn't quite feel like real players"; the bots team watched internal matches of the studio's higher-level players and analysed what humans did that bots did not, e.g. "players will react by jumping or strafing in specific ways." (same source).
- Bots were a major playtesting tool for map flow and team strategy (Andrew Witts, lead multiplayer designer, same source).

### 1.2 How they were built (from developer interviews)
- Senior lead gameplay engineer Brie Chin-Deyerle and multiplayer designer Sara Stern: "We spent a lot of time breaking down how humans play in internal playtests and prior Halo games"; the aim was to "figure out why people do what they do in multiplayer, and then how we could model those choices." Source: Kotaku, https://kotaku.com/why-halo-infinite-s-bots-act-so-much-like-people-1847511140
- **Build order:** movement first (walking, sprinting, crouching, mantling), then aiming and shooting, then route selection. Getting bots to recognize the "best path" took longer than expected (Kotaku, same).
- **Radar:** Infinite's radar only shows fast-moving players; higher-tier bots were given the ability to use radar "to replicate human play" (Kotaku, same). Implication: perception is gated by the same HUD information a human has.
- **Names:** about three dozen names were created to mimic human gamertags; the developers said "Recognizing and responding to player names is a skill" (Kotaku, same).
- Bots flank, coordinate, and pick up weapons from fallen players (Kotaku, same).
- **"Teabagging" was a bug:** a failed jump onto stair or ramp edges left bots in a looping landing animation that looked like crouch spam. Sources: PC Gamer https://www.pcgamer.com/uk/halo-infinites-bots-arent-teabagging-you-at-least-not-on-purpose/ , Windows Central https://windowscentral.com/halo-infinites-bots-arent-actually-teabagging-343-industries . Lesson: players read social meaning into any repeated motion, so movement glitches become "personality" whether we want it or not.

### 1.3 Difficulty tiers and tuning feedback
- Four tiers: Recruit, Marine, ODST, Spartan (TechRadar, https://www.techradar.com/news/halo-infinites-first-bot-focused-preview-could-happen-as-soon-as-next-weekend ). During the 2021 tech test the community unlocked ODST after 1.2 million bot kills and Spartan after about 7 million (Kotaku). Higher tiers add sharper shooting, faster strafing and radar use (Kotaku).
- 343's own feedback summary from the first preview (Pure Xbox, https://www.purexbox.com/news/2021/09/343_industries_reveals_the_key_feedback_from_halo_infinites_technical_preview ):
  - "Bots were too accurate when shooting weapons and throwing grenades"
  - "Bots all went the same way to start, could get confused while moving on the map, and didn't use equipment enough"
  - "Spartan Bots weren't much better than ODST Bots"
- Sara Stern: bots "ran in a pack to all try and get the same weapon at once ... we're exploring solutions for getting them to spread out ... search for weapon pickups without competing with one another"; they also worked on "how well Bots prioritize contesting powerful weapons on map" (WCCFtech, https://wccftech.com/halo-infinite-tech-preview-feedback-discussed-while-343-industries-explains-lack-of-campaign-gameplay/amp/ ).
- For the next preview "Spartans will share some information with each other," like teammates calling out positions (Stern, Pure Xbox, https://www.purexbox.com/news/2021/09/343_admits_it_probably_over-hyped_halo_infinites_spartan_bots ).

### 1.4 GDC 2022 talks (primary sources, behind the GDC Vault login)
- "Deconstructing the Combat Dance: Designing Multiplayer Bots for 'Halo Infinite'", Sara Stern: how the team broke down the Halo combat dance so bots strafe, bounce grenades and use equipment like players. https://gdcvault.com/play/1028054/Deconstructing-the-Combat-Dance-Designing
- "Thinking Like Players: How 'Halo Infinite's' Multiplayer Bots Make Decisions", Brie Chin-Deyerle: how bots interpret game state, which actions are valid, how competing actions (fight, get weapon, go for the flag) are weighed, and how bot performance was evaluated. https://gdcvault.com/play/1027689/Thinking-Like-Players-How-Halo
- **UNVERIFIED:** the abstract's "weighing different actions against each other" suggests a utility-scoring architecture, but I could not access the talk content (GDC Vault was in maintenance during this research). Recommended follow-up: watch both talks and append notes here.
- **UNVERIFIED:** no developer statement found on exact reaction times, aim error models or perception cones for Infinite bots.

---

## 2. Bungie's Halo AI architecture (campaign AI, but the ideas transfer)

### 2.1 Halo CE: "The Illusion of Intelligence" (Chris Butcher and Jaime Griesemer, GDC 2002)
Slides: https://www.jmeiners.com/shamans/papers/ai/the_illusion_of_intelligence.pdf
- Split of responsibility: design owns the "3 minute scope" (racial personalities, strategic purpose); code owns the "30 second scope" (intelligent decisions, instant reactions).
- Design goals: intelligible, interactive, unpredictable. Individual goals include "Imitating the Player's capabilities" and "Transparent thought process".
- Players should see enemies **Impressed** (react with surprise, anger, awe), **Fooled** (limited knowledge, predictable reactions) and **Thwarted** (breaking point: flee, berserk, retreat, defensive state).
- **Randomness discarded** in favour of reactive AI: unpredictability comes from the unpredictable player and situation, with "analog reactions" in position and timing.
- **Individual knowledge model**, "complete model" discarded: "'Real' perception, No cheating, Vision, Hearing, Touch, ESP", "Selective Memory", "Persistent State", "Can be fooled".
- **Communication of intent** (hidden states discarded): language, posture, gesture, focus of attention, dialogue, animation.
- Emergent behavior from cause-effect stimuli (discovery, weapon fire, damage, death); a "fuzzy emotion system" was discarded.
- Playtest data, the most quoted result in game AI: with **weak** enemies, 8% of testers rated the AI "very intelligent"; with **tough** enemies, 43% did (and 0% "not intelligent"). Slide text: "Smarter = Tougher, Tougher = Smarter". Lesson for us: perceived intelligence is entangled with perceived toughness; bots that die too easily read as dumb regardless of their logic.
- Position choice uses designer-placed **firing points** weighted by line of sight, distance to target, cover proximity, friends, enemies, vehicles, grenades, sensed by multiple ray casts.
- Combat dialogue triggered from decisions and stimuli (hurt, death, saw enemy, throw grenade, seek cover), filtered by priority, context, uniqueness, relevance; nearby characters can reply. Scale: 57 events, 166 dialogue types, 12 speaking characters, 5147 recorded lines.

### 2.2 Halo 2: "Handling Complexity in the Halo 2 AI" (Damian Isla, GDC 2005)
Article: https://www.gamedeveloper.com/programming/gdc-2005-proceeding-handling-complexity-in-the-i-halo-2-i-ai
- **Behavior DAG** (a hierarchical FSM where subtrees can be shared). Parent nodes pick children by **prioritized list**: "The first one that can run, does, but higher-priority siblings can always interrupt the winner on subsequent ticks." Other schemes: sequential, sequential-looping, probabilistic, one-off.
- **Binary relevancy:** float relevancy scores became untunable with 20+ competing behaviors, so relevancy became a yes/no test and priority came from tree position.
- **Impulses:** lightweight references to behaviors placed elsewhere in the tree to change priority situationally (e.g. self-preservation when damaged), also usable as hooks. "Hackability is key."
- **Stimulus behaviors:** inserted into the tree at runtime by event handlers for a short window (e.g. "flee when leader dies" after an actor-died event) instead of polling every tick.
- **Behavior tags:** bitvector conditions (vehicle status, alertness) checked before full relevancy, locking/unlocking whole branches for driver, passenger, infantry.
- **Memory categories:** per-behavior persistent (grenade throws), per-behavior short-term, per-object (perception data, last seen position), per-object per-behavior (last melee time, search failures).
- **Knowledge model:** each actor holds "props" (perceived targets) filtered through its senses, so beliefs can differ from world state and AI can be "tricked, confused, surprised". Isla notes it was "simply a flat list of object references".
- **Styles:** each designer "order" references a style, a whitelist of allowed behaviors ("a behavior cannot be considered unless it is explicitly allowed by the order's style"), which can also skew parameters (e.g. flee more easily). Character files inherit parameter blocks from parents to manage about 10,350 numbers.

### 2.3 Halo 3: "Building a Better Battle: The Halo 3 AI Objectives System" (Isla, GDC 2008)
Slides: https://web.cs.wpi.edu/~rich/courses/imgd4000-d10/lectures/halo3.pdf ; secondary write-up: https://www.gamedeveloper.com/design/combat-evolved-the-encounter-design-of-halo-3 (also cites Max Dyckhoff, "Decision Making and Knowledge Representation in Halo 3", GDC 2008; I could not locate those slides, **UNVERIFIED** content).
- Halo 2's imperative method (designer FSMs with explicit transitions between "generators") had n-squared complexity. Halo 3 moved to a **declarative** method: "Enumerate 'tasks that need doing' in the environment. Let the system figure out who should perform them."
- Structure: a tree of prioritized tasks; each task is self-describing (priority, activation script fragments, capacity). Algorithm: "Pour squads in at the top. Allow them to filter down to the most important tasks to be filling RIGHT NOW. Basically, it's a plinko machine." Tasks turn on and off; squads are pulled up when a higher-priority task activates and pushed down when theirs deactivates.
- Squad distribution respects task capacity (a bin-packing problem, NP-hard, so sub-optimal is fine) and minimizes a cost function **H(s,t)** that weighs,. Implementation is greedy: repeatedly assign the (squad, task) pair with minimum H that fits capacity. O(n^2 m) but n and m are small; results cached and timesliced.
- Warning from the slides:
- Refinements: **filters** (occupation conditions: character type, in or out of vehicle, snipers), implemented as infinite H; activation latch on / latch off; **exhaustion** by death count or living count; one-time assignment.
- Case studies: **leadership** (leader filter on core task; leader death puts the task in a "broken" state with broken behaviors) and **player pickup** (dedicated task with vehicle filter so allies drive to the player).
- Known weakness: bucketing by squad is not always right ("give a guy a sniper rifle ... shouldn't he then be allowed to occupy a 'sniper' task?"). For our bots, assign per bot, not per squad.
- Event-driven "stimulus behaviours" in Halo 3 react to spotted enemies, nearby grenades, and the defeat of a nearby commander (Game Developer article above).

### 2.4 Halo engine tag parameters (directly relevant to MCC modding)
The Halo CE tag reference documents the campaign AI knobs that ship inside the engine we are modding:
- `actor` tag (https://c20.reclaimers.net/h1/tags/actor/): max vision distance, central vision angle, max vision angle, **peripheral vision angle** and distance, hearing distance, notice projectile chance, notice vehicle chance, **combat / guard / non-combat perception time** (seconds), surprise distance, panic when surprised, friend-killed and leader-killed panic chances, danger triggers (visible, shooting, shooting near us, damaging us), idle facing / aiming / looking time bounds, target search time, pursuit position time, melee attack delay.
- `actor_variant` tag (https://c20.reclaimers.net/h1/tags/actor_variant/): **burst geometry** ("burst origin radius: the starting point of the burst, randomly to the left or right of the target"; burst origin angle; "burst return length: how far the burst point moves back towards the target"; burst duration; burst separation; burst angular velocity), projectile error angle, **first burst delay time** ("the delay in seconds before the actor starts its first burst on a new target"), surprise delay time, surprise fire wildly time, **target tracking** (0 fires at the starting location, 1 follows perfectly), **target leading** (0 aims at the target, 1 predicts lead perfectly).
- Whether these systems can drive biped "player" bots in MCC multiplayer is an engine question for tracks 03/04. Even if we write our own aim code, the parameter set is a proven, Halo-tuned vocabulary.

### 2.5 Related Isla technique: occupancy maps for "where did he go?"
Isla adapted robotics occupancy maps for searching a hidden target: a grid of probabilities that the target is in each cell, diffused to neighbours each tick, with cells the searcher can see (and that are empty) zeroed and the map renormalized. Described in AI Game Programming Wisdom 3 (2006, **UNVERIFIED** chapter details) and used as the core of Isla's stealth game Third Eye Crime: https://ojs.aaai.org/index.php/AIIDE/article/view/12663 . This is the right model for last-known-position memory that degrades believably.

---

## 3. Classic human-like bot work

### 3.1 Quake III Arena bot (J.M.P. van Waveren, id Software, 2001)
The thesis "The Quake III Arena Bot" (TU Delft, 2001) describes a layered architecture (AAS navigation, fuzzy logic, goal stack); my download of the thesis PDF failed (**UNVERIFIED** thesis text), but the GPL source is authoritative. Bot "characteristics" are per-bot personality floats (https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/chars.h):
- `ATTACK_SKILL`, `VIEW_FACTOR` (view angle change factor), `VIEW_MAXCHANGE` (max degrees/s), `REACTIONTIME` (seconds, 0 to 5), `AIM_ACCURACY` (overall and per weapon), `AIM_SKILL` with documented bands: "> 0.0 && < 0.9 = aim is affected by enemy movement; > 0.4 && <= 0.8 = enemy linear leading; > 0.8 && <= 1.0 = enemy exact movement leading; > 0.5 && <= 1.0 = prediction shots when enemy is not visible; > 0.6 && <= 1.0 = splash damage by shooting nearby geometry".
- Personality: `CROUCHER`, `JUMPER`, `WALKER`, `WEAPONJUMPING`, `AGGRESSION`, `SELFPRESERVATION`, `VENGEFULNESS` ("how likely the bot is to take revenge"), `CAMPER` ("tendency to camp"), `EASY_FRAGGER`, `ALERTNESS` (view distance), `FIRETHROTTLE` (how much it fires), plus chat traits (`CHAT_INSULT`, `CHAT_CPM` typing speed, etc).

Concrete mechanics in `ai_dmq3.c` and `ai_main.c` (https://github.com/id-Software/Quake-III-Arena/tree/master/code/game):
- Enemy origin and velocity are **re-sampled only every 0.5 s**; if aim skill is below 0.9 and the enemy moved more than 48 units and **changed direction** (velocity dot product < 0), accuracy is multiplied by 0.7. This directly models humans being wrong-footed by strafe reversals.
- Random aim noise: direction += 0.3 x random x (1 - accuracy) per axis, plus pitch/yaw spread of 6 x weapon spread x random x (1 - accuracy).
- For hitscan weapons, accuracy is scaled by 0.6 to 1.0 with distance up to 150 units, i.e. close fast targets are harder (angular speed).
- Invisible enemies: 90% of the time accuracy x 0.4.
- Reaction time: `0.5 x REACTIONTIME` delay before aiming at a newly sighted (or teleported) enemy, but only applied for aim skill > 0.95 in this code path.
- View control: an "over reaction" model where angular speed accumulates toward the desired speed and is damped by `0.45 x (1 - factor)`, capped by `VIEW_MAXCHANGE` (minimum 240 deg/s). This creates overshoot and settle, a cheap human-looking flick.
- Combat strafing: strafe direction considered for change every `0.4 + (1 - attack_skill) x 0.2` s (plus up to 0.2 s jitter for skilled bots), then flips with only 6.5% chance per check ("some magic number :)"); 10% chance to back off a little each move; low-skill bots (attack skill <= 0.4) only walk toward or away. Jump and crouch during attack are rolled against `JUMPER` and `CROUCHER`.
- Camping: camp duration includes `180 x camper` seconds.
- Team chat replies are scheduled `2 x random()` seconds later (`teammessage_time`), a built-in information delay.

CTF team orders in `ai_team.c` (https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_team.c): a bot team leader sorts teammates by travel time to base and by stated task preference (defender, attacker, roamer) and splits roles by flag state:
- Both flags at base: passive 50% defend / 40% attack; aggressive 40% / 50%.
- Both flags taken: about 40% defend / 50% attack.
- Our flag taken: passive 30% defend / 70% go get the enemy flag; aggressive 20% / 70%.
- We hold their flag: "60% will defend the base, 30% accompanies the flag carrier".
- Leadership itself is negotiated with randomized timers (e.g. ask for a leader after `5 + random x 10` s), so bot teams do not all speak on the same frame.

### 3.2 Soar Quakebot humanness study (Laird and Duchi, AAAI Fall Symposium 2001)
Source: https://www.qrg.northwestern.edu/Resources/aigames.org/2001/Laird.pdf
- Parameters varied: decision time (5 levels), aggressiveness, tactics complexity, aiming skill (poor, "good" = shoot at the enemy's current location, "best" = superhuman lead using exact depth and velocity).
- Method: bots and humans played an expert; their first-person views were videotaped; 8 judges (3 per tape) rated humanness 1 to 10 blind and gave a binary human/computer call.
- Results: humans rated 6.83 to 8.25; highest bot 6.7. Humanness by decision time: 0.50 s = 4.3, 0.25 s = 2.6, **0.10 s = 6.3** (unanimously judged human), 0.05 s = 5.6, AFAP = 5.0. Humanness by aim: poor 6.7, good 6.7, **best 5.0** ("judges recognized that the best aiming skill was unlikely to be possible by a human"). Skill rose monotonically as decision time fell; aiming skill strongly drove win rate (0.0 / 0.56 / 0.93).
- The authors note human decision cycles are commonly modeled at 50 to 100 ms, before adding perception and motor time.
- Practical conclusion: you can scale skill by decision time and aim **within** the human band without losing humanness; leaving the band in either direction (too slow, or perfect) is what judges catch.

### 3.3 Unreal Tournament bots (Steve Polge, Epic)
- Bot state flow: roam under "FreeLance" orders collecting weapons and powerups; on seeing or hearing a player go to "Acquisition" (decide where to attack from), then "Attacking". Defend orders use mapper-placed DefensePoint actors (flag bases, sniping spots). Source (community wiki, written partly from guesswork): https://unrealarchive.org/wikis/unreal-wiki/Legacy:Bot_Support_(UT).html
- Polge said bot aim should resemble human aim with similar strengths and weaknesses that shift with circumstances (German interview): https://www.pcgames.de/Unreal-Tournament-3-Spiel-40655/Specials/Interview-mit-Steve-Polge-603648/2/
- UT2004 has 8 skill levels Novice to Godlike. **UNVERIFIED** community claims: Godlike aims less than 1 degree off, has 360 degree view without line-of-sight limits, and turns in under half a second; bots dodge instantly after landing and react instantly to fired rockets, which real players cannot; experienced players still beat Godlike 1v1 because bots are predictable. Source: https://www.unrealarchive.org/wikis/the-liandri-archives/Bot.html . These are exactly the "robotic tells" to avoid.
- Known CTF weakness reported by players: defenders abandon posts to chase the carrier instead of ambushing (https://unrealarchive.org/wikis/unreal-wiki/Legacy:Bot_Support.html, community forum level evidence).

### 3.4 The 2K BotPrize (UT2004 Turing test, 2008 to 2014)
- Format from 2010: a "judging game" where every player, bots included, carries a judging gun; humanness = human judgments / all judgments. Correct judgments kill the target for +10, wrong ones kill the shooter for -10. Source: UT^2 paper, https://nn.cs.utexas.edu/downloads/papers/schrum.cig11competition.pdf
- 2010 results: humans scored 35.5% to 80.0%; best bot 31.8%; UT^2 27.3% ("none of the entries are more human than the least human of humans"), same paper.
- 2012: MirrorBot 52.2% and UT^2 51.9% (reported as "52 percent"), human players averaged about 40%. Sources: https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/ and https://en.wikipedia.org/wiki/Computer_game_bot_Turing_test
- Test proposed by Philip Hingston (Edith Cowan University), https://ro.ecu.edu.au/ecuworks/594

**What made UT^2 human-like** (Schrum, Karpov, Miikkulainen):
- Priority module stack: UNSTUCK (top, "being stuck is a very bot-like behavior"), GET DROPPED WEAPON, IMPORTANT ITEM (even breaking off combat), GET GOOD WEAPON, JUDGE, **OBSERVE** (humans "stand back and watch other players"), SHIELD GUN, BATTLE, CHASE, RETRACE (replay human traces to explore), PATH (navgraph fallback).
- Combat evolved with multiobjective neuroevolution (maximize damage dealt, minimize damage received, minimize wall collisions), but outputs are filtered by hand-written human-likeness rules and "the bot's accuracy is reduced with respect to how much it and its target are moving, as well as the distance between the two individuals, in order to make the bot fallible in a human-like manner." The bot always looks at its opponent while fighting.
- Schrum: "If we just set the goal as eliminating one's enemies, a bot will evolve toward having perfect aim, which is not very human-like. So we impose constraints on the bot's aim, such that rapid movements and long distances decrease accuracy." (UT News, above).
- A database of recorded human paths, indexed by nav points, was replayed for exploration and for getting unstuck; time stuck was lowest and movement "looked qualitatively smoothest and most human-like" with traces used for both.

**What made MirrorBot human-like** (Mihai Polceanu), via https://cdn.aaai.org/ocs/12920/12920-57663-1-PB.pdf and https://hal.archives-ouvertes.fr/hal-00864153 :
- When it meets an opponent judged *unaggressive*, it records that player's low-level actions (aim, movement, fire, jumping, crouching, weapon choice) and replays them mirrored in real time, "borrowing" human-ness.
- Default mode navigates a graph but **perturbs each waypoint with random offsets** to hide bot-like trajectories, anticipates corners, and aims by predicting target position from velocity for smooth tracking.
- Follow-up note from the same group: the 50% bar is shaky because human judges themselves often score below it.

### 3.5 Counter-Strike bot (Michael Booth, Turtle Rock / Valve, CS 1.6 and Condition Zero, 2003 to 2004)
GDC 2004 talk "The Making of the Official Counter-Strike Bot" says believability required deep game knowledge and modeling human limits such as reaction time and attention: https://gdcvault.com/play/1022878/The-Making-of-the-Official . Source code (GPL reimplementation preserving Valve's code and comments) at https://github.com/rehlds/ReGameDLL_CS/tree/master/regamedll/dlls/bot :
- **Reaction queue:** `UpdateReactionQueue()` stores a snapshot of the most dangerous visible threat (plus whether it is reloading or shielded) each think into a 20-entry ring buffer and "rewinds" by `ReactionTime / thinkInterval` steps; the bot only acts on the threat it is "conscious" of (`GetRecognizedEnemy`). Perception lag, not motor lag, is the reaction model.
- **Aim focus** (`SetAimOffset`, cs_bot_weapon.cpp): imperfect bots "focus in" while not rotating their view; focus time = max(5 x (1 - accuracy), 2) seconds, capped at 75% bonus accuracy; moving the view resets focus. Aim error = range x 0.1 x (FOV / default FOV) x (1 - accuracy), randomized per axis and re-rolled every 0.25 to 1.0 s ("wiggle aim error").
- **Looking around** (`UpdateLookAround`, cs_bot_vision.cpp): turn toward enemy gunfire heard within 1000 units and suppress other look-arounds for 2 to 4 s; look at the last known enemy position for 2 to 3 s; when stationary glance at random "approach points" every 1 to 2 s (snipers 5 to 10 s, and only bots with skill > 0.4 pre-zoom); while moving, check precomputed "encounter spots" with a delay of (1 - skill)^4 x 10 to 30 s for low skill bots ("lower skills have exponentially longer delays").
- **Teamwork and going rogue** (cs_bot.cpp): every 10 to 30 s a bot re-rolls "rogue" status with chance 100 x (1 - Teamwork); rogues ignore team plans. Radio replies wait `1 + 2 x ReactionTime` s (plus 2 s more in some cases) and are ignored if the bot is busy or too far.
- Profile fields: `Skill`, `Aggression`, `ReactionTime`, `AttackDelay`, `Teamwork`, `AimFocusInitial`, `AimFocusDecay`, `AimFocusOffsetScale`, `AimFocusInterval`, weapon preferences (bot_profile.cpp in the same repo). Community-documented Condition Zero templates pair Skill 100 with 0.20 s reaction and 0 attack delay, and Skill 50 with 0.40 s reaction and 0.70 s attack delay (fan wiki, https://counterstrike.fandom.com/wiki/List_of_Tour_of_Duty_Terrorist_Bots/Normal , **UNVERIFIED** against the shipped file). A CS:GO tuning guide suggests measuring your own reaction time and setting bots similar; its author's was 0.22 s (https://steamcommunity.com/groups/p_nm/discussions/0/522730075468755846 ).
- CS:GO later moved bots to behavior trees with per-difficulty aim acquisition and tracking parameters (community page, https://developer.valvesoftware.com/wiki/User:Gazyi/CS:GO_Bot_Behavior_Trees , could not be fetched, **UNVERIFIED** values).

### 3.6 Team Fortress 2 bots (Valve NextBot, Michael Booth, 2010)
Source code released in Valve's SDK: https://github.com/ValveSoftware/source-sdk-2013/tree/master/src/game/server
- **Recognition time** (`CTFBotVision::GetMinRecognizeTime`, "return VISUAL reaction time"): Easy 1.0 s, Normal 0.5 s, Hard 0.3 s, Expert 0.2 s.
- **Aim tracking interval** (`CTFBotBody::GetHeadAimTrackingInterval`, "to allow realistic slop in tracking"): Easy 1.0 s, Normal 0.25 s, Hard 0.1 s, Expert 0.05 s; MvM spies forced to 0.25 s.
- **Head aim model** (NextBotPlayerBody.cpp): at each tracking sample, desired point = target point + lead time x target velocity; the bot computes an aim velocity that would close the error over one interval and then integrates that velocity until the next sample (re-timed with 0.8 to 1.2 jitter). Head is "steady" only below 100 deg/s; settle duration 0.3 s; saccade time 0.1 s at 1000 deg/s. **Virtual mousepad:** "After rotating through this angle [100 degrees], the bot pauses to 'recenter' its virtual mouse on its virtual mousepad" for 0.3 s (x0.9 to 1.1).
- **Memory:** a known entity becomes obsolete after 10 s without new information (NextBotKnownEntity.h).
- TF2 bots disengage when low on ammo, need a full reload (Hard/Expert), are below a health threshold, or are outnumbered; they seek health below a threshold; there is a convar for post-kill taunt chance. Source (community wiki): https://developer.valvesoftware.com/wiki/TFBot_Technicalities

### 3.7 Left 4 Dead survivor bots and the AI Director (Booth, 2009)
Slides: https://cdn.fastly.steamstatic.com/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf
- Survivor bots are "competent human player proxies" built on "Believability/Fairness": no perfect knowledge, simulated senses, simulated aiming, reaction times, reliable and predictable decisions.
- Trust rules: bots prioritize human teammates, cannot deal friendly fire, never use Molotovs, and if a bot gets far out of place "it is teleported near the team when no human is looking at it". (A cheat that is fine only because no one can see it.)
- Two concurrent behavior systems: Main (decisions, attention, targeting, attack) and Legs (stay near the team). This split maps well to "aim brain" versus "movement brain" for our bots.
- Reactive path following (steer toward a look-ahead point with local avoidance) because "following path directly looks robotic".
- **Adaptive dramatic pacing**, inspired by Counter-Strike's "spiky" rhythm: track each survivor's "emotional intensity" (rises with damage taken, incapacitation, nearby kills; decays when not engaged); states Build Up, **Sustain Peak for 3 to 5 s**, Peak Fade, **Relax for 30 to 45 s**. Relevant to us as a *team momentum* signal for the director, not as a way to rig PvP outcomes.

### 3.8 Killzone (Guerrilla Games)
- **Killzone 1 (PS2)**: "dynamic procedural combat tactics", position evaluation functions for position picking, tactical pathfinding, indirect fire and suppression (Straatman, van der Sterren, Beij): https://www.guerrilla-games.com/media/News/Files/gdce05_killzone_ai.pdf (not read in full; summary via search).
- **Killzone 2 multiplayer bots** (Tim Verweij MSc thesis 2007, basis for the shipped bots): https://www.guerrilla-games.com/media/News/Files/VUA07_Verweij_Hierarchically-Layered-MP-Bot_System.pdf
  - Three levels: faction leader (strategy), squad leader (HTN), individual. Highest and lowest layers do not talk directly.
  - Perception: stimuli filtered by receiver sensitivity, source, range and type; threats are **suspected** (belief), **confirmed** (knowledge of presence) or **identified** (exact identity). Footsteps can raise alert to "threats suspected". Hidden threats are predicted over areas not in clear sight; threats not perceived for a long time are forgotten.
  - Individuals message their squad leader when they first encounter an enemy, lose track of one, or see one killed. Squad leaders report task failure and combat engagement up to the faction leader.
  - "Bots would have to cheat by requesting the actual position of invisible teammates and enemy targets" without a last-known-position world model.
  - Level knowledge (which objective matters, choke points) is explicitly considered **not cheating** because experienced humans learn it.
  - Respawn trick: attackers who die mid-attack are not re-spawned until the fight resolves, so the squad regroups instead of trickling in.
  - Using an HTN planner "forces the developer to think about which data is actually needed", which prevents accidental cheating.
  - Playtest observation: during bot tests designers "started to play in a much more organized and strategic fashion ... communicated by shouting orders", i.e. organized bots made humans organize.
  - Self-criticism: bots regrouping by standing still was "less human like" ("any novice FPS player will say that it is best not to stand still").
- **Killzone 3** (Straatman, Verweij, Champandard, Morcus, Kleve, Game AI Pro ch. 29): http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf
  - Commander orders: Attack area, Defend area, Escort player, Advance to regroup point. Objectives (AdvanceToWaypoint, DefendMarker, AttackEntity, EscortEntity) each have a **weight** and an **optimal number of bots**; game-mode classes add and remove objectives (e.g. in Search and Retrieve the carrier's side creates Escort, the other side Attack carrier, and either may add base defense).
  - Assignment algorithm: (1) compute ideal distribution of bots then squads, (2) create squads, (3) remove excess squads, (4) assign the best objective to each squad, preferring previous assignment else distance, (5) unassign surplus bots, (6) put free bots in the closest needy squad. Dead bots choose the spawn with the best travel cost (including influence) to their squad.
  - Squads reason on a **strategic graph** (clustered waypoint areas) plus a per-faction **influence map** computed from friendly and enemy bots, players, turrets and drones per area, **recent friendly and enemy deaths**, smoothed by distance and blended with previous values over time. Squads path around enemy-controlled areas and pick regroup markers by influence; a penalty on areas already chosen by friendly squads "provides variation for repeated attacks and spreads out simultaneous attacks."
  - Individuals have view cones and maximum distances, so "the bot's idea of the world may be believably wrong"; they can ignore orders to survive.

### 3.9 F.E.A.R. squad coordination (Jeff Orkin, GDC 2006)
Paper: https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf
- Individual AI uses GOAP (A* over actions) with only three FSM states (Goto, Animate, UseSmartObject).
- A global coordinator re-clusters AI into squads by proximity. Simple squad behaviors only: Get-to-Cover, Advance-Cover (one member suppresses), Orderly-Advance, Search (pairs). Individuals may prioritize their own goals (fleeing a grenade) over orders.
- "We actually did not have any complex squad behaviors at all in F.E.A.R." Pincers and retreats emerged from simple orders plus geometry.
- Dialogue cues the player that coordination is intentional: make lines a **dialogue between two AIs** (one asks status, the other answers; one asks "see anything?", the other calls a known or suspected position), and use dialogue to explain inaction. Implied reinforcements ("calling for backup") were pure dialogue.

### 3.10 Battlefield
- EA SEED's Battlefield 1 self-learning agents watched about 30 minutes of human play then trained for six days; a single neural network controlled them; they sometimes moved like a unit and restocked ammo but also "spun randomly in circles", were weak at planning, and lost (not badly) to DICE developers. Source: https://www.pcgamer.com/au/ea-shows-off-self-teaching-ai-bots-that-have-trained-in-battlefield-1-for-six-days
- Battlefield 2042 "AI soldiers" fill up to 64 slots in 128-player modes, humans always prioritized; no evidence they used the SEED learning approach. Source: https://mp1st.com/news/battlefield-2042-ai-soldiers-will-be-used-to-fill-128-player-matches-hazard-zone-not-battle-royale
- Takeaway: learned agents still need hand constraints to avoid inhuman tells; not a shortcut for our scope.

### 3.11 Paragon bots (Epic, Game AI Pro 3 ch. 32)
http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter32_Paragon_Bots_A_Bag_of_Tricks.pdf
- Bots aimed perfectly at higher difficulties (projectile travel time hid it); easy bots add angle deviation.
- Players complained all bots raced down lanes at match start, so a scripted one-time opening was added (wait for minions, then flow down until seeing an enemy). Same lesson as Infinite's "all went the same way to start": **openings need per-bot variation and humans' social pacing.**
- Behavior "moods" (attacking, fleeing) exported from the behavior tree to drive focus and movement-ability permissions.

---

## 4. Humanizing techniques catalogue (with numbers)

### 4.1 Reaction time
- Lab simple reaction times vary widely by method: e.g. visual 148 ms and auditory 141 ms in one student sample (https://ajol.info/index.php/ahs/article/view/176248 ); auditory significantly faster than visual in another (https://pmc.ncbi.nlm.nih.gov/articles/PMC4456887 ); other baselines around 290 to 320 ms. The Human Benchmark online test reported a 251 ms median and 262 ms mean in 2015 with a long slow tail (https://ibmathsresources.com/2015/03/20/reaction-times-how-fast-are-you ). Online tests include display and input latency.
- In-game recognition is a *choice* reaction (is it an enemy, which weapon, am I safe) so it is slower than simple RT. Shipped values: TF2 0.2 to 1.0 s; CS bot templates about 0.2 to 0.4 s (community); Laird's best humanness at 0.1 s decision cycles *plus* separate perception.
- Use a **right-skewed distribution** (e.g. log-normal), not a constant: real RT distributions have a long slow tail (the 2015 mean above the median shows this). Add modifiers: peripheral targets slower (Crytek gives peripheral stimuli "a longer attack time", http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter31_Crytek's_Target_Tracks_Perception_System.pdf ), sound-cued targets faster than surprise targets, pre-aimed lanes (camping) faster.

### 4.2 Aim models
- **Two-phase movement:** a ballistic primary movement covers most of the distance, then slower feedback-driven corrections (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5744918/ ). A 2024 rapid-aiming study reports overshooting primary submovements were more common than undershooting, especially for faster movements (via abstract, https://link.springer.com/10.1007/s00221-024-06784-0 , **UNVERIFIED** in full text).
- In Aim Lab data from 32 pro and semi-pro players, flicks are modeled as reaction, sigmoid ballistic movement (accelerate, peak at midpoint, decelerate), shot timing (fire after landing for "flick-and-land" vs during motion for "swipe"), then corrective submovements on a miss; smaller targets produced more undershoot ("hypometric") (https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.979293/full ).
- **Fitts' law:** FPS targeting was shown to conform to Fitts' law (Looser, Cockburn, Savage 2005, cited in https://arxiv.org/pdf/2203.12050 ): MT = a + b log2(A/W + 1). Caveat: the Aim Lab study found combined data "poorly characterized by Fitts Law" (Frontiers, above). Use Fitts for the *duration* of a flick, not as gospel.
- **Laggy tracking:** NextBot's periodic re-sampling with velocity integration (Section 3.6) produces natural trailing, overshoot on direction changes and catch-up. Quake III's 0.5 s velocity sampling plus 0.7x accuracy on direction change does the same more crudely.
- **Lead error:** Halo CE `target leading` 0 to 1; Quake III bands (linear leading only above 0.4 aim skill, exact leading only above 0.8). Most humans lead imperfectly; Laird's "superhuman lead" was spotted by judges.
- **Focus-in:** CS bots get more accurate the longer the view stays still on a target (2 to 5 s), and lose it when they turn. Matches human "settle then shoot".
- **Visible misses:** Halo CE burst geometry starts bursts beside the target and walks onto it. Game AI Pro 3 ch. 33 (http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter33_Using_Your_Combat_AI_Accuracy_to_Balance_Difficulty.pdf ) uses "hit tokens" with delays scaled by distance (closer than 5 m halves the delay, past 15 m no effect), stance (crouch doubles), cover (doubles), facing away (doubles), approach angle (running at the AI halves), with misses placed visibly around the target. That is PvE difficulty control; for PvP it is useful only as a principle (misses must land where a human's miss would land).
- **Controller vs mouse:** in Halo Infinite top-20 data, KBM and controller headshot accuracies were similar on average (68.7% vs 71.5%) but distributions differ; Reddit-level data reports large accuracy gaps by input (https://lr.in.psf.lt/r/halo/comments/r3es60/comment/hmajwb0/?context=3 , **UNVERIFIED**). MCC players on controller get aim assist; a bot emulating controller input through the game's own assist would inherit authentic Halo aim feel (**UNVERIFIED** feasibility; engine track).
- **Accuracy targets for Halo:** I found no reliable published "typical accuracy %" per Halo title (**UNVERIFIED**). Plan to measure from human telemetry or Halo Waypoint/Halo Tracker style stats (definition: share of shots that hit enemies, https://support.halowaypoint.com/hc/en-us/articles/30643133470868-Where-to-View-Halo-Infinite-Player-Stats ).

### 4.3 Perception limits
- **FOV shapes:** Splinter Cell Blacklist found plain cones model peripheral vision and long-distance vision badly; they used a box plus cone plus peripheral shapes, with a detection timer scaled by distance, lighting and NPC state; "predictability does not mean repetitiveness" (consistent distances and timings, varied barks): http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter28_Modeling_Perception_and_Awareness_in_Tom_Clancy's_Splinter_Cell_Blacklist.pdf
- **Envelopes:** Crytek "target tracks" store one ADSR envelope per stimulus type per target; target value = highest envelope; peripheral sight has lower peak and slower attack (Section 4.1 link).
- **Sound:** CS bots turn toward enemy gunfire within 1000 units; Killzone footsteps raise alert to "suspected" without identifying. Halo-specific: the **motion tracker** is the human's main non-visual sense (Infinite's bots were given radar use at higher tiers, Section 1.2).
- **Memory and forgetting:** TF2 forgets after 10 s; CS looks at last known position for 2 to 3 s; Killzone predicts hiding waypoints and eventually loses track; Isla occupancy maps diffuse belief. A behavior-cloned CS:GO agent was judged non-humanlike partly because "it quickly forgets" enemies behind cover and ignores "second-order clues ... (e.g. teammates firing in some direction)" (https://arxiv.org/abs/2104.04258 ). Forgetting too fast is as bad as remembering too well.

### 4.4 Decision latency and imperfect information
- Think at human cadence (Laird: around 0.1 s decisions) and **commit** to choices. Wetzel and Anderson found players see AIs that switch targets too often as "computery"; humans are **persistent** and take **revenge** on whoever hurt them (http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter04_Player_Perception_of_AI_Opponents.pdf ). Quake III also has `VENGEFULNESS`.
- Halo 2's binary relevancy plus prioritized list gives stable, explainable choices; Halo CE explicitly preferred reactive variation over randomness.

### 4.5 Mistakes on purpose ("hustling")
- Wetzel and Anderson: players are "bad at determining AI's strategies and detecting randomness and cheating"; "hustling" AIs that throttle themselves when ahead were perceived as just as difficult as non-hustling ones. What players do catch is **visible error severity**: one inhumanly stupid mistake outweighs many good plays (their billiards example: a pro-level shot then three easy misses).
- So: allowed mistakes must be **human mistakes** (overshoot on a flick, losing track after a strafe reversal, reloading at a bad time, greed for a power weapon, over-chasing), never bot mistakes (walking into walls, staring at a wall, jittering at a ledge, stuck loops). UT^2 put UNSTUCK at top priority for this reason.

### 4.6 Personality and playstyle profiles
- Quake III's characteristic set (camper, jumper, croucher, aggression, self-preservation, vengefulness, easy-fragger, fire throttle, alertness, weapon and item weights, chat style) is a proven schema (Section 3.1).
- CS adds `Teamwork` (drives rogue chance and follow behavior) and `Aggression`.
- Halo 2 adds designer "styles" (whitelists of allowed behaviors) and parameter inheritance (child profiles define only deviations).
- Archetypes for us: Slayer-rusher, flanker, camper/anchor, power-weapon chaser, objective player (runner), support/escort, sniper, grenade spammer. Each is a parameter preset plus a style whitelist, not separate code.

### 4.7 Tilt and momentum
- Research on tilt is mostly self-report; one validated scale describes tilt as tied to stressful situations and persisting about 30 minutes (https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1385242/full ); competitive motivation, anger and hours played raise tilt risk (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11082399/ ). Objective evidence that tilt lowers performance is thin (Akron thesis proposal, https://ideaexchange.uakron.edu/honors_research_projects/2188 ).
- Design implication (design inference, not a cited result): model tilt as a **style shift** (more aggression, more revenge targeting, worse self-preservation, faster peeks) after deaths in a short window, not as an accuracy nerf. Keep it subtle and per-personality.

### 4.8 Movement
- Strafe reversal timing matters: Quake III checks every 0.4 to 0.6 s and flips rarely (6.5% per check), producing long runs with occasional reversals; human Halo strafing data should replace these constants (see track 05).
- Smooth paths: L4D reactive path following; MirrorBot random offsets around waypoints; UT^2 replayed human traces. Judges in the "Navigates Like Me" study penalized wild camera swings, wall collisions and too-slow movement; reward shaping against those three fixed it (https://arxiv.org/abs/2303.02160 ).
- Halo Infinite's GDC talk title literally frames this as "the combat dance": strafe, jump, crouch, grenade bounce, equipment (Section 1.4). Halo-specific moves (jump shots, crouch-jumps, retreating to recharge shields, peeking) belong in track 05 and should be expressed as behaviors with human-measured timing.
- Avoid standing still while waiting (Killzone 2 self-critique).

### 4.9 Idle head motion and looking around
- CS: random approach-point glances every 1 to 2 s when stationary (5 to 10 s for snipers), encounter-spot checks while moving, look at last known enemy position, snap to dangerous noises.
- NextBot: saccades (0.1 s), settle (0.3 s), and virtual-mousepad recentering pauses after 100 degrees.
- UT^2 OBSERVE: humans sometimes just watch fights.

### 4.10 Weapon and power-item pursuit, item timing
- UT^2 ranked "get dropped weapon", "important item" and "get good weapon" above fighting.
- Infinite bots needed explicit **spreading out** for weapon pickups (Section 1.3).
- Human timing knowledge in Halo: Halo 3 MLG settings used fixed timers, e.g. Sniper 150 s and Rockets 180 s, power-ups 120 s, raised from defaults "to promote more map movement" (https://www.halopedia.org/MLG_(playlist) , https://xboxaddict.com/news/9003/MLG-Playlist-is-Live-in-Halo-3.html ). In Halo 2 some power weapons do not respawn while held (https://www.rampancy.net/blog/narcogen/22052007/replayability_and_brute_force ). Fans built timer apps with alerts at 20, 10 and 2 s (https://mikechambers.com/blog/files/timetrocity/ ). Knowing timers is human skill (Killzone thesis: level knowledge is not cheating), so expert bots may time; novices should not.

### 4.11 Avoiding robotic patterns
Checklist distilled from the sources: no instant 180s (NextBot steady-rate limits, mousepad pauses); no frame-perfect reaction to projectiles (UT2004 complaint); no identical openings (Infinite, Paragon); no pack behavior around one item (Infinite); no long stand-still regroups (Killzone 2); no wall hugging or collisions (Navigates Like Me); no repeated identical barks (Splinter Cell); no rapid target switching (Wetzel); no omniscient tracking through walls (Halo CE "no cheating", Killzone thesis).

### 4.12 Difficulty scaling without cheating, and rubber-banding
- Scale **perception latency, tracking interval, aim error, lead quality, decision cadence, and tactical knowledge**, as Q3, CS, TF2 and Laird all do. Laird shows these can scale skill while staying human.
- Halo CE's lesson: tougher reads as smarter; for PvP we cannot add health, so lower tiers should still look *competent* (good movement, sensible positioning) and lose through human-like slowness and errors.
- Dynamic difficulty: Hunicke's Hamlet adjusted NPC accuracy and damage reactively to prevent repeated deaths (https://users.cs.northwestern.edu/~hunicke/pubs/Hamlet.pdf ); Infinite's Academy aimed to spawn bots "comparable to your own skill level" (Game Informer). For PvP, rubber-banding should be slow (between rounds or over minutes), bounded, and applied through the same knobs, never through hidden damage or hit tokens on humans. Wetzel's data suggests mild hustling goes unnoticed; getting caught is the failure mode.

---

## 5. Team coordination and the per-team AI director

### 5.1 Architecture patterns that shipped
| Game | Strategic layer | Mid layer | Individual | Info flow |
|---|---|---|---|---|
| Halo 3 (campaign) | Designer task tree, priorities, capacities | Squads assigned by greedy min H(s,t) | Behavior tree with styles | Squads pushed/pulled as tasks toggle |
| Killzone 2/3 (MP bots) | Commander: weighted objectives, ideal bot counts | Squad HTN on strategic graph + influence map | Autonomous HTN bot, can ignore orders | Orders down; completion, failure, threat sightings up |
| Quake III (CTF) | Elected bot team leader | none | Bot with personality | Leader issues orders by chat/voice with random delays |
| CS 1.6/CZ | Bot manager scenario logic | Radio commands | Bot with Teamwork/rogue | Radio replies delayed 1 + 2 x RT |
| F.E.A.R. | Global coordinator clusters squads | Simple squad behaviors | GOAP soldier | Dialogue makes coordination visible |

### 5.2 Blackboard and information honesty
- Each team's director should only know what its bots perceived and reported (Killzone: first seen, lost track, saw kill; Halo CE: individual knowledge, no ESP). Deaths are reported because a dead human sees the killcam and knows roughly where they died; **UNVERIFIED** which Halo titles show killcams or killer location (track 05).
- Store reports as timestamped, decaying beliefs (occupancy map or per-area threat values), like Killzone's suspected / confirmed / identified tiers.

### 5.3 Influence and threat maps
- Killzone 3 recipe: per area, count friendly and enemy units, add recent friendly and enemy deaths, smooth by distance, blend with previous values over time (Section 3.8).
- Implementation notes from Champandard's influence mapping tutorial: sources can be entities or events (gunfire, damage), use double buffering when propagating, a 2D grid or area graph is safest, expect heavy tuning (https://www.gamedev.net/tutorials/programming/artificial-intelligence/the-core-mechanics-of-influence-mapping-r2799 ). Dave Mark's modular influence map chapter: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf
- Death heatmaps as static priors: Bungie published Halo 3 death/kill heatmaps filterable by weapon (https://www.coolinfographics.com/blog/2009/1/12/halo-3-heatmaps.html ) and used heatmaps internally in development (Wired summary, https://blog.kartones.net/post/wired-article-on-halo-3/ ). We can build per-map priors from our own human sessions and bot matches.

### 5.4 Objective assignment for CTF
- Use the Halo 3 / Killzone 3 pattern: objectives (Defend flag, Attack/steal flag, Escort carrier, Hunt enemy carrier, Hold midfield / control power weapon) each with weight, desired count, filters (only a sniper-equipped bot can take "sniper overwatch"), and assignment by greedy cost (travel time, current role inertia, personality fit, weapon fit).
- Starting ratios to tune from Quake III's shipped CTF logic: both flags home 50/40 (passive) or 40/50 (aggressive) defend/attack; our flag taken 30/70 or 20/70; we hold theirs 60% defend, 30% escort.
- Role inertia (Killzone: keep existing squads on their objectives, avoid "unneeded exchanges"; avoid removing bots mid-order "causing the appearance of indecisive behavior").
- Personality overrides: CS-style rogue chance so some bots ignore the plan, like real pub players.

### 5.5 Callouts as messages, with delay
- Callouts are generated from the blackboard and spoken by a bot that plausibly saw it (or the director voice, per our design). Two-party exchanges and explanations of inaction (F.E.A.R.) make it feel real.
- Delay and degrade: CS radio replies `1 + 2 x ReactionTime` s; Quake III team chat `2 x random()` s; Killzone squad messages are held until the next squad update. Recommended: a 0.5 to 2.5 s delay distribution from the triggering event to the callout, location rounded to named areas, enemy count fuzzed, and callouts expiring after a few seconds unless refreshed.
- Infinite planned exactly this ("Spartans will share some information with each other").

### 5.6 Team momentum (director pacing)
- L4D's intensity model (damage taken, nearby kills, decay when not engaged) can track each team's stress and momentum. In PvP it should drive **behavioral** responses a human team would show (fall back and regroup after a wipe, push after a multi-kill, stack defense when the flag is threatened), not spawn manipulation.

---

## 6. How human-likeness is measured

1. **Blind judging in first person** (Laird 2001): judges watch the bot's own view on video and rate 1 to 10 plus a binary call. Cheap and sensitive to aim and timing.
2. **In-game judging** (BotPrize 2010 to 2014): players judge during play; humanness = human calls / total. Expect humans themselves to score around 40 to 80%, so compare bots against the human baseline, not 50% (https://nn.cs.utexas.edu/downloads/papers/schrum.cig11competition.pdf ). Active participants judge differently from third-person viewers (summary of a 2014 study via search, **UNVERIFIED** in full text).
3. **Side-by-side video Turing test with coded justifications** (Milani et al., CHI 2023, https://arxiv.org/abs/2303.02160 ): judges pick which of two videos is more human, justify, rate certainty; responses coded for smoothness, goal-directedness, collision avoidance; significance tested against chance.
4. **Telemetry similarity** (Pearce and Zhu 2021, https://arxiv.org/abs/2104.04258 ): 100 minutes of positions on a 60 x 60 grid; compare histograms by Earth mover's distance (the agent scored 0.447 to 0.349 versus human data while the built-in bot scored about 0.62 to 0.64, lower is more similar). Also report kills per minute and K/D against humans of known skill.
5. **Behavioral imitation statistics** (Gorman, Thurau, Bauckhage, Humphrys 2006): statistical reproduction, believability tests and performance comparisons as three separate axes (https://www.humphryscomputing.com/Publications/SAB_06.pdf , not read in full).
6. **Distribution metrics we should log per bot and per human:** reaction time to first shot, time-to-kill and time-to-death distributions, accuracy and headshot rate by weapon and range, camera angular velocity and acceleration histograms, overshoot ratio on flicks, strafe reversal intervals, jump and crouch frequency in fights, target switch rate, time stationary, path entropy and map coverage EMD, grenade throw rate and success, power-weapon pickup share, callout-to-event delay. Infinite's own feedback items ("too accurate", "same route", "pack chasing") are each one of these metrics drifting from human.
7. **Perception surveys**: Halo CE asked testers difficulty and intelligence; Wetzel and Anderson asked difficulty, realism, fun. Keep both "how hard" and "how human" questions since they correlate.

---

## 7. Recommendations for our Halo bots

Each row maps a researched technique to something buildable. "Priority" is my suggested order for Slayer then CTF.

| # | Technique (source) | What we build | Priority |
|---|---|---|---|
| 1 | Perception delay queue (CS reaction queue; TF2 min recognize time) | Per-bot ring buffer of perceived world state; decision layer reads the snapshot `RT` ago. RT sampled per encounter from a log-normal fit to human data (start median about 0.25 s for "average", 0.18 to 0.2 s for top tier), with modifiers for periphery, motion tracker pre-warning, and pre-aimed angles | P0 |
| 2 | Laggy tracking aim controller (NextBot head aim; Q3 0.5 s sampling and direction-change penalty) | Aim velocity recomputed every tracking interval (tier presets about 0.25 / 0.15 / 0.08 / 0.05 s, jittered 0.8 to 1.2), lead time below perfect, error spike on target strafe reversal | P0 |
| 3 | Ballistic flick plus corrections (motor control literature; Fitts) | Flick duration from Fitts (a, b fit to human captures), sigmoid velocity profile, configurable overshoot probability and magnitude, 1 to 2 corrective submovements; swipe vs flick-and-land as a personality trait | P0 |
| 4 | Halo burst geometry and first-burst delay (Halo CE actor_variant) | Misses that start beside the target and walk in; first-shot delay on new targets; per-weapon tracking/leading factors | P0 |
| 5 | Virtual mousepad and steady-rate limits (NextBot; CS:GO BC agent) | Max turn rate, brief pause after about 100 degrees of continuous turn (KBM profile); stick acceleration and deadzone model for controller profile | P1 |
| 6 | Aim focus (CS SetAimOffset) | Accuracy grows while view is still on target, resets on large turns; drives "camper is deadly on his angle" naturally | P1 |
| 7 | Individual knowledge and forgetting (Halo CE; Killzone suspected/confirmed/identified; TF2 10 s; occupancy maps) | Per-bot belief store with last-known positions, diffused occupancy for hidden enemies, confidence decay, forget after about 5 to 10 s without cues; never read true positions | P0 |
| 8 | Motion tracker as a sense (Infinite bots used radar) | Bots read only what the HUD radar would show them (moving/firing enemies within range, per-game rules); crouch-walking enemies invisible to it | P0 |
| 9 | Look-around behavior (CS UpdateLookAround) | Glance at approach points when holding, check encounter spots while moving (lower skill checks less), snap to gunfire and grenade sounds, hold last-known position 2 to 3 s | P1 |
| 10 | Prioritized behavior tree with impulses and stimulus behaviors (Halo 2) | Bot brain as prioritized list with binary relevancy; event-inserted stimuli (shield popped, grenade landed, teammate died nearby); "styles" whitelist per personality | P0 |
| 11 | Utility-weighted action choice (Infinite "weighing actions", **UNVERIFIED** architecture) | Scorers for fight / disengage-to-recharge / grab weapon / grab powerup / objective, used inside the tree where choices compete | P1 |
| 12 | Personality profiles (Q3 characteristics; CS Teamwork/rogue; Halo 2 inheritance) | Data files with inheritance: camper, rusher, flanker, power-weapon chaser, objective runner, support, sniper, grenade spammer; traits: aggression, self-preservation, vengefulness, persistence, jumper, croucher, grenade throttle, teamwork | P0 |
| 13 | Persistence and revenge (Wetzel; Q3 vengefulness) | Target stickiness with switch cost; revenge weight toward last killer; tilt window after deaths that shifts style, not accuracy | P1 |
| 14 | Human-mistake library (Wetzel visible error severity; UT^2 unstuck priority) | Allowed mistakes: overshoot, lost track after strafe, bad reload timing, greed, over-chase, wasted grenade. Disallowed: stuck, wall staring, jitter. Top-priority unstuck behavior and watchdogs | P0 |
| 15 | Movement "combat dance" (Infinite GDC; Q3 strafe timing; track 05 data) | Strafe patterns with human-measured reversal intervals, jump shots, crouch at kill moments, peek and retreat-to-recharge, grenade bounce lineups per map | P0 |
| 16 | Smooth navigation (L4D reactive path following; MirrorBot waypoint jitter; UT^2 human traces) | Look-ahead steering, randomized lane offsets, optional replay of recorded human routes per map | P1 |
| 17 | Opening and pickup variation (Infinite feedback; Paragon opening) | Director assigns distinct opening routes and spreads pickups so bots never pack on one weapon | P0 |
| 18 | Item timing as skill (MLG timers; Killzone "level knowledge is not cheating") | Timer knowledge only for experienced profiles, with timing error; novices react to seen spawns only | P2 |
| 19 | Team director as objectives plinko (Halo 3 H(s,t); Killzone 3 commander) | Per-team director: objective list with weights, desired counts, filters; greedy assignment by cost (travel, role inertia, personality fit, loadout); CTF roles runner, escort, defender, midfield/power control, carrier hunter; Q3 ratios as initial tuning | P0 (CTF) |
| 20 | Influence and death maps (Killzone 3; Halo 3 heatmaps) | Per-team area influence from reported sightings and deaths, temporally smoothed; route penalty to spread attacks; static per-map priors from logged matches | P1 |
| 21 | Honest information flow (Killzone messages; Halo CE no ESP) | Director only ingests bot reports (seen, lost, killed, died at) and death events; no global truth | P0 |
| 22 | Delayed, fuzzed callouts (CS radio delay; Q3 chat delay; F.E.A.R. dialogue) | Callout queue with 0.5 to 2.5 s delay, named-area locations, fuzzed counts, expiry; two-voice exchanges ("Where?" "Blue flag, two of them") and inaction explanations | P0 |
| 23 | Rogue and pub behavior (CS rogue chance) | Some bots ignore director orders periodically according to Teamwork | P1 |
| 24 | Team momentum (L4D intensity, behavior only) | Team stress meter driving regroup after wipes, push after multi-kills, turtle when flag threatened | P2 |
| 25 | Difficulty without cheating (Laird; Q3/CS/TF2 knobs; Hunicke) | Tiers scale RT, tracking interval, aim error, lead, decision cadence, tactical knowledge, teamwork; optional slow, bounded adaptation between rounds; no hit tokens or damage scaling against humans | P0 |
| 26 | Measurement harness (BotPrize; Laird; Milani; Pearce EMD) | Telemetry logger for bots and humans with the metrics in Section 6.6; blind clip review tool (side-by-side, justification text); map-coverage EMD report per map; humanness dashboard per tier | P0 |

### Suggested default tier table (starting points to tune against human telemetry)
Values are synthesized from the sources above (TF2, CS, Laird, Q3), not measured in Halo; treat as **UNVERIFIED for Halo** until our own captures replace them.

| Parameter | Novice | Average | Strong | Top |
|---|---|---|---|---|
| Recognition RT median (s) | 0.45 | 0.30 | 0.22 | 0.18 |
| Aim tracking interval (s) | 0.30 | 0.18 | 0.10 | 0.05 |
| Lead quality (0 to 1) | 0.3 | 0.6 | 0.8 | 0.9 |
| Decision cadence (s) | 0.20 | 0.12 | 0.10 | 0.08 |
| Flick overshoot chance | 0.5 | 0.4 | 0.3 | 0.25 |
| Memory before forgetting (s) | 4 | 6 | 8 | 10 |
| Uses motion tracker well | no | partly | yes | yes |
| Item timing knowledge | none | rough | good | precise with error |
| Teamwork (rogue chance) | 0.4 (60%) | 0.6 | 0.8 | 0.9 |

### Open questions for other tracks
1. Can MCC's campaign actor systems (perception time, burst geometry) be reused for multiplayer bipeds, or must aim and perception be reimplemented? (tracks 03, 04)
2. What are real Halo human numbers per title: strafe reversal intervals, accuracy by weapon and range, jump-shot frequency, shield-recharge retreat thresholds, typical opening routes? (track 05)
3. Which titles expose killcams, location names, or other information a dead or living human legitimately has? (track 05)
4. Get the two Halo Infinite GDC 2022 talks (Stern; Chin-Deyerle) when GDC Vault is back and append their specifics here.

---

## Source index
- Halo Infinite: https://kotaku.com/why-halo-infinite-s-bots-act-so-much-like-people-1847511140 ; https://www.gameinformer.com/preview/2021/11/15/how-halo-infinites-bots-became-so-ruthless-and-helped-343-develop-multiplayer ; https://www.purexbox.com/news/2021/09/343_industries_reveals_the_key_feedback_from_halo_infinites_technical_preview ; https://www.purexbox.com/news/2021/09/343_admits_it_probably_over-hyped_halo_infinites_spartan_bots ; https://wccftech.com/halo-infinite-tech-preview-feedback-discussed-while-343-industries-explains-lack-of-campaign-gameplay/amp/ ; https://www.techradar.com/news/halo-infinites-first-bot-focused-preview-could-happen-as-soon-as-next-weekend ; https://gdcvault.com/play/1028054/Deconstructing-the-Combat-Dance-Designing ; https://gdcvault.com/play/1027689/Thinking-Like-Players-How-Halo ; https://www.pcgamer.com/uk/halo-infinites-bots-arent-teabagging-you-at-least-not-on-purpose/
- Bungie: https://www.jmeiners.com/shamans/papers/ai/the_illusion_of_intelligence.pdf ; https://www.gamedeveloper.com/programming/gdc-2005-proceeding-handling-complexity-in-the-i-halo-2-i-ai ; https://web.cs.wpi.edu/~rich/courses/imgd4000-d10/lectures/halo3.pdf ; https://www.gamedeveloper.com/design/combat-evolved-the-encounter-design-of-halo-3 ; https://c20.reclaimers.net/h1/tags/actor/ ; https://c20.reclaimers.net/h1/tags/actor_variant/ ; https://ojs.aaai.org/index.php/AIIDE/article/view/12663
- Quake III: https://github.com/id-Software/Quake-III-Arena/tree/master/code/game ; Laird: https://www.qrg.northwestern.edu/Resources/aigames.org/2001/Laird.pdf
- BotPrize: https://nn.cs.utexas.edu/downloads/papers/schrum.cig11competition.pdf ; https://news.utexas.edu/2012/09/26/artificially-intelligent-game-bots-pass-the-turing-test-on-turings-centenary/ ; https://cdn.aaai.org/ocs/12920/12920-57663-1-PB.pdf ; https://hal.archives-ouvertes.fr/hal-00864153 ; https://en.wikipedia.org/wiki/Computer_game_bot_Turing_test
- Valve: https://github.com/rehlds/ReGameDLL_CS/tree/master/regamedll/dlls/bot ; https://gdcvault.com/play/1022878/The-Making-of-the-Official ; https://github.com/ValveSoftware/source-sdk-2013/tree/master/src/game/server ; https://developer.valvesoftware.com/wiki/TFBot_Technicalities ; https://cdn.fastly.steamstatic.com/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf
- Killzone: https://www.guerrilla-games.com/media/News/Files/VUA07_Verweij_Hierarchically-Layered-MP-Bot_System.pdf ; http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf ; https://www.guerrilla-games.com/media/News/Files/gdce05_killzone_ai.pdf
- F.E.A.R.: https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf
- Game AI Pro chapters: ch.31 Crytek target tracks, GAP2 ch.28 Splinter Cell, GAP2 ch.30 influence maps, GAP3 ch.4 player perception, GAP3 ch.32 Paragon, GAP3 ch.33 accuracy (links inline above)
- Measurement: https://arxiv.org/abs/2303.02160 ; https://arxiv.org/abs/2104.04258 ; https://www.humphryscomputing.com/Publications/SAB_06.pdf
- Human motor and RT: https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.979293/full ; https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5744918/ ; https://arxiv.org/pdf/2203.12050 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC4456887 ; https://ajol.info/index.php/ahs/article/view/176248 ; https://ibmathsresources.com/2015/03/20/reaction-times-how-fast-are-you
- Other: https://www.pcgamer.com/au/ea-shows-off-self-teaching-ai-bots-that-have-trained-in-battlefield-1-for-six-days ; https://users.cs.northwestern.edu/~hunicke/pubs/Hamlet.pdf ; https://www.halopedia.org/MLG_(playlist) ; https://www.coolinfographics.com/blog/2009/1/12/halo-3-heatmaps.html ; https://www.gamedev.net/tutorials/programming/artificial-intelligence/the-core-mechanics-of-influence-mapping-r2799 ; https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11082399/ ; https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1385242/full
