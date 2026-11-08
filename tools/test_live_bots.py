"""Offline check of the live glue (no MCC needed): snapshot, flag/death events and button
encoding run against a fake game reader, so a typo there fails here instead of in a match.

usage: python -I test_live_bots.py      -> "live_bots OK"
"""
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import live_bots  # noqa: E402
from brain.core import Action  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


class FakeLive:
    def __init__(s):
        s.carrier = None

    def players(s):
        return [dict(index=0, name="Human", team=0, unit=1, pos=(90.0, -150.0, 0.1), fwd=(1, 0, 0), aim=(1, 0, 0),
                     health=1.0, shield=1.0, weapon="pistol", weapons=["assault_rifle", "pistol"]),
                dict(index=1, name="Bot 1", team=1, unit=2, pos=(50.0, -90.0, 0.1), fwd=(0, 1, 0), aim=(0, 1, 0),
                     health=1.0, shield=0.0, weapon="assault_rifle", weapons=["assault_rifle", "pistol"])]

    def objects(s, types=None):
        return [(0xE2790001, 1, "vehicles\\ghost\\ghost_mp", (52.0, -90.0, 0.4))]

    def flags(s, players, stands=None):
        return [dict(team=0, pos=(95.69, -159.45, -0.29), carrier=s.carrier),
                dict(team=1, pos=(40.24, -79.12, -0.29), carrier=None)]


