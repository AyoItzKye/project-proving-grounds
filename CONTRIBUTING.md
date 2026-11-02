# Contributing

Thanks for helping make the bots better. Everything here is free and noncommercial: by contributing you agree that
your contribution is shared under this project's [PolyForm Noncommercial License 1.0.0](LICENSE.md).

## Reporting a problem

1. In the match, press **F9** right when it happens and type what went wrong: the report is saved with the recording
   around it in `logs\bug_reports\<date-time>` (the launcher's **Open the install folder**).
2. Open an issue on GitHub: what you expected, what happened, the game, map, mode and difficulty, and attach the
   report folder zipped, or the Observer's **Export game** zip of that match (names and Xbox ids are removed).
3. Also useful: the version (top of the launcher) and `logs\brain.txt`.

## Suggesting a change

Open an issue first for anything bigger than a small fix, so the approach can be agreed before work starts.

## Pull requests

- Set up a developer copy: [docs/CODE_GUIDE.md](docs/CODE_GUIDE.md#building-from-source).
- Keep a pull request to one change. Match the code around it: naming, comment density, idioms.
- Comments explain what the code does and why. Numbers carry their units and where they came from (a measurement,
  a game's tag, a recorded match).
- Every change to the bots' logic comes with a test in `tools\test_*.py` that fails without it, and
  `python -I tools\run_tests.py` passes.
- A fix to how the bots play is judged on recorded matches (the Observer), not only offline.
- No personal data in code, tests or data files: no gamertags, Xbox ids, local paths or e-mail addresses.
  `python -I tools\make_release.py --scan <folder>` checks a folder.
- Never add anything that works online, in matchmaking, or with anti-cheat on.

## Data contributions

Recorded matches help calibrate the bots against people. Share them as the Observer's **Export game** zips (names
replaced, Xbox ids removed); say in the issue which game, map and mode, and whether the person was skilled.
