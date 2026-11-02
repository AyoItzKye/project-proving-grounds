"""Offline check of the Data collector (tools/collector.py) and your numbers (tools/player_stats.py):

- the file: everyone every tick (yours with your crosshair and ride), your guns / rounds / equipment only when they
  change, and nothing of the keyboard, mouse or controller (no key rows, no key list, no key reading in the module);
- an older (0.1.0) file's key rows and key list are left out of what is shared (without_keys);
- the numbers on a made-up match with known answers: an enemy comes into view at 1.0 s, you aim on him at 1.3 s and
  fire from 1.4 s (the magazine going down: 18 rounds), he dies at 2.0 s (your kill, 2.0 damage); one ability use of
  0.5 s; one gun switch.

usage: python -I test_collector.py      -> "collector OK"
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import collector  # noqa: E402
from collector import Collector  # noqa: E402
from brain.core import PlayerState, Vec  # noqa: E402
import player_stats  # noqa: E402


def main():
    fails = []
    src = open(collector.__file__, encoding="utf-8").read()
    for word in ("GetAsyncKeyState", "XInput", "GetKeyState", "keyboard"):
        if word in src.split('"""', 2)[2]:                    # (the code, not the docstring that says it is not read)
            fails.append(f"collector.py reads input: {word}")
    tmp = tempfile.mkdtemp(prefix="halo_collect_")
    path = os.path.join(tmp, "collect_test_20991231-000000.jsonl")
    clock = [0.0]
    c = Collector(path, "test", "reach", lambda: clock[0])
    aim_at = math.atan2(3.0, 10.0)
    for i in range(0, 91):                            # 3 s at 30 a second
        t = i / 30
        clock[0] = t
        fired = sum(1 for k in range(42, i + 1) if k / 30 < 2.0)   # a round a tick from 1.4 s while he lives
        me = PlayerState(0, 0, "you", Vec(0, 0, 0), yaw=aim_at if t >= 1.3 else 0.0, is_bot=False,
                         weapon="assault_rifle" if t < 2.5 else "magnum", weapons=["assault_rifle", "magnum"],
                         ammo=[96 - fired, 36], mag=[32 - fired, 12], equipment="sprint", ability_on=0.5 <= t < 1.0)
        life = 2.0 - max(0.0, (t - 1.4) / 0.6 * 2.0) if t >= 1.4 else 2.0
        foe = PlayerState(1, 1, "bot", Vec(10, 3, 0), yaw=math.pi, alive=1.0 <= t < 2.0, shield=max(0.0, life - 1.0),
                          health=min(1.0, max(0.0, life)), is_bot=True)
        c.tick(t, [me, foe], aims={0: ([10.0, 3.0, 0.4, 1 if t >= 1.3 else None], ["warthog", "gun"] if t < 0.5 else None)})
    c.close()
    lines = [json.loads(x) for x in open(path, encoding="utf-8")]
    if lines[0] != dict(t=0.0, collect="start", map="test", game="reach") or any("key" in x or "vk" in x for x in lines):
        fails.append(f"key data in the file: start {lines[0]}")
    rows = {r[0]: r for r in next(x for x in lines if "p" in x)["p"]}
    if len(rows[0]) != 15 or rows[0][13:] != [[10.0, 3.0, 0.4, None], ["warthog", "gun"]] or len(rows[1]) != 13:
        fails.append(f"tick rows {rows} (want your crosshair and ride after your 13 columns, the bot's row as before)")
    gear = [x for x in lines if "wpn" in x]
    if len([x for x in lines if "p" in x]) != 91 or len(gear) != 22:
        fails.append(f"file: {len([x for x in lines if 'p' in x])} tick lines (want 91), {len(gear)} gear lines (want 22: "
                     "start, ability on, off, 18 rounds, switch)")
    a = player_stats.analyze(path, 0, los=lambda p, q: True, zones=lambda p: "Mid")
    you = a["players"]["0"]
    aim, fire = you["reaction"]["aim"], you["reaction"]["fire"]
    dm, g = you["damage"], you["gear"]
    if not (len(aim) == 1 and abs(aim[0] - 0.3) < 0.04 and len(fire) == 1 and abs(fire[0] - 0.4) < 0.04):
        fails.append(f"reaction aim {aim} fire {fire} (want 0.3 and 0.4)")
    if not (dm["kills"] == 1 and abs(dm["dealt"] - 2.0) < 0.15):
        fails.append(f"damage {dm['dealt']} kills {dm['kills']} (want 2.0 and 1)")
    if not (g["switches"] == 1 and len(g["uses"]) == 1 and abs(g["use_len"][0] - 0.5) < 0.04 and g["shots"] == 18):
        fails.append(f"gear: switches {g['switches']}, uses {g['uses']} for {g['use_len']}, shots {g['shots']} "
                     "(want 1 switch, one 0.5 s use, 18 shots)")
    if "keys" in you:
        fails.append("a key report in your numbers")
    old = open(path, encoding="utf-8").read().replace('"game": "reach"}', '"game": "reach", "keys": {"1": "fire"}}', 1)
    old += json.dumps(dict(t=1.4, key="fire", vk=1, down=1)) + "\n"
    if collector.without_keys(old) != open(path, encoding="utf-8").read():
        fails.append("an older file's keys went into the shared copy")
    os.remove(path)
    os.rmdir(tmp)
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("collector OK")


if __name__ == "__main__":
    main()
