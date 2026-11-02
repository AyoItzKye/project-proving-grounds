# The Legendary bar: the player's Halo 2 SWAT games (2026)

the player: "I played really well and feel like thats how it should feel playing against a legendary bot in all
games. I will say, the legendary bots in Halo 2 swat felt very good, and they absolutely decimated the easy bots."
So: the player's play below is what a Legendary bot should feel like in every game, and Halo 2 SWAT's Legendary
bots already feel right. Use these numbers as the target when tuning Legendary (and the gap to Easy) per game.

Sources: logs/trace_h2_foundation_20261024-161707 and -162157 (+ the Data collector files, collect_*), measured with
tools/player_stats.py (`python -I tools/observer.py you <trace>`), MCC's post-game report for game 2, and
tools/critic.py's critiques. Both games: Halo 2 Classic, Foundation, SWAT (battle rifles, no shields, no grenades
used), first to 50.

## The games

| | Game 1 (16:17, 3.3 min) | Game 2 (16:21, 4.0 min) |
|---|---|---|
| Teams | the player + 3 Legendary vs 4 Legendary | the player + 3 Easy vs 4 Legendary |
| Result | the player's team won 53-32 | the player's team lost 41-51 |
| the player | 22 kills, 8 deaths | 30 kills, 9 deaths (MCC), best streak 8 |
| Bots | the player's Legendary teammates 8 deaths each; enemy Legendary 11-14 deaths | Easy teammates 5/15, 4/14, 2/12; enemy Legendary 16/10, 14/7, 11/14, 9/10 |

## the player's play (the target)

| Measure | Game 1 | Game 2 | Legendary bots (same games) | Easy bots (game 2) |
|---|---|---|---|---|
| Aim onto a man who comes into view | 0.35 s | 0.30 s | 0.30 s | 0.40 s |
| First shot after he comes into view | 0.71 s | 0.52 s | | |
| Aim onto someone after being shot | 0.12 s | 0.61 s | 0.45-0.50 s | 1.31 s |
| Pre-aimed where the man appeared | 21 times | 20 times | | |
| Fights a minute alive | 6.1 | 6.3 | 3.5-3.8 | 3.7 |
| Fight length / time between | 2.2 s / 7.8 s | 2.4 s / 5.2 s | | |
| First fight after a spawn | 2.7 s | 3.7 s | | |
| Speed (units / s, median) | 2.06 | 1.97 | 2.07-2.09 | 2.08 |
| Standing still | 8% | 13% | 6% | 18% |
| Sideways speed in fights (strafe) | 1.15 | 0.89 | 0.93-1.06 | 0.00 (Easy does not strafe) |
| Won the first look (both saw each other) | 61% of 38 | 70% of 40 | 49-60% | 50% |
| Fight distance | 14.2 u | 14.5 u | | |
| An enemy had the player in view | 16% | 15% | | |
| Trigger time on a body | 38% | 45% | 73-91% | 64% |
| Zones | Mid 38%, Red side 26%, Blue side 20% | Mid 41%, Red side 25%, Blue side 16% | | |

How the player plays: battle rifle almost all game (145 s and 198 s of it), tap-fires (93% of trigger presses under
0.15 s, held 0.10-0.12 s, about 25-31 presses a minute), scopes in and out constantly (zoom 27-28 a minute),
strafes hard (left / right about 30 presses a minute each), jumps a few times a minute (3.3-3.5), rarely
crouches, melees or reloads early; holds Mid; fights every 5-8 s; wins first looks by pre-aiming where people come
from.

What the comparison says: Legendary already matches the player on reaction to sight, movement speed and strafing.
the player fights about 70% more often (6.1-6.3 fights a minute vs 3.5-3.8: Legendary bots spent 36-55% of their
time on "item" and 23-37% on "objective" goals in SWAT) and wins more first looks. Legendary's trigger time on a
body (73-91%) is far above the player's (38-45%): bots fire only when on target; the player fires on the move and
pre-fires corners. Neither felt wrong to the player; they are the levers if another game's Legendary feels off.

## Easy review

Game 2's three Easy bots against four Legendary: 42 deaths, 11 kills in 4 minutes. Not game-breaking:
- They fight back: of their deaths, 64% came after they had fired in the last 4 s and 73% in a fight (Legendary bots
  killed by the player: 36% and 53%; in SWAT the first burst to the head wins).
- They react, slowly by design: aim onto someone 0.40 s after he comes into view, 1.31 s after being shot (the Easy
  tier is 25% slower than a person and never strafes, README Difficulty).
- They roam (74-82% of the time) as the Easy tier does in Slayer (no plan, no director orders), stand still 18%.
- The critic found little: two Easy bots each paced in a small area for 15 s once and each pushed into something for
  3 s once; no frozen bots, no falls. Legendary bots: a few long chases of a man unseen for 10-42 s, a wall push.

Small things for the to-do list (docs/VISION.md): bots pressed grenade about 60 times in a variant with no grenades
(no grenade kills by anyone, the player never pressed grenade): read Halo 2 grenade counts so bots do not plan throws
they cannot make. MCC's post-game report shows the bots without names in Halo 2 (the s75 name hooks cover Reach).
