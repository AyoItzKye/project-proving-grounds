"""Rebuild maps/reach_*/objects.json from the scenario XML already exported (tools/reach_export.py scenario_objects),
without the heavy steps (mesh, heightmap, callouts): for changes to what is read from the scenario, such as the
objectives' boundary shapes. Prints each map's counts before and after; a map whose counts change other than by the
new fields is reported.

usage: python -I refresh_objects.py [reach_map ...] [--force]   (default: every reach_* map; --force keeps changed counts)
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reach_export as rx  # noqa: E402

ROOT = os.path.join(HERE, "..", "maps")


def counts(path):
    o = json.load(open(path, encoding="utf-8"))
    return {k: len(v) for k, v in o.items() if isinstance(v, list)}


def main(names):
    import numpy as np
    names = names or sorted(os.path.basename(os.path.dirname(os.path.dirname(p)))
                            for p in glob.glob(os.path.join(ROOT, "reach_*", "source", "scenario.xml")))
    bad = []
    for name in names:
        d = os.path.join(ROOT, name)
        xml, objs, hm = (os.path.join(d, f) for f in ("source/scenario.xml", "objects.json", "heightmap.npz"))
        if not os.path.exists(xml) or not os.path.exists(objs):
            continue
        before = counts(objs)
        rx.FLOORS = None
        if os.path.exists(hm):
            h = np.load(hm)
            rx.FLOORS = (h["floors"], float(h["x0"]), float(h["y0"]), float(h["cell"]))
        tmp = objs + ".new"
        rx.scenario_objects(xml, tmp)
        after = counts(tmp)
        zones = sum(1 for f in json.load(open(tmp, encoding="utf-8"))["netgame_flags"] if "boundary" in f)
        if after != before and "--force" not in sys.argv:
            bad.append(name)
            print(f"{name}: counts changed {before} -> {after}: kept the old file", flush=True)
            os.remove(tmp)
            continue
        os.replace(tmp, objs)
        print(f"{name}: {zones} objective zones with a boundary", flush=True)
    if bad:
        sys.exit(f"changed: {bad}")


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if a != "--force"])
