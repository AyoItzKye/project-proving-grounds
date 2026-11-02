# 12 - Team objective play: CTF and the objective modes as bot rules

Date: 2026-10-24. Scope: Halo CE, Halo 2 / H2A, Halo 3 and Reach in MCC (Halo 4 only where a rule differs).
This file adds to the player's guides 05 (map playbooks), 07 (mode playbooks) and the DIGEST. It does not
repeat them. Where a source or the map tags disagree with a guide, section 0.2 says so.

How to read it:
- Rule IDs are `O<section>.<n>`. A rule names who acts, when, and what, with numbers where a source has them.
- Source keys in brackets, for example `[hp-ctf]`, resolve to URLs in the Sources list at the end.
  A key ending in `(x)` was read through a web-search excerpt because the site blocks direct fetches
  (Prima, StrategyWiki, Halo Fandom, some news sites). Treat those as lower confidence.
- **unconfirmed** = no source found. **synthesis** = my combination of sourced facts; no single source says it.
- WU = Halo world unit = 10 ft = about 3.05 m [c20-scale]. Range bands are guide 01's (Short 0.8-4,
  Medium 4-12, Long 12-30 WU). Other engines' units are converted at 32 Quake III units per metre (the
  Quake III code's own comment, `3.5 * 32 //3.5 meter`) [q3-dm] and about 1.9 cm per UT2004 unit (assumption
  from UT's 88-unit-tall player; the WU values for UT numbers are approximate).
- "Tags" = the map's own placement data, exported from the official editing kits into
  `maps/<folder>/objects.json` (`spawn_time` in seconds, 0 = gametype default) [tags].
- Reddit (the main community archive for Halo strategy) refuses this research tool's user agent, so no
  Reddit thread is cited. See section 7.

---

## 0. What matters most

### 0.1 The ten findings with the biggest effect on bot play

1. **The variant decides the CTF plan, and the defaults differ by game.** "Flag at home to score" is OFF
   by default in Halo 3 and Halo 2 custom games and ON in Reach custom games; Reach matchmaking turned it
   OFF for every non-Classic CTF variant [hp-custom][shack-reach]. With it OFF the enemy carrier can score
   at any moment, so collapsing on him is mandatory; with it ON a two-flag standoff appears. Read it live.
2. **Touch-return is not the norm after CE.** CE returns a dropped flag when a teammate walks over it
   (unless "flag must reset" is set) [hbo-ce-ref]. Halo 2 custom defaults have touch return OFF and a 30 s
   reset [hp-custom]. Halo 3 and Reach use a countdown that friendly players near the flag speed up, and an
   enemy re-touch restarts it [hp-ctf]; defaults are 15 s "return" and 30 s "reset" [hp-custom]; Reach
   matchmaking used 30 s / 45 s (10 s / 30 s for One Flag on small maps) and touch return only in
   Classic variants [shack-reach]. Guide 07's "Touch it" row is wrong for H2, H3 and Reach defaults.
3. **One body in the hill, the rest outside.** "It only takes one person to accrue time atop the hill;
   more members of a team in the hill only gives your enemy a fatter target" [hbo-ce-ref]; one inside with
   the team fanned out around it [hp-koth]; on Cold Storage only one player on the hill, ideally with a
   Bubble Shield and Shotgun, teammates on the ledges [prima-coldstorage(x)]. The current director puts
   n-1 bots in the hill (section 6.8).
4. **Shipped CTF bots split by team size and flag state, and re-plan within seconds of a flag event.**
   Quake III's team leader re-issues orders 3 s after any flag-status change, sends the bots closest to home
   to defend, and flips between passive and aggressive splits if nobody has capped for 240 s [q3-team].
   UT2004 fills Attack, Defend, Attack, Attack, Attack, Defend, Freelance, Attack in join order and swings the
   freelance squad to defense or attack every 5 s by score [ut-ctfteam][ut-teamai]. Section 1.2 has the
   numbers for 2v2 to 8v8.
5. **The carrier is the top threat, and defenders intercept on the carrier's route home, not at our base.**
   UT2004 adds +6 threat to a visible enemy carrier within about 9.5 WU or within about 12.5 WU of his own
   base (else +1.5), and its pursuers path to intercept him on the way to his capture point [ut-ctfsquad].
   A Halo 2 guide gives the human version: if you lose the carrier, go to his base and watch it [hbo-coag].
6. **Carriers vary their route on purpose.** After a grab at the enemy stand, UT2004 carriers take the direct
   "final stretch" only 20% of the time and otherwise a weighted-random alternate return path [ut-ctfsquad]
   (a flag picked up mid-field goes direct); Halopedia's carrier rules say
   the same in words (detours, no route exposed on all sides, drop the flag to kill a lone chaser) [hp-multiflag].
7. **Juggling and passing are real Halo 2 / Halo 3 tools and dead in Reach.** Halo 2 and Halo 3 carriers can
   drop and re-grab to beat the carry speed penalty, and teams relay-throw the flag (Midship) or launch it
   through a man cannon (Narrows) [hp-multiflag][hbo-midship][hp-narrows]. Reach makes a carrier wait 1 s
   after a drop before full speed returns [hp-flagdrop][hp-custom].
