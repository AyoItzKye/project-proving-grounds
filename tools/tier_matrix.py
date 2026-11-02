"""The difficulty pyramid.

Every pair of tiers, one team of each, in the offline sim (brain/sim.py): Team Slayer on maps of several games plus one
objective mode (King of the Hill by default), every seed played from both sides (a map's sides are not even). Per pair:
the higher tier's wins (a draw half), its share of the kills, both tiers' accuracy. Per tier:
  difficulty %  its mean win rate against the three other tiers (each pair weighs the same)
  Elo           Bradley-Terry from every game (a draw half a win each way, one virtual draw a pair so a clean sweep
                stays finite), scaled to Elo points with Easy at 1000
Clean pyramid = Easy < Normal < Heroic < Legendary by difficulty %, each step at least STEP points, and every higher
tier winning over half its games against every lower one.

usage: python -I tier_matrix.py [--seconds 180] [--seeds 2] [--maps bloodgulch,h3_construct,...] [--modes slayer,king]
                                [--obj-maps h3_construct,reach_30_settlement] [--per-team 4] [--procs 2] [--mirrors]
       -> a table per run, and logs/tier_matrix.md (one block per run) and logs/tier_matrix.json (the games)
"""
import argparse
import itertools
import json
import math
import multiprocessing
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

TIERS = ["novice", "average", "strong", "top"]        # Easy, Normal, Heroic, Legendary
NAME = dict(novice="Easy", average="Normal", strong="Heroic", top="Legendary")
STEP = 5.0     # difficulty % points each tier must clear the one under it by ("each step clear")
SLAYER_MAPS = "bloodgulch,h2_beavercreek,h3_construct,h3_cyberdyne,reach_30_settlement,h4_ca_warhouse,h2a_ca_lockout"
OBJ_MAPS = "h3_construct,reach_30_settlement"


def play(job):
    """One match, `hi` on hi_team and `lo` on the other: its numbers."""
    lo, hi, mode, map_name, seed, seconds, n, hi_team = job
    from brain.sim import Sim
    sim = Sim(mode, per_team=n, seed=seed, map_name=map_name, tiers={hi_team: [hi], 1 - hi_team: [lo]})
    sim.limit = 10 ** 6                         # time decides, not a score limit
    sim.run(seconds)
    k = {0: 0, 1: 0}
    acc = {}
    for pid, st in sim.stats.items():
        k[sim.bots[pid].team] += st["kills"]
        a = acc.setdefault(st["tier"], [0, 0])
        a[0] += st["hits"]
        a[1] += st["shots"]
    hs, ls = sim.score[hi_team], sim.score[1 - hi_team]
    return dict(lo=lo, hi=hi, mode=mode, map=map_name, seed=seed, hi_team=hi_team, hk=k[hi_team], lk=k[1 - hi_team],
                hs=hs, ls=ls, win=1.0 if hs > ls else 0.5 if hs == ls else 0.0, acc=acc)


def elo(games):
    """Bradley-Terry strengths by its MM iteration, as Elo points (Easy 1000)."""
    w = {(a, b): 0.5 for a in TIERS for b in TIERS if a != b}       # one virtual draw a pair
    for g in games:
        if g["lo"] != g["hi"]:
            w[(g["hi"], g["lo"])] += g["win"]
            w[(g["lo"], g["hi"])] += 1.0 - g["win"]
    n = {(a, b): w[(a, b)] + w[(b, a)] for a, b in w}
    p = {t: 1.0 for t in TIERS}
    for _ in range(500):
        p = {i: sum(w[(i, j)] for j in TIERS if j != i) / sum(n[(i, j)] / (p[i] + p[j]) for j in TIERS if j != i)
             for i in TIERS}
    return {t: round(1000 + 400 * math.log10(p[t] / p["novice"])) for t in TIERS}


def pyramid(games):
    """(difficulty % by tier, Elo by tier, problems [text])."""
    rate = {}
    for a, b in itertools.permutations(TIERS, 2):
        gs = [g for g in games if {g["lo"], g["hi"]} == {a, b} and g["lo"] != g["hi"]]
        if gs:
            rate[(a, b)] = sum(g["win"] if g["hi"] == a else 1.0 - g["win"] for g in gs) / len(gs)
    pct = {t: round(100 * sum(rate[(t, o)] for o in TIERS if (t, o) in rate) / max(1, sum((t, o) in rate for o in TIERS)), 1)
           for t in TIERS}
    bad = []
    for lo, hi in itertools.combinations(TIERS, 2):
        if (hi, lo) in rate and rate[(hi, lo)] <= 0.5:
            bad.append(f"{NAME[hi]} wins only {100 * rate[(hi, lo)]:.0f}% against {NAME[lo]}")
    for lo, hi in zip(TIERS, TIERS[1:]):
        if pct[hi] - pct[lo] < STEP:
            bad.append(f"{NAME[hi]} {pct[hi]}% is not {STEP:g}+ over {NAME[lo]} {pct[lo]}%")
    return pct, elo(games), bad


