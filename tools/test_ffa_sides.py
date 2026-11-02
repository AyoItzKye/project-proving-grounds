"""Directors by team, side or bot (tools/live_bots.py regroup): Infection and Juggernaut lobbies have teams off, so a free
for all is split into its two sides, each with one director.

1. A team game: one director per game team (Green is not Red); a plain free for all: one per bot.
2. Infection (brain/modes.py split: snap.infected 1, survivors team 0, infected 1): two directors, survivors and
   infected; a survivor infected moves to the infected side's director (both rebuilt), the others stay as they are
   when nothing changed (no rebuild every tick).
3. Juggernaut (the same split: hunters 0, the Juggernaut 1): two sides.
4. A bot's death report finds its director whatever the keying (events: it looked up ("bot", id) or the game team,
   so a side's bots reported to nobody).

usage: python -I test_ffa_sides.py      -> "ffa_sides OK (...)"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(0, HERE)
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []


class Dir:
    def __init__(s, k, members):
        s.k, s.bots, s.reports = k, dict(members), []

    def report(s, now, index, kind, pos, **kw):
        s.reports.append((index, kind))


def setup(teams, tiers=None):
    from brain.maps import get_map
    m = get_map("bloodgulch")
    rng = random.Random(1)
    bots, players = {}, []
    for i, t in enumerate(teams):
        b = Bot(i, t % 2, make_profile((tiers or ["top"] * len(teams))[i], "rusher", rng), m, random.Random(i))
        b.game_team = t
        bots[i] = b
        players.append(PlayerState(i, t, f"b{i}", Vec(i, 0, 0)))
    return bots, Snapshot(0.0, players)


def main():
    import live_bots as L
    made = []

    def make(k, members):
        made.append(k)
        return Dir(k, members)

    # 1. team game: by game team (three teams); plain free for all: by bot
    bots, snap = setup([0, 1, 2, 0])
    dirs = L.regroup({}, bots, snap, False, make)
    if sorted(dirs) != [0, 1, 2] or set(dirs[0].bots) != {0, 3}:
        fails.append(f"team game: {sorted(dirs)} {set(dirs[0].bots) if 0 in dirs else None}")
    bots, snap = setup([0, 1, 2, 3])
    dirs = L.regroup({}, bots, snap, True, make)
    if sorted(dirs) != [("bot", i) for i in range(4)]:
        fails.append(f"plain free for all: {sorted(dirs)}")
    # 2. Infection: the game's teams 0..5 (free for all), split by brain/modes.py into survivors 0 and infected 1
    bots, snap = setup([0, 1, 2, 3, 4, 5])
    dirs = L.regroup({}, bots, snap, True, make)
    for p in snap.players:
        p.team = 1 if p.id == 5 else 0
    snap.infected = 1
    made.clear()
    L.regroup(dirs, bots, snap, True, make)
    if sorted(dirs, key=str) != [("side", 0), ("side", 1)] or set(dirs[("side", 0)].bots) != {0, 1, 2, 3, 4}:
        fails.append(f"Infection: directors {sorted(dirs, key=str)}")
    made.clear()
    L.regroup(dirs, bots, snap, True, make)
    if made:
        fails.append(f"Infection: directors rebuilt with nothing changed: {made}")
    snap.players[2].team = 1                              # a survivor infected
    survivors = dirs[("side", 0)]
    L.regroup(dirs, bots, snap, True, make)
    if set(dirs[("side", 1)].bots) != {2, 5} or 2 in dirs[("side", 0)].bots or dirs[("side", 0)] is survivors:
        fails.append(f"Infection: the newly infected bot's director: {set(dirs[('side', 1)].bots)}")
    # 4. its death report reaches its side's director
    before = {p.id: PlayerState(p.id, p.team, p.name, p.pos) for p in snap.players}
    snap.players[2].alive = False
    bots[2].goal = ("fight", 0)
    L.events(bots, dirs, before, snap, 1.0)
    if (2, "died") not in dirs[("side", 1)].reports:
        fails.append(f"Infection: the death report of a side's bot went nowhere ({dirs[('side', 1)].reports})")
    # 3. Juggernaut: two sides
    bots, snap = setup([0, 1, 2, 3], tiers=["novice", "novice", "novice", "top"])
    for p in snap.players:
        p.team = 1 if p.id == 3 else 0
    snap.infected = 1
    dirs = L.regroup({}, bots, snap, True, make)
    if sorted(dirs, key=str) != [("side", 0), ("side", 1)]:
        fails.append(f"Juggernaut: {sorted(dirs, key=str)}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("ffa_sides OK (team games by team, plain free for all by bot, Infection and Juggernaut by side, rebuilt only "
          "on a change, reports reach a side's director)")


if __name__ == "__main__":
    try:
        main()
    except (AttributeError, ImportError) as e:       # (live_bots before: no director_key / regroup)
        sys.exit(f"FAIL\n{type(e).__name__}: {e}")
