"""Offline checks for the three kinds of wall (tools/lidar_walls.py, maps/<map>/wall_kinds.json): solid walls stop
walking, sight and shots; windows (glass) stop walking and shots but not sight; fences (grates, railings) stop walking
only. On Halo 3 Construct's own collision data:

1. the shader names sort as the kits name them (Construct's glass_activation a window, panel_poop_railing a fence,
   panel_catwalk solid; Reach glass_light_vertical_a a light, not a pane; CE's sgla tag group glass);
2. a line across the Mid / Red side glass (5.25, 2.25, 11.5) -> (5.25, 6.25, 11.5): Terrain.los (solid) blocked, sees clear,
   shot_los blocked; across the Mid railing (8.75, -9.7, 4.8) -> (8.75, -7.3, 5.45): sees and shot_los clear; spawn to
   spawn (red base to blue base) all three blocked;
3. the decision: a Legendary bot facing a man behind that glass (the trace pair, h3_construct t 5.4 s: bot 1 at Mid
   (7.39, 2.57, 10.77), enemy 7 on Blue side) recognises him with sight (sees) and never fires (shot_los: the glass
   stops rounds); with the old every-wall-solid sight it never saw him. Behind the railing it fires;
4. LiDAR paints the glass and the railing as their own kinds (KIND_WINDOW / KIND_FENCE), not cover walls;
5. the CE / Halo 2 export (tabs, values as text) parses: surfaces, edges, vertices and the shader's tag group;
6. a man aiming straight at a bot lands three bursts through a wall the data calls solid: that spot is learned as a
   fence (Terrain.learn_shot_through: sight and shots pass, walking does not);
7. Forge pieces: a Halo 4 Bonanza railing is a fence, Reach Forge World's window walls bring windows.

usage: python -I test_wall_kinds.py      -> "wall kinds OK"
"""
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import lidar  # noqa: E402
import lidar_walls as W  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

GLASS = (Vec(5.25, 2.25, 11.5), Vec(5.25, 6.25, 11.5))
RAIL = (Vec(8.75, -9.7, 4.8), Vec(8.75, -7.3, 5.45))
BASES = (Vec(4.26, 6.71, 8.72), Vec(-0.02, -20.28, 10.62))
TRACE = (Vec(7.39, 2.57, 10.77), Vec(-0.47, -11.53, 11.82))


