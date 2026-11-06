"""Offline checks for equipment, armor abilities and their counters (brain/equipment.py, wired into
brain/bot.py). Each check is a guide 08 rule.

usage: python -I test_equipment.py      -> "equipment OK"
"""
import inspect
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import Energy, Kit  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
ground = lambda x, y: Vec(x, y, T.nav_z(x, y))
A = ground(70.0, -120.0)                       # open gulch
DT = 1 / 30


def bot(tier, game, kind="", pers="rusher", i=1):
    b = Bot(i, 0, make_profile(tier, pers, random.Random(i)), MAP, random.Random(i))
    b.kit = Kit(b.p, game)
    b.kind = kind
    b.can_pickup = False          # (no run for a power item before it has noticed the man in front)
    return b


def me_state(b, pos, yaw, pitch, **kw):
    return PlayerState(b.id, 0, "bot", pos, yaw=yaw, pitch=pitch, alive=True, equipment=b.kind, **kw)


def run(b, t0, t1, foes, pos=A, los=T.los, nav=None, deployed=(), me_kw=None, each=None, yaw0=math.pi):
    """Think from t0 to t1 with these enemies (list of PlayerState, or a function of t); returns the acts."""
    acts, t, yaw, pitch = [], t0, yaw0, 0.0
    while t < t1:
        fs = foes(t) if callable(foes) else foes
        kw = me_kw(t) if callable(me_kw) else (me_kw or {})
        me = me_state(b, pos, yaw, pitch, **kw)
        snap = Snapshot(t, [me] + list(fs), deployed=[dict(d) for d in deployed])
        a = b.think(t, DT, snap, los, nav or (lambda p, q, **k: q), [])
        if each:
            each(t, b, a)
        yaw, pitch = a.yaw, a.pitch
        acts.append((t, a, list(b.notes)))
        t += DT
    return acts


def foe(pos, i=2, **kw):
    return PlayerState(i, 1, "human", pos, alive=True, **kw)


def plan_now(b, foes, seen=(), goal=None, hit=False, me_kw=None, now=1.0, **snap_kw):
    """Kit.plan at one moment, at A facing east: the foes listed in seen in view (recognized), the rest remembered
    (teammates in foes are only there)."""
    for e in foes:
        if e.team == 0:
            continue
        b.per.beliefs[e.id] = Belief(e.pos, e.vel, now, e.id in seen, "eyes")
        if e.id in seen:
            b.per.recognized.add(e.id)
    b.goal = goal or b.goal
    b.hit_at = now if hit else -9.0
    me = me_state(b, A, 0.0, 0.0, **(me_kw or {}))
    snap = Snapshot(now, [me] + list(foes), **snap_kw)
    b.kit.perceive(b, now, me, snap)
    return b.kit.plan(b, now, me, snap) or (None,) * 5     # (kind, how, point, hold, why)


def pressed(acts, t_from=0.0):
    return [a for t, a, _ in acts if t >= t_from and a.equipment]


def notes(acts):
    return [n for _, _, ns in acts for n in ns]


