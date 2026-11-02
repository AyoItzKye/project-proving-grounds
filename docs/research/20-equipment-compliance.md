# Guide 20 compliance: every rule of the equipment and power-up guide against the code

the player's guide `docs/research/20-equipment-powerups-brain.md` (file 3 of the set) rule by rule, plus guide 18's
equipment tier table (Part 2.3, rows numbered `TIER-EQP-01..07` as in `18-tiers-compliance.md`) and `INT-04`.
Status: **done** (coded; it works with what that game reads and presses; offline test named where one exists),
**partial** (what is missing is named), **open** (not coded), **blocked** (coded or codable, but a read or an input is
missing in live play; the note names it per game, and says "coded offline" when the brain side already exists).
Blocked is not "not applicable". A row is "seen live" only where a match trace shows it; nothing here was re-run live.

Audit at HEAD 0880c6b (read only, no code changed); fa07af3 (favourite loadout guns), committed during the audit,
changes no equipment rule. Bare file names are under `brain/`; `Kit.plan sN` is step N of the
numbered comments in `equipment.py` Kit.plan (1 survive, 2 shield popped, 3 push, 4 sniper, 5 hold, 6 carry, 7 still
enemy, 8 overshield, 9 fight). Live evidence measured for this audit from match traces (`cmd` bit 7 = the equipment
button, `eq` = [kind, reader on], speed from a bot's consecutive rows):
`logs/bug_reports/reach_35_island_20261027-140807/trace.jsonl` (Spire, the player's sprint report),
`logs/trace_reach_20_sword_slayer_20261028-222915.jsonl`, `logs/trace_h3_isolation_20261028-223914.jsonl`,
`logs/trace_h4_ca_blood_crash_20261028-224436.jsonl`, `logs/evidence/h4_infslayer_g1.jsonl`,
`logs/qc_keep/trace_beavercreek_20261024-020453.jsonl`. Offline suites `tools/test_equipment.py` and
`tools/test_loadouts.py` pass at this HEAD.

update: rows
marked "" changed in 13d89c0 (misread guard per ability kind), caa0177 (sprint), f72bd5e (use rules), b488b53
(loadout ties), b741f1f (Halo 3 equipment naming), b4b6427 (move_to's dead sprint flag). Offline only; nothing re-run
live. Reach's held input: 14554e4 adds +0x08 bit 16 (live check pending), so the Reach rows stay blocked.

## the player's live observation (Spire):

| Finding | Evidence |
|---|---|
| The brain does press: sprint is held while planned (HELD, baaeaed); botcore sets +0x40 0x3000 every held tick and bit 31 on the press tick | maps/_inputs/reach.json "equipment"; native/reach.cpp (hr update: +0x40 written, then shared.h:hb_apply_buttons) |
| Sprint never engages: at the report moment bot 3 held it 3.98 s from 13.84 s, forward input 0.97, at 2.02 u/s (run speed). Whole match: 4,154 held ticks, p90 2.37 u/s; people in its first 300 s p99 3.55 u/s, 6.6 % of their samples over 3.0 u/s against 0.4 % for bots | Spire trace (bot rows and the 4 Hz world rows) |
| Still broken after every fix: Sword Base, 11,004 held ticks (21 % of bot ticks), p90 2.30 u/s | Sword Base trace |
| Toggle abilities work: each one-tick camo tap turned the reader on for the plan's 6 s and the next tap off (bot 7, 406-449 s) | Spire trace |
| Hold abilities never engage: Armor Lock 107 held ticks, never read on, bot 4 took damage while holding it (health 0.99 to 0.44 in 0.5 s at 603 s, button still down); Evade 58 ticks, no roll (0.3-1.9 u/s in the 0.6 s after); Jetpack 56 ticks, never on. Sprint's reader goes on at the press and lingers 2-3 s after release while the speed stays flat: the game takes the press edge, then sees the button up | Spire trace |
| Conclusion: Reach's held ability state is not what botcore sends (+0x40 0x3000 is not it). Leading candidate: +0x08 bit 16, which gates the ability checks in FUN_18004bc0c (static RE) and which the melee decode calls a bit that "rides on every key"; tools/decode_buttons.py drops bits that change during its idle second, so it may have been filtered. The "sprint pressed and on for every bot" was the reader, not movement. HANDOFF still lists the sprint report as "Not looked at yet" | docs/HANDOFF.md 750-751, 1116, 1989, 2012, 2430, 2750; tools/decode_buttons.py main (noisy mask) |

## Part 1. Universal pickup policy

| Rule | Status | Note | Evidence |
|---|---|---|---|
| EQP-01 timer tracking | partial | team timers start when a bot is within 25 u of an empty spawn (late, not at the take); respawn = the scenario's spawn_time else 60 s powerups / 45 s weapons; no CE map exceptions, no variant respawn settings read in any game | director.py:Director.item_up, item_taken; tools/live_bots.py:item_check; maps.py:power_items |
| EQP-02 pickup order | partial | values rockets 1.0 > overshield 0.9 = sword 0.9 > sniper 0.8 > camo 0.7 (guide: power weapon > camo > overshield > custom); no one-bot-per-item split | maps.py:POWER; bot.py:Bot.best_item |
| EQP-03 denial beats use | open | a powerup is skipped at shield > 1.0; posture never consulted, no denial pickup | bot.py:Bot.best_item |
| EQP-04 pre-position, do not fight on it | partial | arrival timed to the respawn (error sd 8(1-map_iq)+1 s); coach play rotate_power_weapon posts the formation at the next item; 5 s early behind cover, take and leave: open | bot.py:Bot.best_item; director.py:next_item |
| EQP-05 quick camo clock | partial | same arrival timing (top bots take it at spawn); no push lined up with its expiry | bot.py:Bot.best_item |
| EQP-06 carrier routing | partial | camo +0.25 flanker / sniper personality, overshield +0.3 x (posture - 0.5), speed boost +0.3 for the runner role; overshield to carriers, camo to stealth roles, skipping power weapon holders: open | bot.py:Bot.best_item |
| EQP-07 never two power-ups on one bot | partial | an overshielded bot takes no powerup; a camouflaged bot can still take the overshield (own camo not read) | bot.py:Bot.best_item |
| EQP-08 no use "to see what happens" | done | every plan carries its trigger (why); Easy uses nothing but sprint on a long walk | equipment.py:Kit.plan; tools/test_equipment.py |
| EQP-09 enemy item detection | partial | lock, hardlight, jetpack (ability_on), sprinters by speed, overshield (shield > 1.05), camo radar static, decoys by a straight walk; live: snap.deployed never filled (no dome, drain, mine, flare, jammer, field read), holograms not listed, camo powerup not read, no sounds | equipment.py:Kit.perceive, Kit.state; tools/live_bots.py (no deployed fill) |
| EQP-10 pick up on death (H3) | open | only map placements are offered; loose type-3 objects are read for timers but never as pickups | bot.py:Bot.best_item; tools/live_bots.py:item_check |

## Part 2. Power-ups

| Rule | Status | Note | Evidence |
|---|---|---|---|
| EQ-OS-01 who takes it | partial | posture bonus only; carrier / pusher / vehicle thief priority: open | bot.py:Bot.best_item |
| EQ-OS-02 use it now, AGGRESSIVE 20 s | open | nothing changes while our own shield is over 1 | bot.py (no rule) |
| EQ-OS-03 melee during the charge | open | | |
| EQ-OS-04 never with camo | partial | no camo pickup at shield > 1.0; camo then overshield not checked | bot.py:Bot.best_item |
| EQ-OS-05 carriers take the busy route | open | | |
| EQ-OS-06 overshield to the escort hog driver | open | | |
| EQ-OS-07 do not duel it early | partial | Heroic+ weight him x0.7; no back-off, no decay clock | equipment.py:Kit.threat_mod |
| EQ-OS-08 plasma pistol overcharge | done | noob-combo opener for any target with shield > 0.6 within 10 u (+5.5, Reach +3), then the precision switch | bot.py:Bot.choose_weapon, charge_fire |
| EQ-OS-09 power drain on him (H3) | done | "drain his overshield" within 4.5 u; the H3 press works live (regenerator); this use not seen live | equipment.py:Kit.plan s8 |
| EQ-OS-10 stick it | partial | generic grenade openers; no overshield trigger | bot.py:Bot.fight |
| EQ-OS-11 melee from behind | partial | generic melee in range (CE native, H3 / Reach decoded); no behind-the-overshield rule | bot.py:Bot.fight |
| EQ-OS-12 splatter through it | done | no shield gate on a ram (only Armor Lock and anti-vehicle guns stop one) | bot.py:Bot.ram_ok |
| EQ-CAMO-01 who takes camo | partial | flanker / sniper personalities only; not by role (flag sneak, planter, ball thief, Juggernaut hunter, last man) | bot.py:Bot.best_item |
| EQ-CAMO-02 crouch-walk under camo | partial | the Reach / H4 camo ability crouches for the plan's hold; a camo powerup carrier: own camo not read, no crouch | equipment.py:Kit.act |
| EQ-CAMO-03 no fire unless it kills | open | no fire discipline under camo (INT-04 hard rule) | bot.py:Bot.fight |
| EQ-CAMO-04 radar discipline | open | | |
| EQ-CAMO-05 camo to the sword holder | open | | |
| EQ-CAMO-06 objective uses | open | | |
| EQ-CAMO-07 camo does not carry | open | | |
| EQ-CAMO-08 detecting camo | partial | a camo enemy is unseen 90 % of the time past 4 u, static belief for Heroic+; camo_until comes only from the Reach / H4 / H2A ability: the CE / H2 / H3 / H2A camo powerup has no reader | bot.py:Perception.update; tools/live_bots.py (camo_until) |
| EQ-CAMO-09 counter-position | open | | |
| EQ-CAMO-10 spray the shimmer | partial | the static belief draws the look; no spray rule | equipment.py:Kit.perceive |
| EQ-CAMO-11 wait it out | open | | |
| EQ-CAMO-12 Promethean Vision shows camo | **blocked** | coded offline (PV on: beliefs of every enemy within 12 u, decoys marked); Halo 4 has no ability read or press; the counter-camo PV loadout: open | equipment.py:Kit.perceive |
| EQ-CUST-01 custom powerup traits | **blocked** | no custom powerup name in maps.POWER; the variant's Custom Powerup Traits block is not read in H3 / Reach / H4 | maps.py:POWER |
| EQ-SPD-01 speed boost routing | partial | +0.3 for the runner role (H2A / H4 speedboost placements); ball / skull runners, hill rotators, hunters: open | bot.py:Bot.best_item |
| EQ-SPD-02 long route while boosted | open | | |
| EQ-DMG-01 damage boost routing | open | no damage boost name in maps.POWER; H4 ordnance not readable | maps.py:POWER |
| EQ-DMG-02 grenades while boosted | open | | |
| EQ-DMG-03 mid-range in open lanes | open | | |
| EQ-DMG-04 against a boosted enemy | **blocked** | an enemy's damage boost has no reader in H4 / H2A | brain/live.py:LiveH4F |
| EQ-HP-01 map and route to packs | open | CE "powerup health pack" (96 on 19 maps) and ODST health_pack_small / medium / large (45) are not in maps.POWER | maps.py:POWER |
| EQ-HP-02 not at full health | open | | |
| EQ-HP-03 ODST stamina vs health | open | | |
| EQ-HP-04 Firefight packs shared | open | | |

## Part 3. Halo 3 equipment

| Rule | Status | Note | Evidence |
|---|---|---|---|
| EQ-BUBBLE-01 triggers | partial | own shield < 0.3 under fire with no cover within 1 u (s2), a rocket / laser aimed at us or a vehicle line (s1), a hit flag carrier (s6); a teammate's shields, flag / bomb grab, arm / disarm, the hold's team recharge: open | equipment.py:Kit.plan s1, s2, s6 |
| EQ-BUBBLE-02 placement | partial | dropped at our feet; no lean toward the enemy, no doorway check | equipment.py:Kit.act |
| EQ-BUBBLE-03 behavior inside | **blocked** | coded offline: recharge inside, then step out at shield > 0.6, but the exit point is on the enemy's side (dp + (e - dp).norm() x (r + 0.4)); live: our own dome is not read (snap.deployed) | equipment.py:Kit.fight_move |
| EQ-BUBBLE-04 expect melee inside | **blocked** | stands still inside and melees through the normal fight; drain inside our own bubble: open; live: dome not read | equipment.py:Kit.fight_move |
| EQ-BUBBLE-05 vehicles drive through | open | | |
| EQ-BUBBLE-06 walk in and melee | **blocked** | coded offline: no shots through a dome, Heroic+ walk in and melee (test_equipment 10); live: H3 domes not read | equipment.py:Kit.can_shoot, fight_move |
| EQ-BUBBLE-07 grenade at expiry, lift / drain the generator | **blocked** | needs the dome and its start time (deployed read); the plays themselves: open | equipment.py:Kit.grenade_spot |
| EQ-BUBBLE-08 drive through it | open | | |
| EQ-BUBBLE-09 wait at the exits for a carrier | open | | |
| EQ-DRAIN-01 triggers | partial | (b) / (d): a push on a believed enemy within 4.5 u with no teammate in its radius (s3); (c) overshield (s8); (a) boarding EMP, (e) parked tank: open | equipment.py:Kit.plan s3, s8 |
| EQ-DRAIN-02 throw and shoot | partial | thrown at the belief; every bot steers out of any drain (ours too) but only from snap.deployed (empty live); no fire-into-the-field rule | equipment.py:Kit.avoid, steer_clear |
| EQ-DRAIN-03 hill clear | open | | |
| EQ-DRAIN-04 vehicle stop role | open | | |
| EQ-DRAIN-05 at own feet vs sword / shotgun | open | | |
| EQ-DRAIN-06 leave an enemy drain | **blocked** | coded offline: step out, steer clear (test_equipment 12); live: drains not read; shooting the drain: open | equipment.py:Kit.fight_move, steer_clear |
| EQ-DRAIN-07 vehicles reverse / exit | open | | |
| EQ-DRAIN-08 bubble over a drain | open | | |
| EQ-MINE-01 vehicle lanes | open | | |
| EQ-MINE-02 chokepoints | partial | holding a post with nobody seen: the mine goes to the believed push point or 2 u ahead; no chokepoint list | equipment.py:Kit.plan s5 |
| EQ-MINE-03 on a vehicle | open | | |
| EQ-MINE-04 arm site / flag stand | partial | the same hold trigger (a defender within 4 u of its post), not keyed to the site | equipment.py:Kit.situation, Kit.plan s5 |
| EQ-MINE-05 never on our vehicle routes | open | | |
| EQ-MINE-06 shoot it or crouch past | **blocked** | coded offline: step round an enemy mine (test_equipment 13); live: mines not read; shoot / crouch / path cost: open | equipment.py:Kit.avoid, steer_clear |
| EQ-MINE-07 vehicles treat mine lanes as blocked | open | | |
| EQ-REGEN-01 triggers | partial | broken shield under fire with no cover (s2; Heroic+ alone too since the team-item wait rule sits below s2), the hold under fire at shield < 0.6 (s5), winning up close (s9); seen live once (Isolation, bot 3 at 191.5 s: slot empty the next tick, shields climbing within 0.2 s while still hit); after-fight regroup: open | equipment.py:Kit.plan s2, s5, s9 |
| EQ-REGEN-02 behind cover | open | dropped at the feet wherever the bot stands | equipment.py:Kit.act |
| EQ-REGEN-03 never where the enemy shares it | open | contradicted: s9 drops it with the enemy within 4 u | equipment.py:Kit.plan s9 |
| EQ-REGEN-04 to the close-range bot | open | | |
| EQ-COVER-01 triggers | partial | toward an aimed rocket (s1), across a sniper lane (s4); arm, stand, hill wall: open (no H3 map places cover) | equipment.py:Kit.plan s1, s4 |
| EQ-COVER-02 split a sightline | partial | placed in front toward the threat; no doorway check | equipment.py:Kit.act |
| EQ-COVER-03 stop rams | open | | |
| EQ-COVER-04 against enemy cover | open | (also needs the deployed read) | |
| EQ-JAM-01 triggers | partial | "jam their radar for the push" on any push (Normal, or with a teammate); no mode / base condition | equipment.py:Kit.plan s3 |
| EQ-JAM-02 throw ahead, ignore our radar | partial | thrown at the push point; our radar is not discounted under our own jammer | equipment.py:Kit.perceive |
| EQ-JAM-03 our radar full of dots | **blocked** | coded offline: jammed_until, Easy-level fake dot chase; live: jammers not read; SWAT corner discipline switch: open | equipment.py:Kit.perceive |
| EQ-FLARE-01 flare the corner, look away | partial | flare before a push within 4.5 u (s3); at a scoping sniper whatever his distance (s4; it needed him within 4.5 u while a sniper counts from 12 u: never fired); no look-away | equipment.py:Kit.plan s3, s4; tools/test_equipment.py 16 |
| EQ-FLARE-02 carrier escape | open | | |
| EQ-FLARE-03 look away from theirs | **blocked** | coded offline: blind while it burns, Heroic+ turn away after 1 s (test_equipment 15); live: flares not read | equipment.py:Kit.perceive |
| EQ-LIFT-01 perches and routes | open | | |
| EQ-LIFT-02 under their bubble / cover | open | only "grav lift under him" (a still enemy within 3 u, Legendary) | equipment.py:Kit.plan s7 |
| EQ-LIFT-03 vehicle launch | open | | |
| EQ-LIFT-04 anti-vehicle lane | open | | |
| EQ-INV-01 invincibility | open | campaign / Firefight items not handled | |
| EQ-CLOAK-01 cloaking | open | | |
| EQ-TURRET-01 auto-turret | open | | |
| EQ-BRUTEEQ-01 ODST Brute equipment | **blocked** | no deployed-object read in LiveODST; reactions would reuse the H3 counters | brain/live.py:LiveODST |

## Part 4. Halo: Reach armor abilities

| Rule | Status | Note | Evidence |
|---|---|---|---|
| EQ-SPRINT-01 triggers | **blocked** | coded offline: clear route (a man remembered past 25 u no longer stops it; any memory blocked 64% of Spire's moving decisions), retreat out of sight, and with the shield under 0.3 even in view (turns and runs at its waypoint, Kit.run_away, a sprint goes forward only), a chase (see EQ-SPRINT-03), closing with a close-range gun; Easy sprints a walk to a goal 15+ u off with nobody about; held (baaeaed); live the press never sprinted (the player's report above): Reach's held-ability input, +0x08 bit 16 added in 14554e4, live check pending | equipment.py:Kit.situation, Kit.sprint_wish, Kit.run_away, Kit.act; tools/test_equipment.py 6b |
| EQ-SPRINT-02 end it before a corner | partial | Heroic+ stop with a believed enemy within 12 u; no corner geometry; live as EQ-SPRINT-01 | equipment.py:Kit.sprint_wish |
| EQ-SPRINT-03 sprint at a target only with sword / shotgun inside 15 m | partial | close-range gun from 1.2 to 5 u; beyond the rule: a chase sprint with any gun at a target looking away, past 8 u and past the gun's WEAPON_RANGE reach | equipment.py:Kit.sprint_wish; tools/test_equipment.py 6b |
| EQ-SPRINT-04 carriers | done | no ability press with an objective in hand in Reach (the press drops it, 8886e07); the variant setting is not read (blanket rule) | equipment.py:Kit.act |
| EQ-JET-01 triggers | **blocked** | coded: "up the ledge" (next waypoint 0.8+ u up within 3 u, unseen) and travelling to a goal 2+ u up within 15 u; live: 56 held ticks, never on: Reach held input | equipment.py:Kit.plan; tools/test_equipment.py 16 |
| EQ-JET-02 bursts | **blocked** | 0.5 s pulses coded; Reach held input | equipment.py:Kit.plan |
| EQ-JET-03 never hover in the open | **blocked** | flies only unseen; Reach held input | equipment.py:Kit.plan |
| EQ-JET-04 CTF offense | open | | |
| EQ-JET-05 Invasion Spire | open | | |
| EQ-JET-06 Firefight | open | | |
| EQ-JET-07 shoot it in the air (1.4) | partial | x1.3 for a flying jetpacker; the enemy jetpack on-read is unverified (never read on in Spire) | equipment.py:Kit.threat_mod |
| EQ-JET-08 grenade the landing | open | | |
| EQ-JET-09 precision over rockets | open | | |
| EQ-LOCK-01 triggers | **blocked** | coded: aimed rocket / laser, vehicle line, lunge (s1), enemy within 2 u at a hold (s5), Normal at a broken shield (s2), any tier shot at a broken shield with a man within 8 u (s2); stuck plasma (no stuck read), two shooters, EMP stall: open; live: 107 held ticks, never on, damage taken inside: Reach held input | equipment.py:Kit.plan s1, s2, s5 |
| EQ-LOCK-02 hold duration | partial | 2.0 s (projectile, vehicle, stand), 1.2 s (lunge); no release when the blast passes, no full-hold EMP rule | equipment.py:Kit.plan |
| EQ-LOCK-03 EMP exit | partial | Legendary lets go beside a meleeing enemy and melees; no head shot on the stripped man, no boarding cue | equipment.py:Kit.act |
| EQ-LOCK-04 no lock without help coming | partial | Heroic+ lock on a broken shield only when shot with a man within 8 u (the player's every-ability request); Normal also with no cover (guide 09 misuse by design); no teammate ETA | equipment.py:Kit.plan s2 |
| EQ-LOCK-05 objective rules | partial | carriers never press (done); body-block: 2 s with an enemy within 2 u (guide: 5 s while teammates arrive) | equipment.py:Kit.act, Kit.plan s5 |
| EQ-LOCK-06 vehicle bait | open | | |
| EQ-LOCK-07 never in Infection | open | no mode check (INT-04 hard rule) | equipment.py:Kit.plan |
| EQ-LOCK-08 stop shooting, keep 6 m | partial | coded: no shots at a lock (Heroic+ at once, Normal after 1 s), back off from within 5 u to 6 u away and reload (test_equipment 9); 6 u is 18 m; enemy lock read unverified live | equipment.py:Kit.can_shoot, fight_move |
| EQ-LOCK-09 grenade timed to the end | partial | a grenade at his feet (Heroic+), not timed | equipment.py:Kit.grenade_spot |
| EQ-LOCK-10 lock as he comes out | open | | |
| EQ-LOCK-11 never ram a lock | done | ram refused; drivers keep 1.5 u away | bot.py:Bot.ram_ok, Bot.evade |
| EQ-LOCK-12 Firefight Elites | open | | |
| EQ-RCAMO-01 camo pickup rules apply | partial | inherits EQ-CAMO-01..07 (mostly open) | |
| EQ-RCAMO-02 switch on in position (radar on) | partial | "camo for the approach" switches it on while moving in (the opposite), every style since (flanker / sniper / camper only before; the s9 "camo ambush" it made dead was removed); no tracker check; a tap off is not re-pressed for 0.3 s (re-planned in the same tick, the one press left it off); live: the tap works (Spire bot 7) | equipment.py:Kit.plan s3, Kit.act; tools/test_equipment.py 16 |
| EQ-RCAMO-03 hold still to extend | open | | |
| EQ-RCAMO-04 Generator Defense / Invasion | partial |: Invasion attackers and objective runners switch it on, unseen, for an objective 15+ u away (s10); Generator Defense: not coded | equipment.py:Kit.plan s10; tools/test_equipment.py 16 |
| EQ-RCAMO-05 Firefight | open | | |
| EQ-RCAMO-06 their radar jam tells | partial | an enemy camo user within 10 u: static + a belief near him (Heroic+); grenade the corners, hologram probe: open | equipment.py:Kit.perceive |
| EQ-HOLO-01 triggers | partial | round the corner on a push (s3), bait a sniper (s4), pull a still man out (s7), in a fight past 6 u while he looks elsewhere (s9); Regicide, fake runner: open; live: 405 press ticks in Spire, deployment unverified (holograms not read) | equipment.py:Kit.plan |
| EQ-HOLO-02 where a real player goes | partial | aimed at the believed enemy; no cover route | equipment.py:Kit.plan |
| EQ-HOLO-03 follow it | open | | |
| EQ-HOLO-04 sniper bait, count the tracer | partial | sent at the sniper; no tracer count or push | equipment.py:Kit.plan s4 |
| EQ-HOLO-05 detect holograms | **blocked** | coded offline: 1.5 s straight line, not our attacker, one test shot (test_equipment 11); live: holograms are not in the player list (decoys_listed False) in Reach / H4 | equipment.py:Kit.decoy_suspect; tools/live_bots.py |
| EQ-EVADE-01 triggers | **blocked** | coded: aimed rocket / laser, vehicle line, lunge (s1), shot at a broken shield with a man within 8 u (s2); lock tone, bolts, needler, grenade at feet, mortar, the finish: open; live: 58 held ticks, no roll: Reach held input | equipment.py:Kit.plan s1 |
| EQ-EVADE-02 perpendicular | **blocked** | 3 u side point coded (one side for s1, s2, s4 since); Reach held input | equipment.py:Kit.plan s1, s2; tools/test_equipment.py 16 |
| EQ-EVADE-03 keep the second roll | open | the energy model allows two (cost 0.5); no rule | equipment.py:Energy |
| EQ-EVADE-04 Invasion Elites | open | | |
| EQ-EVADE-05 against Evade | open | | |
| EQ-DROP-01 triggers | **blocked** | coded: broken shield with no cover (s2; at Heroic+ alone too since: the team-item wait rule now sits below s2), the hold (s5), otherwise kept for the regroup at Heroic+; teammate health, waves, Wraith: open; hold-mode ability (Reach held input) | equipment.py:Kit.plan s2, s5 |
| EQ-DROP-02 placement and inside | **blocked** | as the bubble; own dome not read | equipment.py:Kit.fight_move |
| EQ-DROP-03 carriers' stand protector | open | | |
| EQ-DROP-04 against a drop shield | **blocked** | coded offline: Normal shoots it down, Heroic+ walk in; live: drop shields not read | equipment.py:Kit.can_shoot, fight_move |

## Part 5. Halo 4 armor abilities and packages

Halo 4 cannot press anything: no `maps/_inputs/h4.json` (Kit.pressable and sprint_ok stay False), and its ability
reader returned no ability in 235,979 bot ticks of two live matches (Infinity Slayer evidence trace, Blood Crash).

| Rule | Status | Note | Evidence |
|---|---|---|---|
| EQ-PV-01 triggers | **blocked** | coded: PV before a push (s3), unseen with a man remembered within 20 u (s10); H4 input and reader | equipment.py:Kit.plan s3, s10; tools/test_equipment.py 16 |
| EQ-PV-02 pulse | **blocked** | 2 s pulse coded (guide 1 s), 10 s between pulses; H4 | equipment.py:Kit.plan s3, Kit.act |
| EQ-PV-03 share what it sees | **blocked** | PV beliefs feed the director's sightings; no broadcast; H4 | equipment.py:Kit.perceive; director.py:sighting |
| EQ-PV-04 pre-aim the door | **blocked** | beliefs drive the generic pre-aim; H4 | equipment.py:Kit.perceive |
| EQ-PV-05 against PV | open | | |
| EQ-THRUST-01 triggers | **blocked** | coded: danger (s1), to cover on a broken shield (s2), else square to a man within 8 u when shot at a broken shield (s2), across a sniper lane (s4), with the flag unseen (s6); H4 | equipment.py:Kit.plan; tools/test_equipment.py 16 |
| EQ-THRUST-02 only to cover | **blocked** | only s2's first rule needs cover; the rest (s2's dash out of his aim too) dash 3 u sideways into anything; H4 | equipment.py:Kit.plan |
| EQ-THRUST-03 last 3 m to the goal | **blocked** | thrusts with the flag whenever unseen, not on the last 3 m; H4 | equipment.py:Kit.plan s6 |
| EQ-THRUST-04 aim at the exit | open | | |
| EQ-HLS-01 triggers | **blocked** | coded: aimed rocket / lunge (Heroic+), shot and losing at 4-20 u (s9; was 4-12 u with no cover near); H4 | equipment.py:Kit.plan s1, s9; tools/test_equipment.py 16 |
| EQ-HLS-02 never with two sides | open | contradicted: s9 fires when losing, which includes two or more enemies seen | equipment.py:Kit.situation |
| EQ-HLS-03 drop it on their reload | open | | |
| EQ-HLS-04 not against vehicles | open | contradicted: s1 raises it at a vehicle about to splatter; ABILITY_FIT rates hardlight 0.6 against vehicles | equipment.py:Kit.plan s1; loadouts.py:ABILITY_FIT |
| EQ-HLS-05 against a hardlight | **blocked** | x0.5 weight, a grenade at his feet (Heroic+); flank / wait: open; enemy hardlight not read (H4) | equipment.py:Kit.threat_mod, grenade_spot |
| EQ-SENTRY-01 triggers | **blocked** | coded: the hold under fire (s5), a still enemy (s7), on the target in a fight past 6 u (s9); H4 | equipment.py:Kit.plan s5, s7, s9; tools/test_equipment.py 16 |
| EQ-SENTRY-02 placement | open | | |
| EQ-SENTRY-03 not in the open | open | | |
| EQ-SENTRY-04 against a sentry | open | | |
| EQ-RFIELD-01 triggers | **blocked** | coded: broken shield with no cover (Heroic+ alone too since), the hold heal (s2, s5); push-back escape, Flood: open; H4 | equipment.py:Kit.plan s2, s5; tools/test_equipment.py 16 |
| EQ-RFIELD-02 on the capture point | **blocked** | the hold heal covers a defender within 4 u of its post; H4 | equipment.py:Kit.situation |
| EQ-RFIELD-03 against a field | **blocked** | grenade into an enemy heal field coded; needs the deployed read | equipment.py:Kit.grenade_spot |
| EQ-PKG-01 role loadouts | **blocked** | whole slots by how the bot died (guns + the slot's ability) and, since fa07af3, by favourite primary; slots alike in the gun go to the ability the team carries least, then the slot it has (b488b53: 103 of 105 requests were "liked", a tie always the lowest slot); never by role; H4 tactical / support packages not read per slot; SET_LOADOUT never requested in the H4 traces | loadouts.py:want_slot, liked_slot, Palette; native/h4f.cpp:f_set_loadout |
| EQ-PKG-02 posture packages | open | | |
| EQ-PKG-03 ordnance choice | **blocked** | no ordnance read and no ordnance-menu input in H4 | |

## Patch: tiers, integration and coach hooks

| Rule | Status | Note | Evidence |
|---|---|---|---|
| TIER-EQP-01 pickup timing | partial | Easy: only an item in sight on its way (done); others: arrival timed with the tier's error; Heroic pre-position, Legendary 5 s early and denial: open | bot.py:Bot.best_item |
| TIER-EQP-02 pickup routing | partial | personality / posture / runner bonuses above Easy, no tier gradient | bot.py:Bot.best_item |
| TIER-EQP-03 triggers enabled | done | Easy none but sprint on a walk to a goal 15+ u off with nobody about, Normal use-now, Heroic + hold / bait / grenade counters, Legendary + sneaky; the use rules (close-range lock and dash, camo runs, fight hologram / sentry / hardlight, PV, jetpack) apply from Normal up; live effect needs the press (Reach held, H4) | equipment.py:level, Kit.plan, Kit.sprint_wish |
| TIER-EQP-04 hologram detection | **blocked** | as EQ-HOLO-05: no tier ever sees a live hologram | equipment.py:Kit.decoy_suspect |
| TIER-EQP-05 camo detection | partial | the same at every tier; camo powerup not read | bot.py:Perception.update |
| TIER-EQP-06 Armor Lock use | **blocked** | ladder coded (18-tiers-compliance: partial); live no lock engages (Spire) | equipment.py:Kit.plan |
| TIER-EQP-07 Halo 4 loadout packages | **blocked** | as EQ-PKG-01 (18-tiers-compliance: partial; no H4 ability or package read live) | loadouts.py |
| INT-04 equipment triggers in the on-foot tick | partial | the Kit runs inside Bot.think (perceive, act, fight hooks); never ram a lock: done; never lock in Infection: open; no fire from camo: open; no equipment_hint from the objective brain | bot.py:Bot.think, Bot.fight; equipment.py:Kit |
| COACH-EQ-pickup_owner | open | the coach has no equipment fields | coach.py:ORDERS |
| COACH-EQ-deny_or_use | open | "deny" exists as a verb (role mid) with no item meaning | coach.py:ORDERS; director.py:VERB_ROLE |
| COACH-EQ-trigger_mask | open | | |
| COACH-EQ-loadout | open | | |
| COACH-EQ-ordnance_pick | **blocked** | as EQ-PKG-03 | |
| COACH-EQ-decoy | open | | |

## Per-game matrix

| Game | (a) picks up | (b) knows what it holds | (c) presses use | (d) seen working live |
|---|---|---|---|---|
| CE | overshield / camo: yes (67 placements, timed); health packs: no | overshield yes (shield reads to 3.0); own camo no | nothing to press (pickups are passive) | yes: overshield, Beaver Creek (bots 1, 5, 6 at shield 3.0 for 3,377 ticks); not in HANDOFF |
| H2 | overshield / camo: yes (23 placements) | overshield through the shield read (no pickup seen); camo no | nothing to press | no pickup found (Lockout, Colossus) |
| H2A | overshield / camo / speed boost: yes (6 placements, walk-over) | no live reading (reader static; no H2A trace since) | no input decoded (no armor abilities in standard H2A MP) | no |
| H3 | equipment: yes (106 placements, never swaps down; Isolation: 3 flares, 2 regenerators taken); overshield / camo (powerup_red 18, powerup_blue 16): no | yes: unit +0x288 named by placement (flare, regenerator read live); (b741f1f): within 1.5 u of its spot lying, 3 u of the player at the pickup (8 of 14 pickups had read "unknown") | yes: +0x08 bit 4 on the press (maps/_inputs/h3.json) | yes, once: regenerator, Isolation 22:39 (5 pickups, 1 use); not in HANDOFF |
| ODST | no (Firefight health packs not in maps.POWER; players carry no equipment) | n/a | n/a | no |
| Reach | by loadout: SET_LOADOUT taken 16 times in Spire, next-spawn kits changed (bot 6 slot 1 at 25.4 s, camo + needler at 30.4 s; Invasion also changes kits by phase); ability / Forge pickups: no | kind yes (unit +0x374; per-life kinds match the kits); on-state: camo right, sprint lingers, lock / jetpack / evade never on; charge modelled from tags, not read; the misread guard is per kind with 3 s of slack since 13d89c0 (a skilled player's 2 s evade reading had blanked every kit, the bots' own too, for the rest of Spire) | tap yes, held no | camo ability yes (Spire bot 7); sprint, Armor Lock, Evade no; Jetpack, Hologram unverified |
| H4 | loadouts coded, never requested live; 1 overshield ordnance placement; ordnance drops no | no: no ability in 235,979 bot ticks | no: no maps/_inputs/h4.json (no equipment, no sprint) | no |

## Counts

174 rows (160 guide 20 rule ids, 7 TIER-EQP rows, INT-04, 6 coach hooks): done 7, partial 49, open 76, blocked 42
(EQ-RCAMO-04 open to partial).
Blocked by cause: Reach held-ability input 9, no deployed-object read 12, Halo 4 input, ability reader, packages and
ordnance 17, other reads 4 (hologram objects 2, custom powerup traits 1, damage boost 1). Nothing is live-verified
except what the per-game matrix's column (d) and the player's-report table name.

## Top 12 gaps for live play (what a player notices first)

1. **Reach abilities do nothing when pressed (sprint, Armor Lock, Evade, Jetpack; Hologram and Drop Shield likely).**
   the player's report; numbers above. Change: decode the held state. Re-run `python -I tools/decode_buttons.py
   equipment=shift --hold 3 --dry` with the mouse untouched in the idle second and diff +0x08; test the static candidate
   by adding `{"off": 8, "mask": 65536, "press": false}` to `maps/_inputs/reach.json` "equipment" (+0x08 bit 16; data
   only, loaded at start, no botcore rebuild). Pass: a bot holding sprint over 3.0 u/s, a held lock taking no damage.
2. **Halo 4 bots never sprint and never use an ability.** No `maps/_inputs/h4.json`, and LiveH4F.ability reads
   nothing. Change: decode sprint and equipment with tools/decode_buttons.py on Halo 4 (native/h4f.cpp already applies
   the table through hb_apply_buttons); probe LiveH4F's unit +0x664 / tag +8 read on the player's player holding a known
   ability and fix the offsets.
3. **Bots stop shooting for up to a second when a sprint plan meets an enemy.** Kit.act holds the 1.0 s sprint plan
   without re-checking and sets act.fire False (Sword Base: 330 held ticks in fights, 119 inside 5 u, all DMR /
   magnum); a close-range gun sprints at a man from 15 u (45 m). Change: in Kit.act re-run sprint_wish every tick and
   drop the hold when it returns None; cut the close-range window to 5 u (EQ-SPRINT-03); never clear act.fire for a
   sprint whose speed stays under RUN_SPEED x 1.3 after 0.5 s.
4. **Bots shoot into bubbles, stand in power drains, walk onto trip mines.** tools/live_bots.py never fills
   snap.deployed, so every coded counter (no shots through a dome, walk in and melee, step out of a drain, round a mine,
   look away from a flare, our own dome's recharge) is dead live. Change: find the deployed objects (list every object
   near a throw once: their type and tag paths), then fill snap.deployed [{kind, pos, team, t first seen}] in the
   snapshot; the Kit needs no change.
5. **A camo powerup gives a player no stealth against bots (CE / H2 / H3 / H2A).** camo_until is set only from the
   Reach / H4 camo ability. Change: find each game's unit camo field (diff the player's unit before and after a camo
   pickup) and set PlayerState.camo_until in the live snapshot; Perception.update already hides camo past 4 u, and the
   same field gives our own camo for EQ-CAMO-02 / -03.
6. **Halo 3 overshield and camo spawns are ignored.** powerup_red (18) and powerup_blue (16) are not in maps.POWER, so
   best_item never routes to them (the CE names are, and CE overshield pickups happen live). Change: add both to
   maps.POWER after confirming which is which (H3 kit tag, or one live touch: shield > 1 after it).
7. **Bubble shields are wasted.** Only for our own broken shield or an aimed rocket, never for a teammate, a flag grab
   or a bomb arm, and fight_move's exit walks out toward the enemy. Change: exit at dp - (e - dp).norm() x (r + 0.4) or
   to cover; Kit.plan triggers for a teammate within 2 u at shield < 0.3 with an enemy in sight, a pickup or arm under
   fire (needs gap 4 for our own dome).
8. **Halo 3 equipment is carried to the grave.** Isolation: 5 pickups, 1 use; flares and drains need a push or
   a sniper within 4.5 u; s9 drops the regenerator with the enemy inside. Change: use-before-death (shield + health
   under 0.3 with an enemy in sight: the survival item), the guide's drain (vehicle within 10 u) and flare (carrier
   escape) triggers, and s9 only with the enemy outside the 0.75 u radius.
9. **Holograms neither fool nor get tested.** Holograms are not in the live player list (decoys_listed False). Change:
   read Reach / H4 hologram objects into snap.players as decoy rows (as simgear.py does offline) and set decoys_listed
   True.
10. **INT-04 hard rules missing: Armor Lock in Infection, firing from camo.** Change: Kit.plan returns None for
    armor_lock when snap.mode is "infection"; in Bot.fight, while our camo is on, fire only when the target's shield is
    0 or the gun kills in one (sniper, shotgun inside 2 u, sword).
11. **Overshields are not played.** A bot with one plays as usual (EQ-OS-02) and duels an overshielded enemy
    (EQ-OS-07 weights him 0.7 only). Change: posture +0.3 for 20 s after our shield goes over 1; Heroic+ disengage
    from a shield > 1.05 enemy for 20 s unless the plasma pistol opener is available.
12. **Health packs are ignored (CE, ODST Firefight).** Change: add "powerup health pack" and health_pack_small /
    medium / large to maps.POWER as kind "health"; best_item scores them only below 0.5 health with no enemy seen and
    never at full health (EQ-HP-01 / -02).
