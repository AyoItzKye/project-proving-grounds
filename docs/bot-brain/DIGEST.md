# Bot-brain guide digest (Claude's working notes)

the player's guides (01-10 in this folder) condensed into rules to implement, with where each lands in
our code and its status. Rule IDs: G<file>.<section>. Status: TODO / DONE (commit) / PARTIAL / N/A
(why). Re-read the guide section before coding a rule; this file is an index, not a replacement.

## Hard the player requirements (message)
- R1 Score-relative play: thresholds follow the VARIANT's score limit read from the game (50 -> act
  conservative at 45, 100 -> at 95), never constants in code. Needs per-game readers of score limit,
  team scores, time limit and time left.
- R2 Bots: no grouping into blobs, no getting stuck in nonsense spots, actively engage and get kills,
  minimal self-deaths (falls, own grenades/rockets), games end by score not by the clock. Camping is ok.
- R3 Tools to track movement and gameplay (diagnose stuck, crowding, kills, self-deaths, score pace).
- R4 Sim LiDAR on all maps. R5 research the 16-player cap (Reclaimer etc.). R6 Kev-4B vs Ollama.

## 09 Architecture (the target shape)
- G09.1/2 BT skeleton + utility selector over verbs, impulses as hard interrupts, hysteresis
  (current verb +10-25%, challenger must beat by a margin), softmax pick among near-equal verbs.
- G09.3 Layers: Sense (FOV ~90-100, LOS to several body points, detection time 100 ms melee .. 400
  ms long; sound; radar tier-gated) -> Remember (beliefs w/ confidence + decay by tier 2..10 s;
  shared team board with 300-800 ms comms delay at tier>=3) -> Assess (threat, confidence 0-1,
  objective pressure, resource need, team need, posture) -> Decide (impulses, survive check, valid
  verbs, score, hysteresis, log reason) -> Plan (1-4 s plans) -> Act (human-limited controllers).
- G09.3.7 Rates: sense/remember 20 Hz, assess/decide 10 Hz, plan <=5 Hz on change, act 60 Hz,
  squad 2 Hz, director every 5-20 s.
- G09.4.1 Reaction: distribution per tier (mean/sd), busy penalty, anticipation bonus; perception
  through a DELAY QUEUE (react to what was true ~250 ms ago).
- G09.4.2 Aim: acquire (proportional step + gaussian noise ~0.2 x move, overshoot), track (lag 60-150
  ms, tremor 8-12 Hz), micro-correct (error ellipse, horizontal > vertical; grows with own movement,
  target movement, flinch, band), fire only when reticle inside accepted radius and pacing allows; no
  firing while turning fast; target switch costs a reaction + re-acquire.
- G09.4.4 Mistakes = missing skills (consistent), panic (confidence collapse widens aim, slows
  reaction), tilt (3 quick deaths -> more aggressive for 30 s).
- G09.4.5 Commitment: hold times Fight 1.5 s, Hold 5 s, Retreat until shields recharge; hesitation
  100-300 ms when two choices are close.
- G09.4.6 Movement first: stop-to-shoot for precision (tier), strafe patterns by tier, look around
  while moving, take known shortcuts by tier.
- G09.5 Seven tiers (Recruit..Pro) unlock skills, not stats. Table 5.1 reaction/aim; 5.2 unlock flags
  (radar, sound, callouts, memory decay, timers, spawn prediction, routes/jumps, setups, threat
  scoring, retreat threshold, objective weight, strafe, peeks, stop-to-shoot, reload timing,
  grenades, abilities, techniques, shared awareness, roles, trades, director). Personality on top
  (rusher/anchor/flanker/sniper/...; patience, grenade appetite, tilt). Mix personalities per team.
- G09.6 Core + TierProfile + Personality + GameProfile + MapPack + ModeAddon + DirectorLink. Mode
  add-on: ambitions, objective pressure fn, verb biases, roles+phases. Biases capped 0.5-1.5; Survive
  and impulses outside the biased set.
- G09.7 Squad layer (code, 2 Hz): roles, callouts, team shots, trades, spacing (REPULSION so bots do
  not stack in a doorway; cohesion for escorts), setups. Director = Kev (fast judge, choice/score/noul)
  + Ollama (slow coach, JSON schema, validated). Orders = intents with TTL, bias <= 1.5x.
