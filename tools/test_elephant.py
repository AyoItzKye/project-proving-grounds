"""Offline check of Sandtrap's Elephants (the player: "The bots have issues on H3 with delivering the flag on
elephants ... the last bot that had a flag sat on the first level the whole time"):
1. Bot.way_in: a goal in an Elephant (vehicles.ELEPHANT: its model and a player's flags of its second floor, Nov 11) is
   reached round the hull to the rear ramp's foot, straight up the ramp, and for the capture on the second floor by the
   a player's jump from the bay floor (7 jumps, Nov 11), the stairs after three that failed; walked from in front, beside and behind, the way never crosses the hull
   outside the ramp's lane, bay and stairs, and ends at the goal on the deck; a goal outside the bay is left alone.
   Every way in (a player's tire-well climbs and jumps, ELEPHANT entries) walked from just outside it; with every jump
   way left, from beside its side round the hull's corner to the ramp, never through the side.
2. Director.capture_point: the team's flag return where the map has one (Narrows' lie 0.7 u off the stands), else the
   stand (Blood Gulch has none).
usage: python -I test_elephant.py      -> "elephant OK"
"""
import math
import os
import random
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

E = vehicles.ELEPHANT


def on_stairs(f, l):
    (sf, sl), (uf, ul, uz) = E["stair"]
    k = (f - sf) / (uf - sf)
    return 0.0 <= k <= 1.0 and abs(l - (sl + (ul - sl) * k)) <= 0.5, k


def floor_z(f, l, z=0.0):
    """The walking height in the Elephant's frame (z over its origin), roughly: the sand round it 0, the ramp rising 0
    to 0.55 from f -3.6 to -2.5 in its lane, the bay floor 0.55 (to the rear beside the lane), the stairs 0.55 to the deck's 1.72 along their line
    (stepped onto from the bay floor), the deck 1.72 once up (z: the height a step ago)."""
    (af, al), _ = E["ramp"]
    f0, f1, w = E["bay"]
    stair, k = on_stairs(f, l)
    sz = 0.55 + (E["stair"][1][2] - 0.55) * k
    if stair and (z > sz - 0.25 or k < 0.05):      # (on from their foot or from a step below; the bay floor beside
        return sz                                   # them is not on them: live Nov 11, a carrier walked under them)
    if z > E["deck"] and f0 <= f <= f1 and abs(l) <= 2.0:   # (the deck: a player walked it to l +-2.0)
        return E["stair"][1][2]
    if 0.9 < z < 1.5 and 1.5 <= abs(l) <= 2.8 and -4.4 <= f <= 3.0:   # (a tire well's top, landed on: a player's climbs)
        return z
    if abs(l - al) <= 0.6 and -3.6 <= f <= -2.5:
        return 0.55 * (f + 3.6) / 1.1
    if f0 <= f <= f1 and abs(l) <= w and (f > -2.5 or abs(l - al) > 0.6):   # (beside the ramp's lane: the bay to the
        return 0.55                                                     # rear, the stairs' foot, a player's flag z 0.76)
    return 0.0


def walk(bot, el, start, goal, steps=400):
    """Walk the bot from start (Elephant frame f, l) to the goal by way_in's waypoints, 0.25 u a step. Returns
    (reached, crossed the hull outside the ramp lane and bay)."""
    local, world = vehicles.frame_of(el)
    f, l = start
    z = floor_z(f, l)
    h0, h1, hw = E["hull"]
    (af, al), _ = E["ramp"]
    f0, f1, w = E["bay"]
    crossed = False
    for step in range(steps):
        bot.now = step * 0.1
        z = floor_z(f, l, z)
        p = world(f, l, z)
        way = bot.way_in(PlayerState(1, 0, "bot", p, yaw=0.0), goal)
        if way is not None and len(way) > 2 and way[2]:           # the deck jump: up 1.1 u, landing where it aims
            lf, ll, lz = local(way[0])
            f, l, z = lf, ll, lz
            continue
        target = goal if way is None else way[0]
        tf, tl, _ = local(target)
        d = math.hypot(tf - f, tl - l)
        gf, gl, gz = local(goal)
        if math.hypot(gf - f, gl - l) < 0.3 and abs(gz - z) < 0.6:
            return True, crossed
        k = min(1.0, 0.25 / max(d, 1e-6))
        f, l = f + (tf - f) * k, l + (tl - l) * k
        inside = h0 <= f <= h1 and abs(l) <= hw
        lane = abs(l - al) <= 0.8 and f <= -2.4
        bay = f0 <= f <= f1 and abs(l) <= w and z > 0.35
        if inside and not lane and not bay and not on_stairs(f, l)[0] and z <= 0.9:
            crossed = True
    return False, crossed


