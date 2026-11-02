"""Find live counters in a game's memory (scores, game clock): snapshot memory every few seconds and
keep int32 cells that behave like the wanted counter.: the score readers for the score posture
(brain/match.py).

usage: python -I find_counters.py <dll> [--seconds 90] [--every 3]          the module image (Halo CE, H2)
       python -I find_counters.py --tls <h3|reach|odst|h2a|h4> [--window 0x40000]
           the game-state blocks the game thread's TLS block points to (Halo 3 and later keep the game
           globals there): every pointer in the first 0x400 bytes of the block, a window after each.
Prints cells that grow at ~30/s or ~60/s (tick clocks) and small cells (0..400) that only went up in
whole steps (score candidates) with their history; addresses as module+offset or tls+slot:+offset.
"""
import argparse
import ctypes as C
import os
import struct
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from memread import Game  # noqa: E402


def module_range(pid, name):
    snap = C.windll.kernel32.CreateToolhelp32Snapshot(0x18, pid)

    class ME(C.Structure):
        _fields_ = [("size", C.c_uint32), ("mid", C.c_uint32), ("pid", C.c_uint32), ("g", C.c_uint32), ("p", C.c_uint32),
                    ("base", C.c_void_p), ("bsize", C.c_uint32), ("h", C.c_void_p), ("name", C.c_wchar * 256), ("path", C.c_wchar * 260)]
    e = ME(); e.size = C.sizeof(ME)
    ok = C.windll.kernel32.Module32FirstW(C.c_void_p(snap), C.byref(e))
    out = None
    while ok:
        if e.name.lower() == name.lower():
            out = (e.base, e.bsize)
        ok = C.windll.kernel32.Module32NextW(C.c_void_p(snap), C.byref(e))
    C.windll.kernel32.CloseHandle(C.c_void_p(snap))
    return out


def read_all(g, base, size, chunk=1 << 16):
    buf = bytearray(size)
    for off in range(0, size, chunk):
        b = g.read(base + off, min(chunk, size - off))
        if b:
            buf[off:off + len(b)] = b
    return np.frombuffer(bytes(buf[: size // 4 * 4]), dtype="<i4").copy()


def tls_regions(game, window):
    """[(label, base, size)] for every distinct pointer in the game thread's TLS block."""
    from brain.live import LiveH3, LiveReach, LiveODST, LiveH4F
    L = {"h3": LiveH3, "reach": LiveReach, "odst": LiveODST, "h2a": lambda: LiveH4F("groundhog.dll"),
         "h4": LiveH4F}[game]()
    L.players()                                   # finds the TLS block
    blk = L._blk
    raw = L.g.read(blk, 0x400)
    seen, out = set(), []
    for slot in range(0, 0x400, 8):
        p = struct.unpack_from("<Q", raw, slot)[0]
        if p < 0x10000 or p > 0x7FFFFFFFFFFF or p in seen:
            continue
        seen.add(p)
        if L.g.read(p, 16):
            out.append((f"tls+{slot:#x}", p, window))
    return L.g, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dll", nargs="?")
    ap.add_argument("--tls")
    ap.add_argument("--window", type=lambda x: int(x, 0), default=0x40000)
    ap.add_argument("--seconds", type=float, default=90)
    ap.add_argument("--every", type=float, default=3)
    o = ap.parse_args()
    if o.tls:
        g, regions = tls_regions(o.tls, o.window)
    else:
        g = Game(o.dll)
        base, size = module_range(g.pid, o.dll)
        regions = [(o.dll, base, size)]
    print("regions:", [(r[0], hex(r[1]), hex(r[2])) for r in regions])
    snaps, times = [], []
    t0 = time.time()
    while time.time() - t0 < o.seconds:
        times.append(time.time() - t0)
        snaps.append(np.concatenate([read_all(g, b, s) for _, b, s in regions]))
        time.sleep(max(0, o.every - (time.time() - t0 - times[-1])))
    labels = []
    for name, b, s in regions:
        labels.append((name, s // 4))

    def where(k):
        for name, n in labels:
            if k < n:
                return f"{name}:+{k * 4:#x}"
            k -= n
    A = np.stack(snaps)
    dt = times[-1] - times[0]
    d = A[-1].astype(np.int64) - A[0]
    mono = np.all(np.diff(A, axis=0) >= 0, axis=0)
    for rate in (30, 60):
        hit = np.nonzero(mono & (np.abs(d / dt - rate) < 0.08 * rate))[0]
        print(f"~{rate}/s:", [f"{where(k)}={A[-1][k]}" for k in hit[:16]])
    steps = np.diff(A, axis=0)
    small = (A.min(0) >= 0) & (A.max(0) <= 400) & mono & (d > 0) & np.all((steps == 0) | (steps <= 10), axis=0)
    idx = np.nonzero(small)[0]
    print(f"{len(idx)} small growing cells")
    for k in idx[:120]:
        print(f"{where(k)}: {[int(x) for x in A[:, k]]}")


if __name__ == "__main__":
    main()
