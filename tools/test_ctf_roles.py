"""CTF roles (the player: bots must play the objective, help the flag carrier, defend while others pull).
Live, Boardwalk CTF: our carrier waited 2 min on our stand with both escorts while our flag lay 15 u from their base
(Reach: "Flag at home: Yes"), and defenders spent 0-7% of their defending time at home. Checks:
1. a standoff (both flags out): the carrier waits at a base post off the stand, the far one from our flag; the rest
   go for our flag, one escort with four or more of us
2. no standoff (our flag home): runner home with two escorts
3. a capture with our flag out turns the home rule off for the match (the variant does not need it home)
4. keep_role: a defender's far item / far fight lose to its post; a man close by is still fought
5. an escort trails the carrier 3 u on the side away from home; a CTF hunter heads for our dropped flag and
   stands on it (no loiter)

usage: python -I test_ctf_roles.py      -> "ctf roles OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot, Order, ESCORT_TRAIL, STAGE_WAIT  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

MAP = get_map("reach_50_panopticon")
RED, BLUE = MAP["flags"][0], MAP["flags"][1]


def team(rng, n=4):
    return {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), MAP, random.Random(i)) for i in range(1, n + 1)}


def players(spots, carrier=None, foes=()):
    out = [PlayerState(i, 0, f"b{i}", p, has_flag=i == carrier) for i, p in spots.items()]
    out += [PlayerState(10 + k, 1, f"e{k}", p) for k, p in enumerate(foes)]
    return out


def main():
    testdata.need_lidar("reach_50_panopticon")
    fails = []
    rng = random.Random(3)
    bots = team(rng)
    d = Director(0, MAP, bots, rng=random.Random(0))
    near_red = {1: RED + Vec(2, 0, 0), 2: RED + Vec(-3, 2, 0), 3: RED + Vec(0, 4, 0), 4: RED + Vec(4, 3, 0)}
    dropped = BLUE + Vec(8, -3, 0)            # our flag, lying by their base
    # 1. standoff
    flags = {0: FlagState(0, RED, dropped, "dropped"), 1: FlagState(1, BLUE, near_red[1], "carried", 1)}
    snap = Snapshot(10.0, players(near_red, carrier=1, foes=[BLUE]), flags, mode="ctf")
    d.assign_roles(10.0, snap)
    roles = sorted(d.roles[i] for i in (2, 3, 4))
    if d.roles.get(1) != "runner" or roles != ["escort", "hunter", "hunter"]:
        fails.append(f"standoff roles {d.roles}, want runner + escort + 2 hunters")
    posts = MAP["holds"][0][1:]
    want = max(posts, key=lambda h: dist(h, dropped))
    if bots[1].order.point != want:
        fails.append(f"standoff carrier goes to {bots[1].order.point}, want the far post {want}")
    # 2. our flag home: runner home, two escorts
    d2 = Director(0, MAP, team(rng), rng=random.Random(0))
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, near_red[1], "carried", 1)}
    snap = Snapshot(10.0, players(near_red, carrier=1, foes=[BLUE]), flags, mode="ctf")
    d2.assign_roles(10.0, snap)
    if d2.bots[1].order.point != RED or sorted(d2.roles[i] for i in (2, 3, 4)).count("escort") != 2:
        fails.append(f"carrier with our flag home: {d2.roles}, point {d2.bots[1].order.point}")
    # 3. a capture with our flag out: the rule is off
    d3 = Director(0, MAP, team(rng), rng=random.Random(0))
    flags = {0: FlagState(0, RED, dropped, "dropped"), 1: FlagState(1, BLUE, BLUE, "home")}
    for t, sc in ((1.0, 0), (1.5, 1)):
        d3.update(t, Snapshot(t, players(near_red, foes=[BLUE]), flags, score={0: sc, 1: 0}, mode="ctf", score_limit=3))
    if d3.home_rule:
        fails.append("scored with our flag out: home_rule still on")
    # 4. keep_role
    b = bots[2]
    post = MAP["holds"][0][1]
    b.order = Order("defender", post)
    me = PlayerState(2, 0, "b2", post + Vec(2, 0, 0))
    snap = Snapshot(20.0, [me], {}, mode="ctf")
    far_item, far_obj = post + Vec(0, 30, 0), ("objective", post)
    scores = {("item", far_item): 1.2, far_obj: 0.71, ("hunt", post + Vec(-25, 0, 0)): 1.0}
    b.keep_role(scores, me, snap, [])
    if scores[("item", far_item)] >= 0.71 or scores[("hunt", post + Vec(-25, 0, 0))] >= 0.71:
        fails.append(f"defender at its post: far item / hunt kept their weight {scores}")
    me_far = PlayerState(2, 0, "b2", post + Vec(0, 25, 0))
    scores = {("item", far_item): 1.2}
    b.keep_role(scores, me_far, snap, [])
    best = max(scores, key=scores.get)
    if best[0] != "objective":
        fails.append(f"defender 25 u from its post picks {best}, want its post")

    foe_close = post + Vec(2 + 5, 0, 0)
    b.per.beliefs[50] = Belief(foe_close, Vec(), 20.0, True, "eyes")
    b.per.beliefs[51] = Belief(post + Vec(0, -40, 0), Vec(), 20.0, True, "eyes")
    scores = {("fight", 50): 1.7, ("fight", 51): 1.7}
    b.keep_role(scores, me, snap, [50, 51])
    if scores[("fight", 50)] != 1.7 or scores[("fight", 51)] >= 1.0:
        fails.append(f"defender fights: close {scores[('fight', 50)]} (want 1.7), far {scores[('fight', 51)]} (want < 1)")
    # 5. escort trail, hunter on our dropped flag
    e = bots[3]
    e.order = Order("escort", RED)
    c_pos = RED + Vec(-12, 4, 0)
    snap = Snapshot(30.0, [PlayerState(1, 0, "b1", c_pos, has_flag=True), PlayerState(3, 0, "b3", c_pos + Vec(-10, 0, 0))],
                    {}, mode="ctf")
    q = e.live_point(snap.player(3), snap)
    want_d = math.hypot(ESCORT_TRAIL, 1.5)
    if q is None or not (abs(dist(q, c_pos) - want_d) < 0.01 or q == c_pos) or (q != c_pos and dist(q, RED) <= dist(c_pos, RED)):
        fails.append(f"escort point {q}: want {want_d:.2f} u off the carrier at {c_pos}, away from home")
    h = bots[4]
    h.order = Order("hunter", dropped)
    hp = PlayerState(4, 0, "b4", dropped + Vec(0, 2, 0))          # inside loiter range
    flags = {0: FlagState(0, RED, dropped, "dropped"), 1: FlagState(1, BLUE, BLUE, "home")}
    shooter = dropped + Vec(20, 0, 0)          # shot at by a man out of sight (hunt 1.6 beats a plain objective)
    snap = Snapshot(40.0, [hp, PlayerState(60, 1, "e", shooter)], flags, mode="ctf")
    if h.live_point(hp, snap) != dropped:
        fails.append(f"hunter point {h.live_point(hp, snap)}, want our dropped flag {dropped}")
    h.per.beliefs[60] = Belief(shooter, Vec(), 39.6, False, "hit")
    h.next_decide = 0.0
    h.think(40.0, 1 / 30, snap, lambda a, b_: dist(b_, shooter) > 3, lambda a, b_, **k: b_, [])
    if h.goal != ("objective", dropped):
        fails.append(f"hunter goal {h.goal}, want our dropped flag over a hunt")
    if getattr(h, "loiter_pt", None) is not None:
        fails.append(f"hunter loiters at {h.loiter_pt} instead of standing on our flag")
    # 6. in play (decide): a defender 25 u from its post leaves a man in view far from both alone and goes back
    g = Bot(7, 0, make_profile("top", "objector", random.Random(7)), MAP, random.Random(7))
    g.order = Order("defender", post)
    gp, foe = post + Vec(0, 25, 0), post + Vec(12, 25, 0)
    goals, t = [], 50.0
    while t < 52.0:
        sn = Snapshot(t, [PlayerState(7, 0, "b7", gp), PlayerState(20, 1, "e", foe, yaw=0.0)], {}, mode="ctf")
        g.think(t, 1 / 30, sn, lambda a, b_: True, lambda a, b_, **k: b_, [])
        goals.append(g.goal[0])
        t += 1 / 30
    if goals[-1] != "objective" or "fight" in goals[-20:]:
        fails.append(f"defender far from its post: goals end {goals[-5:]}, want back to its post")
    # 7. on the enemy flag, fighting or not, the bot holds action (its pickup); never on its own flag
    r = Bot(8, 0, make_profile("top", "rusher", random.Random(8)), MAP, random.Random(8))
    r.order = Order("runner", BLUE)
    home_flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, BLUE, "home")}
    for t in (60.0, 60.5):
        sn = Snapshot(t, [PlayerState(8, 0, "b8", BLUE + Vec(0.5, 0, 0)), PlayerState(21, 1, "e", BLUE + Vec(6, 0, 0))],
                      home_flags, mode="ctf")
        a = r.think(t, 1 / 30, sn, lambda a_, b_: True, lambda a_, b_, **k: b_, [])
    if not a.action:
        fails.append(f"runner on the enemy flag (goal {r.goal}) does not hold action")
    sn = Snapshot(61.0, [PlayerState(8, 0, "b8", RED + Vec(0.3, 0, 0))], home_flags, mode="ctf")
    if r.think(61.0, 1 / 30, sn, lambda a_, b_: True, lambda a_, b_, **k: b_, []).action:
        fails.append("bot on its own flag holds action")
    # 8. a runner keeps to its line: an item 15 u to the side and a man 20 u behind lose to the flag; a man on the line
    #    12 u ahead is still fought
    q = Bot(9, 0, make_profile("top", "rusher", random.Random(9)), MAP, random.Random(9))
    q.order = Order("runner", BLUE)
    qp = BLUE + (RED - BLUE) * 0.5
    me = PlayerState(9, 0, "b9", qp)
    ahead = qp + (BLUE - qp) * (12.0 / dist(BLUE, qp))
    behind = qp + (RED - qp) * (20.0 / dist(RED, qp))
    q.per.beliefs[70] = Belief(behind, Vec(), 70.0, True, "eyes")
    q.per.beliefs[71] = Belief(ahead, Vec(), 70.0, True, "eyes")
    side = qp + Vec(0, 15, 0)
    scores = {("item", side): 1.2, ("fight", 70): 1.7, ("fight", 71): 1.7}
    q.keep_role(scores, me, Snapshot(70.0, [me], home_flags, mode="ctf"), [70, 71])
    top = max(scores, key=scores.get)
    if top[0] == "item" or scores[("fight", 70)] >= 1.0 or scores[("fight", 71)] != 1.7:
        fails.append(f"runner off its line: {scores}")
    # 9. both flags home, four of us: the runner gets escorts that go with it (Order.target = the runner), and an escort
    #    follows that runner
    d9 = Director(0, MAP, team(rng), rng=random.Random(0))
    spots = {1: RED + Vec(2, 0, 0), 2: RED + Vec(-3, 2, 0), 3: RED + Vec(0, 4, 0), 4: RED + Vec(4, 3, 0)}
    d9.assign_roles(10.0, Snapshot(10.0, players(spots, foes=[BLUE] * 4), home_flags, mode="ctf"))
    run_ids = [i for i in d9.roles if d9.roles[i] == "runner"]
    esc = [d9.bots[i] for i in d9.roles if d9.roles[i] == "escort"]
    if not run_ids or not esc or any(b.order.target != run_ids[0] for b in esc):
        fails.append(f"both home: roles {d9.roles}, escort targets {[b.order.target for b in esc]}, runner {run_ids}")
    else:
        e9 = esc[0]
        rp = BLUE + (RED - BLUE) * 0.5
        sn = Snapshot(11.0, [PlayerState(run_ids[0], 0, "r", rp), PlayerState(e9.id, 0, "e", RED)], home_flags, mode="ctf")
        lp = e9.live_point(sn.player(e9.id), sn)
        if lp is None or dist(lp, rp) > 4.0:
            fails.append(f"escort of the runner goes to {lp}, want near the runner at {rp}")
    # 10. a runner 12 u from their flag with nobody near waits (holds) at most STAGE_WAIT s; with a mate at 5 u it goes
    st = Bot(10, 0, make_profile("top", "objector", random.Random(10)), MAP, random.Random(10))
    st.order = Order("runner", BLUE)
    sp = BLUE + (RED - BLUE) * (12.0 / dist(RED, BLUE))
    alone = Snapshot(80.0, [PlayerState(10, 0, "s", sp)], home_flags, mode="ctf")
    scores = {("objective", BLUE): 1.0}
    st.keep_role(scores, alone.player(10), alone, [])
    if max(scores, key=scores.get)[0] != "hold":
        fails.append(f"lone runner by their flag: {scores}, want it to wait")
    late = Snapshot(80.0 + STAGE_WAIT + 0.5, [PlayerState(10, 0, "s", sp)], home_flags, mode="ctf")
    scores = {("objective", BLUE): 1.0}
    st.keep_role(scores, late.player(10), late, [])
    if max(scores, key=scores.get)[0] != "objective":
        fails.append(f"lone runner after {STAGE_WAIT} s: {scores}, want it to go in")
    st.stage_since = None
    mate = Snapshot(90.0, [PlayerState(10, 0, "s", sp), PlayerState(11, 0, "m", sp + Vec(3, 0, 0))], home_flags, mode="ctf")
    scores = {("objective", BLUE): 1.0}
    st.keep_role(scores, mate.player(10), mate, [])
    if max(scores, key=scores.get)[0] != "objective":
        fails.append(f"runner with a mate by their flag: {scores}, want it to go in")
    # 10b. guide 07 (Multi Flag, setup): the pull starts when the base is clear, at least two enemies dead or none known
    # within Medium band (10 u) of their flag (live, Boardwalk: 3 of 6 carriers shot within 5 u of the stand by the
    # defender still on it); held at most STAGE_CLEAR_WAIT s. Since (bot.STAGE_NEED_CLEAR False) a runner with company
    # goes in guarded or not: both Halo 3 CTF games went 0-0 live, the sim's runners on The Pit held 39% of their time
    # for a clear base that 8v8 never gives (tools/test_ctf_grab.py)
    from brain.bot import STAGE_CLEAR_WAIT, STAGE_NEED_CLEAR
    st.stage_since = None
    st.per.beliefs[20] = Belief(BLUE + Vec(2, 0, 0), Vec(), 99.0, True, "eyes")
    pl = [PlayerState(10, 0, "s", sp), PlayerState(11, 0, "m", sp + Vec(3, 0, 0)), PlayerState(20, 1, "d", BLUE + Vec(2, 0, 0))]
    for t, extra, want, why in ((100.0, [], "hold" if STAGE_NEED_CLEAR else "objective", "a defender on their flag"),
                                (100.0 + STAGE_CLEAR_WAIT + 0.5, [], "objective", "after the longest wait"),
                                (130.0, [PlayerState(21, 1, "x", RED, alive=False), PlayerState(22, 1, "y", RED, alive=False)],
                                 "objective", "two of them dead")):
        if t == 130.0:
            st.stage_since = None
        st.per.beliefs[20].t = t
        sn = Snapshot(t, pl + extra, home_flags, mode="ctf")
        scores = {("objective", BLUE): 1.0}
        st.keep_role(scores, sn.player(10), sn, [20])
        if max(scores, key=scores.get)[0] != want:
            fails.append(f"runner with a mate by their flag, {why}: {scores}, want {want}")
    st.per.beliefs.pop(20)
    st.stage_since = None
    # 12. a carrier never switches guns (it drops the objective) and swings at a man at arm's length
    cb = Bot(12, 0, make_profile("top", "rusher", random.Random(12)), MAP, random.Random(12))
    cb.order = Order("runner", RED)
    swung, t = False, 95.0
    while t < 96.5:
        sn = Snapshot(t, [PlayerState(12, 0, "c", RED + Vec(-8, 0, 0), has_flag=True, weapons=["dmr", "magnum", "unknown"],
                                      weapon="unknown"), PlayerState(22, 1, "e", RED + Vec(-7.0, 0, 0))],
                      home_flags, mode="ctf")
        a = cb.think(t, 1 / 30, sn, lambda a_, b_: True, lambda a_, b_, **k: b_, [])
        if a.weapon >= 0:
            fails.append(f"carrier asked for slot {a.weapon}")
            break
        swung = swung or a.melee
        t += 1 / 30
    if not swung:
        fails.append("carrier with a man at 1 u never swung")
    # 13. a fight past 6 u where nobody gets hurt for 6 s (shots into a rail) loses weight; a hit restarts the clock;
    #     a close one never
    sb = Bot(13, 0, make_profile("strong", "flanker", random.Random(13)), MAP, random.Random(13))
    near_foe, far_foe = RED + Vec(4, 0, 0), RED + Vec(12, 0, 0)
    sb.per.beliefs[30] = Belief(far_foe, Vec(), 0.0, True, "eyes")
    sb.per.beliefs[31] = Belief(near_foe, Vec(), 0.0, True, "eyes")
    got = {}
    for k in range(40):
        t = 200.0 + 0.25 * k
        hurt = 0.6 if k == 8 else 1.0          # the far man takes a hit at 2 s: the clock restarts there
        sn = Snapshot(t, [PlayerState(13, 0, "s", RED), PlayerState(30, 1, "f", far_foe, shield=hurt if k >= 8 else 1.0),
                          PlayerState(31, 1, "n", near_foe)], {}, mode="slayer")
        sc = {("fight", 30): 1.7, ("fight", 31): 1.7}
        sb.break_stalemates(t, sn.player(13), sn, sc)
        got[round(t - 200.0, 2)] = (sc[("fight", 30)], sc[("fight", 31)])
    if got[5.0][0] != 1.7 or got[9.0][0] >= 1.0 or any(v[1] != 1.7 for v in got.values()):
        fails.append(f"stalemate: far 5 s {got[5.0]}, 9 s {got[9.0]} (want 1.7 then < 1, 6 s after the hit; the near man always 1.7)")
    # 14. One Flag: attacking (only their flag) nobody defends, a runner and escorts go; defending (only ours) all but a
    #     forward pair hold it; no flag of either team read: Slayer slots, no crash
    d14 = Director(0, MAP, team(rng), rng=random.Random(0))
    att = d14.role_slots(5.0, Snapshot(5.0, players(spots, foes=[BLUE] * 4), {1: FlagState(1, BLUE, BLUE, "home")},
                                       mode="ctf"), 4)
    dfn = d14.role_slots(5.0, Snapshot(5.0, players(spots, foes=[BLUE] * 4), {0: FlagState(0, RED, RED, "home")},
                                       mode="ctf"), 4)
    neutral = d14.role_slots(5.0, Snapshot(5.0, players(spots, foes=[BLUE] * 4), {8: FlagState(8, RED, RED, "home")},
                                           mode="ctf"), 4)
    ra, rd = [r for r, p, f in att[:4]], [r for r, p, f in dfn[:4]]
    if "defender" in ra or "runner" not in ra or rd.count("defender") < 2 or "runner" in rd or not neutral:
        fails.append(f"one flag: attacking {ra}, defending {rd}, neutral {len(neutral)} slots")
    # the round with the sides swapped (Boardwalk): blue's flag lives on RED's stand; red attacks and scores on the
    # other stand; blue defends posts at the flag, not at its own empty base
    d15 = Director(0, MAP, team(rng), rng=random.Random(0))
    swapped = {1: FlagState(1, RED, RED, "home")}
    if d15.capture_point(Snapshot(5.0, [], swapped, mode="ctf")) != BLUE:
        fails.append("one flag on red's stand: red's capture point is not the other stand")
    d16 = Director(1, MAP, {i: Bot(i, 1, make_profile("top", "camper", random.Random(i)), MAP, random.Random(i))
                            for i in range(1, 5)}, rng=random.Random(0))
    blue_def = d16.role_slots(5.0, Snapshot(5.0, [PlayerState(i, 1, f"b{i}", RED + Vec(i, 0, 0)) for i in range(1, 5)],
                                            swapped, mode="ctf"), 4)
    posts = [p for r, p, f in blue_def if r == "defender"]
    if not posts or any(dist(p, RED) > 8 for p in posts):
        fails.append(f"blue defending its flag on red's stand: posts {[round(dist(p, RED), 1) for p in posts]} u from it")
    # 11. King of the Hill: one on the hill, the rest on spots around it; Oddball: two guards on our carrier
    hill = MAP["spots"]["hills"][1]          # a real Boardwalk hill (the mid point is a sunken plaza nothing sees)
    dk = Director(0, MAP, team(rng), rng=random.Random(0))
    slots = dk.role_slots(5.0, Snapshot(5.0, players(spots), mode="king", hill=hill, hill_r=3.0), 4)
    if [r for r, p, f in slots[:4]].count("defender") != 1 or any(r == "mid" and dist(p, hill) < 3.0 for r, p, f in slots):
        fails.append(f"king slots {[(r, round(dist(p, hill), 1)) for r, p, f in slots[:4]]}: want one on the hill")
    # the scorer stays in the hill (guide 19 KOTH-STATIC-01/02): a gun 8 u off and a hunt outside it are a quarter;
    # with a man of theirs in the hill it waits outside for company, alone (KOTH-STATIC-10); the whole team
    # goes in (hill_contested) only while the team knows a man in it
    kb = Bot(14, 0, make_profile("top", "objector", random.Random(14)), MAP, random.Random(14))
    kb.order = Order("defender", hill)
    kp = PlayerState(14, 0, "k", hill)
    sn = Snapshot(300.0, [kp], mode="king", hill=hill, hill_r=3.0)
    scores = {("item", hill + Vec(8, 0, 0)): 1.2, ("hunt", hill + Vec(0, -7, 0)): 1.0}
    kb.keep_role(scores, kp, sn, [])
    if max(scores.values()) > 0.31:
        fails.append(f"king scorer on the hill: a gun 8 u off / a hunt 7 u off kept {scores} (want a quarter)")
    kb.per.beliefs[40] = Belief(hill + Vec(0.5, 0, 0), Vec(), 310.0, True, "eyes")
    kp = PlayerState(14, 0, "k", hill + Vec(8, 0, 0))
    sn = Snapshot(310.0, [kp, PlayerState(40, 1, "x", hill + Vec(0.5, 0, 0))], mode="king", hill=hill, hill_r=3.0)
    scores = {("objective", hill): 1.0}
    kb.keep_role(scores, kp, sn, [40])
    if max(scores, key=scores.get)[0] != "hold":
        fails.append(f"king scorer alone 8 u from a hill they hold: {scores}, want it to wait")
    ks = Snapshot(5.0, players(spots), mode="king", hill=hill, hill_r=3.0)
    free_hill = dk.hill_contested(5.0, ks)
    next(iter(dk.bots.values())).per.beliefs[40] = Belief(hill + Vec(0.5, 0, 0), Vec(), 5.0, True, "eyes")
    if free_hill or not dk.hill_contested(5.0, ks):
        fails.append(f"hill contested: free {free_hill}, a man in it {dk.hill_contested(5.0, ks)}")
    ob = Snapshot(5.0, players(spots, carrier=1), mode="oddball", ball=spots[1], ball_carrier=1)
    slots = dk.role_slots(5.0, ob, 4)
    if [r for r, p, f in slots[:4]].count("escort") != 2:
        fails.append(f"oddball slots {[r for r, p, f in slots[:4]]}: want two guards")
    # a runner standing on their flag with a gun the map's names miss ("unknown" all along) presses Use, looking at the
    # flag (live Boardwalk: the old read took "unknown" for the flag in hand and held Use back 50 s, no pickup)
    blue = MAP["flags"][1]
    rb = Bot(3, 0, make_profile("top", "rusher", random.Random(3)), MAP, rng=random.Random(3))
    rb.order = Order("runner", blue)
    pressed, looked, yaw, pitch = 0, 0, 0.0, 0.0
    for k in range(120):                      # (its first read counts as just turned: the last 60 ticks are judged)
        t = 100.0 + k / 30
        me = PlayerState(3, 0, "r", Vec(blue.x + 0.3, blue.y, blue.z), alive=True, weapon="unknown",
                         weapons=["assault_rifle", "unknown"], yaw=yaw, pitch=pitch)
        sn = Snapshot(t, [me], {0: FlagState(0, MAP["flags"][0], MAP["flags"][0], "home", -1),
                                1: FlagState(1, blue, blue, "home", -1)}, mode="ctf")
        a = rb.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
        yaw, pitch = a.yaw, a.pitch           # (the view it turned to: no turn is instant, profiles.TURN)
        pressed += bool(a.action) and k >= 60
        looked += a.pitch < -0.3 and k >= 60
    if pressed < 30 or looked < 30:
        fails.append(f"runner on their flag with an unknown gun: Use on {pressed} of 60 ticks, looking down {looked}")
    # urgency: while a man runs with our flag a gun lying 8 u off waits (one theft drew 66 gun choices from its 6
    # defenders in 10 s, Boardwalk); with our flag home it is scored as before
    red = MAP["flags"][0]
    gb = Bot(4, 0, make_profile("top", "rusher", random.Random(4)), MAP, rng=random.Random(4))
    gun = red + Vec(8.0, 0.0, 0.0)
    gb.best_item = lambda now, me: (gun, 0.86)
    item_score = {}
    for state in ("home", "carried"):
        me = PlayerState(4, 0, "g", red + Vec(1.0, 0.0, 0.0), alive=True, weapon="assault_rifle", weapons=["assault_rifle"],
                         ammo=[30])
        thief = PlayerState(7, 1, "x", red + Vec(30.0, 0.0, 0.0), alive=True, has_flag=state == "carried")
        sn = Snapshot(120.0, [me, thief], {0: FlagState(0, red, thief.pos if state == "carried" else red, state,
                                                        7 if state == "carried" else -1),
                                           1: FlagState(1, blue, blue, "home", -1)}, mode="ctf")
        gb.decide(120.0, me, sn)
        item_score[state] = gb.last_scores.get(("item", gun), 0.0)
    if not (item_score["home"] > 0.8 and item_score["carried"] < 0.3):
        fails.append(f"a gun 8 u off while a man runs with our flag: scored {item_score} (want about 0.86 home, a quarter carried)")
    # a Normal defender's guns stay in its area (live Boardwalk, Normal / Heroic: at three of four pulls no
    # defender was home, off 19-31 u after a gun or a radar dot; the leash took off only 38% for Normal)
    nd = Bot(5, 0, make_profile("average", "camper", random.Random(5)), MAP, rng=random.Random(5))
    post = red + Vec(4.0, 0.0, 0.0)
    nd.order = Order("defender", post)
    far_gun = post + Vec(18.0, 0.0, 0.0)
    nd.best_item = lambda now, me: (far_gun, 0.86)
    me = PlayerState(5, 0, "d", post, alive=True, weapon="assault_rifle", weapons=["assault_rifle"], ammo=[30])
    sn = Snapshot(130.0, [me], {0: FlagState(0, red, red, "home", -1), 1: FlagState(1, blue, blue, "home", -1)}, mode="ctf")
    nd.decide(130.0, me, sn)
    if nd.last_scores.get(("item", far_gun), 0.0) > 0.3:
        fails.append(f"a Normal defender, a gun 18 u from its post: scored {nd.last_scores.get(('item', far_gun), 0.0):.2f} "
                     f"(want a quarter: it stays in its area)")
    # Slayer, even score (guide 19 SLAY-CORE-07): two of theirs dead and the team pushes (posture 0.7 and up, every bot a
    # hunter); all four alive, the standard plan (an anchor on a post)
    dn = Director(0, MAP, team(rng), rng=random.Random(0))
    for t, dead in ((1.0, 0), (3.5, 2)):
        ps = players(spots, foes=[BLUE + Vec(k, 0, 0) for k in range(4)])
        for p in ps[4:4 + dead]:
            p.alive = False
        dn.update(t, Snapshot(t, ps, score={0: 10, 1: 10}, mode="slayer", score_limit=50))
        roles = sorted(dn.roles.values())
        if (dead == 2) != (dn.posture.value >= 0.7 and roles == ["hunter"] * 4):
            fails.append(f"slayer, {dead} of theirs dead: posture {dn.posture.value:.2f}, roles {roles}")
    # map brain MAP-09: our carrier goes home by a lane, the one the threat map rates quiet (pick_route: on Blood Gulch
    # red's dark-side sneak route, the other way), and keeps it while home stays put, even once that lane turns hot (it
    # ran home straight, back through the fight). (Panopticon's three lanes all lie in Mid: no lane to choose there.)
    bg = get_map("bloodgulch")
    dl = Director(0, bg, {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), bg, random.Random(i))
                          for i in range(1, 5)}, rng=random.Random(0))
    dark = tuple(bg["sneak"][0][0])

    def heat(zones, t):                        # every route's zones: level 10 in zones, else 0
        for p in list(bg["lanes"]) + [q for r in bg["sneak"][0] for q in r]:
            dl.threat[dl.zones.name(p)] = (10 if dl.zones.name(p) in zones else 0, t)
    heat({dl.zones.name(p) for p in list(bg["lanes"]) + list(bg["sneak"][0][1])}, 40.0)
    red, blue = bg["flags"][0], bg["flags"][1]
    men = lambda t: Snapshot(t, [PlayerState(1, 0, "b1", blue + Vec(1, 0, 0), has_flag=True)] +
                             [PlayerState(i, 0, f"b{i}", red + Vec(i, 0, 0)) for i in (2, 3, 4)],
                             {0: FlagState(0, red, red, "home"), 1: FlagState(1, blue, blue + Vec(1, 0, 0), "carried", 1)},
                             mode="ctf")
    dl.assign_roles(40.0, men(40.0))
    took = (dl.bots[1].order.via, list(dl.bots[1].via_left))
    heat({dl.zones.name(p) for p in dark}, 42.0)
    dl.assign_roles(42.0, men(42.0))
    if took != (dark[::-1], list(dark[::-1])) or dl.bots[1].order.via != dark[::-1] or dl.bots[1].order.point != red:
        fails.append(f"carrier's lane home: took {took}, then {dl.bots[1].order.via} to {dl.bots[1].order.point} "
                     f"(want the quiet dark side {dark[::-1]}, kept, home {red})")
    if fails:
        print("\n".join(fails))
        sys.exit(1)
    print("ctf roles OK")


if __name__ == "__main__":
    main()
