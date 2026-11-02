# Bot brain architecture: coding human-like Halo bots

How to build the decision-making for PvP bots that feel like people instead of aimbots: what Halo's own AI does, what the industry has learned, a layered and modular brain design, a skill ladder that unlocks knowledge and technique instead of inflating stats, and how a local LLM Director coaches the teams without fighting the bots' reflexes.

## 1. How Halo's own AI works

The two generations of Halo AI are the best starting point because they solved the exact problems this project has: complexity, believability, and multiplayer objectives.

### Bungie (Halo 2 and 3): behavior trees

- Damián Isla's GDC 2005 talk, Handling Complexity in the Halo 2 AI, is the paper that made behavior trees the industry standard. Halo 2 replaced a finite state machine (which exploded in complexity as states multiplied and every transition had to be hand-wired) with a prioritized tree of behaviors: each level is a selector that runs the highest-priority child whose conditions hold, and children are either more selectors or leaf actions.
- Key ideas worth copying: behaviors are reusable modules; conditions are cheap checks that gate expensive behaviors; impulses let a rare, urgent event (a grenade landing at your feet) jump the queue without wiring a transition from every other state; stimulus and perception are separate from decision, so the tree only sees what the character is allowed to know.
- Halo 3's AI Objectives System (Isla, GDC 2008) added a declarative layer above the tree: a tree of prioritized tasks that assigns squads to positions and goals, so designers describe what matters and the AI works out who goes where. Changing a task moves AI around the space; the encounter has O(n) complexity instead of the O(n squared) of explicit transitions. This is the ancestor of the Director layer in this guide.
- What does not carry over: campaign AI is built to be fun to fight and to lose; it has scripted encounter logic, perfect designer-placed positions, and enemies who are meant to be read easily. PvP bots must be opponents and teammates who make choices a player would respect.

### 343 (Halo Infinite): behavior tree plus utility, tuned to humans

Halo Infinite was the first Halo with multiplayer bots, and the two GDC 2022 talks (Brie Chin-Deyerle, Thinking Like Players; Sara Stern, Deconstructing the Combat Dance) describe the design. The public slides give these facts:

