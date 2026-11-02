"""Live probe of the Falcon's controls and of the seat exit (Reach; supervisor). Falcon pilots never left the ground (0%
moving in 3 seats) and no source gives a hovering aircraft's climb input. Needs a match on a map with Falcons (the
player's VEHICLE TEST) started with the test override's "brain": "none" and one bot (play.py adds it and leaves it to
this tool).

falcon: bot slot 0 walks to the nearest Falcon by the nav, presses Use for the pilot's seat (0) until in, then holds each
  candidate HOLD s with REST s of nothing between, reading the Falcon's place every tick: nothing, forward, pitch up /
  down with and without forward, jump; then each bit of the control flags (+0x08, 64 bits) and of the action flags
  (+0x40, 32 bits but 1 / 21, the seat exit) and 1.0 / -1.0 in each float not decoded (+0x18, +0x24 .. +0x3C), pressed
  through botcore's button table (the crouch button's entry: Reach has none decoded). Over 1 u up in a hold = a climb
  input, over 1 u down = a descent.
exits: the same bot gets into each kind of vehicle on the map (pilot / driver seat) and presses Use (botcore s107: the
  pressed bits while seated): the seconds until it is out, or "stayed in".
Writes logs/verify/falcon_probe_<date>.txt.

usage: python -I falcon_probe.py [falcon] [exits] [--only basic|bits|floats] [--hold S] [--rest S]
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import botctl  # noqa: E402
import live_bots  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.live import LiveReach  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

ACTION, JUMP, CROUCH = botctl.BTN["action"], botctl.BTN["jump"], botctl.BTN["crouch"]
HZ = 30
OUT = []


def say(line):
    print(line, flush=True)
    OUT.append(line)


def kind(path):
    return path.rsplit("\\", 1)[-1]


class Probe:
    def __init__(s):
        s.live, s.m = LiveReach(), botctl.shm()
        bots = botctl.status(s.m)["bots"]
        if not bots:
            sys.exit("no bot slots: start the match with the test override's brain none and one bot")
        s.slot, s.index = sorted(bots.items())[0]
        s.base = live_bots.decoded_buttons("reach")
        M = get_map("reach_forge_halo")
        try:                                        # the variant's own nav, as live_bots finds it
            from brain.forge import live_pieces
            from brain.variants import base_area, base_placed, identify
            name = identify(M["name"], live_pieces(s.live), base_placed(M["objects"]), game="reach",
                            area=base_area(M["objects"]))
            M = get_map(name)
        except Exception as e:
            say(f"(variant not read: {e}; the base map's nav)")
        s.T = terrain(M)
        s.yaw = 0.0

    def me(s):
        return next((p for p in s.live.players() if p["index"] == s.index and p.get("pos") is not None), None)

    def vehicles(s, want=None):
        return [(h, kind(path), pos) for h, typ, path, pos in s.live.objects((1,)) if want is None or kind(path) == want]

    def act(s, forward=0.0, pitch=0.0, buttons=0, strafe=0.0):
        botctl.act(s.m, s.slot, forward, strafe, s.yaw, pitch, buttons)

    def doors(s, handle, k, pos):
        """Where to stand to get in: the brain's driver door (Bot.seat_point, front left by the facing), then the
        other sides 1.8 u out (live: 1.9 u west of a Falcon's middle, 60 s of Use entered nothing)."""
        from brain.bot import Bot
        f = live_bots.vehicle_fwd(s.live, handle)
        out = [Bot.seat_point(dict(kind=k, pos=pos, fwd=f), "driver")]
        fx, fy = (f[0], f[1]) if f and math.hypot(f[0], f[1]) > 0.1 else (1.0, 0.0)
        n = math.hypot(fx, fy)
        fx, fy = fx / n, fy / n
        for ax, ay in ((fx, fy), (-fy, fx), (fy, -fx), (-fx, -fy)):    # front, left, right, back
            out.append(Vec(pos[0] + ax * 1.8, pos[1] + ay * 1.8, pos[2]))
        return out

    def board(s, handle, seconds=60.0):
        """Walk to each door in turn and press Use for seat 0 there (6 s a door) until in. True when in."""
        t0, door, at, best = time.time(), 0, None, None
        pts = None
        while time.time() - t0 < seconds:
            p = s.me()
            v = next((x for x in s.vehicles() if x[0] == handle), None)
            if p is None or v is None:
                time.sleep(0.2)
                continue
            if p["vehicle"] == handle:
                s.act()
                return True
            if p["vehicle"] != -1:                  # in something else: out first
                s.act(buttons=ACTION if int(time.time() * 6) % 2 == 0 else 0)
                time.sleep(1 / HZ)
                continue
            pts = pts or s.doors(handle, v[1], v[2])
            goal = pts[door % len(pts)]
            if at is None and math.dist(p["pos"][:2], (goal.x, goal.y)) < 0.7 or at is not None and time.time() - at < 6.0:
                at = at or time.time()              # tap Use with the seat (shared.h HB_SEAT_SHIFT: seat + 1 << 14)
                s.yaw = math.atan2(v[2][1] - p["pos"][1], v[2][0] - p["pos"][0])
                s.act(buttons=(ACTION | 1 << 14) if int(time.time() * 6) % 2 == 0 else 0)
            else:
                if at is not None:                  # 6 s at this door: the next one
                    door, at, best = door + 1, None, None
                    say(f"   (no way in from door {door}: trying door {door + 1})")
                    continue
                d = math.dist(p["pos"][:2], (goal.x, goal.y))
                if best is None or d < best[0] - 0.3:
                    best = (d, time.time())
                elif time.time() - best[1] > 3.0:   # no headway (the vehicle's body is not in the nav): next door
                    door, best = door + 1, None
                    say(f"   (door {door} not reached: trying door {door + 1})")
                    continue
                w = s.T.nav(Vec(*p["pos"]), goal)
                if (w - Vec(*p["pos"])).flat() < 0.2:
                    w = goal
                s.yaw = math.atan2(w.y - p["pos"][1], w.x - p["pos"][0])
                s.act(forward=1.0)
            time.sleep(1 / HZ)
        s.act()
        return False

    def hold(s, handle, seconds, forward=0.0, pitch=0.0, buttons=0):
        """Hold an input; [(t, x, y, z)] of the vehicle, and whether the bot stayed in."""
        rows, t0 = [], time.time()
        while time.time() - t0 < seconds:
            s.act(forward, pitch, buttons)
            v = next((x for x in s.vehicles() if x[0] == handle), None)
            if v is not None:
                rows.append((time.time() - t0, *v[2]))
            time.sleep(1 / HZ)
        p = s.me()
        return rows, p is not None and p["vehicle"] == handle


def candidates(only):
    basic = [("nothing", 0.0, 0.0, 0, None), ("forward", 1.0, 0.0, 0, None), ("jump", 0.0, 0.0, JUMP, None),
             ("pitch up", 0.0, 0.5, 0, None), ("pitch up + forward", 1.0, 0.5, 0, None),
             ("pitch down", 0.0, -0.5, 0, None), ("pitch down + forward", 1.0, -0.5, 0, None),
             ("jump + forward", 1.0, 0.0, JUMP, None)]
    floats = [(f"+0x{off:02X} = {v:+.0f}.0", 0.0, 0.0, CROUCH, (off, 0x3F800000 if v > 0 else 0xBF800000))
              for off in (0x18, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x3C) for v in (1, -1)]
    bits = [(f"+0x08 bit {b}", 0.0, 0.0, CROUCH, (0x08, 1 << b)) for b in range(64)]
    bits += [(f"+0x40 bit {b}", 0.0, 0.0, CROUCH, (0x40, 1 << b)) for b in range(32) if b not in (1, 21)]
    # FUN_18004d7d0 (ghidra/hr_action_unit.c): the unit control's vertical input is +1 / -1 from the byte at +0x34
    # bits 0 / 1, or the float at +0x3C (with +0x08 bit 20: -1) where FUN_18004d70c(player, 8) holds
    vert = [("+0x34 bit 0", 0.0, 0.0, CROUCH, (0x34, 1)), ("+0x34 bit 1", 0.0, 0.0, CROUCH, (0x34, 2)),
            ("+0x34 bit 0 + forward", 1.0, 0.0, CROUCH, (0x34, 1)), ("+0x3C = +1.0 long", 0.0, 0.0, CROUCH,
            (0x3C, 0x3F800000))]
    sets = {"basic": basic, "floats": floats, "bits": bits, "vert": vert}
    return [c for k in only.split(",") for c in sets[k]] if only else basic + floats + bits


def falcon(P, only, hold_s, rest_s):
    fs = P.vehicles("falcon")
    p = P.me()
    if not fs or p is None:
        say(f"no Falcon ({len(fs)}) or no bot")
        return
    h = min(fs, key=lambda v: math.dist(v[2][:2], p["pos"][:2]))[0]
    if not P.board(h):
        say("could not get into the Falcon in 60 s")
        return
    say(f"in the Falcon's pilot seat {h:#x}")
    P.hold(h, 2.0)
    found = []
    for name, fwd, pitch, btn, entry in candidates(only):
        p = P.me()
        if p is None or p["vehicle"] != h:          # out (a bit got it out, or it died): back in
            say(f"   (out before '{name}': boarding again)")
            if not P.board(h):
                say("could not get back in: stopped")
                break
            P.hold(h, 2.0)
        botctl.set_button_map(P.m, P.base + ([("reach", "crouch", entry[0], entry[1], False)] if entry else []))
        rest, _ = P.hold(h, rest_s)
        rows, inside = P.hold(h, hold_s, fwd, pitch, btn)
        if not rows:
            say(f"{name}: no reads")
            continue
        z0 = rest[-1][3] if rest else rows[0][3]
        up, down = max(r[3] for r in rows) - z0, min(r[3] for r in rows) - z0
        moved = math.dist(rows[0][1:3], rows[-1][1:3])
        tag = "CLIMB" if up > 1.0 else "DESCENT" if down < -1.0 else ""
        say(f"{name:24s} z {z0:7.2f} -> max {up:+6.2f} min {down:+6.2f} end {rows[-1][3] - z0:+6.2f}; across "
            f"{moved:5.2f} u; {'in' if inside else 'OUT'} {tag}")
        if tag:
            found.append((name, tag, up, down))
    botctl.set_button_map(P.m, P.base)
    P.hold(h, 1.0)
    say("climb / descent inputs: " + (", ".join(f"{n} {t} ({u:+.1f} / {d:+.1f} u)" for n, t, u, d in found) or "none"))
    return h


def fly(P, h, native=False):
    """A whole flight on the decoded climb (+0x3C, the unit control's vertical input): up, hover, forward, down. native:
    through botcore s108's own vertical bits (live_bots.buttons of an Action.vertical), not the button table."""
    from brain.core import Action
    up, down, half = 0x3F800000, 0xBF800000, 0x3F000000
    for name, fwd, val, v, secs in (("climb +1.0", 0.0, up, 1.0, 6.0), ("hover 0", 0.0, 0, 0.0, 3.0),
                                    ("forward, +0.5", 1.0, half, 0.5, 4.0), ("forward, 0", 1.0, 0, 0.0, 3.0),
                                    ("descend -1.0", 0.0, down, -1.0, 8.0)):
        if native:
            rows, inside = P.hold(h, secs, fwd, 0.0, live_bots.buttons(Action(vertical=v)))
        else:
            botctl.set_button_map(P.m, P.base + ([("reach", "crouch", 0x3C, val, False)] if val else []))
            rows, inside = P.hold(h, secs, fwd, 0.0, CROUCH if val else 0)
        if not rows:
            say(f"fly {name}: no reads")
            continue
        say(f"fly {'(s108) ' if native else ''}{name:14s} {secs:.0f} s: z {rows[0][3]:6.2f} -> {rows[-1][3]:6.2f} "
            f"({rows[-1][3] - rows[0][3]:+.2f}), across {math.dist(rows[0][1:3], rows[-1][1:3]):5.2f} u; "
            f"{'in' if inside else 'OUT'}")
    botctl.set_button_map(P.m, P.base)


def exits(P):
    """Each kind once: in, 2 s, then Use (s107's pressed bits) until out or 6 s."""
    seen = set()
    p = P.me()
    for h, k, pos in sorted(P.vehicles(), key=lambda v: math.dist(v[2][:2], p["pos"][:2]) if p else 0.0):
        if k in seen or k in ("sabre", "seraph", "shade"):
            continue
        seen.add(k)
        if not P.board(h, 60.0):
            say(f"exit {k}: could not get in")
            continue
        P.hold(h, 2.0)
        t0, out = time.time(), None
        while time.time() - t0 < 6.0:
            P.act(buttons=ACTION)
            p = P.me()
            if p is not None and p["vehicle"] == -1:
                out = time.time() - t0
                break
            time.sleep(1 / HZ)
        P.act()
        say(f"exit {k:9s}: " + (f"out after {out:.2f} s of Use" if out is not None else "stayed in (6 s of Use)"))
        time.sleep(1.0)


def main():
    a = sys.argv[1:]
    only = a[a.index("--only") + 1] if "--only" in a else None
    hold_s = float(a[a.index("--hold") + 1]) if "--hold" in a else 2.5
    rest_s = float(a[a.index("--rest") + 1]) if "--rest" in a else 1.5
    P = Probe()
    say(f"falcon probe {time.strftime('%Y-%m-%d %H:%M')}, bot slot {P.slot} (player {P.index}), hold {hold_s} s, "
        f"rest {rest_s} s")
    try:
        if "falcon" in a or "exits" not in a and "fly" not in a:
            falcon(P, only, hold_s, rest_s)
        if "fly" in a:
            fs = P.vehicles("falcon")
            p = P.me()
            h = p and p["vehicle"] if p and p["vehicle"] in [v[0] for v in fs] else None
            h = h or min(fs, key=lambda v: math.dist(v[2][:2], p["pos"][:2]))[0]
            if P.board(h):
                fly(P, h, native="--native" in a)
            else:
                say("fly: could not get into the Falcon")
        if "exits" in a:
            exits(P)
    finally:
        botctl.set_button_map(P.m, P.base)
        P.act()                                     # never leave the bot pressing (botcore has no watchdog)
    os.makedirs(os.path.join(ROOT, "logs", "verify"), exist_ok=True)
    path = os.path.join(ROOT, "logs", "verify", f"falcon_probe_{time.strftime('%Y%m%d-%H%M%S')}.txt")
    open(path, "w", encoding="utf-8").write("\n".join(OUT) + "\n")
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
