"""Intent to kill (brain/bot.py press_on, profiles.PRESS): in its gun's band a Legendary bot walks in on the one man it
fights instead of standing to strafe; Normal holds as before; nobody presses in a match without shields (Halo 2 SWAT's
Legendary already plays as it should), while losing the trade, or with two men in view unless the target's shield is
down (then it commits). The gap: tools/intent.py (a skilled player walks in 47% of in-view time, Legendary 33%).

usage: python -I test_press.py      -> "press OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import Kit  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
A = Vec(70.0, -120.0, T.nav_z(70.0, -120.0))
DT = 1 / 30


def forward(tier, foes, shieldless=False, my_shield=1.0, secs=2.5):
    """Mean forward stick over the fight's last 1.5 s (the bot faces him: forward = toward him)."""
    b = Bot(1, 0, make_profile(tier, "rusher", random.Random(4)), MAP, random.Random(4))
    b.kit = Kit(b.p, "reach")
    b.can_pickup = False
    out, t, yaw, pitch = [], 0.0, 0.0, 0.0
    while t < secs:
        me = PlayerState(1, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, weapon="dmr", weapons=["dmr"],
                         shield=my_shield)
        snap = Snapshot(t, [me] + foes)
        snap.shieldless = shieldless
        a = b.think(t, DT, snap, T.los, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        if t > secs - 1.5 and b.goal[0] == "fight":
            out.append(a.forward)
        t += DT
    return sum(out) / len(out) if out else None


def man(i, dx, dy=0.0, shield=1.0):
    return PlayerState(i, 1, "human", A + Vec(dx, dy, 0.0), alive=True, weapon="dmr", yaw=0.0, shield=shield,
                       health=1.0)


def main():
    fails = []
    one = [man(2, 12.0)]
    cases = [
        ("Legendary, one man at 12 u, even trade: walks in", "top", one, {}, lambda f: f > 0.5),
        ("Normal, same: holds", "average", one, {}, lambda f: abs(f) < 0.2),
        ("Legendary, no shields (SWAT): holds", "top", one, dict(shieldless=True), lambda f: abs(f) < 0.2),
        ("Legendary, his shield full, ours down: holds", "top", one, dict(my_shield=0.0), lambda f: abs(f) < 0.2),
        ("Legendary, two in view, both full: holds", "top", [man(2, 12.0), man(3, 12.0, -3.0)], {},
         lambda f: abs(f) < 0.2),
    ]
    for name, tier, foes, kw, ok in cases:
        f = forward(tier, foes, **kw)
        if f is None or not ok(f):
            fails.append(f"{name}: forward {f}")
    # two in view, the one it fights has no shield: commit (whichever it picked, the cracked man is the threat-ranked
    # pick; the check is that it walks in)
    f = forward("top", [man(2, 12.0, shield=0.0), man(3, 12.0, -3.0)])
    if f is None or f < 0.5:
        fails.append(f"Legendary, two in view, target's shield down: forward {f}")
    if fails:
        print("FAIL\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("press OK")


if __name__ == "__main__":
    main()
