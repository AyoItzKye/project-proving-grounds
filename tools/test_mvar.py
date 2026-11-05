"""Map variant files read directly (brain/mvar.py): a Forge map's labels, Invasion phases and kill boundaries from its
.mvar, a custom game type's phase objectives from its .bin (GitHub issue #2: Invasion on a Forge Tempest; the game's
memory gives no object's label, so the bots played it as Slayer).
1. the issue #2 player's Tempest Invasion (his .mvar and .bin, in the bug reports folder beside this project; skipped
   when absent): parses (every palette folder's count matches), Invasion objects and his inv_res_zone hills present
   by team and phase, two soft kill boundaries in the shared kill-zone schema, the game variant's options read
   (Attacking Team Spartans; phases Assault, Territories, CTF)
2. its Invasion setup from the file: phase 1 a bomb plant (Assault) with the bomb at its inv_obj_flag, phase 2 two
   territories, phase 3 the core run to the delivery point by the Pelican, the attackers team 0 (his option says
   Spartans), respawn zones from inv_res_zone (he uses no inv_res_p1..p3), the Pelican no wall
3. MCC's own Reach map variants on this PC (skipped when MCC is not found): every one parses; Bungie's Boneyard,
   Breakpoint and Spire files give the same Invasion setup as their scenarios (spawn sequence = phase)
4. the live match's file: picked by the pieces standing (the right one of several), filed under the variant
   (mvar_objects.json, killzones.json, variant.json "mvar"), and brain/maps.py load_map / tools/lidar.py
   objective_points use its objectives (every mode's labels: hills, flags, territories, Invasion zones ...)
5. Halo 3 map variants (its own format, no labels: objectives are objects): every one on this PC parses, its
   objectives name every mode (flag, hill, ball, territory, bomb ...), positions match the scenario (MLG Construct)
Fails on the code before (no reader: no labels, no phases, no Forge boundaries).

usage: python -I test_mvar.py      -> "mvar OK"
"""
import glob
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from brain import maps, mvar, paths, variants  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.invasion import layout  # noqa: E402

ISSUE2 = os.path.join(ROOT, "..", "Match recordings and bug reports", "issue2_tempest_map", "Maps Invasion tempest")


def near(v, xyz, tol=0.5):
    return v is not None and (v - Vec(*xyz)).flat() <= tol


def tempest(fails):
    mv, gb = (glob.glob(os.path.join(ISSUE2, p)) for p in ("*.mvar", "*.bin"))
    if not mv or not gb:
        print("  (issue #2 files not here: part 1-2 skipped)")
        return None
    v = mvar.read(mv[0])
    if not v["ok"] or v["map"] != "reach_dlc_medium" or v["title"] != "Tempest Invasion" or len(v["objects"]) != 212:
        fails.append(f"Tempest file: ok {v['ok']}, map {v['map']}, title {v['title']!r}, {len(v['objects'])} objects")
    if any(o["name"] is None for o in v["objects"]):
        fails.append("Tempest file: objects the palette does not name")
    zones = {}
    for o in v["objects"]:
        if o["label"] == "inv_res_zone":
            zones.setdefault((o["team"], o["spawn_sequence"]), []).append(o)
    want = {(1, 1): 2, (0, 1): 2, (1, 2): 3, (0, 2): 2, (1, 3): 1}
    if {k: len(z) for k, z in zones.items()} != want or any(o["name"] != "mp_hill_beacon" for z in zones.values()
                                                                for o in z):
        fails.append(f"inv_res_zone hills by (team, phase): {({k: len(z) for k, z in zones.items()})}, want {want}")
    labels = {o["label"] for o in v["objects"]}
    for lb in ("inv_objective", "inv_obj_flag", "inv_gates", "inv_platform", "inv_vehicle"):
        if lb not in labels:
            fails.append(f"Tempest file: no {lb}")
    kz = mvar.killzones(v)["volumes"]
    if [(k["kind"], k["shape"]) for k in kz] != [("soft", "box")] * 2 or kz[1]["forge_label"] != "inv_slayer" \
            or not kz[1]["gametype_specific"] or abs(kz[1]["size"][0] - 24.98) > 0.05:
        fails.append(f"Tempest kill boundaries: {kz}")
    g = mvar.read_game_variant(gb[0])
    opts = {o["name"]: o["value"] for o in g["options"]}
    if not g["ok"] or g["icon"] != 9 or opts.get("Attacking Team") != "Spartans":
        fails.append(f"Tempest game variant: ok {g['ok']}, icon {g['icon']}, options {opts}")
    styles = mvar.phase_styles(g)
    if styles != {1: "assault", 2: "territories", 3: "ctf"}:
        fails.append(f"phase styles {styles}")
    inv = layout(mvar.scenario_objects(v), styles=styles)
    if inv is None:
        fails.append("Tempest: no Invasion setup from the file")
        return v
    ph = inv["phases"]
    if (inv["attackers"] != 0 or len(ph[1]) != 1 or not near(ph[1][0], (-0.9, 0.25, 4.93))
            or sorted(round(p.y) for p in ph[2]) != [-27, 29] or not near(ph[3][0], (-28.38, 23.95, 1.66))
            or not near(inv["core"], (18.85, 23.57, 0.43)) or not near(inv["bomb"], (-18.67, 7.58, 1.33))
            or inv["bomb_phase"] != 1):
        fails.append(f"Tempest setup: attackers {inv['attackers']}, phases {ph}, core {inv['core']}, bomb "
                     f"{inv['bomb']} (phase {inv['bomb_phase']})")
    if sorted((t, p, len(z)) for t, r in inv["res"].items() for p, z in r.items()) != \
            sorted((t, p, n) for (t, p), n in want.items()):
        fails.append(f"respawn zones {inv['res']}")
    if any(b["name"] == "pelican" for b in inv["barriers"]) or not any(b["kind"] == "one_way" for b in inv["barriers"]):
        fails.append(f"barriers {[(b['name'], b['kind']) for b in inv['barriers']]}")
    if layout(mvar.scenario_objects(v)) is None or layout(mvar.scenario_objects(v))["bomb"] is not None:
        fails.append("without the game variant: phase 1 is not a bomb run (no Assault said)")
    return v


