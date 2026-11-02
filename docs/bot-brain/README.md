# Halo MCC PvP Bot Brain — Rules of Engagement (guide pack)

Markdown export of the Claude Doc, split one file per tab. Drop the folder into your repo (for example `docs/bot-brain/`) and reference it from `CLAUDE.md` so Claude Code can read the rules while scripting the bots.

| File | What it holds |
| --- | --- |
| 01-rules-of-engagement.md | Main guide: range model, fundamentals, per-game differences, weapon/vehicle/equipment ROE tables, map power spots and timers, mode logic summary, skill tiers and play styles, the bot decision stack, the two scenario libraries, pro habits and sources |
| 02-advanced-techniques.md | Per-game techniques: CE pistol/grenade play, H2 button combos and sword flying, H3 BR control and equipment, Reach bloom/abilities, H4 sprint/thruster/ordnance, cross-game strafing, peeks, de-scoping, radar, jumps |
| 03-weapon-deep-dives.md | Precision, automatic, CQB, sniper, explosive and support weapons in depth, plus the grenade throw table |
| 04-vehicle-deep-dives.md | Warthog family, light vehicles, heavy vehicles, air, and boarding/hijacking |
| 05-map-playbooks.md | Callouts, openings, setups, grenade spots and jumps for the key maps in every MCC title |
| 06-mechanics-and-spawn-research.md | Tag-sourced player stats, the Halo 3 damage model, the Halo 3 spawn-weighting system, competitive settings, red reticle range |
| 07-game-mode-playbooks.md | Every game mode in depth: Slayer family, CTF family, Oddball/KOTH/Headhunter/Ricochet, Assault/Territories/Dominion/Extraction/Stockpile/Invasion, Infection/Juggernaut/VIP/Regicide/Grifball/Race, ODST Firefight, Reach Firefight |
| 08-equipment-and-abilities.md | H3 equipment, Reach and H4 armor abilities, perks, powerups: basics, sneaky tricks, counters, bot rules |

Suggested `CLAUDE.md` line:

> Bot behaviour rules live in `docs/bot-brain/`. Read `01-rules-of-engagement.md` first (sections 10–12 are the decision stack and scenario rules), then the tab matching the task (weapons, vehicles, maps, modes, mechanics). Treat every "Situation → Decision → Why" row as a condition/action pair; the Why text is the generalisation rule.
