"""Offline check of the Data collector (tools/collector.py) and your numbers (tools/player_stats.py):

- MCC's bindings: a key named by its action wherever one of its buttons has one (fire, jump ...), else by its name;
- key edges only while MCC is in front: alt-tab releases every held key; a controller's buttons the same ("pad A");
- the file: everyone every tick (yours with your crosshair and ride), your guns / equipment only when they change,
  key presses;
- the numbers on a made-up match with known answers: an enemy comes into view at 1.0 s, you aim on him at 1.3 s and
  fire at 1.4 s, he dies at 2.0 s (your kill, 2.0 damage); one ability use of 0.5 s; one gun switch.

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
from collector import Collector, Keys, key_name, read_binds  # noqa: E402
from brain.core import PlayerState, Vec  # noqa: E402
import player_stats  # noqa: E402

LINE = ("CustomKeyboardMouseMappingV2[0]=(GameKeyboardMouseMappings[0]=(AbstractButton=27,VirtualKeyCodes[0]=1,"
        "VirtualKeyCodes[1]=0),GameKeyboardMouseMappings[1]=(AbstractButton=8,VirtualKeyCodes[0]=1,VirtualKeyCodes[1]=0),"
        "GameKeyboardMouseMappings[2]=(AbstractButton=0,VirtualKeyCodes[0]=32,VirtualKeyCodes[1]=0),"
        "GameKeyboardMouseMappings[3]=(AbstractButton=23,VirtualKeyCodes[0]=160,VirtualKeyCodes[1]=0))")


def main():
    fails = []
    b = read_binds(LINE)
    if b != {1: "fire", 32: "jump", 160: "LShift"}:
        fails.append(f"binds {b} (want LMB fire though its first button is unnamed, Space jump, LShift by name)")
    # key edges: pressed while MCC is in front, released when it is not
    held, front, clock = {1}, [True], [0.0]
    k = Keys([1, 32], 1234, lambda: clock[0], state=lambda vk: vk in held, front=lambda: front[0])
    down = {}
    k.poll(down)
    clock[0], front[0] = 0.5, False
    k.poll(down)
    ev = k.take()
    if ev != [(0.0, 1, 1), (0.5, 1, 0)]:
        fails.append(f"key edges {ev} (want fire down at 0, up at 0.5 when MCC lost the front)")
    # a controller's buttons the same way: A and the right trigger held while MCC is in front, released when it is
    # not
    mask, front[0], clock[0] = [1 << 12 | 1 << 17], True, 1.0
    k = Keys([1], 1234, lambda: clock[0], state=lambda vk: False, front=lambda: front[0], pad=lambda: mask[0])
    down = {}
    k.poll(down)
    clock[0], front[0] = 1.5, False
    k.poll(down)
    ev = [(t, key_name(vk), d) for t, vk, d in k.take()]
    if ev != [(1.0, "pad A", 1), (1.0, "pad RT", 1), (1.5, "pad A", 0), (1.5, "pad RT", 0)]:
        fails.append(f"controller edges {ev} (want pad A and pad RT down at 1.0, up at 1.5 when MCC lost the front)")
    # the file and the numbers
    tmp = tempfile.mkdtemp(prefix="halo_collect_")
    path = os.path.join(tmp, "collect_test_20991231-000000.jsonl")
    clock[0], front[0], held = 0.0, True, set()
    keys = Keys([1], 1234, lambda: clock[0], state=lambda vk: vk in held, front=lambda: front[0])
    c = Collector(path, "test", "reach", 1234, lambda: clock[0], keymap={1: "fire"}, keys=keys)
    aim_at = math.atan2(3.0, 10.0)
    for i in range(0, 91):                            # 3 s at 30 a second
        t = i / 30
        clock[0] = t
        if 1.4 <= t < 2.0:
            held = {1}
        else:
            held = set()
        keys.poll(down)
        me = PlayerState(0, 0, "you", Vec(0, 0, 0), yaw=aim_at if t >= 1.3 else 0.0, is_bot=False,
                         weapon="dmr" if t < 2.5 else "magnum", weapons=["dmr", "magnum"], ammo=[60, 36], mag=[15, 12],
                         equipment="sprint", ability_on=0.5 <= t < 1.0)
        life = 2.0 - max(0.0, (t - 1.4) / 0.6 * 2.0) if t >= 1.4 else 2.0
        foe = PlayerState(1, 1, "bot", Vec(10, 3, 0), yaw=math.pi, alive=1.0 <= t < 2.0, shield=max(0.0, life - 1.0),
                          health=min(1.0, max(0.0, life)), is_bot=True)
        c.tick(t, [me, foe], aims={0: ([10.0, 3.0, 0.4, 1 if t >= 1.3 else None], ["warthog", "gun"] if t < 0.5 else None)})
    c.close()
    lines = [json.loads(x) for x in open(path, encoding="utf-8")]
    rows = {r[0]: r for r in next(x for x in lines if "p" in x)["p"]}
    if len(rows[0]) != 15 or rows[0][13:] != [[10.0, 3.0, 0.4, None], ["warthog", "gun"]] or len(rows[1]) != 13:
        fails.append(f"tick rows {rows} (want your crosshair and ride after your 13 columns, the bot's row as before)")
    gear = [x for x in lines if "wpn" in x]
    if len([x for x in lines if "p" in x]) != 91 or len(gear) != 4:
        fails.append(f"file: {len([x for x in lines if 'p' in x])} tick lines (want 91), {len(gear)} gear lines (want 4: "
                     "start, ability on, off, switch)")
    a = player_stats.analyze(path, 0, los=lambda p, q: True, zones=lambda p: "Mid")
    you = a["players"]["0"]
    aim, fire = you["reaction"]["aim"], you["reaction"]["fire"]
    dm, g = you["damage"], you["gear"]
    if not (len(aim) == 1 and abs(aim[0] - 0.3) < 0.04 and len(fire) == 1 and abs(fire[0] - 0.4) < 0.04):
        fails.append(f"reaction aim {aim} fire {fire} (want 0.3 and 0.4)")
    if not (dm["kills"] == 1 and abs(dm["dealt"] - 2.0) < 0.15):
        fails.append(f"damage {dm['dealt']} kills {dm['kills']} (want 2.0 and 1)")
    if not (g["switches"] == 1 and len(g["uses"]) == 1 and abs(g["use_len"][0] - 0.5) < 0.04):
        fails.append(f"gear: switches {g['switches']}, uses {g['uses']} for {g['use_len']} (want 1 switch, one 0.5 s use)")
    if you["keys"]["fire_presses"] != 1 or abs(you["keys"]["hold"]["fire"] - 0.6) > 0.04:
        fails.append(f"keys {you['keys']} (want one fire press held 0.6 s)")
    os.remove(path)
    os.rmdir(tmp)
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("collector OK")


if __name__ == "__main__":
    main()