- G09.8 Authority ladder: impulses/survive > mode legality > bot verb selection > squad > director.
  Validation gate (vocabulary, reality, feasibility, safety, rate, confidence). Min plan hold 8 s.
- G09.9 Telemetry per decision (scalars, verb scores, chosen + why), humanness metrics (reaction
  first-sight->first-shot, accuracy per weapon per band, stationary share, path entropy, target
  switches, combat vs objective time, death causes), ablations, tier ladders.
- G09.9.6 Tuning order: movement, aim, perception, single-bot slayer decisions, modes, tiers, director.

## 01 Rules of engagement (knowledge + decision stack)
- G01.1 Range bands in WU: Melee 0-0.8, Short 0.8-4, Medium 4-12, Long 12-30, Extreme 30+.
- G01.2 Fundamentals: strip shield then headshot; strafe irregular 0.3-0.8 s reversals; jump only to
  reach cover/dodge; peek and retreat; grenades where the enemy is going; melee combos; radar dot
  vanishing = crouched enemy waiting; fight from cover; height advantage; team shot; stay within
  Medium band of a teammate; reload behind cover / after a kill, never mid-fight unless empty (then
  melee at melee band, or swap at medium).
- G01.3 Per-game table (sprint, dual wield, equipment, health system, fall damage: CE yes, H2/H3/H4
  no, ODST/Reach yes).
- G01.4 Weapon ROE per game: class bands (precision Medium/Long; automatic Short; CQB Melee/Short;
  sniper Long+; explosive never at melee band (self-damage); support = strip then precision).
- G01.5 Vehicles (later: we drive CE Ghosts only).
- G01.7 Power positions scored by height, sightlines, entrances, escape, cover, resupply; timers;
  per-map power weapons + positions tables.
- G01.8 SCORE STATE TABLE (R1): far ahead (lead > 20% of limit) conservative; slightly ahead
  controlled; even standard; slightly behind pressure; far behind + time/score running out
  aggressive; ENEMY WITHIN 3-7 POINTS OF WINNING sneaky + conservative; last 60 s and leading: hide
  and hold. Posture 0..1: default 0.5, far ahead 0.3, far behind late 0.9, enemy one kill from
  winning 0.2. Slayer: value life = a kill; two-on-one; rotate as a group between 2-3 power positions.
  CTF roles 1 runner, 2 escorts, 1 defender; lead management. Oddball/KOTH rules.
- G01.9 Tier aim/reaction table (Recruit 30-40% at medium .. Pro 85-95%); play styles (slayer,
  support, sniper, rusher, objective, vehicle, defender, lone wolf); style drifts with score.
- G01.10 Priority stack: survive > immediate threat > objective > team > map control > roam.
  Threat score: weapon base (power in band 100, precision at medium 60, auto in band 70 / out 20,
  sniper at long 90) x proximity (melee 1.5 .. extreme 0.4) x shield (popped 0.6) x facing (aiming at
  me 1.3, away 0.5) + 40 objective carrier + 30 teammate already shooting it; switch only if +25%.
  Engagement decision 1-5 (in band/out of band, shield advantage, enemy power weapon -> break LOS).
  States: Retreat, Fight, Close, Hunt, Objective, Control, Roam; min dwell 0.5 s, Retreat instant.
- G01.11 Scenario library 1 (weapon bands, health/shield, grenades, melee, reload/ammo).
- G01.12 Scenario library 2 (team, objective, map control, vehicles, retreat, respawn, firefight);
  catch-all order: survive, take the kill, mode says go, team shoot, timer, hold best position.
  Score rows: enemy needs <= 7 -> posture 0.2; team needs <= 3 -> hold and let them come; 30 s left
  leading -> hide; 30 s left behind -> posture 0.9. Respawn: rejoin the team; lone fresh spawn holds.
- G01.13 Pro habits (Veteran+ only): timers 15 s early, never straight lines, lead in H3, etc.

## 10 Multi-brain and director integration
- G10.1 Killzone 2 lessons: 3 rates (individual 5 Hz, squad 2 Hz, faction ~6.7 s, teams interleaved);
  chain of command; orders refreshed not accumulated; priority classes initiative / follow / commit;
  bots report only first sight, lost, killed, order done. FAILURE TO AVOID: a strategic layer that
  reasons from one scalar (kill score) sent every bot to ONE area -> kill rate collapsed. (Relevant to
  R2 grouping: never let the team plan collapse everyone onto one spot.)
