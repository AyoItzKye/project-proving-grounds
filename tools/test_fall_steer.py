"""Offline checks for falls onto Spire's heat vents (live-30: 22 of 29 deaths off the spire top in three matches
came down 1.7-2.6 u off a vent, most past it, the jumpers steering at it with a full stick all the way; the core carrier
who slid off the rim by the vent drop's take-off braked, steered back at the rim and fell 36 u). A fall is integrated
with a simple air model: gravity 4.1 u/s^2, the stick pulling the horizontal speed
toward 2.4 u/s its way at ACC u/s^2 (live, a defender braking against 2.4 u/s lost 1.5 u/s in 1.5 s: about 1.0), no
stick keeping the speed, or with DRAG pulling it to 0. The game's own air control is not this model: these check the
steering's logic over a range of it; a live match checks the game's.
1. A planned drop from the take-off (defender #9's, live 529.35 s): down within 0.6 u of the vent.
2. A slide off the rim 1.7 u past the take-off (the carrier's, live 507.7 s): a metre under the ledge it falls for the
   vent ("air: onto the landing below") and comes down within 0.6 u of it.
3. Just off the ledge (0.5 u under it): no try for the vent, it steers back onto the ledge (as before).
4. fall_time: 33 u from rest 4.0 s; falling already, less; on a jump's way up, more.

usage: python -I test_fall_steer.py      -> "fall steer OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import GRAVITY, Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

MAP = get_map("reach_35_island")
VENT = Vec(-164.59, -415.67, -58.25)        # drop 3's landing (maps/reach_35_island/drops.json), a covy_heat_vent
DT = 1 / 30


def bot():
    return Bot(1, 0, make_profile("top", "rusher", random.Random(1)), MAP, random.Random(1))


def world_move(act):
    c, sn = math.cos(act.yaw), math.sin(act.yaw)
    return c * act.forward - sn * act.strafe, sn * act.forward + c * act.strafe


def fall(b, pos, vel, acc=1.0, drag=False, planned=False, t0=100.0):
    """Integrate a fall until it is down at the vent's height: (how far from the vent, the edge guard's notes)."""
    yaw = math.atan2(VENT.y - pos.y, VENT.x - pos.x)       # looking where it goes
    now, notes, first = t0, set(), True
    while pos.z > VENT.z:
        me = PlayerState(1, 0, "bot", pos, vel=vel, yaw=yaw)
        act = Action(forward=1.0, yaw=yaw)                  # move_to's command: on toward the vent's way
        b.notes, b.planned_jump = [], planned and first     # (move_to plans the jump on the take-off tick)
        if b.planned_jump:
            b.jump_land = VENT
        b.edge_guard(now, me, act)
        notes.update(str(n) for n in b.notes)
        mx, my = world_move(act)
        m = math.hypot(mx, my)
        tx, ty = (mx / m * 2.4 * min(1.0, m), my / m * 2.4 * min(1.0, m)) if m > 0.05 else \
            ((0.0, 0.0) if drag else (vel.x, vel.y))
        dx, dy = tx - vel.x, ty - vel.y
        dn = math.hypot(dx, dy)
        k = min(dn, acc * DT) / dn if dn else 0.0
        vel = Vec(vel.x + dx * k, vel.y + dy * k, vel.z - GRAVITY * DT)
        pos = Vec(pos.x + vel.x * DT, pos.y + vel.y * DT, pos.z + vel.z * DT)
        now, first = now + DT, False
    return math.hypot(pos.x - VENT.x, pos.y - VENT.y), notes


def main():
    testdata.need_lidar("reach_35_island")
    models = [(acc, drag) for acc in (0.7, 1.0, 1.5) for drag in (False, True)]

    # 1. defender #9's planned drop (live 529.35 s: take-off at a run, 2.5 u/s, jump 2.7 u/s up)
    for acc, drag in models:
        miss, notes = fall(bot(), Vec(-169.58, -408.68, -24.33), Vec(1.55, -1.95, 2.7), acc, drag, planned=True)
        print(f"  planned drop, air {acc} u/s^2{' drag' if drag else ''}: down {miss:.2f} u from the vent")
        assert miss < 0.6, ("planned drop came down off the vent", acc, drag, miss)

    # 2. the carrier's slide off the rim (live 507.69 s: 1.03 u/s on, 3.3 u/s down), its ledge the rim at 507.43 s
    for acc, drag in models:
        b = bot()
        b.last_ground = Vec(-169.39, -410.54, -24.37)
        miss, notes = fall(b, Vec(-169.25, -410.81, -25.16), Vec(0.5, -0.9, -3.3), acc, drag)
        print(f"  slide off the rim, air {acc} u/s^2{' drag' if drag else ''}: down {miss:.2f} u from the vent, "
              f"{sorted(notes)}")
        assert "air: onto the landing below" in notes, ("no try for the vent", notes)
        if acc >= 1.0:
            assert miss < 0.6, ("the slide came down off the vent", acc, drag, miss)

    # 3. 0.5 u under the ledge, over the void: back onto the ledge, no vent
    b = bot()
    b.last_ground, b.notes = Vec(-169.39, -410.54, -24.37), []
    me = PlayerState(1, 0, "bot", Vec(-169.3, -410.7, -24.87), vel=Vec(0.5, -0.9, -2.0))
    act = Action(forward=1.0, yaw=-0.8)
    b.edge_guard(100.0, me, act)
    mx, my = world_move(act)
    back = Vec(-169.39 + 169.3, -410.54 + 410.7, 0.0)
    assert "air: onto the landing below" not in b.notes and (mx * back.x + my * back.y) > 0, \
        ("left the ledge for the vent at 0.5 u under it", b.notes, act)

    # 4. fall times
    t0 = Bot.fall_time(PlayerState(1, 0, "bot", Vec(0, 0, 33.0)), Vec(0, 0, 0))
    down = Bot.fall_time(PlayerState(1, 0, "bot", Vec(0, 0, 33.0), vel=Vec(0, 0, -5.0)), Vec(0, 0, 0))
    up = Bot.fall_time(PlayerState(1, 0, "bot", Vec(0, 0, 33.0), vel=Vec(0, 0, 2.7)), Vec(0, 0, 0))
    assert abs(t0 - math.sqrt(2 * 33 / GRAVITY)) < 1e-6 and down < t0 < up, (t0, down, up)
    print("fall steer OK")


if __name__ == "__main__":
    main()
