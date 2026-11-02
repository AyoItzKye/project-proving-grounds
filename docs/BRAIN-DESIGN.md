# Bot brain and team director: design

Three layers, fastest to slowest. Only the slowest one uses a language model.

| Layer | Runs | What it decides | Code |
|---|---|---|---|
| Bot reflexes | every game tick (30 Hz in CE) | where to look, aim error, strafe, jump, crouch, fire, melee, grenade | `brain/bot.py` |
| Bot decisions | every 0.1 to 0.2 s per bot (tier) | fight, retreat to recharge, take a role order, camp, hunt last known enemy | `brain/bot.py` |
| Team director | every 0.5 s (callouts), 2 s (roles) | reads bot reports, makes delayed callouts, assigns CTF roles, sends help to a threatened flag | `brain/director.py` |
| AI director: team coach (Ollama, on by default, live since) | every 10-30 s per team (adaptive), in the background | the team's play, tempo, roles and up to 4 orders from a state report of team knowledge; validated (guide 10 V1-V16, staleness, hold times, tier gate, the player's score rules) before the director applies it | `brain/coach.py` (+ `Director.state_doc` / `coach_*`) |

Why the model is not the per-tick brain: a local 14B model answers in about 0.1 to 3 s and competes with the game for the GPU (RTX 5080, 16 GB: the 14B model alone holds about 9 GB). Aim and movement need an answer 30 times a second. So the language model plays coach, not player; if it is slow or wrong, the rule-based director keeps going (every model answer is validated and clamped).

## Rules every layer follows (from docs/research)

- Honest information. A bot knows only what it saw (field of view plus line of sight), what the motion tracker shows (moving, not crouched, within range), and what teammates called out. The director knows only what bots reported.
- Reaction delay. A bot acts on a sighting only after its reaction time (log-normal, median by tier: 0.45 / 0.30 / 0.22 / 0.18 s).
- Memory fades. Last known positions lose confidence and are forgotten after 4 to 10 s by tier.
- Human aim. Re-aim at a tracking interval (0.30 / 0.18 / 0.10 / 0.05 s), flick with Fitts-law duration, overshoot sometimes, lead imperfectly, aim tightens while held on target (focus) and loosens on big turns.
- Halo habits. Shoot body until shields pop, then head. Grenade before engaging when it can. Back off to recharge shields when cracked. Strafe with randomised reversal timing; jump shots and crouch at the kill by personality.
- Callouts are late and fuzzy. Delivered 0.5 to 2.5 s after the report, counts fuzzed ("two, maybe three"), named areas, expire after 6 s.
- Not a hive mind. Each bot has a teamwork value; low-teamwork bots sometimes ignore orders.

## Interface to the game

Every tick the game layer (DLL, later) hands the brain a `Snapshot`: players (id, team, position, velocity, facing, alive, shield, health, weapon, holding flag), flags (home, carried, dropped, position), score and time. The brain returns one `Action` per bot: forward and strafe throttle (-1 to 1), desired yaw and pitch, and buttons (fire, jump, crouch, grenade, melee, action, reload). That matches Halo CE's `player_action` (throttle, facing, control flags), so the DLL only copies it into the bot's action slot.

The offline simulator (`brain/sim.py`) produces the same snapshots for Blood Gulch, so the brain and director are tested before the game hook exists.
