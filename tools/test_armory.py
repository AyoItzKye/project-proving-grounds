"""The profile view's armor worked out offline (brain/armory.py, tools/armory_tables.py: Reach's and Halo 4's rolls, the
customization tables of all four): checks that fail on a wrong mirror of botcore's roll, a misread catalog log or table.

1. xorshift and the roll by hand: botcore's generator from x = 1, then hr_roll_armor's order (a step for the item, a
   step for the variant, a step for a slot with no items, "none" slots first without a step)
2. parse_log: Reach's and Halo 4's catalog lines into variant counts and per-variant writes (offsets as the game's
   equip wrote them; a faulted equip None; Halo 4's r / s / x writes at +0x38 / +0x40 / +0x2B)
3. pieces: the base, the female body over it, an option's records by body mask (a robot-arm chest's male / female
   arms), the Elite's own base and set
4. the live roll: five bots of the Boardwalk match (their profile seeds; botcore s102 read their bodies'
   appearance bytes): maps/_looks/reach_armory.json and the mirror give the same helmet ... effect bytes and visor
5. maps/_looks/reach_armory.json is whole: every value the catalog writes names an option of its byte
6. maps/_looks/h2a_armory.json: an MCC Spartan helmet with its visor on the techsuit, an Elite's mixed sets on its base
7. maps/_looks/h3_armory.json: the Spartan's and the Elite's bytes on their own, the shared regions with their pieces

usage: python -I test_armory.py      -> "armory OK"
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import armory_tables  # noqa: E402
from brain import armory, looks  # noqa: E402

# 4: name, profile seed, the live bytes at appearance +0x38..+0x41 (body +0xDE6..+0xDEF) and the visor tint +0x2B
# (logs/looks/avatars/reach_live_20261027.txt; profiles logs/backup_live/bot_profiles_20261027d.ini: Original, rare)
LIVE = [("Medic10", 382444035, [19, 6, 5, 12, 4, 4, 3, 1, 0, 0], 0),
        ("LazyBandit", 138024932, [8, 6, 9, 5, 3, 2, 2, 6, 5, 5], 1),
        ("SirBadger", 46492862, [47, 4, 16, 15, 3, 1, 2, 7, 5, 5], 4),
        ("LilElite", 667848984, [37, 0, 9, 14, 0, 0, 3, 4, 0, 0], 2),
        ("Fox343", 1516579937, [56, 16, 10, 19, 5, 4, 2, 5, 0, 0], 4)]


def main():
    fails = []
    # 1. x = 1: 1 ^ 1 << 13 = 0x2001; ^ 0x2001 >> 17 (0) = 0x2001; ^ 0x2001 << 5 = 0x42021
    if armory.xorshift(1) != 0x42021:
        fails.append(f"xorshift(1) = {armory.xorshift(1):#x}, botcore's gives 0x42021")
    x1 = armory.xorshift(1)
    x2 = armory.xorshift(x1)
    x5 = armory.xorshift(armory.xorshift(armory.xorshift(x2)))
    cat = [[3, 4], [], [18]]           # slot 0: two items, slot 1 none, slot 2 one item of 18 variants
    want = {0: (x1 % 2, x2 % [3, 4][x1 % 2]), 2: (0, x5 % 18)}
    if armory.roll(1, 0b111, 0, cat) != want:
        fails.append(f"roll: {armory.roll(1, 0b111, 0, cat)}, by hand {want}")
    if armory.roll(1, 0b100, 0b001, cat) != {0: (0, 0), 2: (0, armory.xorshift(x1) % 18)}:
        fails.append(f"roll with a none slot: {armory.roll(1, 0b100, 0b001, cat)}")
    # 2. the log halves
    reach_lines = ["reach armory slot 0: 2 items: 0:3:00004ef9 1:3:00004f01",
                   "reach armory slot 1: 0 items:",
                   "reach armory map slot 0 item 0 raw 0: v0[38=0 ] v1[38=1 ] v2[38=2 ]",
                   "reach armory map slot 0 item 1 raw 1: v0[38=3 40=5 41=5 ] v1[fault] v2[38=5 ]"]
    c, w = armory_tables.parse_log(reach_lines)
    if c != [[3, 3], []] or w[0][1] != [{0x38: 3, 0x40: 5, 0x41: 5}, None, {0x38: 5}] or w[0][0][2] != {0x38: 2}:
        fails.append(f"Reach log: {c} {w}")
    h4_lines = ["h4 armory slot 0: 1 items: 0:86:00006e3f [v0 r0=0] [v1 r0=70]",
                "h4 armory slot 13: 1 items: 0:17:00006a34 [v0 x=0] [v1 x=1 s1=2]",
                "h4 armory slot 15: 1 items: 0:52:00006e57 [v0] [v1]"]
    c, w = armory_tables.parse_log(h4_lines, "h4")
    if c[0] != [86] or c[13] != [17] or w[0][0] != [{0x38: 0}, {0x38: 70}] or w[13][0][1] != {0x2B: 1, 0x41: 2} \
            or w[15][0] != [{}, {}]:
        fails.append(f"Halo 4 log: {c} {w}")
    if armory.appearance({0: (0, 2)}, {"writes": w}) is not None:     # variant 2 not logged: not known, never a guess
        fails.append("a variant botcore did not log was taken as known")
    # 3. pieces by body
    t = {"base": [["arms", "default", 0], ["body", "default", 0]],
         "female": [["body", "female", 0], ["arms", "female", 0]],
         "elite_base": [["head", "default", 0], ["armor_pieces", "default", 0]], "elite_bytes": [0x3F],   # (Reach's)
         "options": {"59": [[], [["flair_chest_a", "jun", 0], ["arms", "player_john117", 1], ["arms", "kat", 2]]],
                     "63": [[["armor_pieces", "default", 0]], [["armor_pieces", "spec_ops", 4]]]}}
    male = [("arms", "player_john117"), ("body", "default"), ("flair_chest_a", "jun")]
    if (armory.pieces({0x3B: 1}, "male", t) != male
            or armory.pieces({0x3B: 1}, "female", t) != [("arms", "kat"), ("body", "female"), ("flair_chest_a", "jun")]
            or armory.pieces({0x3F: 1, 0x3B: 1}, "elite", t) != [("armor_pieces", "spec_ops"), ("head", "default")]
            or armory.pieces({}, "female", t) != [("arms", "female"), ("body", "female")]):
        fails.append("pieces: base, female body, body masks or the Elite's set")
    # 4. the live roll (the table as built from the s104 log and the map)
    rt = armory.table()
    if rt is None:
        fails.append("maps/_looks/reach_armory.json missing (python -I tools/armory_tables.py)")
    else:
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bot_profiles.ini")
            with open(p, "w", encoding="utf-8") as f:
                f.write("experience=original\neffects=rare\n" + "".join(f"bot={n},{s},\n" for n, s, _, _ in LIVE))
            for name, _, body, visor in LIVE:
                lk = looks.look(name, "reach", p)
                app = armory.appearance(armory.roll(*lk[1:4], rt["catalog"]), rt)
                got = [app.get(0x38 + k) for k in range(10)]
                if got != body or app.get(0x2B) != visor:
                    fails.append(f"{name}: offline {got} visor {app.get(0x2B)}, live {body} visor {visor}")
        # 5. every logged write names an option of its byte (the visor tint and the voice have no table)
        for s, items in enumerate(rt["writes"]):
            for v in (v for it in items for v in it if v):
                for off, val in v.items():
                    opts = rt["options"].get(off)
                    if opts is not None and not 0 <= val < len(opts):
                        fails.append(f"slot {s} writes {val} at {off}: {len(opts)} options")
    # 6. H2A's table: a Spartan's helmet value 7 (MCC's Orion, with its visor) on the techsuit, an Elite's 4 / 6 / 3 / 5
    # (armor_var1 helmet, var3 chest, var1 arms, var3 legs) on its own base, the Spartan's sets left off the Elite
    ht = armory.table(os.path.join(HERE, "..", "maps", "_looks", "h2a_armory.json"))
    if ht is not None:
        sp = dict(armory.pieces({0x38: 7, 0x39: 1}, "male", ht))
        el = dict(armory.pieces({0x38: 4, 0x39: 6, 0x3D: 3, 0x3E: 5}, "elite", ht))
        if (sp.get("armor_head") != "spartan_orion" or sp.get("visor") != "spartan_orion"
                or sp.get("armor_torso") != "spartan_var2" or sp.get("body_torso") != "techsuit"):
            fails.append(f"H2A Spartan pieces: {sp}")
        if el != {"armor_helmet": "armor_var1", "armor_torso": "armor_var3", "armor_arms": "armor_var1",
                  "armor_legs": "armor_var3", "head": "anatomy", "techsuit_arms": "techsuit",
                  "techsuit_legs": "techsuit", "techsuit_torso": "techsuit"}:
            fails.append(f"H2A Elite pieces: {el}")
    # 7. Halo 3's areas: the Spartan's bytes +0x46.. (appearance 0x26..), the Elite's +0x4E.. on their own; the mp_
    # chests bring chest_shared, the legacy Elite head its shared head (the live findings of-26)
    h3 = armory.table(os.path.join(HERE, "..", "maps", "_looks", "h3_armory.json"))
    if h3 is not None:
        sp = dict(armory.pieces({0x26: 5, 0x29: 13}, "male", h3))
        el = dict(armory.pieces({0x2E: 0, 0x33: 1}, "elite", h3))
        if sp.get("helmet") != "legacy_mark_v" or sp.get("chest") != "mp_bungie" or sp.get("chest_shared") != "base":
            fails.append(f"Halo 3 Spartan pieces: {sp}")
        if el.get("head") != "legacy" or el.get("head_shared") != "legacy" or el.get("legs_shared") != "empty":
            fails.append(f"Halo 3 Elite pieces: {el}")
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print("armory OK")


if __name__ == "__main__":
    main()