def block(games, label):
    """The markdown for a set of games: pair rows, the tiers, the verdict."""
    rows = []
    for lo, hi in itertools.combinations_with_replacement(TIERS, 2):
        gs = [g for g in games if g["lo"] == lo and g["hi"] == hi]
        if not gs:
            continue
        hk, lk = sum(g["hk"] for g in gs), sum(g["lk"] for g in gs)
        acc = {}
        for g in gs:
            for t, (x, y) in g["acc"].items():
                a = acc.setdefault(t, [0, 0])
                a[0] += x
                a[1] += y
        ra = lambda t: acc[t][0] / max(acc[t][1], 1)
        wins = sum(g["win"] for g in gs)
        rows.append(f"| {NAME[hi]} vs {NAME[lo]} | {100 * wins / len(gs):.0f}% ({wins:g}/{len(gs)}) | "
                    f"{hk / max(hk + lk, 1):.2f} | {hk}-{lk} | {ra(hi):.2f} / {ra(lo):.2f} |")
    pct, el, bad = pyramid(games)
    tiers = "\n".join(f"| {NAME[t]} | {pct[t]}% | {el[t]} |" for t in TIERS)
    verdict = "CLEAN PYRAMID" if not bad else "NOT a clean pyramid: " + "; ".join(bad)
    return (f"### {label}\n\n| pair (higher vs lower) | higher's wins | higher's kill share | kills | accuracy higher / "
            f"lower |\n|---|---|---|---|---|\n" + "\n".join(rows) +
            f"\n\n| tier | difficulty % (mean win rate vs the others) | Elo (Easy 1000) |\n|---|---|---|\n{tiers}\n\n"
            f"{verdict}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=180)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--maps", default=SLAYER_MAPS, help="Team Slayer maps")
    ap.add_argument("--modes", default="slayer,king")
    ap.add_argument("--obj-maps", default=OBJ_MAPS, help="the objective modes' maps")
    ap.add_argument("--per-team", type=int, default=4)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--mirrors", action="store_true", help="also tier against itself (a map's side bias)")
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "tier_matrix.md"))
    a = ap.parse_args()
    if os.name == "nt":                         # below normal: a live match's brain may be running beside it
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    pairs = list(itertools.combinations_with_replacement(TIERS, 2) if a.mirrors else itertools.combinations(TIERS, 2))
    jobs = []
    for mode in a.modes.split(","):
        maps = (a.maps if mode == "slayer" else a.obj_maps).split(",")
        jobs += [(lo, hi, mode, m, seed, a.seconds, a.per_team, side)
                 for (lo, hi), m, seed, side in itertools.product(pairs, maps, range(1, a.seeds + 1), (0, 1))]
    t0 = time.monotonic()
    print(f"{len(jobs)} games on {a.procs} processes", flush=True)
    games = []
    with multiprocessing.Pool(a.procs, maxtasksperchild=1) as pool:   # (a fresh process a game: maps.py caches every map)
        for g in pool.imap_unordered(play, jobs):
            games.append(g)
            print(f"{NAME[g['hi']]:9s} vs {NAME[g['lo']]:9s} {g['mode']:7s} {g['map']:20s} seed {g['seed']} side "
                  f"{g['hi_team']}: score {g['hs']}-{g['ls']} kills {g['hk']}-{g['lk']}", flush=True)
    out = (f"\n## {time.strftime('%Y-%m-%d %H:%M')} tier matrix: {a.per_team} v {a.per_team}, {a.seconds:.0f} s, "
           f"{a.seeds} seeds x both sides, {len(games)} games ({time.monotonic() - t0:.0f} s wall)\n"
           f"Slayer maps: {a.maps}; objective maps: {a.obj_maps}\n\n")
    out += block(games, "all modes")
    for mode in a.modes.split(","):
        out += "\n" + block([g for g in games if g["mode"] == mode], mode)
    with open(a.out, "a", encoding="utf-8") as f:
        f.write(out)
    with open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(games, f)
    print(out)


if __name__ == "__main__":
    main()