def main():
    live_bots.MAP = get_map("bloodgulch")
    live = FakeLive()
    snap = live_bots.snapshot(live, 0.0, {}, {1})
    assert snap.mode == "ctf" and snap.flags[0].state == "home" and len(snap.players) == 2
    assert snap.player(1).weapons == ["assault_rifle", "pistol"] and snap.player(1).is_bot
    assert snap.vehicles and snap.vehicles[0]["kind"] == "ghost_mp" and not snap.vehicles[0]["occupied"]
    live_bots.RIDE_ONLY = {"falcon"}               # a test match about Falcons: an empty Ghost is not offered
    assert not live_bots.snapshot(live, 0.5, {}, {1}).vehicles, "--ride-only falcon still showed the empty Ghost"
    live_bots.RIDE_ONLY = None

    # a vehicle on its side or roof is no ride (Halo 4 Exile: an upturned Warthog boarded 20 times); its riders keep
    # it. The reader's orientation: forward at ORIENT_AT, up the next 12 bytes
    class TippedLive(FakeLive):
        ORIENT_AT = 0x70

        def __init__(s, upz, ridden=False):
            super().__init__()
            s.upz, s.ridden = upz, ridden
            live_ = s

            class Mem:
                def read(s, a, n):
                    if a == 0x1000 + 0x70:
                        return struct.pack("<3f", 1.0, 0.0, 0.0)
                    if a == 0x1000 + 0x7C:
                        return struct.pack("<3f", 0.0, (1 - live_.upz ** 2) ** 0.5, live_.upz)
                    return b"\xff" * n                 # (the parent field: none)
            s.g = Mem()

        def object(s, handle):
            return 0x1000

        def players(s):
            ps = super().players()
            if s.ridden:
                ps[1]["vehicle"] = 0xE2790001
            return ps
    for upz, ridden, want in ((1.0, False, True), (-1.0, False, False), (0.3, False, False), (-1.0, True, True)):
        vs = live_bots.snapshot(TippedLive(upz, ridden), 1.0, {}, {1}).vehicles
        if bool(vs) != want or (vs and (vs[0].get("up") or (0, 0, None))[2] != upz):
            raise AssertionError(f"vehicle up z {upz}, ridden {ridden}: offered {bool(vs)} (want {want}), {vs}")
    bot = Bot(1, 1, make_profile("strong", "rusher", random.Random(1)), live_bots.MAP, random.Random(1))
    dirs = {t: Director(t, live_bots.MAP, {1: bot} if t == 1 else {}, random.Random(t)) for t in (0, 1)}
    live.carrier = 1                                   # the bot takes the red flag
    snap2 = live_bots.snapshot(live, 1.0, {}, {1})
    assert snap2.flags[0].state == "carried" and snap2.player(1).has_flag
    live_bots.flag_events(dirs, {0: "home", 1: "home"}, snap2, 1.0)
    live_bots.events({1: bot}, dirs, {p.id: p for p in snap.players}, snap2, 1.0)
    # an item spawn next to the bot with nothing lying there: its team starts the timer
    it = min(range(len(live_bots.MAP["items"])), key=lambda k: (live_bots.MAP["items"][k]["pos"] - snap2.player(1).pos).flat())
    live_bots.MAP["items"][it]["pos"] = snap2.player(1).pos
    live_bots.item_check(live, dirs, {1: bot}, snap2, 5.0)
    assert dirs[1].item_up[it] > 5.0 and dirs[0].item_up[it] == 0.0, "only the team that saw it knows"
    a = Action(fire=True, action=True, weapon=1)
    assert live_bots.buttons(a) == 1 | 32 | (2 << 8)
    assert live_bots.buttons(Action()) == 0
    # an ability reading the game cannot produce (armor lock on for 10 s: its energy lasts 5, the reader lingers 2-3 s
    # after release) turns that kind's on-state off for the match, its name kept; the other kinds and a real evade whose
    # reader lingers keep theirs (logs/brain.txt, Spire: a skilled player's evade, read on 2 s, blanked every player's
    # ability, the bots' own too)
    class AbLive(FakeLive):
        kinds = {}                                     # player index -> (equipment, reader on)

        def players(s):
            return [dict(p, equipment=s.kinds.get(p["index"], ("", False))[0],
                         ability_on=s.kinds.get(p["index"], ("", False))[1]) for p in super().players()]
    ab = AbLive()
    ab.kinds = {0: ("evade", True), 1: ("sprint", False)}
    for t in (0.0, 2.0, 4.0):                          # an evade roll read on 4 s (2-3 s of it the reader lingering)
        s4 = live_bots.snapshot(ab, t, {}, {1})
    if not s4.player(0).ability_on or s4.player(1).equipment != "sprint":
        raise AssertionError(f"a 4 s evade reading: {s4.player(0)}, the bot's kit {s4.player(1).equipment!r}")
    ab.kinds = {0: ("armor_lock", True), 1: ("active_camo", True)}
    for t in (5.0, 10.0, 15.0):                        # a lock read on 10 s: a misread; the camo next to it is not
        s15 = live_bots.snapshot(ab, t, {}, {1})
    a0, a1 = s15.player(0), s15.player(1)
    if a0.ability_on or a0.equipment != "armor_lock" or not a1.ability_on or a1.camo_until <= 15.0:
        raise AssertionError(f"after a 10 s lock reading: {a0.equipment} on {a0.ability_on}, {a1.equipment} on "
                             f"{a1.ability_on} camo {a1.camo_until} (want the lock off, its name and the camo kept)")
    ab.kinds = {1: ("armor_lock", True)}               # another player's lock later on: that kind stays distrusted
    if live_bots.snapshot(ab, 16.0, {}, {1}).player(1).ability_on:
        raise AssertionError("the armor lock reader came back on in the same match")
    live_bots.ABILITY_READ.update(bad=set(), since={})
    # Reach's ability reader: a failed read returns None (TypeError in struct / the tag table), unknown for that tick,
    # not a failed tick (logs/brain.txt, Spire 244.6 s: "tick failed (TypeError ...)" in ability)
    from brain.live import LiveReach
    rd = object.__new__(LiveReach)
    rd.g = type("G", (), dict(base=0, read=lambda s, a, n: None, u64=lambda s, a: None))()
    rd.object = lambda h: 0x1000
    try:
        got = rd.ability(0x10001)
    except TypeError as e:
        raise AssertionError(f"a failed ability read raised {e!r} (want ('unknown', False))")
    if got != ("unknown", False):
        raise AssertionError(f"a failed ability read gave {got} (want ('unknown', False))")
    # the Reach name dump: texts with their offsets, a free player slot skipped, then the raw bytes
    class Mem:
        def read(s, a, n):
            b = bytearray(n)
            if a == 1000:                              # player 0 in use: its name and a tag
                b[0:2], b[0xB0:0xBA], b[0x150:0x156] = b"\1\0", "Owner".encode("utf-16-le"), "TAG".encode("utf-16-le")
            return bytes(b)
        def u64(s, a):
            return 5000
    reach = type("R", (), dict(g=Mem(), _blk=0, _array=lambda s, off: (1000, 2, 0x490)))()
    path = os.path.join(HERE, "_reach_names_test.txt")
    live_bots.reach_name_dump(reach, path)
    lines = open(path, encoding="utf-8").read().splitlines()
    os.remove(path)
    assert lines[0] == "player 0: +0xB0 'Owner'; +0x150 'TAG'", lines[0]
    assert len(lines) == 2 * 17 and not any(x.startswith("player 1") for x in lines), "a free slot was listed"
    # the unit's zoom byte for the trace ("uz"): read at the reader's UNIT_ZOOM from the unit snapshot() saw; None
    # where the game's offset is not decoded or the player is dead
    class ZoomLive(FakeLive):
        UNIT_ZOOM = 0x255

        def object(s, handle):
            return {1: 0x1000, 2: 0x2000}.get(handle)

        g = type("G", (), dict(read=lambda s, a, n: bytes([0xFF if a == 0x1000 + 0x255 else 0x00][:n])))()
    zl = ZoomLive()
    live_bots.snapshot(zl, 2.0, {}, {1})
    if live_bots.unit_zoom(zl, 0) != 0xFF or live_bots.unit_zoom(zl, 1) != 0x00:
        raise AssertionError(f"unit_zoom read {live_bots.unit_zoom(zl, 0)}, {live_bots.unit_zoom(zl, 1)} (want 0xFF, 0)")
    if live_bots.unit_zoom(live, 1) is not None or live_bots.unit_zoom(zl, 7) is not None:
        raise AssertionError("unit_zoom read a byte for a game without UNIT_ZOOM or a player it never saw")
    # each reader keeps its own players' units (no module-level state, Code Master AR-08): a second reader's
    # snapshot must not change what the first one reads
    class OtherLive(ZoomLive):
        def players(s):
            return [dict(p, unit=p["unit"] + 6) for p in FakeLive.players(s)]
    live_bots.snapshot(OtherLive(), 3.0, {}, {1})
    if live_bots.unit_zoom(zl, 0) != 0xFF:
        raise AssertionError(f"another reader's snapshot changed this reader's units: {live_bots.unit_zoom(zl, 0)}")
    # Halo 3 rounds (tools/ammo_scan.py h3: reserve +0x236, magazine +0x23A): a gun's (reserve + magazine,
    # magazine); a gun whose magazine never held a round (battery weapons keep 0 there) is unknown (-1), not dry;
    # games whose fields are not decoded (Reach, ODST, Halo 4 / H2A) stay unknown
    from brain.live import LiveH3, LiveODST, LiveReach, LiveH4F
    h3 = object.__new__(LiveH3)
    guns = {0xA: (0xE10A, 24, 12), 0xB: (0xE10B, 0, 0)}      # handle: (tag, reserve, magazine)

    class GunMem:
        def read(s, a, n):
            g = guns[a >> 16]
            b = bytearray(0x300)
            struct.pack_into("<I", b, 0, g[0])
            struct.pack_into("<hxxh", b, 0x236, g[1], g[2])
            return bytes(b[a & 0xFFFF:(a & 0xFFFF) + n])
    h3.g, h3.object = GunMem(), lambda h: h << 16
    if h3.rounds(0xA) != (36, 12) or h3.rounds(0xB) != (-1, -1):
        raise AssertionError(f"Halo 3 rounds: {h3.rounds(0xA)}, {h3.rounds(0xB)} (want (36, 12), (-1, -1))")
    guns[0xA] = (0xE10A, 0, 0)                               # the same kind run dry: 0, not unknown
    if h3.rounds(0xA) != (0, 0):
        raise AssertionError(f"a dry Halo 3 gun read {h3.rounds(0xA)}")
    # Halo 3 Sandtrap: each CTF flag hangs on a stand (a type 10 object) riding its team's Elephant, placed relative to
    # it; found there, the places the teams' stands now; a gun on an Elephant's turret is no stand (the player: Multi
    # Flag read as Slayer: no flag lay on the map's stand points). Objects: (type, parent index, position, forward, up,
    # tag)
    sand = {1: (1, None, (8.56, 33.12, -21.77), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), 0xE001),        # blue Elephant, facing +y
            2: (10, 1, (1.44, -0.45, 1.35), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0xE002),            # its flag stand
            3: (2, 2, (0.0, 0.0, 0.31), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0x1AFC),                # its flag
            4: (1, None, (-0.27, -58.56, -22.26), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0xE001),     # red Elephant, facing -x
            5: (10, 4, (1.44, -0.57, 1.35), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0xE002),
            6: (2, 5, (0.0, 0.0, 0.31), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0x1AFC),
            7: (1, 1, (2.9, -1.31, 1.48), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0xE003),              # a turret on the blue one
            8: (2, 7, (-0.18, -0.05, 0.09), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0x08FE)}            # ... and its gun
    ENTS = 0x100000

    class SandMem:
        def read(s, a, n):
            if ENTS <= a < ENTS + 9 * 0x18:
                b = bytearray(9 * 0x18)
                for i, o in sand.items():
                    struct.pack_into("<H", b, i * 0x18, 0x100 + i)
                    b[i * 0x18 + 3] = o[0]
                    struct.pack_into("<Q", b, i * 0x18 + 0x10, 0x200000 + i * 0x1000)
                return bytes(b[a - ENTS:a - ENTS + n])
            i, off = (a - 0x200000) >> 12, (a - 0x200000) & 0xFFF
            typ, par, pos, fwd, up, tag = sand[i]
            b = bytearray(0x100)
            struct.pack_into("<I", b, 0, tag)
            struct.pack_into("<I", b, 0x10, 0xFFFFFFFF if par is None else (0x100 + par) << 16 | par)
            struct.pack_into("<9f", b, 0x50, *pos, *fwd, *up)
            return bytes(b[off:off + n])
    h3s = object.__new__(LiveH3)
    h3s.g, h3s._placements = SandMem(), []
    h3s.object = lambda h: 0x200000 + (h & 0xFFFF) * 0x1000 if (h & 0xFFFF) in sand and h >> 16 == 0x100 + (h & 0xFFFF) else 0
    h3s._array = lambda off: (ENTS, 9, 0x18)
    from brain.core import Vec
    sand_stands = {0: Vec(-0.002, 22.533, -23.732), 1: Vec(-21.008, -62.002, -20.753)}   # the map's (the Elephants' start)
    got = {f["team"]: f["pos"] for f in h3s.flags([], stands=sand_stands)}
    want = {0: (9.01, 34.56, -20.11), 1: (-1.71, -57.99, -20.60)}   # along each Elephant's own axes
    near = lambda p, q: all(abs(p[k] - q[k]) < 0.02 for k in range(3))
    if set(got) != {0, 1} or not all(near(got[t], want[t]) for t in want) or \
            not all(near((h3s.live_stands[t].x, h3s.live_stands[t].y, h3s.live_stands[t].z), want[t]) for t in want):
        raise AssertionError(f"Sandtrap flags {got}, stands {h3s.live_stands} (want both at {want})")
    # ... and each team captures at its Elephant's flag_return, on the bay floor (brain/vehicles.ELEPHANT)
    want_ret = {0: (8.83, 33.36, -21.22), 1: (-0.51, -58.29, -21.71)}
    rets = getattr(h3s, "live_returns", {})
    if set(rets) != {0, 1} or not all(near((rets[t].x, rets[t].y, rets[t].z), want_ret[t]) for t in want_ret):
        raise AssertionError(f"Sandtrap returns {rets} (want {want_ret})")
    # Halo 2: reserve +0x22E and magazine +0x230 side by side (found live: 120 -> 60 per refill, 60 -> 14 firing)
    from brain.live import LiveH2

    class GunMem2:
        def read(s, a, n):
            b = bytearray(0x300)
            struct.pack_into("<I", b, 0, 0xE20A)
            struct.pack_into("<hh", b, 0x22E, 120, 41)
            return bytes(b[a & 0xFFFF:(a & 0xFFFF) + n])
    h2 = object.__new__(LiveH2)
    h2.g, h2.object = GunMem2(), lambda h: h << 16
    if h2.rounds(0xA) != (161, 41):
        raise AssertionError(f"Halo 2 rounds: {h2.rounds(0xA)} (want (161, 41))")
    guns[0xA] = (0xE10A, 24, 12)                  # loaded again: a reader using Halo 3's offsets would read (36, 12)
    # loose guns for a dry bot's rearm, Halo 2 / 3 (second review: they read CE's offsets, parent +0xD8 and rounds
    # +0x286): parent (Halo 2 +0x14, Halo 3 +0x10) none and rounds left. Left out: a gun in hand (1), an emptied gun of
    # a kind seen loaded (3), a flag (5: Halo 3 knows its tag from the stand); kept: unknown rounds (4, battery). Reach
    # (+0x14) and Halo 4 / H2A (+0x24) by their own parent fields, the ones their loose-flag readers use live (CTF and
    # Oddball pickups), rounds not decoded there so an emptied gun stays (3): CE's reader found no Reach power weapon
    # lying loose in match 220515, and no bot was sent for one
    from brain.live import NONE, Live
    for cls, parent_at, at, want in ((LiveH2, 0x14, (0x22E, 0x230), [2.0, 4.0]), (LiveH3, 0x10, (0x236, 0x23A), [2.0, 4.0]),
                                     (LiveReach, 0x14, (0x200, 0x202), [2.0, 3.0, 4.0]),
                                     (LiveH4F, 0x24, (0x200, 0x202), [2.0, 3.0, 4.0])):
        objs = {1: (0xE301, 0x12340001, 24, 12), 2: (0xE302, NONE, 24, 12), 3: (0xE301, NONE, 0, 0),
                4: (0xE304, NONE, 0, 0), 5: (0xE305, NONE, 0, 0)}     # handle: (tag, parent, reserve, magazine)

        class LooseMem:
            def read(s, a, n):
                tag, parent, reserve, mag = objs[a >> 16]
                b = bytearray(0x300)
                struct.pack_into("<II", b, 0, tag, 0)
                struct.pack_into("<I", b, parent_at, parent)
                struct.pack_into("<h", b, at[0], reserve)
                struct.pack_into("<h", b, at[1], mag)
                return bytes(b[a & 0xFFFF:(a & 0xFFFF) + n])
        r = object.__new__(cls)
        r.g, r.object, r._flag_tags = LooseMem(), lambda h: h << 16, {0xE305}
        r.objects = lambda types=None: [(h, 2, f"weapons\\gun{h}", (float(h), 0.0, 0.0)) for h in objs]
        r.rounds(1)                                          # gun 1 in hand seen loaded (players() reads it each tick)
        got = r.ground_weapons()
        if [p[0] for _, p in got] != want:
            raise AssertionError(f"{cls.__name__} loose guns: {got} (want guns {want})")
    if LiveODST.ground_weapons is not Live.ground_weapons:
        raise AssertionError("ODST loose guns changed (not decoded there: left as they were)")
    # CE's gun in hand: the slot is the byte at unit +0x2D3 (+0x2D2 beside it stays 0). Read as an int16 at +0x2D2, a
    # player on his second gun read slot 256, "none" (live: +0x2D3 followed the slot asked, 0 then 1, and fire on
    # slot 1 drained the needler a bot had picked up, 20 -> 6)
    mem = {0x1000: bytearray(0x68), 0x20000: bytearray(0x400)}       # a player in use, its unit (handle 7)
    struct.pack_into("<H", mem[0x1000], 0, 1)
    struct.pack_into("<I", mem[0x1000], 0x64, 7)
    struct.pack_into("<4I", mem[0x20000], 0x2D8, 0xA, 0xB, NONE, NONE)
    struct.pack_into("<I", mem[0x20000], 0xD8, NONE)

    class CEMem:
        base = 0                        # (the variant's tracker flags read past the fake memory: zeros)

        def read(s, a, n):
            base = max(k for k in mem if k <= a)
            return bytes(mem[base][a - base:a - base + n]).ljust(n, bytes(1))
    ce = object.__new__(Live)
    ce.g, ce._array, ce.object = CEMem(), lambda ptr: (0x1000, 1, 0x68), lambda h: 0x20000 if h == 7 else None
    ce.weapon_name = lambda h: {0xA: "plasma_pistol", 0xB: "needler"}.get(h, "none")
    ce.ammo = ce.mag = lambda h: -1
    for slot, gun in ((0, "plasma_pistol"), (1, "needler")):
        mem[0x20000][0x2D3] = slot
        if ce.players()[0]["weapon"] != gun:
            raise AssertionError(f"CE slot {slot} in hand read {ce.players()[0]['weapon']!r} (want {gun})")
    for cls in (LiveReach, LiveODST, LiveH4F):
        r = object.__new__(cls)
        r.g, r.object = GunMem(), lambda h: h << 16
        if r.rounds(0xA) != (-1, -1):
            raise AssertionError(f"{cls.__name__} read rounds without a decode")
    # gun naming from map spawns (the rockets mislabel, and starting guns named from their map copies): moved to
    # tools/test_weapon_names.py, which runs the readers' real objects / weapon_name over fake memory. The check
    # that stood here ("a kind someone has held is never named from a spawn") was the bug: Halo 3 starting guns
    # never got a name (spec change, see the commit)
    # a flag read as a team the map has no stand for (Halo 2 Containment: red's as team 7, on stand 1; the brain
    # stopped on its first tick, KeyError 7): taken as the team whose stand it is on, kept when it moves
    class Team7Live(FakeLive):
        def __init__(s, at):
            super().__init__()
            s.at = at

        def flags(s, players, stands=None):
            return [dict(team=0, pos=(95.69, -159.45, -0.29), carrier=None),
                    dict(team=7, pos=s.at, carrier=None)]
    live_bots.MAP = get_map("bloodgulch")
    live_bots.MAP.pop("flag_team_fix", None)
    s7 = live_bots.snapshot(Team7Live((40.24, -79.12, -0.29)), 20.0, {}, {1})
    assert set(s7.flags) == {0, 1} and s7.flags[1].state == "home", f"team 7 flag on stand 1: {s7.flags}"
    s7b = live_bots.snapshot(Team7Live((60.0, -100.0, 0.1)), 21.0, {}, {1})
    assert s7b.flags[1].state == "dropped", f"team 7 flag moved off: {s7b.flags}"
    live_bots.MAP.pop("flag_team_fix", None)
    print("live_bots OK")


if __name__ == "__main__":
    main()
