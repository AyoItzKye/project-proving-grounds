"""The coordinator's second wave on the player's combat asks (docs/oct31/combat.md section 5), each part failing on
the code before (3bd1b48):
1. alone against two, hurt now and not ahead on health: Normal and up pull back (cover, else a teammate within 15 u);
   with a teammate within 8 u, or Easy: no
2. an edge stop in a fight takes a safe way instead (the strafe the other way, ...), not a freeze (Ascension)
3. power weapon runs in every mode (a power gun lying loose in Slayer gets a fetcher); a spawn due back within 10 s is
   fetched by Heroic and up only (its timer is map knowledge)
4. on foot, a rocket at a tank from behind goes at its rear (the hatch), not its middle
5. against a sword or hammer, Normal and up back off inside his reach + 1.5 u (shooting); Easy does not
6. after a kill in SWAT (no shields), Normal and up move off the spot to cover
7. a hand dead on a man crossing fast counts as on target (the pursuit's trail), the aim itself unchanged

usage: python -I test_combat_oct31b.py      -> "combat oct31b OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain.bot import Aim, Belief, Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from test_combat_oct31 import A, DT, M, fight, mk, mean  # noqa: E402


def seen(b, k, pos, t):
    b.per.beliefs[k] = Belief(pos, Vec(), t, True, "eyes")
    b.per.recognized.add(k)
    b.per.last_seen[k] = t


def main():
    fails, info = [], []
    # 1. alone against two
    for tier, mate, want in (("strong", None, True), ("average", None, True), ("strong", 5.0, False), ("novice", None, False)):
        b = mk(tier, pers="flanker")
        b.cover_from = lambda me, th: A + Vec(-3.0, 0.0, 0.0)
        e1, e2 = A + Vec(9.0, 2.0, 0.0), A + Vec(9.0, -3.0, 0.0)
        seen(b, 2, e1, 10.0)
        seen(b, 3, e2, 10.0)
        b.hit_at = 9.8
        me = PlayerState(b.id, 0, "bot", A, alive=True, shield=0.4, weapon="battle_rifle", weapons=["battle_rifle"])
        ps = [me, PlayerState(2, 1, "a", e1, alive=True), PlayerState(3, 1, "b", e2, alive=True)]
        if mate:
            ps.append(PlayerState(4, 0, "m", A + Vec(0.0, mate, 0.0), alive=True))
        g = b.decide(10.0, me, Snapshot(10.0, ps))
        got = g[0] == "retreat"
        if got != want:
            fails.append(f"{tier} alone against two{' (mate ' + str(mate) + ' u)' if mate else ''}: {g[0]} (want "
                         f"{'retreat' if want else 'no retreat'})")
    # 2. an edge in a fight: the other way
    b = mk("top")
    b.goal = ("fight", 2)

    class Edge:          # the void east of A
        @staticmethod
        def ground_ok(x, y, z, drop=0.6):
            return x <= A.x + 0.2
    act = Action(yaw=0.0, pitch=0.0)
    act.forward, act.strafe = 1.0, 1.0
    me = PlayerState(b.id, 0, "bot", A, alive=True)
    try:
        ok = b.edge_other_way(Edge, me, act, (0.6, 1.1))
    except AttributeError:
        ok = False
    if not ok or act.forward > 0.05:
        fails.append(f"edge in a fight: other way {ok}, stick ({act.forward}, {act.strafe}) (want a safe way, not east)")
    # 3. power runs: Slayer, a rocket launcher lying loose; a timed spawn for Heroic only
    m = get_map("bloodgulch")
    rk = next(it for it in m["items"] if it["name"] == "rockets")
    for tier, lying, want in (("average", True, True), ("average", False, False), ("strong", False, True)):
        b = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), m, random.Random(1))
        d = Director(0, m, {1: b}, rng=random.Random(0))
        i = m["items"].index(rk)
        d.item_up[i] = 105.0                       # back in 5 s by the team's timer
        me = PlayerState(1, 0, "bot", rk["pos"] + Vec(10.0, 0.0, 0.0), alive=True, weapon="pistol", weapons=["pistol"])
        snap = Snapshot(100.0, [me], mode="slayer")
        snap.ground_weapons = [("rockets", rk["pos"])] if lying else [("pistol", rk["pos"] + Vec(30, 0, 0))]
        d.next_roles = 0.0
        try:
            d.update(100.0, snap)
        except Exception as ex:               # (the rest of the director's update needs a full match; power_runs ran)
            info.append(f"update: {type(ex).__name__}")
        got = getattr(b, "fetch", None) is not None
        if got != want:
            fails.append(f"{tier} Slayer, rockets {'lying' if lying else 'due in 5 s'} 10 u off: fetch {got} (want {want})")
    # 4. a rocket at a tank's rear from behind
    b = mk("top")
    tank = dict(handle=9, kind="scorpion", pos=(A.x + 10.0, A.y, A.z), occupied=True, fwd=(1.0, 0.0, 0.0))
    man = PlayerState(2, 1, "d", Vec(A.x + 10.0, A.y, A.z), alive=True, vehicle=9)
    me = PlayerState(b.id, 0, "bot", A, alive=True, weapon="rockets")
    p = b.weak_point(me, 2, Belief(man.pos, Vec(), 0.0, True, "eyes"), Snapshot(0.0, [me, man], vehicles=[tank]), "rockets")
    if not p.x < man.pos.x - 0.5:
        fails.append(f"rocket at a tank from behind: aims at x {p.x:.2f} (want its rear, under {man.pos.x - 0.5:.2f})")
    # 5. back off a sword
    for tier, want in (("average", True), ("top", True), ("novice", False)):
        bb = mk(tier, i=40)
        man = Vec(A.x + 2.5, A.y, A.z)
        bb.per.beliefs[2] = Belief(man, Vec(), 0.0, True, "eyes")
        bb.per.recognized.add(2)
        fw, t = [], 0.0
        while t < 1.0:
            bb.per.last_seen[2] = t
            me = PlayerState(bb.id, 0, "bot", A, alive=True, weapon="battle_rifle", weapons=["battle_rifle"], yaw=0.0)
            a = bb.think(t, DT, Snapshot(t, [me, PlayerState(2, 1, "s", man, alive=True, weapon="sword", yaw=math.pi)]),
                         lambda p, q: True, lambda p, q, **k: q, [])
            if bb.goal == ("fight", 2):
                fw.append(a.forward)
            t += DT
        f = mean(fw)
        info.append(f"{tier} v a sword at 2.5 u: forward {f:.2f}")
        if (f < -0.3) != want:
            fails.append(f"{tier} against a sword at 2.5 u: forward {f:.2f} (want {'back off' if want else 'no back-off'})")
    # 6. off the spot after a SWAT kill
    b = mk("top")
    b.cover_from = lambda me, th: A + Vec(-3.0, 1.0, 0.0)
    b.goal, b.last_shot_t = ("fight", 2), 9.7
    me = PlayerState(b.id, 0, "bot", A, alive=True, shield=0.0, weapon="battle_rifle", weapons=["battle_rifle"])
    dead = PlayerState(2, 1, "x", A + Vec(12.0, 0.0, 0.0), alive=False, shield=0.0)
    snap = Snapshot(10.0, [me, dead])
    snap.shieldless = True
    g = b.decide(10.0, me, snap)
    if g[0] != "retreat":
        fails.append(f"after a SWAT kill: {g} (want off the spot, a retreat to cover)")
    # 7. the trigger window with a crossing man
    aim = Aim(make_profile("strong", "rusher", random.Random(2)), random.Random(2))
    aim.goal, aim.goal_rate = (0.015, 0.0), 0.27       # the plan's point 0.015 rad ahead, swinging 0.27 rad/s
    me = PlayerState(1, 0, "bot", A, alive=True, yaw=0.0)
    if not aim.on_target(me, A + Vec(8.0, 0.0, 0.0), 0.0, 0.0):
        fails.append("hand 0.015 rad behind a man crossing at 0.27 rad/s, 8 u: not on target")
    aim.goal_rate = 0.0
    if aim.on_target(me, A + Vec(8.0, 0.0, 0.0), 0.0, 0.0):
        fails.append("0.015 rad off a still man at 8 u counted as on target (the window grew for still men)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("combat oct31b OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
