"""The fluidity fixes: checks that fail if they break.

1. range: an AR bot holds fire at a man 20 units off (past reach x OUT_OF_REACH), fires at 8; shot at from 20 units it
   answers with a short deterrent burst, not a stream
2. detour: Legendary sometimes goes round by a zone off the straight line on a long trip, Easy never
3. edge stop: held at an edge 0.6 s the bot drops its step and decides again
4. fluidity score: a habit at the person's value scores 1, twice it 0 ("match"); a "max" habit is free up to its floor

usage: python -I test_fluidity_fixes.py      -> "fluidity fixes OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain.bot import Belief, Bot, Order, reach, OUT_OF_REACH  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
import fluidity  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
on_ground = lambda x, y: Vec(x, y, T.nav_z(x, y))
A = on_ground(70.0, -120.0)


def fire_share(bot, foe_pos, seconds=4.0, shot_at=False):
    t, yaw, pitch, sh, fires, ticks = 0.0, math.pi, 0.0, 1.0, 0, 0
    while t < seconds:
        if shot_at:
            sh = 1.0 if sh < 0.2 else sh - 0.01          # the man keeps hitting us
        me = PlayerState(bot.id, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=sh, weapon="assault_rifle",
                         weapons=["assault_rifle"])
        foe = PlayerState(2, 1, "human", foe_pos, alive=True)
        a = bot.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        if t > 1.5:
            ticks += 1
            fires += bool(a.fire)
        t += 1 / 30
    return fires / max(ticks, 1)


def main():
    fails = []
    # 1. range discipline
    far, near = A + Vec(-20.0, 0, 0), A + Vec(-8.0, 0, 0)
    assert 20.0 > reach("assault_rifle") * OUT_OF_REACH > 8.0
    mk = lambda: Bot(1, 0, make_profile("top", "rusher", random.Random(3)), MAP, random.Random(3))
    for b in (mk(),):
        b.can_pickup = False
        f_far = fire_share(b, far)
    b = mk()
    b.can_pickup = False
    f_near = fire_share(b, near)
    b = mk()
    b.can_pickup = False
    f_deter = fire_share(b, far, seconds=8.0, shot_at=True)
    if f_far > 0.0:
        fails.append(f"AR at 20 units, nobody shooting: fired {f_far:.0%} of ticks (want 0: out of reach)")
    if f_near < 0.05:
        fails.append(f"AR at 8 units: fired {f_near:.0%} of ticks (want bursts)")
    if not 0.0 < f_deter < 0.25:
        fails.append(f"AR at 20 units, shot at: fired {f_deter:.0%} of ticks (want short deterrent bursts)")
    # 2. detours: a long trip, many goals; Legendary sometimes off the line, Easy never
    for tier, want in (("top", True), ("novice", False)):
        b = Bot(1, 0, make_profile(tier, "flanker", random.Random(5)), MAP, random.Random(5))
        me = PlayerState(1, 0, "bot", A)
        took = 0
        for k in range(40):
            goal = Vec(A.x - 40.0 - k * 0.5, A.y + 30.0, A.z)
            took += b.detour(0.0, me, "objective", goal) is not goal
        if bool(took) != want:
            fails.append(f"{tier}: {took} of 40 long trips went round by a zone (want {'some' if want else 'none'})")
    # 3. edge stop: replan after 0.6 s held at an edge
    b = mk()
    b.loiter_pt, b.next_decide = A + Vec(3, 0, 0), 99.0
    edge_T = type("T", (), {"ground_ok": lambda s, x, y, z, drop=4.0: abs(x - A.x) < 0.2 and abs(y - A.y) < 0.2,
                            "learn_stuck": lambda s, *a, **k: None})()
    b._terrain = edge_T
    from brain.core import Action
    for k in range(25):
        t = k / 30
        act = Action(yaw=0.0, pitch=0.0, forward=1.0)
        me = PlayerState(1, 0, "bot", A, yaw=0.0, alive=True)
        b.planned_jump = False
        b.edge_guard(t, me, act)
    if b.next_decide > 1.0 or b.loiter_pt is not None:
        fails.append(f"held at an edge 0.8 s: next decision {b.next_decide}, loiter step {b.loiter_pt} (want a replan)")
    # 5. a Halo 3 rider's position is relative to what it rides: the world position is the parent's plus the turned
    #    offset (the player on a Cyberdyne turret read as (-0.39, 0, -0.02): no bot ever shot at him)
    import struct
    from brain.live import LiveH3, NONE
    h3 = object.__new__(LiveH3)
    turret = bytearray(0x74)
    struct.pack_into("<3f", turret, 0x50, 10.0, 5.0, 2.0)       # the turret stands here
    struct.pack_into("<3f", turret, 0x5C, 0.0, 1.0, 0.0)        # facing +y
    struct.pack_into("<3f", turret, 0x68, 0.0, 0.0, 1.0)
    struct.pack_into("<I", turret, 0x10, NONE)
    h3.object = lambda h: 0x1000 if h == 7 else None
    h3.g = type("G", (), {"read": lambda s, a, n: bytes(turret[:n])})()
    got = h3.world_pos((-0.39, 0.0, -0.02), 7)
    want = (10.0, 5.0 - 0.39, 2.0 - 0.02)
    if max(abs(a - b) for a, b in zip(got, want)) > 1e-4:
        fails.append(f"rider on a turret at (10, 5, 2) facing +y read at {got} (want {want})")
    if h3.world_pos((1.0, 2.0, 3.0), NONE) != (1.0, 2.0, 3.0):
        fails.append("a unit on foot moved by world_pos")
    # 6. turning on a new shooter mid-fight waits for the bot to notice him (live Spire: half the Legendary bots
    #    turned in 0.0-0.11 s to the player's 0.40); once noticed it still turns at once (they never turned)
    b6 = mk()
    me6 = PlayerState(1, 0, "bot", A, alive=True, shield=0.6, health=1.0)
    cur = PlayerState(8, 1, "cur", A + Vec(10, 0, 0), yaw=0.0, alive=True)            # looking away from us
    shooter = PlayerState(7, 1, "shooter", A + Vec(0, 9, 0), yaw=-math.pi / 2, alive=True)
    sn6 = Snapshot(50.0, [me6, cur, shooter])
    b6.per.last_hp = 2.0
    b6.per.hurt_by(50.0, me6, sn6)
    early = b6.shot_by_other(50.02, me6, sn6, 7, 8, [7, 8])
    b6.per.attacker_t = 50.6
    later = b6.shot_by_other(50.6, me6, sn6, 7, 8, [7, 8])
    if early or not later or b6.per.attacker_id != 7:
        fails.append(f"new shooter mid-fight: turn at once {early} (want False), after 0.6 s {later} (want True)")
    # 6b. a shooter aiming half a radian off us (leading, a burst's spread) is still the one we look for (live Boneyard
    #     missed attributions left a third of the first hits unanswered); one aiming well away is not
    b6b = mk()
    lead = PlayerState(7, 1, "lead", A + Vec(0, 9, 0), yaw=-math.pi / 2 + 0.5, alive=True)
    away = PlayerState(9, 1, "away", A + Vec(9, 0, 0), yaw=0.0, alive=True)
    b6b.per.last_hp = 2.0
    got = b6b.per.hurt_by(60.0, me6, Snapshot(60.0, [me6, lead, away]))
    if got is None or got.id != 7 or b6b.per.beliefs.get(7) is None:
        fails.append(f"a shooter 0.5 rad off: attributed to {getattr(got, 'id', None)} (want 7, with a belief)")
    # 6c. hit with nobody aiming our way (a grenade, splash: 25 of 31 unanswered first hits, live Spire): the
    #     nearest enemy who can see us is the one to look for, not the nearer one behind a wall; none past 30 u
    b6c = mk()
    seer = PlayerState(7, 1, "seer", A + Vec(12, 0, 0), yaw=0.0, alive=True)          # facing away from us
    walled = PlayerState(9, 1, "walled", A + Vec(0, 6, 0), yaw=math.pi / 2, alive=True)
    b6c.per.last_hp = 2.0
    got = b6c.per.hurt_by(70.0, me6, Snapshot(70.0, [me6, seer, walled]), los=lambda a, b: (a - A).flat() > 10.0)
    far = PlayerState(7, 1, "far", A + Vec(40, 0, 0), yaw=0.0, alive=True)
    b6d = mk()
    b6d.per.last_hp = 2.0
    none = b6d.per.hurt_by(71.0, me6, Snapshot(71.0, [me6, far]), los=lambda a, b: True)
    if got is None or got.id != 7 or none is not None:
        fails.append(f"no aimer: attributed to {getattr(got, 'id', None)} (want the seeing 7), past 30 u to "
                     f"{getattr(none, 'id', None)} (want nobody)")
    # 6f. shot by a man seen (recognised) 2 s ago and out of sight since: his shot's spot is turned to, not the spot
    #     he was last seen at (only the unrecognised became "hit" beliefs: 4-16% of first hits got no turn at all,
    #     Legendary 16%, three Reach matches)
    b6f = mk()
    old_spot = A + Vec(-12, 0, 0)
    known = PlayerState(7, 1, "known", A + Vec(0, 9, 0), yaw=-math.pi / 2, alive=True)    # aiming at us from (0, 9)
    b6f.per.recognized.add(7)
    b6f.per.beliefs[7] = Belief(old_spot, Vec(), 78.0, True, "eyes")
    b6f.per.last_hp = 2.0
    b6f.per.hurt_by(80.0, me6, Snapshot(80.0, [me6, known]))
    b = b6f.per.beliefs.get(7)
    if b is None or b.source != "hit" or (b.pos - known.pos).flat() > 0.5:
        fails.append(f"shot by a man seen 2 s ago: belief {getattr(b, 'source', None)} at "
                     f"{None if b is None else (round(b.pos.x, 1), round(b.pos.y, 1))} (want a hit at his spot)")
    # 6g. and when the radar has re-marked his belief since, with a newer dot of another man on it, the look stays on
    #     the man hurting us for 1.5 s (Powerhouse: a Heroic watched its shooter 0.3 s, then two radar dots)
    b6f.per.beliefs[7] = Belief(known.pos, Vec(), 80.3, False, "radar")
    b6f.per.beliefs[10] = Belief(A + Vec(15, -5, 0), Vec(), 80.5, False, "radar")
    b6f.now = 80.5
    look = b6f.look_point(me6, A + Vec(-20, 0, 0))
    if (look - known.pos).flat() > 0.5:
        fails.append(f"0.5 s after a hit, his belief radar-marked and another dot newer: looking at "
                     f"({look.x:.1f}, {look.y:.1f}), {b6f.att} (want the shooter at ({known.pos.x:.1f}, {known.pos.y:.1f}))")
    # 6h. a shot heard is glanced at, not stared at: Legendary watched one as long as its memory held (5 s) and looked
    #     60 deg or more off its way 14% of its walking time to the player's 9.4% (live). 1 s: watched; 2.5 s: not
    b6h = Bot(1, 0, make_profile("top", "rusher", random.Random(6)), MAP, random.Random(6))
    b6h.per.beliefs[9] = Belief(A + Vec(0, 20, 0), Vec(), 90.0, False, "heard")
    seen_at = {}
    for t in (91.0, 92.5):
        b6h.now = t
        b6h.look_point(me6, A + Vec(-20, 0, 0))
        seen_at[t] = "heard" in str(b6h.att)
    if not seen_at[91.0] or seen_at[92.5]:
        fails.append(f"Legendary and a shot heard: watching it 1 s on {seen_at[91.0]} (want True), 2.5 s on "
                     f"{seen_at[92.5]} (want False)")
    # 6e. an Invasion attacker in its territory shot by a man the radar already showed: the turn to him is not cut by
    #     the post's leash (the radar took the belief's "hit" mark within 0.7 s; 9 of 23 unanswered hits, Spire)
    b6e = mk()
    post = A + Vec(1, 0, 0)
    b6e.order = Order("defender", post)
    shooter_at = A + Vec(0, 14, 0)
    b6e.per.beliefs[7] = Belief(shooter_at, Vec(), 80.0, False, "radar")
    b6e.per.attacker_id, b6e.per.attacker_t = 7, 80.0
    me6e = PlayerState(1, 0, "bot", A, alive=True)
    sn6e = Snapshot(80.2, [me6e], mode="invasion", inv_phase=1, inv_attackers=0, inv_zones=[post], inv_zone_r=[2.0])
    sc = {("objective", post): 1.6, ("hunt", shooter_at): 3.2}
    b6e.keep_role(sc, me6e, sn6e, [])
    if max(sc, key=sc.get)[0] != "hunt":
        fails.append(f"shot in its territory by a radar-known man: {sc} (want the hunt to win)")
    # 6f. shot from a ledge the level data makes solid (live Boneyard: 22 of 26 unanswered first hits came
    #     from men 6-8 u away and 5-6 u up whom the line-of-sight model hid even from their own aim on the bot; the bots
    #     turned their heads, never saw or fought them). A man aiming straight at us whose shot just hurt us has a line
    #     to us: seen, and the aim on him within 1.5 s. One not aiming at us, behind the same wall, stays unseen
    from brain.core import angles_to, eye, wrap
    for tier in ("average", "top"):
        b6f = Bot(1, 0, make_profile(tier, "rusher", random.Random(9)), MAP, random.Random(9))
        b6f.can_pickup = False
        ledge = A + Vec(-5.0, 4.5, 5.6)
        aimer_yaw, aimer_pitch = angles_to(eye(PlayerState(7, 1, "x", ledge)), A + Vec(0, 0, 0.35))
        yaw, pitch, hp, on_t = 0.0, 0.0, 2.0, None
        for k in range(45):
            t = 90.0 + k / 30
            if k % 9 == 0:
                hp -= 0.12                              # a burst lands every 0.3 s
            me = PlayerState(1, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=max(0.0, hp - 1.0),
                             health=min(1.0, hp), weapon="assault_rifle", weapons=["assault_rifle"])
            shooter = PlayerState(7, 1, "ledge", ledge, yaw=aimer_yaw, pitch=aimer_pitch, alive=True)
            a6f = b6f.think(t, 1 / 30, Snapshot(t, [me, shooter]), lambda p, q: False, lambda p, q, **kw: q, [])
            yaw, pitch = a6f.yaw, a6f.pitch
            wy, wp = angles_to(eye(me), ledge + Vec(0, 0, 0.35))
            if on_t is None and abs(wrap(yaw - wy)) < 0.12 and abs(pitch - wp) < 0.12 and 7 in b6f.per.visible_enemies():
                on_t = t - 90.0
        if on_t is None:
            fails.append(f"{tier}: shot from a ledge 6 u up the model hides: never saw him / aim on him in 1.5 s")
    b6g = mk()
    me6g = PlayerState(1, 0, "bot", A, alive=True, shield=0.5, health=1.0)
    wall = PlayerState(9, 1, "wall", A + Vec(-5.0, 4.5, 5.6), yaw=0.0, pitch=0.0, alive=True)   # looking elsewhere
    b6g.per.last_hp = 2.0
    b6g.per.update(95.0, me6g, Snapshot(95.0, [me6g, wall]), lambda p, q: False, [])
    if 9 in b6g.per.recognized or b6g.per.pending.get(9) is not None:
        fails.append("hit while a man behind a wall looks elsewhere: he was seen through it")
    # 7. walking out of a fight, a deliberate look (a man watched, a post's sightline, a flank check) stays within 50
    #    degrees of the way it goes (live Spire: 43k walking ticks slowed to 0.3 for looking 60+ degrees off;
    #    speed varying 0.36 to the player's 0.23); a look already inside the cone is left alone
    try:
        p0 = Vec(10.0, 0.0, 0.0)
        me7 = PlayerState(1, 0, "bot", p0)
        side = Bot.walk_cone(me7, p0 + Vec(0.0, 8.0, 1.0), 0.0)            # 90 degrees left of walking east
        a7 = math.degrees(math.atan2(side.y - p0.y, side.x - p0.x))
        keep = Bot.walk_cone(me7, p0 + Vec(8.0, 3.0, 0.0), 0.0)
        if not 49.0 < a7 < 51.0 or abs((side - p0).flat() - 8.0) > 1e-6 or side.z != 1.0 or keep != p0 + Vec(8.0, 3.0, 0.0):
            fails.append(f"walk cone: a look 90 degrees off became {a7:.0f} degrees ({side}); inside kept as {keep}")
    except AttributeError as e:
        fails.append(f"walk cone: {e}")
    # 8. a Legendary bot dodging a man who aims at it strafes with short stops, not without a break (live Spire:
    #    fight strafe 0.90 u/s to the player's 0.70)
    b8 = mk()
    foe8 = A + Vec(-9.0, 0.0, 0.0)
    t, yaw, stops, ticks, sizes = 0.0, math.pi, 0, 0, set()
    while t < 8.0:
        me = PlayerState(b8.id, 0, "bot", A, yaw=yaw, alive=True, weapon="dmr", weapons=["dmr"])
        foe = PlayerState(2, 1, "human", foe8, yaw=0.0, alive=True)          # facing the bot: aiming at it
        a8 = b8.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        yaw = a8.yaw
        if t > 1.5 and b8.goal[0] == "fight":
            ticks += 1
            stops += a8.strafe == 0.0
            if not any("unstuck" in n for n in b8.notes):      # (held in place: the wiggle steers anyhow)
                sizes.add(round(abs(a8.strafe), 2))
        t += 1 / 30
    if ticks < 60 or not 0.04 < stops / ticks < 0.4:
        fails.append(f"dodging strafe: {stops} of {ticks} fight ticks with no strafe (want a few stops, 4-40%)")
    # 8b. in Reach the stick goes 0.5-0.95 of the way a step (live Spire: full stick on 74% of the aim-on fight
    #     ticks, strafe 0.87-0.92 u/s to the player's 0.70); the other games full (Halo 2 SWAT's Legendary is right)
    RM = get_map("reach_35_island")
    b8b = Bot(1, 0, make_profile("top", "rusher", random.Random(3)), RM, random.Random(3))
    b8b.can_pickup = False
    # (at River, on open floor: the spire top's spot put the man over the top's hole, floor 36 u down, and the bot,
    # held still here, only faced him by a route the false learned spots there priced; they were pruned, cells the
    # player stood on: maps.terrain people_walked)
    RA, rsizes, t, yaw = Vec(-112.7, -327.0, -63.2), set(), 0.0, math.pi
    while t < 8.0:
        me = PlayerState(1, 0, "bot", RA, yaw=yaw, alive=True, weapon="dmr", weapons=["dmr"])
        foe = PlayerState(2, 1, "human", RA + Vec(-9.0, 0.0, 0.0), yaw=0.0, alive=True)
        a8 = b8b.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        yaw = a8.yaw
        if t > 1.5 and b8b.goal[0] == "fight" and a8.strafe and not any("unstuck" in n for n in b8b.notes):
            rsizes.add(round(abs(a8.strafe), 2))
        t += 1 / 30
    if sizes - {0.0} != {1.0} or not rsizes or not all(0.5 <= x <= 0.95 for x in rsizes) or len(rsizes) < 3:
        fails.append(f"strafe stick: Blood Gulch {sorted(sizes)}, Reach {sorted(rsizes)} (want full; 0.5-0.95 a step)")
    # 8c. a novice with a man 1.5 u off and 1.2 u under it: in melee reach by floor distance; its tick must not fail (the
    #     close-fight clock went by 3D distance and was unset, tools/test_modes.py)
    nb = Bot(1, 0, make_profile("novice", "rusher", random.Random(5)), MAP, random.Random(5))
    nb.can_pickup = False
    try:
        t = 0.0
        while t < 2.0:
            me = PlayerState(1, 0, "bot", A, yaw=math.pi, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
            foe = PlayerState(2, 1, "human", A + Vec(-1.5, 0.0, -1.2), alive=True)
            nb.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
            t += 1 / 30
    except TypeError as e:
        fails.append(f"novice in melee reach of a man below: tick failed ({e})")
    # 8d. an Easy Invasion attacker holding a small zone (Boneyard's boxes, 0.9 u from the middle to the edge) is not a
    #     statue: live Boneyard, Easy stood still 46% of the time to the player's 13%, nearly all of it holding a
    #     territory (the loiter's 0.5 u spots ended inside the walk's own arrival distance). Moving most of 4 s, and in it
    zb = Bot(1, 0, make_profile("novice", "objector", random.Random(8)), MAP, random.Random(8))
    zb.can_pickup = False
    zone = A + Vec(2.0, 0.0, 0.0)
    zb.order = Order("defender", zone)
    pos, yaw, moving, ticks, worst = Vec(zone.x, zone.y, A.z), 0.0, 0, 0, 0.0
    for k in range(150):
        t = 300.0 + k / 30
        me = PlayerState(1, 0, "bot", pos, yaw=yaw, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
        a = zb.think(t, 1 / 30, Snapshot(t, [me], mode="invasion", inv_phase=1, inv_attackers=0, inv_zones=[zone],
                                         inv_zone_r=[0.9]), lambda p, q: True, lambda p, q, **kw: q, [])
        step = Vec(math.cos(a.yaw) * a.forward - math.sin(a.yaw) * a.strafe,
                   math.sin(a.yaw) * a.forward + math.cos(a.yaw) * a.strafe, 0.0) * (2.5 / 30)
        pos, yaw = pos + step, a.yaw
        if k >= 30:
            ticks += 1
            moving += step.flat() * 30 > 0.3
            worst = max(worst, (pos - zone).flat())
    if moving < 0.6 * ticks or worst > 1.2:
        fails.append(f"Easy holding a 0.9 u zone: moving {moving} of {ticks} ticks, furthest {worst:.2f} u from its "
                     f"middle (want moving most of the time, inside 1.2 u)")
    # 8e. the same as Easy really plays it: a runner (director.assign_roles sends Easy straight at the objective), on a
    #     2 u territory. Live Spire: Easy's runners stood on the middle with no input 44% of their objective time
    #     (a runner never loitered: that is for a flag or the core). Moving most of 4 s, inside the zone
    zr = Bot(1, 0, make_profile("novice", "objector", random.Random(9)), MAP, random.Random(9))
    zr.can_pickup = False
    zr.order = Order("runner", zone)
    pos, yaw, moving, ticks, worst = Vec(zone.x, zone.y, A.z), 0.0, 0, 0, 0.0
    for k in range(150):
        t = 300.0 + k / 30
        me = PlayerState(1, 0, "bot", pos, yaw=yaw, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
        a = zr.think(t, 1 / 30, Snapshot(t, [me], mode="invasion", inv_phase=1, inv_attackers=0, inv_zones=[zone],
                                         inv_zone_r=[2.0]), lambda p, q: True, lambda p, q, **kw: q, [])
        step = Vec(math.cos(a.yaw) * a.forward - math.sin(a.yaw) * a.strafe,
                   math.sin(a.yaw) * a.forward + math.cos(a.yaw) * a.strafe, 0.0) * (2.5 / 30)
        pos, yaw = pos + step, a.yaw
        if k >= 30:
            ticks += 1
            moving += step.flat() * 30 > 0.3
            worst = max(worst, (pos - zone).flat())
    if moving < 0.5 * ticks or worst > 2.5:
        fails.append(f"Easy runner on a 2 u territory: moving {moving} of {ticks} ticks, furthest {worst:.2f} u from its "
                     f"middle (want moving at least half the time, inside 2.5 u)")
    # 8g. a Headhunter runner on its 2 u drop point works it as one on a territory (zone_at left Headhunter out: its
    #     runners stood on the drop point with no input 41-65% of their standing time, Boardwalk)
    hh = Bot(1, 0, make_profile("average", "objector", random.Random(9)), MAP, random.Random(9))
    hh.can_pickup = False
    hh.order = Order("runner", zone)
    pos, yaw, moving, ticks = Vec(zone.x, zone.y, A.z), 0.0, 0, 0
    for k in range(150):
        t = 300.0 + k / 30
        me = PlayerState(1, 0, "bot", pos, yaw=yaw, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
        a = hh.think(t, 1 / 30, Snapshot(t, [me], mode="headhunter", obj_zones=[(zone, 2.0, None)]),
                     lambda p, q: True, lambda p, q, **kw: q, [])
        step = Vec(math.cos(a.yaw) * a.forward - math.sin(a.yaw) * a.strafe,
                   math.sin(a.yaw) * a.forward + math.cos(a.yaw) * a.strafe, 0.0) * (2.5 / 30)
        pos, yaw = pos + step, a.yaw
        if k >= 30:
            ticks += 1
            moving += step.flat() * 30 > 0.3
    if moving < 0.5 * ticks:
        fails.append(f"Headhunter runner on a 2 u drop point: moving {moving} of {ticks} ticks (want at least half)")
    # 8f. a Normal holding a post in an objective game (2.5 u to work): standing still under 22% of 20 s, the player 13%
    #     (its loiter stops were 0.8-2.6 s: 27-43% here, and the Oddball side holding the ball stood 27-59% of its time
    #     at its posts)
    hp = Bot(1, 0, make_profile("average", "rusher", random.Random(0)), MAP, random.Random(0))
    hp.can_pickup = False
    hp.goal, hp.next_decide = ("hold", A), 1e9
    pos, yaw, still, ticks = A, 0.0, 0, 0
    for k in range(630):
        t = 300.0 + k / 30
        me = PlayerState(1, 0, "bot", pos, yaw=yaw, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
        a = hp.think(t, 1 / 30, Snapshot(t, [me], mode="ctf"), lambda p, q: True, lambda p, q, **kw: q, [])
        step = Vec(math.cos(a.yaw) * a.forward - math.sin(a.yaw) * a.strafe,
                   math.sin(a.yaw) * a.forward + math.cos(a.yaw) * a.strafe, 0.0) * (2.5 / 30)
        pos, yaw = on_ground(pos.x + step.x, pos.y + step.y), a.yaw
        if k >= 30:
            ticks += 1
            still += step.flat() * 30 < 0.3
    if still > 0.22 * ticks:
        fails.append(f"Normal at a post: still {still} of {ticks} ticks (want under 22%)")
    # 4. the fluidity score
    assert fluidity.score("reaction", 0.45, 0.45) == 1.0
    assert fluidity.score("reaction", 0.9, 0.45) == 0.0 and fluidity.score("reaction", 0.225, 0.45) == 0.0
    assert fluidity.score("range", 0.04, 0.0) == 1.0 and fluidity.score("range", 0.5, 0.05) == 0.0
    # 5. jumps: a take-off over two samples (+1.5 then +2.6 u/s, as every game's at 30 a second) counts once, a ramp
    # climbed at 1.2 u/s never (the old rule counted no Halo 4 take-off: tools/player_stats.py movement)
    import json, tempfile
    import player_stats
    climb = [0.0] * 30 + [1.5, 2.6, 2.4, 2.1, 1.8, 1.5, 1.2, 0.6, 0.0, -0.6, -1.2, -1.8, -2.4, -2.6, -2.6] + [0.0] * 30 \
        + [1.2] * 30 + [0.0] * 30 + [2.7, 2.4, 2.1, 1.5, 0.9, 0.0, -0.9, -1.5, -2.1, -2.7] + [0.0] * 30
    z, rows = 0.0, []
    for k, vz in enumerate(climb):
        z += vz / 30
        rows.append({"t": k / 30, "p": [[0, 0, 1, k * 0.07, 0.0, z, 0.0, 0.0, 1.0, 1.0, 0, 0, 0]]})
    path = os.path.join(tempfile.mkdtemp(), "collect_test_jumps.jsonl")
    with open(path, "w") as f:
        f.write(json.dumps({"t": 0.0, "collect": "start", "map": "bloodgulch", "game": "h4"}) + "\n")
        f.writelines(json.dumps(r) + "\n" for r in rows)
    m = player_stats.Match(path, los=lambda a, b: True, zones=lambda p: "a")
    got = round(m.movement(0)["jumps_min"] * m.alive[0][1:].sum() / 30 / 60)
    if got != 2:
        fails.append(f"jumps: {got} counted in a run with two take-offs (one over two samples) and a ramp, want 2")
    # 9. the looser trigger below Legendary (brain/profiles.py LOOSE): a man 29 degrees off fired at sooner with it on
    # (the end of the swing onto him). Its follow-through, Normal still firing 0.3-0.5 s after the man went behind a
    # wall at 2.0 s, ended the same evening with the player's rule ("bots shouldnt be shooting at other bots unless
    # there is clear line of site": Bot.line_clear): no tier fires once the line is gone
    import brain.profiles as P

    def fire_times(tier, loose, foe_pos, hide_at=None, seconds=3.0):
        P.LOOSE_AIM = loose
        bot = Bot(1, 0, make_profile(tier, "rusher", random.Random(7)), MAP, rng=random.Random(7))
        t, yaw, pitch, out = 0.0, math.pi, 0.0, []
        while t < seconds:
            me = PlayerState(1, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=1.0, weapon="assault_rifle",
                             weapons=["assault_rifle"])
            foe = PlayerState(2, 1, "human", foe_pos, alive=True)
            vis = hide_at is None or t < hide_at
            a = bot.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: vis, lambda p, q, **k: q, [])
            yaw, pitch = a.yaw, a.pitch
            if a.fire:
                out.append(t)
            t += 1 / 30
        P.LOOSE_AIM = True
        return out
    ahead, aside = A + Vec(-8.0, 0.0, 0.0), A + Vec(8.0 * math.cos(math.pi + 0.5), 8.0 * math.sin(math.pi + 0.5), 0.0)
    late = {(tier, lo): sum(2.3 < t < 2.5 for t in fire_times(tier, lo, ahead, hide_at=2.0))
            for tier in ("average", "top") for lo in (True, False)}
    if any(late.values()):
        fails.append(f"loose trigger: shots 0.3-0.5 s after the man went behind a wall (Normal on, Normal off, "
                     f"Legendary on, off) {[late[k] for k in (('average', True), ('average', False), ('top', True), ('top', False))]}"
                     ", want 0, 0, 0, 0 (no shot without a clear line)")
    first = {lo: (fire_times("average", lo, aside) or [9.0])[0] for lo in (True, False)}
    if not first[True] < first[False] < 9.0:
        fails.append(f"loose trigger: first shot at a man 29 degrees off {first[True]:.2f} s on, {first[False]:.2f} s off "
                     "(want sooner on)")
    # 10. walking to a vehicle with a radar dot 80 degrees off the way: a Heroic keeps it within the walking look cone
    #     (it watched freely: Normal to Legendary walked to vehicles 13-22% of their walking time 60+ degrees off their
    #     way, Spire King and High Ground); never at speed with the view 60+ degrees off its way
    vb = Bot(1, 0, make_profile("strong", "rusher", random.Random(5)), MAP, rng=random.Random(5))
    vb.goal, vb.next_decide = ("vehicle", 5), 1e9
    car = A + Vec(-18.0, 0.0, 0.0)
    hog = dict(handle=5, kind="warthog", pos=(car.x, car.y, T.nav_z(car.x, car.y)), riders=0, occupied=False, team=-1,
               fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0))
    pos, yaw, fast_off, n = A, 0.0, 0, 0
    for k in range(120):
        t = 300.0 + k / 30
        me = PlayerState(1, 0, "bot", pos, yaw=yaw, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
        way = math.atan2(car.y - pos.y, car.x - pos.x)
        dot = pos + Vec(15 * math.cos(way + 1.4), 15 * math.sin(way + 1.4), 0)
        vb.per.beliefs[9] = Belief(dot, Vec(), t, False, "radar")
        a = vb.think(t, 1 / 30, Snapshot(t, [me, PlayerState(9, 1, "camper", dot)], vehicles=[hog]),
                     lambda p, q: (p - q).flat() < 5.0, lambda p, q, **kw: q, [])
        size, rel = math.hypot(a.forward, a.strafe), abs(math.atan2(a.strafe, a.forward))
        if k >= 30 and size > 0.5:
            n += 1
            fast_off += rel > math.radians(60)
        step = Vec(math.cos(a.yaw) * a.forward - math.sin(a.yaw) * a.strafe,
                   math.sin(a.yaw) * a.forward + math.cos(a.yaw) * a.strafe, 0.0) * (2.5 / 30)
        pos, yaw = on_ground(pos.x + step.x, pos.y + step.y), a.yaw
    if n < 30 or fast_off:
        fails.append(f"walking to a vehicle with a radar dot to the side: {fast_off} of {n} walking ticks at speed with "
                     "the view 60+ degrees off the way (want 0)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"fluidity fixes OK (AR fire share: 20 u {f_far:.0%}, 8 u {f_near:.0%}, 20 u shot at {f_deter:.0%})")


if __name__ == "__main__":
    main()
