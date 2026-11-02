"""The audit's equipment rows (docs/oct31/audit.md "### Equipment", the player's equipment guide), each a check that
fails on the code before:

wrong before:
 1. EQ-RCAMO-02 camo is switched on while moving in only with no radar in the match; radar on, not
 2. EQ-RCAMO-03 radar on: camo goes on in position (still at the hold spot, a man expected) and stays on past 6 s while
    the bot stands there; it ends when the bot moves off
 3. EQ-THRUST-02 a thruster dash out of a rocket's line ends in cover (cover within reach), never into the open
 4. EQ-HLS-02 no hardlight shield with two enemies in sight; one: yes
 5. EQ-HLS-04 no hardlight shield against a vehicle about to hit us
 6. EQ-BUBBLE-03 out of our own dome on the side away from him, and only at full shields
 7. EQ-REGEN-03 the regenerator never goes down with him near enough to walk into the mist
 8. INF-SURV-05 an Infection survivor never armor locks against the infected; with a jetpack it flies up
not coded before:
 9. H3-CTF-07 / EQ-BUBBLE-01 (b) a bubble shield before the enemy flag grab under fire; (a) over a teammate, shield down
10. EQ-DRAIN-01 (a) a power drain on an enemy vehicle in throwing range; (b) on two men grouped
11. EQ-OS-02 our own overshield makes the bot's posture aggressive for 20 s
12. EQP-03 overshielded, the team playing safe: a powerup near is still taken (denial)
13. PU-01 / PU-02 (H3-ASS-07, REACH-CTF-03) the camo powerup is worth more to a runner than to a defender

usage: python -I test_equipment_audit.py      -> "equipment audit OK (...)"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief  # noqa: E402
from brain.core import Action, FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from test_equipment import A, DT, bot, foe, me_state, plan_now  # noqa: E402

NOCOVER = lambda me, threats: None


def why(p):
    return p[4] if p else None


def main():
    fails, info = [], []
    hunt = ("hunt", A + Vec(3.5, 0, 0))

    # 1
    for tracker, want in ((False, "camo for the approach"), (True, None)):
        b = bot("strong", "reach", "active_camo")
        got = why(plan_now(b, [foe(A + Vec(3.5, 0, 0))], (), hunt, me_kw=dict(tracker=tracker)))
        if got != want:
            fails.append(f"camo moving in, radar {'on' if tracker else 'off'}: {got!r} (want {want!r})")

    # 2
    b = bot("strong", "reach", "active_camo")
    spot = A + Vec(0.5, 0, 0)
    b.goal, b.order.role = ("hold", spot), "defender"
    t, on, ended = 1.0, [], None
    while t < 12.0:
        moving = t > 9.0
        me = me_state(b, A + (Vec(0.1 * (t - 9.0) * 15, 0, 0) if moving else Vec()), 0.0, 0.0,
                      vel=Vec(1.5, 0, 0) if moving else Vec())
        b.per.beliefs[2] = Belief(A + Vec(15, 0, 0), Vec(), t, False, "radar")
        snap = Snapshot(t, [me, foe(A + Vec(15, 0, 0))])
        b.kit.perceive(b, t, me, snap)
        a = Action()
        b.kit.act(b, t, DT, me, snap, a)
        if a.equipment:
            on.append(round(t, 2))
        if moving and ended is None and b.kit.press is None:
            ended = t
        t += DT
    if not on or on[0] > 1.1:
        fails.append(f"camo in position (radar on, still, a man expected): first press at {on[:1]} (want at once)")
    elif any(1.2 < x < 9.0 for x in on):
        fails.append(f"camo in position: tapped again at {[x for x in on if 1.2 < x < 9.0][:1]} while still (want kept on)")
    if ended is None or ended > 9.3:
        fails.append(f"camo in position: still held {ended} after moving off at 9.0 s")

    # 3
    rocket = foe(A + Vec(-10.0, 0.0, 0.0), weapon="rockets", yaw=0.0)
    b = bot("strong", "h4", "thruster")
    b.cover_from = NOCOVER
    p = plan_now(b, [rocket], (2,))
    if p and p[1] == "dash":
        fails.append(f"thruster out of a rocket's line with no cover: dashed to {p[2]} (want no dash into the open)")
    b = bot("strong", "h4", "thruster")
    cov = A + Vec(0.0, 2.5, 0.0)
    b.cover_from = lambda me, threats: cov
    p = plan_now(b, [rocket], (2,))
    if not p or p[1] != "dash" or p[2] is None or (p[2] - cov).flat() > 1.0:
        fails.append(f"thruster out of a rocket's line with cover 2.5 u off: {p and p[:3]} (want a dash into it)")

    # 4
    hard = dict(shield=0.2)
    for n, want in ((1, "hardlight: shot and losing"), (2, None)):
        b = bot("strong", "h4", "hardlight_shield")
        b.cover_from = NOCOVER
        foes = [foe(A + Vec(15, 0, 0), yaw=math.pi, weapon="dmr")] + (
            [foe(A + Vec(0, 12, 0), i=3, yaw=-math.pi / 2, weapon="dmr")] if n > 1 else [])
        got = why(plan_now(b, foes, tuple(range(2, 2 + n)), ("fight", 2), True, hard))
        if got != want:
            fails.append(f"hardlight with {n} enemies in sight: {got!r} (want {want!r})")

    # 5
    b = bot("strong", "h4", "hardlight_shield")
    hog = foe(A + Vec(5, 0, 0), vel=Vec(-8, 0, 0), vehicle=4)
    got = why(plan_now(b, [hog], (2,)))
    if got and got.startswith("hardlight"):
        fails.append(f"hardlight against a Warthog about to hit: {got!r} (want none: step aside)")

    # 6
    dome = [dict(kind="bubble_shield", pos=A, team=0, t=0.0)]
    for shield, want in ((1.0, "own dome: step out away from him"), (0.7, "own dome: recharge inside")):
        b = bot("strong", "h3")
        me = me_state(b, A, 0.0, 0.0, shield=shield)
        e = foe(A + Vec(6, 0, 0))
        snap = Snapshot(1.0, [me, e], deployed=dome)
        a = Action(yaw=0.0)
        got = b.kit.fight_move(b, 1.0, me, e, snap, a)
        if got != want or (shield == 1.0 and a.forward > -0.9):
            fails.append(f"own dome at shield {shield}, him east: {got!r}, stick forward {a.forward:.2f} (want {want!r}"
                         f"{', west' if shield == 1.0 else ''})")

    # 7
    mate = PlayerState(5, 0, "bot", A + Vec(0, 2, 0))
    for at, want in ((6, "regenerator: winning, out of his reach"), (3, None)):
        b = bot("strong", "h3", "regenerator")
        weak = foe(A + Vec(at, 0, 0), yaw=math.pi, shield=0.0, health=0.3)
        got = why(plan_now(b, [weak, mate], (2,), ("fight", 2)))
        if got != want:
            fails.append(f"regenerator winning, him {at} u off: {got!r} (want {want!r})")

    # 8
    zombie = foe(A + Vec(3, 0, 0), yaw=math.pi, weapon="sword")
    inf = dict(mode="infection", infected=1)
    b = bot("strong", "reach", "armor_lock")
    got = why(plan_now(b, [zombie], (2,), ("fight", 2), True, dict(shield=0.1), **inf))
    if got and got.startswith("armor lock"):
        fails.append(f"Infection survivor, a zombie lunging: {got!r} (want no armor lock)")
    b = bot("strong", "reach", "jetpack")
    got = why(plan_now(b, [zombie], (2,), ("fight", 2), False, {}, **inf))
    if got != "jetpack up out of the lunge":
        fails.append(f"Infection survivor with a jetpack, a zombie lunging: {got!r} (want up out of it)")

    # 9
    flag = {1: FlagState(1, A + Vec(1.5, 0, 0), A + Vec(1.5, 0, 0))}
    b = bot("strong", "h3", "bubble_shield")
    got = why(plan_now(b, [foe(A + Vec(15, 0, 0), yaw=math.pi)], (2,), ("objective", A + Vec(1.5, 0, 0)), True,
                       flags=flag, mode="ctf"))
    if got != "bubble before the grab":
        fails.append(f"at the enemy flag under fire with a bubble: {got!r} (want the bubble before the grab)")
    b = bot("strong", "h3", "bubble_shield")
    hurt_mate = PlayerState(5, 0, "bot", A + Vec(1, 0, 0), alive=True, shield=0.0)
    got = why(plan_now(b, [foe(A + Vec(15, 0, 0), yaw=math.pi), hurt_mate], (2,), ("fight", 2)))
    if got != "bubble over a teammate, shield down":
        fails.append(f"a teammate beside us shield down, a man in sight: {got!r} (want the bubble over him)")

    # 10
    b = bot("strong", "h3", "power_drain")
    got = why(plan_now(b, [foe(A + Vec(5, 0, 0), vehicle=4)], (2,)))
    if got != "drain the vehicle, board it":
        fails.append(f"an enemy vehicle 5 u off with a power drain: {got!r} (want drain it)")
    b = bot("strong", "h3", "power_drain")
    got = why(plan_now(b, [foe(A + Vec(4, 0, 0)), foe(A + Vec(4, 2, 0), i=3)], (2, 3), ("fight", 2)))
    if got != "drain the group":
        fails.append(f"two men grouped 4 u off with a power drain: {got!r} (want drain the group)")

    # 11
    b = bot("strong", "reach")
    post = getattr(b.kit, "posture", lambda now, me, p: p)
    me_os = me_state(b, A, 0.0, 0.0, shield=1.8)
    got = [post(t, me_os, 0.5) for t in (1.0, 15.0, 22.0)]
    if got != [0.9, 0.9, 0.5]:
        fails.append(f"overshielded posture at 0 / 14 / 21 s: {got} (want 0.9 0.9 0.5)")

    # 12 + 13
    def item(role="defender", posture=0.5, shield=1.0):
        b = bot("top", "ce")
        b.order.role, b.posture = role, posture
        return b.best_item(1.0, me_state(b, A, 0.0, 0.0, shield=shield, weapon="rockets"))

    camo = Vec(59.0, -116.9, 1.8)
    got = item(posture=0.2, shield=1.5)
    if not got or (got[0] - camo).flat() > 0.5:
        fails.append(f"overshielded, the team playing safe, camo 11 u off: goes for {got and got[0]} (want the camo)")
    run, dfd = item("runner"), item("defender")
    if not (run and dfd and (run[0] - camo).flat() < 0.5 and run[1] - dfd[1] > 0.2):
        fails.append(f"camo for a runner {run and round(run[1], 2)} vs a defender {dfd and round(dfd[1], 2)} (want the "
                     f"runner's higher)")
    else:
        info.append(f"camo runner {run[1]:.2f} / defender {dfd[1]:.2f}")

    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("equipment audit OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
