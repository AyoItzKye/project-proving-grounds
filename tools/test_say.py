"""The person's chat commands for his teammate bots (overlay.cpp chat_key -> tools/live_bots.py say_command ->
Director.say): "follow me" puts every bot of his team on escort with him as the lead, in any mode; "roam" gives each a
hold of its own (modes.find_holds: roofed, fewest ways in, least exposed rim), spread apart and near the team, out of the
open; a later command replaces the earlier one; the other team never hears it.

usage: python -I tools/test_say.py      -> "say OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.modes import holds  # noqa: E402
import botctl  # noqa: E402
import live_bots  # noqa: E402

M = get_map("reach_30_settlement")


def main():
    fails = []
    T = None
    team = {i: Bot(i, 0, make_profile("top", "rusher", random.Random(i)), M, random.Random(i)) for i in (1, 2, 3, 4)}
    d = Director(0, M, team, random.Random(1))
    T = d.terrain()
    hs = holds(T, M["name"], wait=True)
    me = hs[len(hs) // 2]["pos"]
    human = PlayerState(0, 0, "you", me, is_bot=False)
    mates = [PlayerState(i, 0, f"b{i}", me + Vec(i * 2.0, 0, 0)) for i in team]
    foe = PlayerState(9, 1, "foe", me + Vec(30, 0, 0))
    sn = Snapshot(10.0, [human] + mates + [foe], mode="ctf")
    before = d.role_slots(10.0, sn, 4)
    # 1. follow me: every bot escorts him by name, whatever the mode had them on
    d.say = "follow"
    d.assign_roles(11.0, sn)
    for i, b in team.items():
        lead = b.lead(sn.player(i), sn)
        if b.order.role != "escort" or lead is None or lead.id != 0:
            fails.append(f"follow me: bot {i} order {b.order.role} target {b.order.target} (want escort, lead you)")
    # 2. roam: each its own hold, out of the open (better than the map's typical hold), apart, near the team
    d.say, d.roam_picks = "roam", None
    slots = d.role_slots(12.0, sn, 4)
    pts = [p for _, p, _ in slots]
    ranks = {(round(h["pos"].x, 2), round(h["pos"].y, 2)): k for k, h in enumerate(hs)}
    got = [ranks.get((round(p.x, 2), round(p.y, 2))) for p in pts]
    if any(r != "defender" for r, _, _ in slots) or None in got:
        fails.append(f"roam: {[(r, p) for r, p, _ in slots]} (want defenders on the map's holds)")
    if any(Director.exposure(T, p) > Director.ROAM_OPEN for p in pts):
        fails.append(f"roam: a spot open to {max(Director.exposure(T, p) for p in pts):.2f} of the lines out (want <= "
                     f"{Director.ROAM_OPEN})")
    if any(dist(a, b) < 5.9 for k, a in enumerate(pts) for b in pts[k + 1:]):
        fails.append(f"roam: spots closer than 6 u apart {pts}")
    if any(dist(p, me) > Director.ROAM_NEAR + 5 for p in pts):
        fails.append(f"roam: a spot past {Director.ROAM_NEAR} u from the team")
    # (as covered, the nearer: no trek to a covered room across the map past covered ones by the team)
    c4 = me                                         # (round the person: say_slots)
    best = max(round(Director.exposure(T, p) / Director.ROAM_STEP) for p in pts)
    tied = sorted(dist(h["pos"], c4) for h in hs if dist(h["pos"], c4) <= Director.ROAM_NEAR
                  and round(Director.exposure(T, h["pos"]) / Director.ROAM_STEP) <= best)
    if tied and max(dist(p, c4) for p in pts) > tied[min(len(tied) - 1, 2 * len(pts))]:
        fails.append(f"roam: a spot {max(dist(p, c4) for p in pts):.1f} u off with {len(tied)} as covered nearer "
                     f"(the {2 * len(pts) + 1}th nearest {tied[min(len(tied) - 1, 2 * len(pts))]:.1f} u)")
    again = d.role_slots(20.0, sn, 4)
    if [p for _, p, _ in again] != pts:
        fails.append("roam: the spots changed before ROAM_KEEP s (bots would trek back and forth)")
    # 2c. round him, not the team's middle: bots on far spots do not drag the next picks further off (live Beachhead
    #     Firefight Nov 8: spots 26-42 u from the person)
    far = [PlayerState(i, 0, f"b{i}", me + Vec(40.0, 0, 0)) for i in team]
    d.roam_picks = None
    off = [dist(p, me) for _, p, _ in d.role_slots(12.5, Snapshot(12.5, [human] + far + [foe], mode="ctf"), 4)]
    if max(off) > 25.0:
        fails.append(f"roam: spots {[round(x, 1) for x in off]} u from the person with the bots 40 u off (want within 25 u: "
                     "round him, not the team middle)")
    d.roam_picks = None
    # 2d. Beachhead Firefight as live (Nov 8, 083208): the person in the pavilion, 3 bots; never the room 27 u off and
    #     4 u down (-189.9, 45.5) that a 0.00 spot won over covered ones beside him by exact cover
    BH = get_map("reach_ff50_park")
    bteam = {i: Bot(i, 0, make_profile("top", "rusher", random.Random(i)), BH, random.Random(i)) for i in (1, 2, 3)}
    bd = Director(0, BH, bteam, random.Random(1))
    holds(bd.terrain(), BH["name"], wait=True)          # (the holds found first, as live)
    bd.say = "roam"
    you_bh = PlayerState(0, 0, "you", Vec(-162.8, 60.1, -33.5), is_bot=False)
    bmates = [PlayerState(i, 0, f"b{i}", Vec(-162.8 + i, 57.0, -33.5)) for i in bteam]
    bsn = Snapshot(10.0, [you_bh] + bmates, mode="firefight")
    bpts = [p for _, p, _ in bd.role_slots(10.0, bsn, 3)]   # (by cover alone: 2 by him, 2 rooms 30 u off, 4 u down)
    if any(dist(p, Vec(-189.9, 45.5, -37.7)) < 2.0 for p in bpts) or max(dist(p, you_bh.pos) for p in bpts) > 20.0:
        fails.append(f"roam on Beachhead: spots {[(round(p.x, 1), round(p.y, 1)) for p in bpts]} (want all within 20 u "
                     f"of the person, not the low room at (-189.9, 45.5))")
    # 2b. a death re-deals no spot: each living bot keeps its own (live Beachhead Firefight Nov 8: one bot's spot flipped
    #     30 u back and forth five times as teammates died and came back)
    d.assign_roles(21.0, sn)
    mine = {i: b.order.point for i, b in team.items()}
    team[1].on_death(9)
    dead1 = [PlayerState(1, 0, "b1", Vec(), alive=False)] + [p if p.id != 2 else PlayerState(2, 0, "b2", mine[1])
                                                               for p in mates[1:]]        # (bot 2 by bot 1's spot)
    sn2 = Snapshot(22.0, [human] + dead1 + [foe], mode="ctf")
    d.assign_roles(22.0, sn2)
    moved = {i: (mine[i], b.order.point) for i, b in team.items() if b.order.point != mine[i]}
    if len(set((p.x, p.y) for p in mine.values())) < 4 or moved:
        fails.append(f"roam: spots re-dealt after bot 1 died: {moved}")
    # 3. back to the mode's own roles: no command
    d.say = None
    if d.role_slots(13.0, sn, 4) != before:
        fails.append("no command: the mode's own roles changed")
    # 4. the live path: botctl.said's count, a stale count ignored, the person's team only
    m = bytearray(botctl.SIZE)
    other = Director(1, M, {}, random.Random(2))
    dirs = {0: Director(0, M, {}, random.Random(3)), 1: other}
    live_bots.botctl.notice = lambda *a: None
    m[botctl.OFF_SAY:botctl.OFF_SAY + 2] = bytes((4, 2))      # a command from before the brain started
    live_bots.SAY["seen"] = None
    if live_bots.say_command(m, sn, dirs, 1.0) is not None or getattr(dirs[0], "say", None):
        fails.append("a command typed before the brain started was acted on")
    m[botctl.OFF_SAY:botctl.OFF_SAY + 2] = bytes((5, 1))
    if live_bots.say_command(m, sn, dirs, 2.0) != ("follow", 0) or dirs[0].say != "follow" or getattr(other, "say", None):
        fails.append("follow me: not given to the person's team alone")
    if live_bots.say_command(m, sn, dirs, 3.0) is not None:
        fails.append("the same command read twice")
    # 5. the no-progress check (Bot.unstuck, live Boardwalk Nov 8): rocking 0.5-0.8 u by one spot for 9 s, the goal 15 u
    # off, counts as stuck; a way round that walks 4 u away from the goal does not
    from brain.core import Action
    from brain.bot import NO_PROGRESS_S
    for label, path, want in (("rocking in place", [Vec(0.7 * (k % 2), 0, 0) for k in range(100)], True),
                              ("a way round", [Vec(-0.05 * k, 0.03 * k, 0) for k in range(100)], False),
                              # (at its spot: loitering 2-3 u off it is no stall, live Beachhead roam Nov 8)
                              ("loitering 2.5 u off its spot", [Vec(12.5 + 0.7 * (k % 2), 0, 0) for k in range(100)],
                               False)):
        rb = Bot(5, 0, make_profile("top", "rusher", random.Random(5)), M, random.Random(5))
        rb.notes, rb.goal = [], ("objective", Vec(15.0, 0, 0) + me)
        stuck = False
        for k, q in enumerate(path):
            t = 100.0 + k * (NO_PROGRESS_S + 1.0) / len(path)
            rb.wiggle_until = 0.0
            rb.unstuck(t, PlayerState(5, 0, "r", me + q), Action(forward=1.0), sn)
            stuck = stuck or rb.wiggle_until > t
        if stuck != want:
            fails.append(f"no-progress check, {label}: stuck {stuck} (want {want})")
    # 5b. the person's command holds over the bot's own missions: an anti-vehicle fetch 20 u off loses under "follow
    #     me", as any trip past its leash; with no command it outranks the post as before (live Beachhead Firefight
    #     Nov 8, a Wraith wave: the bots 9-17 u off for plasma pistols, 61-72% within 6 u of the person)
    from brain.bot import Order as _Order
    you = PlayerState(0, 0, "you", me, is_bot=False)
    for said, want_cut in (("follow", True), ("", False)):
        mb = Bot(7, 0, make_profile("top", "rusher", random.Random(7)), M, random.Random(7))
        mb.order = _Order("escort", me, target=0, said=said)
        mb.mission_keys = (("item", me + Vec(20.0, 0, 0)),)
        sc = {mb.mission_keys[0]: 2.4}
        mme = PlayerState(7, 0, "m", me + Vec(2.0, 0, 0))
        mb.keep_role(sc, mme, Snapshot(50.0, [you, mme], mode="firefight"), set())
        if (sc[mb.mission_keys[0]] < 2.4) != want_cut:
            fails.append(f"mission under {said or 'no command'}: score {sc[mb.mission_keys[0]]:.2f} (want "
                         f"{'cut' if want_cut else 'kept 2.40'})")
        # (a pickup 9 u from him, inside the 12 u leash: only beside him under "follow me", live Beachhead 085922)
        mb.mission_keys, key9 = (), ("item", me + Vec(9.0, 0, 0))
        sc = {key9: 1.5}
        mb.keep_role(sc, mme, Snapshot(50.0, [you, mme], mode="firefight"), set())
        if (sc[key9] < 1.5) != want_cut:
            fails.append(f"a pickup 9 u off under {said or 'no command'}: score {sc[key9]:.2f} (want "
                         f"{'cut' if want_cut else 'kept 1.50'})")
    # 6. a roam holder fights from its spot: aim on the man, the walk back to its spot
    #    (live Beachhead Firefight Nov 8: roam spots covered, the bots 8-18 u off them in fights, in the open)
    import math
    from brain.bot import Belief, Order
    from brain.core import Action
    spot = Vec(0.0, 0.0, 0.0)
    for label, said, role, at, foe, want in (("roam, 5 u off, the man 12 u off", "roam", "defender", Vec(5, 0, 0),
                                              Vec(5, 12, 0), True),
                                             ("a guard (its own play), 5 u off", "gen", "defender", Vec(5, 0, 0), Vec(5, 12, 0), False),
                                             ("roam, on its spot", "roam", "defender", Vec(1, 0, 0), Vec(5, 12, 0), False),
                                             ("roam, the man 3 u off", "roam", "defender", Vec(5, 0, 0), Vec(5, 3, 0), False),
                                             ("an escort", "follow", "escort", Vec(5, 0, 0), Vec(5, 12, 0), False)):
        hb = Bot(6, 0, make_profile("top", "camper", random.Random(6)), M, random.Random(6))
        hb.order = Order(role, spot, said=said)
        hb.per.beliefs[9] = Belief(foe, Vec(), 1.0, True, "eyes")
        act = Action(yaw=math.atan2(foe.y - at.y, foe.x - at.x))
        aim = act.yaw
        went = hb.hold_spot(PlayerState(6, 0, "h", at), act, "fight", 9)
        head = act.yaw + math.atan2(act.strafe, act.forward)
        back = abs(math.atan2(math.sin(head - math.atan2(-at.y, -at.x)), math.cos(head - math.atan2(-at.y, -at.x))))
        if went != want or (want and (back > 0.2 or act.yaw != aim)):
            fails.append(f"hold spot, {label}: walked back {went}, heading off the spot by {back:.2f} rad, aim kept "
                         f"{act.yaw == aim} (want {want})")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print(f"say OK (follow me: 4 escorts on you; roam: holds ranked {sorted(got)} of {len(hs)}, apart, near; "
          "kept 30 s; the person's team only)")


if __name__ == "__main__":
    main()
