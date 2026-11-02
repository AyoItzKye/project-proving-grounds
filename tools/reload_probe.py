"""Live check of a bot's reload (brain off: logs/test_override.json "brain": "none"): every bot fires in pulses for
4 s (its magazine drops), stands 2 s (nothing may change: no reload without the button), then presses reload (botcore's
HB_BTN_RELOAD: native in CE, the decoded entry of maps/_inputs/<game>.json elsewhere) and waits 3.5 s. A bot passes
when the magazine refilled and the reserve fell by exactly what the magazine gained. Writes
logs/verify/reload_probe_<game>[_tap]_<date>.txt.

usage: python -I reload_probe.py <ce|h2|h3> [--tap] [--pickup]   (--tap: a one-tick press, as the brain sends it;
       --pickup: first 20 s walking each bot onto a loose gun with rounds)
"""
import math
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
import live_bots  # noqa: E402
from ammo_scan import GUN, held, release  # noqa: E402

RELOAD = botctl.BTN["reload"]


def rounds(live, h):
    """(reserve, magazine) of a gun: the reader's rounds() (Halo 2 / 3) or CE's ammo / mag."""
    if hasattr(live, "rounds"):
        total, mag = live.rounds(h)
    else:
        total, mag = live.ammo(h), live.mag(h)
    return (total - mag if total >= 0 and mag >= 0 else -1), mag


def drive(m, live, buttons, seconds):
    t0 = time.time()
    while time.time() - t0 < seconds:
        b = buttons(time.time() - t0)
        for slot in botctl.status(m)["bots"]:
            yaw = struct.unpack_from("<f", m, botctl.OFF_ACTIONS + slot * 24 + 8)[0]
            botctl.act(m, slot, 0.0, 0.0, yaw, 0.0, b)
        time.sleep(1 / 30)


def pickup(m, live, seconds):
    """Walk every bot straight at the nearest loose gun with rounds on its own floor (1.5 up or down) and press action on
    it (standing on one takes nothing in CE): for a lobby whose bots spawn with battery guns only (the player question
    3; a bot walled off from every gun gets none: no path finding here). An armed bot then steps 2.5 units clear of
    every loose gun (one of its kind underfoot tops the reserve up and hides what a reload cost: an AR's reserve held
    at its 600 cap) and stops. The list is re-read every second."""
    t0, read_at, loose = time.time(), -1.0, []
    while time.time() - t0 < seconds:
        if time.time() - read_at >= 1.0:
            read_at, loose = time.time(), live.ground_weapons()
        units = {p["index"]: p for p in live.players() if p.get("pos") is not None}
        for slot, index in botctl.status(m)["bots"].items():
            u = units.get(index)
            p = u and u["pos"]
            floor = [(n, q, math.hypot(q[0] - p[0], q[1] - p[1])) for n, q in loose if p and abs(q[2] - p[2]) < 1.5]
            armed = u and any(a > 0 for a in u.get("ammo", []))   # a gun with rounds (third review N6: by name, an
                                                                   # "unknown" Halo 3 gun counted as armed)
            near = [x for x in floor if armed and x[2] < 2.5 or not armed and x[0] not in live.BATTERY | {"flag", "ball"}]
            if not near:
                botctl.act(m, slot, 0.0, 0.0, struct.unpack_from("<f", m, botctl.OFF_ACTIONS + slot * 24 + 8)[0], 0.0, 0)
                continue
            _, q, d = min(near, key=lambda x: x[2])
            yaw = math.atan2(q[1] - p[1], q[0] - p[0]) + (math.pi if armed else 0.0)     # armed: away from it
            on = not armed and d < 0.6
            press = botctl.BTN["action"] if on and (time.time() - t0) % 0.4 < 0.2 else 0     # pulses: a fresh press each
            botctl.act(m, slot, 0.0 if on else 1.0, 0.0, yaw, 0.0, press)
        time.sleep(1 / 30)


def state(m, live, game):
    units = {p["index"]: p["unit"] for p in live.players() if p.get("pos") is not None}
    out = {}
    for slot, index in botctl.status(m)["bots"].items():
        if index in units:
            h, w = held(live, game, units[index])
            if w:
                out[slot] = (h, *rounds(live, h))
    return out


def main():
    game = sys.argv[1]
    live, m = GUN[game][0](), botctl.shm()
    if game != "ce":                                   # the decoded buttons, as live_bots loads them
        botctl.set_button_map(m, live_bots.decoded_buttons(game))
    tap = "--tap" in sys.argv                         # one tick, as the brain presses it (reload_check)
    try:
        if "--pickup" in sys.argv:
            pickup(m, live, 20.0)
            drive(m, live, lambda t: 0, 1.0)
        drive(m, live, lambda t: 1 if (t % 1.0) < 0.4 else 0, 4.0)    # fire in pulses: the magazines drop
        drive(m, live, lambda t: 0, 0.5)
        a = state(m, live, game)
        drive(m, live, lambda t: 0, 2.0)                               # no button: nothing may change
        b = state(m, live, game)
        drive(m, live, lambda t: RELOAD if t < (0.02 if tap else 0.3) else 0, 3.5)   # reload
        c = state(m, live, game)
    finally:
        release(m)                                     # never leave the bots pressing (botcore has no watchdog)
    out, ok = [f"{game}: reload probe ({'one-tick press' if tap else '0.3 s press'}), {len(a)} bots"], 0
    for slot in sorted(a):
        if slot not in b or slot not in c or a[slot][0] != c[slot][0]:
            out.append(f"bot slot {slot}: gun changed or bot gone, skipped")
            continue
        (_, r0, m0), (_, r1, m1), (_, r2, m2) = a[slot], b[slot], c[slot]
        still = (r0, m0) == (r1, m1)
        refill = m2 > m1 and r2 == r1 - (m2 - m1)
        ok += still and refill
        out.append(f"bot slot {slot}: before (reserve {r0}, magazine {m0}); 2 s idle ({r1}, {m1}) unchanged: {still}; "
                   f"after reload ({r2}, {m2}): refilled from reserve: {refill}")
    out.append(f"passed: {ok} of {len(a)}")
    path = os.path.join(HERE, "..", "logs", "verify",          # dated: a later run with no armed bot overwrote a pass
                        f"reload_probe_{game}{'_tap' if tap else ''}_{time.strftime('%Y%m%d-%H%M%S')}.txt")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
