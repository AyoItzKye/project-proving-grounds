"""CTF effort, split attacks and flag defense (the player, Guardian: "the teams weren't making good efforts to
get each others objectives", "a chance to split squads up and attack different routes", "defend the general area, not
stand ontop of their flag with no cover"). On h3_guardian, 6 bots, both flags home:
1. tied: a pull goes (runners); two ahead: the runs go on, one more defender (LEAD_KEEPS_SPLIT, the player Nov 12)
2. defenders' posts: none on the stand (3 u off or more), every one sees it, 3 u apart
3. a split cycle: two runners on different lanes, each escort with its own runner, the pushers on the lanes

usage: python -I test_ctf_effort.py      -> "ctf effort OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.match import Posture  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

MAP = get_map("h3_guardian")
RED, BLUE = MAP["flags"][0], MAP["flags"][1]


def setup(lead=0, split=False):
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), MAP, random.Random(i)) for i in range(1, 7)}
    d = Director(0, MAP, bots, rng=random.Random(0))
    d.posture = Posture(0.5, "even" if lead == 0 else "ahead", lead=lead)
    d.split, d.split_until = split, 1e9
    ps = [PlayerState(i, 0, f"b{i}", RED + Vec(i * 0.7, 1.0, 0)) for i in bots]
    ps += [PlayerState(10 + k, 1, f"e{k}", BLUE + Vec(k * 0.7, 0, 0)) for k in range(6)]
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, BLUE, "home")}
    snap = Snapshot(10.0, ps, flags, mode="ctf")
    d.assign_roles(10.0, snap)
    return d, bots


def main():
    testdata.need_lidar("h3_guardian")
    fails = []
    d, _ = setup(lead=0)
    if "runner" not in d.roles.values():
        fails.append(f"tied: no runner {d.roles}")
    tied = sum(r == "defender" for r in d.roles.values())
    d, _ = setup(lead=2)
    # two ahead the runs go on with one more defender (director LEAD_KEEPS_SPLIT, the player Nov 12: "more than half
    # the team isnt attacking"; before, two ahead stopped pulling)
    if "runner" not in d.roles.values():
        fails.append(f"two ahead: no runner (the runs go on when ahead) {d.roles}")
    if sum(r == "defender" for r in d.roles.values()) != tied + 1:
        fails.append(f"two ahead: not one more defender than tied ({tied}) {d.roles}")
    d, bots = setup()
    T, eye = terrain(MAP), Vec(0, 0, 0.6)
    posts = [b.order.point for b in bots.values() if b.order.role == "defender"]
    if not posts or any(dist(q, RED) < 3.0 or not T.los(q + eye, RED + eye) for q in posts) or any(
            dist(a, b) < 3.0 for i, a in enumerate(posts) for b in posts[i + 1:]):
        fails.append(f"defender posts {posts} (stand {RED})")
    d, bots = setup(split=True)
    runners = [b for b in bots.values() if b.order.role == "runner"]
    escorts = [b for b in bots.values() if b.order.role == "escort"]
    lanes = MAP.get("lanes", [])
    if len(runners) != 2 or runners[0].order.via == runners[1].order.via:
        fails.append(f"split: runners {[(b.id, b.order.via) for b in runners]}")
    laned = next((b for b in runners if b.order.via), None)
    if laned is None:
        fails.append("split: no runner on a lane")
    else:
        laned.on_death(None)                 # a new life draws its lane again (the director's next pick_route)
        if laned.order.via or laned.via_left or laned.order.role != "runner":
            fails.append(f"a dead runner kept its lane {laned.order.via} / {laned.via_left}")
    if len(escorts) == 2 and escorts[0].order.target == escorts[1].order.target:
        fails.append(f"split: both escorts with runner {escorts[0].order.target}")
    mids = [b.order.point for b in bots.values() if b.order.role == "mid"]
    if lanes and any(all(dist(q, l) > 0.01 for l in lanes) for q in mids):
        fails.append(f"split: pushers off the lanes {mids}")
    # 4. Boardwalk: they carry ours, theirs is home. The player's rule (his flagged games, Nov 11; director.OWNER_SPLITS):
    #    two flags, about half on the carrier and the rest attack theirs, nobody on the empty stand. Off (research 12
    #    3.5, the play before): everyone but one defender on the carrier
    import brain.director as Dmod
    for splits in (True, False):
        Dmod.OWNER_SPLITS = splits
        try:
            d, bots = setup()
            ps = [PlayerState(i, 0, f"b{i}", RED + Vec(i * 0.7, 1.0, 0)) for i in bots] + [
                PlayerState(10, 1, "e0", Vec(2, -10, 17), has_flag=True)]
            flags = {0: FlagState(0, RED, Vec(2, -10, 17), "carried", 10), 1: FlagState(1, BLUE, BLUE, "home")}
            d.next_roles = 0.0
            d.assign_roles(20.0, Snapshot(20.0, ps, flags, mode="ctf"))
            got = sorted(d.roles.values())
        finally:
            Dmod.OWNER_SPLITS = True
        if splits and (got.count("hunter") != 3 or "runner" not in got or "defender" in got):
            fails.append(f"our flag carried, theirs home: roles {got} (want 3 of 6 hunting, a runner, no defender)")
        if not splits and (got.count("hunter") != len(bots) - 1 or "runner" in got):
            fails.append(f"our flag carried, theirs home, splits off: roles {got} (want all but one hunting)")
    # 5. a person of ours carries theirs: no bot runs "home" for him, the escorts go with him
    d, bots = setup()
    ps = [PlayerState(i, 0, f"b{i}", RED + Vec(i * 0.7, 1.0, 0)) for i in bots] + [
        PlayerState(0, 0, "you", Vec(5, -5, 17), has_flag=True, is_bot=False)]
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, Vec(5, -5, 17), "carried", 0)}
    d.assign_roles(30.0, Snapshot(30.0, ps, flags, mode="ctf"))
    esc = [b for b in bots.values() if b.order.role == "escort"]
    if "runner" in d.roles.values() or not esc or any(b.order.target != 0 for b in esc):
        fails.append(f"a person carries: roles {d.roles}, escorts' lead {[b.order.target for b in esc]} (want him, 0)")
    # 6. the tick a bot has the flag in hand (its gun read shows it before the flag read does): no Use, no switch
    from brain.bot import Order
    for wpn, want in (("assault_rifle", True), ("unknown", False)):
        b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), MAP, random.Random(1))
        b.order = Order("runner", BLUE)
        ps = [PlayerState(1, 0, "b1", BLUE + Vec(0.3, 0, 0), weapon=wpn)]
        flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, BLUE, "home")}
        act = b.think(5.0, 0.033, Snapshot(5.0, ps, flags, mode="ctf"), lambda a, c: True, lambda a, c, **k: c, [])
        if bool(act.action) != want or (not want and act.weapon != -1):
            fails.append(f"on their flag holding {wpn}: action {act.action}, weapon {act.weapon} (want Use {want})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("ctf effort OK")


if __name__ == "__main__":
    main()
