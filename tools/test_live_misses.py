"""The misses of the live Boardwalk match (060423, Team Slayer DMR 4v4: jetpack 20 of 20 presses on, armor lock 3 of 5,
camo 6 of 6, sprint 9 of 34, hologram 0 of 50; logs/tmp/press_misses.py, owner_press_detail.py):

1. press shapes by the game's rule (use_of): a press of a hold-mode kind lasts its warmup and 0.2 s more, so the drop
   shield (warmup 0.5 s) is held 0.7 s (the player's held 1.06 / 1.44 s ones went down, his 0.2 s taps mostly not);
   evade and hologram (no warmup) keep the player's 0.2 s tap; all three send the hold bit (hold-mode tags)
2. sprint: no button while the stick is short of full forward (turning to the way); with it full, pressed
3. sprint: held 0.6 s by a bot that runs, but not running now (a wall, the unstuck wiggle): let go
4. armor lock: refused by the game (the reader showed our locks before, this one never comes on, unhurt): let go by
   0.6 s and the meter taken as empty; with the reader turned off for armor lock (live_bots' misread guard), held on
Hologram: its tag is hold-mode and is pressed as one; its on-state is never read, a skilled player's 14 presses in the
collector files never read on either (logs/tmp/owner_press_detail.py): the live 0 of 50 is the reader, not the press.

usage: python -I test_live_misses.py      -> "live misses OK (...)"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import hold_bit, use_of  # noqa: E402
from test_equipment import A, DT, bot  # noqa: E402


def tick(b, t, kind, plan=None, **me_kw):
    me = PlayerState(b.id, 0, "bot", A, alive=True, equipment=kind, **me_kw)
    snap = Snapshot(t, [me])
    b.kit.perceive(b, t, me, snap)
    b.kit.plan = (lambda *a, **k: plan) if plan else (lambda *a, **k: None)
    return me, snap


def main():
    fails, info = [], []

    # 1
    for kind, lo, hi in (("drop_shield", 0.68, 0.74), ("evade", 0.18, 0.22), ("hologram", 0.18, 0.22)):
        how, secs = use_of("reach", kind)
        if how != "press" or not lo <= secs <= hi or not hold_bit("reach", kind):
            fails.append(f"reach {kind}: {how} {secs:.2f} s, hold bit {hold_bit('reach', kind)} (want a press "
                         f"{lo}-{hi} s with the hold bit)")
        info.append(f"{kind} {secs:.2f} s")

    # 2 + 3
    for fwd, want in ((0.5, False), (1.0, True)):
        b = bot("strong", "reach", "sprint")
        me, snap = tick(b, 1.0, "sprint", ("sprint", "self", None, 4.0, "sprint the clear route"))
        a = Action(forward=fwd)
        b.kit.act(b, 1.0, DT, me, snap, a)
        if a.equipment != want:
            fails.append(f"sprint with the stick at {fwd}: button {a.equipment} (want {want})")
    b = bot("strong", "reach", "sprint")
    t, held, let_go = 1.0, [], None
    while t < 2.5:
        speed = 3.2 if t < 1.3 else 0.4                  # sprinting, then held up at a wall
        me, snap = tick(b, t, "sprint", ("sprint", "self", None, 4.0, "sprint the clear route") if t == 1.0 else None,
                        vel=Vec(speed, 0, 0))
        a = Action(forward=1.0)
        note = b.kit.act(b, t, DT, me, snap, a)
        if a.equipment:
            held.append(t)
        if note == "sprint: blocked, let go" and let_go is None:
            let_go = t
        t += DT
    if let_go is None or held and held[-1] > 1.75:
        fails.append(f"sprint held into a wall: let go at {let_go}, last pressed {held[-1] if held else None:.2f} s "
                     f"(want let go by 1.7 s: 0.6 s in, slow)")

    # 4
    for unread, want_released in ((False, True), (True, False)):
        b = bot("strong", "reach", "armor_lock")
        if unread:
            b.kit.unread = {"armor_lock"}
        t, on_t, held = 1.0, None, []
        plan = ("armor_lock", "self", None, 2.0, "armor lock: rocket / laser")
        # first lock comes on (the reader works), let go at 1.5 s; then a second press the game refuses
        for t0, comes_on in ((1.0, True), (3.0, False)):
            t = t0
            while t < t0 + (0.5 if comes_on else 1.2):
                me, snap = tick(b, t, "armor_lock", plan if t == t0 else None, ability_on=comes_on and t > t0 + 0.05)
                if not comes_on:
                    b.kit.cool.clear()
                a = Action()
                note = b.kit.act(b, t, DT, me, snap, a)
                if not comes_on and a.equipment:
                    held.append(t)
                if not comes_on and note == "armor_lock: did not lock, fighting on":
                    on_t = t - t0
                t += DT
            b.kit.hold_until = 0.0
            if comes_on and b.kit.energy is not None:
                b.kit.energy.level = 1.0
        last = held[-1] - 3.0 if held else 0.0
        released = on_t is not None and last < 0.65
        if released != want_released:
            fails.append(f"armor lock refused (reader {'off' if unread else 'on'}): pressed to {last:.2f} s (want "
                         f"{'let go by 0.6 s: did not lock' if want_released else 'no did-not-lock'})")
        if want_released and b.kit.energy is not None and b.kit.energy.level > 0.2:
            fails.append(f"armor lock refused: the model's meter {b.kit.energy.level:.2f} (want taken as empty)")

    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("live misses OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
