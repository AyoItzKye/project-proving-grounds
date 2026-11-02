"""Offline check of tools/ammo_scan.py's field finder (classify) on a made-up gun, sampled as the scan samples (30 Hz,
trigger down 0.4 s a second, 20 s). Its int16 fields, in order (offsets 0, 2, ... 10):
  A  a magazine: one round every 3rd sample of a pulse; empty, it reloads in a pause, paid by B
  B  A's reserve: falls only when A reloads
  C  a shot counter (Halo 2 +0x1B6): +1 on each of a pulse's first 3 shots, back to 0 at the next press
  D  a field that jumps at every press (CE +0x22A on a plasma pistol): 0 -> 18 at the press, -1 a sample, 0 on release
  E  a shotgun magazine: two shells a pulse, two loaded one by one in each pause, paid by F
  F  E's reserve (it pays the second shell a sample late: the two fields are not always read on one game tick)
  G  a clock counting down every sample, trigger or not
Magazines A and E (with reserves B and F) must be found; C, D and G must not (third review B2: D passed and E failed).

usage: python -I test_ammo_scan.py      -> "ammo_scan OK"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ammo_scan import classify  # noqa: E402


def gun():
    a, b, c, d, e, f, owed, rows = 60, 120, 0, 0, 12, 50, False, []
    for i in range(600):
        k = i % 30                                       # the sample within its second
        firing = k < 12
        if k in (1, 4, 7, 10) and a > 0:
            a -= 1
            c = min(3, c + 1) if k < 10 else c
        if k == 20 and a == 0:
            a, b = 60, b - 60
        if k == 0:
            c, d = 0, 18
        elif firing:
            d -= 1
        elif k == 12:
            d = 0
        if k in (0, 6):
            e -= 1
        if k == 18 and e < 12:
            e, f = e + 1, f - 1
        if k == 24 and e < 12:
            e, owed = e + 1, True
        if k == 25 and owed:
            f, owed = f - 1, False
        rows.append((i / 30, firing, (a, b, c, d, e, f, 900 - i)))
    return rows


def main():
    mags, res, _ = classify({(0, 1): gun()})
    if dict(mags) != {0: 1, 8: 1} or dict(res) != {(0, 2): 1, (8, 10): 1}:
        sys.exit(f"FAIL: magazines {dict(mags)} (want +0x0 and +0x8), reserves {dict(res)} (want (0x0, 0x2), (0x8, 0xa))")
    print("ammo_scan OK")


if __name__ == "__main__":
    main()