- G10.2 One blackboard per team, sections with one writer each (rules, ambitions, timers, beliefs,
  self, roles, plan, orders, requests, events, director_in/out, morale). Not engine truth.
- G10.3 Messages: seen/lost/killed/died/order_done/status/pickup/timer_seen/need; orders target a
  callout/ambition/bot/belief, never a raw point; one active order per bot; peer requests team_shot,
  trade, pickup_intent (do not race me for the sniper), ride; 3 s TTL.
- G10.4 Clocks; adaptive referee/coach periods; match phases (opening runs authored setups, no
  director); latency budget: bot reflex 250-400 ms, squad 0.6-1.5 s, referee 1-3 s, coach 4-15 s.
- G10.5 Director runs in another process; Ollama: keep_alive -1, num_ctx 8192, think false, one
  model loaded; Kev: python -m kev.serve --run jaredpalmer/kev-4b --port 8008, POST /v1/systemone
  {model, state, questions{name:{type choice|score|noul,...}}}; 14.3 GB resident (16 GB GPU = Kev only,
  or Kev-0.8B + 8B coach). Client: one in-flight request per model per team, timeouts (referee
  1.5 s), no retries, newest response wins, warm-up, degraded after 3 timeouts. Degradation ladder:
  NEITHER model must still play well (baseline).
- G10.6 State builder: stable prefix -> volatile suffix; callouts not coordinates; <2000 tokens.
- G10.7 Referee questions: play (choice among 4-8 candidates incl. current), order_valid (noul),
  urgency, risk, focus; per mode extras (Slayer tempo push/hold/bait/stall). Thresholds: adopt play
  p>=0.45 and +0.15 over current after min hold; order_valid<0.4 drops the plan. Play-transition cache.
- G10.8 Coach: qwen3:4b-class, format=JSON schema, temp 0.3, system prompt rules 1-10, schema 8.4.
- G10.9 Invariants 1-10; validator V1-V16; staleness table; conflict matrix (own Fight at short band
  beats a director rotate); hysteresis table (verb 1.5 s fight / 5 s hold, switch margin 15%).
- G10.10 Humans on a bot team: never ordered, treated as occupied slots, assume the human attacks.
- G10.11 Build order: blackboard + recorder, reports/orders, SQUAD LEADER WITH NO MODELS (must win
  alone), playbook, validator, state builder, then referee, coach, calibration. Models last 30%.

## 07 Game mode playbooks
- G07.S Slayer: score limits typical 50 (TS), 25 (FFA, doubles), 100 BTB, H4 points (10/kill).
  Roles anchor / slayer / support / floater. Phases: opening (move as a unit to nearest power position,
  slayer+support take first power weapon with a grenade first; nobody crosses mid alone) -> control
  (hold two ADJACENT positions, rotate as a PAIR, fights only 2v1, after a kill push as a group to the
  next position, never a solo chase) -> lead management (up >=5 stop pushing, hold; down >=5 group as
  four and push one side, accept even trades) -> closing (last 5 kills or 60 s: leading hide and hold;
  trailing all-in). NOTE: "up by 5"/"last 5 kills" must scale with the variant limit (R1).
  Spawn control: trap from the edges 40-60 ft from the cluster, never inside the enemy spawn zone.
  Buddy spawn: a dead bot waits for teammates spawning near it.
- G07.FFA: third-party rule (find a fight in progress, shoot the winner), travel the map edge, hold a
  corner seeing one lane, move after each kill; play to be first; 2nd with 20 s left pushes leader.
- G07.SWAT: pre-aim head height at corners, hold corners not lanes, no crouch/jump, spread out (no team
  shot value), stay within Medium of one teammate.
- G07.CTF: per-game rules table (carrier cannot shoot except H4 magnum; flag at home to score; touch to
  return except H4 auto-return; H4 auto pickup). Multi flag roles runner, lead escort 10-20 ft ahead,
  rear escort 10 ft behind facing back (picks up the flag if the runner dies), defender (never chases,
  sits off the flag, crouched). Pull when >= 2 enemies dead or far; covered route not shortest; home
  stretch: wait under cover near the cap point if our flag is away. Lead mgmt: +1 keep an escort home;
  +2 stop pulling, defend with three. Return only if no enemy sightline; a dropped flag near the enemy
  is bait.
