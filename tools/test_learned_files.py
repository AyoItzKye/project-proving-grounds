"""Learned map files (brain/maps.py read_learned, save_learned): a broken one (two saves run together: live Boardwalk
walls_learned.json Nov 10, Valhalla rides.json Nov 9) is set aside as .bad and read as empty, not the match stopped; a
good one reads; save_learned writes through its own closed temp file (no .tmp left behind, the file whole).

usage: python -I test_learned_files.py      -> "learned files OK"
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import maps as M  # noqa: E402


class T:
    blocked = {(1, 2, 3, 4)}
    stuck = {(0.5, 0.5, 1.0)}
    walls_learned = [[1, 2, 3.0, 3.5, 0]]


def main():
    fails = []
    d = tempfile.mkdtemp()
    try:
        bad = os.path.join(d, "walls_learned.json")
        open(bad, "w").write('[[1, 2, 3.0, 3.5, 0]][[4, 5')
        got = M.read_learned(bad)
        if got != () or not os.path.exists(bad + ".bad") or os.path.exists(bad):
            fails.append(f"a broken file: read {got!r}, set aside {os.path.exists(bad + '.bad')}")
        good = os.path.join(d, "nav_learned.json")
        json.dump([[1.0, 2.0, 3.0]], open(good, "w"))
        if M.read_learned(good) != [[1.0, 2.0, 3.0]]:
            fails.append("a good file: not read")
        if M.read_learned(os.path.join(d, "none.json"), {}) != {}:
            fails.append("a missing file: not the empty value")
        # save_learned into a map folder under d
        old_root = M.ROOT
        M.ROOT = d
        os.makedirs(os.path.join(d, "fake_map"))
        M._TERRAIN["fake_map"] = T
        try:
            M.save_learned({"name": "fake_map"})
        finally:
            M.ROOT = old_root
            M._TERRAIN.pop("fake_map", None)
        left = [f for f in os.listdir(os.path.join(d, "fake_map")) if f.endswith(".tmp")]
        if left:
            fails.append(f"save_learned left temp files: {left}")
        for name in ("los_learned.json", "nav_learned.json", "walls_learned.json"):
            try:
                json.load(open(os.path.join(d, "fake_map", name)))
            except Exception as e:
                fails.append(f"save_learned {name}: {type(e).__name__}")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("learned files OK (a broken file set aside and read empty; saves whole, no temp left)")


if __name__ == "__main__":
    main()