8. **The map tags give exact power-weapon timers, and they match a 2015 community stopwatch test.** For the
   Halo 3 maps both cover, 27 of 28 timers agree (Epitaph's hammer is the exception) [tags][r-05]. Section 5
   tabulates every target map.
9. **Reach HUD location names are the callouts a human sees.** Halopedia lists them for 20+ Reach maps
   ("so named on the player's heads-up display") [hp-countdown][hp-powerhouse][hp-swordbase]...; several
   of guide 05's Reach callouts and weapon claims do not match them or the tags (0.2).
10. **Assignment quality beats assignment cleverness.** Killzone 3 keeps squads on their previous objective
    and lets bots ignore orders to survive [kz3]; Paragon scores dead bots by respawn time plus travel time
    [paragon]; spatial-query writers add 10% hysteresis so bots do not oscillate [taming-queries]. These
    three cost a few lines each and remove most "indecisive bot" symptoms.

### 0.2 Corrections to guides 05 and 07

| Guide claim | What the sources or tags say | Source |
| --- | --- | --- |
| 07 CTF table: flag return "Touch it" in CE, H2, H3, Reach | CE yes (default). H2 custom default: touch return Off, 30 s reset. H3: countdown sped up by friendlies, no touch option. Reach: countdown; touch return only in Classic matchmaking variants | [hbo-ce-ref][hp-custom][hp-ctf][shack-reach] |
| 07 CTF table: "flag must be home to score: Yes (default)" in H3 | H3 custom default "Flag at Home to Score: Disabled". H2 custom default Off. Reach custom default Yes, Reach matchmaking non-Classic Off | [hp-custom][shack-reach] |
| 07: dropped flag reset about 30 s everywhere | 30 s is the custom default; Reach matchmaking 45 s (30 s small One Flag); MLG Pit 15 s with no teammate return (x) | [hp-custom][shack-reach][fandom-mlg(x)] |
| 05 Countdown: home "Sniper ledge", grenade launcher at center, sword at Bottom mid | Default layout has only Energy Sword (180 s), Shotgun (180 s) and Concussion Rifle (90 s); Halopedia: "only three power weapons" | [tags][hp-countdown] |
| 05 Powerhouse: callouts Dam, Blue base, Creek; "Sniper (the dam side)" | HUD names are Cliffside, Dormitory, Yard, Spillway, Shed, Rock Garden, Lockers... (5.4). No sniper: a Focus Rifle (180 s) | [hp-powerhouse][tags] |
| 05 Sword Base: "Top (the upper floor with the sniper ledge)" | No sniper in the default layout: Sword 120 s, Shotgun 120 s, Concussion 180 s, Grenade Launcher 180 s | [tags] |
| 05 Zealot: Red/Blue room, Top/Bottom mid, Purple, grenade launcher | HUD names: Red/Blue Platform, Curved Hall, Corner, Halls; Center Platform; High Center; Ground Floor; Basement; Holograms. Tags: Sword 120 s, Concussion 180 s, no grenade launcher | [hp-zealot][tags] |
| 05 Boardwalk: "Concussion" callout | Tags: Sniper x2 120 s, Rockets 180 s, Plasma Launcher 180 s, Shotgun x2 120 s; no concussion rifle | [tags][hp-boardwalk] |
| 05 Construct: sword at "Bottom mid", laser on the lower side | Sword is on the upper Narrow Walkway (sniper at its other end); laser and missile pod are on the lower-corridor ramps | [hp-construct] |
| 05 Guardian: "Camo (the camo spawn at bottom)" | The green-area man cannon leads to "yellow lift's active camo spawn"; overshield is on Sniper Tower floor 2 with the carbine; tags agree (overshield next to the carbine) | [hp-guardian][tags] |
| 05 The Pit: "Rockets (the center tunnel under the mid)", "Green side (overshield...)" | Rocket Hall connects the two lower bases; Camo Hall ("Green Home", "Green Box") holds the camo; the overshield is in Overshield Alley under the Sword Room | [hp-pit] |
| 07 KOTH: hills move "60 to 90 s" | H3 and Reach custom default: 30 s; H2 Crazy King: once a minute | [hp-custom][hp-koth] |

---

## 1. Team roles per mode and team size

### 1.1 Read the variant first

These settings change who should defend and when to collapse. The live reader must fetch them; the defaults
below are what to assume until it does.

| Setting | CE | Halo 2 | H2A | Halo 3 | Reach |
| --- | --- | --- | --- | --- | --- |
| Flag at home to score (custom default) | No; built-in "CTF" says "You must have your own flag to capture"; CTF Pro: yes | Off; "CTF Classic": yes | No | Disabled (MLG Narrows: own flag must be returned) | Yes; matchmaking non-Classic: Off, Classic: On |
| Touch return | On unless "Flag Must Reset" (default No) | Off | Disabled | not an option (countdown) | Classic matchmaking only |
| Return time (friendly near the dropped flag) | n/a | n/a | Never | 15 s | 15 s; matchmaking 30 s, One Flag small maps 10 s |
| Reset time (dropped flag untouched) | fixed delay when "must reset" is on (value unconfirmed) | 30 s | 30 s | 30 s | 30 s; matchmaking 45 s, One Flag small maps 30 s |
| Enemy re-touch restarts the countdown | yes (general rule) | yes | yes | yes | yes |
| Carrier speed | unconfirmed | slow ("Slow With Flag: On") | unconfirmed | walks slowly | 75% |
| Drop and re-grab | drop yes | yes (juggling) | unconfirmed | yes (juggling) | 1 s carrier cooldown kills juggling |
| Carrier marker for enemies | unconfirmed | flag indicator "When Uncontrolled" | "Always Off" | waypoint (guide 07) | waypoint (guide 07) |
| Respawn | Instant/5/10/15 s options, growth capped at 25 s | unconfirmed | unconfirmed | 5 s default | matchmaking CTF 10 s, Assault 10-15 s |
| Caps to win | 3 (built-in) | 3 | 3 | 3; MLG Pit and Narrows 3, Heretic and Onslaught 5 | 3; MLG Sanctuary 3, Countdown, Zealot, Pit 5 |

Sources: [hbo-ce-ref][hp-custom][hp-ctf][hp-multiflag][hp-flagdrop][shack-reach][hp-mlg].
Return vs reset semantics for H3 and Reach are inferred: both have a "return" and a "reset" timer, Reach
Classic adds a separate "Touch Return", and Halopedia says friendlies near a dropped flag speed its return
**(verify in a custom game)**.

**O1.1** At load, read: flag-at-home, touch return, return time, reset time, respawn time, carrier traits
(speed, vehicle use), caps to win, time limit, sudden death. Store them on the team blackboard; every rule
below that says "if flag-at-home" reads this. Until the reader exists, use the per-game defaults above.

**O1.2** Respawn time sets the length of every advantage window. A kill buys the killer's team the
victim's respawn time (5 s H3 default, 10 s Reach matchmaking CTF) plus his travel time back
[hp-custom][shack-reach]. Halopedia: CTF respawns are usually longer than Slayer's "giving more time for
players in the offense to capture the flag" [hp-ctf].

### 1.2 What shipped CTF bots do

Quake III Arena (team leader bot, `BotCTFOrders_*`) [q3-team]. Teammates are sorted by travel time to the
home flag; defenders come from the near end, attackers from the far end. Formulas for 4 or more players
(`trunc(k*n + 0.5)`, capped):

| Flag state | Passive split | Aggressive split |
| --- | --- | --- |
| Both flags home | defend 0.5n (max 5), attack 0.4n (max 4) | defend 0.4n (max 4), attack 0.5n (max 5) |
| Our flag taken, theirs home | defend 0.3n (max 3), attack 0.7n (max 6) | defend 0.2n (max 2), attack 0.7n (max 7) |
| We hold theirs, ours home | defend 0.6n (max 6), escort our carrier 0.3n (max 3) | same |
| Both flags away | escort our carrier 0.4n (max 4), attack 0.5n (max 5) | same |

The same formulas for our team sizes (D = defend, A = attack or "get flag", E = escort the carrier;
leftover bots are unassigned and free):

| n | Both home (passive / aggressive) | Ours taken (passive / aggressive) | We hold theirs | Both away |
| --- | --- | --- | --- | --- |
| 2 | 1D 1A / 1D 1A | 1D 1A / 0D 2A | carrier + 1D | carrier + 1A |
| 4 | 2D 2A / 2D 2A | 1D 3A / 1D 3A | carrier + 2D + 1E | 2E 2A |
| 6 | 3D 2A / 2D 3A | 2D 4A / 1D 4A | 4D 2E (carrier counted inside) | 2E 3A |
| 8 | 4D 3A / 3D 4A | 2D 6A / 2D 6A | 5D 2E | 3E 4A |

Note: in Quake III a capture needs your own flag at home, so "our flag taken" sends most bots to grab the
enemy flag (it blocks the enemy's capture). That is right only when flag-at-home is ON.

Timing in the same code [q3-team][q3-dm][q3-net]:
- Orders are re-issued 3 s after a flag-status change or a team-size change.
- No capture for 240 s: 40% chance to flip passive and aggressive.
- A bot's own decision holds for 5 s (`owndecision_time = now + 5`).
- A defend order lasts 2 minutes; within 70 units (about 2.2 m) of the post the defender moves away for
  3-6 s within 350 units (about 11 m, 3.6 WU) so it never sits on the flag.
- An escort ("accompany") holds a 3.5 m formation distance from the carrier, steps back if the carrier
  walks into it, and gives up after 3 minutes or when the companion no longer carries.
- A carrier at home whose own flag is gone loiters near the base 5-15 s before trying again.
- A carrier who grabbed the flag within 128 units (4 m) of the enemy base uses no alternate route: "just get
  the hell out of the base"; otherwise it takes an alternate route goal.

UT2004 (`CTFTeamAI`, `TeamAI`, `CTFSquadAI`) [ut-ctfteam][ut-teamai][ut-ctfsquad]:
- Initial orders in join order: Attack, Defend, Attack, Attack, Attack, Defend, Freelance, Attack. Team of 2:
  1A 1D; 4: 3A 1D; 6: 4A 2D; 8: 5A 2D 1 freelance. CTF squads hold at most 3 bots.
- Every 5 s the freelance squad re-assesses: with a time limit, ahead at all, defend the least-defended
  objective; behind by more than 2, attack; with under 180 s left, behind at all, attack. Without a time
  limit the margin is 2 both ways.
- Attackers break off to chase our stolen flag only if they see it, are near home, respawned after it was
  taken, or it has been gone longer than the base-exit time while they are not near the enemy base.

Killzone (Domination, the predecessor of KZ2 Capture and Hold) [verweij]: attackers 100% when no switch is
held, 50-75% (linear, fewer as more are held) when at least one is held, 0% when all are held. Killzone 3's
commander instead creates objectives (AdvanceToWaypoint, DefendMarker, AttackEntity, EscortEntity), each with
a weight and an optimal number of bots, and a Capture and Hold commander "ahead in score and owns two of the
three areas" generates only defend objectives [kz3].

Battlefield 1942's strategic AI (by BF2's lead AI designer) exposes the same knobs: a strategy's aggression is
the fraction of resources on offense (0.0-1.0), a maximum number of simultaneous attacks, a minimum number of
defenses, and an optional time limit after which the strategy loses appeal so the AI switches
[bf1942-sai]. A BF2 modding tutorial quotes the designer: one baseline strategy for the dominant side and one
for the dominated side covers most maps [bf2-moddb(x)].

### 1.3 What human Halo teams do

- Halo 2, four per team: two guard the base, two attack [sw-h2ctf(x)].
- Four or more: one flag carrier, one "color guard", and everyone else except a few defenders gives cover
  fire; in Multi Flag "one inside defender with a shotgun" (ideally rockets too) "and a sniper in the
  backfield or midfield" is enough for a good team [fandom-ctf(x)].
- Halo CE, six per team on Sidewinder/Blood Gulch [hbo-poocho]: plan "The Flood" = one defender (in a Ghost
  parked behind the flag), three or four attackers in a Warthog, two "backup" in the tank; plan "The
  Covenant" = 2 offense, 2 backup, 2 defense. Backup supports both and scouts.
- Halopedia's offense rule for every size: "Make sure the whole opposing team is eliminated before grabbing
  the flag"; the team covers the carrier while the enemy respawns [hp-ctf].
- Guide 07's 4v4 split (runner, lead escort, rear escort, defender) matches these.

### 1.4 The default split (synthesis)

Defenders here means bots whose job is the home flag; the floater takes power weapons and the flank and
becomes the second defender or third escort as the state demands.

| Team size | Both flags home | We hold their flag (flag-at-home ON) | We hold theirs (OFF) | Our flag taken |
| --- | --- | --- | --- | --- |
| 2 | 1 home, 1 out; both push only after a kill | carrier + 1 hunting our flag | carrier + 1 escort | both hunt if they can score (OFF); else 1 hunts, 1 grabs theirs |
| 4 | 1 defender, runner, 2 escorts (guide 07) | carrier + 1 escort; 2 retrieve ours | carrier + 2 escorts, 1 defender | 3 hunt (OFF); 2 hunt + 1 defender + 1 pull (ON) |
| 6 | 2 defenders (sniper + inside CQB), runner, 2 escorts, 1 floater | carrier + 2 escorts, 3 retrieve | carrier + 3 escorts, 2 defenders | 4 hunt, 2 defend (OFF); 3 hunt, 2 defend, 1 pull (ON) |
| 8 | 2 defenders + 1 anti-vehicle, runner, 2-3 escorts, 1-2 vehicle crew | carrier + 3 escorts, 4 retrieve | carrier + 3 escorts + taxi, 3 home | 5 hunt + 3 home (OFF); 4 hunt, 3 home, 1 pull (ON) |

Basis: Quake III's state-dependent ratios [q3-team], UT2004's size table [ut-ctfteam], the human splits in 1.3,
and finding 1 (flag-at-home decides whether hunting is urgent). The 8v8 vehicle roles are guide 07's.

### 1.5 When a defender may leave the flag

**O1.3** Never leave a home flag with nobody inside Medium band of it, unless both your teammates and the
enemy team are dead or respawning (a 5-10 s window) [ut-ctfsquad: its own code carries "FIXME - try to leave
one defender at base"].

**O1.4** Roam, do not stand: move to a new spot inside about 3.5 WU of the post every 3-6 s (Quake III
defender) and never stand on the stand itself, which is where grenades land [q3-net][hp-multiflag].

**O1.5** Leave to return our dropped flag only when it is within about 10 WU, in sight, and no enemy has a
sightline to it. UT2004's own carrier picks up a dropped friendly flag only if it can see it and it is within
1500 units (about 9.5 WU) [ut-ctfsquad]; guide 07 adds the no-enemy-sightline condition.

**O1.6** Leave to chase the enemy carrier when (a) flag-at-home is OFF and he is moving toward his base, or
(b) a teammate has respawned at home after the theft and can hold the post. UT2004 lets bots that "respawned
after the flag was taken" break off and chase [ut-ctfsquad].

**O1.7** Join the attack (stop defending) when behind by 2 or more caps, or behind by 1 with under 180 s left:
UT2004's freelance swing [ut-teamai]. The last defender still stays if flag-at-home is OFF.

**O1.8** A defender that is the sniper stays a sniper: UT2004 bots that are sniping do not join a chase
(`if B.IsSniping() return false`) [ut-ctfsquad]. Our sniper defender shoots the carrier from the post.

### 1.6 Role swaps after deaths, captures and score changes

**O1.9** Re-plan on events, not only on a clock: flag taken, dropped, returned, captured, team size changed.
Quake III waits 3 s after the event so the picture settles [q3-team]. Our director re-assigns every 2 s,
which is fine as long as an event also forces it.

**O1.10** Keep roles sticky. Killzone 3's assignment "prefers to keep squads assigned to previously assigned
objectives" and only then uses distance [kz3]; the Killzone thesis warns against removing bots mid-order
because it looks indecisive [verweij]. Give the current holder of a role a cost bonus (the director's 0.5
role-inertia term) and only swap when the gain clears a margin (section 6.6: 10%).

**O1.11** Dead bots are still candidates. Paragon treats a dead hero as standing in its base with extra travel
time equal to its respawn time, so "the one that respawns in 10 seconds will be picked over the one that would
need 20 seconds" [paragon]. For Halo CTF: a bot due to respawn in 2 s near home is the right next defender;
a living escort should not be pulled back for that slot.

**O1.12** Respawning bots become home-side roles (synthesis). In Halo 3 a team's own flag at home pulls its
spawns toward it (guide 06, G06.3, +700 weight) [r-06], so after a death the bot most likely re-enters near
home: it takes defender or the next pull from there, and the living defender may step up to escort.

**O1.13** Score changes move the swing player, not the whole team: UT2004 moves only the freelance squad by
score [ut-teamai]; guide 07's lead management (+1 cap keep an escort home, +2 stop pulling) does the same with
named roles. Quake III flips the whole split only after 240 s without a capture, with p = 0.4 [q3-team].

**O1.14** Time changes the plan near the end: with 10-20 s left and the flag in hand, run for the cap even
under fire, "you're going to lose anyway" otherwise [gg-ctf]; One Flag attackers with 30 s left pull
regardless of cover (guide 07).

---

## 2. Supporting the flag carrier

### 2.1 Escort geometry

**O2.1** At least two teammates stay with any objective carrier (Halopedia says it of the bomb carrier: "Have at
least two people around you at all times") [hp-assault]; three is the UT2004 CTF squad cap [ut-ctfsquad].

**O2.2** Close escort distance: Quake III holds 3.5 m (about 1.1 WU) from the carrier [q3-dm]; guide 07's lead
escort runs 10-20 ft (1-2 WU) ahead and the rear escort 10 ft behind facing back. Both fit inside Short band.
Use 1-2 WU, never closer than about 0.5 WU (the Quake III escort backs off when the carrier walks into it)
[q3-net], and never two escorts in one spot (one rocket kills both): "If you can melee your teammate within
1-2 seconds of walking, you are TOO CLOSE" [hbo-ivory].

**O2.3** The formation centers on the carrier, not on a squad leader: UT2004's `FormationCenter` returns the
enemy-flag holder for non-defend squads, and the carrier becomes the squad leader the moment he grabs
[ut-ctfsquad]. Killzone 2's escort is "invisibly tied to the position of the player by means of what could
best be described as a rubber leash" [verweij].

**O2.4** Escorts stand between the carrier and the threat, not around him (synthesis): Dave Mark lists
"positioning of tank style defenders between enemies and more vulnerable allies" as a core influence-map use
[imap-mark]; guide 07's neutral-flag "wall between the flag and the enemy" is the same idea. Section 6.4 turns
this into slot math.

**O2.5** Leapfrog on long open stretches: half the escort advances while the other half covers, then they swap
at a set distance (Killzone squad behavior "Leapfrog") [verweij].

**O2.6** Shooting discipline: the escort does not fire at an enemy chasing the carrier if the shot risks the
carrier ("If you can't hit the enemy who's following our flag bearer without killing the flag bearer, don't
shoot") [hbo-poocho].

### 2.2 Routes

**O2.7** Pick the route home by cover and surprise, not length. Halopedia: "Do not always take the shortest
route back to base... Do not take a route which leaves you exposed from all corners, even if you have
teammates escorting you" [hp-multiflag]; "Choose a route that your opponent will think you are least likely to
take" [hp-ctf].

**O2.8** Randomize: after a grab at the stand, UT2004 carriers go direct 20% of the time and otherwise pick an
alternate return path at random, weighted by the path's priority; a flag picked up away from the stand goes
direct [ut-ctfsquad]. Quake III uses alternate route goals except right at
the enemy base [q3-dm]. The director's `pick_route` already weighs lanes, sneak routes and team threat; add the
20% direct share and a weight per route.

**O2.9** Do not reveal the pull early: shooting an unaware enemy "is simply alerting the whole team that the
flag is about to be taken"; active camo helps but "you become visible when you pick up the flag"
[hp-multiflag].

**O2.10** Pull timing: pull right after the defenders die so the grab happens inside their respawn window
[hp-ctf][hp-multiflag]. In CE, where players respawn at their own base, a Halo CE guide warns the distraction
team not to kill enemies in the field during the attack,
[hbo-poocho]. Rule (synthesis): count `t_window = victim respawn left + victim travel to his flag`; pull when
the runner's travel to the flag plus the grab is under `t_window` for at least 2 of the enemy defenders.

**O2.11** Hide when home is not ready: with flag-at-home ON and our flag away, the UT2004 carrier goes to a
hiding spot near home that the enemy base cannot see, closer than 0.7x its distance to the enemy base and
within 2400 units (about 15 WU), then camps or stakes out [ut-ctfsquad]. On Last Resort, players hide with the
flag inside the enemy base "behind the other entrance" until the enemy heads for your base, then escape
[hp-lastresort].

### 2.3 Juggling, passing and drop-to-fight

| Game | Drop the flag | Juggle (drop, re-grab, repeat) | Pass or throw | Notes |
| --- | --- | --- | --- | --- |
| CE | yes | unconfirmed | unconfirmed | no flag melee one-hit kill in CE [hp-ctf] |
| Halo 2 | yes | yes: default buttons "RT X RT X RT X" | yes: jump and drop to throw; relay plays exist | [hp-multiflag][hbo-midship] |
| Halo 3 | yes (switch weapon) | yes: "Y RB Y RB Y RB" | man cannons carry a dropped flag (Narrows); windows (Isolation) | [hp-multiflag][hp-narrows][hp-isolation] |
| Reach | yes | effectively no: full speed returns 1 s after a drop | unconfirmed | [hp-flagdrop][hp-custom] |
| Halo 4 | no (cannot drop) | no | no | [hp-flagdrop] |

**O2.12** Juggle only on stretches the enemy cannot see: it is "slightly faster" but tells the enemy where the
flag is [hp-multiflag][hp-flagdrop]. The flag must touch the ground before it can be re-grabbed
[hp-multiflag]. (Our input layer needs the drop and pick-up buttons decoded for H2/H3 first, DIGEST input row.)

**O2.13** Drop to fight a lone chaser: "If a single pursuer is chasing you, do not be afraid to drop the flag
and kill him" [hp-multiflag]; the same for the bomb [hp-assault]. Modern Halo guidance: drop whenever attacked
unless a few steps from the cap or with 10-20 s left [gg-ctf].

**O2.14** At Melee band keep the flag and melee: the flag melee kills a full-shield enemy in one hit in Halo 2,
3 and Reach (not in CE, and not through an overshield) [hp-ctf][hp-multiflag].

**O2.15** Relay throws (Halo 2 Midship, from a 2004 strategy guide): two players grab and throw the flag out of
the enemy base toward mid ("It doesn't matter if they die"), a third drops to the center, catches it, jumps
and throws to a fourth, who scores [hbo-midship]. The counter is the defense rule in O3.8.

**O2.16** Man-cannon delivery (Halo 3 Narrows): "players can actually throw the flags with the man cannons and
stay behind to defend them... the cannons throw the flag very close to a player's return point" [hp-narrows].

### 2.4 When the carrier dies

**O2.17** The nearest escort re-grabs within the reset window, even at the cost of its life: "picking it up,
even at the cost of your own life, will prevent the flag from returning, and keep it in a more desirable
location" [hp-1flag]; an enemy touch restarts the defenders' return countdown [hp-ctf].

**O2.18** If enemies are close, clear first and grab second: Halopedia's bomb rule is "drop the bomb, attack,
and pick it up after you kill them" [hp-assault]; a Halo 2 assault plan says "if all 4 of you are at the base,
and there are only 2 enemies, drop the bomb and all 4 of you gang up on them" [hbo-zanzibar].

**O2.19** Guard the drop from the sightlines, not on it (synthesis): the flag is where the grenades go. Escorts
take angles that see the flag and the routes the returners will use; whoever re-grabs comes from cover.

**O2.20** Give up a dropped flag deep in their base when the reset will beat any re-grab (synthesis from the
timers in 1.1); spend those seconds killing the returners instead.

### 2.5 Calling out the carrier

**O2.21** Callout cadence: UT2004 bots announce "enemy flag carrier here" and "got our flag" at most once every
6 s [ut-ctfsquad]. Our director should share carrier sightings on the team blackboard at that rate, with the
0.5-2.5 s human-like delay research 01 recommends [r-01].

**O2.22** In Halo 2 (flag indicator only "When Uncontrolled") and H2A (indicator "Always Off") nobody sees the
carrier on the HUD [hp-custom], so team callouts are the only shared fix; in Halo Infinite sprinting with the
flag reveals the carrier [sportskeeda-ctf]. Use the callout name of the zone (Reach HUD names, section 5).

**O2.23** Reach players call positions by their own death marker: "at my X" [shack-beginner].

### 2.6 Vehicles

**O2.24** Carriers may ride passenger seats only (Warthog, Mongoose) [hp-multiflag]; a good Warthog crew can
also "run rampant inside the base, creating a distraction that enables the flag carrier to escape on foot"
[hp-lastresort]. Halo 2 Coagulation: "If the enemy has your flag, and is speeding across the map in a hog,
you've probably lost. Your best bet is to get there before him, or to kill his hog" [hbo-coag].

**O2.25** Halo Infinite's own bots were patched to "jump into allies' vehicles as either passengers or
gunners" and to be "more capable of completing objectives in... Capture the Flag (CTF) and Strongholds"
[infinite-s2]: carrier taxi and gunner support are expected bot skills.

---

## 3. Flag defense

### 3.1 Where defenders sit

**O3.1** One inside the flag room with a CQB weapon, one at range covering the approaches (sniper or
precision): the minimal good defense [fandom-ctf(x)][hp-multiflag]. "Staying in the flag base can help, but the
closer you stay to your teammates, the bigger the target"; expect grenades before the rush [hp-multiflag].

**O3.2** Cover every entrance: "most of the bases have more than one way to get in" [hp-1flag]. Keep doors and
gates closed where the map has switches (Standoff: "Keep the doors to your base shut... Open the other team's
door") [hp-standoff].

**O3.3** Sit off the stand, out of sight lines that see the stand, crouched where crouching hides you (guide 07).
In Reach, crouched players do not show on the motion tracker at all ("while you are crouched, you do not show up
on enemy radar-moving or not") [hp-boardwalk].

Map examples with a source:

| Map | Defender spot or setup | Source |
| --- | --- | --- |
| Narrows | small ledge against the pillar next to the flag spawn, "concealed from most viewpoints", with a Mauler | [hp-narrows] |
| The Pit | the Flag Spawn is "the heart of each base"; Shortcut ("Cut") links it to the Sniper Tower; a sniper and sword on a tower is "one of the strongest positions" (watch the vent and the ramp) | [prima-pit(x)][hp-pit] |
| Last Resort | defenders take the Spartan Laser first, then the active camo; bomb site: the recess beside the staircase | [hp-lastresort] |
| High Ground | laser on vehicles, rockets on the sniper or objective player; bombers crawl the pipe with camo, so nade the pipe and cover its other end with the laser | [hp-highground] |
| Valhalla | "imperative to control the Spartan Laser"; on defense "fall back to the base and use it on assaulting vehicles" | [hp-valhalla] |
| Standoff | shotgun camping in the bases; keep the switch unflipped at home; bubble shield when the enemy grabs | [hp-standoff] |
| Isolation | defend the windows: attackers pass the flag through them to a teammate in the basement hallway | [hp-isolation] |
| Sandtrap | protect your Elephant: attackers steal it and park it at their base to cap repeatedly | [hp-sandtrap] |
| Midship (H2) | "The guy with the BR always stays in the base. Always" | [hbo-midship] |

### 3.2 Stopping a pull

**O3.4** The carrier is target one: UT2004 adds +6 to a visible carrier's threat when he is within about
9.5 WU, the bot is sniping, or he is within about 12.5 WU of his own base; +1.5 otherwise [ut-ctfsquad]. Keep
the carrier as the target even when other threats appear (`MustKeepEnemy`) [ut-ctfsquad].

**O3.5** Intercept on his way home: UT2004 bots of decent skill path to intercept the carrier on the route to
his capture point (`TryToIntercept(B, Holder, EnemyFlag.Homebase)`) [ut-ctfsquad]. If nobody sees him, go to his
base and watch it [hbo-coag].

**O3.6** Shoot the carrier, let teammates take the escorts (guide 07); the carrier cannot shoot back [hp-ctf].

**O3.7** A plasma stick on the carrier is a known kill (Reach even has an achievement for it) [hp-ctf].

**O3.8** Against relay throws and fake returns: one defender never leaves the base; he "can just peck at the
guy with the flag from afar" [hbo-midship]. The Midship "overstrat" baits the whole team out to return a thrown
flag, then re-grabs it after they touch it [hbo-midship].

### 3.3 Returning a dropped flag

**O3.9** Per game (defaults from 1.1):
- CE (touch return on): run over it; one touch returns it [hbo-ce-ref]. The "Flag Returned" medal exists only in
  CTF variants "where touch return is enabled" (CE, Halo 2, H2A in MCC), so seeing it awarded tells the reader
  that touch return is on [hp-flagreturned].
- Halo 2: by default nobody can return it by touch; it resets after 30 s untouched [hp-custom]. Defend the
  drop from range for 30 s and kill anyone who re-touches.
- Halo 3 and Reach: stand within the flag's radius; a friendly near it shortens the countdown (15 s default
  return vs 30 s reset); any enemy touch restarts it [hp-ctf][hp-custom]. Several friendlies can return at once
  and each gets credit (Reach) [ta-returntosender(x)]; Reach matchmaking used 30 s return / 45 s reset
  [shack-reach].
- Halo 4: no touch return; it auto-returns on a timer (guide 07).

**O3.10** Return only when nobody has a sightline on the flag (guide 07). If they do, hold the sightline and
kill whoever comes to touch it: an enemy touch restarts our return countdown [hp-ctf].

**O3.11** One Flag defenders: "the flag can be reset by the defenders hovering around it"; attackers re-grab it
even at the cost of their life to stop the reset [hp-1flag]. Race it: the nearest two defenders return, the
others shoot.

### 3.4 Spawns and the flag

**O3.12** In Halo 3 your own flag at home pulls your spawns toward it (guide 06), so a team whose flag is home
keeps re-entering the fight near it; once it is taken that pull is gone. Defend before the theft, not after
[r-06]. Narrows warns: "Your opponents often spawn behind you" [hp-narrows].

### 3.5 When the whole team collapses on the enemy carrier

| Situation | Who goes | Why |
| --- | --- | --- |
| Flag-at-home OFF, enemy carrier moving home | everyone except 1 defender (2 at 8v8) | he scores the moment he touches his stand [hp-custom][shack-reach] |
| Flag-at-home ON, their flag is home | everyone except 1 defender | same: nothing blocks his cap |
| Flag-at-home ON, we hold their flag | 2-3 hunt; carrier + 1 escort hide near home; no full collapse | standoff: he cannot score until we lose theirs (director's `standoff` case) |
| Carrier within about 12.5 WU of his base | everyone with a sightline shoots him first | UT2004's +6 threat rule [ut-ctfsquad] |
| Carrier in a vehicle | anti-vehicle first (laser, rockets, plasma), or race him to his base | [hbo-coag] |

### 3.6 One Flag rounds

**O3.13** Matchmaking One Flag is 4 rounds, two attacks each [hp-1flag]. Attack: rush the flag at the start
while defenders are still collecting power weapons (Zanzibar) [hp-1flag]; or kill everyone, then "walk out of
the base unscathed" [hp-1flag]. Defense: "control the power weapons and push the offense back to their base"
(Headlong, Zanzibar, Burial Mounds) [hp-1flag].

**O3.14** Equip the likely carrier with a CQB weapon (sword or shotgun) and a sniper covering both him and
the home flag [hp-1flag].

---

## 4. The other objective modes

Guide 07 covers the basics of each mode. This section adds the numbers and the sourced habits.

### 4.1 King of the Hill and Crazy King

Rules that matter [hp-koth][hp-custom][hp-mlg][hbo-ce-ref]:
- CE: score to win in minutes (default 2); Team King has a 10 s respawn.
- Halo 2: Team King "uncontested for 1 minute to win"; Crazy King "The hill moves once a minute"; Team Crazy King
  1 minute uncontested on the moving hill [hp-crazyking-team].
- Halo 3: Team King "The hill must be uncontested. 150 points to win"; custom default hill movement 30 s,
  random order; MLG Team King on Construct 250 points, with a 3x-overshield custom power-up that appears after
  2:00 [hp-mlg].
- Reach: custom default 150 points, hill moves every 30 s, style Crazy Random King.
- Halo 4 shows the next hill once the current one falls to 5 points or fewer [mp1st-h4(x)].
- The hill and territory positions are in the tags (Halo 3: `koth_hill_static`, Reach: `koth_hill`) [tags];
  the order is in the variant.

**O4.1** One bot in the hill; the rest outside on positions that see the approaches
[hbo-ce-ref][hp-koth][prima-coldstorage(x)]. Late in a close game, a second bot inside is a backup that keeps the
clock running if the first falls [sw-ce-koth(x)]. Exception: if a variant scores per player in the hill
(H2A's "Scoring Style: One Per Player" may mean this, **unconfirmed**), stacking pays.

**O4.2** The hill player carries a CQB weapon and a Bubble Shield if the map has one [hp-koth][prima-coldstorage(x)].

**O4.3** Clear before entering: attackers throw a grenade into the hill first, which is why stacked defenders die
in multiples [hp-koth]. Defenders outside punish the thrower.

**O4.4** Contest cheaply: in uncontested variants one enemy body in the hill stops the holder's score, so a lone
attacker stepping in is worth it even if he dies after a few seconds (rule text [hp-koth]; synthesis).

**O4.5** Rotate early: hold the hill until about 15 s before it moves, then go to where the next hill will be and
wait in cover; that gives a 20-30 s head start (the source's example is Halo 2 Turf) [fandom-crazyking(x)]. In random-order variants hold the spot that
sees the most hill sites (guide 07).

**O4.6** FFA hills: crouch in a hill corner and do not shoot; most attackers die to someone else first
(Halo 2 Lockout, near the sniper) [hbo-lockout].

**O4.7** Mistakes: chasing kills off the hill; the whole team inside; arriving at the next hill alone.

### 4.2 Oddball

Rules [hp-oddball][hp-custom][hp-mlg]:
- The carrier cannot use weapons or grenades; ball melee is a one-hit kill in H3, Reach and H4 (setting).
- Halo 3: Team Oddball 100 points; custom default ball respawn delay 30 s, initial ball delay 3 s; MLG Guardian
  250 points. CE Team Oddball: 2 minutes, 5 s respawn. Reach custom: 150, carrier speed 75%. Halo 2: carrier
  slow, ball indicator always on.
- Halo 4 is the first game where the ball can be thrown [hp-oddball].

**O4.8** Hold where attackers must come close: "an area with multiple angles for cover, forcing your enemy to get
close" [progameguides(x)]. Map spots with a source:
- Hang 'Em High: the shotgun shelters: shotgun on one entrance, pistol on the other, "carrier duck below the
  window with a sniper looking out from it" [hp-hangemhigh].
- Snowbound: the carrier sticks to the tunnels [hp-snowbound].
- Guardian: a Bubble Shield on the tree stump forces attackers to leap to melee [hp-guardian].
- The Pit: hiding in the Ops Center works, but grenades get in through gaps in its walls [prima-pit(x)].
- Lockout, Midship, Guardian, Countdown spots: guide 07 and guide 05.

**O4.9** Guards stand between the carrier and the attackers ("Step in front of the shots and give some covering
fire") [progameguides(x)]; kills do not score, so guards fight only to protect the hold [gg-oddball].

**O4.10** A doomed carrier dies at the map edge so the ball resets to its spawn instead of dropping at the
enemy's feet ("When a ball leaves the map, it returns to its original spawn") [progameguides(x)]. In Halo 4 he
throws it to a teammate instead [progameguides(x)].

**O4.11** Staying alive is the score: the carrier is marked for the enemy, so the team sticks together around
him [gg-oddball].

### 4.3 Assault (bomb)

Rules [hp-custom][hp-assault]:
- Halo 2: arm 5 s, bomb reset 30 s, "Sticky Arming: On" (arming continues after the carrier dies if the bomb
  stays in the circle), carrier slow.
- Halo 3: custom default arming time "Instant", disarm 5 s, fuse 15 s, reset 30 s; One Bomb is 4 rounds; Attrition
  Bomb has long respawns but teams respawn on detonations.
- Reach: arm 5 s, fuse 10 s, disarm 5 s, reset 30 s; matchmaking Assault respawn 10-15 s [shack-reach].
- H2A: arm 5 s, fuse 2 s, 4 m arming cylinder.

**O4.12** At least two teammates around the carrier at all times [hp-assault].

**O4.13** "The more people you have on the bomb, the faster it is disarmed" [hp-assault]: defenders disarm in
pairs.

**O4.14** One Bomb: put active camo on the carrier while the team keeps the defenders busy [hp-assault]; High
Ground bombers take the camo and crawl the pipe [hp-highground].

**O4.15** Do not hide the bomb on the ground: it resets and the other team will probably get it [hp-assault].

**O4.16** Shipped plays (Halo 2, 4 players) [hbo-zanzibar][hbo-beaver]:
- Zanzibar: carrier rides the Warthog passenger seat, the hog parks in the base door, the driver takes the turret
  and covers the arm; a sniper crouch-walks the second tier; one player contests from corners. Alternative:
  break the glass on the camo side, toss the bomb to the bottom floor, a shotgun jumps in first, the carrier
  follows and arms, two snipers cover. "Remember to look down when arming the bomb." Defense: rockets in the
  stairway watching the plant zone.
- Beaver Creek (neutral bomb): the whole team crouch-walks through the teleporter, splits into two groups, the
  bomb group gets on the roof and breaks the glass, both groups throw one round of grenades, everyone enters,
  "the bomb guy entering a moment or two after the rest". Or throw the bomb in first to make the defenders look
  at it, then rain fire.
- Valhalla (Halo 3): secure the enemy base and the bomb spawn, plant, camp the plant with shotguns, keep one
  player near the bomb spawn to repeat; bring a regenerator to the plant [hp-valhalla].
- Last Resort (Halo 3) One Bomb defense: a power drain can flip the container vertical to block the site
  [hp-lastresort].

### 4.4 Territories and Land Grab

Rules [hp-custom][hp-territories][hp-landgrab]:
- Halo 2: 3 territories by default, contest 5 s, control 5 s.
- Halo 3: capture 30 s, one-sided by default, lock after capture; "Territories" 4 rounds, "Land Grab" 3 rounds
  (locked once taken), "Flag Rally" (no lock).
- Reach: 5 territories, capture 30 s, asymmetric default, contested scoring off.
- Land Grab (later games): three zones, each locks for the set once captured, then three new zones.

**O4.17** Offense moves as one group territory to territory, "making it hard for a team to defend all of the
territories at once"; defense masses at the territories that are easiest to take (Valhalla: the crashed Pelican
and the shotgun points) [hp-valhalla].

**O4.18** Hold two, not all: own the two that are close or mutually visible and rotate in pairs to the third; a
2-capture / 2-defend split works when organized (Halo Infinite Strongholds, the closest modern analog)
[gg-strongholds]. Guide 07 says the same for Territories.

**O4.19** Cave and room territories are grenade traps: bring a Bubble Shield or Regenerator (Valhalla
Territory 4) [hp-valhalla]; a camo-shotgun defender in the pipe holds High Ground Territory 5 [hp-highground].

### 4.5 Headhunter (Reach)

Rules [hp-custom][hp-headhunter]: FFA by default, 25 to win, 2 drop points, the zone moves every 30 s and
flashes about 3 s before it moves; a navpoint over each carrier shows his skull count "even if they are in
active camouflage"; every death drops all skulls (one even with none); 10 at once is a Skullamanjaro.

**O4.20** Deposit small and often (guide 07); never start a deposit run when the zone is flashing.

**O4.21** Hunt by the navpoint count: the biggest number is worth that many kills, and his camo does not hide it
[hp-headhunter].

### 4.6 Stockpile (Reach)

Rules [hp-stockpile][hp-custom]: four neutral flags spawn at random spots; carry them to your capture point; a
60 s countdown runs and only flags still held in the point at the end score; 10 to win or most in 10 minutes;
carrier speed 75%, 1 s carrier cooldown after a drop.

**O4.22** Never leave the zone empty: flags in it can be stolen until the cycle scores [giantbomb-stockpile(x)].

**O4.23** When the enemy sits on three flags with about 30 s left in the cycle, send a small squad to push their
carriers out of the zone [engadget-reach(x)].

**O4.24** Collectors take the nearest flags early in the cycle; defenders hold the zone's sightlines (guide 07).

### 4.7 Juggernaut

Rules [hp-custom][hp-juggernaut]: Halo 3: 10 points, killer of the Juggernaut becomes the next one after 3 s,
everyone allied against him by default. Reach custom: 150 points, Juggernaut has 200% damage resistance,
2x overshields with 0% recharge, 300% melee, a Gravity Hammer, 150% speed and jump; 5 points a kill, 10 for
killing the Juggernaut.

**O4.25** Hunters stick together and get the power weapons before the Juggernaut (not in Reach, where he has the
hammer) [hp-juggernaut].

**O4.26** Do not kill a former ally in the instant you become Juggernaut: "you are not Juggernaut until a moment
after you kill the Juggernaut", so that kill is a betrayal [hp-juggernaut].

### 4.8 Infection

Rules [hp-custom][hp-infection]: Halo 3: 25% of players start as zombies. Reach: 1 zombie, 5 rounds of 4
minutes, last man standing on; suicide makes you a zombie in Reach (in Halo 3 it let a survivor escape).

**O4.27** Survivors hold one defensible spot together; "a lone human is a zombie in 10 s" (guide 07)
[hp-infection].

**O4.28** Bait: when attacks lull, one survivor lures zombies into the base where the rest kill them
[hp-infection].

**O4.29** Never Armor Lock in Infection (zombies wait it out); avoid mounted turrets unless the flanks are held;
body shots beat missed head shots for ammo [hp-infection]. Construct has a column spot by the main lift's support
legs [hp-construct].

### 4.9 VIP (Halo 3)

Rules [hp-custom][hp-vip]: 10 points, the next VIP is chosen at the next death, optional goal areas and an
optional influence radius that gives nearby teammates traits; Escort variant: the VIP scores at checkpoints and
can only ride as a passenger.

**O4.30** Valhalla VIP setup: the VIP stays on the base's lower level, a Warthog jams the center, a shotgun covers
one entrance and an SMG the other, with a Bubble Shield or Regenerator, a gunner on the hog and a Banshee slowing
the enemy [hp-valhalla]. Sandtrap: the VIP rides on top of a Banshee crouched by the far towers [hp-sandtrap].

### 4.10 Race and Rocket Race

**O4.31** Race in a Warthog with a gunner (it shoots chasers while the driver drives); a Mongoose if you have a
rocket passenger; Rocket Race is four teams of two with the VIP in the passenger seat [hp-race][hp-vip].

### 4.11 Invasion (Reach)

Rules [hp-invasion][hp-custom]:
- Phase 1: attackers must hold the marked territories for 20 s within 4 minutes; Phase 2: hold one of two new
  territories for 30 s (Boneyard, Spire) or arm a bomb (Breakpoint); Phase 3: carry the core to the dropship.
- Defenders win by holding any one phase; if the attackers hold the objective when time runs out, sudden death
  disables respawns.
- Custom defaults: offense respawn 20 s, defense respawn 7 s; core return 30 s; carrier passenger-only.
- Boneyard and Breakpoint: Elites attack. Spire: Spartans attack.

**O4.32** The 20 s vs 7 s respawn gap means attackers must commit together: a lone attacker death costs 13 s
more than a defender death (synthesis from the defaults).

**O4.33** Defenders spread so no objective is uncovered [twinfinite-invasion(x), attribution within the search
excerpt uncertain]; they fall back when a territory falls (guide 07).

**O4.34** Attackers should not push a territory right beside the enemy spawn [twinfinite-invasion(x), same
caveat]. Holding
Boneyard's opening is hard because attackers get a strong forward spawn [ta-skunked(x)].

---

## 5. Map knowledge

### 5.0 How to use this section

- Power items and timers come from the map tags [tags]. They are the base layout used by custom games on the
  default map; matchmaking and MLG variants move weapons and use drop timers (Reach MLG: rockets 178 s, sniper and
  grenade launcher 118 s; Halo 3 MLG: sniper 150 s, rockets 180 s, powerups 120 s) [hp-mlg].
- Validation: for the Halo 3 maps covered by both, the tags match a 2015 MCC stopwatch test (research 05, 3.1)
  on 27 of 28 timers: The Pit, Guardian, Narrows, High Ground, Last Resort, Snowbound, Construct and Isolation
  agree; Epitaph's hammer is 120 s in the tags and 3:00 in the test; Isolation's shotgun uses the gametype default
  in the tags (test: 0:30), so it is not counted [tags][r-05].
- Reach callouts below are the HUD location names Halopedia lists. Halo 3 names are Halopedia's area names,
  Bungie.net names (Valhalla) and community nicknames where a source gives them.
- `objects.json` also holds each map's objective points (flags, hills, oddball spawns, territories, Reach
  Headhunter and Stockpile points) [tags]. Use them to precompute hill staging and carrier routes.
- Tag names: Halo 3 `excavator` = Mauler (the repo's own note in brain/bot.py), `energy_blade` = Energy Sword,
  `powerup_red` = overshield, `powerup_blue` = active camo (red sits next to the carbine on Guardian's Sniper
  Tower floor 2 and under The Pit's Sword Room, where Halopedia puts the overshield) [tags][hp-guardian][hp-pit].

### 5.1 Halo 3 power items (tags, seconds; count x time)

| Map (folder) | Sniper | Rockets | Laser | Sword / Hammer | Shotgun | Other power | Powerups and equipment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| The Pit (h3_cyberdyne) | 2 x 120 | 1 x 180 | - | Sword 1 x 120 | 2 x 120 | Brute Shot 2 x 120 | Overshield 180, Camo 180, Regenerator 2 x 90, Power Drain 90 |
| Guardian (h3_guardian) | 1 x 180 | - | - | Hammer 1 x 180 | 1 x 180 | Brute Shot 120, Mauler 3 x 15 | Overshield 180, Camo 180, Bubble 60, Flare 90 |
| Construct (h3_construct) | 1 x 180 | - | 1 x 120 | Sword 1 x 180 | - | Missile Pod 120, Flamethrower 120 | Bubble, Power Drain x2 (default) |
| Narrows (h3_chill) | 2 x 150 | 1 x 180 | - | - | 1 x 120 | Brute Shot 2 x 90 | Overshield 180, Camo 180, Bubble 90, Jammer 90, Power Drain 90 |
| Valhalla (h3_riverworld) | 2 x 180 | - | 1 x 180 | - | 2 x 90 | Missile Pod 2 x 150 | Power Drain 2 x 30; Banshee 2 x 180, Warthog 2 x 90, Mongoose 5 x 15, turret 60 |
| High Ground (h3_deadlock) | 1 x 90 | 1 x 120 | 1 x 120 | - | 1 x 90 | Brute Shot 2 x 90 | Overshield 180, Camo 180, Bubble 90, Grav Lift 90, Power Drain 120; Ghost 2 x 120, Mongoose 3 x 10 |
| Last Resort (h3_zanzibar) | 2 x 120 | - | 1 x 120 | - | 2 x 90 | Brute Shot 4 x 60 | Camo 60, Power Drain 60; Warthog 120, Ghost 120, Mongoose 4 x 15, turrets 2 x 180 |
| Snowbound (h3_snowbound) | Beam Rifle 1 x 150 | - | 1 x 150 | - | 1 x 180 | Brute Shot 2 x 120 | Overshield 180, Camo 180, Bubble 90, Power Drain 90; Ghost 180 |
| Isolation (h3_isolation) | 1 x 180 | 1 x 180 | - | - | 1 (default) | Brute Shot 4 | Regenerator 2, Flare; Ghost 180, Mongoose 2 x 30 |
| Epitaph (h3_salvation) | - | 1 x 120 | - | Hammer 1 x 120 | 1 x 120 | Brute Shot 90 | Overshield 180, Camo 180, Bubble 60, Power Drain 80 |
| Sandtrap (h3_shrine) | 1 x 120 | 1 x 120 | 2 x 180 | Hammer 1 x 120 | 2 (default) | Missile Pod 2 x 180 | Banshee 180, Elephant 2, Chopper 2 x 10, Warthog 4 x 10, Mongoose 4 x 10 |
| Diamondback (h3_s3d_avalanche) | 2 x 120 | 2 x 60 | 1 x 200 | - | 1 x 80 | Brute Shot 2 x 50 | Overshield 2 x 180; Scorpion 90, Wraith 2 x 60, Hornet 2 x 180, Banshee 80, Warthog 4 x 30 |
| Edge (h3_s3d_edge) | 2 x 180 | 1 x 180 | - | - | 2 x 180 | Sentinel Beam 2 x 180 | Overshield 180, Bubble 90, Power Drain 90 |

The `h3_s3d_*` folders are Halo Online maps: s3d_avalanche is Diamondback, "a desert-themed remake of Halo 3's
Avalanche", and Edge is a Halo Online original "later ported into" MCC [hp-diamondback][hp-halo-online]. What
s3d_lockout and s3d_powerhouse are is **unconfirmed** (their tags hold a few items with default timers). The
original Avalanche, Blackout, Standoff, Rat's Nest, Foundry, Ghost Town, Orbital, Assembly, Longshore, Citadel,
Heretic, Sandbox and Cold Storage are not in `maps\` yet.

### 5.2 Halo 3 maps

**The Pit** (h3_cyberdyne): symmetric; tags hold 2 flags, 3 hills, 4 ball spawns, 10 territories [tags].
- Callouts: each base has an Upper Base, "also known to players as Sniper Tower" (sniper, Brute Shot, regenerator,
  turret on top) and a Lower Base (spawn room; the shotgun "in the farthest corner in a small hallway curving
  around the edge of the map"); Rocket Hall (connects the two lower bases); Camo Hall ("Green Home", "Green Box",
  the central hall parallel to Rocket Hall); Sword Room ("Blue Room", "Control Room", "Sword Spawn");
  Overshield Alley (under the Sword Room, three ways in, battle rifles at both ends); High Bridge [hp-pit].
  Prima adds Flag Spawn, Shotgun Tunnel, Shortcut ("Cut", between Flag Spawn and Sniper Tower), Snipe 2 (reached
  by a grav lift) and Plat (the Platform) [prima-pit(x)].
- Setups: rushing rockets at the start is "very risky... hold off the enemy and get someone to flank through the
  Camo Hall"; a sniper and sword on a Sniper Tower is one of the strongest positions, weak points the vent and the
  ramp; a Brute Shot on the tower watching the Sword Room and Overshield Alley protects the sniper [hp-pit].
- Objective: Assault: "grab the Overshield and go for the bomb in the corridor" [hp-pit]. MLG CTF is 3 caps
  [hp-mlg]; MLG Pit flags reset after 15 s and teammates cannot return them [fandom-mlg(x)].
- Carrier routes: no sourced route. The two covered cross-map lanes in the layout are Overshield Alley (it
  "connects both Upper Bases") and the Camo Hall [hp-pit] (route choice is **unconfirmed**).

**Guardian** (h3_guardian): 4 hills, 5 ball spawns [tags]; MLG Team Oddball map, 250 points [hp-mlg].
- Callouts: Sniper Tower (three floors, circular ramp; sniper on the bottom floor, carbine and overshield on floor
  2, plasma grenades and a plasma battery at the top; "S1" = the bottom level), Blue Room (two plasma batteries,
  flare, Mauler; archway to both floors of yellow lift), Bottom Blue (shotgun in a dead-end hallway, man cannon to
  Sniper Tower), Yellow Lift ("the gold room"; battle rifle and four doorways on top), Green Area (Bubble Shield on
  a tree stump, Brute Shot at its base, man cannon to yellow lift's camo spawn; "the Elbow" catwalk to Sniper
  Tower floor 2), Center Platform (open top, hammer on the closed bottom floor) [hp-guardian][fandom-guardian(x)].
- Setups: a team spawning at Sniper Tower has its sniper guard the hammer until a teammate grabs it; from Blue
  Room, a shotgun plus the Bottom Blue man cannon to Sniper Tower can disable the enemy sniper (watch for the
  overshield); a hammer holder waits in the corners of yellow lift's top; the hammer's splash goes through the
  glass at its spawn [hp-guardian]. SWAT: the Blue-room team watches the Elbow, the Elbow team watches Bottom
  Blue's lift [hp-guardian].
- Oddball: Bubble Shield on the stump (O4.8); guide 05 adds Blue room back corner and Snipe 1.

**Construct** (h3_construct): 4 hills, 3 ball spawns [tags]; MLG Team King map [hp-mlg].
- Callouts: Lower Level (a plus-shaped corridor; Spartan Laser and Missile Pod on the ramps of the small corridor,
  flamethrower at the intersection, power drain at the yellow lift entrance), Middle Level (the "transport" level;
  the lifts only go up from here), Upper Level with the Yellow Lift Zone ("by far the most sought after position"),
  the two Purple Lift Zones, and the Narrow Walkway (sword and power drain at one end, sniper and Bubble Shield at
  the other); the orange lift area holds a hill [hp-construct].
- Setups: camp lift tops, not directly in front of them (grenades come up the lifts); learn where lift riders land
  and plant a plasma there; lift-top trio: sword, Mauler and flamethrower at the three lifts; "If the opposing team
  has control of the top, just hide at the bottom... if they have the lead then they will probably just sit there"
  [hp-construct].
- KOTH: frag grenades bounced off the sloped ceiling from the lower levels reach the orange-lift hill
  [hp-construct].

**Narrows** (h3_chill): 3 hills, 4 ball spawns [tags]; MLG CTF 3 caps, own flag must be returned [hp-mlg][hp-multiflag].
- Callouts: Blue Base and Yellow Base (by their tint; Blue's man cannon on its right, Yellow's on its left), Upper
  Bridge (open, little cover), Lower Bridge (more cover, rockets at its center, snipers on each side of the
  bridge), the man cannons and their landings, the cooling core below (death after 5 s, with a hidden covered
  ledge), the flag-spawn pillar ledge [hp-narrows].
- Setups: at least two players go straight for rockets at the start; the opening sniper duel lets a battle rifle
  teammate help the sniper and take the rockets; kill man-cannon riders at the landing; throw a Bubble Shield
  through the cannon and land inside it; power-ups are under the sniper spawn (overshield against rockets, camo
  against the sniper) [hp-narrows].
- CTF: launch the flag through the man cannon (O2.16); jump from the far ends of the upper bridge to the bottom of
  the bases for a faster route to the flag or bomb return point; defender on the flag-spawn ledge with a Mauler
  [hp-narrows].

**Valhalla** (h3_riverworld): 3 hills, 3 ball spawns, 10 territories [tags].
- Callouts (Bungie.net): Lake Base, Waterfall Base, Waterfall, Canyon Bend, Ravine, Turret, Turret Side, Center
  Ridge, Pelican, Pelican Rear Cave, Pelican Nose Cave, River [hp-valhalla].
- Setups: control the laser and the ground around it, "however, sometimes a mad rush for the Spartan Laser leaves
  your base open"; the sea-side base sits farther from the laser and usually loses that race, so it snipes the
  land side [hp-valhalla][gamesradar-h3beta(x)]; the side man-cannon sniper perch has an average life under 30 s
  [sw-h3maps(x)]; Banshee hit-and-run around the towers [hp-valhalla].
- Objective: CTF carrier must be unpredictable against the laser; Assault, VIP and Territories setups in 4.3, 4.9
  and 4.4 [hp-valhalla].

**High Ground** (h3_deadlock): asymmetric attack/defend; 4 hills, 5 ball spawns [tags].
- HUD callouts: Beach, Base, Bunker, Bunker Cave, Broken Wall, Missile Launcher, Beach Tunnel, Broken Tunnel, Ledge,
  Tower, Gate, Gate Switch, Pipe Room, Backside [hp-highground].
- Layout: attackers spawn on the Beach (sniper, rockets, shotgun, grav lift, bubble, camo); defenders in the
  Fortress; the broken-down control room in the base center holds the flag spawn and the bomb plant point; the
  Pipe Room is to its east [hp-highground].
- Setups: a fight for the rockets "ensues at the start of the game, and repeats whenever the weapon respawns"; the
  rocket user goes after the sniper or the objective player, the laser user takes vehicles; rip the gate turret
  off rather than sit in it unless the sniper is yours; defenders hold the sniper tower in SWAT [hp-highground].
- Objective: bombers take camo through the pipe, so nade the pipe and hold its other end with the laser; Territory 5
  defense: shotgun plus camo in the pipe [hp-highground].

**Last Resort** (h3_zanzibar): asymmetric; 5 hills, 3 ball spawns [tags].
- Callouts: Fortress (the generator station; a flag room "three or four" times Zanzibar's, a switch that lowers
  three barriers), Camp Froman (sniper, an open room underneath with four entrances, a second catwalk from the
  fortress so defenders reach the sniper as fast as attackers), Transformers (three, next to Camp Froman), Beach
  (Warthog, Ghost, two Mongooses), Sea Wall, Wind Wheel (camo in the wheel, Bubble Shield at the tower)
  [hp-lastresort].
- Setups: the generators are the best area to control; take the sniper, battle rifle and Brute Shot from Camp
  Froman; the Brute Shot protects the sniper; a battle rifle watches the catwalk near the Wheel [hp-lastresort].
- Objective: defenders take the laser first, then the camo; attackers take shotgun, Bubble Shield and camo, open the
  door, and let a Warthog and Ghost distract while they plant; an attacking sniper on the walkway that sees into the
  flag room (enemies can spawn below him); the carrier may hide in their base behind the other entrance until they
  head for your base [hp-lastresort]. Halo 2 Zanzibar plays in 4.3.

**Snowbound** (h3_snowbound): 5 hills, 4 ball spawns [tags].
- Callouts: Low Base ("BR Spawn"; laser, two spikers and a Bubble Shield inside), High Base ("Sniper Spawn" or
  "Carbine Base"; beam rifle, two plasma rifles, power drain inside), Low Base Batteries, High Base Batteries, Rock
  Side, Tundra Side, Ice Cave Entrance (main entrance with a large shield door), Ice Cave ("Shotgun Spawn" in Lone
  Wolves, "Sniper Spawn" in Team Slayer), Ice Cave Tunnel, Ice Tunnel, Underpass ("Ghost Spawn"), Far Rocks
  [hp-snowbound].
- Setups: the Ice Cave main entrance "affords the player with a full view of the cave's three most-used entrances";
  wait behind a shield door with a shotgun or Mauler; the Far Rocks are a relatively safe base-to-base path; the
  bases' ceilings are transparent [hp-snowbound]. Oddball: stay in the tunnels [hp-snowbound].

**Shorter notes:**
- Standoff (not in maps\ yet): doors and switch rules in 3.1; "majority of games... decided in the first few
  minutes" by the power weapons; a suicide Mongoose run opens the door, grabs the flag and escapes the way it came
  [hp-standoff].
- Sandtrap (h3_shrine): CTF and Assault: seize the enemy Elephant and bring it to your base; Neutral Assault: take
  it to the middle; CTF: sneak in with a partner and take the Mongoose that spawns on the Elephant's lower level;
  a Mongoose can cross the minefield [hp-sandtrap].
- Isolation (h3_isolation): pass the flag through the windows to a teammate in the basement hallway [hp-isolation].
- Epitaph (h3_salvation): no objective tips found; rockets and hammer are central [hp-epitaph][tags].
- Blackout and Avalanche: Halopedia's strategy sections have no objective-mode tips [hp-blackout][hp-avalanche].

### 5.3 Reach power items (tags, seconds; count x time)

| Map (folder) | Sniper | Rockets | Sword / Hammer | Shotgun | Other power |
| --- | --- | --- | --- | --- | --- |
| Countdown (reach_45_launch_station) | - | - | Sword 1 x 180 | 1 x 180 | Concussion Rifle 90 |
| Boardwalk (reach_50_panopticon) | 2 x 120 | 1 x 180 | - | 2 x 120 | Plasma Launcher 180 |
| Powerhouse (reach_30_settlement) | Focus Rifle 1 x 180 | 1 x 180 | Hammer 1 x 120 | 1 x 180 | Grenade Launcher 90 |
| Sword Base (reach_20_sword_slayer) | - | - | Sword 1 x 120 | 1 x 120 | Concussion 180, Grenade Launcher 180 |
| Zealot (reach_45_aftship) | - | - | Sword 1 x 120 | - | Concussion 180 |
| Reflection (reach_52_ivory_tower) | 1 x 180 | 1 x 180 | Sword 1 x 180 | 1 x 180 | - |
| Condemned (reach_condemned) | 2 x 90 | 1 x 180 | Sword 1 x 120 | 1 x 180 | - |
| Anchor 9 (reach_dlc_slayer) | - | 1 x 90 | - | 1 x 90 | - |
| Tempest (reach_dlc_medium) | 2 x 180 | 2 x 180 | - | 2 x 120 | Warthog 2 x 120, Mongoose 2 x 60 |
| Highlands (reach_trainingpreserve) | 2 x 90 | 2 x 160 | - | 2 x 45 | Laser 120, Grenade Launcher 120, Plasma Launcher 120; Warthog 2 x 45, Ghost 2 x 60, Mongoose 6 x 60 |
| Battle Canyon (reach_cex_beaver_creek) | 1 x 180 | 1 x 180 | Sword 1 x 180 | 2 x 90 | Grenade Launcher 2 x 90 |
| Penance (reach_cex_damnation) | 2 x 180 | 1 x 180 | Sword 1 x 180 | 1 x 90 | - |
| Ridgeline (reach_cex_timberland) | 2 x 180 | 2 x 180 | - | 2 x 90 | Laser 180, Grenade Launcher 2 x 90 |
| Solitary (reach_cex_prisoner) | 2 x 180 | 1 x 180 | Hammer 1 x 180 | 2 x 90 | - |
| High Noon (reach_cex_hangemhigh) | 2 x 180 | 1 x 180 | - | 2 x 90 | Grenade Launcher 90 |
| Breakneck (reach_cex_headlong) | 2 x 180 | 2 x 180 | Sword 1 x 180 | 2 x 90 | Plasma Launcher 180, Grenade Launcher 90; Banshee 180 |
| Boneyard (reach_70_boneyard) | 1 x 120 + 2 x 180 | 1 x 120 + 2 x 180 | - | 2 x 60 | Laser 120, Focus 2 x 45 + 1 x 180, Plasma Launcher 2 x 90 + 2 x 180, Concussion 60, GL 60 + 120 (includes Invasion phase drops) |
| Spire (reach_35_island) | 3 x 120 | 1 x 90 + 3 x 120 | - | 1 x 45 | Fuel Rod 2 x 120 + 1 x 180, Focus 1 x 90 + 2 x 120, Plasma Launcher 90 + 180, Concussion 60, GL 60 (includes Invasion drops) |

Forge World variants (Asylum, Hemorrhage, Paradiso, Pinnacle) have no object export in the repo
(`maps\reach_forge_halo` holds only LiDAR data), so their weapons are not listed.

### 5.4 Reach maps

**Countdown** (reach_45_launch_station): 7 hills, 5 ball and 5 flag points in the Forge labels [tags]; MLG CTF to
5 caps [hp-mlg].
- HUD callouts: Tech Stairs, Tech Hall, Balcony, Pipe Stairs, Pipe Hall, Second Floor, Third Floor, Big Door,
  Launch Pad, Ventilation [hp-countdown].
- Setups: "only three power weapons... the Energy Sword, the Concussion Rifle, and the Shotgun... highly
  contested"; Jet Pack is near-mandatory on the stacked layout; get to the upper and middle tiers before the enemy
  without riding lifts that may be camped; three lifts under the ship and two in the inside corners; grenade or
  Hologram up a lift before riding it; a Hologram into the center draws attention [hp-countdown].
- Carrier routes and defender spots: none sourced (**unconfirmed**).

**Boardwalk** (reach_50_panopticon): 10 hills [tags].
- HUD callouts: Cafe Hall, Cafe Square, Upper Courtyard, Skybridge, Courtyard, Service Tunnels, Visitor Center,
  Ocean View, Courtyard Balcony, Rest Stop 1st Floor, Rest Stop 2nd Floor, Rest Stop Balcony, Overlook, Make Out
  Point, Abyss [hp-boardwalk].
- Setups: the long open center is a sniper lane, so move along the sides and the lower level; the Plasma Launcher
  is under the waterfall and the Rocket Launcher near the stairs on the high side, the lower level's two hot zones;
  trees are perches; crouching keeps you off radar [hp-boardwalk].
- Bungie removed Oddball and Hot Potato from Boardwalk in matchmaking [shack-reach]: treat Boardwalk as a poor
  Oddball map.

**Powerhouse** (reach_30_settlement): 8 hills, 5 ball spawns, a VIP point [tags].
- HUD callouts: Cliffside, Dormitory, Dormitory Roof, Water Tank, Yard, Powerhouse 1st Floor, Powerhouse 2nd Floor,
  Ridge, Dirt Path, Concrete Vents, Shed Roof, Shed, Concrete Path, Spillway, Rock Garden, Green Roof, Green
  Residence, Lockers, Ravine; "Vaya Con Dios!" is a hidden ledge below the waterfall [hp-powerhouse][hp-special].
- Layout: a central circular arena ringed by Concrete Path and Dirt Path, three areas around it; the two-floor
  Powerhouse has four doorways; each area has a direct path to the center: Water Tank, Yard and Lockers
  [hp-powerhouse].
- Power: rockets in the Spillway below the bridges, Gravity Hammer in the Shed above Cliffside [fandom-powerhouse(x)];
  Focus Rifle, Grenade Launcher, Shotgun per the tags [tags].

**Sword Base** (reach_20_sword_slayer): 13 hills, 3 lifts [tags].
- HUD callouts: Meeting Room, Atrium, Processing, Lobby, Elbow, Low Bridge, Medium Bridge, High Bridge, Reception,
  Low Vent, Corner Vent, Break Room, Attic, Control Center, Laboratory, Collider, F.S, High Hall, Operations,
  Operations Hall, Security [hp-swordbase].
- Layout: small, asymmetric, three gravity lifts, bridges over a central atrium; many controllable rooms, which
  makes it a good Infection map [hp-swordbase].

**Zealot** (reach_45_aftship): 8 hills, 5 flag points [tags]; MLG CTF to 5 caps [hp-mlg].
- HUD callouts: Red Platform, Red Curved Hall, Red Corner, Red Halls, Blue Platform, Blue Curved Hall, Blue Corner,
  Blue Halls, Center Platform, High Center, Ground Floor, Basement, Holograms [hp-zealot].
- Layout: levels joined by ramps and gravity lifts; the third level is exposed to space behind a shield that players
  pass but projectiles do not, with low gravity (longer jumps, slower falls) [hp-zealot]. Matchmaking uses the
  "Arena Zealot" variant since October 2010 [hp-zealot(x)].

**Reflection** (reach_52_ivory_tower), the Ivory Tower remake: 6 hills, 5 ball spawns [tags].
- HUD callouts: Entrance, Zen Garden, Walkway, Water Ramp, Water Balcony, Grass Ramp, West View, Kai Rends, East View,
  High Balcony, Balcony Hall, Back Hall, Elevator Shaft, Law Hall, Koi Ponds [hp-reflection].
- Halo 2 Ivory Tower hold that should carry over: behind the lift facing the waterfall with the sword, a shotgun and
  a sword on either side, a rocket launcher and a sniper looking down the hall [hbo-ivory].

**Boneyard** (reach_70_boneyard): Invasion map, Elites attack [hp-invasion].
- HUD callouts: Bow, Hold, The Ship, Stern Scaffold, Port Scaffold, Cliff Scaffold, Loading Bay, Junk Yard, Shop,
  Refinery (1st, 2nd, 3rd floor), Conveyor Belt, Abyss, Cliff Approach, Middle Approach, Bridge Approach, Bulkheads,
  Low Road [hp-boneyard].
- Setups: vehicles carry the fight; snipers own the open ground; the ship and refinery have few chokepoints, so
  grenade before entering or send a Hologram through; convoys beat lone vehicles; respawn at base on purpose to get
  a Scorpion or Wraith [hp-boneyard]. Bungie removed Multi Flag from Boneyard and Spire in matchmaking
  [shack-reach].

**Spire** (reach_35_island): Invasion map, Spartans attack [hp-spire][hp-invasion].
- HUD callouts: Cliff Road, Alpha Generator, Bravo Generator, Ridge Road, Middle Road, Devil's Den, Lower Spire, High
  Trail, River, Spire Airspace, Upper Spire, Conveyor Belt, Crater, BFG [hp-spire].
- Invasion Phase 2 territories are beside the gravity lifts at the spire's base [hp-invasion]; a Falcon, a Banshee
  and a Warthog are on the map [hp-spire].

**Shorter Reach notes:**
- Breakpoint (reach_dlc_invasion): HUD names Front Yard, Research Center, Upper Rock Tunnel, Lower Rock Tunnel, Rock
  Spine, The Hub, Tunnel, Back Yard, Barracks, Vehicle Bay, Retrieval, Bridge, Vault. Invasion: Phase 1 territories
  Alpha (red lights turn green as the timer runs) and Bravo (a vent rises); then the Bridge lowers and the Tunnel
  opens; Phase 2 is a bomb on the Vault; Phase 3 takes the core to the Phantom near the Bridge [hp-breakpoint].
- Tempest (reach_dlc_medium): Forest Base, Rocky Base, Center, Cliff Side, Beach Side, Wreckage, Rock Fort, Rocky and
  Forest Walkway, Rocky and Forest Tunnel, Power Source; an energy beam between the bases EMPs aircraft; man cannons
  to the flanks and to a turret rock; side caves are alternate routes to the bases [hp-tempest].
- Condemned (reach_condemned): Stairwell, Repair Bay, Communications, Comm Hallway, Observation Deck, Tram Station,
  Generator, Center Core; the Center Core has low gravity and shield doors that block fire [hp-condemned].
- Highlands (reach_trainingpreserve): Operations, Motor Pool, Waterfall, Communications, Rock Arch, Red Base, Red
  Tower, West Cave, Underpass, Pond, Rappelling Towers, Blue Base, Blue Tower, Big Horn River, Radio Tower, Crash Site,
  East Cave, Cliffs [hp-highlands].
- Anniversary maps (HUD names): Battle Canyon: East Terrain, Blue Roof, Blue Base, Blue Teleporter, South Perch,
  South Cave, North Cave, North Perch, West Terrain, Red Roof, Red Base, Red Teleporter, Creek, Rock Arch
  [hp-battlecanyon]. Penance: Abyss, Lower Bridge, Cave, Teleporter Room, Teleporter Overlook, Waterfall Balcony,
  Observation Deck, Lower Pit, Pit Overlook, Rafters, Upper Bridge, Control Room, Ramp Hallway, Pump Room, Upper Pump
  Room, Pump Room Balcony [hp-penance]. Ridgeline: Upper, Lower and Outer Red Base, Red Foothill, Overlook, Red
  Encampment, South Ridge, River, the same for Blue, Waterfall Path, North Ridge [hp-ridgeline]. Solitary: Ground
  Floor, Ground Floor Cells, Ground Floor Viewing, Monolith, Lift Room, Lower Ramp, Observation Deck, 2nd Floor,
  Upper Ramp, 3rd Floor, 3rd Floor Cells, Overlook, Red and Blue Ramp, Red and Blue Loft, Upper Chamber, 4th Floor,
  Security Platform [hp-solitary]. High Noon: Red and Blue Base, Bunker, Tunnels, Overlook, Overlook Room, Portal
  Overlook, Portal Footbridge, Central Area, Covered Ramp, Lower, Upper and Outer Catwalk, Trench, Overlook
  Footbridge, Long Ramp [hp-highnoon]. Breakneck: Hotel, Hotel Balcony, Underpass, Footbridge, Monument, Freight
  Hallway, Office 1st-3rd Floor, Construction 1st-3rd Floor, Construction Scaffolding, Engineering Hallway and Lift,
  Lower and Upper Terrace and more [hp-breakneck].
- Forge World variants: Asylum is the Sanctuary remake built in the Quarry; Hemorrhage is the Blood Gulch remake in
  the Canyon (Coagulation's terrain) [hp-forgeworld][hp-hemorrhage]; Paradiso: Banshee and Scorpion trade at the
  start, players take the mountain top to snipe respawning enemies and their vehicles [hp-paradiso]. Guide 05's
  Asylum and Pinnacle notes stand.

### 5.5 Halo 2 classics (plays that carry to their remakes)

- Midship (Heretic): the relay-throw CTF play and its counter (O2.15, O3.8) [hbo-midship].
- Zanzibar (Last Resort): Warthog-taxi and glass-drop assault plays (O4.16) [hbo-zanzibar].
- Beaver Creek (Battle Canyon): two-group roof-glass neutral-bomb play (O4.16) [hbo-beaver].
- Coagulation (Hemorrhage): race a hog-borne carrier to his base; park two hogs and snipers on the hill behind red
  base with a rocket man watching for Banshees; "The Rocket Launcher is THE KEY to this map" [hbo-coag].
- Ivory Tower (Reflection): spacing rule and the lift hold (O2.2, 5.4) [hbo-ivory].
- Lockout (Blackout): FFA hill corner crouch (O4.6) [hbo-lockout].

---

## 6. Bot AI techniques for team objective play

### 6.1 What shipped objective bots compute

| Game | Strategic layer | How roles are chosen | Update | Escort / defend behavior | Source |
| --- | --- | --- | --- | --- | --- |
| Quake III | a bot elected team leader | fixed ratios by flag state and team size; teammates sorted by travel time to home | re-order 3 s after a flag event; flip strategy after 240 s without a cap (p 0.4) | escort at 3.5 m; defenders roam 3-6 s within about 11 m | [q3-team][q3-dm][q3-net] |
| UT2004 | team AI with attack, defense, freelance squads (max 3 in CTF) | join-order list; freelance swings by score | every 5 s | formation centered on our carrier; intercept the enemy carrier on his route home; carrier +6 threat | [ut-ctfteam][ut-teamai][ut-ctfsquad] |
| Killzone 2/3 | per-faction commander, squads, autonomous HTN bots | objectives with weight and optimal bot count; 6-step assignment that keeps previous assignments | squads re-plan on order changes; anytime strategic pathing | escort = rubber leash; leapfrog; regroup markers by influence | [kz3][verweij] |
| Paragon | AI commander per team | greedy by objective priority, each pick lowers the priority by MaxPriority/TeamSize; agent score = role fit + travel time (dead = respawn time + travel) | on game events | opportunistic objectives along the path | [paragon] |
| Battlefield 1942/2 | strategic AI with strategies | aggression = share on offense; max attacks; min defenses; time limit forces change | strategy re-chosen when its time limit decays it | area "temperature" decides where to attack or defend | [bf1942-sai][bf2-moddb(x)] |
| CoD MW2 "Bot Warfare" (community mod) | none; per-bot scripted threads | probabilistic: each bot runs its Domination defend check every 1-3 s with 65% chance; when its team leads or ties on score it goes capturing with 85% / 65% / 5% chance while holding fewer / equal / more flags (always when behind), 70% to the nearest flag and 30% to a random one | 1-20 s threads | a bot more than 1024 units from the bomb carrier moves to within 256 units of him | [botwarfare] |
| Halo Infinite | unpublished | unpublished | unpublished | Season 2 made bots ride as passengers or gunners and better at CTF and Strongholds | [infinite-s2] |
| F.E.A.R., Halo 3 campaign | covered in research 01 (global coordinator; Halo 3 objective tasks with capacities) | | | | [r-01] |

### 6.2 Role assignment

**Data each tick:** bot positions and alive/respawn timers; path distance from every bot (or spawn area) to every
slot (the zone graph's all-pairs table, computed once per map); each bot's weapon and personality fit; current role.

**Technique 1, greedy in slot order (what `director.assign_roles` does now):** fill slots in list order with the
cheapest bot. Simple, but the first slot can take the only bot that suits a later one.

**Technique 2, optimal assignment:** build the same cost matrix (rows bots, columns slots, cost = path time + role
inertia - fit) and solve it with the Hungarian method; `scipy.optimize.linear_sum_assignment` accepts rectangular
matrices (more slots than bots) and is installed (scipy 1.18.1) [scipy-lsa]. For 8 bots x 12 slots it is
microseconds at the director's 2 s cadence. To avoid paths crossing and bots blocking each other, minimize the
largest travel time instead of the sum (minimal makespan), as RoboCup's SCRAM does for formation positions
[scram(x)].

**Technique 3, priority with diminishing returns (Paragon):** sort objectives by priority, let the top one take its
minimum set of bots, then reduce its priority by MaxPriority/TeamSize per bot taken, and repeat [paragon]. This
spreads a team over several objectives without hand-tuned counts (good for Territories and Stockpile).

**Rules:**
- O6.1 Cost terms: travel time (dead bots: respawn left + travel from their likely spawn) [paragon]; role inertia
  (keep the holder unless the gain is over 10%) [taming-queries]; weapon fit (sniper slot needs a long weapon,
  inside-defender slot a CQB weapon) [hp-multiflag]; personality fit (existing `b.p` traits).
- O6.2 Hard constraints first: the carrier is always the runner; at least one defender when flag-at-home is OFF; no
  two bots on one spot (`spread`).
- O6.3 Event re-plan (O1.9) plus the 2 s clock.

### 6.3 Influence and threat maps

**Killzone 3 recipe** [kz3]: per area of the strategic graph, count friendly and enemy players (and turrets),
add recent friendly and enemy deaths, smooth by distance, blend with the previous values. Squads path with these
costs, choose regroup markers by them, and add a penalty to areas other friendly squads already plan to cross so
repeated attacks vary and simultaneous attacks spread out.

**Dave Mark's modular maps** [imap-mark]:
- Base maps per faction: a proximity map (where an agent can be shortly: template radius from its maximum speed) and
  a threat map (what it can hit: template radius from its weapon range, possibly a ring for weapons weak up close),
  stamped with a strength multiplier.
- Cell size = the smallest positioning step you care about. Update about once a second (no faster than 0.5 s, no
  slower than 2 s), zeroing and re-stamping each time.
- Questions are small "working maps" around an agent built by adding, multiplying, normalizing and inverting base
  maps, then taking the highest or lowest cell.
- Use path distance (Dijkstra from the agent) instead of straight distance where walls matter.

**For our maps (synthesis):** use the zone graph from `callouts.json` (or 1 WU cells from the 0.25 WU heightmap) per
team. Each second stamp every enemy belief (not true positions) with: proximity radius = run speed (about 2.25 WU/s,
guide 06) x 1-2 s; threat radius = the weapon's effective band (guide 01); strength = 1 normal, 2 power weapon,
0.5 one shot. Add -1 where a teammate died, fading over about a minute like the director's existing threat
memory (`pick_route` fades one level per 6 s).
Blend 50/50 with the previous second (Killzone gives no factor; 0.5 is a starting value).

### 6.4 Escort formations

**Data:** carrier position, his planned path (next 2-3 nodes), the enemy threat map, cover points.

**Slot math (synthesis from [q3-dm][ut-ctfsquad][imap-mark][verweij][days-gone]):**
1. Lead slot: the path point 1.5-2 WU ahead of the carrier, shifted up to 1 WU toward the side with the highest
   enemy threat. Rear slot: 1 WU behind, facing back along the path. Third escort (8v8): flank slot on the threat
   side, perpendicular to the path at 1.5 WU.
2. Score each candidate spot near a slot: + threat-side coverage, + cover, - exposure to enemy threat, - distance to
   the slot; pick with 10% hysteresis [taming-queries].
3. Assign escorts to slots by minimal total move (Days Gone gives each squad member its own lane along the front,
   assigned "in a manner that minimizes the overall distance the Squad members will have to move") [days-gone].
4. Leash: an escort further than 3 WU from the carrier drops its fight and returns unless it is finishing a kill
   (the Killzone rubber leash) [verweij].
5. Open ground longer than about 8 WU: leapfrog, half move, half cover [verweij].

### 6.5 Objective-weighted goal arbitration

Per bot, per decision tick, score the verbs the mode adds (Return flag, Hunt carrier, Escort, Pull, Hold post,
Contest hill, Take power weapon, Fight) and keep the existing survive-first ladder (DIGEST G09.8).

| Input | Use | Source |
| --- | --- | --- |
| objective weight and desired count | each objective's base utility; its share falls as bots join (Paragon's MaxPriority/TeamSize) | [kz3][paragon] |
| state of play | aggression share of the team on offense (BF1942); UT2004's score swing; Quake III's no-capture flip | [bf1942-sai][ut-teamai][q3-team] |
| carrier threat | +6-style bonus when the enemy carrier is close to us or to his cap | [ut-ctfsquad] |
| time left | last 10-20 s: run the flag; last 30 s One Flag: pull regardless | [gg-ctf] guide 07 |
| self state | survive overrides: Killzone bots "can also decide to temporarily ignore orders in order to survive" | [kz3] |

Dual utility keeps bots from all doing the same thing when two options score alike: each option gets a rank and
a weight; take only the options in the highest-rank category, then pick among them by weight-based random
[dual-utility].

### 6.6 Position selection and hysteresis

- Crytek's tactical position selection: a query = generation (candidate points around the agent), conditions
  (filters such as minimum distance from a threat, cover direction) and weights (desirability), with fallback
  options tried in order if the first finds nothing [tps].
- Oscillation fixes: a tiny constant preference for one side breaks symmetric ties; explicit hysteresis re-scores
  the current destination and switches only when the new best is better "by more than some threshold (say, 10%)"
  [taming-queries].
- Use both for defender posts, hill guards, oddball guards and escort slots.

### 6.7 Budget per second (4v4 and 8v8)

| Job | Rate | Cost for 8 bots a team | Notes |
| --- | --- | --- | --- |
| influence and threat map | 1 Hz | zone graph: under 1 ms in Python; 1 WU grid with numpy: a few ms | [imap-mark] update rule |
| role assignment | event + every 2 s | `linear_sum_assignment` on 8 x 12: microseconds | [scipy-lsa] |
| escort slots | 2-5 Hz while a carrier exists | 3 slots x about 20 candidates | |
| route scoring | per pull | lanes x threat sums | existing `pick_route` |
| callouts on the blackboard | event, throttled to one per 6 s per topic | trivial | [ut-ctfsquad] |

### 6.8 Where this lands in brain/director.py

Read 2026-10-24 [director]. These are the places where the research and the current code differ; no code was
changed.

| Area | Code now | Research rule |
| --- | --- | --- |
| `assign_roles` | greedy per slot in list order, 2 s cadence, dead bots skipped | optimal assignment (6.2) and dead bots as candidates with respawn + travel cost (O1.11) |
| `role_slots`, King | `max(1, n-1)` defenders at the hill point plus hunters at the hill | one inside, the rest outside on overlooks beyond grenade range (O4.1) |
| `role_slots`, Oddball | all n bots "escort" at the carrier's position | two guards at distinct angled spots 10-25 ft out, one hunter outside (guide 07, O4.9) |
| CTF `home_rule` | starts True ("the default in CE, Halo 2, Reach") and turns off only after we score with our flag out | Halo 3 and Halo 2 custom defaults are off and Reach matchmaking turned it off (1.1): until it is learned the team plays standoffs that do not exist; read the variant, or start from the per-game default |
| CTF defenders | `min(want, n-1, (n_enemy+1)//2)`, +1/+2 on a lead | add the flag-state ratios of 1.2/1.4 and the collapse table 3.5 |
| `pick_route` | threat-weighted lanes and sneak routes, 0.6 penalty for routes already used | add a 20% direct share and per-route weights (O2.8) |

---

## 7. Gaps and unconfirmed items

1. Reddit (r/halo, r/CompetitiveHalo, r/halomcc, r/HaloReach, r/halo3) refused the research tool, so no
   community thread is quoted. Prima, StrategyWiki and Halo Fandom block direct fetches and were read only through
   search excerpts, marked (x).
2. No sourced flag-carrier routes or defender spots for the Reach arena maps (Countdown, Zealot, Sword Base,
   Boardwalk, Powerhouse, Reflection); only HUD names, layout and weapon data.
3. Community callouts for Reach maps that differ from the HUD names were not found.
4. The exact meaning of Halo 3 and Reach "Flag Return Time" vs "Flag Reset Time" is inferred (1.1); test in a custom
   game with short values.
5. Whether H2A's KOTH "Scoring Style: One Per Player" pays per player in the hill is unconfirmed (O4.1).
6. CE's "flag must reset" delay, CE and H2A carrier speed, and the CE carrier marker are unconfirmed.
7. The MLG Pit rule (15 s reset, no teammate return) comes from a Halo Fandom page read through a search excerpt.
8. Reach matchmaking timers were not checked against the Reach tags the way the Halo 3 timers were (5.0).
9. `h3_s3d_lockout` and `h3_s3d_powerhouse` are unidentified Halo Online assets.
10. The Forge World variants (Asylum, Hemorrhage, Paradiso, Pinnacle) have no object export in the repo.
11. Halo Infinite's bot objective logic is not published beyond patch notes.
12. Many H3/Reach maps the player listed (Standoff, Rat's Nest, Foundry, Ghost Town, Orbital, Assembly, Longshore,
    Citadel, Heretic, Sandbox, Cold Storage, original Avalanche and Blackout) are not in `maps\`; they got short
    notes only where a source had objective content.

---

## Sources

Repo and project files
- [tags] Map placements exported from the official editing kits: `maps/<folder>/objects.json`, made by
  `tools/h3_export.py` and `tools/reach_export.py` (field "spawn time", 0 = default).
- [director] `brain/director.py` (`assign_roles`, `role_slots`, `pick_route`, `spread`).
- [r-01] `docs/research/01-human-like-bot-behavior.md` (F.E.A.R., Halo 3 objectives system, callout delays).
- [r-05] `docs/research/05-how-humans-play-halo.md` section 3.1 (2015 MCC stopwatch timer table).
- [r-06] `docs/bot-brain/06-mechanics-and-spawn-research.md` (Halo 3 spawn weights, G06.3).

Halopedia (mechanics and modes)
- [hp-ctf] https://www.halopedia.org/Capture_the_Flag
- [hp-multiflag] https://www.halopedia.org/Multi_Flag_CTF
- [hp-1flag] https://www.halopedia.org/1_Flag_CTF
- [hp-flagdrop] https://www.halopedia.org/Flag_dropping
- [hp-flagreturned] https://www.halopedia.org/Flag_Returned
- [hp-custom] https://www.halopedia.org/Custom_game (default settings per game)
- [hp-mlg] https://www.halopedia.org/MLG_(playlist)
- [hp-koth] https://www.halopedia.org/King_of_the_Hill
- [hp-crazyking-team] https://www.halopedia.org/Team_Crazy_King
- [hp-oddball] https://www.halopedia.org/Oddball
- [hp-assault] https://www.halopedia.org/Assault
- [hp-territories] https://www.halopedia.org/Territories
- [hp-landgrab] https://www.halopedia.org/Land_Grab
- [hp-headhunter] https://www.halopedia.org/Headhunter_(game_variant)
- [hp-stockpile] https://www.halopedia.org/Stockpile
- [hp-juggernaut] https://www.halopedia.org/Juggernaut
- [hp-infection] https://www.halopedia.org/Infection
- [hp-vip] https://www.halopedia.org/VIP
- [hp-invasion] https://www.halopedia.org/Invasion
- [hp-race] https://www.halopedia.org/Race
- [hp-special] https://www.halopedia.org/Special_locations

Halopedia (maps)
- [hp-pit] https://www.halopedia.org/The_Pit
- [hp-guardian] https://www.halopedia.org/Guardian_(map)
- [hp-construct] https://www.halopedia.org/Construct
- [hp-narrows] https://www.halopedia.org/Narrows
- [hp-valhalla] https://www.halopedia.org/Valhalla
- [hp-highground] https://www.halopedia.org/High_Ground
- [hp-lastresort] https://www.halopedia.org/Last_Resort
- [hp-snowbound] https://www.halopedia.org/Snowbound
- [hp-standoff] https://www.halopedia.org/Standoff
- [hp-sandtrap] https://www.halopedia.org/Sandtrap
- [hp-isolation] https://www.halopedia.org/Isolation
- [hp-epitaph] https://www.halopedia.org/Epitaph
- [hp-blackout] https://www.halopedia.org/Blackout
- [hp-avalanche] https://www.halopedia.org/Avalanche
- [hp-diamondback] https://www.halopedia.org/Diamondback
- [hp-halo-online] https://www.halopedia.org/Halo_Online
- [hp-hangemhigh] https://www.halopedia.org/Hang_%27Em_High
- [hp-countdown] https://www.halopedia.org/Countdown
- [hp-boardwalk] https://www.halopedia.org/Boardwalk
- [hp-powerhouse] https://www.halopedia.org/Powerhouse
- [hp-swordbase] https://www.halopedia.org/Sword_Base
- [hp-zealot] https://www.halopedia.org/Zealot_(map)
- [hp-reflection] https://www.halopedia.org/Reflection
- [hp-boneyard] https://www.halopedia.org/Boneyard
- [hp-spire] https://www.halopedia.org/Spire_(map)
- [hp-breakpoint] https://www.halopedia.org/Breakpoint
- [hp-tempest] https://www.halopedia.org/Tempest
- [hp-condemned] https://www.halopedia.org/Condemned
- [hp-highlands] https://www.halopedia.org/Highlands
- [hp-battlecanyon] https://www.halopedia.org/Battle_Canyon
- [hp-penance] https://www.halopedia.org/Penance
- [hp-ridgeline] https://www.halopedia.org/Ridgeline
- [hp-solitary] https://www.halopedia.org/Solitary
- [hp-highnoon] https://www.halopedia.org/High_Noon
- [hp-breakneck] https://www.halopedia.org/Breakneck
- [hp-forgeworld] https://www.halopedia.org/Forge_World
- [hp-hemorrhage] https://www.halopedia.org/Hemorrhage
- [hp-paradiso] https://www.halopedia.org/Paradiso

Halo.Bungie.Org guides
- [hbo-ce-ref] Reference Guide for Halo Multi-player Gametype Creation (CE): https://halo.bungie.org/misc/multiplayer_refguide.html
- [hbo-poocho] Halo Tactical Strategy Guide, CTF (CE): https://halo.bungie.org/misc/poocho_ctfguide.html
- [hbo-midship] https://halo.bungie.org/gameplay/stratguide/matchmaking/midship.html
- [hbo-zanzibar] https://halo.bungie.org/gameplay/stratguide/matchmaking/zanzibar.html
- [hbo-beaver] https://halo.bungie.org/gameplay/stratguide/matchmaking/beavercreek.html
- [hbo-coag] https://halo.bungie.org/gameplay/stratguide/matchmaking/coagulation.html
- [hbo-ivory] https://halo.bungie.org/gameplay/stratguide/matchmaking/ivorytower.html
- [hbo-lockout] https://halo.bungie.org/gameplay/stratguide/matchmaking/lockout.html

Other Halo sources
- [shack-reach] Shacknews, "Bungie Rolls Out New Playlists, Map Variants, and More in Halo: Reach" (CTF and Assault settings): https://www.shacknews.com/article/66085/bungie-rolls-out-new-playlists
- [shack-beginner] Shacknews, "A Beginner's Guide to Halo: Reach Multiplayer - Part Two": https://www.shacknews.com/article/65493/a-beginners-guide-to-halo
- [gg-ctf] Gamer Guides, Halo Infinite Capture the Flag: https://www.gamerguides.com/halo-infinite/guide/multiplayer/game-modes/how-to-play-the-capture-the-flag-game-mode
- [gg-oddball] Gamer Guides, Halo Infinite Oddball: https://www.gamerguides.com/halo-infinite/guide/multiplayer/game-modes/how-to-play-the-oddball-game-mode
- [gg-strongholds] Gamer Guides, Halo Infinite Strongholds: https://www.gamerguides.com/halo-infinite/guide/multiplayer/game-modes/how-to-play-the-strongholds-game-mode
- [sportskeeda-ctf] Sportskeeda, How to play CTF in Halo Infinite: https://www.sportskeeda.com/esports/how-play-capture-the-flag-halo-infinite
- [infinite-s2] TheSixthAxis, Halo Infinite Season 2 patch notes (bot changes): https://www.thesixthaxis.com/2022/05/03/halo-infinite-season-2-launch-patch-notes-maintenance/
- [c20-scale] c20 (Reclaimers), Scale and unit conversions: https://c20.reclaimers.net/general/scale/

Read through web-search excerpts (direct fetch blocked)
- [sw-h2ctf(x)] https://strategywiki.org/wiki/Halo_2/CTF
- [sw-h3maps(x)] https://strategywiki.org/wiki/Halo_3/Maps
- [fandom-ctf(x)] https://halo.fandom.com/wiki/Capture_the_Flag
- [fandom-mlg(x)] https://halo.fandom.com/wiki/MLG_(Halo:_3_playlist)
- [fandom-guardian(x)] https://halo.fandom.com/wiki/Guardian (the "S1" label)
- [fandom-crazyking(x)] https://halo.fandom.com/wiki/Crazy_King
- [sw-ce-koth(x)] https://strategywiki.org/wiki/Halo:_Combat_Evolved/KoTH
- [fandom-powerhouse(x)] https://halo.fandom.com/wiki/Powerhouse
- [hp-zealot(x)] Halopedia Zealot playlist note ("Arena Zealot"), via search: https://halopedia.org/Arena_Zealot
- [prima-pit(x)] https://primagames.com/eguides/halo-3-odst-eguide/multiplayer/multiplayer-maps/the-pit
- [prima-coldstorage(x)] https://primagames.com/eguides/halo-3-odst-eguide/multiplayer/multiplayer-maps/cold-storage
- [progameguides(x)] https://progameguides.com/halo/how-to-win-at-oddball-in-halo-infinite-multiplayer-tips-and-tricks/
- [mp1st-h4(x)] https://mp1st.com/news/halo-4-playlist-update-for-monday-november-26
- [engadget-reach(x)] https://www.engadget.com/2010-04-14-halo-reach-multiplayer-modes-blown-wide-open.html
- [giantbomb-stockpile(x)] https://giantbomb.com/wiki/Concepts/Stockpile
- [gamesradar-h3beta(x)] https://gamesradar.com/the-halo-3-beta-walkthrough/3
- [twinfinite-invasion(x)] https://twinfinite.net/guides/halo-reach-how-to-play-invasion/
- [ta-skunked(x)] https://www.trueachievements.com/a288679/skunked-achievement
- [ta-returntosender(x)] https://www.trueachievements.com/viewcomment.aspx?commentid=340128
- [bf2-moddb(x)] https://www.moddb.com/tutorials/enhancing-battlefield-2-bot-intelligence-part-1
- [scram(x)] MacAlpine, Price, Stone, "SCRAM: Scalable Collision-avoiding Role Assignment with Minimal-makespan for Formational Positioning", AAAI 2015: https://www.cs.utexas.edu/~AustinVilla/papers/AAAI15-MacAlpine.pdf (abstract via search; paper not read)

Game AI sources
- [q3-team] Quake III Arena source, `ai_team.c`: https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_team.c
- [q3-dm] Quake III Arena source, `ai_dmq3.c` (`BotCTFSeekGoals`): https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_dmq3.c
- [q3-net] Quake III Arena source, `ai_dmnet.c` (accompany and defend goals): https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_dmnet.c
- [ut-ctfteam] UT2004 `UnrealGame/CTFTeamAI.uc`: https://github.com/Deaod/UT2004/blob/HEAD/UnrealGame/CTFTeamAI.uc
- [ut-teamai] UT2004 `UnrealGame/TeamAI.uc`: https://github.com/Deaod/UT2004/blob/HEAD/UnrealGame/TeamAI.uc
- [ut-ctfsquad] UT2004 `UnrealGame/CTFSquadAI.uc` and `SquadAI.uc`: https://github.com/Deaod/UT2004/blob/HEAD/UnrealGame/CTFSquadAI.uc
- [kz3] Straatman, Verweij, Champandard, Morcus, Kleve, "Hierarchical AI for Multiplayer Bots in Killzone 3", Game AI Pro ch. 29: http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf
- [verweij] Verweij, "A Hierarchically-Layered Multiplayer Bot System for a First-Person Shooter" (2007): https://www.guerrilla-games.com/media/News/Files/VUA07_Verweij_Hierarchically-Layered-MP-Bot_System.pdf
- [paragon] Zielinski, "Being Where It Counts: Telling Paragon Bots Where to Go", Game AI Pro 3 ch. 24: http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter24_Being_Where_It_Counts_Telling_Paragon_Bots_Where_to_Go.pdf
- [imap-mark] Mark, "Modular Tactical Influence Maps", Game AI Pro 2 ch. 30: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf
- [tps] Jack, "Tactical Position Selection: An Architecture and Query Language", Game AI Pro ch. 26: http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter26_Tactical_Position_Selection.pdf
- [taming-queries] Johnson, "Taming Spatial Queries: Tips for Natural Position Selection", Game AI Pro Online Edition 2021 ch. 5: http://www.gameaipro.com/GameAIProOnlineEdition2021/GameAIProOnlineEdition2021_Chapter05_Taming_Spatial_Queries_Tips_for_Natural_Position_Selection.pdf
- [days-gone] Karlsson, "Squad Coordination in Days Gone", Game AI Pro Online Edition 2021 ch. 12: http://www.gameaipro.com/GameAIProOnlineEdition2021/GameAIProOnlineEdition2021_Chapter12_Squad_Coordination_in_Days_Gone.pdf
- [dual-utility] Dill, "Dual-Utility Reasoning", Game AI Pro 2 ch. 3: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter03_Dual-Utility_Reasoning.pdf
- [bf1942-sai] Karlsson, "A Primer on Writing Strategies for the AI of Battlefield 1942" (DICE, 2003): https://www.realtimerendering.com/erich/bf1942/mdt/MDTDOC/AI/StrategyAI1.pdf
- [botwarfare] ineedbots, "Bot Warfare" for MW2 (IW4), `maps/mp/bots/_bot_script.gsc`: https://github.com/ineedbots/iw4_bot_warfare/blob/master/maps/mp/bots/_bot_script.gsc
- [scipy-lsa] SciPy `scipy.optimize.linear_sum_assignment`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html
