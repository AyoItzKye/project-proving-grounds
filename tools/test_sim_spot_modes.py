"""King of the Hill, Oddball and VIP in the offline sim (brain/sim_modes.py: the director's King and Oddball plans had
no offline game, so tools/mode_matrix.py could not measure them):

1. hills(): CE's rings of "hill - flag" markers and Halo 2's "King Hill N" one hill each (Blood Gulch 10, Ascension 5),
   Reach's koth_hill one per flag with its boundary's radius (Settlement 8, one 1.0 u box), Halo 3's koth_hill_static
   (Construct 4, 3 u); a map with no hill data: its mid and power positions. ball_spawn(): the ball spot nearest mid.
2. King rules with players put by hand: a team alone in the hill scores 1 a second, both teams in it nobody (contested);
   "king" keeps its hill, "crazy_king" moves it every HILL_MOVE_S; the snapshot says "king" with the hill and radius.
3. Oddball: walking over the ball takes it (has_flag), its team scores 1 a second, the carrier's death drops it where he
   fell, BALL_RESET_S loose sends it home.
4. VIP: each team has one in snap.vips; killing the other team's scores 1 and the dead team gets a new VIP; another kill
   scores nothing.
5. Played by the brain (4 v 4 Legendary, 120 s): King on Construct and Oddball on Settlement both score, the ball is
   taken, the hill is taken.

usage: python -I test_sim_spot_modes.py      -> "sim spot modes OK (...)"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import sim_modes as SM  # noqa: E402
from brain.core import TICK, Vec, dist  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.sim import Sim  # noqa: E402


def put(sim, pid, pos):
    p = sim.players[pid]
    p.pos, p.alive = Vec(pos.x, pos.y, pos.z), True


def far(sim, pids):
    """Players out of the way: at the farthest spawn point from the objective."""
    for pid in pids:
        sim.players[pid].alive = False


def main():
    fails = []
    # 1
    n = {k: len(SM.hills(get_map(k))) for k in ("bloodgulch", "h2_ascension", "reach_30_settlement", "h3_construct")}
    if n != {"bloodgulch": 10, "h2_ascension": 5, "reach_30_settlement": 8, "h3_construct": 4}:
        fails.append(f"1 hill counts {n}")
    st = SM.hills(get_map("reach_30_settlement"))
    if sorted({round(r, 1) for _, r in st}) != [1.0, 1.4, 1.5, 3.0]:
        fails.append(f"1 Settlement radii {sorted({round(r, 1) for _, r in st})}")
    fake = dict(get_map("bloodgulch"))
    fake["objects"] = {"netgame_flags": []}
    if [p for p, _ in SM.hills(fake)][:1] != [fake["points"]["mid"]] or SM.ball_spawn(fake) != fake["points"]["mid"]:
        fails.append("1 a map without data does not fall back to its mid")
    b = SM.ball_spawn(get_map("reach_30_settlement"))
    if dist(b, Vec(125.552, 242.884, 36.8)) > 0.01:
        fails.append(f"1 Settlement's ball spawn {b}")

    # 2 King, by hand
    sim = Sim("king", per_team=2, seed=1, map_name="h3_construct", tiers=["top"])
    om = sim.objmodes
    hill, r = om.hills[om.hill_k]
    sim.now = 0.0

    def tick(k):
        for _ in range(k):
            sim.now += TICK
            om.step()
    far(sim, (1, 2, 3))
    put(sim, 0, hill)
    tick(int(5.0 / TICK) + 1)
    if sim.score != {0: 5, 1: 0}:
        fails.append(f"2 alone 5 s: score {sim.score}")
    put(sim, 2, hill + Vec(0.5, 0, 0))
    tick(int(5.0 / TICK))
    if sim.score != {0: 5, 1: 0} or om.contested < 4.9:
        fails.append(f"2 contested 5 s: score {sim.score}, contested {om.contested:.1f}")
    snap = sim.snapshot()
    if snap.mode != "king" or snap.hill != hill or snap.hill_r != r:
        fails.append(f"2 snapshot {snap.mode} {snap.hill} {snap.hill_r}")
    sim.now = 61.0
    om.step()
    if om.hills[om.hill_k][0] != hill:
        fails.append("2 the static hill moved")
    sim = Sim("crazy_king", per_team=2, seed=1, map_name="h3_construct", tiers=["top"])
    om, k0 = sim.objmodes, sim.objmodes.hill_k
    sim.now = 59.9
    om.step()
    k59 = om.hill_k
    sim.now = 60.0
    om.step()
    if k59 != k0 or om.hill_k == k0 or sim.snapshot().mode != "king":
        fails.append(f"2 crazy king: hill {k0} -> {k59} at 59.9 s -> {om.hill_k} at 60 s")

    # 3 Oddball, by hand
    sim = Sim("oddball", per_team=2, seed=1, map_name="reach_30_settlement", tiers=["top"])
    om = sim.objmodes
    sim.now = 0.0
    far(sim, (1, 2, 3))
    put(sim, 0, om.ball["home"])
    tick(1)
    if om.ball["carrier"] != 0 or not sim.players[0].has_flag:
        fails.append("3 the ball was not taken")
    put(sim, 0, om.ball["home"] + Vec(10, 0, 0))
    tick(int(3.0 / TICK) + 1)
    if sim.score != {0: 3, 1: 0} or dist(sim.snapshot().ball, sim.players[0].pos) > 0.01 or sim.snapshot().ball_carrier != 0:
        fails.append(f"3 carried 3 s: score {sim.score}, snapshot ball {sim.snapshot().ball}")
    sim.kill(sim.players[0], sim.players[2])
    if om.ball["carrier"] is not None or sim.players[0].has_flag or dist(om.ball["pos"], sim.players[0].pos) > 0.01:
        fails.append("3 the carrier's death did not drop the ball where he fell")
    tick(int((SM.BALL_RESET_S - 1) / TICK))
    loose = om.ball["pos"]
    tick(int(1.5 / TICK))
    if dist(loose, om.ball["home"]) < 1 or om.ball["pos"] != om.ball["home"]:
        fails.append("3 a loose ball did not go home after BALL_RESET_S")

    # 4 VIP
    sim = Sim("vip", per_team=3, seed=1, map_name="h3_construct", tiers=["top"])
    om = sim.objmodes
    tick(1)
    vips = sim.snapshot().vips
    v1 = om.vips[1]
    other = next(p for p in sim.players if p.team == 1 and p.id != v1)
    sim.kill(other, sim.players[0])
    s_other = dict(sim.score)
    sim.kill(sim.players[v1], sim.players[0])
    if len(vips) != 2 or s_other != {0: 0, 1: 0} or sim.score != {0: 1, 1: 0} or om.vips[1] in (v1, None):
        fails.append(f"4 VIP: vips {vips}, score after a kill {s_other}, after the VIP {sim.score}, new {om.vips[1]}")

    # 5 the brain plays them
    played = {}
    for mode, m in (("king", "h3_construct"), ("oddball", "reach_30_settlement")):
        sim = Sim(mode, per_team=4, seed=3, map_name=m, tiers=["top"])
        sim.run(120)
        played[mode] = (dict(sim.score), sim.objmodes.takes)
        if sum(sim.score.values()) < 10 or sim.objmodes.takes < 1:
            fails.append(f"5 {mode} on {m}: score {sim.score}, takes {sim.objmodes.takes}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"sim spot modes OK (hills {n}; King / Oddball rules by hand; VIP; played 120 s: {played})")


if __name__ == "__main__":
    main()
