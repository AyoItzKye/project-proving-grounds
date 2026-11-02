# Human play data

Recorded play of a skilled person against and with the bots, shared so that anyone (people, or their own tools and AI)
can study how people play Halo and how the bots compare, and make bots better. It is the data this project's
difficulties, reaction times, aim and movement were tuned against.

Two places:

- **In the repository:** `maps/_human/reference.json` (the skilled player's numbers: reaction, aim, movement,
  positioning, grenades, strafing ...) and `maps/_human/gold.json` (per map, the same numbers for the person and for
  each bot difficulty in reference matches). `tools/player_stats.py` computes these numbers from any recording.
- **On the Releases page:** `human-play-data-<version>.zip`, the recordings themselves (below).

## What is in the zip

| Folder | What |
|---|---|
| `collect/` | Data collector recordings (`collect_<map>_<date>-<time>.jsonl`): a person playing, with every player's position every tick and the person's aim, guns and rounds. Halo: CE, Halo 2, Halo 2 Anniversary, Halo 3, Halo: Reach and Halo 4 matches, with and without bots. |
| `matches/` | full recorded matches with bots as the Observer's export makes them: each zip holds `manifest.json` (the game, map, modes, score, every player marked human or bot), the brain's recording (`trace.jsonl`: everyone 4 times a second, every bot every tick with its decisions), the person's Data collector recording when it was on, MCC's post-game report and the Observer's analyses. Each zip's `manifest.json` lists the format of every row. |
| `human/` | `reference.json` and `gold.json` as in the repository |

The Observer (from the launcher) opens a match zip with **Import game**; `python -I tools\player_stats.py <file>`
gives a recording's numbers.

## How it was anonymized

- Gamertags, clan tags and service tags are replaced by "Player 1", "Player 2" ... (bots keep their made-up names).
- Xbox user ids are removed.
- The Windows user folder in any file path is replaced by `<home>`.
- Every file was scanned for e-mail addresses, user folders, local drive paths and the recorder's own names and ids
  before it went in (`tools/human_data.py`, `tools/make_release.py`); the build stops on any hit.
- No keys: the keyboard, mouse and controller are not in the data (the Data collector reads only the game; the key
  rows the first version also recorded were left out of this zip).

## Data collector rows (`collect/*.jsonl`)

One JSON object per line; `t` is seconds since the match started.

| Row | Fields |
|---|---|
| start (once) | `{"t", "collect": "start", "map", "game"}`: the map and the game |
| players (every tick, 30 a second) | `{"t", "p": [row per player]}`. Row: 0 player id, 1 team, 2 alive, 3-5 x y z (world units), 6 yaw, 7 pitch (radians), 8 shield, 9 health (1 = full), 10 riding a vehicle, 11 carrying the flag, 12 bot (1) or person (0); a person's row adds 13 what the crosshair is on `[x, y, z, on]` (on: a player id, `"v<handle>"` for a vehicle, null for the level; null when only sky) and 14 the seat `[vehicle kind, gun]` (null on foot) |
| gear (on change) | `{"t", "id", "wpn", "inv", "ammo", "mag", "eq", "ab", "uz"}`: a person's gun in hand, guns carried, rounds, magazine, equipment, armor ability, zoom (a shot: the magazine of the gun in hand going down) |

## Related studies in the repository

- Vehicles: `maps/_vehicles/` (how far from walls a person drives each vehicle, measured from recorded drives, which
  the bots' driving follows) and `docs/bot-brain/04-vehicle-deep-dives.md`.
- Objectives: `docs/research/12-team-objective-play.md` and `docs/bot-brain/07-game-mode-playbooks.md`; every match zip
  carries `objective_report.txt` (`tools/objective_report.py`: flag runs, captures, holds, who did what).
- How people play: `docs/research/05-how-humans-play-halo.md`, `docs/research/14-legendary-target.md`.

## License

The same as the project: [PolyForm Noncommercial License 1.0.0](../LICENSE.md). Use it freely for any noncommercial
purpose; selling it or earning money from it is not permitted.
