"""The match clock in a TLS game (H2A): cells growing at 60/s whose value matches the HUD clock. Reads
twice 3 s apart, takes a screenshot (logs/nav_now.jpg), prints every 60/s cell with its value in
seconds so it can be matched to the HUD's time (time limit - HUD = elapsed).: H2A's tick cell from one
session froze in the next.

usage: python -I find_clock.py <game> [--elapsed SECONDS]   (with --elapsed: only cells within 10 s)
"""
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_counters as fc  # noqa: E402


def main():
    game = sys.argv[1]
    elapsed = float(sys.argv[sys.argv.index("--elapsed") + 1]) if "--elapsed" in sys.argv else None
    g, regions = fc.tls_regions(game, 0x40000)
    a = [fc.read_all(g, b, s) for _, b, s in regions]
    t0 = time.time()
    time.sleep(3)
    b = [fc.read_all(g, b, s) for _, b, s in regions]
    dt = time.time() - t0
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "shot"], capture_output=True)
    seen = set()
    for (name, base, _), x, y in zip(regions, a, b):
        rate = (y.astype(np.int64) - x) / dt
        for k in np.nonzero(np.abs(rate - 60) < 6)[0]:
            sec = y[k] / 60.0
            if elapsed is not None and abs(sec - elapsed) > 10:
                continue
            addr = base + k * 4
            if addr in seen:
                continue
            seen.add(addr)
            print(f"{name}:+{k * 4:#x} = {y[k]} ({sec:.1f} s)")


if __name__ == "__main__":
    main()
