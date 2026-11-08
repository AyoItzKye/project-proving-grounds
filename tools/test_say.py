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
    again = d.role_slots(20.0, sn, 4)
    if [p for _, p, _ in again] != pts:
        fails.append("roam: the spots changed before ROAM_KEEP s (bots would trek back and forth)")
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
                              ("a way round", [Vec(-0.05 * k, 0.03 * k, 0) for k in range(100)], False)):
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
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print(f"say OK (follow me: 4 escorts on you; roam: holds ranked {sorted(got)} of {len(hs)}, apart, near; "
          "kept 30 s; the person's team only)")


if __name__ == "__main__":
    main()