- G07.ODD Oddball: carrier hides crouched in a 1-2 entrance corner, two guards 10-25 ft inside angled,
  a hunter outside; throw the ball when shields drop; lost hold -> fall back, then push as four with
  grenades. Ahead by 60 s: hunter joins guards.
- G07.KOTH: one bot inside crouched at the edge, guards on overlooking high ground outside grenade range,
  rotator goes to the next hill at 10 s left; contest by stepping in.
- G07.Assault/Territories/Dominion/Extraction/Stockpile/Invasion/Infection/Juggernaut/VIP/Regicide/
  Grifball/Race: later (our bots do not play these yet). Party posture rule: read traits.
- G07.FF ODST + Reach Firefight: one hold + one fallback, lanes per bot, life economy (low health ->
  pack; dead teammates -> hold, never push), target priority (fuel rod grunts, engineers, chieftains
  from range, jackal snipers, hunters from behind, grunts last), skull rules, holds by map table,
  roles marksman/heavy/line holder/runner. Failure modes: chasing into the open, hunters in a hallway,
  standing in a phantom lane.

## 06 Mechanics and spawns
- G06.1 Tag stats: run 2.25 (CE/H2/H3), 2.2 Reach/H4, 2.3 H2A; shield 75/70, delay+recharge CE 6+4,
  H2/H3 5+2, Reach 6+3, H4 6+2; health 75 CE (no regen), 45 others (H2/H3 regen after 10 s).
  Rules: a retreat at a popped shield = out for 7-10 s, do not re-peek at 3 s; H2/H3 low health
  -> no second fight for 10 s; Reach health regenerates only to the next third; CE values health
  packs over shield resets.
- G06.2 Damage: H3 115 hp (70 + 45), BR bullet 6; melee 70 = exactly a shield; count DAMAGE (team shot
  adds up) and switch to the head when the shield is gone; plasma for shields, kinetic for health.
- G06.3 Spawn (H3, FyreWulff): base 1000, ally near +500, enemy near -500, teammate death -700
  recovering +100/s, own flag home +700, slayer zone +300; 7-second rule; buddy spawn beats zones.
  Rules: predict enemy respawn near their living teammates and away from us; one living bot at a
  safe spawn cluster pulls the team back as a group; push spawns with POSITION, not fire; kill
  near their cluster keeps it closed.
- G06.4 Competitive markers (no radar etc). G06.5 Red reticle range = the weapon's real range: commit
  only inside RRR; low tiers close to 2/3 RRR.

## 02 Advanced techniques (per game)
- CE: pistol cadence ~0.2 s/shot (3 in 0.6 s), zoom at medium+, magnetism lets upper chest count at
  long; grenades thrown far onto camp spots and spawns; crouch does not hide from radar in CE;
  FALL DAMAGE: >~2 player heights pops the shield; ladders: grenade the top; health packs route.
- H2 Classic: BXR, double shot, sword fly (tier 6+), dual wield drop rules, super bounces (casual Pro
  only). H2A: none of the combos.
- H3: BR burst 0.5 s medium / 0.7-0.8 s long, lead (projectile), 2 bursts + melee, crouch-jump,
  crouch-walk off radar, man cannon riders cannot strafe. Standard 4v4 setups per map.
- Reach: DMR bloom pacing 0.4-0.5 s at medium/long, spam at short; armor lock / jetpack / camo rules.
- H4: sprint discipline (stop sprinting 10 ft before a corner), thruster, PV, loadouts, ordnance.
- Cross-game: strafe patterns (basic irregular 0.3-0.8 s, reversal on hit, crouch strafe not in CE,
  backpedal vs CQB, jump at most once a fight), peeks (shoulder, jump, crouch, wide, pre-fire),
  pre-aim heights (head at medium, chest at long, back to head once shields pop), de-scope, radar
  play, edge jumps, ladder/lift exits, reload behind cover, switch instead of reload, sound.

## 03 Weapons
- Precision table (magazine, zoom, kill counts) + head-shot timing rule: count hits to the shield pop
  (2 pistol, 3 BR bursts, 4 DMR, 6 carbine, 4 H4 BR bursts), aim center of mass until then, head after.
