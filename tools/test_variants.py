"""Map variants filed under their base map, with a nav that grows (the player: "forge world is the general file, but
paradiso is a separate navmesh ... gradually expand the nav mesh as it grows, not generate the whole map then generate
the navmesh again on it"; brain/variants.py, brain/maps.py grow / swap). On a skilled player's Forge World layouts (saved
live scans, logs/looks/forge_objects_20261027_*.json); variant files go to a temp folder:
1. filing: a layout is a variant under its base map; the same layout again is the same one; the layout edited in Forge
   (pieces added) stays the same one; a different layout is another; a stock map's own objects are the base map;
   skybox scenery is no part of a layout; a variant of a regular map (Settlement) keeps the whole map in its window
2. a variant's files: its LiDAR data and learned spots in its own folder, the level from the base map's; the LiDAR view
   accepts its name
3. its nav covers its window only, the same inside as the whole level's build with the same pieces, and builds faster
4. growing: a player near an edge the level goes on past grows the window (built in the background, put in the same
   terrain object, kept for the next match); one inside, or at the level's own edge, does not
5. its own strategy (tools/variant_strategy.py): its mid inside it (not Forge World's at 1, 3, 0), holds on its
   pieces, zones named after its structures inside it, power positions; made once, then not stale
Fails on the code before (no variants: every layout on Forge World in one folder, the whole level built every time).

usage: python -I test_variants.py      -> "variants OK"
"""
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from brain import forge, maps, variants  # noqa: E402
from brain.core import Vec  # noqa: E402
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

LOOKS = os.path.join(HERE, "..", "logs", "looks")


def layout(fn):
    rows = [r for r in json.load(open(os.path.join(LOOKS, fn))) if r["type"] in (6, 10)]
    return [(r["name"].rsplit("\\", 1)[-1], tuple(r["pos"]),
             (tuple(r["fwd"]), forge._cross(r["up"], r["fwd"]), tuple(r["up"]))) for r in rows]