def main():
    fails = []
    m = get_map("h3_shrine")
    bot = Bot(1, 0, make_profile("average", "rusher", random.Random(1)), m, random.Random(1))
    el = dict(handle=7, kind="behemoth", pos=(-0.27, -58.56, -22.26), fwd=(-1.0, 0.0, 0.0), occupied=False, riders=0)
    bot.vehicles_now = [el]
    local, world = vehicles.frame_of(el)
    goal = world(*E["flag_return"][:2], E["flag_return"][2])
    flag = world(1.45, -0.47, 1.67)
    for name, start, g in (("in front", (7.0, 0.5), goal), ("beside", (0.5, -4.5), goal), ("behind", (-8.0, 2.0), goal),
                           ("in front, to the flag", (6.0, -1.0), flag)):
        reached, crossed = walk(bot, el, start, g)
        if not reached or crossed:
            fails.append(f"{name}: reached {reached}, through the hull {crossed}")
    w0 = bot.way_in(PlayerState(1, 0, "bot", world(-4.7, -0.5, 0.0), yaw=0.0), goal)
    if not (w0 and w0[1] and abs(local(w0[0])[0] - E["ramp"][1][0]) < 0.01):
        fails.append(f"at the ramp's foot: {w0} (want straight up to its top)")
    (sf, sl), (uf, ul, uz) = E["stair"]
    bot.deck_jumps, bot.now = [], 50.0
    from brain.bot import DECK_RUNUP
    JF = E["deck_jump"][0][0]
    w1 = bot.way_in(PlayerState(1, 0, "bot", world(-1.0, 0.0, 0.6), yaw=0.0), goal)
    if not (w1 and w1[1] and math.hypot(local(w1[0])[0] - (JF - DECK_RUNUP), local(w1[0])[1] - 0.2) < 0.01):
        fails.append(f"on the bay floor in front of the jump, the capture upstairs: {w1} (want back to its run-up)")
    wn = bot.way_in(PlayerState(1, 0, "bot", world(JF, 0.2, 0.6), yaw=0.0), goal)
    if not wn or (len(wn) > 2 and wn[2]):
        fails.append(f"on the take-off with no run-up (live: a jump with the momentum rearward): {wn} (want no jump)")
    bot.now = 51.0
    wr = bot.way_in(PlayerState(1, 0, "bot", world(JF - DECK_RUNUP, 0.2, 0.6), yaw=0.0), goal)
    if not (wr and wr[1] and math.hypot(local(wr[0])[0] - (JF), local(wr[0])[1] - 0.2) < 0.01):
        fails.append(f"at the run-up: {wr} (want on to the take-off)")
    ws = bot.way_in(PlayerState(1, 0, "bot", world(-1.79, 0.99, 1.36), yaw=0.0), goal)
    if not (ws and abs(local(ws[0])[2] - E["stair"][1][2]) < 0.01):
        fails.append(f"two thirds up the stairs (live: z 1.36, turned for the goal, off their side): {ws} (want their top)")
    bot.now = 51.5
    we = bot.way_in(PlayerState(1, 0, "bot", world(JF - 0.3, 0.2, 0.6), yaw=0.0), goal)
    if not we or (len(we) > 2 and we[2]):
        fails.append(f"0.3 u short of the take-off (live: jumped 0.28 u early, the lip met falling): {we} (want no jump yet)")
    bot.now = 52.0
    wj = bot.way_in(PlayerState(1, 0, "bot", world(JF, 0.2, 0.6), yaw=0.0), goal)
    if not (wj and len(wj) > 2 and wj[2] and abs(local(wj[0])[2] - 1.72) < 0.01):
        fails.append(f"at the jump spot after the run-up: {wj} (want a jump onto the deck)")
    # the deck jump is a crouch-jump (live Nov 11: plain jumps peaked 1.66 u up, the deck at 1.72): crouched once off
    # the ground (Bot.edge_guard), not at the take-off (GitHub #20's crouch-jumps go the same way)
    from brain.core import Action
    takeoff = world(JF, 0.2, 0.6)
    bot.crouch_jump(PlayerState(1, 0, "bot", takeoff, yaw=0.0))
    a0, a1 = Action(yaw=0.0, forward=1.0), Action(yaw=0.0, forward=1.0)
    bot.edge_guard(bot.now, PlayerState(1, 0, "bot", takeoff, yaw=0.0), a0)
    bot.edge_guard(bot.now + 0.3, PlayerState(1, 0, "bot", world(-1.2, 0.2, 1.4), yaw=0.0), a1)
    if a0.crouch or not a1.crouch:
        fails.append(f"the deck's crouch-jump: crouched at the take-off {a0.crouch}, in the air {a1.crouch} (want no, yes)")
    bot.jump_crouch_until = 0.0
    bot.deck_jumps, bot.now = [44.0, 46.0, 48.0], 50.0
    wb = bot.way_in(PlayerState(1, 0, "bot", world(-2.63, 0.86, 0.64), yaw=0.0), goal)
    if not (wb and math.hypot(local(wb[0])[0] - sf, local(wb[0])[1] - sl) < 0.01):
        fails.append(f"on the bay floor beside the stairs (live 15:51 match, t 168.9): {wb} (want their foot, not their top)")
    bot.deck_jumps, bot.now = [44.0, 46.0, 48.0], 50.0
    wf = bot.way_in(PlayerState(1, 0, "bot", world(-1.0, 0.0, 0.6), yaw=0.0), goal)
    if not (wf and math.hypot(local(wf[0])[0] - sf, local(wf[0])[1] - sl) < 0.01):
        fails.append(f"three jumps in 12 s that did not get up: {wf} (want the stairs' foot)")
    # (the stairs once three jumps in 12 s failed; before that a player's jump spot)
    (jf, jl), (lf, ll, lz) = E["deck_jump"]
    bot.deck_jumps, bot.now = [0.0, 2.0, 4.0], 5.0
    w3 = bot.way_in(PlayerState(1, 0, "bot", world(sf, sl, 0.6), yaw=0.0), goal)
    if not (w3 and w3[1] and abs(local(w3[0])[2] - uz) < 0.01):
        fails.append(f"at the stairs' foot: {w3} (want up them to the deck)")
    w4 = bot.way_in(PlayerState(1, 0, "bot", world(0.5, 0.6, uz), yaw=0.0), goal)
    if not (w4 and w4[1] and w4[0] is goal):
        fails.append(f"on the deck: {w4} (want straight to the goal)")
    low = world(-1.0, 0.0, 0.55)
    w5 = bot.way_in(PlayerState(1, 0, "bot", world(-2.0, 0.0, 0.6), yaw=0.0), low)
    if not (w5 and w5[1] and w5[0] is low):
        fails.append(f"a goal on the bay floor: {w5} (want straight along the floor)")
    w2 = bot.way_in(PlayerState(1, 0, "bot", world(-1.0, 0.0, 3.0), yaw=0.0), goal)
    if not w2 or w2[1]:
        fails.append(f"on its roof: {w2} (want off it to the ramp's foot by the nav, not straight on)")
    if bot.way_in(PlayerState(1, 0, "bot", world(8.0, 0.0, 0.0), yaw=0.0), world(12.0, 0.0, 0.0)) is not None:
        fails.append("a goal outside the bay was routed")
    # past it: from behind to a goal beyond its front, round a corner, never through it
    beyond = world(9.0, 0.3, 0.0)
    f, l = -7.0, 0.2
    for _ in range(200):
        way = bot.way_in(PlayerState(1, 0, "bot", world(f, l, 0.0), yaw=0.0), beyond)
        tf, tl, _ = local(way[0] if way else beyond)
        d = math.hypot(tf - f, tl - l)
        if d < 0.3 and way is None:
            break
        k = min(1.0, 0.25 / max(d, 1e-6))
        f, l = f + (tf - f) * k, l + (tl - l) * k
        h0, h1, hw = E["hull"]
        if h0 < f < h1 and abs(l) < hw:
            fails.append(f"walking past it from behind to beyond its front: through the hull at ({f:.1f}, {l:.1f})")
            break
    if math.hypot(9.0 - f, 0.3 - l) > 0.5:
        fails.append(f"walking past it: ended at ({f:.1f}, {l:.1f}), not beyond its front")
    bot.vehicles_now = [dict(el, fwd=None)]
    if bot.way_in(PlayerState(1, 0, "bot", world(7.0, 0.0, 0.0), yaw=0.0), goal) is not None:
        fails.append("an Elephant with no facing read was routed")
    # 4. every way in (vehicles.ELEPHANT entries, a player's climbs): from 1.5 u outside its take-off the walker gets in
    # by a jump (that way in or a cheaper one beside it) and to the capture spot without walking through the hull
    bot.vehicles_now = [el]
    for name, to, steps in E["entries"]:
        (xf, xl), _ = steps[0]
        n = math.hypot(xf, xl)
        start = (xf + 1.5 * xf / n, xl + 1.5 * xl / n)
        bot.deck_jumps, bot.entry_tries, bot.entry_ban = [], {}, {}
        first = []
        orig = bot.entry_try
        bot.entry_try = lambda now, nm, _f=first, _o=orig: (_f.append(nm), _o(now, nm))
        reached, crossed = walk(bot, el, start, goal)
        bot.entry_try = orig
        if not reached or crossed or not first:
            fails.append(f"from outside the {name}: reached {reached}, through the hull {crossed}, jumps {first[:2]}")
    # every jump way left (banned): from beside its right side to the rear ramp, round the hull's rear corner, never
    # through its side ("the bots need to stop running into the side of the elephant")
    bot.deck_jumps, bot.entry_tries = [], {}
    bot.entry_ban = {name: 1e9 for name, _, _ in E["entries"]}
    reached, crossed = walk(bot, el, (0.5, -4.5), goal)
    if not reached or crossed:
        fails.append(f"from beside its right side by the ramp only: reached {reached}, through the hull {crossed}")
    # a way tried three times with no progress is left for ENTRY_BAN s: the next cheapest is taken
    bot.entry_tries, bot.entry_ban = {}, {}
    for t in (0.0, 1.5, 3.0):
        bot.entry_try(t, "front jump")
    if not bot.entry_ban.get("front jump", 0.0) > 3.0:
        fails.append(f"three failed tries at the front jump: not left ({bot.entry_ban})")
    # its take-off on a dune (live Nov 11: an Elephant driven onto one, its wells jumped at from 1 to 2 u up for 56 s):
    # no jump there, that way left
    bot.now, bot.entry_tries, bot.entry_ban = 10.0, {}, {}
    (wf_, wl_), _ = next(steps for name, _, steps in E["entries"] if name == "front right well")[0]
    wd = bot.elephant_entry(PlayerState(1, 0, "bot", world(wf_, wl_, 1.5), yaw=0.0), world, (wf_, wl_, 1.5), (0.3, -0.3, 1.7))
    if (len(wd) > 2 and wd[2]) or not bot.entry_ban.get("front right well", 0.0) > 10.0:
        fails.append(f"a take-off on a dune 1.5 u up: {wd}, left {bot.entry_ban} (want no jump, that way left)")
    bot.now, bot.entry_ban = 4.0, {}
    # 3. a stand on an Elephant followed while its flag is away (brain/live.py _in_frame / _on_frame): its place on the
    # Elephant kept, then the Elephant drives 12 u and turns 90 degrees: the stand is where it rides now
    from brain.live import _in_frame, _on_frame
    g0 = (-0.27, -58.56, -22.26, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    stand = (1.14, -59.33, -20.7)
    loc = _in_frame(g0, stand)
    g1 = (11.73, -58.56, -22.26, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    now = _on_frame(g1, loc)
    want = (11.73 + 0.77, -58.56 + 1.41, -20.7)
    if max(abs(a - b) for a, b in zip((now.x, now.y, now.z), want)) > 1e-6:
        fails.append(f"a stand riding an Elephant that drove and turned: {now} (want {want})")
    # 2. the capture point
    for name, side, want_return in (("h3_chill", 0, True), ("bloodgulch", 0, False)):
        mp = get_map(name)
        d = Director(side, mp, {})
        snap = SimpleNamespace(flags={t: FlagState(t, mp["flags"][t], mp["flags"][t]) for t in (0, 1)}, mode="ctf",
                               players=[])
        got, want = d.capture_point(snap), (mp["returns"][side] if want_return else mp["flags"][side])
        if (got - want).flat() > 0.01 or (want_return and (want - mp["flags"][side]).flat() < 0.3):
            fails.append(f"{name}: capture point {got} (want {want}, the stand {mp['flags'][side]})")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("elephant OK (round the hull, up the ramp, along the bay and up the stairs from in front, beside and behind; "
          "captures on the second floor)")


if __name__ == "__main__":
    main()