def fight(T, me_pos, foe_pos, los, secs=1.5):
    """A Legendary bot standing at me_pos facing a still man at foe_pos: (recognised him, fire ticks, notes)."""
    bot = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), get_map("h3_construct"), random.Random(1))
    yaw = math.atan2(foe_pos.y - me_pos.y, foe_pos.x - me_pos.x)
    pitch, fired, notes, t = 0.0, 0, set(), 0.0
    while t < secs:
        me = PlayerState(1, 0, "bot", me_pos, yaw=yaw, pitch=pitch, alive=True)
        foe = PlayerState(2, 1, "human", foe_pos, alive=True)
        a = bot.think(t, 1 / 30, Snapshot(t, [me, foe], mode="slayer"), los, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        fired += bool(a.fire)
        notes |= set(getattr(bot, "notes", []) or [])
        t += 1 / 30
    return 2 in bot.per.recognized or 2 in bot.per.beliefs, fired, notes


def main():
    fails = []
    # 1. names
    want = {"glass_activation": "window", "panel_glass2": "window", "panel_poop_railing": "fence", "panel_catwalk": None,
            "guardian_railings_a": "fence", "glass_light_vertical_a": None, "guardian_centerplatform_metalunderglass": None,
            "m30_grate": "fence", "chillout alpha grate": "fence", "metal_flat": None}
    got = {k: W.kind_of(k) for k in want}
    if got != want:
        fails.append(f"shader kinds {got}, want {want}")
    # 2. the lines
    m = get_map("h3_construct")
    T = terrain(m)
    if not getattr(T, "wall_kinds", None) or not T.wall_kinds.get("window"):
        fails.append(f"Construct's wall_kinds.json not loaded into its terrain ({getattr(T, 'wall_kinds', None)})")
    for name, (a, b), want in (("glass", GLASS, (False, True, False)), ("railing", RAIL, (False, True, True)),
                               ("bases", BASES, (False, False, False))):
        got = (T.los(a, b), T.sees(a, b), T.shot_los(a, b))
        if got != want:
            fails.append(f"{name}: (los, sees, shot_los) {got}, want {want}")
    # 3. the decision
    seen, fired, notes = fight(T, *TRACE, T.sees)
    if not seen or fired:
        fails.append(f"behind glass with sight: recognised {seen}, fired {fired} ticks (want seen, no shot)")
    if "seen through glass: go round" not in notes:
        fails.append(f"behind glass: the bot does not go round (notes {sorted(notes)})")
    seen_old, fired_old, _ = fight(T, *TRACE, T.los)
    if seen_old:
        fails.append("behind glass with the old all-solid sight: recognised (the case this changes: want unseen)")
    seen, fired, _ = fight(T, *RAIL, T.sees)
    if not seen or not fired:
        fails.append(f"behind the railing: recognised {seen}, fired {fired} ticks (want both)")
    seen, fired, _ = fight(T, *BASES, T.sees)
    if fired:
        fails.append(f"through the solid level base to base: fired {fired} ticks")
    # 4. LiDAR kinds
    rec = lidar.Recorder("h3_construct", count_run=False, path=os.path.join(tempfile.mkdtemp(), "lidar.json"))
    def kind_on(a, b):        # what LiDAR paints where the line crosses the face (floor height: the lower end's)
        for k in range(1, 20):
            u = k / 20
            got = rec.see_through(a.x + (b.x - a.x) * u, a.y + (b.y - a.y) * u, min(a.z, b.z))
            if got is not None:
                return got
        return None
    kinds = [kind_on(*GLASS), kind_on(*RAIL)]
    if kinds != [lidar.KIND_WINDOW, lidar.KIND_FENCE]:
        fails.append(f"LiDAR kinds at the glass / railing {kinds}, want {[lidar.KIND_WINDOW, lidar.KIND_FENCE]}")
    # 5. the tab export
    xml = os.path.join(tempfile.mkdtemp(), "ce.xml")
    sv = '\t\t\t\t\t<field name="{}" type="real point 3d">{}</field>\n'
    with open(xml, "w") as f:
        f.write('<?xml version="1.0"?>\n<tag group="scenario_structure_bsp" id="x" version="5">\n'
                '\t<block name="collision materials">\n\t\t<element index="0">\n'
                '\t\t\t<tag_reference name="shader" type="sgla">levels\\test\\x\\shaders\\x glass</tag_reference>\n'
                '\t\t</element>\n\t</block>\n\t<block name="collision bsp">\n\t\t<element index="0">\n'
                '\t\t\t<block name="surfaces">\n\t\t\t\t<element index="0">\n'
                '\t\t\t\t\t<field name="first edge" type="long integer">0</field>\n'
                '\t\t\t\t\t<field name="flags" type="byte flags">\n\t\t\t\t\t\t8\n\t\t\t\t\t</field>\n'
                '\t\t\t\t\t<field name="material" type="short integer">0</field>\n\t\t\t\t</element>\n\t\t\t</block>\n'
                '\t\t\t<block name="edges">\n'
                + "".join('\t\t\t\t<element index="%d">\n' % k + "".join(
                    '\t\t\t\t\t<field name="%s" type="long integer">%d</field>\n' % (n, v) for n, v in
                    (("start vertex", k), ("end vertex", (k + 1) % 3), ("forward edge", (k + 1) % 3),
                     ("reverse edge", -1), ("left surface", 0))) + '\t\t\t\t</element>\n' for k in range(3))
                + '\t\t\t</block>\n\t\t\t<block name="vertices">\n'
                + "".join('\t\t\t\t<element index="%d">\n' % k + sv.format("point", p) + '\t\t\t\t</element>\n'
                          for k, p in enumerate(("0,0,0", "1,0,0", "0,0,1")))
                + '\t\t\t</block>\n\t\t</element>\n\t</block>\n</tag>\n')
    r = W.classify(xml)
    if not r["window"] or r["counts"]["window"] != 1 or not all(c[4] for c in r["window"]):
        fails.append(f"CE export: {r['counts']}, {len(r['window'])} window cells (want 1 upright breaking glass face)")
    # 7. Forge pieces: Halo 4 Bonanza's railing (fw_unsc_c_railing_2 at (-18.87, 125.87, 3.65), a variant's piece in
    #    no palette: object_shapes.py had no shape for it, so no wall at all) walls the walk and lets sight and shots
    #    through; Reach Forge World's window wall (ff_wall_2x2_window) brings its energy panes as windows
    FT = terrain(get_map("h4_ca_forge_bonanza/variants/v37a78dad"))
    fa, fb = Vec(-19.72, 125.02, 3.65), Vec(-18.02, 126.71, 3.65)
    if (FT.los(fa, fb), FT.sees(fa, fb), FT.shot_los(fa, fb)) != (False, True, True):
        fails.append(f"7. Bonanza railing: (los, sees, shot_los) {(FT.los(fa, fb), FT.sees(fa, fb), FT.shot_los(fa, fb))}, "
                     "want (False, True, True)")
    RT = terrain(get_map("reach_forge_halo/variants/v07243a32"))
    if not getattr(RT, "wall_kinds", {}).get("window"):
        fails.append(f"7. Forge World window walls: no window cells ({getattr(RT, 'wall_kinds', None)})")
    # 6. learning (last: it changes the shared terrain): a man aiming straight at the bot lands battle rifle rounds
    #    through a wall the data calls solid (Construct's red side, 6 u east of (-2, 7.7, 6.4)), three bursts: the spot
    #    becomes a fence (sight and shots pass), the walking map keeps it
    a, b = Vec(-2.0, 7.7, 6.4), Vec(4.0, 7.7, 6.4)
    if (T.los(b, a), T.sees(b, a), T.shot_los(b, a)) != (False, False, False):
        fails.append("6. the learning line is not solid to start with")
    bot = Bot(1, 0, make_profile("top", "rusher", random.Random(2)), m, random.Random(2))
    t, hp, learned = 0.0, 2.0, []
    while t < 4.0:
        if any(abs(t - h) < 0.5 / 30 for h in (0.2, 1.6, 3.0)):
            hp -= 0.2                                  # a hit, a burst 1.4 s apart
        me = PlayerState(1, 0, "bot", a, yaw=math.pi, alive=True, shield=max(0.0, hp - 1.0), health=min(1.0, hp))
        foe = PlayerState(2, 1, "human", b, yaw=math.pi, alive=True,
                          weapon="battle_rifle")
        bot.think(t, 1 / 30, Snapshot(t, [me, foe], mode="slayer"), T.sees, lambda p, q, **k: q, [])
        t += 1 / 30
    learned = list(getattr(T, "walls_learned", []))
    if not learned or not T.shot_los(b, a) or not T.sees(b, a) or T.los(b, a):
        fails.append(f"6. three hits through the wall: learned {len(learned)} cells, (los, sees, shot_los) "
                     f"{(T.los(b, a), T.sees(b, a), T.shot_los(b, a))} (want cells, (False, True, True))")
    if fails:
        print("FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("wall kinds OK")


if __name__ == "__main__":
    main()
