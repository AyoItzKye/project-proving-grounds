"""A vehicle's up vector where the reader has no ORIENT_AT (Reach): the vector after its facing, taken only as a unit
vector square to the facing. An upturned one reads as not upright; a read that is not an up vector (zeros, along the
facing, not unit length) stays None (standing, as before); Halo 4's ORIENT_AT read is unchanged.

usage: python -I test_vehicle_up.py      -> "vehicle up OK"
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from live_bots import vehicle_fwd  # noqa: E402


class Fake:
    POS_AT = 0x44

    def __init__(s, fwd, up, orient=None):
        s.g, s.mem = s, {0x50: fwd, 0x5C: up}
        if orient is not None:
            s.ORIENT_AT = orient
            s.mem.update({orient: (0.0, 1.0, 0.0), orient + 12: (0.0, 0.0, 1.0)})

    def object(s, h):
        return 1000

    def read(s, addr, n):
        return struct.pack("<3f", *s.mem.get(addr - 1000, (0.0, 0.0, 0.0)))


def main():
    fails = []
    fwd = (1.0, 0.0, 0.0)
    for up, want in (((0.0, 0.0, 1.0), (0.0, 0.0, 1.0)), ((0.0, 0.0, -1.0), (0.0, 0.0, -1.0)),
                     ((0.0, 0.0, 0.0), None), ((1.0, 0.0, 0.0), None), ((0.707, 0.0, 0.707), None),
                     ((0.0, 0.0, 0.5), None)):
        got = vehicle_fwd(Fake(fwd, up), 7, 1)
        if (got is None) != (want is None) or (got is not None and any(abs(a - b) > 1e-3 for a, b in zip(got, want))):
            fails.append(f"up read {up}: {got} (want {want})")
    if vehicles.upright(dict(up=(0.0, 0.0, -1.0))) or not vehicles.upright(dict(up=(0.0, 0.0, 1.0))):
        fails.append("an upturned vehicle (up z -1) read as upright, or a standing one as not")
    if vehicle_fwd(Fake(fwd, (0.0, 0.0, 1.0)), 7, 0) != fwd:
        fails.append("the facing read changed")
    h4 = Fake(fwd, (0.0, 0.0, 1.0), orient=0x100)
    if vehicle_fwd(h4, 7, 0) != (0.0, 1.0, 0.0) or vehicle_fwd(h4, 7, 1) != (0.0, 0.0, 1.0):
        fails.append("Halo 4's ORIENT_AT read changed")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("vehicle up OK (Reach's up vector read and checked; an upturned vehicle is not upright)")


if __name__ == "__main__":
    main()
