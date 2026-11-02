"""Find a memory value that tells which MCC menu screen is open (read-only).

usage: python -I screenscan.py snap <name>        save the exe's writable data to logs/snap_<name>.npy
       python -I screenscan.py diff <want> <other> [<other> ...] [--same <want2>]
           offsets (exe-relative) whose byte is equal in <want> (and <want2>) and different from
           every <other>; 4-byte aligned ints are printed with their values
"""
import os
import sys

import numpy as np
import pefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memread import Game  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def sections(g, exe):
    path = None
    import ctypes as C
    buf = C.create_unicode_buffer(520)
    C.WinDLL("psapi").GetModuleFileNameExW(g.h, C.c_void_p(exe), buf, 520)
    pe = pefile.PE(buf.value, fast_load=True)
    for s in pe.sections:
        if s.Characteristics & 0x80000000:          # writable
            yield s.Name.rstrip(b"\0").decode(), s.VirtualAddress, s.Misc_VirtualSize


def snap(name):
    g = Game()
    exe = g.module("MCC-Win64-Shipping.exe")
    parts = {}
    for sec, va, size in sections(g, exe):
        data = bytearray()
        for off in range(0, size, 1 << 20):           # read in 1 MB chunks (holes read as zeros)
            n = min(1 << 20, size - off)
            data += g.read(exe + va + off, n) or bytes(n)
        parts[f"{sec}@{va:x}"] = np.frombuffer(bytes(data), np.uint8)
        print(sec, hex(va), size)
    np.savez(os.path.join(OUT, f"snap_{name}.npz"), **parts)


def diff(want, others, same):
    load = lambda n: np.load(os.path.join(OUT, f"snap_{n}.npz"))
    W = load(want)
    S = [load(n) for n in same]
    O = [load(n) for n in others]
    for key in W.files:
        w = W[key]
        ok = np.ones(len(w), bool)
        for s in S:
            ok &= s[key][:len(w)] == w
        for o in O:
            ok &= o[key][:len(w)] != w
        idx = np.nonzero(ok)[0]
        va = int(key.split("@")[1], 16)
        print(key, len(idx), "candidates")
        for i in idx[:40]:
            print(f"  exe+{va + i:x}: {want}={w[i]}", " ".join(f"{n}={X[key][i]}" for n, X in zip(others, O)))


if __name__ == "__main__":
    if sys.argv[1] == "snap":
        snap(sys.argv[2])
    else:
        args = sys.argv[2:]
        same = []
        if "--same" in args:
            k = args.index("--same")
            same, args = args[k + 1:], args[:k]
        diff(args[0], args[1:], same)
