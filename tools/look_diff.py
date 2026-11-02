"""Which object bytes a look byte changes (tools/look_probe.py bots): each probe bot's biped (0x800 bytes) against
the REF (or BASE) bot's, on bytes that hold still over a second (positions, timers and animation move). Read only.

usage: python -I look_diff.py [--game reach|h3|odst|h4|h2a]
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from look_dump import live_for  # noqa: E402

N = int(sys.argv[sys.argv.index("--bytes") + 1], 16) if "--bytes" in sys.argv else 0x800   # of each biped


def snap(live):
    out = {}
    for p in live.players():
        o = live.object(p["unit"]) if p.get("unit") is not None else None
        if o:
            out[p["name"]] = live.g.read(o, N)
    return out


def main():
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "reach"
    live = live_for(game)
    shots = []
    for _ in range(6):
        shots.append(snap(live))
        time.sleep(0.25)
    names = [n for n in shots[0] if all(n in s and s[n] for s in shots)]
    still = set(range(N))
    for n in names:                                   # bytes that change on any bot over time: not a look
        for s in shots[1:]:
            a, b = shots[0][n], s[n]
            still -= {i for i in range(N) if a[i] != b[i]}
    want = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else None     # another reference bot
    ref = want if want in names else next((n for n in names if n.startswith(("REF", "BASE"))), None)
    if ref is None:
        sys.exit("no REF / BASE bot (tools/look_probe.py --spec with a REF or BASE entry)")
    r = shots[0][ref]
    probes = [n for n in sorted(names) if n != ref and not n.startswith("PlayerOne")]
    # a look byte moves one object byte on the bot that has it, not on every bot (position, identity, bounds
    # differ on all): offsets where at most 3 of the probe bots differ from REF
    for i in sorted(still):
        who = [n for n in probes if shots[0][n][i] != r[i]]
        if 0 < len(who) <= 3:
            print(f"+0x{i:03X} ref {r[i]:02x}: " + ", ".join(f"{n} {shots[0][n][i]:02x}" for n in who))


if __name__ == "__main__":
    main()
