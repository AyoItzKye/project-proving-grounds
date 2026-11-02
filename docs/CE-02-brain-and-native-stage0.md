# CE-02 - Brain, directors, Ollama coach, native stage 0

Date: 2026-10-21 night. Design: `docs\BRAIN-DESIGN.md`.

## Built and tested

| Part | Files | How it was checked |
|---|---|---|
| Bot brain: perception with reaction delay and memory, motion tracker, human aim (re-aim interval, Fitts flicks, overshoot, focus), decisions (fight, retreat while shooting, objective, hunt, hold), Halo habits (shield then head, grenade openers, strafe reversals, jump shots, crouch at the kill), runner and carrier rules | `brain\bot.py`, `brain\profiles.py` (4 tiers x 7 personalities) | offline sim self-check |
| Team director: delayed fuzzy callouts by named area, CTF roles (runner on separate lanes, escort, defender, hunter, push group), threat pull-back to a threatened flag, rogue moments | `brain\director.py`, `brain\maps.py` | offline sim self-check |
| Ollama coach: stance, defender count, team chat line every 15 s in a background thread, validated and clamped | `brain\strategist.py` | sim with `--ollama`: 4 answers, 2.6 to 5.9 s each, valid JSON |
| Offline Blood Gulch sim (same interface as the game hook) | `brain\sim.py` | `python -m brain.sim` from the project folder; ends with `self-check OK` |
| Read-only memory reader (Blam data arrays, HCM 1.3528 pointers, refuses with anti-cheat running) | `tools\memread.py` | found a planted `players` header in a test process |
| botcore.dll stage 0 (loads, refuses with anti-cheat, shared memory link, heartbeat, log) and inject.exe (refuses with anti-cheat) | `native\` (`build.bat` -> `native\bin`) | built with VS 2022 Build Tools; DLL heartbeat at 30 Hz in a test host; injector exits cleanly when MCC is not running |

Latest sim run (`python -m brain.sim --seconds 600`):

- Slayer 4v4, 300 s: 28 kills; accuracy novice 40% (small sample), average 25%, strong 41%, top 66%.
- CTF 8v8, 600 s: 324 kills, 958 callouts, no captures. The flat sim has no cover, so mid is a constant firefight. This is a sim limit; judge CTF flow in the game.
- CTF 3v1, 400 s: flag taken twice, one capture.
- Callout delays all within 0.5 to 2.5 s.

## Known gaps

- Top-tier accuracy (63 to 77% in the sim) is probably too high for Halo; tune once there is real telemetry from the player's games.
- `decide()` reads enemy shield and health to judge a trade. Humans see shield flares, so this is a fair approximation, but it should become "what the shield effect shows".
- Blood Gulch areas, holds and lanes are first-pass guesses around the community flag coordinates. Replace them with values read from the scenario tag in-game.
- Navigation is straight lines in the sim. In-game it will use Halo's own pathfinding (the halo-64 approach).

## Not done: live test

MCC was not launched because the player was playing LastEvil full screen. Next live session, in order:
1. Start MCC with anti-cheat disabled, run a Blood Gulch custom game.
2. `python -I tools\memread.py arrays` and `players`: get the player table, element size and layout.
3. `native\bin\inject.exe`: confirm `botcore.log` shows `halo1.dll at ...`.
4. Use Ghidra (analysis finished, project `ghidra\mcc_1_3528`) and x64dbg to find player creation and the per-tick action path, then add the bot player hook.
