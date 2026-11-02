"""Find which bytes of a game's player configuration hold which armor piece or colour (brain/looks.py needs the
layout): in a running match with no other bots (logs/test_override.json: no roster, red 0, blue 0, brain none),
add one bot per byte to test, each a copy of the player's look with that one byte stepped by one (its name says
which: "B58+1"), walk them into two rows in front of the player's player, facing it, and save a screenshot.
Nothing shoots; the player's player stays idle. Reach, Halo 3, ODST, Halo 4, H2A (--game).

usage: python -I look_probe.py <first byte hex> <last byte hex> [--game G] [--label NAME] [--step N] [--spec FILE]
                               [--team T]
       e.g. look_probe.py 48 56   (config +0x48 .. +0x56: up to 15 bots); --team: every bot on team T (same colours)
Bytes go to botcore as (offset, {0..63: value}) (botctl.add_bot): before every byte from +0x40 on was
dropped there (the offset was always 0), so the earlier Reach byte probes of +0x48.. tested nothing.
"""
import math
import os

import struct

import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import botctl  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from look_dump import live_for, map_folder, person_config  # noqa: E402

SKIP = {"reach": range(0x64, 0x6C), "h3": range(0x56, 0x5E)}   # the service tag (its own probe: text)


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def packed(vals):
    """{config byte: value} -> (offset, {0..63: value}) as botctl.add_bot sends a look."""
    off = min(vals)
    if max(vals) - off >= 64:
        sys.exit(f"bytes {sorted(vals)} span 64 or more: one look holds 64")
    return off, {b - off: v for b, v in vals.items()}


def main():
    first, last = int(sys.argv[1], 16), int(sys.argv[2], 16)
    step = int(sys.argv[sys.argv.index("--step") + 1]) if "--step" in sys.argv else 1
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else f"{first:02x}_{last:02x}"
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "reach"
    m = botctl.shm()
    live = live_for(game)
    players = live.players()
    me = players[0]
    person = person_config(game, live)                      # the configuration every bot starts from (player 0's)
    machine = 1 + max(p["index"] for p in players)
    tested = [b for b in range(first, last + 1) if b not in SKIP.get(game, ())][:15]
    bots = [(f"B{b:02X}+{step} {(person[b] + step) & 0xFF}"[:15], {b: (person[b] + step) & 0xFF}) for b in tested]
    if "--spec" in sys.argv:          # [[name, {"0x58": "+3" | 7...}]...]: any bytes per bot ("+n": the player's + n)
        import json
        bots = [(name[:15], ("roll", *spec["roll"]) if "roll" in spec else
                 {int(k, 16): ((person[int(k, 16)] + int(v)) & 0xFF if isinstance(v, str) else v) for k, v in spec.items()})
                for name, spec in json.load(open(sys.argv[sys.argv.index("--spec") + 1]))][:15]   # roll: [seed, slots]
        tested = list(range(len(bots)))
    room = max(0, botctl.player_cap(game) - len(players)) if "--no-add" not in sys.argv else len(bots)
    if len(bots) > room:                              # ODST holds 4 players: more crashed it (botctl.player_cap)
        print(f"{game}: {room} bots at most here, {len(bots) - room} left out")
        bots, tested = bots[:room], tested[:room]
    team = int(sys.argv[sys.argv.index("--team") + 1]) if "--team" in sys.argv else None   # one colour for all: shapes
    for k, (name, vals) in enumerate(bots if "--no-add" not in sys.argv else ()):   # --no-add: those there
        look = vals if isinstance(vals, tuple) else packed(vals) if vals else None
        r = botctl.add_bot(m, machine, team if team is not None else 1 + k % 7, name, game, look=look)
        print(name, "added" if r.get("result", -1) & 0xFFFFFFFF != 0xFFFFFFFF else r, flush=True)
        machine += 1
        time.sleep(0.2)
    time.sleep(3.0)                                   # let them spawn
    try:
        T = terrain(get_map(map_folder(game, live)))
    except (OSError, KeyError):                       # a Forge map with no data here (the player's Bot Lineup maps,
        T = None                                      # a flat floor in front of him): walk straight
    look = Vec(*me["aim"]) if me.get("aim") else Vec(1, 0, 0)
    yaw0 = math.atan2(look.y, look.x)
    origin = Vec(*me["pos"])
    fwd, side = Vec(math.cos(yaw0), math.sin(yaw0), 0), Vec(-math.sin(yaw0), math.cos(yaw0), 0)
    spots = []
    for k in range(len(tested)):
        per = int(arg("--row", 8))                  # bots a row, their spacing and the first row's distance (units,
        row, col = divmod(k, per)                   # about 3 m): wider spacing keeps one name tag a bot
        p = origin + fwd * (arg("--dist", 1.8) + 1.2 * row) + side * ((col - (per - 1) / 2) * arg("--spacing", 0.75))
        p = Vec(p.x, p.y, T.nav_z(p.x, p.y) if T and T.walkable(p) else origin.z)
        spots.append(p)
    t0 = time.time()
    while time.time() - t0 < 120:
        st = botctl.status(m)["bots"]                 # slot -> player index
        now = {p["index"]: p for p in live.players()}
        done = 0
        for slot, index in st.items():
            p = now.get(index)
            k = slot                                     # added in order: slot k is tested[k]
            if not p or not p.get("pos") or k >= len(spots):
                continue
            pos = Vec(*p["pos"])
            goal = spots[k]
            if (pos - goal).flat() < 0.35:
                face = math.atan2(origin.y - pos.y, origin.x - pos.x)
                botctl.act(m, slot, 0.0, 0.0, face, 0.0)
                done += 1
                continue
            w = T.nav(pos, goal) if T else goal
            w = Vec(w.x, w.y, w.z)
            yaw = math.atan2(w.y - pos.y, w.x - pos.x)
            botctl.act(m, slot, 1.0 if (pos - goal).flat() > 1.0 else 0.4, 0.0, yaw, 0.0)
        if done >= len(tested):
            break
        time.sleep(1 / 30)
    time.sleep(1.0)
    import mcc_nav
    out = os.path.join(ROOT, "logs", "looks")
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, f"{game}_{label}.png")
    mcc_nav.grab().save(dst)                          # MCC's window, full size: armor pieces need it
    print("in place:", done, "of", len(tested), "->", dst)
    print("person's bytes:", " ".join(f"{b:02X}={person[b]:02x}" for b in tested))


if __name__ == "__main__":
    main()
