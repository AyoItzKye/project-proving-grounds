"""Stations for the player's boot camps:

1. classify, on real tag names from each Forge game's own table (Reach, Halo 3, Halo 4, H2A): armor abilities and
   equipment to pick up (not the deployed shield, turret or lift), teleporter sides, man cannons, lifts, zones, spawns,
   power-ups, ammo; vehicles and weapons by object type; building pieces are no station
2. Stations: a taken ability keeps its spot (its respawn merges, where it is dropped is no spawn), a ridden vehicle
   stays where it stood, a teleporter moved in Forge follows, a gun beside a player does not; a jump from beside a
   sender to beside a receiver is their pair; a mark keeps the stations nearest it; objects a 60 s run never saw are
   gone on save, and the file loads back
3. scan reads a (made-up) Reach object table: names by tag, place, facing and parent
4. the LiDAR view's features carry the stations, the pair and the mark
5. a bug report filed in a LiDAR run carries the stations nearest the player and becomes a mark

usage: python -I test_stations.py      -> "stations OK"
"""
import json
import os
import struct
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import stations as S  # noqa: E402
from brain.core import PlayerState, Vec  # noqa: E402

SHAPES = os.path.join(HERE, "..", "maps", "_shapes")
NAMES = {   # (table, tag name, object type) -> (kind, what)
    ("reach_tags_forge_halo", r"objects\equipment\jet_pack\jet_pack", 3): ("ability", "jetpack"),
    ("reach_tags_forge_halo", r"objects\equipment\armor_lockup\armor_lockup", 3): ("ability", "armor_lock"),
    ("reach_tags_forge_halo", r"objects\equipment\drop_shield\drop_shield_shield\drop_shield_shield", 6): (None, None),
    ("reach_tags_forge_halo", r"objects\equipment\health_pack\health_pack", 3): ("health", "health_pack"),
    ("reach_tags_forge_halo", r"objects\levels\forge\ff_teleporter_sender\ff_teleporter_sender", 10): ("teleporter", "sender"),
    ("reach_tags_forge_halo", r"objects\levels\forge\ff_teleporter_receiver\ff_teleporter_receiver", 10): ("teleporter", "receiver"),
    ("reach_tags_forge_halo", r"objects\levels\forge\ff_teleporter_2_way\ff_teleporter_2_way", 10): ("teleporter", "2way"),
    ("reach_tags_forge_halo", r"objects\levels\forge\ff_teleport_frame\ff_teleport_frame", 10): (None, None),
    ("reach_tags_forge_halo", r"objects\levels\forge\ff_man_cannon_forge\ff_man_cannon_forge", 10): ("launcher", "ff_man_cannon_forge"),
    ("reach_tags_forge_halo", r"objects\levels\forge\ff_grav_lift\ff_grav_lift", 10): ("lift", "ff_grav_lift"),
    ("reach_tags_forge_halo", r"objects\multi\boundaries\soft_kill_volume", 6): ("kill_zone", "soft_kill_volume"),
    ("reach_tags_forge_halo", r"objects\multi\boundaries\soft_safe_volume", 6): ("safe_zone", "soft_safe_volume"),
    ("reach_tags_forge_halo", r"objects\multi\spawning\respawn_point", 6): ("spawn", "respawn_point"),
    ("reach_tags_forge_halo", r"objects\multi\powerups\powerup_blue\powerup_blue", 3): ("powerup", "powerup_blue"),
    ("h3_tags_sandbox", r"objects\equipment\bubbleshield_equipment\bubbleshield_equipment", 3): ("ability", "bubble_shield"),
    ("h3_tags_sandbox", r"objects\equipment\bubbleshield\bubbleshield", 6): (None, None),
    ("h3_tags_sandbox", r"objects\equipment\gravlift_equipment\gravlift_equipment", 3): ("ability", "grav_lift"),
    ("h3_tags_sandbox", r"objects\equipment\gravlift\gravlift", 6): (None, None),
    ("h3_tags_sandbox", r"objects\equipment\gravlift_permanent\gravlift_permanent", 6): ("lift", "gravlift_permanent"),
    ("h3_tags_sandbox", r"objects\multi\teleporter_reciever\teleporter_reciever", 6): ("teleporter", "receiver"),
    ("h3_tags_sandbox", r"objects\levels\dlc\shared\man_cannon_forge\man_cannon_forge", 7): ("launcher", "man_cannon_forge"),
    ("h3_tags_sandbox", r"objects\powerups\shotgun_ammo\shotgun_ammo", 2): ("ammo", "shotgun_ammo"),
    ("h4_tags_ca_forge_erosion", r"objects\equipment\storm_jet_pack\storm_jet_pack", 3): ("ability", "jetpack"),
    ("h4_tags_ca_forge_erosion", r"objects\equipment\storm_active_shield\storm_active_shield", 3): ("ability", "hardlight_shield"),
    ("h4_tags_ca_forge_erosion", r"objects\equipment\storm_forerunner_vision\storm_forerunner_vision", 3): ("ability", "promethean_vision"),
    ("h4_tags_ca_forge_erosion", r"objects\equipment\storm_auto_turret\turret\turret", 1): (None, None),
    ("h2a_tags_ca_forge_skybox01", r"objects\levels\forge\fw_gadgets\fw_teleporter_sender\fw_teleporter_sender", 10): ("teleporter", "sender"),
    ("h2a_tags_ca_forge_skybox01", r"objects\levels\forge\fw_gadgets\fw_cannon_man\fw_cannon_man", 10): ("launcher", "fw_cannon_man"),
    ("h2a_tags_ca_forge_skybox01", r"objects\multi\models\mp_trait_zone\mp_trait_zone", 10): ("trait_zone", "mp_trait_zone"),
}