def builtin(fails):
    files = mvar.library(home=tempfile.gettempdir())          # MCC's own only (no LocalLow there)
    if not files:
        print("  (MCC not found: part 3 skipped)")
        return []
    bad = [os.path.basename(f) for f in files if not mvar.read(f)["ok"]]
    if bad:
        fails.append(f"built-in map variants not read: {bad[:5]} ({len(bad)} of {len(files)})")
    for name, base in (("boneyard_default_031", "reach_70_boneyard"), ("breakpoint_default_031", "reach_dlc_invasion"),
                       ("spire_default_031", "reach_35_island")):
        f = next((p for p in files if os.path.basename(p) == name + ".mvar"), None)
        if f is None:
            fails.append(f"{name}.mvar missing")
            continue
        a = layout(mvar.scenario_objects(mvar.read(f)))
        b = layout(json.load(open(os.path.join(ROOT, "maps", base, "objects.json"), encoding="utf-8")))
        key = lambda L: (L["attackers"], {k: sorted((round(p.x), round(p.y)) for p in ps)
                                          for k, ps in L["phases"].items()},
                         (round(L["core"].x), round(L["core"].y)),
                         None if L["bomb"] is None else (round(L["bomb"].x), round(L["bomb"].y)))
        if a is None or key(a) != key(b):
            fails.append(f"{name}: file setup {a and key(a)} != scenario {key(b)}")
    print(f"  {len(files)} built-in Reach map variants read")
    return files


