# Guide 19 compliance: every rule of the objective brain against the code

the player's spec `docs/research/19-objective-logic-brains.md` (the objective brain, file 2 of 4) rule by rule, plus guide 18
Part 1 (what the objective brain hands the on-foot brain), Part 2.2 (objective brain tiers) and the spec's coach hooks.
Status: **done** (coded: the function named does it), **partial** (what is missing is named), **open** (not coded),
**blocked** (names the read or input still needed; blocked is not "not applicable"). Audit of the working tree
(HEAD 0880c6b; the only uncommitted brain change is bot.py's jump rates). Nothing was run for this audit: a row is done only
where the code does it.

Counts: the spec's 327 rule IDs: 6 done, 99 partial, 94 open, 128 blocked. The 53 other rows (posture effects, role
lists, guide 18 Part 1 fields and INT rules, Part 2.2 tiers, coach hooks): 7 done, 37 partial, 8 open, 1 blocked.

Short names: director = brain/director.py `Director`, bot = brain/bot.py `Bot`, match = brain/match.py, modes =
brain/modes.py, invasion = brain/invasion.py, live = brain/live.py, coach = brain/coach.py, vehicles = brain/vehicles.py,
live_bots = tools/live_bots.py. Code distances are game units (u).

How the code maps onto the spec's shape: one director per team (one per bot in free for all: live_bots `key`) computes a
score posture every tick (match.posture: a 0-1 value and a state word, not the four-value enum) and every 2 s hands each
bot an `Order(role, point, target, via)` from `Director.role_slots` (branches: Firefight, King, Invasion, the modes.py
modes, Oddball, VIP, CTF, else Slayer). Each bot weighs that order against fights, hunts and items in `Bot.decide`;
`Bot.keep_role` leashes defenders, escorts, runners and hunters. There are no per-bot target weights, stances, fire
discipline or grenade budgets. A carrier (`has_flag`: flag, ball, bomb, stockpile flag, core) never fights.

## What the brain can read, per game

| Game | Score / limit / clock | Objective state read | Modes the bots play |
|---|---|---|---|
| CE | limit and clock always; team score only for Slayer (Live.match_state, engine 2) | flags (Live.flags), hill (Live.king_hill), ball (Live.balls); race engine 5 read, not used | Slayer, CTF, King, Oddball |
| Halo 2 | limit and clock; no team score (LiveH2.match_state) | flags, ball; hill not decoded (LiveH2.king_hill returns None); no Territories / Assault watch | Slayer, CTF, Oddball |
| Halo 3 | team score, limit, clock (LiveH3.match_state) | flags and balls by stand, hill (HUD waypoint, radius fixed 3 u), VIP marks, Juggernaut by overshield, Assault bombs (objective_items, item_stands), Infection sides by gun; engine number names the mode (modes.H3_ENGINES); variant name not read | Slayer, CTF, One Flag, King, Oddball, Assault, Territories (no zones: see TERR), Juggernaut, Infection, VIP |
| Reach | team score, limit, clock (LiveReach.match_state) | flags, ball, hill (REACH_HILL), Invasion phase / sides / core / gates (invasion.Watch), the places of Territories, Assault, Stockpile, Headhunter, Infection from the scenario (modes.Watch), variant name | Slayer, CTF, One Flag, King, Oddball, Invasion, Territories, Assault, Stockpile, Headhunter, Infection; Juggernaut never marked (shield read is 1 - damage) |
| H2A / Halo 4 | team score, limit, clock (LiveH4F.match_state) | none: flags() and balls() return [], engine() returns 2; the places are exported (maps/h4_*: koth_hill, dominion, ext_site, rico_endzone, grif_goal; maps/h2a_*: terr_object, as_goal, koth_hill, rico_endzone, race_checkpoint) | Slayer only |
| ODST / Reach Firefight | none | AI positions and vitals (ai_units: no species, rank, wave, lives or skulls; riders skipped) | Firefight: escort the nearest human |

Cross-cutting:
- No game reads lives (per round or the Firefight pool), the round index, sudden death, hill move timers or order,
  territory capture or lock state, Assault's armed bomb, skull counts, the active drop point or haven, Stockpile's
  collection tick, or variant traits (carrier speed, uncontested scoring, hill traits). Rules that need them are blocked.
- CE objective engines and every Halo 2 game read no team score: CTF reads 0-0 ("even") all match; King and Oddball run
  on the death tally (live_bots.snapshot TALLY, set before the mode is known), so the posture there is noise.
- Fairness: director.mode_slots and invasion_slots count enemies near a zone
  from every enemy's true position (snap.players), and carry_point (Oddball) flees every enemy's true position, while the
  director's docstring says it knows only what its bots report.
- the player decision: P-08 / SLAY-CORE-08 (enemy about to win: AGGRESSIVE) contradict the player's rule coded in
  match.posture (enemy_near_win: careful, 0.2).

## Part 0. Architecture, posture engine, universal modules