def main():
    testdata.need("logs/looks", why="Forge object recordings from live matches")
    fails = []
    variants.ROOT = tempfile.mkdtemp(prefix="variants_test_")
    base = maps.get_map("reach_forge_halo")
    placed = variants.base_placed(base["objects"])
    shields, build = layout("forge_objects_20261027_all.json"), layout("forge_objects_20261027_buildings.json")
    # 1. filing
    a = variants.identify("reach_forge_halo", shields, placed, game="reach")
    if not a.startswith("reach_forge_halo/variants/v"):
        fails.append(f"the shield layout filed as {a}")
    if variants.identify("reach_forge_halo", shields, placed) != a:
        fails.append("the same layout again is another variant")
    grown_layout = shields + [(n, (p[0] + 0.0, p[1], p[2]), ax) for n, p, ax in build[:20]]
    if variants.identify("reach_forge_halo", grown_layout, placed) != a:
        fails.append("the layout with 20 pieces added is another variant (it was edited in Forge)")
    moved = [(n, (p[0] + 150.0, p[1] - 150.0, p[2]), ax) for n, p, ax in shields]
    b = variants.identify("reach_forge_halo", moved, placed)
    if b == a or not b.startswith("reach_forge_halo/variants/v"):
        fails.append(f"a different layout is {b} (the first: {a})")
    sett = maps.get_map("reach_30_settlement")["objects"]
    stock = [(it["name"], tuple(it["pos"]), ((1, 0, 0), (0, 1, 0), (0, 0, 1))) for it in sett["placed"]]
    if variants.identify("reach_30_settlement", stock, variants.base_placed(sett)) != "reach_30_settlement":
        fails.append("Settlement's own objects filed as a variant")
    if any(n.startswith("sky") for n, _ in variants.own([(n, p) for n, p, _ in build], placed)):
        fails.append("skybox scenery counted in a layout")
    # a few pieces added to a regular map: the window still takes in the whole of its own layout
    extra = stock + [("ff_plat_2x2", (p[0] + 0.3, p[1] + 0.7, p[2] + 3.0), ax) for _, p, ax in stock[:5]]
    s = variants.identify("reach_30_settlement", extra, variants.base_placed(sett), area=variants.base_area(sett))
    sw, area = variants.info(s)["window"], variants.base_area(sett)
    if not all(sw[0] <= x <= sw[2] and sw[1] <= y <= sw[3] for x, y, _ in area):
        fails.append(f"Settlement with 5 pieces added: window {sw} leaves out part of the map's own layout")
    # 2. files
    v = variants.identify("reach_forge_halo", build, placed, game="reach")
    m = maps.get_map(v)
    if m["heightmap"] != base["heightmap"] or m["base"] != "reach_forge_halo" or not m.get("variant", {}).get("pieces"):
        fails.append(f"variant map: level {m['heightmap']}, base {m.get('base')}, pieces kept "
                     f"{len(m.get('variant', {}).get('pieces', []))}")
    want = os.path.normpath(os.path.join(maps.ROOT, "reach_forge_halo", "variants", v.rsplit("/", 1)[-1], "lidar.json"))
    import lidar
    rec = lidar.Recorder(v, count_run=False)
    if os.path.normpath(rec.path) != want or not lidar.map_ok(v) or "Forge layout" not in lidar.map_title(v):
        fails.append(f"LiDAR: data at {rec.path} (want {want}), view accepts it {lidar.map_ok(v)}, "
                     f"title {lidar.map_title(v)!r}")
    # 3. its window's nav: the whole level's inside it, sooner
    t = time.time()
    T = maps.terrain(m)
    tw = time.time() - t
    full = dict(base)
    full["live_blocks"], full["shields"] = forge.nav_pieces(build)
    t = time.time()
    F = maps._build(full, None)
    tf = time.time() - t
    if not (T.w * T.h < 0.5 * F.w * F.h and tw < tf):
        fails.append(f"window {T.w} x {T.h} cells in {tw:.1f} s, the whole level {F.w} x {F.h} in {tf:.1f} s")
    x0, y0, x1, y1 = T.window
    same = tot = 0
    for x in np.arange(x0 + 10, x1 - 10, 2.0):
        for y in np.arange(y0 + 10, y1 - 10, 2.0):
            a_, b_ = T._cell(Vec(x, y, 0)), F._cell(Vec(x, y, 0))
            za = sorted(round(float(z), 3) for z, w in zip(T.lz[:, a_[0], a_[1]], T.lwalk[:, a_[0], a_[1]]) if w)
            zb = sorted(round(float(z), 3) for z, w in zip(F.lz[:, b_[0], b_[1]], F.lwalk[:, b_[0], b_[1]]) if w)
            same, tot = same + (za == zb), tot + 1
    if same != tot:
        fails.append(f"walkable floors in the window: {same} of {tot} cells as the whole level's")
    # 4. growing
    if maps.grow(m, [Vec((x0 + x1) / 2, (y0 + y1) / 2, 2.2)]) is not None:
        fails.append("a player in the middle grew the window")
    far = (T.full[0] + 2.0, (y0 + y1) / 2, 2.2)
    if variants.grown((T.full[0], y0, x1, y1), far, T.full) is not None:
        fails.append("a player at the level's own west edge grew the window past it")
    ident, before = id(T), tuple(m["window"])
    w = maps.grow(m, [Vec(x1 - 4.0, (y0 + y1) / 2, 2.2)])
    while m["grow"].get("job") is not None:
        time.sleep(0.1)
    swapped = maps.swap(m)
    T2 = maps.terrain(m)
    if not (w and swapped and id(T2) == ident and m["window"][2] > before[2] and T2.window[2] > x1
            and tuple(variants.info(v)["window"]) == tuple(m["window"])):
        fails.append(f"growing east: to {w}, swapped {swapped}, same terrain {id(T2) == ident}, window {before} -> "
                     f"{m['window']}, saved {variants.info(v)['window']}")
    # 5. its own strategy (tools/variant_strategy.py): zones, mid and holds of its own layout, not Forge World's canvas
    # (on the layout the player played on, its pieces copied into the temp folder; the catalog row of pieces above
    # floats where no player goes)
    import variant_strategy
    played = json.load(open(os.path.join(maps.ROOT, "reach_forge_halo", "variants", "v2ba2727c", "variant.json")))
    v = variants.identify("reach_forge_halo", variants.pieces_of(played), placed, game="reach")
    if not variant_strategy.stale(v):
        fails.append("a new variant's strategy files count as made")
    took = variant_strategy.build(v)
    maps._MAPS.pop(v, None)
    maps._TERRAIN.pop(v, None)
    sm = maps.get_map(v)
    ST = maps.terrain(sm)
    canvas = maps.get_map("reach_forge_halo")["points"]["mid"]
    holds_on = [bool(ST.piece[ST._node(h)]) for h in sm["holds"][0]]
    if (variant_strategy.stale(v) or not ST.inside(sm["points"]["mid"].x, sm["points"]["mid"].y)
            or (sm["points"]["mid"] - canvas).flat() < 1.0 or not any(holds_on) or not sm["positions"]
            or not all(ST.inside(z.center.x, z.center.y) for z in sm["zones"].zones)
            or not any(not z.area for z in sm["zones"].zones)):
        fails.append(f"strategy ({took:.0f} s): mid {sm['points']['mid']} (canvas {canvas}), holds on pieces {holds_on}, "
                     f"{len(sm['positions'])} positions, zones {[z.name for z in sm['zones'].zones]}")
    # 6. a built-in map's variant (Invasion: Spire's layout) builds on the base map's navmesh data, its own on top; a Forge
    #    canvas's variant keeps its own (live: Spire's variant had no LiDAR jumps or approved ramps: no core pickup)
    spire = maps.load_map("reach_35_island")
    names = maps.data_names(dict(spire, name="reach_35_island/variants/vtest"))
    fw = maps.data_names(dict(maps.load_map("reach_forge_halo"), name="reach_forge_halo/variants/vtest"))
    if names != ["reach_35_island", "reach_35_island/variants/vtest"] or fw != ["reach_forge_halo/variants/vtest"]:
        fails.append(f"navmesh data of variants: Spire's {names}, Forge World's {fw}")
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print(f"variants OK (window {T.w} x {T.h} cells in {tw:.1f} s; the whole level {F.w} x {F.h} in {tf:.1f} s; "
          f"strategy in {took:.0f} s: {len(sm['zones'].zones)} zones, holds on pieces {sum(holds_on)} of {len(holds_on)})")


if __name__ == "__main__":
    main()
