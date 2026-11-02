"""People's moves off the nav: a crate top a person walked is a review candidate, an approved one joins the nav
and is no candidate again, a rejected one stays out (review_moves.selftest); a ride in a vehicle records no
floor, jump or death for the person (lidar.HumanWatch).

usage: python -I test_moves_review.py      -> "moves review OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import review_moves  # noqa: E402
from lidar import HumanWatch, Recorder  # noqa: E402


def main():
    review_moves.selftest()
    # a jump-like arc (rise 0.8 over 0.8 s) while seated in a vehicle; then the same on foot
    dt, path = 1 / 30, []
    for k in range(60):
        t = max(0.0, min(0.8, (k - 10) * (1 / 30)))
        path.append((k * 0.08, 0.0, 4.0 * t * (0.8 - t) * 1.25 if 10 <= k <= 34 else 0.0))
    for riding, want in ((False, 1), (True, 0)):                 # on foot first: the arc is a jump at all
        hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False))
        hw.rec.links = []
        for k, p in enumerate(path + [path[-1]] * 200):          # 7 s on the ground after: confirmed
            hw.update(k * dt, [(0, p, True, False, True, riding)])
        got = len(hw.rec.links)
        if got != want or (riding and (hw.rec.deaths or hw.rec.events)):
            sys.exit(f"FAIL: riding={riding}: {got} links (want {want}), {len(hw.rec.deaths)} deaths, "
                     f"{len(hw.rec.events)} cells")
    print("moves review OK")


if __name__ == "__main__":
    main()
