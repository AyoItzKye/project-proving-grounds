"""Offline checks for loadout changes (brain/loadouts.py, live_bots.loadout_check)..

usage: python -I test_loadouts.py      -> "loadouts OK"
"""
import collections
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.loadouts import Palette, death_kind, liked_guns, record_death, want_slot  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")


def bot(tier, i=1):
    return Bot(i, 0, make_profile(tier, "rusher", random.Random(i)), MAP, random.Random(i))


def death(t, mine, theirs, d, slot=0, vehicle=False):
    return dict(t=t, slot=slot, mine=mine, theirs=theirs, d=d, vehicle=vehicle)


def palette(**slots):
    p = Palette()
    for k, guns in slots.items():
        p.learn(int(k[1:]), guns)
    return p


def main():
    fails = []
    # 1. reading how a life ended
    for d, want in ((death(0, "assault_rifle", "dmr", 15.0), "outranged"),
                    (death(0, "dmr", "assault_rifle", 2.0), "close"),
                    (death(0, "dmr", "dmr", 10.0), None),                 # a fair fight lost
                    (death(0, "dmr", "magnum", 3.0, vehicle=True), "vehicle"),
                    (death(0, "dmr", None, None), None)):                  # killer unknown
        if death_kind(d) != want:
            fails.append(f"death_kind {d} = {death_kind(d)}, want {want}")

    # 2. the palette: learned from spawns; all slots alike = no choice in this gametype
    p = palette(s0=["assault_rifle", "magnum"], s1=["dmr", "magnum"])
    if not p.choice() or p.seen[1] != ("dmr", "magnum"):
        fails.append(f"palette {p.seen}")
    same = palette(s0=["dmr", "magnum"], s1=["dmr", "magnum"], s2=["dmr", "magnum"])
    if same.choice():
        fails.append("three slots with the same guns still offered a choice")
    unknown = Palette()
    unknown.learn(2, ["unknown", "none"])
    if unknown.seen:
        fails.append("learned a slot from unknown guns")

    # 3. the problem decides; the tier decides how fast (top 1 death, strong 2, average 3, novice never)
    for tier, deaths_needed in (("top", 1), ("strong", 2), ("average", 3)):
        b = bot(tier)
        b.deaths = []
        got = None
        for n in range(1, 4):
            b.deaths.append(death(n, "assault_rifle", "dmr", 15.0))
            got = want_slot(b, palette(s0=["assault_rifle", "magnum"], s1=["dmr", "magnum"]), 0, 10.0 + n)
            if got:
                break
        if not got or got[0] != 1 or n != deaths_needed:
            fails.append(f"{tier}: outranged with an AR -> {got} after {n} deaths (want slot 1 after {deaths_needed})")
    b = bot("novice")
    b.deaths = [death(n, "assault_rifle", "dmr", 15.0) for n in range(5)]
    if want_slot(b, palette(s0=["assault_rifle", "magnum"], s1=["dmr", "magnum"]), 0, 9.0):
        fails.append("a novice changed loadout (novices keep the wrong gun)")

    # ... up close with a DMR against an AR: the AR slot; a driver: the plasma pistol slot
    b = bot("top")
    b.deaths = [death(1, "dmr", "assault_rifle", 2.0, slot=1)]
    got = want_slot(b, palette(s0=["assault_rifle", "magnum"], s1=["dmr", "magnum"]), 1, 5.0)
    if not got or got[:2] != (0, "close"):
        fails.append(f"close deaths with a DMR -> {got} (want the AR slot 0)")
    b = bot("top")
    b.deaths = [death(1, "dmr", "magnum", 5.0, vehicle=True)]
    got = want_slot(b, palette(s0=["dmr", "magnum"], s1=["assault_rifle", "magnum"], s2=["dmr", "plasma_pistol"]), 0, 5.0)
    if not got or got[:2] != (2, "vehicle"):
        fails.append(f"vehicle deaths -> {got} (want the plasma pistol slot 2)")

    # ... the same guns everywhere, the ability decides: vehicles -> the armor lock slot (guide 08)
    b = bot("top")
    b.deaths = [death(1, "dmr", "magnum", 5.0, vehicle=True)]
    pal = Palette()
    for slot, ab in ((0, "sprint"), (1, "jetpack"), (2, "armor_lock"), (3, "hologram"), (4, "drop_shield")):
        pal.learn(slot, ["dmr", "magnum"], ab)
    got = want_slot(b, pal, 0, 5.0)
    if not pal.choice() or not got or got[0] != 2:
        fails.append(f"vehicle deaths with equal guns -> {got} (want the armor lock slot 2)")

    # ... no known answer: try a slot nobody has seen (the team learns it)
    b = bot("top")
    b.deaths = [death(1, "assault_rifle", "dmr", 15.0)]
    got = want_slot(b, palette(s0=["assault_rifle", "magnum"]), 0, 5.0)
    if not got or got[0] == 0:
        fails.append(f"outranged with only the AR slot known -> {got} (want an unseen slot)")

    # ... counted again from each change: the same deaths do not switch twice; fair fights never switch
    b = bot("top")
    b.deaths = [death(1, "assault_rifle", "dmr", 15.0)]
    pal = palette(s0=["assault_rifle", "magnum"], s1=["dmr", "magnum"])
    want_slot(b, pal, 0, 5.0)
    if want_slot(b, pal, 1, 6.0) or want_slot(b, pal, 0, 6.0):
        fails.append("switched again on the deaths before the last change")
    b = bot("top")
    b.deaths = [death(n, "dmr", "dmr", 10.0) for n in range(4)]
    if want_slot(b, pal, 1, 9.0):
        fails.append("fair fights lost changed the loadout")
    if want_slot(bot("top"), same, 0, 1.0):
        fails.append("asked for a loadout where every slot gives the same guns")

    # 3b. a favourite gun: fixed per name, varied across names; a bot with no problem goes for the slot with the gun
    # it likes most, looks in an unseen slot while its favourite has not turned up, and keeps the answer once a
    # problem made it change
    tops = collections.Counter(liked_guns(f"bot{n}")[0] for n in range(200))
    if liked_guns("Hawk983") != liked_guns("hawk983") or not {"battle_rifle", "dmr", "assault_rifle"} <= set(tops) \
            or not 40 < tops["battle_rifle"] < 100:
        fails.append(f"liked guns: {dict(tops)}")
    b = bot("novice")
    b.liked = ["battle_rifle", "dmr", "assault_rifle"]
    pal = palette(s0=["dmr", "magnum"], s1=["battle_rifle", "magnum"], s2=["assault_rifle", "magnum"],
                  s3=["dmr", "plasma_pistol"], s4=["covenant_carbine", "magnum"])
    if want_slot(b, pal, 0, 1.0) != (1, "liked", 0) or want_slot(b, pal, 1, 2.0):
        fails.append(f"a BR lover with the BR in slot 1 -> {want_slot(b, pal, 0, 1.0)} (want slot 1, then stay)")
    got = want_slot(b, palette(s0=["dmr", "magnum"]), 0, 1.0)
    if not got or got[0] == 0 or got[1] != "liked":
        fails.append(f"a BR lover with only the DMR slot known -> {got} (want an unseen slot)")
    b = bot("top")
    b.liked = ["battle_rifle", "dmr"]
    b.deaths = [death(1, "battle_rifle", "sniper", 30.0, slot=1)]
    pal = palette(s0=["dmr", "magnum"], s1=["battle_rifle", "magnum"], s2=["sniper", "magnum"])
    got = want_slot(b, pal, 1, 5.0)
    if not got or got[1] != "outranged" or want_slot(b, pal, got[0], 9.0):
        fails.append("after a problem switch the bot went back to its favourite")

    # 4. record_death: the enemy that hurt it last, the distance, both guns, the slot
    b = bot("top")
    b.last_pos, b.last_weapon, b.slot = Vec(0.0, 0.0, 0.0), "assault_rifle", 0
    b.per.attacker_id, b.per.attacker_t = 2, 9.5
    killer = PlayerState(2, 1, "human", Vec(12.0, 0.0, 0.0), alive=True, weapon="dmr")
    record_death(b, 10.0, Snapshot(10.0, [PlayerState(1, 0, "bot", Vec(), alive=False), killer]))
    d = b.deaths[-1]
    if (d["theirs"], round(d["d"], 1), d["mine"], d["slot"], death_kind(d)) != ("dmr", 12.0, "assault_rifle", 0, "outranged"):
        fails.append(f"record_death {d}")

    # 5. the live glue: spawns teach the palette, a death asks for the slot, a refusal turns it off
    import live_bots

    class FakeLive:
        slots = {1: 0, 3: 1}
        def loadout(s, index):
            return s.slots.get(index)

    def ps(alive1, w1=("assault_rifle", "magnum")):
        return Snapshot(0.0, [PlayerState(1, 0, "bot", Vec(), alive=alive1, weapon=w1[0], weapons=list(w1)),
                              PlayerState(3, 0, "bot", Vec(), alive=True, weapon="dmr", weapons=["dmr", "magnum"]),
                              PlayerState(2, 1, "human", Vec(15.0, 0.0, 0.0), alive=True, weapon="dmr")])
    b1, b3 = bot("top", 1), bot("top", 3)
    pal, state, asked = Palette(), {}, []
    for t in (0.0, 0.5, 1.2):
        live_bots.loadout_check(FakeLive(), lambda i, sl: asked.append((i, sl)) or True, {1: b1, 3: b3}, pal, state, ps(True), t)
    if pal.seen != {0: ("assault_rifle", "magnum"), 1: ("dmr", "magnum")}:
        fails.append(f"live: palette from spawns {pal.seen}")
    b1.last_pos, b1.last_weapon = Vec(), "assault_rifle"
    b1.per.attacker_id, b1.per.attacker_t = 2, 1.9
    live_bots.loadout_check(FakeLive(), lambda i, sl: asked.append((i, sl)) or True, {1: b1, 3: b3}, pal, state, ps(False), 2.0)
    if asked != [(1, 1)]:
        fails.append(f"live: a top bot outranged with an AR asked {asked} (want [(1, 1)])")
    live_bots.loadout_check(FakeLive(), lambda i, sl: asked.append((i, sl)) or True, {1: b1, 3: b3}, pal, state, ps(False), 2.1)
    if len(asked) != 1:
        fails.append(f"live: asked again while still dead {asked}")
    b5 = bot("top", 5)
    b5.deaths = [death(1, "assault_rifle", "dmr", 15.0)]
    pal2, st2 = palette(s0=["assault_rifle", "magnum"], s1=["dmr", "magnum"]), {5: dict(alive=False, born=None, asked=None)}
    snap5 = Snapshot(3.0, [PlayerState(5, 0, "bot", Vec(), alive=False)])
    live_bots.loadout_check(FakeLive(), lambda i, sl: False, {5: b5}, pal2, st2, snap5, 3.0)
    if not pal2.off:
        fails.append("live: a refused request did not turn loadouts off")
    # ... slots alike in the gun: the one whose ability its team carries least, so a team's kits vary (guide 20 review,
    #     103 of 105 requests "liked", a tie always the lowest slot; the player: one Elite used camo).
    #     The enemy's abilities do not count; with the team's counts alike it keeps the slot it has
    pal3 = Palette()
    for slot, ab in ((0, "sprint"), (1, "jetpack"), (2, "armor_lock")):
        pal3.learn(slot, ["dmr", "magnum"], ab)
    for kits, have, want in ((("sprint", "jetpack"), None, [(7, 2)]), (("sprint", "jetpack", "armor_lock"), 1, [])):
        b7 = bot("top", 7)
        b7.liked, b7.slot = ["dmr", "battle_rifle"], have
        snap7 = Snapshot(5.0, [PlayerState(7, 0, "bot", Vec(), alive=False)] +
                         [PlayerState(8 + n, 0, "bot", Vec(), equipment=k) for n, k in enumerate(kits)] +
                         [PlayerState(2, 1, "human", Vec(), equipment="armor_lock")])
        asked = []
        live_bots.loadout_check(FakeLive(), lambda i, sl: asked.append((i, sl)) or True, {7: b7}, pal3,
                                {7: dict(alive=False, born=None, asked=None)}, snap7, 5.0)
        if asked != want:
            fails.append(f"a DMR lover in slot {have}, slots 0-2 DMR, the team on {kits}: asked {asked} (want {want})")

    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("loadouts OK")


if __name__ == "__main__":
    main()