def live_match(fails, v, files):
    if v is None:
        return
    pieces = [(o["name"], tuple(o["pos"]), None) for o in v["objects"] if o["mp_type"] == "ordinary"][:60]
    others = [f for f in files if mvar.header_map_id(f) == 2004][:6]
    got, share = mvar.find("reach_dlc_medium", pieces, files=others + [v["path"]])
    if got is None or got["path"] != v["path"] or share < 0.99:
        fails.append(f"find: {got and got['path']} at {share}")
    if mvar.find("reach_dlc_medium", [(n, (p[0] + 9, p[1], p[2]), a) for n, p, a in pieces],
                 files=[v["path"]])[0] is not None:
        fails.append("find: pieces moved 9 u matched the file")
    tmp = tempfile.mkdtemp()
    old = variants.ROOT, mvar.ROOT
    try:
        variants.ROOT = mvar.ROOT = tmp
        name = "reach_dlc_medium/variants/vtest"
        os.makedirs(os.path.join(tmp, name))
        json.dump(dict(id="vtest", base="reach_dlc_medium", name=None),
                  open(os.path.join(tmp, name, "variant.json"), "w"))
        nf, ns, nk = mvar.write(name, v, share)
        info = variants.info(name)
        if info["mvar"]["title"] != "Tempest Invasion" or info["name"] != "Tempest Invasion" or nk != 2:
            fails.append(f"filed: {info.get('mvar')}, {nf} flags {ns} spawns {nk} volumes")
        kz = json.load(open(os.path.join(tmp, name, "killzones.json")))
        if len(kz["volumes"]) != 2 or kz["volumes"][0]["source"] != "mvar":
            fails.append(f"killzones.json {kz}")
        m = maps.load_map(name)
        if not m["objects"].get("mvar") or "inv_res_zone" not in {f["type"] for f in m["objects"]["netgame_flags"]}:
            fails.append("load_map: the file's objects not used")
        for kind in ("drop_points", "stockpile_flags", "territories"):
            if not m["spots"].get(kind):
                fails.append(f"load_map: no {kind} from the file's labels")
        if 0 not in m["flags"] or 1 not in m["flags"]:
            fails.append("load_map: CTF stands lost (the file has none: the scenario's stay)")
        if layout(m["objects"], styles={1: "assault"}) is None:
            fails.append("load_map's objects give no Invasion setup")
        import lidar
        os.makedirs(os.path.join(tmp, "maps", "reach_dlc_medium"))
        shutil.copytree(os.path.join(tmp, "reach_dlc_medium", "variants"), os.path.join(tmp, "maps", "reach_dlc_medium",
                                                                                      "variants"))
        shutil.copy(os.path.join(ROOT, "maps", "reach_dlc_medium", "objects.json"),
                    os.path.join(tmp, "maps", "reach_dlc_medium", "objects.json"))
        lroot, lidar.ROOT = lidar.ROOT, tmp
        try:
            pts = lidar.objective_points(name, stations=type("S", (), {"objects": []})())
        finally:
            lidar.ROOT = lroot
        roles = {r for p in pts for r in p["roles"]}
        if not pts or not all(p["src"] in ("map", "mvar", "map+live") for p in pts) or \
                not {"invasion", "drop_point", "race", "territory"} <= roles:
            fails.append(f"objective_points: {len(pts)} places, roles {sorted(roles)}")
    finally:
        variants.ROOT, mvar.ROOT = old
        shutil.rmtree(tmp, ignore_errors=True)


def halo3(fails):
    files = mvar.library("h3", home=tempfile.gettempdir())
    if not files:
        print("  (MCC not found: part 5 skipped)")
        return
    import map_features as F
    bad, goals = [], set()
    for f in files:
        v = mvar.read_h3(f)
        if not v["ok"] or v["map"] is None:
            bad.append(os.path.basename(f))
        goals |= {n for n, _, _ in v["objectives"]}
    if bad:
        fails.append(f"Halo 3 variants not read: {bad[:5]} ({len(bad)} of {len(files)})")
    roles = {F.role_of(n) for n in goals}
    if not {"flag", "flag_return", "hill", "ball", "territory", "bomb", "bomb_goal"} <= roles:
        fails.append(f"Halo 3 objectives' roles {sorted(map(str, roles))} from {sorted(goals)}")
    hc = next((f for f in files if os.path.basename(f) == "h3_hardcoreConstruct.mvar"), None)
    if hc:                                      # its spawns and objectives where the scenario has them (cm off)
        v, o = mvar.read_h3(hc), json.load(open(os.path.join(ROOT, "maps", "h3_construct", "objects.json")))
        pts = [s["pos"] for s in o["spawns"]] + [f["pos"] for f in o["netgame_flags"]]
        ds = sorted(min(sum((a - b) ** 2 for a, b in zip(x["pos"], p)) ** 0.5 for p in pts) for x in v["objects"]
                    if x["placed"] and x["name"] in ("respawn_point", "ctf_flag_spawn_point", "koth_hill_static"))
        if len(ds) < 10 or ds[len(ds) // 2] > 0.5:
            fails.append(f"Halo 3 MLG Construct positions off the scenario's: {ds}")
    print(f"  {len(files)} Halo 3 map variants read, objectives {sorted(goals)}")


def main():
    fails = []
    if not paths.mcc():
        print("  (MCC not found)")
    v = tempest(fails)
    files = builtin(fails)
    live_match(fails, v, files)
    halo3(fails)
    for f in fails:
        print("FAIL:", f)
    if fails:
        sys.exit(1)
    print("mvar OK")


if __name__ == "__main__":
    main()