def main():
    fails = []
    # 1. classify real names
    tables = {}
    for (table, name, typ), want in NAMES.items():
        if table not in tables:
            tables[table] = set(json.load(open(os.path.join(SHAPES, table + ".json"))))
        if name not in tables[table]:
            fails.append(f"1. {name} is not in {table} (the test must use the game's own names)")
            continue
        got = S.classify(name, typ)
        if got != want:
            fails.append(f"1. {table}: {name.rsplit(chr(92), 1)[-1]} -> {got} (want {want})")
    for path, typ, want in ((r"objects\vehicles\human\warthog\warthog", 1, ("vehicle", "warthog")),
                            (r"objects\weapons\rifle\dmr\dmr", 2, ("weapon", "dmr")),
                            (r"objects\weapons\grenade\frag_grenade\frag_grenade", 2, ("grenade", "frag_grenade")),
                            (r"objects\levels\forge\ff_block_small\ff_block_small", 10, (None, None))):
        if S.classify(path, typ) != want:
            fails.append(f"1. {path} type {typ} -> {S.classify(path, typ)} (want {want})")
    # 2. the keeper
    tmp = tempfile.mkdtemp(prefix="halo_stations_")
    root, S.ROOT = S.ROOT, tmp
    try:
        clock = [1000.0]
        st = S.Stations("camp", clock=lambda: clock[0])
        A, SND, RCV, W, G = (0.0, 0.0, 1.0), (10.0, 0.0, 1.0), (40.0, 0.0, 6.0), (20.0, 5.0, 1.0), (5.0, 10.0, 1.0)
        o = lambda h, kind, what, pos, parent=S.NONE: dict(h=h, kind=kind, what=what, pos=pos, fwd=(1.0, 0.0, 0.0), parent=parent)
        st.update([o(1, "ability", "jetpack", A), o(2, "teleporter", "sender", SND), o(3, "teleporter", "receiver", RCV),
                   o(4, "vehicle", "warthog", W), o(6, "weapon", "dmr", G), o(9, "teleporter", "sender", (0.0, 40.0, 1.0))])
        st.update([o(1, "ability", "jetpack", A, parent=0xE0010001)])                 # taken
        st.update([o(1, "ability", "jetpack", (30.0, 30.0, 1.0)), o(5, "ability", "jetpack", (0.3, 0.0, 1.0))])   # dropped; respawn
        st.update([o(4, "vehicle", "warthog", (60.0, 5.0, 1.0))], ridden={4})          # driven off
        st.update([o(2, "teleporter", "sender", (12.0, 0.0, 1.0))])                    # moved in Forge
        st.update([o(6, "weapon", "dmr", (50.0, 50.0, 1.0))], people=[(50.2, 50.0, 1.0)])   # in a hand, no parent kept
        kinds = sorted((x["kind"], x["what"], tuple(x["pos"])) for x in st.objects)
        want = sorted([("ability", "jetpack", A), ("teleporter", "sender", (12.0, 0.0, 1.0)), ("teleporter", "receiver", RCV),
                       ("vehicle", "warthog", W), ("weapon", "dmr", G), ("teleporter", "sender", (0.0, 40.0, 1.0))])
        if kinds != want:
            fails.append(f"2. kept {kinds} (want {want})")
        st.watch([(7, (12.3, 0.4, 1.0), True)])
        st.watch([(7, (40.2, 0.3, 6.0), True)])
        st.watch([(8, (30.0, 30.0, 1.0), True)])
        st.watch([(8, (0.0, 30.0, 1.0), True)])                                          # a respawn far from both
        st.watch([(9, (12.2, 0.1, 1.0), True)])
        st.watch([(9, (0.3, 40.0, 1.0), True)])                                          # (a respawn beside a sender: no pair)
        if st.teleports != [[[12.0, 0.0, 1.0], list(RCV), 1]]:
            fails.append(f"2. teleports {st.teleports} (want the moved sender to the receiver, once)")
        m = st.mark("station 1 jetpack", (1.0, 0.5, 1.0), "20991231-000001", 12.5)
        if not m or m["near"][0][:2] != ["ability", "jetpack"] or st.mark("again", (0, 0, 0), "20991231-000001") is not None:
            fails.append(f"2. mark {m} (want the jetpack nearest, a stamp marked once)")
        st.objects.append(dict(kind="lift", what="old_lift", pos=[90.0, 90.0, 1.0], fwd=None, seen=1))   # from an older layout
        clock[0] += 61.0
        st.save()
        back = S.load("camp")
        if len(back["objects"]) != 6 or any(x["what"] == "old_lift" for x in back["objects"]) or len(back["marks"]) != 1:
            fails.append(f"2. saved {back['objects']} marks {back['marks']} (want 6, no old lift, one mark)")
        # 3. scan a made-up Reach object table
        names = ["", r"objects\equipment\jet_pack\jet_pack", r"objects\levels\forge\ff_teleporter_sender\ff_teleporter_sender",
                 r"objects\levels\forge\ff_block_small\ff_block_small", r"objects\vehicles\human\warthog\warthog",
                 r"objects\vehicles\human\warthog\turrets\warthog_gauss\warthog_gauss",
                 r"objects\vehicles\human\warthog\turrets\warthog_troop\warthog_troop"]
        mem, ents = {}, 0x1000
        rows = [(1, 3, 1, (1.0, 2.0, 3.0), S.NONE), (2, 10, 2, (4.0, 5.0, 6.0), S.NONE), (3, 10, 3, (7.0, 8.0, 9.0), S.NONE),
                (4, 1, 4, (10.0, 11.0, 12.0), S.NONE), (0, 1, 4, (0.0, 0.0, 0.0), S.NONE),
                (5, 1, 4, (20.0, 0.0, 1.0), S.NONE), (6, 1, 5, (0.1, 0.0, 0.5), (5 << 16) | 5),      # a gauss Warthog
                (7, 1, 4, (30.0, 0.0, 1.0), S.NONE), (8, 1, 6, (0.1, 0.0, 0.5), (7 << 16) | 7)]      # a Transport Hog
        table = bytearray(0x18 * len(rows))
        for i, (salt, typ, tag, pos, parent) in enumerate(rows):
            obj = 0x10000 + i * 0x100
            struct.pack_into("<H", table, i * 0x18, salt)
            table[i * 0x18 + 4] = typ
            struct.pack_into("<Q", table, i * 0x18 + 0x10, obj)
            head = bytearray(0x68)
            struct.pack_into("<I", head, 0, tag)
            struct.pack_into("<I", head, 0x14, parent)
            struct.pack_into("<3f", head, 0x44, *pos)
            struct.pack_into("<3f", head, 0x50, 0.0, 1.0, 0.0)
            mem[obj] = bytes(head)
        mem[ents] = bytes(table)
        live = types.SimpleNamespace(OBJECTS_AT=0x10, TYPE_AT=4, POS_AT=0x44, PARENT_AT=0x14, TAG_AT=0,
                                     _array=lambda ptr: (ents, len(rows), 0x18),
                                     g=types.SimpleNamespace(read=lambda a, n: mem[a][:n]))
        got = [(x["h"], x["kind"], x["what"], x["pos"], x["fwd"]) for x in S.scan(live, "reach", names)
               if x["parent"] == S.NONE]
        want = [((1 << 16) | 0, "ability", "jetpack", (1.0, 2.0, 3.0), (0.0, 1.0, 0.0)),
                ((2 << 16) | 1, "teleporter", "sender", (4.0, 5.0, 6.0), (0.0, 1.0, 0.0)),
                ((4 << 16) | 3, "vehicle", "warthog", (10.0, 11.0, 12.0), (0.0, 1.0, 0.0)),
                ((5 << 16) | 5, "vehicle", "gauss", (20.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
                ((7 << 16) | 7, "vehicle", "thog", (30.0, 0.0, 1.0), (0.0, 1.0, 0.0))]
        if got != want:
            fails.append(f"3. scan {got} (want the jetpack, the sender, a Warthog, a gauss Warthog and a Transport Hog by "
                         "what rides on them; no block, no empty slot)")
        # 3b. LiDAR mode's riders (tools/lidar.py seat_places, people_states): the player on the gauss Warthog's gun
        # reads his seat's offset as his place; he is where the Warthog is, on its gun
        import lidar
        objs = [((5 << 16) | 5, 1, names[4], (20.0, 0.0, 1.0)), ((6 << 16) | 6, 1, names[5], (0.1, 0.0, 0.5))]
        par = {(6 << 16) | 6: (5 << 16) | 5}
        fake = types.SimpleNamespace(PARENT_AT=0x14, objects=lambda types_: objs, object=lambda h: h,
                                     g=types.SimpleNamespace(read=lambda a, n: struct.pack("<I", par.get(a - 0x14, S.NONE))))
        people = [dict(index=0, team=0, name="you", pos=(0.1, 0.0, 0.5), vehicle=(6 << 16) | 6, aim=(1.0, 0.0, 0.0)),
                  dict(index=1, team=0, name="bot", pos=(5.0, 5.0, 1.0), vehicle=-1, aim=(0.0, 1.0, 0.0))]
        vlist = lidar.seat_places(fake, people)
        states = lidar.people_states(people, {1}, lambda p: True, {})
        me = next(q for q in states if q.id == 0)
        if (me.pos != Vec(20.0, 0.0, 1.0) or me.vehicle != (5 << 16) | 5 or me.turret != "warthog_gauss" or not me.gunner_seat
                or [v["handle"] for v in vlist] != [(5 << 16) | 5] or people[1]["pos"] != (5.0, 5.0, 1.0)):
            fails.append(f"3b. a rider in LiDAR mode: at {me.pos} in {me.vehicle} on {me.turret!r}, vehicles {vlist} (want the "
                         "Warthog's place, on its gauss gun; the gun no vehicle of its own; the bot on foot untouched)")
        # 4. the LiDAR view's features
        import lidar
        d = lidar.load_features("camp", st)
        fk = {f["kind"] for f in d.get("features", [])}
        if not {"ability", "teleporter", "vehicle", "mark"} <= fk or d.get("teleporters") != [[[12.0, 0.0, 1.0], list(RCV)]]:
            fails.append(f"4. view features {sorted(fk)}, teleporters {d.get('teleporters')}")
        # 5. a bug report in a LiDAR run
        reports, import_dir = os.path.join(tmp, "bug_reports"), None
        import bug_reports
        import_dir, bug_reports.DIR = bug_reports.DIR, reports
        try:
            os.makedirs(os.path.join(reports, "20991231-000002"))
            import time
            json.dump(dict(time="t", unix=time.time(), title="", how="", description="station 2 armor lock"),
                      open(os.path.join(reports, "20991231-000002", "report.json"), "w"))
            snap = types.SimpleNamespace(mode="lidar", score={}, players=[
                PlayerState(0, 0, "you", Vec(19.0, 5.0, 1.0), is_bot=False), PlayerState(1, 0, "bot", Vec(0, 0, 0))])
            done = bug_reports.attach_new(time.time() - 10, 10.0, snap, "camp", None, "lidar_camp_20991231-000000.jsonl",
                                          {}, mode="lidar", stations=st)
            entry = json.load(open(os.path.join(reports, "lidar_camp_20991231-000000", "reports.json")))[0]
            if (done != ["20991231-000002"] or entry["near"][0][:2] != ["vehicle", "warthog"]
                    or "LiDAR run" not in entry.get("note", "") or st.marks[-1]["text"] != "station 2 armor lock"):
                fails.append(f"5. filed {done}: near {entry.get('near')}, note {entry.get('note')}, marks {st.marks[-1:]}")
        finally:
            bug_reports.DIR = import_dir
    finally:
        S.ROOT = root
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        sys.exit("stations FAILED:\n  " + "\n  ".join(fails))
    print("stations OK")


if __name__ == "__main__":
    main()
