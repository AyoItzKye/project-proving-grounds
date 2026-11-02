"""Score-limit and time-limit fields by elimination: in a match whose lobby was set to a known score to win
and time limit, save every TLS-block cell holding those values (int16 and byte); in a second match set to
other values, keep the cells that changed accordingly. (found Reach's +0x10D28 / +0x17A6 so).

usage: python -I limit_candidates.py save <game> <score> <minutes>      (logs/_limits_<game>.json)
       python -I limit_candidates.py check <game> <score> <minutes>
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_counters as fc  # noqa: E402

LOGS = os.path.join(HERE, "..", "logs")


def cells(game, score, minutes):
    g, regions = fc.tls_regions(game, 0x40000)
    out = {}
    for name, base, size in regions:
        b = np.frombuffer(g.read(base, size) or b"", dtype=np.uint8)
        s16 = b[: len(b) // 2 * 2].view("<i2")
        out[name] = dict(base=base, s=[int(k * 2) for k in np.nonzero(s16 == score)[0]],
                         m=[int(k) for k in np.nonzero(b == minutes)[0]], data=None)
    return g, out


def main():
    mode, game, score, minutes = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    path = os.path.join(LOGS, f"_limits_{game}.json")
    if mode == "save":
        g, out = cells(game, score, minutes)
        json.dump(out, open(path, "w"))
        print({k: (len(v["s"]), len(v["m"])) for k, v in out.items() if v["s"] or v["m"]})
        return
    old = json.load(open(path))
    g, regions = fc.tls_regions(game, 0x40000)
    for name, base, size in regions:
        if name not in old:
            continue
        b = g.read(base, size) or b""
        ks = [k for k in old[name]["s"] if k + 2 <= len(b) and int.from_bytes(b[k:k + 2], "little", signed=True) == score]
        km = [k for k in old[name]["m"] if k < len(b) and b[k] == minutes]
        if ks or km:
            print(f"{name} (base {base:#x}): score to win at {[hex(k) for k in ks]}, minutes at {[hex(k) for k in km]}")


if __name__ == "__main__":
    main()
