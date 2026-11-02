"""The measuring tools' own logic (tools/mode_matrix.py, tools/tier_matrix.py):

1. mode_matrix: whose objective event it is ("team 1 took territory 3", "R2-top-flanker took the ball", "attackers took
   phase 1 (territory 0)") and its kind without the zone number; a row's verdict is the worst of its seeds, "one-sided"
   when a team never scored; one real 30 s run gives every field
2. tier_matrix: a clean synthetic ladder reads CLEAN (difficulty % rising, Elo rising, a sweep's Elo finite); Normal and
   Heroic swapped, or a 2-point step, is reported

usage: python -I test_matrices.py      -> "matrices OK (...)"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import mode_matrix as MM  # noqa: E402
import tier_matrix as TM  # noqa: E402


def ladder(p):
    """Games where tier i beats tier j (i above j) with probability p[(j, i)], 20 games a pair, both sides."""
    games = []
    for lo, hi in [(a, b) for k, a in enumerate(TM.TIERS) for b in TM.TIERS[k + 1:]]:
        wins = round(20 * p[(lo, hi)])
        games += [dict(lo=lo, hi=hi, win=1.0 if k < wins else 0.0) for k in range(20)]
    return games


def main():
    fails = []
    # 1
    for text, side, kind in (("team 1 took territory 3", 1, "took territory"), ("R2-top-flanker took the ball", 0, "took the ball"),
                             ("B0-top-camper banked skulls", 1, "banked skulls"),
                             ("attackers took phase 1 (territory 0)", 1, "took phase 1"),
                             ("team 0 killed the VIP", 0, "killed the VIP"), ("the hill moved to 2", None, None)):
        if MM.side_of(text) != side or (kind is not None and MM.kind_of(text) != kind):
            fails.append(f"1 {text!r}: side {MM.side_of(text)}, kind {MM.kind_of(text)!r}")
    run = lambda v, score: dict(mode="ctf", map="bloodgulch", score=score, ppm=[0, 0], kpm=[3, 3], takes={},
                                share=dict(fight=.2, obj=.2, walk=.4, idle=.1, stuck=.1), verdict=v)
    row = MM.rows_of([run("SCORING", [1, 0]), run("AGGRESSIVE", [0, 0])])[0]
    if row["verdict"] != "AGGRESSIVE" or "one-sided" in row["notes"]:
        fails.append(f"1 worst seed: {row['verdict']} {row['notes']}")
    row = MM.rows_of([run("SCORING", [1, 0]), run("SCORING", [2, 0])])[0]
    if row["verdict"] != "SCORING" or row["notes"] != ["one-sided"]:
        fails.append(f"1 one-sided: {row['verdict']} {row['notes']}")
    r = MM.play(("king", "h3_construct", 1, 30.0, 2, "top"))
    if set(r) < {"score", "ppm", "kpm", "takes", "share", "verdict"} or abs(sum(r["share"].values()) - 1) > 0.01 \
            or "hill s" not in r["takes"]:
        fails.append(f"1 a run's fields: {r}")
    # 2
    good = {("novice", "average"): .75, ("novice", "strong"): .85, ("novice", "top"): 1.0,
            ("average", "strong"): .7, ("average", "top"): .85, ("strong", "top"): .7}
    pct, el, bad = TM.pyramid(ladder(good))
    if bad or not pct["novice"] < pct["average"] < pct["strong"] < pct["top"] or \
            not el["novice"] < el["average"] < el["strong"] < el["top"] < 3000:
        fails.append(f"2 clean ladder read {pct} {el} {bad}")
    swapped = {**good, ("average", "strong"): .3}
    pct2, el2, bad2 = TM.pyramid(ladder(swapped))
    if not any("Heroic wins only" in b for b in bad2):
        fails.append(f"2 Heroic under Normal not reported: {bad2}")
    flat = {k: (.52 if k == ("average", "strong") else v) for k, v in good.items()}
    flat[("novice", "strong")], flat[("strong", "top")] = .75, .85
    pct3, _, bad3 = TM.pyramid(ladder(flat))
    if pct3["strong"] - pct3["average"] >= TM.STEP or not any("is not" in b for b in bad3):
        fails.append(f"2 a small step not reported: {pct3} {bad3}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"matrices OK (clean ladder {pct}, Elo {el}; swapped -> {bad2[0]}; 30 s King run {r['verdict']})")


if __name__ == "__main__":
    main()
