"""Offline checks for the player's brain notes: every tier has the same hands (reaction and aim) and
differs in behaviour; a bot commits to a kill (a 4 s loss of sight does not hand the fight to an
objective order); cover is situational (a losing bot with no cover near fights on, one with cover
right there breaks line of sight); a tactical bot recharges behind cover after a fight, a novice walks
on cracked; no item trips where bots cannot pick up; up close an automatic holds the trigger.

usage: python -I test_brain_tactics.py      -> "brain tactics OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import profiles  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
on_ground = lambda x, y: Vec(x, y, T.nav_z(x, y))
A, B = on_ground(70.0, -120.0), on_ground(58.0, -120.0)     # open gulch, 12 units apart


def snap(now, me_pos, foe_pos, me_id=1, yaw=3.14159, pitch=0.0, me_shield=1.0, me_health=1.0, foe_shield=1.0):
    me = PlayerState(me_id, 0, "bot", me_pos, yaw=yaw, pitch=pitch, alive=True, shield=me_shield, health=me_health)
    foe = PlayerState(2, 1, "human", foe_pos, alive=True, shield=foe_shield)
    return Snapshot(now, [me, foe])


def run(bot, t0, t1, me_pos, foe_pos, los=T.los, **kw):
    goals, t, yaw, pitch = [], t0, 3.14159, 0.0
    while t < t1:
        a = bot.think(t, 1 / 30, snap(t, me_pos, foe_pos, bot.id, yaw, pitch, **kw), los, lambda a, b, **k: b, [])
        yaw, pitch = a.yaw, a.pitch
        goals.append(bot.goal)
        t += 1 / 30
    return goals


def main():
    fails = []
    # 1. the same hands for every tier, but reaction (the player: Easy x1.25, Normal x1, Heroic x0.85,
    #    Legendary x0.7 of a good human's)
    #    ... and sharper hands from Heroic up:
    #    Easy and Normal the same, then each tier at least as quick and tight as the one below
    hands = ("track", "lead", "overshoot", "aim_err", "decide", "lag", "flick")
    order = ("novice", "average", "strong", "top")
    for k in hands:
        vals = [profiles.TIERS[t][k] for t in order]
        if vals[0] != vals[1] or any(b > a for a, b in zip(vals, vals[1:])):
            fails.append(f"{k} by tier {dict(zip(order, vals))}: Easy = Normal, then never worse")
    if not profiles.TIERS["top"]["lag"] < profiles.TIERS["average"]["lag"]:
        fails.append("Legendary's hand is no quicker than Normal's")
    want = {"novice": 0.275, "average": 0.22, "strong": 0.187, "top": 0.154}
    got = {t: round(profiles.TIERS[t]["reaction"], 3) for t in want}
    if got != want:
        fails.append(f"reaction by tier {got}, want {want}")
    if len({profiles.CRAFT[t]["tactics"] for t in profiles.CRAFT}) < 3:
        fails.append("tactics does not separate the tiers")

    # 2. commit: a 4 s loss of sight does not hand the fight to the objective order
    bot = Bot(1, 0, make_profile("top", "objector", random.Random(1)), MAP, random.Random(1))
    bot.set_order(Order("mid", Vec(40.0, -80.0, 0.0)))
    run(bot, 0.0, 3.0, A, B)
    g = run(bot, 3.0, 7.0, A, B, los=lambda a, b: False)
    share = sum(1 for x in g if x[0] == "fight") / len(g)
    if share < 0.95:
        fails.append(f"fight share over a 4 s loss of sight {share:.2f} < 0.95 (goals {sorted(set(x[0] for x in g))})")

    # 3. cracked and losing in the open gulch (no cover within reach): fight on, do not run
    bot = Bot(3, 0, make_profile("top", "camper", random.Random(3)), MAP, random.Random(3))
    bot.cover_from = lambda me, threats: None
    g = run(bot, 0.0, 3.0, A, B, me_shield=0.0, me_health=0.5)
    if any(x[0] == "retreat" for x in g[30:]):
        fails.append("ran from a losing fight with no cover near")
    # ... and with cover 3 units away a top bot breaks line of sight
    bot = Bot(4, 0, make_profile("top", "camper", random.Random(4)), MAP, random.Random(4))
    near = A + Vec(0.0, 3.0, 0.0)
    bot.cover_from = lambda me, threats: near
    g = run(bot, 0.0, 3.0, A, B, me_shield=0.0, me_health=0.5)
    if not any(x[0] == "retreat" for x in g[30:]):
        fails.append("a top bot did not take the cover 3 units away in a losing fight")
    # ... a novice fights it out wherever it stands (its bad spot)
    bot = Bot(5, 0, make_profile("novice", "camper", random.Random(5)), MAP, random.Random(5))
    bot.cover_from = lambda me, threats: near
    g = run(bot, 0.0, 3.0, A, B, me_shield=0.0, me_health=0.5)
    if any(x[0] == "retreat" for x in g[30:]):
        fails.append("a novice used cover (novices fight it out)")

    # 4. after the fight (enemy gone from view), shield down: a top bot recharges behind cover near
    bot = Bot(6, 0, make_profile("top", "flanker", random.Random(6)), MAP, random.Random(6))
    bot.set_order(Order("mid", Vec(40.0, -80.0, 0.0)))
    bot.cover_from = lambda me, threats: near
    run(bot, 0.0, 1.5, A, B)                               # saw him
    g = run(bot, 1.5, 12.0, A, B, los=lambda a, b: False, me_shield=0.2)
    if not any(x[0] == "retreat" for x in g):
        fails.append("a top bot walked on cracked instead of recharging behind cover")
    # ... but not for minutes: 10 s after the last hit any Halo shield is back, whatever the reading says (Reach read
    #     0 shields all match on: Heroic / Legendary bots hid at cover 59-77% of the match, one for 264 s,
    #     a moving enemy on the radar keeping the fight "recent")
    bot = Bot(16, 0, make_profile("top", "flanker", random.Random(16)), MAP, random.Random(16))
    bot.set_order(Order("mid", Vec(40.0, -80.0, 0.0)))
    bot.cover_from = lambda me, threats: near
    run(bot, 0.0, 1.5, A, B)                               # saw him, then lost 0.8 of the shield at 1.5 s
    hid, t, yaw, pitch = [], 1.5, 3.14159, 0.0
    while t < 25.0:
        me = PlayerState(16, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=0.2, health=1.0)
        foe = PlayerState(2, 1, "human", B, vel=Vec(1.0, 0.0, 0.0), alive=True)     # moving: on the radar
        a = bot.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda a, b: False, lambda a, b, **k: b, [])
        yaw, pitch = a.yaw, a.pitch
        hid.append((t, bot.goal[0] == "retreat"))
        t += 1 / 30
    late = [h for tt, h in hid if tt > 14.0]
    shown_late = sum(late)
    # ... and in a match without shields (the player's two games were Team SWAT: every shield reads 0, so it was never
    #     "back") there is nothing to recharge: no recharge retreat after the fight, and a hit to the body is a hit
    swat = Bot(17, 0, make_profile("top", "flanker", random.Random(17)), MAP, random.Random(17))
    swat.set_order(Order("mid", Vec(40.0, -80.0, 0.0)))
    swat.cover_from = lambda me, threats: near
    hid2, t, yaw, pitch = [], 0.0, 3.14159, 0.0
    while t < 10.5:                                       # (past the fight commitment, inside the 10 s cap)
        me = PlayerState(17, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=0.0, health=1.0 if t < 1.0 else 0.7)
        foe = PlayerState(2, 1, "human", B, vel=Vec(1.0, 0.0, 0.0), alive=True, shield=0.0)
        see = (lambda a, b: True) if t < 1.5 else (lambda a, b: False)
        a = swat.think(t, 1 / 30, Snapshot(t, [me, foe], shieldless=True), see, lambda a, b, **k: b, [])
        yaw, pitch = a.yaw, a.pitch
        hid2.append((t, swat.goal[0] == "retreat"))
        t += 1 / 30
    if any(h for tt, h in hid2 if tt > 2.0) or not 0.95 <= getattr(swat, "hit_at", -9.0) <= 1.2:
        fails.append(f"no shields (SWAT): retreated after the fight {any(h for tt, h in hid2 if tt > 2.0)}, the body hit "
                     f"at 1.0 s seen at {getattr(swat, 'hit_at', None)} (want no retreat, the hit seen)")
    if not any(h for tt, h in hid if tt < 8.0) or shown_late > 0.1 * len(late):
        fails.append(f"recharge with a shield that never reads back: retreat before 8 s {any(h for tt, h in hid if tt < 8.0)}, "
                     f"after 14 s {sum(late)} of {len(late)} ticks (want a retreat, then out of it)")

    # 5. no item trips where pickups do not work (H2A / H4)
    bot = Bot(7, 0, make_profile("top", "flanker", random.Random(7)), MAP, random.Random(7))
    bot.can_pickup = False
    g = run(bot, 0.0, 3.0, A, A + Vec(200, 0, 0), los=lambda a, b: False)
    if any(x[0] == "item" for x in g):
        fails.append("an item trip in a game without pickups")

    # 6. he broke line of sight: a tactical bot chases by the nav (round the wall), a novice runs straight
    side = A + Vec(0.0, 6.0, 0.0)                          # the route bends north; he is due west
    for tier, want_nav in (("top", True), ("novice", False)):
        bot = Bot(8, 0, make_profile(tier, "rusher", random.Random(8)), MAP, random.Random(8))
        run(bot, 0.0, 1.5, A, B)
        asked = []
        nav = lambda p, q, **k: asked.append(q) or side
        t, yaw = 1.5, 3.14159
        while t < 2.6:
            a = bot.think(t, 1 / 30, snap(t, A, B, bot.id, yaw), lambda p, q: False, nav, [])
            yaw = a.yaw
            t += 1 / 30
        if bot.goal[0] != "fight":
            fails.append(f"{tier}: dropped the fight 1 s after losing sight")
        elif bool(asked) != want_nav:
            fails.append(f"{tier}: {'did not chase by' if want_nav else 'chased by'} the nav ({len(asked)} asks)")

    # 7. fighting one enemy while another, close, is the one shooting us: a top bot turns on the shooter,
    #    a novice keeps shooting the first (tunnel vision)
    import math
    C = A + Vec(-3.0, 1.0, 0.0)                            # the shooter, 3 units off, aiming at the bot
    c_yaw = math.atan2(A.y - C.y, A.x - C.x)
    for tier, want_switch in (("top", True), ("novice", False)):
        bot = Bot(9, 0, make_profile(tier, "rusher", random.Random(9)), MAP, random.Random(9))
        t, yaw, pitch, sh, goals = 0.0, 3.14159, 0.0, 1.0, []
        while t < 4.0:
            me = PlayerState(9, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=sh)
            foe_b = PlayerState(2, 1, "human", B, alive=True, yaw=0.0)             # the first, looking away
            foe_c = PlayerState(3, 1, "human", C, alive=True, yaw=c_yaw if t > 1.5 else c_yaw + 2.0)
            a = bot.think(t, 1 / 30, Snapshot(t, [me, foe_b, foe_c] if t > 1.5 else [me, foe_b]), T.los,
                          lambda p, q, **k: q, [])
            yaw, pitch = a.yaw, a.pitch
            if t > 1.5:
                sh = max(0.0, sh - (0.06 if int(t * 30) % 6 == 0 else 0.0))   # C hits us in bursts
            goals.append(bot.goal)
            t += 1 / 30
        late = goals[-30:]
        on_c = sum(1 for g in late if g == ("fight", 3)) / len(late)
        if want_switch and on_c < 0.8:
            fails.append(f"a top bot did not turn on the enemy shooting it (fight #3 {on_c:.0%} of the last second)")
        if not want_switch and on_c > 0.2:
            fails.append(f"a novice turned on the shooter ({on_c:.0%}): it should keep tunnel vision")

    # 8. the trigger by range:
    #    at Short band an automatic holds the trigger; a rifle is never held (a held semi-automatic fires
    #    once). What an automatic does at Medium band (taps before ffbfb4d, bursts since) awaits the player:
    #    tools/test_spec_pending.py
    def trigger(weapon, gap):
        bot = Bot(10, 0, make_profile("strong", "rusher", random.Random(10)), MAP, random.Random(10))
        foe = PlayerState(2, 1, "human", A + Vec(-gap, 0.0, 0.0), alive=True)
        t, yaw, pitch, fires = 0.0, 3.14159, 0.0, []
        while t < 4.0:
            me = PlayerState(10, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, weapon=weapon)
            a = bot.think(t, 1 / 30, Snapshot(t, [me, foe]), T.los, lambda p, q, **k: q, [])
            yaw, pitch = a.yaw, a.pitch
            fires.append((t, bool(a.fire)))
            t += 1 / 30
        fires = fires[60:]                                 # spotted, turned and on target by 2 s
        runs, n = [], 0
        for _, f in fires:
            n = n + 1 if f else 0
            runs.append(n)
        return max(runs), sum(f for _, f in fires) / len(fires)

    longest, down = trigger("smg", 3.0)
    if longest < 15 or down < 0.8:
        fails.append(f"an SMG at 3 units tapped (longest hold {longest} ticks, trigger down {down:.0%})")
    longest, down = trigger("battle_rifle", 3.0)
    if longest > 1 or down == 0:
        fails.append(f"a BR at 3 units: held {longest} ticks, trigger down {down:.0%} (want taps)")

    # 9. range bands are a Regular's rule and up: a shotgun in hand, a BR on the back, a man at 20 units:
    #    a top bot switches to the BR; a Recruit keeps the shotgun ("uses the AR at Long band", guide 01 s9)
    for tier, want in (("top", True), ("novice", False)):
        bot = Bot(11, 0, make_profile(tier, "rusher", random.Random(11)), MAP, random.Random(11))
        bot.can_pickup = False
        t, yaw, got = 0.0, 3.14159, []
        while t < 2.0:
            me = PlayerState(11, 0, "bot", A, yaw=yaw, alive=True, weapon="shotgun", weapons=["shotgun", "battle_rifle"])
            a = bot.think(t, 1 / 30, Snapshot(t, [me, PlayerState(2, 1, "human", A + Vec(-20.0, 0, 0), alive=True)]),
                          lambda p, q: True, lambda p, q, **k: q, [])   # (a hill hides him on the real gulch)
            yaw = a.yaw
            got.append(a.weapon)
            t += 1 / 30
        if (1 in got) != want:
            fails.append(f"{tier} with a shotgun at 20 units: switched to the BR = {1 in got}")

    # 10. a radar dot 3 units behind while fighting someone 10 off: Heroic and up check it, a Recruit
    #     tunnels (the player's Reach game: the player closed in on bots' radar unchecked)
    from brain.bot import Belief
    behind = A + Vec(3.0, 0.0, 0.0)                        # east; the bot faces west at B
    for tier, want in (("top", True), ("novice", False)):
        bot = Bot(12, 0, make_profile(tier, "rusher", random.Random(12)), MAP, random.Random(12))
        t, yaw, goals = 0.0, 3.14159, []
        while t < 3.0:
            me = PlayerState(12, 0, "bot", A, yaw=yaw, alive=True)
            foes = [PlayerState(2, 1, "human", B, alive=True, yaw=0.0), PlayerState(3, 1, "human", behind, alive=True, yaw=0.0)]
            if t > 1.5:
                bot.per.beliefs[3] = Belief(behind, Vec(), t, False, "radar")
            a = bot.think(t, 1 / 30, Snapshot(t, [me] + foes), lambda p, q: dist2(p, q) > 2.0 and q.x < A.x + 1,
                          lambda p, q, **k: q, [])
            yaw = a.yaw
            goals.append(bot.goal)
            t += 1 / 30
        # (a hunt toward the dot since: a "fight" on a man never seen flip-flopped and aimed into walls)
        checked = any(g == ("fight", 3) or (g[0] == "hunt" and (g[1] - behind).flat() < 1.0) for g in goals[50:])
        if checked != want:
            fails.append(f"{tier}: checked the radar dot 3 units behind mid-fight = {checked}")

    # 11. walking, nothing known: Heroic and up glance to the flanks now and then; a Recruit looks where it walks
    for tier, want in (("top", True), ("novice", False)):
        bot = Bot(13, 0, make_profile(tier, "rusher", random.Random(13)), MAP, random.Random(13))
        bot.goal, bot.next_decide = ("objective", A + Vec(-40.0, 0.0, 0.0)), 99.0
        t, yaw, offs = 0.0, 3.14159, []
        while t < 6.0:
            me = PlayerState(13, 0, "bot", A, yaw=yaw, alive=True)
            a = bot.think(t, 1 / 30, Snapshot(t, [me]), T.los, lambda p, q, **k: q, [])
            yaw = a.yaw
            offs.append(abs(math.atan2(math.sin(yaw - 3.14159), math.cos(yaw - 3.14159))))
            t += 1 / 30
        if (max(offs[30:]) > 0.5) != want:
            fails.append(f"{tier}: looked off its path by up to {max(offs[30:]):.2f} rad (flank checks = {want})")

    # 12. cracked and losing with cover 5 units off, but taking damage that kills in ~1 s: fight it out
    bot = Bot(14, 0, make_profile("top", "camper", random.Random(14)), MAP, random.Random(14))
    far_cover = A + Vec(0.0, 5.0, 0.0)
    bot.cover_from = lambda me, threats: far_cover
    t, yaw, goals, hp = 0.0, 3.14159, [], 0.8
    while t < 3.0:
        hp = max(0.3, hp - (0.02 if t > 1.0 else 0.0))     # (a slow drain the bot reads as heavy fire)
        bot.per.losses = [(t - 0.1 * k, 0.12) for k in range(10)] if t > 1.0 else []
        me = PlayerState(14, 0, "bot", A, yaw=yaw, alive=True, shield=0.0, health=hp)
        a = bot.think(t, 1 / 30, Snapshot(t, [me, PlayerState(2, 1, "human", B, alive=True)]), T.los,
                      lambda p, q, **k: q, [])
        yaw = a.yaw
        goals.append(bot.goal[0])
        t += 1 / 30
    if "retreat" in goals[45:]:
        fails.append("ran for cover 5 units off under fire that kills before it gets there")

    # 13. a kill under way is finished: fighting #2 (shield gone), #3 steps in aiming at us and hurting
    #     us; a top bot stays on #2. With #2 fresh, it turns on #3 once the target hold is over (the player's
    #     Settlement game: Legendary switched twice as often as Easy and won 11% of its fights to 26%)
    side = A + Vec(-10.0, 3.0, 0.0)
    for cracked, want in ((True, 2), (False, 3)):
        bot = Bot(15, 0, make_profile("top", "rusher", random.Random(15)), MAP, random.Random(15))
        t, yaw, pitch, goals, sh = 0.0, 3.14159, 0.0, [], 1.0
        while t < 4.0:
            late = t > 1.5
            sh = max(0.3, sh - 0.01) if late else 1.0
            me = PlayerState(15, 0, "bot", A, yaw=yaw, pitch=pitch, alive=True, shield=sh)
            foes = [PlayerState(2, 1, "human", B, alive=True, yaw=3.14159, shield=0.0 if late and cracked else 1.0)]
            if late:
                foes.append(PlayerState(3, 1, "human", side, alive=True, yaw=math.atan2(A.y - side.y, A.x - side.x),
                                        pitch=-0.03))
            a = bot.think(t, 1 / 30, Snapshot(t, [me] + foes), lambda p, q: True, lambda p, q, **k: q, [])
            yaw, pitch = a.yaw, a.pitch
            if t > 3.0:
                goals.append(bot.goal)
            t += 1 / 30
        held = sum(1 for g in goals if g == ("fight", want)) / max(1, len(goals))
        if held < 0.9:
            fails.append(f"#2 {'cracked' if cracked else 'fresh'}, #3 shooting us: on #{want} only {held:.0%} of the time")

    # 14. no solo chase: alone with a radar dot 15 units off and a post to hold, a top bot holds; with a
    #     mate beside it, it hunts (guide 07 Team Slayer: "never by a solo chase"); with a mate in a lobby
    #     of three teams it holds (FFA: the third party wins the fight you start)
    dot = A + Vec(-15.0, 0.0, 0.0)
    for mate, third, want in ((False, False, "objective"), (True, False, "hunt"), (True, True, "objective")):
        bot = Bot(16, 0, make_profile("top", "rusher", random.Random(16)), MAP, random.Random(16))
        bot.set_order(Order("mid", A + Vec(0.0, 10.0, 0.0)))
        bot.can_pickup = False
        t, yaw, goals = 0.0, 3.14159, []
        while t < 3.0:
            me = PlayerState(16, 0, "bot", A, yaw=yaw, alive=True)
            players = [me, PlayerState(2, 1, "human", dot, alive=True)]
            if mate:
                players.append(PlayerState(17, 0, "mate", A + Vec(0.0, 2.0, 0.0), alive=True))
            if third:
                players.append(PlayerState(19, 2, "green", A + Vec(30.0, 30.0, 0.0), alive=True))
            bot.per.beliefs[2] = Belief(dot, Vec(), t, False, "radar")
            a = bot.think(t, 1 / 30, Snapshot(t, players), lambda p, q: False, lambda p, q, **k: q, [])
            yaw = a.yaw
            goals.append(bot.goal[0])
            t += 1 / 30
        share = goals[15:].count(want) / len(goals[15:])
        if share < 0.8:
            fails.append(f"top bot {'with a mate' if mate else 'alone'}{', three teams' if third else ''}, radar dot "
                         f"15 off: {want} only {share:.0%}")

    # 15. melee at arm's length is a press per swing, not a held bit; on the lower shield no trade for Easy only (Normal
    #     and up melee whenever in reach since)
    for tier, my_shield, lo, hi in (("average", 1.0, 3, 6), ("average", 0.2, 3, 6), ("novice", 0.2, 0, 0)):
        bot = Bot(18, 0, make_profile(tier, "rusher", random.Random(18)), MAP, random.Random(18))
        t, yaw, presses, held = 0.0, 3.14159, 0, 0
        prev = False
        while t < 4.0:
            me = PlayerState(18, 0, "bot", A, yaw=yaw, alive=True, shield=my_shield)
            a = bot.think(t, 1 / 30, Snapshot(t, [me, PlayerState(2, 1, "human", A + Vec(-1.0, 0, 0), alive=True)]),
                          lambda p, q: True, lambda p, q, **k: q, [])
            yaw = a.yaw
            if t > 1.0:
                presses += bool(a.melee) and not prev
                held += bool(a.melee) and prev
            prev = bool(a.melee)
            t += 1 / 30
        if not lo <= presses <= hi or held:
            fails.append(f"{tier} melee at 1 unit, my shield {my_shield}: {presses} presses in 3 s, {held} held ticks "
                         f"(want {lo}-{hi}, none held)")

    # 16. where a DMR aims: Easy at the chest ~80% of fights (was ~65%), shield or not; the rest center
    #     of mass until the shield pops, then the head about half the time (Normal) to near always (guide 03)
    want = {"novice": (0.20, 0.20), "average": (0.0, 0.5), "strong": (0.0, 0.9), "top": (0.0, 0.97)}   # Easy 20%
    for tier, (up, popped) in want.items():
        bot = Bot(20, 0, make_profile(tier, "rusher", random.Random(20)), MAP, random.Random(20))
        me = PlayerState(20, 0, "bot", A, alive=True, weapon="dmr")
        for shield, share in ((1.0, up), (0.0, popped)):
            heads = sum(bot.aim_head(0.0, me, PlayerState(100 + k, 1, "foe", B, alive=True, shield=shield), 100 + k)
                        for k in range(600))
            if abs(heads / 600 - share) > 0.07:
                fails.append(f"{tier} DMR, his shield {shield}: head {heads / 600:.0%} of fights (want ~{share:.0%})")

    # 17. one switch for range a fight: rockets and a needle rifle, the man hovering 2.5-3.5 units off for 8 s:
    #     at most one swap (live, Boardwalk: rockets <-> needle rifle every 2 s)
    bot = Bot(21, 0, make_profile("top", "rusher", random.Random(21)), MAP, random.Random(21))
    bot.can_pickup = False
    held, swaps, t, yaw = "rockets", 0, 0.0, 3.14159
    while t < 8.0:
        foe_at = A + Vec(-(2.5 if int(t) % 2 else 3.5), 0.0, 0.0)
        me = PlayerState(21, 0, "bot", A, yaw=yaw, alive=True, weapon=held, weapons=["rockets", "needle_rifle"])
        a = bot.think(t, 1 / 30, Snapshot(t, [me, PlayerState(2, 1, "human", foe_at, alive=True)]),
                      lambda p, q: True, lambda p, q, **k: q, [])
        yaw = a.yaw
        if a.weapon >= 0 and ["rockets", "needle_rifle"][a.weapon] != held:
            held, swaps = ["rockets", "needle_rifle"][a.weapon], swaps + 1
        t += 1 / 30
    if swaps > 1:
        fails.append(f"a man hovering at 2.5-3.5 units: {swaps} weapon swaps in 8 s (want 1 at most)")

    # 18. a radar dot 3 units off while fighting a man 4 units off: no turn (he is not much closer); the
    #     dot-check of 10 (fighting a man 12 off) still turns
    bot = Bot(22, 0, make_profile("top", "rusher", random.Random(22)), MAP, random.Random(22))
    near_foe, side_dot = A + Vec(-4.0, 0.0, 0.0), A + Vec(0.0, 3.0, 0.0)
    t, yaw, goals = 0.0, 3.14159, []
    while t < 3.0:
        me = PlayerState(22, 0, "bot", A, yaw=yaw, alive=True)
        foes = [PlayerState(2, 1, "human", near_foe, alive=True, yaw=0.0), PlayerState(3, 1, "human", side_dot, alive=True)]
        if t > 1.5:
            bot.per.beliefs[3] = Belief(side_dot, Vec(), t, False, "radar")
        a = bot.think(t, 1 / 30, Snapshot(t, [me] + foes), lambda p, q: dist2(p, q) > 2.0 and q.y < A.y + 1,
                      lambda p, q, **k: q, [])
        yaw = a.yaw
        goals.append(bot.goal)
        t += 1 / 30
    if any(g == ("fight", 3) for g in goals[50:]):
        fails.append("turned from a man 4 units off to a radar dot 3 units off (not much closer)")

    # 19. accuracy: 0.3 units off his
    #     body at 10 units is not on target (it was), 0.05 is; strafing 2.25 u/s past a man standing 2 units off,
    #     the aim comes from where the eye will be when the shot leaves, not where it is
    from brain.bot import Aim
    aim = Aim(make_profile("average", "rusher", random.Random(23)), random.Random(23))
    aim.goal = (0.0, 0.0)
    me = PlayerState(23, 0, "bot", Vec(0.0, 0.0, 0.0), yaw=0.0, alive=True)
    if aim.on_target(me, Vec(10.0, 0.0, 0.0), math.atan2(0.3, 10.0), 0.0):
        fails.append("on target with the crosshair 0.3 units off his body at 10 units")
    if not aim.on_target(me, Vec(10.0, 0.0, 0.0), math.atan2(0.05, 10.0), 0.0):
        fails.append("not on target with the crosshair 0.05 units off his middle at 10 units")
    aim = Aim(make_profile("average", "rusher", random.Random(24)), random.Random(24))
    me = PlayerState(24, 0, "bot", Vec(0.0, 0.0, 0.0), yaw=0.0, alive=True, vel=Vec(0.0, 2.25, 0.0))
    for k in range(10):
        aim.step(k / 30, 1 / 30, me, 2, Vec(2.0, 0.0, 0.0), Vec(), False)
    if not aim.goal[0] < -0.03:
        fails.append(f"strafing past a man standing still: aimed at yaw {aim.goal[0]:.3f} (want about -0.056: "
                     f"from where the eye will be)")

    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("brain tactics OK")


def dist2(p, q):
    return ((p.x - q.x) ** 2 + (p.y - q.y) ** 2) ** 0.5


if __name__ == "__main__":
    main()
