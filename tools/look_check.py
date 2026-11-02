"""Do the bots in a running match wear what brain/looks.py gave them? Halo 3: each bot's look bytes (from its name and
native/bin/bot_profiles.ini) next to its body's region permutations (tools/look_regions.py). Halo 4 / H2A (an Armory
roll, botcore s83): each bot's worn regions read back from its body's copy of the appearance block (biped +0x129C =
configuration +0x48..). Read only, unless --add N: first add N of the install's bots with their looks, each on its own
team (free for all), as tools/play.py would.

usage: python -I look_check.py [--game h3|h4|h2a] [--add N]
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
from brain import looks  # noqa: E402
from look_dump import live_for  # noqa: E402

SPARTAN = {"helmet": (70, 4), "Lshoulder": (71, 5), "Rshoulder": (72, 7), "chest": (73, 2), "arms": (74, 0),
           "legs": (75, 6), "techsuit": (76, 1)}          # Halo 3: config byte, region column (look_regions.py order)
F_REGIONS = ["helmet", "chest", "r2", "shoulderA", "shoulderB", "forearms", "legs", "r7"]   # Halo 4 regions 0-7


def add(game, n):
    m = botctl.shm()
    live = live_for(game)
    taken = {p["name"].lower() for p in live.players()}
    n = min(n, botctl.player_cap(game) - len(taken))         # ODST holds 4 players (botctl.player_cap)
    names = [nm for nm, _ in looks.profiles() if nm.lower() not in taken][:max(0, n)]
    machine = 1 + max(p["index"] for p in live.players())
    for k, nm in enumerate(names):
        team = k % 2 if "--teams" in sys.argv else 1 + k % 7
        r = botctl.add_bot(m, machine, team, nm, game, look=looks.look(nm, game), clan=looks.clan_of(nm),
                           emblem=looks.emblem_of(nm))
        print("added", nm, r.get("result"))
        machine += 1
        time.sleep(0.3)
    time.sleep(3)


def check_h3(live):
    bad = 0
    for p in live.players()[1:]:
        lk = looks.look(p["name"], "h3")
        o = live.object(p["unit"]) if p.get("unit") is not None else None
        if not lk or not o:
            print(p["name"], "no look" if not lk else "no body")
            continue
        off, b = lk
        a = {off + k: v for k, v in b.items()}
        if a.get(60) == 1:
            print(f"{p['name']:<16} Elite  colours {a[57]},{a[58]},{a[59]}")
            continue
        reg = live.g.read(o + 0x11B0, 64)
        row = []
        for name, (at, col) in SPARTAN.items():
            want, got = a.get(at, 0), reg[8 * col]
            miss = want != 0 and got == 0
            bad += miss
            row.append(f"{name} {want}->{got}{'!' if miss else ''}")
        print(f"{p['name']:<16} " + "  ".join(row))
    print("looks arrived" if not bad else f"{bad} pieces asked for but not worn")


def check_f(live):
    """Halo 4 / H2A: the worn regions of every player; the bots should differ from each other and the player."""
    rows = {}
    print("player".ljust(14) + " ".join(r[:9].rjust(9) for r in F_REGIONS) + "  effect")
    for p in live.players():
        o = live.object(p["unit"]) if p.get("unit") is not None else None
        if not o:
            print(p["name"].ljust(14), "no body")
            continue
        b = live.g.read(o + 0x129C, 0x1C)
        regions, effect = tuple(b[0x10:0x18]), b[0x18]
        rows[p["name"]] = regions
        print(p["name"].ljust(14) + " ".join(str(v).rjust(9) for v in regions) + f"  {effect}")
    bots = [r for n, r in rows.items() if n != live.players()[0]["name"]]
    print(f"{len(set(bots))} different looks among {len(bots)} bots")


def main():
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "h3"
    if "--add" in sys.argv:
        add(game, int(sys.argv[sys.argv.index("--add") + 1]))
    live = live_for(game)
    check_h3(live) if game == "h3" else check_f(live)


if __name__ == "__main__":
    main()
