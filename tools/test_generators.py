"""Generator Defense (guide 11 sections 4 and 6; brain/director.py ff_gen_slots, brain/bot.py generator_work):
1. Spartans: a guard on each generator (beside it, in reach of its lockdown switch), the rest rotator / anchor
2. a guard at its generator presses Use when it takes damage, never for a Grunt alone, never inside 10 s of the
   team's last lock (one lock started per 10 s), never on a locked or dead generator
3. Elites: breakers on the unlocked generator worth the most; all locked: they hunt
4. a breaker with no man near shoots an unlocked generator with a clear line from Medium band in; never a locked one,
   never past GEN_SHOOT, never with a Spartan player 6 u off (it fights him)

usage: python -I tools/test_generators.py      -> "generators OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Action, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.bot import Bot, Order, LOCK_CLAIM  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain import firefight as FF  # noqa: E402

M = get_map("reach_ff50_park")
GEN_POS = [Vec(-190.62, 43.0, -37.24), Vec(-183.86, 71.29, -35.46), Vec(-168.86, 42.55, -37.9)]


def gens(over=None):
    out = []
    for k, p in enumerate(GEN_POS):
        g = dict(i=k, pos=p, health=1.0, alive=True, ready=True, locked=False, state="ready", since=0.0, hit=False)
        g.update((over or {}).get(k, {}))
        out.append(g)
    return out


def snap(players, gl, t=50.0, lock_t=-99.0, left=12):
    sn = Snapshot(t, players, mode="firefight")
    sn.ff = dict(versus=True, lives=4, side={0: FF.SPARTAN, 1: FF.ELITE}, left=left, heat=0.3, zone="cool", gens=gl,
                 lock_t=lock_t)
    return sn


def main():
    fails = []
    sp = [PlayerState(i, 0, f"s{i}", GEN_POS[0] + Vec(i, 0, 0), side=FF.SPARTAN) for i in (1, 2, 3, 4)]
    el = [PlayerState(i, 1, f"e{i}", GEN_POS[1] + Vec(20, i, 0), side=FF.ELITE) for i in (5, 6, 7, 8)]
    # 1. Spartan roles
    d = Director(0, M, {}, random.Random(1))
    slots = d.role_slots(10.0, snap(sp + el, gens()), 4)
    guards = [p for r, p, _ in slots if r == "defender" and min(dist(p, g) for g in GEN_POS) < 2.5]
    if len(guards) < 3 or len({min(range(3), key=lambda k: dist(p, GEN_POS[k])) for p in guards}) < 3:
        fails.append(f"Spartans: {[(r, p) for r, p, _ in slots]} (want a guard beside each of the 3 generators)")
    # 1b. posts kept: a guard's death moves nobody onto its generator, and the living keep theirs (live Nov 8: re-dealt
    # by the living count each pass, posts swapped every 10-20 s)
    team = {i: Bot(i, 0, make_profile("top", "camper", random.Random(i)), M, random.Random(i)) for i in (1, 2, 3)}
    dg = Director(0, M, team, random.Random(1))
    at = {i: PlayerState(i, 0, f"s{i}", GEN_POS[i - 1] + Vec(1, 0, 0), side=FF.SPARTAN) for i in (1, 2, 3)}
    dg.assign_roles(10.0, snap(list(at.values()) + el, gens()))
    post = {i: min(range(3), key=lambda k: dist(team[i].order.point, GEN_POS[k])) for i in team}
    at[1] = PlayerState(1, 0, "s1", Vec(), alive=False, side=FF.SPARTAN)
    team[1].on_death(5)
    at[2] = PlayerState(2, 0, "s2", GEN_POS[0] + Vec(1, 0, 0), side=FF.SPARTAN)   # (bot 2 nearest bot 1's generator)
    dg.assign_roles(12.0, snap(list(at.values()) + el, gens()))
    now_post = {i: min(range(3), key=lambda k: dist(team[i].order.point, GEN_POS[k])) for i in team}
    if len(set(post.values())) < 3 or now_post != post:
        fails.append(f"guard posts: {post} then {now_post} after bot 1 died (want each guard kept on its generator)")
    # 2. a guard's lockdown
    b = Bot(1, 0, make_profile("top", "camper", random.Random(1)), M, random.Random(1))
    b.order = Order("defender", GEN_POS[0] + Vec(1.5, 0, 0))
    me = PlayerState(1, 0, "s1", GEN_POS[0] + Vec(1.5, 0, 0), side=FF.SPARTAN)

    def press(gl, others=(), t=50.0, lock_t=-99.0, left=12, guard=me):
        act = Action()
        b.lock_hold = None                              # (each case on its own: no hold left from the last)
        LOCK_CLAIM.clear()
        b.generator_work(t, guard, act, snap([guard] + list(others), gl, t, lock_t, left), "objective")
        if act.action and not act.device:
            fails.append("guard: a lockdown Use without the device bit (botcore would not work the switch)")
        return act.action
    grunt = PlayerState(1001, 1, "ai", GEN_POS[0] + Vec(-1.0, 0, 0), rank="grunt")
    grunt2 = PlayerState(1002, 1, "ai", GEN_POS[0] + Vec(-1.2, 0.5, 0), rank="grunt")
    hit = gens({0: dict(hit=True, health=0.8)})
    if not press(hit):
        fails.append("guard: its generator taking damage, no lock pressed")
    if not press(gens(), [grunt, grunt2]):
        fails.append("guard: a squad on its generator and it alone, no lock pressed")
    if press(gens(), [grunt]):
        fails.append("guard: locked for one Grunt (it can kill him)")
    if press(hit, t=50.0, lock_t=45.0):
        fails.append("guard: a second lock 5 s after the team's last (one per 10 s)")
    if press(gens({0: dict(hit=True, ready=False, locked=True, state="locked")})):
        fails.append("guard: pressed at a generator already locked")
    if press(gens({0: dict(hit=True, ready=False, state="cool")})):
        fails.append("guard: pressed while its generator cools down (no relock yet)")
    if press(gens({0: dict(hit=True, alive=False)})):
        fails.append("guard: pressed at a dead generator")
    if press(gens(), [grunt, grunt2], left=3):
        fails.append("guard: locked with the wave down to 3")
    far = PlayerState(1, 0, "s1", GEN_POS[0] + Vec(5, 0, 0), side=FF.SPARTAN)
    if press(hit, guard=far):
        fails.append("guard: pressed from 5 u off (out of the switch's reach)")
    walk = Action()
    b.lock_hold = None
    LOCK_CLAIM.clear()
    b.generator_work(50.0, far, walk, snap([far], hit), "objective")
    if walk.forward < 0.9 or walk.action:
        fails.append("guard: a lock due 5 u off, and it did not walk in to the switch")
    # 2a. two guards, both generators hit in the same half second: one lock started, not two (the game shows a lock
    # 0.5 s on: live Nov 8, locks 0.5 s apart)
    b2 = Bot(2, 0, make_profile("top", "camper", random.Random(2)), M, random.Random(2))
    b2.order = Order("defender", GEN_POS[1] + Vec(1.5, 0, 0))
    me2 = PlayerState(2, 0, "s2", GEN_POS[1] + Vec(1.5, 0, 0), side=FF.SPARTAN)
    both = gens({0: dict(hit=True, health=0.8), 1: dict(hit=True, health=0.8)})
    b.lock_hold = b2.lock_hold = None
    LOCK_CLAIM.clear()
    a1, a2 = Action(), Action()
    b.generator_work(50.0, me, a1, snap([me, me2], both, 50.0), "objective")
    b2.generator_work(50.3, me2, a2, snap([me, me2], both, 50.3), "objective")
    if not a1.action or a2.action:
        fails.append(f"guards: two locks started 0.3 s apart ({a1.action}, {a2.action}; want one per 10 s team-wide)")
    # 2b. a guard off its post (after a respawn): straight back, a fight 12 u off loses; a man 3 u off it fights
    from brain.bot import Belief
    post = GEN_POS[0] + Vec(1.5, 0, 0)
    for label, foe_at, want_back in (("a fight 12 u off", Vec(0, 12, 0), True), ("a man in its way 3 u off", Vec(3, 0, 0), False)):
        gb = Bot(2, 0, make_profile("top", "rusher", random.Random(2)), M, random.Random(2))
        gb.order, gb.notes = Order("defender", post, said="gen"), []
        me2 = PlayerState(2, 0, "s2", post + Vec(-20, 0, 0), side=FF.SPARTAN)
        foe = PlayerState(7, 1, "e7", me2.pos + foe_at, side=FF.ELITE)
        gb.per.beliefs[7] = Belief(foe.pos, Vec(), 50.0, True, "eyes")
        gb.per.attacker_id, gb.per.attacker_t = 7, 49.5      # (he is shooting it: still not a reason to chase him)
        sc = {("fight", 7): 2.8, ("objective", post): 0.9}
        gb.keep_role(sc, me2, snap([me2, foe], gens()), {7})
        back = max(sc, key=sc.get)[0] == "objective"
        if back != want_back:
            fails.append(f"guard off its post, {label}: chose {max(sc, key=sc.get)} (want {'the way back' if want_back else 'the fight'})")
    # 2c. a dead guard respawns at the Firefight zone nearest its generator, never one with an enemy 8 u off
    sys.path.insert(0, HERE)
    import live_bots
    from brain.maps import terrain as _terrain
    zones = [(-174.26, 48.05, -34.4), (-180.69, 65.12, -34.56), (-201.22, 17.23, -36.8)]
    gd = Bot(2, 0, make_profile("top", "rusher", random.Random(2)), M, random.Random(2))
    gd.order = Order("defender", GEN_POS[1] + Vec(1.5, 0, 0), said="gen")
    other = Bot(3, 0, make_profile("top", "rusher", random.Random(3)), M, random.Random(3))
    other.order = Order("escort", GEN_POS[1])
    dead = [PlayerState(2, 0, "s2", Vec(), alive=False, side=FF.SPARTAN), PlayerState(3, 0, "s3", Vec(), alive=False,
                                                                                  side=FF.SPARTAN)]
    gd.on_death(9)                                      # (a death keeps the guard's job: on_death dropped it, live)
    if gd.order.said != "gen":
        fails.append("a guard's death dropped its generator job (no respawn pick, no leash after)")
    sent = []
    live_bots.guard_spawn_check(lambda i, *a: sent.append((i, a)), {2: gd, 3: other}, snap(dead, gens()), zones, {},
                                random.Random(1), _terrain(M), 50.0)
    if [i for i, _ in sent] != [2] or dist(Vec(*sent[0][1][:3]), Vec(*zones[1])) > 2.1:
        fails.append(f"guard respawn: sent {sent} (want bot 2 alone, at the zone by generator 1 {zones[1]})")
    camper = PlayerState(9, 1, "e9", Vec(*zones[1]) + Vec(3, 0, 0), side=FF.ELITE)
    sent = []
    live_bots.guard_spawn_check(lambda i, *a: sent.append((i, a)), {2: gd}, snap(dead[:1] + [camper], gens()), zones, {},
                                random.Random(1), _terrain(M), 50.0)
    if not sent or dist(Vec(*sent[0][1][:3]), Vec(*zones[1])) < 5:
        fails.append(f"guard respawn: sent into the zone with an Elite 3 u off ({sent})")
    # 2c2. a zone its guard did not get from to its post in 12 s alive is marked slow and the next pick goes elsewhere
    live_bots.GUARD_SLOW.clear()
    gst, sent = {}, []
    chk = lambda pl, t: live_bots.guard_spawn_check(lambda i, *a: sent.append((i, a)), {2: gd}, snap(pl, gens()), zones,
                                                    gst, random.Random(1), _terrain(M), t)
    chk(dead[:1], 50.0)
    stuck = PlayerState(2, 0, "s2", Vec(*zones[1]) + Vec(10, 0, 0), side=FF.SPARTAN)   # (alive, 10 u off its post)
    chk([stuck], 60.0)
    chk([stuck], 73.0)
    chk(dead[:1], 80.0)
    if len(sent) != 2 or not live_bots.GUARD_SLOW or dist(Vec(*sent[1][1][:3]), Vec(*zones[1])) < 5:
        fails.append(f"guard respawn: the zone it stuck from picked again ({sent}, slow {live_bots.GUARD_SLOW})")
    live_bots.GUARD_SLOW.clear()
    # 2d. a second lock later in the match: lock_t on the match clock, as snap.time (live Nov 8: a wall clock there,
    # after the first lock the 10 s gap never passed, one lock a match)
    class FakeLive:
        sw, health = {"gen": 1.0}, 1.0

        def ff_generators(self):
            return [dict(handle=1, pos=(GEN_POS[0].x, GEN_POS[0].y, GEN_POS[0].z), health=self.health, sw=dict(self.sw))]
    fl = FakeLive()
    live_bots.GENS.update(t=0.0, list=[], hist={}, state={}, lock_t=-99.0, dead=set())
    for t, sw, h in ((20.0, {"gen": 1.0}, 1.0), (24.0, {}, 1.0), (54.0, {"cool": 1.0}, 1.0),
                     (60.0, {"gen": 1.0}, 1.0), (139.0, {"gen": 1.0}, 0.9), (140.0, {"gen": 1.0}, 0.8)):
        fl.sw, fl.health = sw, h
        st = live_bots.ff_state(fl, sp + el, t)
    if not press(st["gens"] + gens()[1:], t=140.0, lock_t=st["lock_t"]):
        fails.append(f"guard: no second lock at 140 s, the first at 24 s (lock_t {st['lock_t']}: not the match clock)")
    # 3. Elite roles
    d = Director(1, M, {}, random.Random(2))
    slots = d.role_slots(10.0, snap(sp + el, gens({1: dict(health=0.4)})), 4)
    if not any(r == "hunter" and dist(p, GEN_POS[1]) < 0.1 for r, p, _ in slots):
        fails.append(f"Elites: {[(r, p) for r, p, _ in slots]} (want breakers on the weakest unlocked generator)")
    shut = gens({k: dict(ready=False, locked=True, state="locked") for k in range(3)})
    slots = d.role_slots(11.0, snap(sp + el, shut), 4)
    if any(r == "hunter" and min(dist(p, g) for g in GEN_POS) < 0.1 for r, p, _ in slots):
        fails.append("Elites: sent at a locked generator")
    # 4. a breaker's shots
    e = Bot(5, 1, make_profile("top", "rusher", random.Random(5)), M, random.Random(5))
    e.order = Order("hunter", GEN_POS[1])
    spot = GEN_POS[1] + Vec(8.0, 0, 0.3)
    T = e._terrain if getattr(e, "_terrain", None) else None
    from brain.maps import terrain
    T = terrain(M)
    cands = [GEN_POS[1] + Vec(dx, dy, 0) for dx in (-9, -7, 7, 9) for dy in (-6, 0, 6)]
    clear = [q for q in cands if T.ground_ok(q.x, q.y, q.z) and T.los(q, GEN_POS[1] + Vec(0, 0, 0.6))]
    if not clear:
        fails.append("breaker: no clear spot near generator 1 to test from")
    else:
        spot = clear[0]
        elite = PlayerState(5, 1, "e5", spot, side=FF.ELITE)

        def shoots(gl, others=(), where=spot):
            a = Action()
            me5 = PlayerState(5, 1, "e5", where, side=FF.ELITE)
            for t in (50.0, 50.1, 50.4, 50.6):
                e.generator_work(t, me5, a, snap([me5] + list(others), gl, t), "objective")
                if a.fire:
                    return True
            return False
        if not shoots(gens()):
            fails.append(f"breaker at {spot}: no shot at the unlocked generator {dist(spot, GEN_POS[1]):.1f} u off")
        if shoots(gens({1: dict(ready=False, locked=True, state="locked")})):
            fails.append("breaker: shot a locked generator")
        if not shoots(gens({1: dict(ready=False, state="cool")})):
            fails.append("breaker: no shot while the generator cools down after a lock (open to damage)")
        if shoots(gens(), [PlayerState(1, 0, "s1", spot + Vec(3, 0, 0), side=FF.SPARTAN)]):
            fails.append("breaker: shot the generator with a Spartan 3 u off")
        if shoots(gens(), where=GEN_POS[1] + Vec(40, 0, 0)):
            fails.append("breaker: shot from past GEN_SHOOT")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("generators OK (a guard on each generator; locks on damage or a squad, not for a Grunt, one per 10 s, never "
          "locked or dead ones; breakers on the weakest unlocked one, never a locked one; shots in band, clear line, "
          "no man near)")


if __name__ == "__main__":
    main()
