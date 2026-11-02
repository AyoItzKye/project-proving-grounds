"""Save the running game variant's memory for one game, to find a setting by changing only it in the lobby and diffing
(the motion tracker setting in every game). CE / Halo 2: the variant copy in the DLL; Halo 3 / Reach / H2A / Halo 4:
the game globals (TLS +0x48). Read-only.

usage: python -I variant_dump.py <ce|h2|h3|reach|h2a|h4> <label>      -> logs/_var_<game>_<label>.bin
       python -I variant_dump.py <game> --diff <label> <label> ...    -> bytes that differ between labels
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)


def path(game, label):
    return os.path.join(ROOT, "logs", f"_var_{game}_{label}.bin")


def read(game):
    from brain import live as L
    if game in ("ce", "h2"):
        g = L.Live() if game == "ce" else L.LiveH2()
        return g.g.read(g.g.base + g.VARIANT, 0x400)
    g = {"h3": L.LiveH3, "reach": L.LiveReach, "h2a": lambda: L.LiveH4F("groundhog.dll"), "h4": L.LiveH4F}[game]()
    g.players()
    # player 0's datum after the globals (its current traits live there); each reader's players() array
    base, mx, size = g._array({"h3": 0x10, "reach": 0x18, "h2a": 0x8, "h4": 0x8}[game])
    return g.g.read(g.g.u64(g._blk + 0x48), 0x30000) + g.g.read(base, size)


def main():
    game = sys.argv[1]
    if sys.argv[2] != "--diff":
        b = read(game)
        open(path(game, sys.argv[2]), "wb").write(b)
        print(f"{len(b)} bytes -> {path(game, sys.argv[2])}")
        return
    labels = sys.argv[3:]
    data = [open(path(game, lb), "rb").read() for lb in labels]
    n = 0
    for off in range(min(map(len, data))):
        vals = [d[off] for d in data]
        if len(set(vals)) > 1:
            n += 1
            if n <= 80:
                print(f"{off:#07x} " + " ".join(f"{lb}={v:#04x}" for lb, v in zip(labels, vals)))
    print(n, "bytes differ")


if __name__ == "__main__":
    main()
