"""Where a CTF carrier scores (brain/maps.py "returns", Director.capture_point). Live, Avalanche Multi Flag: the carriers
stood 9 s on their own stand with their own flag home and never scored (the game's carnage report: every score 0):
Avalanche's "CTF flag return" points sit 7.8 u off the stands on the floor below, and the 3 u rule dropped them, so the
brain sent carriers to the stand.

1. h3_sidewinder (Avalanche): each team's return is its own, 7.8 u off its stand (27 / -27, -39.5, -2.7)
2. h3_cyberdyne (The Pit): the returns are the stands, as before
3. h3_s3d_lockout: a team-tagged return nearer the other stand is not trusted (as before: the one within 3 u)
4. the director's capture point on Avalanche is the team's return, not its stand

usage: python -I test_flag_returns.py      -> "flag returns OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402


def near(a, b, tol=0.5):
    return a is not None and abs(a.x - b[0]) < tol and abs(a.y - b[1]) < tol and abs(a.z - b[2]) < tol


def main():
    fails = []
    m = get_map("h3_sidewinder")
    r = m.get("returns", {})
    for t in (0, 1):
        stand = m["flags"][t]
        want = (27.0 if stand.x > 0 else -27.0, -39.47, -2.66)
        if not near(r.get(t), want):
            fails.append(f"Avalanche team {t}: return {r.get(t)} (want {want}, 7.8 u off its stand {stand})")
    p = get_map("h3_cyberdyne")
    for t in (0, 1):
        if t not in p.get("returns", {}) or (p["returns"][t] - p["flags"][t]).flat() > 0.5:
            fails.append(f"The Pit team {t}: return {p.get('returns', {}).get(t)} (want its stand {p['flags'][t]})")
    lk = get_map("h3_s3d_lockout")
    for t, want in ((1, (7.1, -1.6, 7.5)), (0, (-9.6, 9.1, 6.0))):
        if not near(lk.get("returns", {}).get(t), want, 0.2):
            fails.append(f"Lockout remake team {t}: return {lk.get('returns', {}).get(t)} (want {want}: the one by its stand)")
    d = Director(0, m, {}, random.Random(1))
    snap = Snapshot(10.0, [], {}, mode="ctf")
    cp = d.capture_point(snap)
    if not near(cp, (27.0 if m["flags"][d.side].x > 0 else -27.0, -39.47, -2.66)):
        fails.append(f"Avalanche capture point {cp} (want the team's return, not the stand {m['flags'][d.side]})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"flag returns OK (Avalanche {r[0]} / {r[1]}; The Pit at its stands; the Lockout remake as before; capture "
          f"point {cp})")


if __name__ == "__main__":
    main()
