"""Match the zoom each bot asked (trace cmd bits 12-13) to the game's own zoom byte one tick later (trace "uz", written
since 93c1dad for CE / Halo 2 / Halo 3): the game takes a request on the next tick. Asked 0 / 1 / 2 should read
0xFF / 0x00 / 0x01.

usage: python -I zoom_match.py logs\\trace_<map>_<stamp>.jsonl
"""
import collections
import json
import os
import sys

WANT = {0: 0xFF, 1: 0x00, 2: 0x01}


def main():
    recs = collections.defaultdict(list)
    for line in open(sys.argv[1], encoding="utf-8"):
        r = json.loads(line)
        if "cmd" in r and "id" in r and "uz" in r:
            recs[r["id"]].append(r)
    if not recs:
        sys.exit("no records with uz: a trace from before 93c1dad, or a game without UNIT_ZOOM")
    pairs, asked_by_weapon, first = collections.Counter(), collections.Counter(), {}
    for b, rs in recs.items():
        for k, nxt in zip(rs, rs[1:]):
            if nxt["t"] - k["t"] > 0.1:
                continue                                  # a gap (death, respawn): no next tick to compare
            asked = (k["cmd"][3] >> 12) & 3
            pairs[(asked, nxt["uz"] == WANT[asked])] += 1
            if asked:
                asked_by_weapon[k["wpn"]] += 1
                first.setdefault(b, round(k["t"], 1))
    out = [f"trace: {sys.argv[1]}"]
    for asked in (0, 1, 2):
        ok, bad = pairs[(asked, True)], pairs[(asked, False)]
        if ok or bad:
            out.append(f"asked {asked} (want {WANT[asked]:#04x} next tick): {ok} match, {bad} differ ({ok / (ok + bad):.1%})")
    out.append(f"zoom asked, ticks by weapon: {dict(asked_by_weapon)} | first ask per bot (s): {first}")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "verify",
                        "zoom_match_" + os.path.basename(sys.argv[1]).replace(".jsonl", ".txt"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(chr(10).join(out) + chr(10))
    print(chr(10).join(out))
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
