"""The two teams get the same brain: think order and roster (tools/live_bots.py think_order, roster_pick).

Live B21-B28 / S14: team 1 (players 7-12) did worse on both maps in both roles. Two causes keyed on the join order:
1. the brain thought and sent the bots' sticks in index order each tick (median 35 ms, p90 109 ms), so team 1's six
   always acted on the oldest snapshot, last; now the teams interleave and the first team swaps every tick: over two
   ticks each team's mean place is the same.
2. styles and tiers were dealt round-robin over ALL bots by join order: team 0 got rusher / flanker / camper /
   objector / spammer / grudger, team 1 sniper / rusher / flanker / camper / objector / spammer, with the tiers shifted
   (team 1's tops a sniper, a flanker, an objector). Now dealt per team: the two rosters mirror.

usage: python -I test_team_fair.py      -> "team_fair OK"
"""
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)


def main():
    import live_bots
    fails = []
    bots = {i: types.SimpleNamespace(game_team=0 if i <= 6 else 1) for i in range(1, 13)}
    if not hasattr(live_bots, "think_order"):
        fails.append("1. no think_order: the bots think in index order, team 1 always last")
    else:
        place = {0: [], 1: []}
        for tick in (0, 1):
            for k, (i, b) in enumerate(live_bots.think_order(bots, tick)):
                place[b.game_team].append(k)
        m0, m1 = (sum(v) / len(v) for v in (place[0], place[1]))
        if abs(m0 - m1) > 1e-9 or len(place[0]) != 12:
            fails.append(f"1. mean think place team 0 {m0:.2f}, team 1 {m1:.2f}")
    if not hasattr(live_bots, "roster_pick"):
        fails.append("2. no roster_pick: styles / tiers dealt over all bots by join order")
    else:
        styles, tiers = "rusher,flanker,camper,objector,spammer,grudger,sniper".split(","), ["top", "strong"]
        got, seen = {0: [], 1: []}, {}
        for i in range(1, 13):
            team = 0 if i <= 6 else 1
            got[team].append(live_bots.roster_pick(styles, tiers, seen, team))
        if sorted(got[0]) != sorted(got[1]):
            fails.append(f"2. rosters differ: team 0 {got[0]}, team 1 {got[1]}")
    if fails:
        sys.exit("team_fair FAIL: " + "; ".join(fails))
    print("team_fair OK")


if __name__ == "__main__":
    main()
