"""Save the Reach game globals (TLS +0x48) of the running match, for finding the game-type fields by diffing
matches of different types. Read-only.

usage: python -I reach_variant_dump.py <label>        -> logs/_reach_gg_<label>.bin, prints the variant name
       python -I reach_variant_dump.py --diff a b c   -> offsets whose bytes differ between every pair of labels
                                                         and stay equal inside one label's repeats (a, a2 ...)
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
SIZE = 0x30000
NAME_AT = 0x1574          # the variant's name (UTF-16), HANDOFF


def path(label):
    return os.path.join(ROOT, "logs", f"_reach_gg_{label}.bin")


def dump(label):
    from brain.live import LiveReach
    live = LiveReach()
    live.players()
    gg = live.g.u64(live._blk + 0x48)
    b = live.g.read(gg, SIZE)
    open(path(label), "wb").write(b)
    print(label, hex(gg), "name:", b[NAME_AT:NAME_AT + 64].decode("utf-16-le", "replace").partition(chr(0))[0])


def diff(labels):
    data = {lb: open(path(lb), "rb").read() for lb in labels}
    groups = {}
    for lb in labels:
        groups.setdefault(lb.rstrip("0123456789"), []).append(data[lb])
    keys = list(groups)
    out = []
    for off in range(0, SIZE, 4):
        vals = []
        for k in keys:
            vs = {struct.unpack_from("<I", d, off)[0] for d in groups[k]}
            if len(vs) != 1:
                break
            vals.append(vs.pop())
        else:
            if len(set(vals)) == len(vals):
                out.append((off, vals))
    for off, vals in out[:200]:
        print(hex(off), " ".join(f"{k}={v:#x}" for k, v in zip(keys, vals)))
    print(len(out), "offsets differ between every type and hold inside each")


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2:])
    else:
        dump(sys.argv[1])