- A small set of common verbs formed the basis of behaviors across modes: Pickup, Fight, Deliver, Interact, Guard, Traverse (a few more were added over time). Every mode is described to the bots in terms of these verbs plus ambitions.
- An ambition is an object or area in the level that matters for scoring in the current mode (a zone in Strongholds, the ball in Oddball, a flag in CTF), with metadata: its type, the object it refers to, and which teams or bots may use it. Game mode logic lives in Lua and is the authority on rules and state; a BotManager blackboard is where Lua and bots read and write ambitions and shared bot state. This is exactly the mode add-on pattern this project wants.
- Decisions: the behavior tree evaluates nodes in order and finds a behavior that is valid; a utility system (inspired by Dave Mark and Kevin Dill's 2010 talk, Improving AI Decision Modeling Through Utility Theory) ranks each valid behavior with a number and the bot takes the highest. Their example: with the flag, Fight scored 0.91, Deliver 0.6, Traverse 0.1, and the rest 0.
- Utility curves were hard to map to human thought, so they moved tuning into Lua where designers could write the scoring as fixed values, caps and weighted inputs, and where each game mode could bias the scores directly. A single confidence variable (own health, target health, weapons, edge cases) decided whether to push or pull back mid-fight.
- Reaction time: they targeted 200 to 250 ms to process new information (the human benchmark reaction test), and slowing bots down made them better practice partners. With 8 bots that was 31 ms of thinking per bot per window, which also set their performance budget.
- Thrash: when two utilities are close, a bot flips between them and does neither. They fixed it with hysteresis: inflate the utility of the behavior you just switched to for a while, plus smoothing logic.
- Object permanence and shared awareness: bots remember enemies they saw, and bots above a certain difficulty share known enemy positions with teammates (modeling the moment players start communicating). This made objective modes worse at first because bots spent too long in combat, so the objective weights had to be retuned after the change.
- Skill gating: higher difficulties did not just shoot sharper and strafe faster; they unlocked behaviors. Reading the radar was limited to higher skill tiers because that is a thing players learn later. 343 also noted that experienced players take shortcuts through maps and that teaching bots the best path took longer than expected.
- Method: the team broke down human play from playtests and earlier Halo games, isolated individual actions (movement first, then aiming and shooting), tuned each piece, and used internal matches against high-level players to find what humans did that bots did not. Bots were spawned to match the player's skill.

### What this project takes from both

1. A behavior-tree skeleton with a utility selector at the top, verbs as reusable leaves, and impulses for emergencies.
2. Ambitions and a blackboard as the bridge between mode rules and bot brains.
3. A human reaction-time budget as a design constraint, not a bug.
4. Hysteresis and commitment to stop thrash.
5. Skill tiers that unlock knowledge and behaviors, not stat inflation.
6. Shared awareness as a tier-gated team feature, with objective weights retuned when it is on.
7. A tuning loop built on watching good humans and asking what the bot did not do.

## 2. Game AI architectures compared, and the recommended hybrid

| Architecture | How it decides | Strength | Weakness for PvP bots | Used by |
| --- | --- | --- | --- | --- |
| Finite state machine (FSM) | One state at a time, explicit transitions | Simple, fast, easy to debug | Transitions explode (n squared); hard to add a new behavior without touching every state | Early shooters, Quake bots |
| Hierarchical FSM | States contain sub-machines | Reduces explosion a little | Still hand-wired; brittle under interrupts | Many console shooters |
| Behavior tree (BT) | Prioritized selector/sequence tree ticked every frame; leaves succeed, fail or run | Modular, readable, reusable leaves, easy priority and interrupts | Priorities are fixed; tie-breaking between near-equal options is crude | Halo 2 and 3, Unreal Engine, most modern games |
| Utility AI | Every candidate scored from weighted inputs through response curves; highest wins | Smooth, situational, rarely stuck, easy to bias per mode or personality | Scores are hard to compare across different kinds of acts; needs hysteresis; tuning is math | Halo Infinite (top layer), The Sims, Guild Wars 2, Dave Mark's Infinite Axis Utility System |
| GOAP (planning) | Searches a chain of actions whose preconditions and effects reach a goal | Emergent multi-step plans with little authoring | Expensive, plans go stale fast in a 4v4; hard to make look human | F.E.A.R. |
| HTN (hierarchical task network) | Decomposes a high-level task into methods and primitive tasks | Good for squad plays with ordered steps | Needs authored methods; replanning cost | Killzone 2 and 3, Horizon |
| Learned policies (RL, imitation) | A network maps state to action | Can be very human-like if trained on human traces | Needs data, training infra, hard to tune and explain; opaque failures | BotPrize winners, research |

The BotPrize competition (a Turing test for Unreal Tournament 2004 bots) is the strongest evidence on believability. The winning bots in 2012 scored 52 percent humanness against 40 percent for the actual humans. The UT Austin team's stated lesson: if the only goal is eliminating enemies, a bot evolves toward perfect aim, which is not human-like; constraining the bot to human limits and then optimizing inside them produces skill that is good but still human. A separate research line found human-likeness came mostly from how humans value game states (what to go for, when to retreat) rather than from mechanics, and that bots compensating for weak judgment with perfect aim and perfect map knowledge were the tell.

### Recommended hybrid for this project

Use a behavior-tree skeleton with a utility selector at the top and impulse interrupts, exactly the Infinite shape, and add two things Infinite did not need: a skill-tier gate that decides which branches and inputs exist for a given bot, and an external Director that biases the utility weights and assigns roles on a slow clock.

- The BT provides structure, interrupts and readable debugging. Leaves are the verbs (Section 3) and the techniques from the Advanced Techniques and Weapon Deep Dives tabs.
- The utility selector sits in the Act layer and chooses among valid verbs by score. Scores are computed from a small set of named inputs (threat, confidence, objective pressure, resource need, team need) through curves, with per-mode and per-personality weights. Scores are clamped to 0 to 1 and compared only within the same decision (do not compare a Pickup score against a Fight score raw; normalize each verb's score to its own expected range, as 343 did by hand-tuning).
- Impulses are hard interrupts for a short list: grenade landing within 2 WU, melee incoming, sticky attached, vehicle about to splatter, flag dropped nearby, shields popped with no cover. They bypass the selector and run a fixed response from the tier's unlocked list.
- Hysteresis everywhere: the current behavior gets a bonus (10 to 25 percent of its score) for a minimum hold time, and switching requires the challenger to beat it by a margin.
- No GOAP or HTN at the bot level. Multi-step plays (the setups in the Game Mode Playbooks tab) are authored as mode add-on sequences and selected by the Director or the squad layer, which is where planning belongs and where the time budget allows it.
- Learned components are optional later: a small imitation model for strafe patterns or aim micro-motion trained on human traces would raise believability without touching decisions.

## 3. The layered brain

Every bot runs the same pipeline every tick. Each layer only reads what the layer above produced, and each layer has a time budget. Skill tier and personality are data that configure the layers; they are not separate brains.

```
World state (engine truth)
   |
   v
[1] SENSE      what this bot is allowed to perceive this tick (tier-gated)
   |
   v
[2] REMEMBER   working memory: beliefs with confidence and decay; team-shared beliefs
   |
   v
[3] ASSESS     threat score, confidence, objective pressure, resource need, band, posture
   |
   v
[4] DECIDE     impulses -> utility selector over valid verbs -> chosen verb + target
   |             (Director and squad bias the weights here; Survive always wins)
   v
[5] PLAN       verb expands into a short action plan: path, stance, weapon, timing
   |
   v
[6] ACT        movement controller, aim controller, trigger, abilities; human-limited
   |
   v
Engine inputs (as if from a controller)
```

### 3.1 Sense

The bot perceives through a model of the player's senses, never by reading engine truth directly.

- Vision: a field of view cone (about 90 to 100 degrees horizontal, matching the game FOV), line-of-sight raycasts to several body points (head, chest, hips, feet) so partial cover works, distance falloff so a far target in shadow needs a longer look, and a peripheral zone where a target is noticed as motion only. A target must be in view for a detection time before it becomes a belief: 100 ms at Melee or Short band, up to 400 ms at Long band, longer if only a sliver is visible. Camo targets add detection time; a still camo target is not detected at all beyond Melee band.
- Hearing: gunfire, grenades, footsteps, vehicle engines, reloads, ability sounds, each with a radius and a direction error. A heard event creates a belief with a position error of 5 to 15 percent of the distance.
- Radar: an input that exists only for tiers that unlocked it. It gives dots with the same information the HUD gives (in-range enemies that are moving or firing, by game), updated on the HUD's cadence, with no identity.
- HUD and game state the player would see: own shields and health, ammo, grenades, teammate positions and shield state (if the game shows them), the objective markers, the score and time, kill feed events, the flag carrier waypoint. Nothing else.
- Reaction latency: every new perception is time-stamped and only becomes available to Decide after the tier's reaction delay (200 to 300 ms for mid tiers, see Section 5). Events pass through a delay queue, not a frame skip, so the bot reacts to what was true a quarter second ago, the way a human does.

### 3.2 Remember

Working memory is a list of beliefs: entity, last known position, velocity, confidence 0 to 1, time stamp, source (seen, heard, radar, teammate, inferred). Confidence decays over time at a rate set by tier (a low tier forgets an enemy who broke line of sight in 2 seconds; a high tier tracks the corner for 8 seconds and predicts where they went). Beliefs about enemies include their estimated shield state (seen damage), weapon (seen or heard), and the band they were last in.

- Object permanence is what 343 called this; without it bots look like amnesiacs.
- Shared awareness: at tiers that unlocked callouts, a bot's new high-confidence beliefs are pushed to the team's shared belief board with a 300 to 800 ms delay (the time to say it), and teammates adopt them at reduced confidence. This models comms. The Director reads the team board; it never reads engine truth about enemies.
- Map memory: timers for weapons, powerups and equipment the bot saw taken, with the tier deciding whether it counts (Section 5). Spawn beliefs: at high tiers, after a kill the bot forms a weighted guess about where the enemy will respawn using the spawn rules in the Mechanics tab.
- Self memory: last action, last fight result, grenade and ammo counts, ability charge, how long since it last saw a teammate.

### 3.3 Assess

From the beliefs the bot computes a few scalars that every decision reads:

- Threat score per known enemy, as in the main tab section 10: distance band, their weapon versus mine, their shield state, whether they are aiming at me, how many of them, whether a teammate is engaged with them.
- Confidence (343's word): will I win this fight? Own shields and health, weapon match-up at this band, ammo, grenades, cover within reach, teammate support within 3 seconds, escape route. Range 0 to 1 and it drives push versus pull back.
- Objective pressure: how much the mode needs me at the ambition right now (the mode add-on computes it: flag out, hill contested, bomb planted, time left, score gap).
- Resource need: low ammo, no grenades, weak weapon for the map, power weapon about to spawn.
- Team need: a teammate calling for help, a role left empty by a death, the Director's current priority.
- Posture: the aggressive, balanced or defensive variable from the main tab, computed from confidence, score state and personality.

### 3.4 Decide

Order matters:

1. Impulses (hard interrupts) are checked first. If one fires, it owns the bot for its duration.
2. Survive check: if confidence is below the tier's survive threshold and an escape exists, Retreat or Reposition is forced. The Director cannot override this.
3. Build the list of valid verbs: a verb is valid if the mode allows it, the tier unlocked it, and its preconditions hold (Pickup needs an item in memory, Deliver needs a carried objective, Flank needs a known enemy and a known route).
4. Score each valid verb with the utility inputs, the mode weights, the personality weights, and the Director bias (a multiplier between 0.5 and 1.5, Section 8).
5. Apply hysteresis to the current verb. Pick the best. Record why (for the replay tool).

The verb list for this project, extended from Infinite's six: Fight, Pickup, Deliver, Interact, Guard, Traverse, plus Retreat, Reposition, Flank, Support (escort or trade with a teammate), Hold (anchor a position or lane), Rotate (move between setup positions), Scout (gain information), Deny (contest a spawn or stand on a timer), and Use (deploy an ability or equipment as its own act).

### 3.5 Plan

A verb expands into a short plan: a path on the navmesh (using jump links and the tier's known shortcuts), a stance per segment (sprint, run, walk, crouch), a weapon to hold, a target point for the aim controller, and a timing rule (wait for a teammate, go on the weapon timer, go when the enemy reloads). Plans are short, 1 to 4 seconds, and are re-planned whenever the verb changes or a belief changes materially.

### 3.6 Act

The act layer is where human limits live and is the subject of Section 4: a movement controller with acceleration and strafe patterns, an aim controller with reaction, lag, noise and overshoot, a trigger controller with weapon pacing, and an ability controller with the use rules from the Equipment tab.

### 3.7 Tick budget

Per-bot work is split by rate. On a 60 Hz game:

| Layer | Rate | Notes |
| --- | --- | --- |
| Sense | 20 Hz, staggered across bots | Raycasts are the cost; cap at a few per enemy per tick |
| Remember | 20 Hz | Decay and merge |
| Assess | 10 Hz | Scalars only |
| Decide | 10 Hz, plus on any impulse | Utility over at most ~15 verbs |
| Plan | On change, max 5 Hz | Pathfinding is the cost; cache paths |
| Act | 60 Hz | Aim and movement controllers must run every frame to look smooth |
| Squad layer | 2 Hz | Role assignment, callouts, setups |
| Director | 0.05 to 0.2 Hz (every 5 to 20 s) | External process, asynchronous |

With 8 bots this keeps the whole AI under a few milliseconds a frame on a modern CPU, and Infinite shipped a similar split on far tighter hardware.

## 4. Human-likeness: what to model and how

The guiding rule from the BotPrize teams and 343: a human-like bot has human limits first and human intelligence second. The limits below are the floor every tier shares; the tiers in Section 5 raise the ceiling of what the bot knows and can do, never remove the limits.

### 4.1 Reaction time

- Simple visual reaction in adults averages about 250 ms; the best FPS players are near 150 to 180 ms; distracted or surprised people are 350 ms or more. 343 targeted 200 to 250 ms for Infinite's bots and said slowing them down made them better partners.
- Model it as a distribution, not a constant: per tier a mean and a spread (Section 5), sampled per event, with a longer tail when the bot is already busy (reloading, mid-strafe, looking the other way) and a shorter one when the bot is pre-aiming a corner it expects an enemy at (anticipation is a real human skill and it is how good players seem fast).
- Separate perception delay (see it), decision delay (choose), and motor delay (move the stick). A good player pre-decides, so their total from seeing to shooting is reaction plus a little; a weak player adds 100 to 300 ms of deciding.

### 4.2 Aim model

Never snap. Human aiming is a closed-loop controller with noise, modelled well by Fitts' law and its feedback extensions: a fast initial ballistic move toward the target that undershoots or overshoots, then one or two corrective movements, with Gaussian noise proportional to the distance moved. Build the aim controller as:

1. Acquire: when a target first becomes a belief, the reticle moves toward the target point with a proportional controller (move a fraction of the remaining angle per frame) plus a per-move noise term drawn from a normal distribution scaled by the angle moved (research aimbots that fool anti-cheat use roughly 0.2 times the move as the noise standard deviation; use that as a starting point and tune per tier). Add an overshoot: the first move targets a point slightly past the target with probability rising with angular speed.
2. Track: once on target, follow the target's motion with a lag (60 to 150 ms by tier) and a small tremor (low-amplitude noise at 8 to 12 Hz). Strafe reversals by the target cause a tracking error spike proportional to their speed change; high tiers recover faster.
3. Micro-correct: before each shot, pull toward the intended body point (head for precision weapons, body for automatics) with a per-shot error ellipse (horizontal error larger than vertical, as human aim is), whose size depends on tier, band, own movement (moving while shooting widens it), target movement, flinch from being hit, scope state, and weapon (the per-weapon notes in the Weapon Deep Dives tab).
4. Fire decision: the trigger controller fires when the reticle is inside the weapon's accepted radius for the target and the pacing rule allows it (burst timing, bloom pacing, scope-in time). A bot never fires on a frame it cannot see the target, except suppressing fire, which is a deliberate act with its own verb.

The red reticle range in the Mechanics tab is the right cut-off for when aim assist would apply; model controller aim assist as a mild pull toward the target inside RRR for console-style bots, and none for the keyboard-and-mouse style personality.

### 4.3 Perception limits

Covered in Section 3.1. The important human-likeness rules: no wall hacks ever; nothing is known that was not seen, heard, read off radar or HUD, or told by a teammate; radar, sound and callouts are tier-unlocked inputs; a bot looking down a scope has tunnel vision (narrow FOV, no peripheral motion); a bot that is sprinting sees but does not aim.

### 4.4 Mistakes as skill gaps, not dice

The worst human-likeness failure is a bot that aims perfectly and then randomly misses, or that knows everything and then randomly forgets. Humans do not miss at random; they miss for reasons. Model mistakes as the absence of a skill or knowledge, so the mistake is consistent and readable:

- A low tier does not know the sniper spawns, so it never goes there; it does not randomly go there 30 percent of the time.
- A low tier reloads when the magazine is empty, mid-fight, because reload discipline is a learned habit; a high tier reloads behind cover between fights.
- A mid tier chases a kill past the point it should stop; over-chasing is a mid-skill habit and a readable one.
- A low tier throws grenades at where the enemy is; a high tier throws at where the enemy will be.
- A low tier peeks a corner slowly and wide; a high tier jiggle-peeks.
- A mid tier panics: when shields pop it stops strafing for a beat. Model panic as a confidence collapse that temporarily widens aim error and lengthens reaction, triggered by sudden damage, a sticky, a surprise at Melee band.
- Tilt: after several deaths in a row a human plays worse or more recklessly; a small posture shift toward aggressive for 30 seconds after three quick deaths is believable and tunable per personality.

Randomness is still used, but inside the human envelope: aim noise, reaction spread, and the choice between two near-equal verbs (pick by weighted random, not always the max; a softmax with low temperature makes bots less predictable without making them stupid).

### 4.5 Commitment and hesitation

Humans commit. A player who decides to push a room pushes it; a player who decides to back off backs off. Bots that re-evaluate every tick look like they are vibrating. Rules: minimum hold times per verb (Fight 1.5 s, Traverse to a destination until arrival or a threat, Hold 5 s, Retreat until shields recharge), hysteresis bonuses, and a hesitation model: when two choices are close the bot waits a beat (100 to 300 ms) and then commits, which reads as thinking.

### 4.6 Movement

Movement is the first thing players read. From 343's experience, model it first: walk, run, sprint, crouch, jump, mantle, with real acceleration and a stop-to-shoot habit for precision weapons. Then the strafe patterns from the Advanced Techniques tab, chosen by tier: none, side-to-side, random-reversal, crouch-strafe, jump-strafe at the right moments only (jumping while shot is a low-tier tell, except deliberate jump-shots at high tiers). Paths: the navmesh gives routes; tier decides whether the bot knows the jumps and shortcuts, so a low tier takes the long ramp and a high tier takes the crouch-jump that experienced players use. Bots should sometimes look around while moving (head and reticle motion that is not aiming), check corners, and glance at the radar area (a brief pause in reticle motion) at tiers that use it.

### 4.7 Readability and intent

A human teammate or opponent can usually guess what a player is doing. Bots should be legible: they go somewhere for a reason, they face where they expect the enemy, they reload at sensible times, they throw grenades at places that make sense. The replay tool in Section 9 logs the reason for every decision so a reviewer can check that the reason would make sense to a player.

### 4.8 What not to do

- Do not scale difficulty by aim accuracy and health alone. It produces aimbots at the top and drunk players at the bottom, and every tier plays the same way.
- Do not let bots read engine state for enemies, item timers, or spawns. Give them the senses and the knowledge instead.
- Do not give bots instant target switching; switching targets costs a human a reaction time and a re-acquire.
- Do not let bots fire while turning fast; wait for the acquire phase to settle.
- Do not let a bot perform a technique its tier does not know, even when it would win the fight.

## 5. The skill ladder: unlock skills, do not inflate stats

The vision: the easiest bot is an ordinary person who happens to find a gun, picks it up, walks toward the objective and shoots what it sees. The hardest bot knows the spawns, the timers, the setups, the jukes and the grenade timings. Difficulty is a growing skill set, not a growing aimbot. 343 did a version of this (radar reading unlocked at higher tiers; shared awareness gated by difficulty) and it is the single most important design choice in this document.

### 5.1 Seven tiers

| Tier | Name | Who it is | Reaction (mean, spread) | Aim error (relative) | Knows | Does |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Recruit | First week of Halo; not technical | 380 ms, wide | 2.0 | Where the objective marker is; what a gun is | Picks up the first weapon it walks over, runs at the objective, shoots at what it sees, reloads when empty, throws grenades straight at enemies, no strafe |
| 2 | Casual | Plays sometimes; knows the basics | 330 ms | 1.6 | The map's rough layout; that some weapons are better | Simple side strafe, takes cover when shields pop, picks up better weapons when seen, chases kills, uses abilities when prompted by an obvious cue |
| 3 | Regular | Plays weekly; respectable | 290 ms | 1.3 | Where the power weapons spawn; the main lanes; basic callouts | Looks for power weapons, holds angles, melees at Melee band, throws grenades to deny, reloads behind cover sometimes, reads radar occasionally |
| 4 | Skilled | Competent ranked player | 250 ms | 1.0 | Weapon timers (roughly), spawn tendencies, setups for the map and mode, grenade spots | Times weapons, trades with teammates, crouch-strafes, descopes snipers, jumps the common shortcuts, calls out, uses abilities on the right triggers |
| 5 | Veteran | High-ranked; disciplined | 220 ms | 0.85 | Exact timers, spawn rules, all jumps and grenade spots on the map, the tier of each enemy | Perfect timer discipline, pre-aims corners, pre-nades spawns, baits with holograms and corners, plays the posture variable deliberately, rotates on calls |
| 6 | Expert | Top of the ladder; semi-pro habits | 200 ms | 0.75 | Everything in the Rules of Engagement and Playbooks tabs; the enemy team's patterns this match | Perfect setups, spawn traps, team shots on call, advanced techniques (BXR, double shot, reload cancels, sword flying where enabled), reads enemy comms by behavior |
| 7 | Pro | Esports-level team play | 190 ms, narrow | 0.7 | Everything, plus the Director's game plan and the esports coaching vocabulary | Runs the Director's plays as a unit, adapts setups mid-match, perfect communication, deliberate tempo control |

Tier 7's aim is still human: 0.7 of the Tier 4 error, with the same reaction floor the best humans have. Tier 7 beats Tier 4 because it knows more, decides better, and plays as a team, not because it shoots like a machine. If a Tier 7 bot's accuracy in testing exceeds the top 1 percent of human accuracy for that weapon and band (Section 9), the aim error floor is wrong.

### 5.2 Unlock table

Every capability is a flag in the tier profile. The bot's Sense, Decide and Act layers consult the flags; a flag that is off means the input does not exist, the verb is not valid, or the technique is not in the Act layer's repertoire.

| Category | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 | Tier 6 | Tier 7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Perception: radar | off | off | occasional glance | regular glance | constant | constant | constant |
| Perception: sound localization | gunfire only, coarse | plus grenades | plus footsteps | plus reloads and abilities | fine | fine | fine |
| Perception: callouts received | off | off | on, slow adoption | on | on | on, trusted | on, trusted |
| Memory: enemy decay | 2 s | 3 s | 4 s | 6 s | 8 s | 10 s, with prediction | 10 s, with prediction |
| Memory: weapon timers | none | none | notices pickups | counts timers roughly | exact | exact plus enemy timers | exact plus Director timers |
| Memory: spawn prediction | none | none | none | basic | spawn rules | spawn rules plus traps | plus trap setups |
| Knowledge: map routes | marker direction | main ramps | lanes | shortcuts | all jumps | all jumps and tricks | all |
| Knowledge: setups | none | none | one hold | mode setups | all setups | adaptive setups | Director setups |
| Knowledge: weapon ROE | shoot it | prefer the bigger gun | band basics | full ROE table | full ROE plus pacing | plus advanced techniques | all |
| Decide: threat scoring | nearest enemy | nearest plus shields | full score | full score plus confidence | plus team need | plus prediction | plus Director priority |
| Decide: retreat threshold | never | shields popped | shields low | confidence based | confidence and posture | plus trade awareness | plus tempo |
| Decide: objective weight | high and constant | constant | mode-tuned | mode-tuned | phase-aware | phase-aware | Director-tuned |
| Movement: strafe | none | side-to-side | random reversal | crouch-strafe | jump and crouch mixes | full patterns | full patterns |
| Movement: peeks | wide and slow | shoulder | jiggle | jiggle and pre-aim | all | all | all |
| Movement: stop-to-shoot | always stops | mostly | precision weapons only | correct | correct | correct | correct |
| Act: reload timing | when empty | when empty | after fights | behind cover | reload cancels | reload cancels | reload cancels |
| Act: grenades | at the enemy | at the enemy | bounce basics | anticipation | pre-nade spawns | cook and stick setups | all |
| Act: abilities | obvious cues only | obvious cues | use-now triggers | use-now and hold rules | plus bait rules | all plus sneaky uses | all |
| Act: advanced techniques | none | none | descoping | descoping, melee timing | plus game-specific (bloom pacing, sprint discipline) | plus BXR, double shot, reload cancel | all |
| Team: shared awareness | off | off | on | on | on | on | on |
| Team: roles | none | none | loose | assigned | assigned and swapped | adaptive | Director-assigned |
| Team: trades and team shots | never | accidental | sometimes | on call | always | always | always |
| Team: Director | not connected | not connected | hints only | role assignment | roles and setups | full plays | full plays plus coaching |

### 5.3 Mapping tiers to the guide

The Rules of Engagement tab (sections 9 to 12) already defines skill tiers and styles for the decision stack. This ladder extends it: Tier 1 to 3 read only the fundamentals (ROE section 2) and the mode logic summary; Tier 4 reads the full ROE tables and the playbooks' standard holds; Tier 5 and 6 read the Advanced Techniques, Weapon and Vehicle Deep Dives, Equipment, and the Mechanics tab's timers and spawn rules; Tier 7 reads everything plus the Director's live plan. In code, each tier profile lists the knowledge packs it loads (Section 6).

### 5.4 Personality on top of tier

Tier is capability; personality is preference. The main tab's styles (aggressive, balanced, defensive; rusher, anchor, flanker, sniper) are personality weights applied to the utility scores and the posture variable, and they exist at every tier. A Tier 2 aggressive bot runs at the enemy with a plasma rifle; a Tier 6 aggressive bot rushes on the weapon timer with a teammate's shots ahead of it. Also personality: patience (how long it holds an angle), grenade appetite, vehicle appetite, callout chattiness, tilt susceptibility, and a console or mouse style (aim assist on or off, turn speed cap).

### 5.5 Matching bots to humans

As 343 did, spawn bots near the human's skill. If the project tracks a human rating, map it to a tier, then fill the lobby with a spread of one tier either side so the team feels like a real lobby. Within a team, mix personalities so the team has a rusher, an anchor and a flanker instead of four of the same.

## 6. Modular brains: core plus add-ons

The intuition that there should be a general combat brain with a mode add-on attached is right, and it is how 343 did it (verbs plus ambitions plus a blackboard). Make it explicit: one core, and five kinds of plug-in data and logic that configure it.

```
BotBrain
  |- Core             : Sense, Remember, Assess, Decide, Plan, Act (Section 3)
  |- TierProfile      : the unlock flags, reaction and aim parameters (Section 5)
  |- Personality      : utility weight multipliers, posture bias, style flags
  |- GameProfile      : per-title rules (CE, H2, H3, Reach, H4): weapons, damage, movement, abilities
  |- MapPack          : callouts, power spots, timers, routes, jumps, grenade spots, setups (Map Playbooks tab)
  |- ModeAddon        : ambitions, roles, phases, objective pressure, utility biases, callout vocab (Game Mode tab)
  |- DirectorLink     : the inbox for orders and the outbox for reports (Section 7)
```

### 6.1 The core

The core knows how to fight, move, pick up, remember and survive. It knows nothing about flags, hills, balls or bombs. It exposes verbs and expects someone to tell it which ambitions exist and how much they matter.

### 6.2 Mode add-ons

A mode add-on is a data file plus a small script with four responsibilities:

1. Ambitions: what objects and areas matter, for which team, with a type (carry, hold, deliver, destroy, defend, collect) and the verbs that apply to each. CTF publishes two flags (ours: defend and return; theirs: pick up and deliver), the capture point, and the enemy flag stand as an attack ambition. KOTH publishes the hill with a hold type and the next hill when known. Oddball publishes the ball with a carry type and the hold spots from the map pack as hold ambitions.
2. Objective pressure: a function from game state to a 0 to 1 pressure per ambition. Flag out and near home: pressure 1.0 on return. Hill contested with 10 seconds left on our capture: 1.0 on hold. Score lead and time short: pressure shifts from attack to defend.
3. Utility biases: multipliers on the core verbs for this mode. In CTF Deliver outranks Fight when the carrier has a clear route; in Slayer Fight outranks almost everything but Survive; in Oddball Guard scores high for two teammates near the carrier; in Infection Hold scores high for survivors and Flank for zombies.
4. Roles and phases: the role list (carrier, escort, anchor, returner; king, guard, rotator; and so on from the Game Mode tab) with the rules for assigning and swapping them, and the phase list (pull, run, defend; setup, hold, rotate) with the triggers between them.

Each tier reads the add-on at its own depth: Tier 1 gets only the ambitions and a constant objective pressure (it runs at the marker); Tier 4 gets roles and phases; Tier 7 gets everything and lets the Director reassign roles.

### 6.3 Map packs

A map pack holds what the Map Playbooks tab describes for that map: callout names tied to navmesh regions, power spots and their timers, standard holds per mode, grenade spots with throw vectors, jump links with the tier that knows them, flag and bomb routes, vehicle routes, sniper lanes, and spawn zones with the spawn rules from the Mechanics tab. The core consults the map pack through the tier filter, so a Tier 2 bot sees the callouts and lanes and nothing else.

### 6.4 Game profiles

Per-title data: weapon stats and ROE table, damage model, movement speeds and jump heights, shield and health values and recharge timings, the ability or equipment list with the use rules from the Equipment tab, and the per-game quirks (CE fall damage, H2 BXR, Reach bloom, H4 sprint and loadouts). The Act layer's controllers are parameterized by the game profile so one aim controller serves every title.

### 6.5 Composition rules

- Load order: core, game profile, map pack, mode add-on, tier profile, personality, Director link. Later layers only filter or bias; they never add facts the earlier layers do not have.
- Conflicts: a mode bias cannot push a verb's score above 1.0 or below 0; Survive and impulses are outside the biased set; a personality multiplier is capped at 0.5 to 1.5.
- Add-ons are stackable for hybrid modes (Assault plus vehicles, Firefight plus Generator Defense): each publishes its ambitions, pressures are summed and clamped, and biases multiply.
- Firefight: the core is the same; the mode add-on publishes enemy waves and the hold spots as ambitions and swaps the threat scorer for the AI-enemy playbook in the Game Mode tab.

### 6.6 A worked example

Multi Flag on Narrows, Tier 5 bot, personality flanker, Director connected. The core senses an enemy at the top of the bridge and a teammate's callout that the enemy flag is pulled. The CTF add-on publishes: enemy flag (deliver, pressure 0.8, our carrier has it), our flag (defend, pressure 0.3), enemy base (attack, pressure 0.4). The map pack says the bot's assigned flank route is the bottom man cannon and the sniper lane is top mid. The Director's last order (12 seconds ago) was escort the carrier; its bias raises Support by 1.3. The utility selector scores Support 0.78, Fight 0.55 (enemy at Long band, confidence 0.6), Flank 0.4, Traverse 0.2. The bot runs Support: it paths toward the carrier's route, pre-aims the top of the bridge as it goes, and fires on the enemy only if the enemy threatens the carrier. If the carrier dies, the add-on flips the flag ambition to pickup with pressure 1.0 and the bot's next decision is Pickup.

## 7. Team coordination and the AI Director

There are three clocks in a team: the reflex clock inside each bot (tens of milliseconds), the squad clock (a second or two: who takes which role, who calls what), and the strategic clock (ten seconds and up: what the team is trying to do this phase of the match). The Director lives on the strategic clock and should never be asked to do the other two.

### 7.1 The squad layer (no model, pure code)

Before any model is involved, a squad layer handles the fast team work, because it has to be reliable and immediate:

- Role assignment from the mode add-on's rules, re-evaluated at 2 Hz and on deaths.
- Callouts: converting shared beliefs into the team belief board with a comms delay; a callout vocabulary from the map pack.
- Team shots: when two bots see the same target, the second's Fight score gets a bonus and both aim at the same enemy.
- Trades: a bot whose teammate is fighting at Short band and losing gets a Support bonus.
- Spacing: a repulsion term keeps bots from stacking in one doorway; a cohesion term keeps escorts near carriers.
- Setup execution: the authored setups from the Playbooks tab are sequences the squad layer can run (bots take positions in order, with timing).

This layer alone makes Tier 4 and up feel like a team. The Director adds judgment on top.

### 7.2 Two kinds of local model, two jobs

The two candidates are different tools and should hold different jobs.

**Kev-4B is a decision model, not a chat model.** It reads a state document plus typed questions and returns calibrated probabilities over the options you give it, in one forward pass, with no text generation. Three question types: choice (pick among named options), score (an ordered level), and noul (yes or no). It runs on a 16 GB GPU or a 32 GB Apple Silicon Mac, needs about 14 GB of GPU memory, and answers a handful of questions on a short state in roughly 20 to 40 ms on a datacenter GPU with a new state, and faster when the state is cached. Its validated context is 8,192 tokens. It cannot write a sentence, so it cannot be the coach's voice, but it is an excellent fast judge: which of these five plays, is this order still valid, how urgent is this. Every question is answered independently, and option order can change an answer, so shuffle options across calls or ask the same question twice with options reversed when it matters.

**Ollama runs generative models** (Qwen, Llama, Gemma and similar at 4 to 14 B). They reason in text, follow instructions, and can produce structured JSON when given a JSON schema in the request's format field, which makes their output parseable and validatable. They are slower (a 7 to 8 B model typically needs one to several seconds for a few hundred tokens on a consumer GPU) and they can hallucinate facts that are not in the prompt, so their output must be validated before use. They are the right tool for the slow strategic read, the coaching text, and anything that needs a sentence.

### 7.3 Division of labor

| Job | Clock | Tool |
| --- | --- | --- |
| Reflexes, aim, movement, survival | 16 to 100 ms | Bot core (code) |
| Roles, callouts, trades, spacing, setups | 0.5 to 2 s | Squad layer (code) |
| Pick the team's play from a candidate list | 2 to 5 s | Kev-4B choice question |
| Check an order is still sensible | 1 to 3 s | Kev-4B noul question |
| Rate urgency or risk of a situation | 2 to 5 s | Kev-4B score question |
| Read the match, set the phase plan, write the coaching | 10 to 30 s | Ollama generative with JSON schema |
| Post-match review and tier calibration notes | after match | Ollama generative |

If only one is available: Kev-4B alone gives a fast, silent, reliable play-picker with no coaching text; Ollama alone gives a slower, chattier Director that must be validated harder. Both together is the design.

### 7.4 The state document

Both models read the same state, rendered as labelled text (a JSON object is fine; Kev renders JSON as labelled text). Keep it under 2,000 tokens so Kev answers fast and Ollama stays focused. It contains only what a coach could know: score, time, mode and phase, the team belief board (not engine truth), each bot's tier, role, health band, weapon, position callout, ammo band and ability state, the enemy beliefs with confidence and age, weapon and powerup timers the team knows, recent events (deaths, pulls, captures, callouts) for the last 30 seconds, the current plan and how long it has been running, and the map pack's named setups for this mode.

### 7.5 Kev-4B question set (every 2 to 5 seconds)

- play: choice among 4 to 8 candidate plays generated by the squad layer from the playbooks (for example: hold_setup_A, push_on_sniper_timer, rotate_to_B, collapse_on_carrier, reset_and_recharge). Each option has a one-line description from the Playbooks tab.
- order_valid: noul, is the current order still sensible given the state.
- urgency: score 1 to 5, how urgently the team must act on the objective.
- risk: score 1 to 5, how risky the chosen play is.
- focus: choice among known enemies, who the team should prioritize.

Thresholds: adopt the play if its probability is at least 0.45 and beats the current play by 0.15; keep the current play otherwise (hysteresis at the strategic level). If order_valid is below 0.4, drop the current order and fall back to the squad layer's default. Freeze these thresholds after measuring on labelled replays (the model card's own advice).

### 7.6 Ollama prompt and output (every 10 to 30 seconds)

System prompt: a coach's role, the vocabulary (Section 7.7), the hard rules (no orders that break Survive, no orders outside the vocabulary, cite only facts in the state, say unknown when unknown), and the JSON schema. User message: the state document. Output schema:

```json
{
  "read": "one sentence on what the enemy seems to be doing",
  "phase_plan": {"name": "string from vocabulary", "for_seconds": 15},
  "role_assignments": [{"bot": "id", "role": "anchor|rusher|flanker|sniper|carrier|escort|returner|king|guard|rotator"}],
  "priorities": {"objective": 0.0, "map_control": 0.0, "power_weapons": 0.0, "kills": 0.0, "safety": 0.0},
  "orders": [{"bot": "id", "order": "vocabulary verb", "target": "callout or ambition", "ttl_seconds": 10, "confidence": 0.0}],
  "callouts": ["short lines the bots may say"],
  "coaching": "one or two sentences for the team, esports tone"
}
```

Every field is validated against the vocabulary, the map pack's callouts, the live bot list and the TTL cap before anything is applied. A response that fails validation is discarded whole; the team keeps its last plan. Set a request timeout at twice the model's median latency; on timeout, keep the last plan.

### 7.7 Esports vocabulary for the Director

The Director speaks the game's competitive language so its plans map directly onto the Playbooks tab. Phase plans: setup, hold, rotate, push, collapse, reset, bait, trap, stall, tempo. Orders: hold [callout], rotate [callout], push [callout] on [timer or event], escort [bot], return flag, pull flag, deliver via [route], contest [ambition], deny [spawn], trade with [bot], team shot [enemy], pre-nade [spot], watch [lane], reset and recharge, bait [callout]. Priorities are the five sliders above. Coaching lines follow the shape pros use: a read, an instruction, a timing ("They have snipe top mid; hold bottom, nade the lift, push when snipe is down").

### 7.8 Coaching layer

Coaching is advice to the squad layer, not control of bots. It arrives as the priorities sliders and the role assignments. The esports habits worth encoding as coaching heuristics in the system prompt: play the timers (power weapons decide fights), win the setup not the fight, trade every death, do not chase without a reason, control spawns before pushing, reset when two are down, stall when ahead late, pressure when behind early, split the map by lanes not by distance, and talk before you act. The Director should be told the enemy's apparent tier so it can plan for a team that will or will not contest timers.

### 7.9 Latency and deployment

- Run the models in a separate process or machine; talk over HTTP (Kev's TypeSafe-compatible endpoint, Ollama's local API). Never block the game thread; requests are asynchronous with a TTL.
- Warm both models at match start with a dummy request so the first real call is not a cold start.
- Cache the state prefix: Kev caches a repeated state, so send stable sections first and the changing events last.
- Budget: one Kev call per team every 2 to 5 seconds and one Ollama call per team every 10 to 30 seconds is comfortable on a single consumer GPU for two teams; both teams' Directors can share the hardware. If GPU memory is tight (Kev's 14 GB plus an 8 B generative model does not fit in 16 GB), run Kev on the GPU and a 4 B generative model on CPU for coaching, or run Ollama only.

## 8. Arbitration: keeping the Director and the bots from colliding

The failure the vision worries about is real and has a name in research: an LLM director is slow and occasionally wrong, and a reactive agent that obeys it literally will miss events, oscillate, or do something nonsensical. Every published system that works (SwarmBrain's reflex net under an LLM brain for StarCraft, the STRATA tiered agents, EA's 2026 hierarchy where an LLM selects among reactive skill policies and the result was rated the most human-like by players) solves it the same way: separate the layers by information scope, decision authority and update frequency, and never let the slow layer touch the fast layer's controls. The rules below make that concrete.

### 8.1 The authority ladder

From highest to lowest. A lower rung can only bias a higher rung, never override it.

1. Impulses and Survive (bot core). Grenade at feet, sticky, melee, splatter, shields popped with no cover. Always win. No order can suppress them.
2. Mode legality (mode add-on). A bot cannot be ordered to do something the mode forbids or the tier has not unlocked.
3. Bot verb selection (utility selector). The bot picks its own verb from valid ones, every 100 ms.
4. Squad layer. Roles, callouts, spacing, setups. Biases the selector up to 1.5x, assigns roles.
5. Director. Phase plan, role assignments, priorities, orders with a TTL. Biases the selector up to 1.5x, proposes roles to the squad layer, never issues controls.

The Director writes to the blackboard; the bots read it. The Director never calls a bot function.

### 8.2 Orders are intents with a lifetime

An order is a verb from the vocabulary, a target, a TTL and a confidence. The squad layer converts it into a utility bias for the matching verb and target on the named bots. It is not a command: if the bot's own scoring finds Fight at 0.9 because an enemy is at Short band, and the order biases Rotate from 0.3 to 0.45, the bot fights, and that is correct. Orders expire; an expired order is removed silently. Orders are refreshed, not accumulated: a new Director response replaces the previous order set wholesale.

### 8.3 Timescale separation

- Bots re-decide every 100 ms. The squad layer updates at 2 Hz. Kev answers every 2 to 5 s. Ollama answers every 10 to 30 s.
- A Director response is time-stamped with the state it was computed from. If the state has changed materially since (a death, a flag event, a capture) the response is applied at half weight, or discarded if the phase changed.
- Minimum plan hold: the team keeps a phase plan at least 8 seconds unless an event invalidates it. This is the Director-level hysteresis and it prevents the team lurching between push and reset.

### 8.4 Validation gate

Every Director output passes through a validator before it touches the blackboard:

- Vocabulary: verbs, phases, roles and targets must be from the allowed lists; unknown strings are dropped.
- Reality: a target callout must exist in the map pack; a bot id must be alive; an ambition must be published by the mode add-on; a timer the Director cites must match the team's timer board within 5 seconds.
- Feasibility: an ordered move must have a navmesh path under 20 seconds for that bot; an escort order needs a carrier; a push on a timer needs the timer to be within 30 seconds.
- Safety: no order may name a bot whose confidence is below the survive threshold for a verb other than Retreat or Reset; the validator rewrites it to Reset.
- Rate: at most one order per bot per response; at most 3 role changes per minute per team; priorities must sum to a sane range.
- Confidence: orders with confidence below 0.4 are advisory (bias 1.1x); above 0.7 they are strong (bias 1.5x).

A response that fails more than two checks is discarded entirely and logged. The team continues on the squad layer's defaults, which must be good enough to play a whole match alone (test this: Section 9).

### 8.5 Kev as the referee

Use Kev-4B's speed as the arbiter between the slow Director and the fast squad: every 2 to 5 seconds, ask order_valid on the current Director plan and play on the candidate list. If Kev says the plan is no longer valid (probability under 0.4), the squad layer drops the plan without waiting for Ollama's next cycle. If Kev picks a different play with a clear margin, the squad layer switches and the next Ollama prompt includes the switch and why, so the Director's next plan builds on it rather than fighting it. This closes the loop: the slow brain proposes, the fast judge polices, the bots act.

### 8.6 Failure catalogue

| Symptom | Cause | Fix |
| --- | --- | --- |
| Bots run toward an order, then back to a fight, then toward the order (oscillation) | Order bias too strong against Fight; no hysteresis | Cap bias at 1.5x; add verb hold times; lower bias while an enemy is in view |
| Team pushes after the plan was invalidated by a death | Stale order applied | Time-stamp orders against state; half-weight or discard on material change; Kev order_valid check |
| Two bots ordered to escort, nobody returns the flag | Role assignment collided with mode rules | Squad layer owns roles; Director proposes; mode add-on enforces minimum roles (one returner) |
| Bot walks into a sniper lane because the Director said rotate | Feasibility ignored risk | Rotate uses the map pack's safe routes; bot Survive still applies; Director sees the death and learns |
| Bot stands still waiting for the Director | Blocking call | Never block; defaults always run; Director is optional |
| Director names a callout that is not on this map | Hallucination | Vocabulary and reality validation; discard |
| Director changes the plan every cycle | No strategic hysteresis | Minimum plan hold 8 s; require a margin to switch |
| Everything slows when the GPU is busy | Shared GPU with the game | Separate process or machine; TTL on requests; timeout keeps last plan |
| Tier 2 bots suddenly play like a team because the Director connected | Director applied below its tier gate | Tier gate on the Director link; low tiers ignore orders |
| Team feels scripted, always the same setup | Director picks the top-scored play every time | Weighted random among plays within 0.1 of the best; personality bias on the team (aggressive teams prefer push) |
| Bots drop the objective to obey a kills priority | Priorities applied to the objective weight directly | Priorities bias only the non-survival, non-objective-critical verbs; objective pressure 1.0 is uncapped |

### 8.7 Human comms model

The Director's callouts and coaching lines are text; the bots do not hear text. The squad layer turns an accepted plan into the same shared-belief and role changes a human team would reach after hearing the call, with the comms delay. If the project has voice or text chat, the coaching line can be surfaced to human teammates as a bot's callout, which is both flavor and a way to show the plan.

## 9. Testing, telemetry and tuning

343's method was to isolate single actions, tune them, then watch skilled humans play against the bots and list what the humans did that the bots did not. Build the tooling for that loop first.

### 9.1 Telemetry per bot per decision

Log every Decide tick: time, tier, personality, beliefs considered (count and age), the scalars (threat, confidence, pressure, need, posture), the valid verbs with scores, the chosen verb and why (which inputs dominated), the active orders and their biases, and the outcome 3 seconds later. Log every Act event: shots fired, hits, body point, reticle error at trigger time, reaction time from belief to first shot, strafe pattern in use, reload timing relative to fights. Log every Director response, the validation result, and whether it changed what the team did.

### 9.2 Humanness metrics

From the BotPrize and later research, these numbers separate bots from humans; collect them for bots and for human players in the same matches and compare distributions, not averages:

- Reaction time from first sight to first shot (distribution with tail).
- Accuracy per weapon per band, and headshot ratio; compare to the human percentile the tier claims.
- Stationary time share, path entropy (how varied the routes are), time to pick up items after seeing them.
- Target switching frequency and the cost of a switch.
- Time spent in combat versus objective behaviors per mode (343 found objective play collapsed when shared awareness went in; watch for it).
- Grenade accuracy and grenade timing relative to enemy movement.
- Death causes by type: a human-like distribution has deaths to grenades, to being outnumbered, to power weapons, to over-chasing; a bot-like distribution has deaths mostly to being out-aimed.
- Chat or callout rate if surfaced.

### 9.3 Believability tests

- Blind judge test: human testers play mixed lobbies and tag each player as human or bot after the match, with a confidence. Target: at Tier 4 and above, bots are tagged bot no more often than humans are. The BotPrize winners reached 52 percent humanness; aim for parity with human testers rather than a number.
- Replay review: a reviewer watches the match with the decision log overlaid and marks every moment a bot did something a player would not, categorized (aim, movement, decision, knowledge, team). Fix categories, not instances.
- Ablations: squad layer off, Director off, Kev off, each tier flag off one at a time. Each ablation should degrade in the expected direction; if turning a flag off makes the bot play better or no different, the flag is not doing what the design says.
- Tier ladders: Tier n versus Tier n plus 1 in fixed matches should give the higher tier a clear but not crushing edge (around 60 to 70 percent win rate); Tier 1 versus Tier 7 should be a wash for Tier 7 that still looks like a human team, not an aimbot team.

### 9.4 Calibration against humans

If the project has human rating data, map each tier's measured stats (accuracy, reaction, K/D in mixed lobbies) to human percentile bands and move the tier parameters until the bot's distribution sits where its human counterpart does. Do this per game title, because CE pistol accuracy and H4 BR accuracy are different human distributions.

### 9.5 Determinism and reproducibility

Seed every random source per bot per match so a replay reproduces decisions. Director responses are logged with their prompts and replayed from the log in tests rather than re-queried, so AI tests do not depend on model nondeterminism. Keep a fixed regression set of match replays and run the decision pipeline over them in CI; a change that alters more than a set share of decisions must be reviewed.

### 9.6 Tuning order

1. Movement until it looks right in an empty map.
2. Aim and trigger until Tier 4 matches a mid-ranked human's accuracy distribution.
3. Reaction and perception until bots stop seeing things humans cannot.
4. Single-bot decisions in Slayer until deaths look human.
5. Mode add-ons one at a time with the squad layer.
6. Tiers, by turning flags on from Tier 1 upward and checking each one changes play visibly.
7. The Director last, and only after the squad layer can win games alone.

## 10. Implementation blueprint

### 10.1 File layout for the project

```
bots/
  core/
    sense.*            perception model, delay queue, tier-gated inputs
    memory.*           beliefs, decay, team board
    assess.*           threat, confidence, pressure, need, posture
    decide.*           impulses, survive, utility selector, hysteresis
    plan.*             verb -> short plan; path cache
    act/
      move.*           movement controller, strafe patterns, peeks
      aim.*            acquire/track/correct controller, error model
      trigger.*        pacing per weapon
      ability.*        use-now, hold, bait rules
    verbs/             one file per verb (fight, pickup, deliver, ...)
  squad/
    roles.*  callouts.*  spacing.*  setups.*  trades.*
  director/
    state_builder.*    renders the state document
    kev_client.*       choice/score/noul questions, thresholds
    ollama_client.*    prompt, JSON schema, timeout
    validator.*        vocabulary, reality, feasibility, safety, rate
    orders.*           blackboard orders with TTL
  data/
    tiers/             tier1.json ... tier7.json (unlock flags, reaction, aim)
    personalities/     rusher.json anchor.json flanker.json sniper.json
    games/             ce.json h2.json h3.json reach.json h4.json (weapons, damage, movement, abilities)
    maps/<game>/       <map>.json (callouts, spots, timers, routes, jumps, setups, spawns)
    modes/             slayer.json ctf.json koth.json oddball.json assault.json infection.json firefight.json
    vocab/             director phases, orders, roles, coaching heuristics
  tools/
    replay_viewer      decision log overlay
    metrics            humanness metric reports
    ablation           flag toggles and ladder matches
docs/bot-brain/        this guide's exported files
```

### 10.2 Tier profile schema

```json
{
  "tier": 4,
  "name": "Skilled",
  "reaction": {"mean_ms": 250, "sd_ms": 60, "busy_penalty_ms": 120, "anticipation_bonus_ms": 80},
  "aim": {"error_scale": 1.0, "acquire_gain": 0.35, "acquire_noise": 0.2, "overshoot_p": 0.25, "track_lag_ms": 100, "tremor_amp": 0.4, "flinch_scale": 1.0, "move_penalty": 1.3},
  "perception": {"radar": "regular", "sound": "full", "callouts_in": true, "detect_ms": {"melee": 100, "short": 150, "medium": 250, "long": 400}},
  "memory": {"enemy_decay_s": 6, "timers": "rough", "spawn_prediction": "basic"},
  "knowledge": {"routes": "shortcuts", "setups": "mode", "weapon_roe": "full", "packs": ["roe", "modes", "maps:standard"]},
  "decide": {"threat": "full_confidence", "survive_threshold": 0.35, "hysteresis": 0.15, "softmax_temp": 0.08},
  "movement": {"strafe": ["side", "reversal", "crouch"], "peeks": ["jiggle", "preaim"], "stop_to_shoot": "precision"},
  "act": {"reload": "cover", "grenades": "anticipation", "abilities": ["use_now", "hold"], "techniques": ["descope", "melee_timing"]},
  "team": {"shared_awareness": true, "roles": "assigned", "trades": "on_call", "director": "roles"}
}
```

### 10.3 Mode add-on schema (CTF excerpt)

```json
{
  "mode": "ctf_multi",
  "ambitions": [
    {"id": "enemy_flag", "type": "carry_deliver", "object": "flag:enemy", "teams": ["us"], "verbs": ["pickup", "deliver", "support"]},
    {"id": "our_flag", "type": "defend_return", "object": "flag:ours", "teams": ["us"], "verbs": ["guard", "hold", "interact"]}
  ],
  "pressure": "scripts/ctf_pressure.lua",
  "biases": {"deliver": 1.4, "support": 1.2, "guard": 1.1, "fight": 0.9, "scout": 0.8},
  "roles": {"min": {"returner": 1}, "list": ["carrier", "escort", "anchor", "returner"], "swap_on": ["death", "flag_event"]},
  "phases": ["setup", "pull", "run", "defend", "reset"],
  "callouts": ["flag pulled", "flag down", "flag home", "carrier low", "one in our base"]
}
```

### 10.4 Director order schema (blackboard)

```json
{"from": "ollama|kev|squad", "issued_at": 183.2, "state_hash": "ab12", "ttl_s": 10, "confidence": 0.72,
 "phase": "push", "orders": [{"bot": "b3", "verb": "push", "target": "top_mid", "on": "timer:sniper"}],
 "roles": {"b1": "carrier", "b2": "escort", "b3": "anchor", "b4": "returner"},
 "priorities": {"objective": 0.7, "map_control": 0.5, "power_weapons": 0.6, "kills": 0.3, "safety": 0.4}}
```

### 10.5 Decide tick pseudocode

```
function decide(bot):
  beliefs = bot.memory.current(now - bot.tier.reaction.sample())
  if impulse = checkImpulses(beliefs): return runImpulse(impulse)
  s = assess(bot, beliefs)                      # threat, confidence, pressure, need, posture
  if s.confidence < bot.tier.survive_threshold and escapeExists(bot):
      return choose(RETREAT or REPOSITION)
  candidates = []
  for verb in VERBS:
      if not mode.allows(verb) or not bot.tier.unlocked(verb): continue
      if not verb.preconditions(bot, beliefs, mode.ambitions): continue
      score = verb.utility(s, beliefs)           # 0..1 from curves
      score *= mode.bias(verb) * bot.personality.bias(verb) * clamp(orders.bias(bot, verb), 0.5, 1.5)
      if verb == bot.current: score *= (1 + bot.tier.hysteresis)
      candidates.add(verb, clamp(score, 0, 1))
  chosen = softmaxPick(candidates, temp = bot.tier.softmax_temp)
  if chosen != bot.current and bot.holdTimeRemaining() > 0 and not materialChange(): chosen = bot.current
  log(bot, candidates, chosen, reasons)
  return chosen
```

### 10.6 Aim controller pseudocode

```
function aimTick(bot, dt):
  t = bot.target                                # belief, may be stale
  if t is None: idleScan(bot); return
  goal = bodyPoint(t, bot.weapon)               # head or chest by weapon ROE
  goal += t.velocity * bot.tier.track_lag       # lag behind movement
  err = angleTo(goal) - bot.reticle
  if bot.aimPhase == ACQUIRE:
      step = err * bot.tier.aim.acquire_gain
      step += gaussian(0, bot.tier.aim.acquire_noise * |step|)
      if rand() < overshootP(|err|): step *= 1.15
      if |err| < settleRadius(bot.weapon): bot.aimPhase = TRACK
  else:
      step = err * trackGain + tremor(bot.tier.aim.tremor_amp)
  step = limitTurnRate(step, bot.personality.turn_cap)
  bot.reticle += step
  if bot.flinchTimer > 0: bot.reticle += gaussian(0, flinchAmp * bot.tier.aim.flinch_scale)
  if trigger.ready(bot) and withinAccepted(bot.reticle, goal, errorEllipse(bot, t)): fire(bot)
```

### 10.7 Director loop pseudocode

```
every 2..5 s (per team):
  state = buildState(team)                      # team beliefs only
  plays = squad.candidatePlays(state)           # 4..8 from playbooks
  r = kev.ask(state, play=Choice(plays), order_valid=Noul(), urgency=Score(5), risk=Score(5))
  if r.order_valid.p < 0.4: orders.drop(team)
  if r.play.p >= 0.45 and r.play.p - currentPlayP > 0.15: squad.setPlay(r.play.choice)

every 10..30 s (per team):
  state = buildState(team)
  resp = ollama.chat(system=coachPrompt, user=state, format=ORDER_SCHEMA, timeout=2*medianLatency)
  if resp and validator.ok(resp, team, map, mode): orders.replace(team, resp, ttl=resp.ttl)
  else: log.discard(resp)

every 100 ms (per bot):
  decide(bot)                                   # reads orders.bias(bot, verb), never the raw text
```

### 10.8 Claude Code notes

- Add to CLAUDE.md: Bot brain design is docs/bot-brain/09-bot-brain-architecture.md; read sections 3, 5, 6 and 8 before touching bots/core, bots/squad or bots/director. Tier behavior is data in bots/data/tiers; do not hard-code tier checks in verbs.
- Treat the unlock table (Section 5.2) as the source of truth for tier flags; generate the tier JSON from it and keep them in sync.
- Every new verb needs: preconditions, a utility function with named inputs, a plan expansion, hold time, and a log reason string.
- Every Director field needs a validator rule before it is read anywhere.

## 11. Sources and further reading

- Damián Isla, Handling Complexity in the Halo 2 AI, GDC 2005 (the behavior-tree paper); Isla, Building a Better Battle: The Halo 3 AI Objectives System, GDC 2008 (slides: https://web.cs.wpi.edu/~rich/courses/imgd4000-d09/lectures/halo3.pdf).
- Brie Chin-Deyerle, Thinking Like Players: How Halo Infinite's Bots Make Decisions, GDC 2022, public slides: https://media.gdcvault.com/GDC+2022/Speaker+Slides/ThinkingLikePlayersHowHaloInfinitesBotsMakeDecision_ChinDeyerle_Brie.pdf (verbs, ambitions, BotManager blackboard, BT plus utility, 200 to 250 ms reaction, hysteresis, shared awareness).
- Sara Stern, Deconstructing the Combat Dance: Designing Multiplayer Bots for Halo Infinite, GDC 2022 (GDC Vault; summarized on the AI and Games channel, episode 71).
- Kotaku, Why Halo Infinite's Bots Act So Much Like People (2021): https://kotaku.com/why-halo-infinite-s-bots-act-so-much-like-people-1847511140 (radar gated by tier, shortcuts, modeling human play); Game Informer, How Halo Infinite's Bots Became So Ruthless (2021).
- Dave Mark and Kevin Dill, Improving AI Decision Modeling Through Utility Theory, GDC AI Summit 2010; Dave Mark and Mike Lewis, Building a Better Centaur: AI at Massive Scale (Infinite Axis Utility System), GDC 2015; Dave Mark, Behavioral Mathematics for Game AI.
- Jeff Orkin, Three States and a Plan: The AI of F.E.A.R., GDC 2006 (GOAP).
- BotPrize: UT Austin, Artificially Intelligent Game Bots Pass the Turing Test (2012): https://www.cs.utexas.edu/news/2012/artificially-intelligent-game-bots-pass-turing-test-turing%E2%80%99s-centenary ; Schrum, Karpov, Miikkulainen, UT^2: Human-like Behavior via Neuroevolution of Combat Behavior and Replay of Human Traces: https://nn.cs.utexas.edu/downloads/papers/schrum.cig11competition.pdf ; Mora et al., Optimising Humanness (MirrorBot), 2017.
- Tastan and Sukthankar, Learning Policies for First Person Shooter Games Using Inverse Reinforcement Learning, AIIDE 2011 (human-likeness comes from how states are valued): https://cdn.aaai.org/ojs/12430/12430-52-15958-1-2-20201228.pdf
- Aiming models: Gori and Rioul, FITTS: a feedback information-theoretic model of trajectory variability in aimed movements: https://arxiv.org/pdf/1804.05021 ; Kanervisto et al., GAN-Aimbots (the 0.2 noise ratio and slow-aim design used to mimic humans): https://arxiv.org/pdf/2205.07060
- LLM directors over reactive agents: SwarmBrain (StarCraft II, reflex net under an LLM brain); STRATA tiered agents (strategic, logistics, tactical separated by scope, authority and frequency): https://arxiv.org/pdf/2609.38881 ; Hösch et al. (EA), Hierarchical Control in Multi-Agent Games: LLM-based Planning and RL Execution, 2026 (LLM selects skills, humans rated it most human-like).
- Kev-4B model card (decision model, choice/score/noul, latency, memory, 8k validated context): https://huggingface.co/hbragge/kev-4b ; repository github.com/jaredpalmer/kev.
- Ollama structured outputs (JSON schema in the format field): docs.ollama.com; Instructor's Ollama guide: https://python.useinstructor.com/integrations/ollama/
- FyreWulff, the Halo 3 spawn system (used by the Mechanics tab): https://halo.bungie.org/misc/fyrewulff_spawnsystem
