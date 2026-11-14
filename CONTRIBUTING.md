# Contributing

Thanks for helping make the bots better. Everything here is free and noncommercial: by contributing you agree that
your contribution is shared under this project's [PolyForm Noncommercial License 1.0.0](LICENSE.md).

## Reporting a problem

1. In the match, press **F9** right when it happens and type what went wrong: the report is saved with the recording
   around it in `logs\bug_reports\<date-time>` (the launcher's **Open the install folder**).
2. Open an issue on GitHub with what you expected, what happened, and the game, map, mode and difficulty. Attach the
   report folder zipped, or the Observer's **Export game** zip of that match (names and Xbox ids are removed).
3. Also useful: the version (top of the launcher) and `logs\brain.txt`.

Attachments are opened only after a malware scan, and only bug reports, match recordings and screenshots are looked at.
Please do not attach programs, scripts or modified mod files.

## Suggesting a fix or a feature

Ideas, explanations of how a game type should be played, and pointers to where a bug comes from are very welcome:
open an issue and describe them in words. They steer the fix.

Code from outside the project is not merged. Every change to the mod is written and tested here, so that one change
cannot break something else and nothing unchecked reaches other players' PCs. Pull requests are read for their idea
and then closed; the change is made in the project's own code.

## Data contributions

Recorded matches help calibrate the bots against people. Share them as the Observer's **Export game** zips (names
replaced, Xbox ids removed); say in the issue which game, map and mode, and whether the person was skilled.

## Working on your own copy

For your own experiments, see [docs/CODE_GUIDE.md](docs/CODE_GUIDE.md#building-from-source) for building from source.
Never add anything that works online, in matchmaking, or with anti-cheat on.
