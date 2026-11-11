"""The LiDAR simulator's "Every map" (tools/lidar_sim.py Control, action "all"):

1. with no game, every map with level data in turn, each Forge layout (maps/<map>/variants/<id>) right after its map
2. with a game ("reach"), only that game's maps, layouts included
3. an unknown game is refused (400) and leaves the queue as it was

usage: python -I test_lidar_mass.py      -> "lidar mass OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jumpphys as J  # noqa: E402
import lidar  # noqa: E402
import lidar_sim  # noqa: E402


def main():
    fails = []
    names = lidar.map_list_names()
    layouts = [m for m in names if "/variants/" in m]
    ctl = lidar_sim.Control(names)
    code, _ = ctl.command({"action": "all"})
    if code != 200 or ctl.queue != names:
        fails.append(f"1. every map: {code}, {len(ctl.queue)} queued of {len(names)}")
    if layouts and not set(layouts) <= set(ctl.queue):
        fails.append("1. the Forge layouts are left out of every map")
    for m in layouts:
        base = m.partition("/")[0]
        if base in ctl.queue and m in ctl.queue and ctl.queue.index(m) < ctl.queue.index(base):
            fails.append(f"1. {m} runs before its map")
    ctl = lidar_sim.Control(names)
    code, _ = ctl.command({"action": "all", "game": "reach"})
    want = [m for m in names if J.game_of(m.partition("/")[0]) == "reach"]
    if code != 200 or ctl.queue != want or not any("/variants/" in m for m in ctl.queue):
        fails.append(f"2. Reach: {code}, {len(ctl.queue)} queued, want {len(want)} with its layouts")
    before = list(ctl.queue)
    code, ans = ctl.command({"action": "all", "game": "halo5"})
    if code != 400 or ctl.queue != before:
        fails.append(f"3. an unknown game: {code} {ans}, queue changed {ctl.queue != before}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"lidar mass OK ({len(names)} maps and layouts, {len(want)} Reach with its {sum('/variants/' in m for m in want)} "
          "layouts)")


if __name__ == "__main__":
    main()