- Automatics: decide in the first 0.5 s: at Short band fight (AR + melee), else leave.
- CQB, snipers (lane selection, relocate after every kill / 2 kills change structure, swap to
  secondary when a dot approaches), explosives (rockets at feet, never within 15 ft of self, keep for
  vehicles/groups), plasma pistol noob combo, grenade throw table (frag throw range 60-70 ft CE, 50
  H2, 45 H3+; fuse; radii) and throw technique (where the enemy will be in 2 s; never at melee band).

## 08 Equipment and abilities: use-now / hold / bait tables (H3 equipment, Reach AAs, H4 AAs,
powerups). brain/equipment.py: every use-now trigger, hold rule, bait rule and
counter, on guide 09's ladder (novice obvious cues and bad uses .. top sneaky uses). Powerup
priority: OS before a push, camo for flankers/snipers. Live: the use input is decoded statically
for Halo 3 only; Reach / H4 / H2A wait for tools/decode_buttons.py.

## 05 Map playbooks: callouts, openings, standard holds, grenade spots, jumps per map (CE: Battle
Creek, Chill Out, Damnation, Prisoner, Hang 'Em High, Blood Gulch, Rat Race, Wizard, Sidewinder;
H2: Lockout, Midship, Beaver Creek, Sanctuary, Warlock, Ascension, Ivory Tower, Zanzibar,
Coagulation...; H3: Pit, Guardian, Construct, Narrows, Heretic, Valhalla, High Ground, Last
Resort...; Reach: Countdown, Zealot, Reflection, Sword Base, Asylum, Pinnacle, Powerhouse,
Boardwalk...; H4: Haven, Adrift, Abandon, Solace, Complex, Ragnarok, Exile...). Use as map packs:
standard hold positions per map = our "power positions" (callouts.json zones).

## 04 Vehicles: driving/gunning/boarding rules. We drive CE Ghosts only; rest N/A for now.