| Rule | Status | Where / what is missing |
|---|---|---|
| 0.1 interface (inputs and outputs every 0.5 s) | partial | director.update every tick, assign_roles every 2 s; out: Bot.posture, Order, team_focus; no target_weights, stance or per-bot vehicle_request (crew_orders instead); in: no lives, round, sudden death, traits |
| P-01 lives limited, one life left: CONSERVATIVE | **blocked** | lives are not read in any game (live *.match_state: score, limit, clock) |
| P-02 sudden death, behind: DESPERATE | **blocked** | sudden death is not read |
| P-03 sudden death, ahead: CONSERVATIVE | **blocked** | as P-02 |
| P-04 margin <= -0.30, time_frac < 0.25: DESPERATE | partial | match.posture far_behind (lead <= -20% of the limit) 0.9 with 180 s or less left, all_in (behind, last 60 s) 0.9; seconds, not time_frac; -0.20, not -0.30 |
| P-05 margin <= -0.15, time_frac < 0.50: AGGRESSIVE | partial | match.posture behind (<= -10%) 0.6, far_behind 0.7, at any time |
| P-06 margin >= +0.30, time_frac < 0.40: CONSERVATIVE | partial | match.posture far_ahead (>= 20%) 0.3 at any time; hide_and_hold 0.15 ahead in the last 60 s |
| P-07 margin >= +0.15: BALANCED, map control | partial | match.posture ahead (>= 10%) 0.4 |
| P-08 enemy closing in < 2 min, behind: AGGRESSIVE | partial | **conflict**: enemy_near_win (enemy within the limit's near-win window) is careful 0.2 by the player's rule; the leader's 3-minute pace (director.update score_hist) only feeds match.tempo |
| P-09 closing in < 2 min, ahead: CONSERVATIVE | partial | match.posture we_near_win 0.35 by points, not pace; match.tempo close_out when our pace falls short |
| P-10 default BALANCED | done | match.posture even 0.5 |
| 0.2 posture effect: engagement range | partial | Bot.decide: at posture <= 0.3 outnumbered fights past 8 u are avoided; the cracked threshold follows posture; no range preference |
| 0.2 posture effect: push rate | partial | director.slayer_slots hold (<= 0.35) / push (>= 0.65); Bot.decide hunt desire x (0.4 + 1.2 posture); no objective mode's slots read the value (CTF reads the lead) |
| 0.2 posture effect: grenade use | open | OBJ_NADE, NADE_RATE and the opener (Bot.think, Bot.fight) ignore posture |
| 0.2 posture effect: vehicle use | open | director.crew_orders and Bot.decide vehicle trips ignore posture |
| 0.2 posture effect: respawn behaviour | open | no spawn wait or regroup |
| 0.2 posture effect: power weapon priority | partial | only the overshield's pull moves with posture (Bot.best_item) |
| PW-01 power weapon timers, one bot there 10 s early | partial | team timers from a seen pickup (live_bots.item_check, director.item_taken); a bot goes when the item is up by its arrival, off by map_iq (Bot.best_item); nobody sent early but the coach's Slayer play rotate_power_weapon (slayer_slots) |
| PW-02 power weapon holder never carries | open | assign_roles' cost: distance, role inertia, personality, coach role; never the gun held |
| PW-03 lost power weapon: broadcast, nearest retrieves | partial | a better gun lying near is taken by whoever sees it (Bot.upgrade_point); no callout, no order |
| PW-04 CONSERVATIVE denies weapons | open | |
| PU-01 overshield to the next contester | partial | Bot.best_item: +0.3 x (posture - 0.5) for any bot; carriers never take items (Bot.decide) |
| PU-02 camo to the stealth role | partial | Bot.best_item: +0.25 for flanker and sniper personalities, not by role |
| PU-03 custom powerup by its traits | **blocked** | the variant's custom powerup traits are not read |
| SP-01 spawn-flip kills weighted 0.5 | open | no spawn influence zones |
| SP-02 on spawn, move by role | partial | orders survive death, re-handed every 2 s (assign_roles); escorts to the carrier (Bot.live_point), defenders to posts; slayers do not join the nearest teammate |
| VC-01 vehicle role at spawn by mode | partial | crew_orders by role with the mode's first (vehicles.ROLE_FIRST: CTF / Assault transport, King / Territories anti-vehicle), else anti-air first always, not keyed to enemy aircraft |
| VC-02 enemy vehicle raises its counter | partial | no counter-vehicle pick; the Grenadier fetches an anti-vehicle gun when an enemy vehicle is about (Bot.vehicle_mission) |
| VC-03 CONSERVATIVE vehicles home, DESPERATE all at the objective | open | |
| 0.3 callouts | partial | carrier seen ("Carrier <zone>!", Bot.think flag_carrier), flag taken / dropped / returned / captured (live_bots.flag_events), seen / one shot / dead (director.text); Easy calls nothing (director.report); no power weapon holder, vehicle spawn, hill move, territory flip or lives calls |

## Part 1. Slayer family

| Rule | Status | Where / what is missing |
|---|---|---|
| SLAY-CORE-01 opening split | partial | slayer_slots standard: anchor on a power position, slayer plus support to the fight, floaters; no rotator to the power weapon; the anchor's post is a random power position, not the high ground by our spawn |
| SLAY-CORE-02 anchor never leaves without a replacement | open | the post is re-drawn every 25-45 s (slayer_slots s.post); the "mid" role has no keep_role leash |
| SLAY-CORE-03 hold power points; weights 1.5 / 0.6 | partial | hold layout at posture <= 0.35 (pairs on two adjacent power positions); no position-based weights in Bot.threat |
| SLAY-CORE-04 rotator takes power weapons on timers | partial | as PW-01; no rotator role |
| SLAY-CORE-05 a slayer dies: the other falls back | partial | a lone bot hunts less (Bot.decide cautious); no fall-back on a teammate's death |
| SLAY-CORE-06 shields down: break line of sight | done | Bot.decide: cracked and losing, cover within reach, held 7 s (recharge_until); off when shieldless |
| SLAY-CORE-07 numbers advantage: AGGRESSIVE 15 s | partial | Director.update counts who is alive (the kill feed): two up raises the posture value to at least 0.7 (slayer_slots' push: two pairs from two sides), two down lowers it to at most 0.3 (the hold), never over enemy_near_win, hide_and_hold or all_in (match.posture, test_ctf_roles); off in Firefight, Infection, Juggernaut. It lasts while the count does (their respawn ends it), not a fixed 15 s; the push goes to the fight, not their spawn side |
| SLAY-CORE-08 enemy closing: all three push one lane | open | **conflict**: enemy_near_win holds pairs (slayer_slots) and fights only two on one (Bot.decide avoid), the player's rule |
| SLAY-CORE-09 behind, they hold the power position: grenades, push as three | partial | push layout at posture >= 0.65: two pairs from two sides (slayer_slots); no regroup or grenade volley first |
| SLAY-CORE-10 bait their power weapon holder | open | (Bot.decide only breaks line of sight from a power weapon in its band when alone, Heroic and up) |
| SLAY-CORE-11 ahead, time low: hold, deny, never cross | partial | hide_and_hold / far_ahead give the hold layout; no weapon denial, no "never cross the middle" |
| SLAY-CORE-12 ahead, they force fights: let them come | partial | hold layout plus Bot.decide avoid; no grenades on their approach, no step-back |
| SLAY-BTB-01 vehicle roles first; their tank up: two anti-vehicle | partial | crew_orders sends bots with no objective job up to 45 u to empty vehicles by role; no tank-triggered pair |
| SLAY-BTB-02 vehicles farm away from their power weapon spawns | open | |
| SLAY-BTB-03 behind, time low: every vehicle at their spawn | open | |
| SLAY-SWAT-01 head height, lead at range | partial | Bot.aim_head: shieldless targets get head aim from the first shot at the tier's rate (HEAD_AIM 0.2-0.97); lead in Aim.step; SWAT known only as snap.shieldless |
| SLAY-SWAT-02 never enter an un-pre-aimed sightline | partial | pre-aim where a man would appear (Bot.man_appears, route_lead), every mode; no rule against stepping into an unchecked lane |
| SLAY-SWAT-03 no melee duels | open | Bot.fight's melee rules ignore shieldless |
| SLAY-SWAT-04 pairs, one lane each | partial | slayer_slots slayer plus support; floaters alone |
| SLAY-SWAT-05 reload below 3 rounds or out of sight | partial | Bot.reload_check: never with a man in view, at 40% of the magazine |
| SLAY-SWAT-06 jump discipline by game | open | HOP_RATE, STRAFE_JUMP, JUMP_SHOT are the same in every game |
| SLAY-SWAT-07 relocate after 2 kills | open | |
| SLAY-SWAT-08 behind him inside 3 m: melee | open | no melee-from-behind choice |
| SLAY-SWAT-09 behind, time low: chain-peek | open | |
| SLAY-SWAT-10 ahead, time low: two crossfires | open | |
| SLAY-SWAT-11 SWAT Magnums: range -30% | open | no variant detection (names readable in Reach and Halo 2: LiveReach.variant_name, LiveH2.variant; unused) |
| SLAY-SWAT-12 ShWATguns | open | as SLAY-SWAT-11 |
| SLAY-SWAT-13 SWAT objective variants | partial | the mode's brain loads and the shieldless rules apply (Bot.decide cracked by health); no corner-check escort |
| SLAY-SNIPE-01 spread to the long lanes | open | Snipers not detected |
| SLAY-SNIPE-02 no-scope inside 10 m, flank check | partial | Bot.zoom_level zooms by band; no 15 m flank check |
| SLAY-SNIPE-03 relocate after a kill | open | |
| SLAY-SNIPE-04 behind: push interiors | open | |
| SLAY-SNIPE-05 ahead: hold the long lanes | open | |
| SLAY-ROCK-01 never inside 8 m, high ground | partial | Bot.fight: no explosive inside its own blast (BLAST rockets 2 u) or onto a teammate; no high ground, no jump when rocketed |
| SLAY-SWORD-01 lunge range, corners | partial | Bot.fight: sword / hammer only in reach (LUNGE), rush by the nav; no corner holding |
| SLAY-FIESTA-01 classify the loadout per spawn | partial | Bot.choose_weapon / loadout_value rate what it holds; no per-life range band or support role |
| SLAY-PHANT-01 Phantoms: hold still | open | camo only perceived (Perception.update misses it past 4 u) |
| SLAY-ENDUR-01 Endurance: fight on health | open | not detected (CE variant names not read) |
| SLAY-ELIM-01 start CONSERVATIVE | **blocked** | lives per round and rounds not read in any game |
| SLAY-ELIM-02 formation, leapfrog | **blocked** | as SLAY-ELIM-01 |
| SLAY-ELIM-03 every engagement 2-on-1 | **blocked** | as SLAY-ELIM-01 (Bot.decide avoid does it only at posture <= 0.3) |
| SLAY-ELIM-04 grenades as openers | partial | the opener exists in every mode (Bot.fight nade_open); Elimination not detected |
| SLAY-ELIM-05 numbers decide position | **blocked** | as SLAY-ELIM-01 |
| SLAY-ELIM-06 last bot alive stalls | **blocked** | as SLAY-ELIM-01 |
| SLAY-ELIM-07 power weapons first, as a group | **blocked** | as SLAY-ELIM-01 |
| SLAY-ELIM-08 Phantom Elimination | **blocked** | as SLAY-ELIM-01 |
| SLAY-REG-01 Regicide bounty weights | **blocked** | Halo 4: no engine or king read (LiveH4F.engine returns 2) |
| SLAY-REG-02 as King: corner, overshield | **blocked** | as SLAY-REG-01 |
| SLAY-REG-03 Infinity loadouts per role, ordnance | partial | loadouts by how lives end (loadouts.want_slot, live_bots.loadout_check), not by role; ordnance **blocked** (no input decoded) |

## Part 2. King of the Hill

| Rule | Status | Where / what is missing |
|---|---|---|
| 2.2 roles SCORER / RING / ROAMER / VEHICLE | partial | role_slots king: one "defender" on the hill, "mid" on overlooks; no ROAMER; vehicles via crew_orders (anti-vehicle first) |
| KOTH-STATIC-01 only the scorer enters | partial | default one inside, the rest on overlooks (role_slots, director.overlooks); the coach's contest_hill (everyone) only while the team knows a man of theirs in the hill (Director.play_ok, and role_slots drops a running one once it is taken back); cover_hill (two) has no precondition; overlooks start 4 u out with no hill-radius check and pad with the hill centre; Easy all run at it (straight_objective, as tier 2.2) |
| KOTH-STATIC-02 scorer on the far edge, crouched, eyes on the approach | partial | stays in the hill: keep_role's leash is the hill radius, guns and hunts outside it a quarter (test_ctf_roles); loiters within 0.6 of the hill radius (Bot.think on_hill), looks along open sightlines (Bot.post_view); a close fight still pulls it out; no edge, crouch or cover |
| KOTH-STATIC-03 ring holds fire into its own scorer's hill | partial | grenades and splash hold off teammates (Bot.fight mates_near; OBJ_NADE needs none within 3 u); no hill rule |
| KOTH-STATIC-04 enemy enters: grenades in, push, scorer back | open | no contested-hill branch; OBJ_NADE is a chance grenade on the way in |
| KOTH-STATIC-05 scorer dies: next one in | done | the hill slot is first and re-handed every 2 s to the cheapest living bot (assign_roles) |
| KOTH-STATIC-06 snipe their scorer first | partial | overlook spots see the hill (overlooks: LOS), so whoever stands there shoots; no precision-weapon pick, no "before anyone pushes" |
| KOTH-STATIC-07 contest beats clear | partial | one bot always walks on (role_slots); a man in view outranks the order (Bot.decide 1.5+ against 0.5-1.2); no run-in-to-die when all_in |
| KOTH-STATIC-08 vehicles take the hill | partial | vehicle guns weight a man in the hill 1.5 (Bot.vehicle_pick); no drive-through or shelling plan |
| KOTH-STATIC-09 grenade the hill before every push | partial | OBJ_NADE: 0.85/s x grenades trait at a man at the objective; not every push, not three |
| KOTH-STATIC-10 never push one at a time | partial | with a man of theirs in the hill (its beliefs, 4 s) a bot posted on it waits outside for a teammate within 12 u, then for the hill to clear or two of theirs dead, 8 s at most (Bot.stage from keep_role, test_ctf_roles); minimum two, not three, and no sniper on the fourth |
| KOTH-STATIC-11 ahead, time low: hold the edge, CONSERVATIVE | partial | posture <= 0.3 avoids uneven fights (Bot.decide); the King layout and item trips do not change |
| KOTH-STATIC-12 behind, time low: everyone on the ring | partial | only if the coach picks contest_hill; no deterministic branch |
| KOTH-STATIC-13 uncontested variants: contest = clear | **blocked** | the uncontested / Team King setting is not read (the scorer goes in either way) |
| KOTH-STATIC-14 Mosh Pit: fight from inside | **blocked** | hill traits not read |
| KOTH-STATIC-15 Kill from the Hill: two scorers | **blocked** | H2A: no hill or engine read (LiveH4F) |
| KOTH-MOVING-01 learn the hill order | open | no hill history; the new hill is used once read (role_slots every 2 s) |
| KOTH-MOVING-02 roamer to the next hill at T-10 s | **blocked** | the move timer is not read (CE KING globals, LiveH3.king_hill, REACH_HILL give the hill only); the interval could be measured from moves |
| KOTH-MOVING-03 no push on a hill about to move | **blocked** | as KOTH-MOVING-02 |
| KOTH-MOVING-04 Ghost first to every hill | open | |
| KOTH-MOVING-05 ahead: rotate early | **blocked** | as KOTH-MOVING-02 |
| KOTH-MOVING-06 behind: set up on the next hill | **blocked** | as KOTH-MOVING-02 |
| KOTH-VEH-01 vehicle hill: scorer drives | open | not detected: the REACH_HILL marker's parent (object +0x14) is not checked |
| KOTH-VEH-02 enemy vehicle hill: EMP, board | open | as KOTH-VEH-01 |

## Part 3. Oddball

| Rule | Status | Where / what is missing |
|---|---|---|
| 3.2 roles CARRIER / BODYGUARD (5 m) / RING | partial | ours: two escorts 3 u behind the carrier (Bot.live_point, ESCORT_R 12 u) plus overlooks of him (role_slots) |
| ODD-CORE-01 scored hold spots, top three | partial | carry_point: the team hold (or mid) farthest from every enemy's true position, re-picked every 2 s; no approach, cover, height or escape scoring |
| ODD-CORE-02 never a hallway | open | holds are the map's holds, unchecked |
| ODD-CORE-03 carrier dies: re-take only with cover in 3 s | open | a loose ball gets two runners and every other bot straight at it (role_slots) |
| ODD-CORE-04 attacked alone: drop, fight, re-take | open | no drop |
| ODD-CORE-05 carrier vehicle use | partial | honked passenger seats go to objective holders first, give_seat (honk_orders); no ferry in Oddball (vehicle_orders: CTF, Assault, Stockpile) |
| ODD-CORE-06 carrier melees a lone attacker | partial | carrier melee at 1.3 u (Bot.think "carrier melee"); no step-in |
| ODD-CORE-07 converge on the carrier's approach | partial | the game marks him; every hunter goes to his position (role_slots), not the door |
| ODD-CORE-08 bodyguard first: 1.8 / ring 1.2 / carrier 1.5 | open | Bot.threat +40 on the carrier, nothing for his guards |
| ODD-CORE-09 grenades into the hold spot | partial | OBJ_NADE chance grenade |
| ODD-CORE-10 vehicles hunt the carrier, weight 2.0 | done | vehicle guns weight the carrier 2.0 (Bot.vehicle_pick), ram rules (Bot.ram_ok) |
| ODD-CORE-11 ahead, time low: hold one spot | open | oddball slots ignore posture (only the coach's reset_and_recharge) |
| ODD-CORE-12 behind, time low: all four on the spot | open | as ODD-CORE-11 |
| ODD-CORE-13 Ninjaball loop | **blocked** | carrier traits not read; Halo 3 names not read |
| ODD-CORE-14 Lowball | **blocked** | not told apart (Halo 3 engine 3 for every ball game) |
| ODD-CORE-15 Hot Potato | open | readable from Reach's variant name, not detected; fuse not read |

## Part 4. Capture the Flag

| Rule | Status | Where / what is missing |
|---|---|---|
| 4.2 roles RUNNER / ESCORT / DEFENDER / HUNTER (+ vehicles) | partial | runner, escort, defender, hunter, mid push (role_slots); driver / gunner by crew_orders and vehicle_orders; no AIR or tank ANCHOR |
| CTF-MULTI-01 stance by posture | partial | defenders by team size (1 up to 4 of us, 2 up to 7, 3) and lead (+1 / +2), never 0 (max(1, ...)) even all_in; 1 runner (2 with 5+ free), 2 escorts, the rest push 45% from their base; the posture value is unused |
| CTF-MULTI-02 power weapons before the push | open | |
| CTF-MULTI-03 escort hog drops the runner at 25 m, circles | partial | transport first (ROLE_FIRST), "hop on the gun", ferry home (vehicle_orders); no outbound drop-off |
| CTF-MULTI-04 outskirts route, two return routes | partial | the way in by lane or sneak route by skill and threat (pick_route); the way home is the nav's shortest path |
| CTF-MULTI-05 runner never fights; alone: drop, fight, re-grab | partial | carriers never fight (Bot.decide: no fight scores, objective 3.0) and melee at arm's length (Bot.think); no drop-and-fight; Halo 4 flagnum **blocked** (no H4 flags) |
| CTF-MULTI-06 flag juggling | open | |
| CTF-MULTI-07 vehicle return as passenger | partial | ferry: a bot driver with a free seat within 45 u collects our carrier 30+ u from home, the carrier boards a passenger seat (vehicle_orders, honk_orders give_seat); rear gunner and Mongoose-lane rule not coded |
| CTF-MULTI-08 flag at home: hold theirs near our base | done | home_rule (CE / Reach default, off once we score with ours out): carry_point waits on the base post farthest from our flag; standoff: everyone but one escort hunts (role_slots) |
| CTF-MULTI-09 dropped flag: 15 s return, bait | partial | a dropped enemy flag gets the runner slot (role_slots theirs.pos); no return clock, no bait |
| CTF-MULTI-10 flag taken: everyone hunts; 2.0 / 1.5 | partial | "Flag pulled!" (flag_events); 2 hunters (3 with return_flag, n-1 when their flag is home, in a standoff, or with collapse_on_carrier); carrier +40 (Bot.threat), no escort weight |
| CTF-MULTI-11 intercept, do not chase | open | hunters go where our flag is now (Bot.live_point: f.pos); no route prediction |
| CTF-MULTI-12 vehicle intercept | partial | vehicle guns weight the carrier 2.0 (Bot.vehicle_pick), rams; not "aim at the vehicle" |
| CTF-MULTI-13 one touches, the rest cover | partial | hunters stand on our dropped flag (Bot.live_point, keep_role HUNT_R); all of them, no split |
| CTF-MULTI-14 both flags out: compare positions | partial | standoff always hunts first (role_slots); no position comparison |
| CTF-MULTI-15 ahead 2-0, time low: defend, park a vehicle | partial | two up: defenders n-1, nobody pulls unless the coach's pull_flag (role_slots lead >= 2); no parked vehicle |
| CTF-MULTI-16 behind, time low: 0 defenders, last-20-s touch | partial | the runner goes with 30 s left (Bot.stage); defenders never 0; sudden death not read |
| CTF-MULTI-17 their tank up: anti-vehicle first, runner waits | open | (the Grenadier's vehicle_mission is personal) |
| CTF-MULTI-18 their Banshee up: runner on foot | open | |
| CTF-MULTI-19 Tank Flag | **blocked** | carrier traits not read |
| CTF-MULTI-20 Attrition Flag | **blocked** | lives not read |
| CTF-MULTI-21 CE CTF overlays | partial | CE flags by tag (Live.flags), CE home_rule on; the CE-CTF-01..05 Blood Gulch tactics not coded |
| CTF-ONE-01 attacking: no defender | done | no flag of ours this round: no defender slots; runner, two escorts, the rest push (role_slots, is_one_flag) |
| CTF-ONE-02 timing: touch the flag by T-15 s | partial | round clock read; Bot.stage goes with 30 s left; one_flag_posture all_in the last minute; sudden death not read |
| CTF-ONE-03 escorts clear, runner on "clear" | partial | the runner waits for company and a clear base (Bot.stage), the even-id escort clears 9 u ahead (Bot.live_point); no exit hold |
| CTF-ONE-04 back door, decoy at the front | open | |
| CTF-ONE-05 Warthog draws fire, tank shells the door | open | |
| CTF-ONE-06 losing: keep the flag out, hide the carrier | open | a carrier always runs to the capture point |
| CTF-ONE-07 defence 2 / 1 / roamer | partial | defenders n - min(2, n // 2) on cover posts 3-11 u round the flag (defend_posts, post_loiter), the rest push; no door / roamer split |
| CTF-ONE-08 kill box, defenders never chase | partial | defenders' guns and hunts kept within 10 u of their post (keep_role firm); no door grenades |
| CTF-ONE-09 carrier out: intercept the exit | partial | n-1 hunters collapse (role_slots collapse); a chase |
| CTF-ONE-10 round-score logic | partial | side-based posture (match.one_flag_posture: defending 0.2, attacking 0.6 / 0.9); the other round's result is not read |
| CTF-NEUT-01 mid fight first, runner hangs back | **blocked** | a neutral flag is never read: flags are found only on the two team stands (live_bots.snapshot MAP["flags"], flags_by_stand), so Neutral Flag plays as Slayer |
| CTF-NEUT-02 escort pre-holds the home route | **blocked** | as CTF-NEUT-01 |
| CTF-NEUT-03 intercept toward their base, no defender | **blocked** | as CTF-NEUT-01 |
| CTF-NEUT-04 dropped mid flag as bait | **blocked** | as CTF-NEUT-01 |
| CTF-VEH-01 runner drives | **blocked** | H4 / H2A flags not read (LiveH4F.flags returns []) |
| CTF-VEH-02 approach and leave at speed | **blocked** | as CTF-VEH-01 |
| CTF-VEH-03 defender vehicle blocks the lane | **blocked** | as CTF-VEH-01 |

## Part 5. Assault, Grifball, Ricochet

| Rule | Status | Where / what is missing |
|---|---|---|
| 5.2 roles CARRIER / ARMER / ESCORT / DEFENDER / DISARMER | partial | carrier runs (assign_roles; has_flag from modes.Watch), 2 escorts, 2 defenders at our goal (mode_slots); no armer or disarmer |
| ASS-MULTI-01 siege: grenades, vehicles, then the carrier | open | carrier plus escorts walk in; OBJ_NADE is a chance grenade |
| ASS-MULTI-02 Halo 2 sticky arming, armer | **blocked** | Halo 2 Assault not read (mode watch is Reach / Halo 3 only; "Assault bomb spawn" flags unmapped in modes.layout) |
| ASS-MULTI-03 Halo 3 instant arm: guard the fuse | partial | modes.Watch marks a bomb with no carrier in the other team's goal, off its own stand, as armed (as invasion's inv_armed); our armed bomb gets one on it and the rest at the cover round it (mode_slots), and nobody presses Use on it (loose_point) (test_modes); the fuse is not read (the 15 s is not timed), no melee or grenade rule on the bomb; a carrier killed on the goal before it arms reads as armed (ponytail: the game's own armed state, once read) |
| ASS-MULTI-04 Reach 5 s arm: escorts clear the circle first | partial | the carrier walks to the enemy goal and stays (carry_point, modes.carry_goal); escorts trail 3 u (Bot.live_point), not in first |
| ASS-MULTI-05 passenger only; tank top | partial | carriers get honked passenger seats first, ferry runs in Assault (vehicle_orders); no tank-top ride |
| ASS-MULTI-06 attacked alone: drop, fight, re-grab | open | |
| ASS-MULTI-07 camo and overshield on the carrier | open | carriers never take items (Bot.decide) |
| ASS-MULTI-08 defender within 10 m; bomb up: two disarmers | partial | two defenders within 3 u of our goal (mode_slots); a carried enemy bomb gets two hunters; no callout |
| ASS-MULTI-09 enemy plants: everyone disarms | partial | Invasion Breakpoint (invasion_slots: every defender on the armed bomb); Assault: their armed bomb on our goal (modes.Watch) sends all but one of us onto it as runners (mode_slots) and Use on it disarms (loose_point / on_loose_objective, the Breakpoint rule) (test_modes); the carrier standing on it is not singled out (a man in view is fought as any) |
| ASS-MULTI-10 vehicle defence of the site | open | |
| ASS-MULTI-11 ahead, time low: 2 defenders, no carrier | open | mode_slots ignore posture |
| ASS-MULTI-12 behind, time low: no defenders | open | as ASS-MULTI-11 |
| ASS-MULTI-13 their tank: EMP, board, use it as a shield | open | |
| ASS-ONE-01 attacking: no defender | open | attackers still post two defenders at their own goal (mode_slots) |
| ASS-ONE-02 plant early; keep the bomb from resetting | open | |
| ASS-ONE-03 defending: 3 on the site, 1 roamer | partial | 2 at the goal plus 2 hunters on the carrier (mode_slots) |
| ASS-ONE-04 round-score logic | **blocked** | rounds not read |
| ASS-NEUT-01 mid fight first; a defender role | partial | the neutral bomb gets two runners and an escort, two defend our goal (mode_slots); no mid fight first |
| ASS-NEUT-02 carrying team AGGRESSIVE, defender to mid | open | |
| GRIF-01 diamond formation | open | Grifball not detected (no GRIFBALL in modes.NAMES; Halo 3's engine 7 plays it as Assault) |
| GRIF-02 hammer timing, sword after a swing | open | Bot.fight swings / lunges only in reach (LUNGE); no prediction |
| GRIF-03 4 m spacing | open | |
| GRIF-04 hammer the carrier from the side | partial | carrier +40 (Bot.threat); no side approach |
| GRIF-05 behind: carrier runs, three body-block | open | |
| RICO-01 carry beats throw | **blocked** | Ricochet is H2A / Halo 4: no engine or ball read (LiveH4F) |
| RICO-02 throw high and short | **blocked** | as RICO-01 |
| RICO-03 pass under pressure | **blocked** | as RICO-01 |
| RICO-04 goalkeeper | **blocked** | as RICO-01 |
| RICO-05 behind: throw from range | **blocked** | as RICO-01 |

## Part 6. Territories, Dominion, Extraction

| Rule | Status | Where / what is missing |
|---|---|---|
| 6.2 roles CAPPER / GUARD / ROTATOR / VEHICLE | partial | two "defender" takers inside the target, an escort on it, holders for up to n - 3 owned zones, overlooks (mode_slots) |
| 6.x zones and ownership (prerequisite) | partial | Reach: terr_object zones (modes.layout); Halo 3's "territory_static" flags (240 on the h3 exports) are not mapped, so Halo 3 Territories has no zones and everyone goes to the map's mid; ownership is a guess, held alone for the game's capture time (modes.CAPTURE_S: Halo 2 10 s, Halo 3 and Reach 30 s; Reach's when the caller names no game, as tools/live_bots.py) |
| TERR-SYM-01 majority set: two or three near us | partial | one target at a time: the zone not ours with the fewest enemies near (true positions), then nearest (mode_slots) |
| TERR-SYM-02 capper crouched inside, guard outside | partial | two inside (spread within 0.6 r, keep_role zone radius, zone_shuffle) plus an escort on the centre, kept on the zone until the game's capture time is up (Reach 30 s, was 10 s: they left a third of the way in;, test_modes); a sighting near the target can still turn the plan to another zone; no crouch, the guard is not outside |
| TERR-SYM-03 never leave the majority undefended | partial | a holder each for at most n - 3 owned zones (mode_slots ours[:n-3]); none with 3 or fewer of us |
| TERR-SYM-04 ours contested: nearest guard and rotator converge | open | |
| TERR-SYM-05 Flag Rally | partial | not detected; the default takes the least-defended zone and leaves holders |
| TERR-SYM-06 vehicles per territory | partial | anti-vehicle role first (ROLE_FIRST); no parking |
| TERR-SYM-07 ahead, time low: hold the majority | open | mode_slots ignore posture |
| TERR-SYM-08 behind: flip the weakest, send three | partial | the default already sends three to the zone with the fewest enemies within 12 u (true positions), not as a time-low branch |
| TERR-LOCK-01 everyone to a different territory | open | everyone goes to one target |
| TERR-LOCK-02 contested 10 s: move on | open | |
| TERR-LOCK-03 majority locked: run out the round | **blocked** | locks and per-round scoring not read |
| TERR-ASYM-01 one guard per territory on its approach | **blocked** | which side defends is not read (both sides attack: mode_slots) |
| TERR-ASYM-02 a guard never leaves its territory | **blocked** | as TERR-ASYM-01; lock state not read |
| TERR-ASYM-03 vehicles on the far territories | **blocked** | as TERR-ASYM-01 |
| TERR-ASYM-04 round-score logic | **blocked** | rounds not read |
| TERR-ASYM-05 attack in sequence with all four | partial | one target at a time (mode_slots); holders peel off as zones flip |
| TERR-ASYM-06 Warthog delivers two cappers; tank shells | open | |
| TERR-ASYM-07 time low: go where a guard just died | open | |
| DOM-01 hold two of three | **blocked** | Halo 4: no engine, base the player or resupply read (LiveH4F); the bases are exported (maps/h4_* dominion, dom_base) |
| DOM-02 resupply is the score | **blocked** | as DOM-01 |
| DOM-03 fortify when safe | **blocked** | as DOM-01 |
| DOM-04 vehicle role at the base 5 s before the cycle | **blocked** | as DOM-01 |
| DOM-05 third base only when they are down players | **blocked** | as DOM-01 |
| DOM-06 Last Stand against us: scatter | **blocked** | as DOM-01 |
| DOM-07 ahead: hold two, fortify | **blocked** | as DOM-01 |
| DOM-08 behind: take their weakest after their resupply | **blocked** | as DOM-01 |
| EXTR-01 arm, two on the beacon | **blocked** | Halo 4: no beacon state read; sites exported (ext_site) |
| EXTR-02 convert, do not kill | **blocked** | as EXTR-01 |
| EXTR-03 roamer to the next site | **blocked** | as EXTR-01 |
| EXTR-04 ahead: defend the current beacon | **blocked** | as EXTR-01 |
| EXTR-05 behind: contest every beacon | **blocked** | as EXTR-01 |

## Part 7. Juggernaut, VIP, Infection, Headhunter, Stockpile

| Rule | Status | Where / what is missing |
|---|---|---|
| JUG-01 hunters converge from different sides | partial | Halo 3: everyone else becomes one side against the marked man (modes.mark_special: overshield), so all fight only him; free for all gives each bot its own director (live_bots key), no shared plan; Reach never marks him (shield read is 1 - damage) |
| JUG-02 range beats melee | open | fight ranges are the bot's own gun's (WEAPON_RANGE); nothing keeps hunters out of hammer reach |
| JUG-03 decide whether to want the mark | open | |
| JUG-04 hold fire through his safe time | open | Halo 3's mark start is known (mark_special); no hold |
| JUG-05 Phantom Fodder: still hunters | **blocked** | variant not read |
| JUG-06 as Juggernaut: chokepoints | open | the Juggernaut's director plays Slayer |
| JUG-07 hammer prediction, free spray | open | |
| JUG-08 Mad Dash: zone to zone | open | Reach exports "juggernaut" goal flags; Halo 3 has none (**blocked** there) |
| JUG-09 Ninjanaut | **blocked** | variant not read |
| JUG-10 overshield management | **blocked** | Reach overshield not read over 1 (LiveReach._vitals) |
| VIP-01 VIP never leads; formation | partial | our VIP has its own play ("free", assign_roles), avoids fights past 8 u (Bot.decide), two escorts trail it (role_slots vip); it still hunts and leads |
| VIP-02 enemy VIP 3.0 | partial | +40 (Bot.threat) and one hunter (role_slots vip) |
| VIP-03 Escort goal areas | **blocked** | VIP variants not told apart (Halo 3 names not read; no goal flags exported) |
| VIP-04 Influential VIP blob | **blocked** | as VIP-03 |
| VIP-05 One Sided VIP | **blocked** | as VIP-03 |
| INF-SURV-01 group and hold one spot | partial | survivors hold the nearest haven 2.5 u apart (mode_slots infection); Halo 3 has no havens: the map's mid; no single-approach scoring |
| INF-SURV-02 ammo is the clock | open | |
| INF-SURV-03 fire discipline, staggered reloads | open | |
| INF-SURV-04 headshots on Reach zombies | partial | shieldless targets get head aim at the tier's rate (Bot.aim_head); Halo 4 Flood **blocked** |
| INF-SURV-05 never Armor Lock | open | no Infection rule in brain/equipment.py |
| INF-SURV-06 bait with 4+ alive | open | |
| INF-SURV-07 moving havens | **blocked** | the active haven is not read (every inf_haven zone is used) |
| INF-SURV-08 last man runs loops | open | survivors are countable (snap teams), not coded |
| INF-SURV-09 Save One Bullet | **blocked** | variant not read |
| INF-SURV-10 time low: hold | open | |
| INF-ZOMB-01 pack rush from two sides | open | each infected hunts one survivor (mode_slots); free for all: one director per bot |
| INF-ZOMB-02 no jumping | open | zombies hop like everyone (HOP_RATE) |
| INF-ZOMB-03 rush the reloader | open | |
| INF-ZOMB-04 alphas lead | **blocked** | alphas not told apart |
| INF-ZOMB-05 Flood frontal rush | **blocked** | Halo 4 |
| INF-ZOMB-06 Hide and Seek sweep | **blocked** | variant not read |
| HH-01 three skulls: go bank | partial | a third of the team goes to the nearest drop point whatever it carries (mode_slots headhunter); skull counts and the active point not read; the skull pickups there read snap.obj_items, which modes.Watch fills only in Assault / Stockpile |
| HH-02 target weight 1 + 0.3 per skull | **blocked** | skull counts not read |
| HH-03 drop point timing | **blocked** | the active drop point and its timer not read |
| HH-04 instant win: escort or sprint | **blocked** | as HH-02 |
| HH-05 vehicles for skull carriers | **blocked** | as HH-02 |
| STOCK-01 the collection tick | open | not read or timed (the score steps could time it) |
| STOCK-02 raids at T-15 s | partial | flags in their pile count as loose (mode_slots skips only ours), so raids happen when nearest; not timed |
| STOCK-03 2 runners, guard, raider | partial | a runner and an escort per loose flag (nearest two), two guard our pile, the rest cover mid (mode_slots); carriers run home (carry_goal) and are ferried (vehicle_orders) |
| STOCK-04 flag juggling | open | |
| STOCK-05 ahead: all guard through each tick | open | |
| STOCK-06 behind: every flag at once, two raiders | open | |

## Part 8. Invasion, Invasion Slayer, Generator Defense, Race

| Rule | Status | Where / what is missing |
|---|---|---|
| INV-ATK-01 fireteam spawns | **blocked** | spawning on a partner is not an input the bots send |
| INV-ATK-02 phase 1: four on one point, two decoy | partial | most of the team on one territory (fewer defenders, kept 30 s: INV_COMMIT), two inside, one to the other with 5+ (invasion_slots); no decoy swap |
| INV-ATK-03 vehicles the instant phase 2 opens | partial | vehicles taken by role when they appear (crew_orders), only by bots with no objective job; no phase-change rush |
| INV-ATK-04 core: passenger-only carry route, drop-and-fight | partial | two take the core, the carrier runs to the delivery point, escorts ahead and behind (invasion_slots, Bot.live_point); no ferry, and right so: the guide's passenger rule is wrong, the core is carried as a turret and its carrier cannot ride; no drop-and-fight |
| INV-ATK-05 T-60 s of a phase: DESPERATE | partial | the pile-on starts 60 s INTO a phase (PUSH_AFTER) or once one of us is inside; phase time left not used |
| INV-ATK-06 loadout per phase | partial | loadouts by how lives end (loadouts.want_slot), not by phase |
| INV-DEF-01 defend aggressively (7 s respawns) | open | |
| INV-DEF-02 phase 1: a fireteam per point | partial | cover posts round every territory (guard_spots, never on it: the player's review), hunters on anyone inside (invasion_slots) |
| INV-DEF-03 deny their vehicles at the phase change | open | |
| INV-DEF-04 core room kill box, intercept, stand on a dropped core | partial | core home: one on it, the rest on cover round it, one at the delivery point; carried: n-1 hunters on the carrier (keep_role pile-on) plus the delivery post; no route intercept |
| INV-DEF-05 time logic, bodies at the objective | open | |
| INV-SLAY-01 Invasion Slayer: unlocks as power spawns | partial | plays as Slayer (LiveReach.invasion excludes it); unlocks not tracked |
| GEN-DEF-01 stagger lockdowns | **blocked** | Generator Defense not detected; generator state not read |
| GEN-DEF-02 Elites push one generator | **blocked** | as GEN-DEF-01 |
| GEN-DEF-03 roamer takes the cache | **blocked** | as GEN-DEF-01 |
| GEN-DEF-04 Crashsite | **blocked** | as GEN-DEF-01 |
| RACE-01 checkpoints in order | open | CE's race engine (5) is read but played as Slayer (live_bots.snapshot); checkpoints exported (CE "race - track", Reach race_flag) |
| RACE-02 Rally: shortest tour | open | as RACE-01 (Reach rally_flag) |
| RACE-03 Rocket Race | open | not detected |
| RACE-04 Gungoose Gauntlet, Velocity | **blocked** | H2A |

## Part 9. Firefight

| Rule | Status | Where / what is missing |
|---|---|---|
| 9.2 roles ANCHOR / CLEANER / PP / HEAVY | partial | every bot escorts the nearest human (role_slots firefight) |
| FF-POS-01 pick a roofed high hold | open | |
| FF-POS-02 move between two holds | open | |
| FF-POS-03 resupply between waves | partial | dry or close to a better gun, a bot takes a loose one (Bot.rearm_point, upgrade_point); waves not read |
| FF-LIFE-01 posture by the lives pool | **blocked** | the pool is not read (LiveODST, LiveReach) |
| FF-LIFE-02 never spend a life for score | **blocked** | as FF-LIFE-01 |
| FF-LIFE-03 bonus rounds aggressive | **blocked** | rounds not read |
| FF-LIFE-04 delay respawn when overrun | **blocked** | as FF-LIFE-01; no respawn input |
| FF-WAVE-01 weights by enemy type | **blocked** | AI species and rank not read (ai_units: position, facing, vitals) |
| FF-WAVE-02 leave three harmless alive | **blocked** | wave state not read |
| FF-WAVE-03 clear the last wave | **blocked** | as FF-WAVE-02 |
| FF-WAVE-04 boss wave: nobody pushes | **blocked** | as FF-WAVE-02 |
| FF-WAVE-05 skull adaptation | **blocked** | skulls not read |
| FF-VEH-01 hijack the dropped Ghost / Choppers | partial | empty vehicles taken by role (crew_orders); no return to the hold on a Wraith drop |
| FF-VEH-02 Wraith: never in the open, EMP | partial | the Grenadier's vehicle_mission; no PP role or roof rule; AI-crewed vehicles read as empty (ai_units skips riders) |
| FF-VEH-03 Banshee: precision on the pilot, under the roof | open | |
| FF-VEH-04 Hornet farms, lands before boss waves | open | |
| FF-GRUNT-01 headshots; Ultras' helmet first | **blocked** | species not read; generic head aim on unshielded targets (Bot.aim_head) |
| FF-GRUNT-02 Fuel Rod Grunts first | **blocked** | as FF-GRUNT-01 |
| FF-GRUNT-03 kill the leader first | **blocked** | as FF-GRUNT-01 |
| FF-GRUNT-04 suicide Grunts at range | **blocked** | as FF-GRUNT-01 |
| FF-GRUNT-05 Birthday Party chain | **blocked** | as FF-GRUNT-01; skulls not read |
| FF-JACKAL-01 shield Jackal procedure | **blocked** | as FF-GRUNT-01 |
| FF-JACKAL-02 headshot when it aims elsewhere | **blocked** | as FF-GRUNT-01 |
| FF-JACKAL-03 overcharge the gauntlet | **blocked** | as FF-GRUNT-01 |
| FF-JACKAL-04 snipers first | **blocked** | as FF-GRUNT-01 |
| FF-JACKAL-05 Skirmishers, holograms | **blocked** | as FF-GRUNT-01 |
| FF-ELITE-01 noob combo pairing | **blocked** | as FF-GRUNT-01 |
| FF-ELITE-02 needle supercombine | **blocked** | as FF-GRUNT-01 |
| FF-ELITE-03 sword and camo Elites | **blocked** | as FF-GRUNT-01 |
| FF-ELITE-04 armor lock Elites | **blocked** | as FF-GRUNT-01 |
| FF-ELITE-05 Rangers in the air | **blocked** | as FF-GRUNT-01 |
| FF-BRUTE-01 shield, helmet, headshot | **blocked** | as FF-GRUNT-01 |
| FF-BRUTE-02 berserkers: back-pedal | **blocked** | as FF-GRUNT-01 |
| FF-BRUTE-03 Catch skull Brutes | **blocked** | as FF-GRUNT-01 |
| FF-BRUTE-04 hammer Chieftain | **blocked** | as FF-GRUNT-01 |
| FF-BRUTE-05 fuel rod Chieftain | **blocked** | as FF-GRUNT-01 |
| FF-BRUTE-06 jump-pack Brutes | **blocked** | as FF-GRUNT-01 |
| FF-HUNTER-01 orange flesh only | **blocked** | as FF-GRUNT-01 |
| FF-HUNTER-02 two-bot procedure | **blocked** | as FF-GRUNT-01 |
| FF-HUNTER-03 melee baiting | **blocked** | as FF-GRUNT-01 |
| FF-HUNTER-04 pair trick | **blocked** | as FF-GRUNT-01 |
| FF-HUNTER-05 never in the open with the pool low | **blocked** | as FF-GRUNT-01; pool not read |
| FF-HUNTER-06 bonus-round sniping | **blocked** | as FF-GRUNT-01 |
| FF-DRONE-01 automatic weapons on the swarm | **blocked** | as FF-GRUNT-01 |
| FF-DRONE-02 shoot them before they land | **blocked** | as FF-GRUNT-01 |
| FF-DRONE-03 backs to a wall | **blocked** | as FF-GRUNT-01 |
| FF-ENG-01 Engineer first | **blocked** | as FF-GRUNT-01 |
| FF-ENG-02 kill it over a squad | **blocked** | as FF-GRUNT-01 |
| FF-ENG-03 no ordnance on its shielded squad | **blocked** | as FF-GRUNT-01 |
| FF-VEHENEMY-01 Ghost: EMP and hijack | **blocked** | AI-crewed vehicles not told apart (ai_units skips riders) |
| FF-VEHENEMY-02 Wraith hatch only | **blocked** | as FF-VEHENEMY-01 |
| FF-VEHENEMY-03 Banshee pilot | **blocked** | as FF-VEHENEMY-01 |
| FF-VEHENEMY-04 Phantom chin gun, troops | **blocked** | as FF-VEHENEMY-01 |
| FF-VAR-01 Gruntpocalypse | **blocked** | Firefight variants not read |
| FF-VAR-02 Rocketfight / Sniperfight | **blocked** | as FF-VAR-01 |
| FF-VAR-03 PvE Generator Defense | **blocked** | as FF-VAR-01; generators not read |
| FF-VAR-04 Crashsite | **blocked** | as FF-VAR-01 |
| FF-VAR-05 Versus | **blocked** | as FF-VAR-01 |

## Patch: objective brain tiers (guide 18 Part 2.2) and coach hooks

| Rule | Status | Where / what is missing |
|---|---|---|
| 2.2 posture engine by tier | partial | Easy always 0.5 (director.update); Normal, Heroic and Legendary all get the full engine with time and pace (match.posture, match.tempo) |
| 2.2 roles by tier | partial | Easy: runner at the objective or free (assign_roles, straight_objective); every other tier every role, reassigned every 2 s |
| 2.2 power weapon timers by tier | partial | Easy only takes guns on its way (Bot.best_item map_iq < 0.15); the rest time items with an error by map_iq; no early arrival |
| 2.2 spawn control by tier | open | |
| 2.2 carrier memory 4 / 6 / 8 / 10 s | partial | enemy memory 4 / 6 / 8 / 10 s by tier (brain/profiles.py TIERS); no Legendary route prediction |
| 2.2 callouts by tier | partial | Easy none (director.report), speech timing by tier (callouts.TIMING); no predicted-spawn calls |
| 2.2 time-low branches by tier | partial | the posture's time rules are the same for every tier above Easy |
| 2.2 lives-limited behaviour | **blocked** | lives not read |
| 2.2 hill / territory discipline by tier | partial | Easy all on the hill (straight_objective); every other tier one scorer and a ring; Normal's two-in-the-hill and the Legendary vehicle anchor not coded |
| 2.2 setups and traps by tier | partial | slayer_slots layouts and the coach's plays, not by tier |
| 2.2 map knowledge by tier | done | routes by tier (pick_route: Easy straight in), items by map_iq, Easy knows no power spots (Bot.decide hold needs map_iq) |
| 2.2 coach availability by tier | partial | no commander for an all-Easy team, Easy takes no orders (coach_on, assign_roles); Normal gets plays like Heroic |
| TIER-MIX-03 team plan at its best living bot's tier | partial | the commander runs if any bot is above Easy (coach_on); the director's own logic has no tier |
| COACH-OBJ-posture one step | partial | tempo pushes the posture to >= 0.7 (pressure) or <= 0.25 (stall), +-0.15 for kills against safety, never over the hard states (coach_posture, HARD_STATES); a value shift, not one step |
| COACH-OBJ-roles within the role list | partial | coach roles bias the role cost (ROLE_FIT); V9 keeps the CTF returner and the Oddball guard (coach.validate, returner_ids); no one-scorer or disarmer floor |
| COACH-OBJ-play bundles of rule IDs | partial | plays for Slayer, CTF, King, Oddball (coach.PLAYS) as director layouts, not rule bundles; none for Invasion, Territories, Assault, Stockpile, Headhunter, Infection (COACH_UNKNOWN) |
| COACH-OBJ-tempo push rate only | partial | moves the posture value, which also changes fight acceptance (Bot.decide) |
| COACH-OBJ-lanes | open | orders name callout zones, no lane list |
| COACH-OBJ-target_weights | open | priorities only shift posture (coach_posture) |
| COACH-OBJ-callouts | partial | validated (coach.validate) but dropped (coach_apply never passes them on) |
| COACH-OBJ-timer_focus | partial | Slayer's rotate_power_weapon posts on the item due within 30 s (slayer_slots, next_item); no tier cap |

## Guide 18 Part 1: what the objective brain hands down

| Rule | Status | Where / what is missing |
|---|---|---|
| 1.2 posture | partial | Bot.posture 0-1 from director.update (Easy 0.5); read by Bot.decide (avoid, cracked threshold, hunts) and best_item; not the four-value enum |
| 1.2 role | partial | Order.role runner / escort / defender / hunter / mid / free (+ ride, board, drive, ferry, driver_wait, give_seat) picks the movement (Bot.think loiter, post_loiter, escort trail) and the leash (keep_role) |
| 1.2 goal {pos, stance} | partial | Order.point and via lanes; no stance (the slot's trait only picks who) |
| 1.2 target_weights | partial | no per-bot map; on foot Bot.threat +40 carrier / VIP, +60 x teamwork team shot; seats vehicles.target_score 2.0 / 1.5 / 1.3 (Bot.vehicle_pick) |
| 1.2 fire_discipline | partial | implicit only: carriers never fight, avoid at posture <= 0.3 (Bot.decide) |
| 1.2 grenade_budget | open | grenades paced by a cooldown and chance (grenade_ready_at, OBJ_NADE, NADE_RATE), no per-role budget |
| 1.2 vehicle_request | done | crew_orders hands a bot a vehicle by role (Order "drive"), Bot.decide walks and enters it, Bot.drive takes over |
| 1.2 equipment_hint | open | the equipment brain (Bot.kit) decides alone |
| 1.2 callouts_in | done | heard callouts become beliefs (director.update hear timing by tier, Perception.update) |
| INT-01 carrier rule | done | has_flag: no fights, no item trips, objective 3.0 (Bot.decide) |
| INT-02 survival override 4 s, not carriers, not DESPERATE | partial | cracked: cover (Bot.decide), carriers exempt; held 7 s; all_in only lowers the threshold to 0.05 |
| INT-03 vehicle handoff | done | seated: Bot.drive; role still applies (ferry, driver_wait, crew roles) |
| INT-04 equipment hard rules | partial | brain/equipment.py rules (kit.can_shoot); no Infection armor lock rule |
| INT-05 weights are multipliers | partial | on-foot weights are additive threat bonuses |
| INT-06 posture caps aggression, not skill | done | posture only changes which fights and where (Bot.decide); aim, reaction, strafe by tier |
| INT-07 coach only through the objective brain | done | coach.validate, then Director.coach_apply into plans, roles, orders |
| INT-08 tick rates | partial | bots and director per tick, roles every 2 s (spec 0.5 s), coach every 5-30 s |

## Top 15 gaps for live play

Ordered by what a player would notice in a real match.

1. **Halo 4 and H2A objective games play as Slayer.** Bots ignore flags, hills, balls, bases and beacons (DOM, EXTR,
   RICO, CTF-VEH, SLAY-REG, KOTH-STATIC-15). Change: live.LiveH4F.engine() and a variant_name() from the game globals as
   LiveReach reads them (offsets from a per-mode dump, as tools/reach_variant_dump.py did for Reach); LiveH4F.flags() /
   balls() through LiveH3's flags_by_stand path with this layout (objects +0x18, position +0x40, weapons +0x640, the
   ponytail note); king_hill() from the HUD waypoints as LiveH3. In live_bots run ModeWatch for "h4" / "h2a" and map
   H4's koth_hill, dominion / dom_base, ext_site, rico_endzone, grif_goal in modes.layout; then DOM-01/02 slots (two
   bases: nearest plus the best drop) and EXTR-01 (two on the beacon, two on the approach) in director.mode_slots.
2. **Halo 3 Territories has no territories; Reach's are taken half-way.** Every bot walks to the map's mid; in Reach the
   takers leave after 10 s of a 30 s capture, and on asymmetric Territories (Reach's default) both teams attack.
   Change: modes.layout maps Halo 3's "territory_static" (and Halo 2's "Territories flag") to "territory"; CAPTURE_S per
   game (Halo 2 10 s, Halo 3 / Reach 30 s) until the game's capture state is read; mode_slots keeps the two takers in
   the target until Watch.the player flips; detect the defending side at round start (every zone held by one side, or by
   spawn side as invasion.roles_from_spawns) and give it one guard per territory on guard_spots (TERR-ASYM-01/05).
3. **Halo 2 King, Territories, Assault and every Neutral Flag play as Slayer.** Change: LiveH2.king_hill() from the
   active hill (the "King Hill N" flags are exported; find the active index global as CE's KING), a Halo 2 ModeWatch
   with the engine numbers checked live, "Assault bomb spawn / return" in modes.layout; for Neutral Flag pass the
   neutral stand (team 8) to live.flags in live_bots.snapshot and add a neutral branch to role_slots: mid fight first
   with the runner held until two enemies are dead, the escort on the home route's chokepoint, no defender (CTF-NEUT-01..03).
4. **Nobody disarms a planted bomb in Assault.** The enemy plants on our goal and our two goal guards stand by; our
   own planted bomb draws runners pressing Use (ASS-MULTI-03/09). Change: modes.Watch marks an item lying in a goal
   with no carrier as armed (as invasion's inv_armed); mode_slots: an armed enemy bomb sends every bot onto it, our
   armed bomb gets guard_spots round it and no runners; Bot.on_loose_objective / loose_point allow Use on an armed enemy
   bomb (disarm) and never on ours, as the Breakpoint branch does.
5. **The King scorer leaves the hill, or everyone stands in it.** The scorer's leash is 15 u (keep_role uses DEFEND_R
   for King) and close fights pull him out; the coach's contest_hill / cover_hill put the whole team or two inside at
   any time (KOTH-STATIC-01/02). Change: Bot.keep_role: King defender r = snap.hill_r with the firm leash (fights,
   hunts, items outside the hill x 0.25) and no chase in Bot.fight while the post is the hill; Director.play_ok:
   contest_hill only with an enemy believed in or at the hill and three of us alive, cover_hill one inside; overlooks
   for a hill start at hill_r + 1.5 u and never pad with the centre.
6. **An enemy-held hill is attacked one bot at a time.** The scorer slot walks in alone; nobody snipes their scorer first
   or grenades the ring (KOTH-STATIC-06/09/10). Change: in role_slots king, when the team believes an enemy is inside,
   give a precision-weapon holder the overlook with the longest sightline, hold the hill slot (Bot.stage with pull =
   the hill) until two teammates are within 10 u, then all go in with a forced objective grenade at the hill.
7. **Posture never changes the objective plan.** King, Oddball, Territories, Assault, Stockpile, Headhunter, Infection
   and Invasion slots ignore it (CTF reads only the lead), and CE / Halo 2 objective games read no score, so posture sits
   at "even" or follows the death tally (P-04..P-09, KOTH-STATIC-11/12, ODD-CORE-11/12, TERR-SYM-07/08, ASS-MULTI-11/12,
   CTF-MULTI-15/16). Change: Live.match_state reads CE's CTF / King / Oddball team scores (the engine globals beside
   SLAYER), LiveH2 sums the players' scores; a branch on s.posture.state at the top of role_slots, mode_slots and
   invasion_slots: losing late (all_in, far_behind with 180 s or less) uses each mode's all-in layout, 0 defenders;
   winning late (hide_and_hold, far_ahead late) its hold layout, no pulls or item trips. the player decides P-08 against
   his rule first.
8. **CTF hunters chase the carrier instead of cutting him off, and only two go.** (CTF-MULTI-10/11, CTF-ONE-09.)
   Change: role_slots: our flag carried and no carrier of ours to escort: every bot but one defender hunts; half the
   hunters get an intercept point on the carrier's way to his capture stand (the nav point ahead of him toward
   s.map["flags"][enemy]), Bot.live_point sends hunters there, not to f.pos.
9. **Headhunter banks blind.** A third of the team stands on drop points, live or not, with no skulls, and loose skulls
   are never picked up (HH-01..05). Change: read the skull count per player and the active drop point (its marker, as
   REACH_HILL); modes.Watch fills obj_zones with the active point and obj_items with loose skulls; mode_slots banks only
   bots with 3+ skulls; Bot.threat adds 0.3 per skull carried.
10. **A carrier alone dies without a fight.** It never drops the flag, ball or bomb to shoot (CTF-MULTI-05, ODD-CORE-04,
    ASS-MULTI-06, INV-ATK-04). Change: Bot.decide: has_flag, no teammate within ESCORT_R and an enemy in view within
    12 u: drop (Reach: a weapon switch, which think() already guards against; other games their drop input), fight from
    Bot.cover_from, then re-take through the on_flag / on_loose_objective take(); off in Halo 4.
11. **The Invasion core is never ferried and the phase push runs on the wrong clock.** (INV-ATK-04/05, INV-DEF-03.)
    Change: director.vehicle_orders adds "invasion" to the ferry modes (home = snap.inv_delivery, passenger seat)
    (NOT TO DO, the player: the core is carried as a turret, not a flag, so its carrier cannot ride); the
    pile-on also at 240 - inv_phase_t <= 60; at phase 2 two defenders with anti-vehicle guns to the attackers' vehicle
    placements.
12. **Oddball: everyone runs at the carrier and shoots him first.** His guards go untouched; a loose ball draws the
    whole team into the open (ODD-CORE-03/07/08). Change: role_slots oddball, theirs: hunters on overlooks of the
    carrier's spot, two at the door before anyone enters; Bot.threat in Oddball weights the guard nearest their carrier
    1.8 and the carrier only with no guard within 5 u; a loose ball gets one runner, the rest cover from overlooks.
13. **Free-for-all sides play without a team plan.** Halo 3 Juggernaut hunters and Infection zombies each have their own
    director (live_bots key), so nobody converges from different sides or rushes as a pack; Reach's Juggernaut is never
    marked (JUG-01, INF-ZOMB-01). Change: key directors by side once modes.Watch makes sides (snap.infected != -1);
    Juggernaut slots: hunters on three guard_spots round him at 8-15 u; zombies gather out of the survivors' sight, then
    rush from two sides; read Reach's Juggernaut mark (HUD waypoint as marked_players).
14. **Crazy King has no rotation.** Bots learn a new hill only after it moves (KOTH-MOVING-01..03). Change: the director
    keeps the hill sequence and move times; after one cycle it predicts the next hill and the interval (median of the
    moves seen); at interval - 10 s one ring bot goes to the predicted hill, and at interval - 8 s nobody pushes a hill
    we do not hold.
15. **Power weapons and power-ups are nobody's job.** No bot is sent to a spawn early, a carrier-to-be may hold the
    rockets, and the overshield goes to whoever passes (PW-01/02, PU-01/02, SLAY-CORE-04). Change: assign_roles adds a
    rotator slot (one bot, posture 0.35-0.65) at next_item(now, within=10); the runner / scorer slot cost rises for a bot
    holding a power weapon (WEAPON_RANK 4+); Bot.best_item gives the overshield to runner, escort and hill roles and camo
    to the runner.
