"""Live check of Halo CE's ragdolls (native/ce_ragdoll.cpp), read only: for N seconds reads every dead biped's node
matrices in a running CE multiplayer game and prints, per body seen at least 2 s: non-finite reads, the worst axis
length error, the lowest and highest node over the corpse object (its floor), the highest node once at rest (3 s on),
and the worst bone stretch (thighs, calves, upper arms, forearms against the cyborg skeleton's lengths) while falling
and at rest. Torn reads (the game thread writing while this reads) are skipped: two reads must match.
Good: no NaN, axis 0.0, at-rest top under ~0.2, stretch at rest under ~0.01 (falling stretch above that is the death
animation's own pose before the ragdoll takes over).
usage: python -I tools/ce_ragdoll_check.py [seconds]"""
import math
import os
import struct
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brain"))
from live import Live  # noqa: E402

DEAD = 0x10000                     # biped +0x10: set the tick it dies
MATRICES, COUNT = 0x548, 19        # cyborg node matrices (object + the u16 at +0x1AE), 0x34 bytes each
BONES = {"l thigh": (1, 4, 0.172), "l calf": (4, 8, 0.156), "r thigh": (2, 5, 0.172), "r calf": (5, 11, 0.156),
         "l upperarm": (13, 15, 0.109), "l forearm": (15, 17, 0.114), "r upperarm": (14, 16, 0.109),
         "r forearm": (16, 18, 0.114)}


def main():
    L = Live()
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    first, rows = {}, {}
    t0 = time.time()
    while time.time() - t0 < secs:
        now = time.time()
        for h, typ, path, pos in L.objects(types=(0,)):
            o = L.object(h)
            if not o or not struct.unpack("<I", L.g.read(o + 0x10, 4))[0] & DEAD:
                first.pop(h, None)
                continue
            first.setdefault(h, now)
            m = L.g.read(o + MATRICES, COUNT * 0x34)
            if m != L.g.read(o + MATRICES, COUNT * 0x34):
                continue
            f = [struct.unpack_from("<13f", m, i * 0x34) for i in range(COUNT)]
            r = rows.setdefault(h, dict(nan=0, axis=0.0, low=9.0, high=-9.0, rest_top=0.0, stretch_falling=0.0,
                                        stretch_rest=0.0, age=0.0))
            r["age"] = now - first[h]
            if not all(math.isfinite(x) for row in f for x in row):
                r["nan"] += 1
                continue
            for row in f:
                for a in (row[1:4], row[4:7], row[7:10]):
                    r["axis"] = max(r["axis"], abs(math.sqrt(sum(x * x for x in a)) - 1))
            zs = [row[12] - pos[2] for row in f]
            r["low"], r["high"] = min(r["low"], min(zs)), max(r["high"], max(zs))
            key = "stretch_rest" if r["age"] > 3 else "stretch_falling"
            if r["age"] > 3:
                r["rest_top"] = max(zs)
            for a, b, rest in BONES.values():
                r[key] = max(r[key], abs(math.dist(f[a][10:13], f[b][10:13]) - rest) / rest)
        time.sleep(0.03)
    seen = {h: r for h, r in rows.items() if r["age"] >= 2}
    for h, r in seen.items():
        print(hex(h), {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    print(len(seen), "bodies checked")


if __name__ == "__main__":
    main()