## Implementation status (update as work lands)
| Rule | Where | Status |
|---|---|---|
| R1 score posture from the variant's limit and clock | brain/match.py posture(), tempo(); director sets bot.posture | DONE (self-test: 45/50 vs 95/100) |
| R1 score readers | brain/live.py match_state(): CE (variant +0x58 limit, +0x78 time ticks, slayer_globals 0x2E32120), H3 (globals +0x249C0 scores, +0x17BC limit, +0x170D minutes, +0x101B4 ticks at 60/s) | CE, H2 (limit + clock; team score = death tally), H3, Reach, H2A, H4 DONE (HUD-checked; H2A + H4 clock from the player records, ~10 s early; H4 points: near-win window in kills via the score step); CTF/Oddball/King scores in CE TODO |
| R2 games end on score: no end-game stall | match.tempo: a leader near the win closes out (close_out, 0.7) when its pace will not reach the limit in time; the trailing team stays careful (the player rule) | DONE (self-test; live: see HANDOFF) |
| R2 minimal self-deaths: edge guard | bot.edge_guard: H2A ground offset 0.38, air check from take-off height, momentum brake, jump only with floor within 1.5 where it lands, trusted jump run-ups | DONE (Lockout falls 17 -> 1-7 of ~86 deaths; tools/test_edge_guard.py, ground_offset.py, fall_check.py) |
| R3 learned data stays honest | terrain.learn_blocked: 3 dry episodes per sight line, 300 keys a map; learn_stuck: 3 reports from 2+ bots, 10 new a match, none in fights or at voids; nav() descent never through its own cell | DONE (A/B: drifted blocks 40 kills a game, committed 89; stuck growth halved in sim; tools/test_focus.py, test_stuck_learning.py) |
| R2 pace: games end on score | match.tempo(): leader pace vs time left -> tempo_push (posture 0.7) | DONE, needs time_left |
| G01.10 threat scoring + 25% switch margin + team-shot +30 | bot.threat(), pick_target(); director team_focus | DONE |
| G01.8/12 enemy near win: fight only 2v1 | bot.decide avoid (posture <= 0.3) | DONE |
| G01.11 / G06 retreat threshold by posture, wait out the recharge (7 s, shield 95%) | bot.decide thr, recharge_until | DONE |
| G01.4 explosives never inside own blast / onto teammates; no grenade near teammates | bot.fight mates_near, SPLASH d < 3 | DONE |
| G07 Slayer roles: anchor / slayer+support pair / floater; hold pairs when protecting; push pairs from two sides | director.slayer_slots | DONE |
| R2 no blobs: every bot its own spot near a team point | director.spread() | DONE (measure) |
| G07 CTF lead management (+1 extra defender, +2 stop pulling) | director.role_slots | DONE |
| G01.7 power positions per map | tools/power_positions.py -> maps/<map>/positions.json -> m["positions"] | DONE (heuristic; roofs need jump links) |
| R3 telemetry | tools/match_report.py (score, deaths by kind, stuck, blobs, idle, goal mix, map PNG), world lines in live + sim traces, tools/watch_freeze.py | DONE |
| G09.4 aim / reaction | existing Aim + Perception (recognition delay, flick, overshoot) | PARTIAL (pre-existing) |
| G09.5 seven tiers, unlock flags | profiles.py: 4 tiers, the same HANDS for all, CRAFT unlocks incl. tactics (cover, recharge, retreat, turn on the attacker) | PARTIAL (4 tiers; behaviour only) |
| G09.4.2 fire pacing by band | bot.fight: an automatic (bot.AUTO) holds the trigger at Short band (< 4 WU), taps at FIRE_GAP beyond; rifles keep FIRE_GAP x 1-1.5 at every band (H3 BR cycle 0.5 s > 0.45 unverified) | PARTIAL (tools/test_brain_tactics.py; live not yet) |
| Loadouts (Reach, H4, H2A) | brain/loadouts.py, live_bots.loadout_check, botcore SET_LOADOUT (s59): slot for the problem a bot keeps dying to (outranged / close / vehicle), slot guns learned from spawns, tier = deaths needed (novice never) | PARTIAL (tools/test_loadouts.py; not run live) |
| G09.4.5 commitment | bot.decide: fight kept until dead / unseen COMMIT_S, follows the threat ranking; chase by the nav | DONE (tools/test_brain_tactics.py) |
| R3 observer (debug mode) | tools/observer.py + observer.html, Observer.bat; brain/tracefmt.py think / call / meta lines | DONE (tools/test_observer.py) |
| G08 equipment / abilities | brain/equipment.py (uses, counters, tells, energy from the kits' tags), brain/simgear.py, live readers (H3 +0x288; Reach +0x374; H4 / H2A +0x664), botcore s60 decoded-button table | PARTIAL (tools/test_equipment.py, gear_ab.py; input: H3 static only, rest to decode live; deployed objects live not decoded) |
| Difficulty by behaviour | profiles aware + teamwork; bot.py threat by tier, Easy tunnel, flank checks, close radar check, Recruit range bands, grenades by tier, engagement rule 5, retreat in time; tools/difficulty_report.py --ladder / --human | MODELLED (sim: Easy ~15% easier, upper tiers within noise; live untested) |
| the player game review | tools/engagement.py; fixes in bot.py (aim flicks, point blank, fight bumps, splash switch / trade, shotgun reach, absent beliefs), equipment.Kit.pressable, live.flags_by_stand (H3 CTF) | PARTIAL (tools/test_close_combat.py; sim A/B; live: H3 flags, Reach battery weapon names, score readers for those variants TODO) |
| Inputs outside CE (found) | melee, grenade, reload never sent in H2 / H3 / ODST / Reach / H4 / H2A; crouch only H2A / H4 | TODO (decode with tools/decode_buttons.py; botcore applies maps/_inputs/<game>.json) |
| G10 Kev referee / Ollama coach | brain/coach.py, live in every team game since (config E, coach only): state builder (6), schema + system prompt + 2 examples a mode (8.2-8.5), link contract with warm-up, adaptive timeout, health and a fallback to qwen3:4b (5.5), validator V1-V16 + staleness + V14 hold + invariants 4/5/8/9/10 (9), adaptive period and phases (4.3, 4.4), observability (trace, brain.txt, Observer, notices), tools/test_coach.py (10.3). Not done: Kev referee (does not fit next to MCC, research 11), post-match reviewer (8.7), play cache (7.5), enemy patterns (9.8), calibration and the on/off A/B gate (10.4) | LIVE, PARTS OPEN |