def main():
    fails = []
    west = A + Vec(-10.0, 0.0, 0.0)
    rocket = foe(west, weapon="rockets", yaw=0.0)            # 10 units west, aiming east at us

    # 1. armor lock against a rocket aimed at us (use-now): strong locks and holds still with no fire;
    #    a novice not yet shot does not (obvious cues only), but locks the moment it is shot, at full
    #    shield in the open (guide 02's abuse)
    b = bot("strong", "reach", "armor_lock")
    acts = run(b, 0.0, 2.0, [rocket])
    held = pressed(acts, 0.4)
    if len(held) < 20:
        fails.append(f"strong did not armor lock against an aimed rocket ({len(held)} ticks)")
    elif any(a.fire or abs(a.forward) > 0.01 for a in held):
        fails.append("armor-locked bot moved or fired")
    b = bot("novice", "reach", "armor_lock")
    if pressed(run(b, 0.0, 2.0, [rocket])):
        fails.append("a novice armor-locked with nothing but an aimed rocket (obvious cues only)")
    b = bot("novice", "reach", "armor_lock")
    hurt = lambda t: dict(shield=1.0 - 0.3 * (t > 1.0))
    if pressed(run(b, 0.0, 2.0, [foe(west, weapon="dmr", yaw=0.0)], me_kw=hurt), 1.0):
        fails.append("a novice locked when shot (Easy uses no equipment, owner Oct 24)")

    # 1d. the rocket gone (he turned away): a lock lets go, unless a teammate runs in to back him up (Panopticon 234435
    #     at 82.9 s)
    def gone(t, mate=False):
        f = [rocket if t < 0.7 else foe(west, weapon="dmr", yaw=math.pi)]
        if mate:
            f.append(PlayerState(5, 0, "mate", A + Vec(15.0 - 4.0 * t, 0.0, 0.0), Vec(-4.0, 0.0, 0.0), alive=True))
        return f
    alone = len(pressed(run(bot("strong", "reach", "armor_lock"), 0.0, 2.5, gone), 1.4))
    backed = len(pressed(run(bot("strong", "reach", "armor_lock"), 0.0, 2.5, lambda t: gone(t, True)), 1.4))
    if alone > 3 or backed < 15:
        fails.append(f"armor lock after the rocket: held {alone} ticks past 1.4 s alone (want let go), {backed} with a "
                     f"teammate running in (want held)")

    # 2. the energy model from the tag: armor lock drains in about 5 s, then has to recharge
    e = Energy("reach", "armor_lock")
    t = 0.0
    while t < 6.0 and e.tick(t, DT, True):
        t += DT
    if not 4.3 < t < 5.3 or e.ready():
        fails.append(f"armor lock energy: ran out at {t:.1f} s (want about 5), ready {e.ready()}")
    while t < 14.0:
        e.tick(t, DT, False)
        t += DT
    if not e.ready():
        fails.append("armor lock not ready again 8 s after running out")

    # 3. shield down, being shot, no cover near: a Halo 3 bubble at our feet
    b = bot("strong", "h3", "bubble_shield")
    b.cover_from = lambda me, threats: None
    cracked = lambda t: dict(shield=0.1 if t < 1.0 else 0.05)
    shooter = foe(A + Vec(-6.0, 0.0, 0.0), weapon="battle_rifle", yaw=0.0)
    acts = run(b, 0.0, 1.5, [shooter], me_kw=cracked, each=lambda t, bb, a: setattr(bb, "hit_at", t))
    if not any(a.equipment and a.pitch < -1.0 for _, a, _ in acts):
        fails.append("no bubble shield at the feet when cracked, shot and without cover")

    # ... not with cover a step away: the bubble is for no cover within 10 ft, one unit (guide 08)
    b = bot("strong", "h3", "bubble_shield")
    b.cover_from = lambda me, threats: A + Vec(0.0, 0.8, 0.0)
    acts = run(b, 0.0, 1.5, [shooter], me_kw=cracked, each=lambda t, bb, a: setattr(bb, "hit_at", t))
    if any(a.equipment for _, a, _ in acts):
        fails.append("bubble used with cover 8 ft away")

    # jetpack: up the ledge the route climbs, unseen; a strong bot does not fly where it is watched,
    # a novice never flies (Easy uses no equipment)
    for tier, foes, want in (("strong", [], True), ("strong", [foe(west, yaw=0.0)], False),
                             ("novice", [foe(west, yaw=0.0)], False)):
        b = bot(tier, "reach", "jetpack")
        b.wp = A + Vec(1.5, 0.0, 1.6)
        b.move_to = lambda me, point, act, nav, bb=b: setattr(bb, "wp", A + Vec(1.5, 0.0, 1.6))
        b.goal, b.next_decide = ("objective", A + Vec(20, 0, 3)), 99.0
        got = bool(pressed(run(b, 0.0, 1.6, foes), 0.7 if foes else 0.0))   # (once it has noticed him)
        if got != want:
            fails.append(f"{tier} with {len(foes)} enemies in view: jetpack up a ledge = {got} (want {want})")

    # 4. about to push a held room: a power drain thrown at where he is believed to be
    b = bot("strong", "h3", "power_drain")
    held_at = A + Vec(-3.5, 1.5, 0.0)                     # within a short throw
    b.per.beliefs[2] = Belief(held_at, Vec(), 0.0, False, "callout")
    b.goal, b.next_decide = ("hunt", held_at), 99.0
    acts = run(b, 0.0, 0.3, [foe(held_at)], los=lambda p, q: False)   # in the room, out of sight
    thrown = [a for _, a, _ in acts if a.equipment]
    want = math.atan2(held_at.y - A.y, held_at.x - A.x)
    if not thrown or abs(math.atan2(math.sin(thrown[0].yaw - want), math.cos(thrown[0].yaw - want))) > 0.2:
        fails.append("no power drain thrown at the held room before the push")

    # 5. hologram: strong sends it round the corner at the believed enemy; a novice sends it at the man
    #    who is looking at it (wasted)
    b = bot("strong", "reach", "hologram")
    b.per.beliefs[2] = Belief(held_at, Vec(), 0.0, False, "callout")
    b.goal, b.next_decide = ("hunt", held_at), 99.0
    if not pressed(run(b, 0.0, 0.3, [foe(held_at)], los=lambda p, q: False)):
        fails.append("strong did not send a hologram ahead of the push")
    b = bot("novice", "reach", "hologram")
    if pressed(run(b, 0.0, 1.5, [foe(west, weapon="dmr", yaw=0.0)])):
        fails.append("a novice used its hologram (Easy uses no equipment, owner Oct 24)")

    # 6. sprint (Reach armor ability): HELD down for a clear route (its tag says toggle, but the game sprints only while
    #    the button is down: a tap was one tick of sprint;
    #    this check asked for a tap on and off until then); strong stops before a corner where an enemy may be
    b = bot("strong", "reach", "sprint")
    b.goal, b.next_decide = ("objective", A + Vec(40, 0, 0)), 99.0
    acts = run(b, 0.0, 1.6, [])
    # (from 0.6 s: the button waits for the full stick while the view swings round, live Boardwalk 060423: a sprint
    # pressed at half stick never came on)
    taps = [t for t, a, _ in acts if a.equipment and t >= 0.6]
    if len(taps) < 0.9 * sum(1 for t, _, _ in acts if t >= 0.6):
        fails.append(f"Reach sprint not held on a clear route (pressed {len(taps)} of {len(acts)} ticks)")
    for tier, want_sprint in (("strong", False), ("novice", False)):   # (Easy: no armor ability at all)
        b = bot(tier, "reach", "sprint")
        b.per.beliefs[2] = Belief(A + Vec(8, 0, 0), Vec(), 0.0, False, "callout")
        b.goal, b.next_decide = ("objective", A + Vec(40, 0, 0)), 99.0
        got = bool(pressed(run(b, 0.0, 0.5, [foe(A + Vec(8, 0, 0))], los=lambda p, q: False)))
        if got != want_sprint:
            fails.append(f"{tier}: sprint toward a corner with an enemy behind it = {got} (want {want_sprint})")
    b = bot("strong", "h4")
    b.goal, b.next_decide = ("objective", A + Vec(40, 0, 0)), 99.0
    if not any(a.sprint for _, a, _ in run(b, 0.0, 0.3, [])):
        fails.append("Halo 4: no sprint on a clear route (everyone's sprint button)")
    # a sprint the game does not take (the body stays at a walk) silences the gun half a second at most (guide 20 audit:
    # Sword Base, the gun quiet 330 held ticks in fights)
    b = bot("strong", "h4")
    b.goal, b.next_decide = ("objective", A + Vec(40, 0, 0)), 99.0
    k = b.kit
    me = PlayerState(1, 0, "bot", A, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
    if not (k.sprinting(0.0, me, "t_test") and k.sprinting(0.4, me, "t_test") and not k.sprinting(0.8, me, "t_test")):
        fails.append("a sprint at walking pace still silences the gun after 0.5 s")
    # 6b. sprint more: a man remembered 30 u off is no reason to walk (any memory
    #     was: 64% of Spire's moving decisions blocked); a man out of the AR's reach who looks away is chased, one who
    #     watches us is not; a lost fight with the shield down is run from even in his view, turned to run (a sprint goes
    #     forward only); Easy sprints a long walk with nobody about, not a short one
    b = bot("strong", "reach", "sprint")
    b.per.beliefs[2] = Belief(A + Vec(-30, 0, 0), Vec(), 0.0, False, "callout")
    b.goal, b.next_decide = ("objective", A + Vec(40, 0, 0)), 99.0
    if not pressed(run(b, 0.0, 0.5, [foe(A + Vec(-30, 0, 0))], los=lambda p, q: False)):
        fails.append("strong: no sprint on a clear route with a man remembered 30 u away")
    for yaw, want in ((math.pi, True), (0.0, False)):          # 10 u west of us, looking west (away) / east (at us)
        b = bot("strong", "reach", "sprint")
        b.goal, b.next_decide = ("fight", 2), 99.0
        acts = run(b, 0.0, 1.2, [foe(west, yaw=yaw, weapon="dmr")],
                   me_kw=dict(weapon="assault_rifle", weapons=["assault_rifle"]))
        if any("sprint after him" in n for n in notes(acts)) != want:
            fails.append(f"strong with an AR, a man 10 u off looking {'away' if want else 'at us'}: chase {not want}")
    b = bot("strong", "reach", "sprint")
    b.goal, b.next_decide = ("retreat", A + Vec(5, 0, 0)), 99.0              # cover east, the man west, watching us
    acts = run(b, 0.0, 1.5, [foe(west, weapon="dmr", yaw=0.0)], me_kw=dict(shield=0.1))
    late = [a for t, a, _ in acts if t > 1.0]
    if not pressed(acts, 0.5) or not all(abs(math.atan2(math.sin(a.yaw), math.cos(a.yaw))) < 0.5 and a.forward > 0.5
                                         for a in late):
        fails.append("strong, shield down, retreating in his view: no sprint turned to run at its cover")
    # 6c. a sprint stepped aside by a guard after the kit (the obstacle guard's "wall ahead: stepping around") is steered,
    #     not strafed: a strafe ends Reach's sprint (the player Spire: "they keep pressing buttons other than forward
    #     instead of steering with their aim")
    b = bot("strong", "reach", "sprint")
    b.per.beliefs[2] = Belief(A + Vec(-30, 0, 0), Vec(), 0.0, False, "callout")
    b.goal, b.next_decide = ("objective", A + Vec(40, 0, 0)), 99.0
    b.obstacle_guard = lambda now, me, act, snap: setattr(act, "strafe", 0.8)
    acts = run(b, 0.0, 0.8, [foe(A + Vec(-30, 0, 0))], los=lambda p, q: False)
    held = [a for _, a, _ in acts if a.equipment]
    if not held or any(abs(a.strafe) > 0.1 for a in held):
        fails.append(f"a sprint stepped aside by the obstacle guard: {sum(abs(a.strafe) > 0.1 for a in held)} of "
                     f"{len(held)} held ticks strafed (want none: steered)")
    for goal, want in ((A + Vec(40, 0, 0), True), (A + Vec(8, 0, 0), False)):
        b = bot("novice", "reach", "sprint")
        b.goal, b.next_decide = ("objective", goal), 99.0
        # (the use, not the button: since the button waits for a full forward stick, and this still harness's Easy
        # walk never turns round to one: its stick reads 0.15 while the look keeps the view west)
        if any("sprint the long walk" in n for n in notes(run(b, 0.0, 0.5, []))) != want:
            fails.append(f"Easy on a {(goal - A).flat():.0f} u walk: sprint {not want} (want {want})")
    # ... move_to takes no sprint flag (Bot.think passed sprint=kind != "hold", never read): the Kit decides, and a bot
    #     on its way to a hold post does not sprint (its moving goals leave hold out)
    if "sprint" in inspect.signature(Bot.move_to).parameters:
        fails.append("Bot.move_to still takes a sprint flag it never reads")
    b = bot("strong", "h4")
    b.goal, b.next_decide = ("hold", A + Vec(40, 0, 0)), 99.0
    if any(a.sprint for _, a, _ in run(b, 0.0, 0.3, [])):
        fails.append("Halo 4: sprinted on its way to a hold post")

    # 7. thruster to cover when the shield pops under fire
    b = bot("strong", "h4", "thruster")
    cover = A + Vec(0.0, 2.5, 0.0)
    b.cover_from = lambda me, threats: cover
    acts = run(b, 0.0, 1.5, [shooter], me_kw=cracked, each=lambda t, bb, a: setattr(bb, "hit_at", t))
    dash = [a for _, a, _ in acts if a.equipment]
    if not dash:
        fails.append("no thruster dash when cracked under fire with cover 2.5 units away")

    # 8. team items wait for the team, but not past a broken shield: a strong bot shot with its shield down and no cover
    #    drops its drop shield alone too (the wait rule above the broken-shield rules kept it for a regroup it did not
    #    live to see, guide 20 review); a regenerator for winning still waits for a teammate, and never goes down
    #    with him near enough to walk into the mist (EQ-REGEN-03, audit: it wanted him 3 u off before)
    for mates in (False, True):
        b = bot("strong", "reach", "drop_shield")
        b.cover_from = lambda me, threats: None
        others = [shooter] + ([PlayerState(5, 0, "bot", A + Vec(0, 2, 0), alive=True)] if mates else [])
        if not pressed(run(b, 0.0, 1.5, others, me_kw=cracked, each=lambda t, bb, a: setattr(bb, "hit_at", t))):
            fails.append(f"drop shield, shot with the shield down, a teammate near = {mates}: not used")
    mate = PlayerState(5, 0, "bot", A + Vec(0, 2, 0))
    for at, mates, want in ((6, [], None), (6, [mate], "regenerator: winning, out of his reach"), (3, [mate], None)):
        weak = foe(A + Vec(at, 0, 0), yaw=math.pi, shield=0.0, health=0.3)
        b = bot("strong", "h3", "regenerator")
        if plan_now(b, [weak] + mates, seen=(2,), goal=("fight", 2))[4] != want:
            fails.append(f"a strong regenerator winning, him {at} u off, {len(mates)} teammates: want {want}")

    # 9. counters: an armor-locked enemy is a timer, not a target: strong holds fire, backs off and
    #    reloads; a novice keeps shooting
    near = A + Vec(-3.0, 0.0, 0.0)
    locked = foe(near, weapon="dmr", yaw=0.0, equipment="armor_lock", ability_on=True)
    b = bot("strong", "reach")
    acts = run(b, 0.0, 2.0, [locked])
    late = [a for t, a, _ in acts if t > 0.6]
    if any(a.fire for a in late):
        fails.append("strong shot at an armor-locked enemy")
    if not any(a.reload for a in late) or not any(a.forward < -0.2 or abs(a.strafe) > 0.2 for a in late):
        fails.append("strong did not back off and reload from an armor lock")
    b = bot("novice", "reach")
    if not any(a.fire for t, a, _ in run(b, 0.0, 2.0, [locked]) if t > 0.6):
        fails.append("a novice did not keep shooting the armor lock (its bad spot)")

    # ... a grenade beside it from a strong bot
    b = bot("strong", "reach")
    b.grenade_ready_at = 0.0
    if not any(a.grenade for _, a, _ in run(b, 0.0, 2.0, [foe(A + Vec(-6, 0, 0), equipment="armor_lock", ability_on=True)])):
        fails.append("no grenade beside an armor lock")

    # 10. a man inside a Halo 3 bubble: nobody shoots the dome from outside; strong walks in to melee
    dome = [dict(kind="bubble_shield", pos=near, team=1, t=0.0)]
    for tier in ("strong", "average"):
        b = bot(tier, "h3")
        acts = run(b, 0.0, 2.0, [foe(near, weapon="battle_rifle", yaw=0.0)], deployed=dome)
        if any(a.fire for t, a, _ in acts if t > 0.6):
            fails.append(f"{tier} shot into a bubble shield from outside")
    acts = run(bot("strong", "h3"), 0.0, 2.0, [foe(near, weapon="battle_rifle", yaw=0.0)], deployed=dome)
    if not any("walk in" in n for n in notes(acts)):
        fails.append("strong did not walk into the bubble to melee")

    # 11. decoys: a runner on one line that never shoots is shot once, then left; if it vanished it was
    #     a hologram. A real man running straight who took the shot stays a target
    runner = lambda t: [foe(A + Vec(-8.0, -4.0 + 2.2 * t, 0.0), vel=Vec(0, 2.2, 0), yaw=math.pi / 2)]
    b = bot("strong", "reach")
    log = []
    run(b, 0.0, 3.5, runner, each=lambda t, bb, a: log.append((t, a.fire, 2 in bb.kit.shot_decoy,
                                                                bb.kit.real_until.get(2, 0.0) > t)))
    test = next((t for t, f, sus, real in log if sus), None)
    if test is None:
        fails.append("strong never test-shot the suspected decoy")
    else:
        if any(f for t, f, sus, real in log if test + 0.12 < t < test + 0.6):
            fails.append("strong kept shooting the suspect before seeing whether it was a decoy")
        if not any(f for t, f, sus, real in log if t > test + 0.7 and real):
            fails.append("a straight runner that took the test shot and stayed was not shot again")
    # ... and one that vanished at the test shot was a hologram
    b = bot("strong", "reach")
    shot = {}
    gone = lambda t: runner(t) if "t" not in shot or t < shot["t"] + 0.05 else []
    run(b, 0.0, 3.0, gone, each=lambda t, bb, a: shot.setdefault("t", t) if 2 in bb.kit.shot_decoy else None)
    if 2 not in b.kit.decoys:
        fails.append("a suspect that vanished at the test shot was not marked a decoy")
    # ... but one killed at it (dead in the list: a body) was a man, shot again once he is back. Dead =
    #     "decoy" for good made 3 bots never fire at the player again (his Reach game)
    b = bot("strong", "reach")
    shot = {}
    dies = lambda t: (runner(t) if "t" not in shot or t < shot["t"] + 0.05 else
                      [PlayerState(2, 1, "human", A + Vec(-8.0, 0.0, 0.0), alive=False)] if t < shot["t"] + 1.0 else
                      [foe(A + Vec(-9.0, 1.0, 0.0), yaw=0.0)])
    run(b, 0.0, 3.0, dies, each=lambda t, bb, a: shot.setdefault("t", t) if 2 in bb.kit.shot_decoy else None)
    back = foe(west, yaw=0.0)
    if "t" not in shot or not b.kit.can_shoot(3.0, me_state(b, A, math.pi, 0.0), back, Snapshot(3.0, [back])):
        fails.append(f"a man killed at the hologram test was taken for one (decoys {sorted(b.kit.decoys)})")
    # live, holograms are never among the players read: nobody is taken for one
    b = bot("strong", "reach")
    b.kit.decoys_listed = False
    sus = []
    run(b, 0.0, 3.5, runner, each=lambda t, bb, a: sus.append(2 in bb.kit.shot_decoy))
    if any(sus):
        fails.append("live (no holograms listed): a straight runner was still tested as a hologram")

    # 12. a power drain going off beside us: step out of it
    b = bot("strong", "h3")
    drain = [dict(kind="power_drain", pos=A + Vec(0.5, 0.0, 0.0), team=1, t=0.0)]
    acts = run(b, 0.0, 1.0, [foe(A + Vec(-5.0, 0.0, 0.0), yaw=0.0)], deployed=drain)
    if not any("power drain" in n for n in notes(acts)):
        fails.append("strong did not step out of a power drain")

    # 13. a trip mine on our path: step round it (novices walk on)
    mine = [dict(kind="trip_mine", pos=A + Vec(1.5, 0.0, 0.0), team=1, t=0.0)]
    for tier, want_round in (("strong", True), ("novice", False)):
        b = bot(tier, "h3")
        b.goal, b.next_decide = ("objective", A + Vec(20, 0, 0)), 99.0
        acts = run(b, 0.0, 0.3, [], deployed=mine, yaw0=0.0)    # facing its route east
        rounded = any(abs(a.strafe) > 0.5 for _, a, _ in acts)
        if rounded != want_round:
            fails.append(f"{tier}: stepped round a trip mine on its path = {rounded} (want {want_round})")

    # 14. Reach camo: the radar static gives him away to a strong bot (a belief near him); a novice
    #     sees nothing
    hidden = foe(A + Vec(-6.0, 0.0, 0.0), equipment="active_camo", ability_on=True, camo_until=99.0)
    for tier, want_belief in (("strong", True), ("novice", False)):
        b = bot(tier, "reach")
        run(b, 0.0, 0.5, [hidden], los=lambda p, q: False)
        got = ("static", 2) in b.per.beliefs
        if got != want_belief:
            fails.append(f"{tier}: radar static of a camo user near = belief {got} (want {want_belief})")

    # 15. a flare in the face: blind while it burns (novice), a second (strong: turns away)
    flare = [dict(kind="flare", pos=A + Vec(-2.0, 0.0, 0.0), team=1, t=0.0)]
    for tier, want_blind in (("novice", 2.5), ("strong", 0.9)):
        b = bot(tier, "h3")
        run(b, 0.0, 0.1, [], deployed=flare)
        if abs((b.kit.blind_until - 0.0) - (3.0 if tier == "novice" else 1.0)) > 0.11:
            fails.append(f"{tier}: flare blind until {b.kit.blind_until:.2f} s")

    # 16. use rules wide enough that every bot uses its ability: (bot tier, game, kind, foes, seen, goal, hit, my state, snapshot, the use
    #     wanted or None)
    nocover = lambda me, threats: None
    near6, far15 = foe(A + Vec(6, 0, 0), yaw=math.pi, weapon="dmr"), foe(A + Vec(15, 0, 0), yaw=math.pi, weapon="dmr")
    away10 = foe(A + Vec(10, 0, 0), yaw=0.0, weapon="dmr")                       # 10 u east, looking further east
    run_to = ("objective", A + Vec(30, 0, 0))
    down = dict(shield=0.1)
    for tier, game, kind, foes, seen, goal, hit, me_kw, snap_kw, want in (
            # camo: every style on a push (a rusher here; flanker / sniper / camper only before), an objective run 15+ u
            # for a runner and an Invasion attacker (not a defender); moving in only with no radar in the match
            # (EQ-RCAMO-02, audit: radar on, the jam gives the approach away; these ran with radar on before)
            ("strong", "reach", "active_camo", [foe(A + Vec(3.5, 0, 0))], (), ("hunt", A + Vec(3.5, 0, 0)), False,
             dict(tracker=False), {}, "camo for the approach"),
            ("strong", "reach", "active_camo", [foe(A + Vec(3.5, 0, 0))], (), ("hunt", A + Vec(3.5, 0, 0)), False, {}, {},
             None),
            ("strong", "reach", "active_camo", [], (), run_to, False, dict(tracker=False),
             dict(mode="invasion", inv_attackers=0), "camo for the objective run"),
            ("strong", "reach", "active_camo", [], (), run_to, False, {}, dict(mode="invasion", inv_attackers=0), None),
            ("strong", "reach", "active_camo", [], (), run_to, False, dict(tracker=False),
             dict(mode="invasion", inv_attackers=1), None),
            # armor lock: any tier, shot with the shield down and him within 8 u (Normal's only before); not him 15 u off
            ("strong", "reach", "armor_lock", [near6], (2,), ("fight", 2), True, down, {},
             "armor lock: shield down, he is close"),
            ("top", "reach", "armor_lock", [far15], (2,), ("fight", 2), True, down, {}, None),
            # evade: shot with the shield down, him within 8 u, no cover: a dash square to him; a thruster only into
            # cover (EQ-THRUST-02, audit: "a thrust into open ground is a slow strafe"; it dashed into the open before)
            ("strong", "reach", "evade", [near6], (2,), ("fight", 2), True, down, {}, "dash out of his aim, shield down"),
            ("strong", "h4", "thruster", [near6], (2,), ("fight", 2), True, down, {}, None),
            # heal field and regenerator alone with the shield down (the team-item wait rule blocked them)
            ("strong", "h4", "regen_field", [near6], (2,), ("fight", 2), True, down, {}, "shield down, no cover: heal field"),
            ("strong", "h3", "regenerator", [foe(A + Vec(6, 0, 0), yaw=math.pi, shield=0.0, health=0.3)], (2,),
             ("fight", 2), True, down, {}, "regenerator: winning the trade"),
            # jetpack: on the way to a goal 3 u up 6 u off, unseen; not one 1 u up
            ("strong", "reach", "jetpack", [], (), ("objective", A + Vec(6, 0, 3)), False, {}, {}, "jetpack up to the goal"),
            ("strong", "reach", "jetpack", [], (), ("objective", A + Vec(6, 0, 1)), False, {}, {}, None),
            # hologram in a fight past 6 u while he looks elsewhere; not while he watches us
            ("strong", "reach", "hologram", [away10], (2,), ("fight", 2), False, {}, {}, "hologram to draw his eyes"),
            ("strong", "reach", "hologram", [foe(A + Vec(10, 0, 0), yaw=math.pi, weapon="dmr")], (2,), ("fight", 2), False,
             {}, {}, None),
            # flare: a sniper 20 u off scoping us (only "within 4.5 u" before, so never: snipers are 12 u off or more)
            ("strong", "h3", "flare", [foe(A + Vec(20, 0, 0), yaw=math.pi, weapon="sniper")], (2,), ("fight", 2), False,
             {}, {}, "flare the sniper"),
            # Promethean Vision unseen with a man remembered 15 u off
            ("strong", "h4", "promethean_vision", [far15], (), ("roam", None), False, {}, {}, "PV: where is he"),
            # autosentry in a fight past 6 u; hardlight when shot and losing at 15 u (4-12 u and no cover before)
            ("strong", "h4", "autosentry", [away10], (2,), ("fight", 2), False, {}, {}, "sentry on him"),
            ("strong", "h4", "hardlight_shield", [far15], (2,), ("fight", 2), True, dict(shield=0.2), {},
             "hardlight: shot and losing")):
        b = bot(tier, game, kind)
        b.cover_from = nocover
        got = plan_now(b, foes, seen, goal, hit, me_kw, **snap_kw)[4]
        if got != want:
            fails.append(f"{tier} {kind}, goal {goal[0]}: {got!r} (want {want!r})")
    # ... a Halo 4 Flood survivor never raises the hardlight shield at a lunging Flood (it shoots him: the owner's Blood
    #     Cavern Flood 20261105-225014, "using the hardlight shield more than shooting"); in Slayer a top bot still blocks
    #     a sword lunge
    lunger = foe(A + Vec(3.0, 0, 0), yaw=math.pi, weapon="sword")
    for snap_kw, want in ((dict(mode="infection", infected=1), None), ({}, "hardlight: block it")):
        b = bot("top", "h4", "hardlight_shield")
        b.cover_from = nocover
        got = plan_now(b, [lunger], (2,), ("fight", 2), False, {}, **snap_kw)[4]
        if got != want:
            fails.append(f"hardlight vs a sword lunge {snap_kw or 'slayer'}: {got!r} (want {want!r})")
    # ... the owner's three cases (Nov 5): a short block when it cannot shoot back first: magazine empty (then a melee),
    #     swarmed by two lunging Flood, or backed into a corner
    lunger2 = foe(A + Vec(2.5, 1.0, 0), i=3, yaw=math.pi, weapon="sword")
    for foes_, seen_, kw, want in (
            ([lunger, lunger2], (2, 3), {}, "survivor: swarmed, block and shoot the gaps"),
            ([lunger], (2,), dict(weapon="shotgun", weapons=["shotgun"], mag=[0], ammo=[12]), "survivor: block, then melee")):
        b = bot("top", "h4", "hardlight_shield")
        b.cover_from = nocover
        got = plan_now(b, foes_, seen_, ("fight", 2), False, kw, mode="infection", infected=1)[4]
        if got != want:
            fails.append(f"survivor, {want.split(':')[1].strip()}: {got!r} (want {want!r})")
    b = bot("top", "h4", "hardlight_shield")
    b.cover_from = nocover
    b.air_terrain = lambda: type("Box", (), {"clearance": staticmethod(lambda p, yaw, far=3.0: 0.6)})()
    got = plan_now(b, [lunger], (2,), ("fight", 2), False, {}, mode="infection", infected=1)[4]
    if got != "survivor: cornered, block":
        fails.append(f"a survivor walled in on every side with a Flood lunging: {got!r} (want a cornered block)")
    # ... and the block stays short (never stretched while the Flood is near), the gun comes back for 1.2 s before the
    #     next, and the let-go of an empty-gun block is a melee
    b = bot("top", "h4", "hardlight_shield")
    b.cover_from = nocover
    close = foe(A + Vec(1.2, 0, 0), yaw=math.pi, weapon="sword")
    held, melee, t = [], 0, 0.0
    while t < 3.0:
        b.per.beliefs[2] = Belief(close.pos, close.vel, t, True, "eyes")
        b.per.recognized.add(2)
        me = me_state(b, A, 0.0, 0.0, weapon="shotgun", weapons=["shotgun"], mag=[0], ammo=[12])
        sn = Snapshot(t, [me, close], mode="infection", infected=1)
        a = b.think(t, DT, sn, lambda p, q: True, lambda p, q, **k: q, [])
        held.append(bool(a.ability or a.equipment))
        melee += bool(a.melee)
        t += DT
    runs, cur = [], 0
    for h in held:
        cur = cur + 1 if h else (runs.append(cur) or 0) if cur else 0
    longest = max(runs + [cur]) * DT
    if not held.count(True) or longest > 0.75:
        fails.append(f"survivor blocks: longest {longest:.2f} s (want 0.6 s blocks), held {held.count(True)} of {len(held)} ticks")
    if held.count(True) * DT > 0.45 * 3.0:
        fails.append(f"survivor blocks: shield up {held.count(True) * DT:.1f} of 3 s (the gun should have most of it)")
    if not melee:
        fails.append("survivor block with an empty gun: no melee on the let-go")
    b = bot("novice", "h4", "hardlight_shield")
    b.cover_from = nocover
    got = plan_now(b, [lunger], (2,), ("fight", 2), True, {}, mode="infection", infected=1)[4]
    if got is not None:
        fails.append(f"a novice survivor hit by the Flood raised the hardlight shield: {got!r}")
    b = bot("strong", "reach", "active_camo")
    b.order.role = "runner"
    if plan_now(b, [], (), run_to, me_kw=dict(tracker=False))[4] != "camo for the objective run":
        fails.append("a runner 30 u from its objective, unseen: no camo")
    b = bot("strong", "reach", "evade")
    b.cover_from = nocover
    point = plan_now(b, [near6], (2,), ("fight", 2), True, down)[2]
    if point is None or abs((point - A).x) > 0.01 or abs(abs((point - A).y) - 3.0) > 0.01:
        fails.append(f"the evade dash goes to {point} (want 3 u square to the man east of us)")
    # ... Promethean Vision pulses every 10 s at most (its unseen trigger would hold it on); a camo switched off at the
    #     end of its run is not switched on again in the same tap (the one press left it off, and the next "off" tap
    #     turned it on)
    b = bot("strong", "h4", "promethean_vision")
    pv = run(b, 0.0, 4.0, [far15], los=lambda p, q: False,
             each=lambda t, bb, a: bb.per.beliefs.__setitem__(2, Belief(far15.pos, Vec(), t, False, "callout")))
    if sum("PV: where is he" in n for n in notes(pv)) != 1:
        fails.append(f"PV pulses in 4 s: {sum('PV: where is he' in n for n in notes(pv))} (want 1)")
    def pushing(t, bb, a):                        # (still pushing the room he is called in)
        bb.per.beliefs[2], bb.goal = Belief(held_at, Vec(), t, False, "callout"), ("hunt", held_at)
    b = bot("strong", "reach", "active_camo", pers="flanker")
    b.goal, b.next_decide = ("hunt", held_at), 99.0
    camo = run(b, 0.0, 6.8, [foe(held_at)], los=lambda p, q: False, each=pushing, me_kw=dict(tracker=False))   # (no radar)
    taps = [round(t, 2) for t, a, _ in camo if a.equipment]
    if len(taps) != 3 or not 0.25 < taps[2] - taps[1] < 0.5:
        fails.append(f"camo taps at {taps} (want on, off at the end of the 6 s run, on again a moment later)")

    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("equipment OK")


if __name__ == "__main__":
    main()
