"""Scaling difficulty (brain/scaling.py; after 5 games: Legendary's behaviour, only reaction / accuracy scale, a lock,
custom profiles, and ).

1. the hands: at 300% the reaction time, aim error and tremor are a third of the baseline's; at 10% ten times worse
   (no floor down); reaction, tracking and decisions go no quicker than one 30 Hz tick, the rest keep improving past
   660% (no cap, at 2.5x his teammates' kills against capped bots); the turn speed grows with the
   rating up to twice Legendary's (2000 deg/s) and no further; chances missed shrink and never reach certain
2. a bot made at any rating plays Legendary's game (tier top: motion tracker, tactics, routes, teamwork at Legendary's)
   with the rated settings, its tier-table settings in .extra; game sense (memory, callout hearing, shots before moving
   on) is Legendary's up to 150% and grows past it above (300%: memory twice Legendary's, hearing and shots half)
3. update() on Scaling games in a scratch folder: none -> 100%; K/D 1.0 keeps it; 3.5 -> 350%; 0.5 -> 50%; newer games
   weigh more; uncounted games ignored; a game counts once
4. the top, MAX (1800%), the bots' best: a steady 2.6 K/D climbs to it and stays (no compounding: it read 5016%,
   ), the hover says "(max)", a game recorded higher counts at MAX,
   settings past it are MAX's; one 0.5 K/D game halves it at once (games averaged 1)
5. it evens out: a 400% player brings the bots to within 5% of 400% in 10 games
6. the games averaged (botcore.ini scale_games=, 1-20) and the hover view (LF only, a block per N, every PARAMS row)
7. the Advanced tab's file (native/bin/scaling.ini): lock and rating, the profile in use and its weights; locked, the
   bots play at the locked rating and the games' own rating is untouched; a weight moves only its setting
8. the panel's SP_KEY / SP_LABEL (native/bots_panel.cpp) are PARAMS' keys and labels, in order
9. the brain reads .extra in place of its tier tables (headshots, ram error, tremor, dry shots, hearing)

usage: python -I test_scaling.py      -> "scaling OK"
"""
import inspect
import json
import math
import os
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import scaling  # noqa: E402
from brain.profiles import CRAFT, HANDS, TIERS, TURN  # noqa: E402

PLAYER = ('<Player mXboxUserId="{xuid}" mGamertagText="{name}" mTeamId="{team}" mKills="{k}" mDeaths="{d}" '
          'mCompletedGame="{done}" mSecondsPlayed="600">')
N = [0]


def game(folder, kills, deaths, skill=1.0, on=True, done=1):
    N[0] += 1
    base = os.path.join(folder, f"trace_m_{N[0]:04d}")
    rows = PLAYER.format(xuid="0x0009000012345678", name="Owner", team=0, k=kills, d=deaths, done=done)
    rows += PLAYER.format(xuid="0xB07B07B000000001", name="Bot", team=1, k=deaths, d=kills, done=1)
    open(base + ".carnage.xml", "w").write('<MultiplayerCarnageReport><IsTeamsEnabled IsTeamsEnabled="true"/><Players>'
                                           + rows + "</Players></MultiplayerCarnageReport>")
    open(base + ".jsonl", "w").write((json.dumps(dict(t=0.0, scaling=skill)) + "\n" if on else "")
                                     + '{"t": 0.1, "world": []}\n')
    t = time.time() + N[0]
    os.utime(base + ".carnage.xml", (t, t))


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(b))


def main():
    fails = []
    flat = type("R", (), {"uniform": staticmethod(lambda a, b: 1.0)})()
    # 1
    v1, v3, v01 = scaling.values(1.0), scaling.values(3.0), scaling.values(0.1)
    v66, v30 = scaling.values(6.6), scaling.values(30.0)
    if not (close(v3["reaction"], HANDS["reaction"] / 3) and close(v3["aim_err"], HANDS["aim_err"] / 3)
            and close(v3["tremor_k"], 1 / 3)):
        fails.append(f"1. at 300%: reaction {v3['reaction']:.4f}, aim error {v3['aim_err']:.5f}")
    if not close(v01["reaction"], HANDS["reaction"] * 10):
        fails.append(f"1. at 10%: reaction {v01['reaction']:.3f} (want {HANDS['reaction'] * 10:.3f}: no floor down)")
    if not (all(close(v30[k], 1 / 30) and close(v66[k], 1 / 30) for k in ("reaction", "track", "decide"))
            and v3["reaction"] > v66["reaction"] and v30["aim_err"] < v66["aim_err"] < v3["aim_err"]
            and v30["tremor_k"] < v66["tremor_k"] and v30["head_aim"] > v66["head_aim"]):
        fails.append(f"1. one tick for reaction / tracking / decisions ({v30['reaction']:.4f}), the rest still improving past "
                     f"660% (aim {v66['aim_err']:.5f} -> {v30['aim_err']:.5f})")
    if not (close(v1["turn"], TURN["average"]) and close(v30["turn"], 2 * TURN["top"])
            and v1["turn"] < scaling.values(1.5)["turn"] < v30["turn"]):
        fails.append(f"1. turn speed {math.degrees(v1['turn']):.0f} / {math.degrees(v30['turn']):.0f} deg/s (want "
                     f"Normal's at 100%, twice Legendary's at most)")
    if not (v30["head_aim"] < 1.0 and v30["head_aim"] > v3["head_aim"] > v1["head_aim"] and v01["head_aim"] == 0.0):
        fails.append("1. headshot chance not climbing toward (and short of) certain")
    # 2
    for r in (0.3, 1.0, 4.0):
        p = scaling.profile(r, "rusher", flat)
        legend = {**TIERS["top"], **CRAFT["top"]}
        game_sense = ("radar", "teamwork", "jump", "strafe", "juke", "routes", "map_iq", "tactics", "aware")
        if p.tier != "top" or any(getattr(p, k) != legend[k] for k in game_sense):
            fails.append(f"2. a bot at {100 * r:.0f}% does not play Legendary's game ({p.tier})")
        vr = scaling.values(r)
        if not (close(p.reaction, vr["reaction"]) and close(p.turn, vr["turn"]) and close(p.extra["head_aim"], vr["head_aim"])
                and set(p.extra) == set(scaling.EXTRA)):
            fails.append(f"2. a bot at {100 * r:.0f}% does not carry the rated hands")
    sense = {r: scaling.values(r) for r in (0.3, 1.5, 3.0, 30.0)}
    if not (all(close(sense[r]["memory"], TIERS["top"]["memory"]) and close(sense[r]["hear"], 0.15)
                and close(sense[r]["dry_shots"], 12.0) for r in (0.3, 1.5))
            and close(sense[3.0]["memory"], 2 * TIERS["top"]["memory"]) and close(sense[3.0]["hear"], 0.075)
            and close(sense[3.0]["dry_shots"], 6.0) and sense[30.0]["dry_shots"] == 1.0
            and sense[30.0]["memory"] > sense[3.0]["memory"]):
        fails.append(f"2. game sense: memory {[round(sense[r]['memory'], 1) for r in sense]} (want Legendary's to 150%, then "
                     f"growing), shots {[sense[r]['dry_shots'] for r in sense]}")
    from brain.bot import Bot as _B
    from brain.callouts import TIMING
    if TIMING["top"]["hear"] != 0.15 or _B.DRY_SHOTS["top"] != 12:
        fails.append("2. Legendary's callout hearing or dry-shot limit moved: brain/scaling.py PARAMS copies them")
    # 3
    d = tempfile.mkdtemp()
    s0 = scaling.update(d)["skill"]
    game(d, 10, 10)
    even = scaling.update(d)["skill"]
    d2 = tempfile.mkdtemp()
    game(d2, 35, 10)
    god = scaling.update(d2)["skill"]
    d3 = tempfile.mkdtemp()
    game(d3, 5, 10)
    low = scaling.update(d3)["skill"]
    if not (s0 == 1.0 and close(even, 1.0) and close(god, 3.5) and close(low, 0.5)):
        fails.append(f"3. none {s0}, K/D 1.0 {even}, 3.5 {god}, 0.5 {low} (want 1, 1, 3.5, 0.5)")
    d5 = tempfile.mkdtemp()
    game(d5, 10, 10, skill=1.0)
    game(d5, 40, 10, skill=1.0)
    w = scaling.update(d5)["skill"]
    if not close(w, 4.0 ** (2 / 3)):
        fails.append(f"3. newer weighs more: {w:.3f} (want {4.0 ** (2 / 3):.3f})")
    d6 = tempfile.mkdtemp()
    game(d6, 30, 5, on=False)
    game(d6, 1, 1)
    game(d6, 20, 2, done=0)
    a = scaling.update(d6)
    game(d6, 20, 10)
    b = scaling.update(d6)
    c = scaling.update(d6)
    if a["skill"] != 1.0 or a["games"] or len(c["games"]) != 1 or c["skill"] != b["skill"]:
        fails.append(f"3. uncounted games moved it ({a['skill']}), or a game counted twice ({len(c['games'])})")
    # 4. the top
    d4, s, seen = tempfile.mkdtemp(), 1.0, []
    for _ in range(12):
        game(d4, 26, 10, skill=s)                       # a steady 2.6
        s = scaling.update(d4, n=10)["skill"]
        seen.append(s)
    view = open(os.path.join(d4, scaling.VIEW), encoding="utf-8").read()
    if max(seen) > scaling.MAX + 1e-9 or not close(seen[-1], scaling.MAX) or "skill|1800% (max)" not in view:
        fails.append(f"4. a steady 2.6 K/D: {[round(100 * x) for x in seen]}% (want up to {100 * scaling.MAX:.0f}% and "
                     f"held, the hover saying (max))")
    if scaling.values(50.0) != scaling.values(scaling.MAX) or not close(scaling.next_skill(
            [dict(skill=50.0, kills=10, deaths=10)], 1), scaling.MAX):
        fails.append("4. past MAX: the settings or a game recorded at 5000% are not MAX's")
    game(d4, 10, 20, skill=s)
    back = scaling.update(d4, n=1)["skill"]
    if not close(back, scaling.MAX / 2):
        fails.append(f"4. one 0.5 K/D game at the top: {100 * back:.0f}% (want {50 * scaling.MAX:.0f}%)")
    # 5
    d7, own, s = tempfile.mkdtemp(), 4.0, 1.0
    for _ in range(10):
        kd = own / scaling.level(s)
        game(d7, round(kd * 20), 20, skill=s)
        s = scaling.update(d7)["skill"]
    if abs(s - own) / own > 0.05:
        fails.append(f"5. after 10 games {100 * s:.0f}% (want 400% +- 5%)")
    # 6
    ini = os.path.join(tempfile.mkdtemp(), "botcore.ini")
    open(ini, "w").write("enabled=1\nscale_games=3\n")
    n3 = scaling.games_window(ini)
    open(ini, "w").write("scale_games=99\n")
    n99 = scaling.games_window(ini)
    if (n3, n99, scaling.games_window(ini + ".missing")) != (3, 20, scaling.GAMES):
        fails.append(f"6. games_window: {n3}, {n99} (want 3, 20, {scaling.GAMES})")
    d8 = tempfile.mkdtemp()
    for k, dd in ((10, 10), (10, 10), (40, 10)):
        game(d8, k, dd, skill=1.0)
    one_game = scaling.update(d8, n=1)["skill"]
    st = scaling.update(d8, n=3)
    if not close(one_game, 4.0) or not close(st["skill"], 4.0 ** 0.5):
        fails.append(f"6. last 1 game {one_game:.3f} (want 4.0), last 3 {st['skill']:.3f} (want 2.0)")
    raw = open(os.path.join(d8, scaling.VIEW), "rb").read()
    text = raw.decode()
    blk = text.split("[3]\n")[1].split("[4]\n")[0].splitlines() if "[3]\n" in text else []
    rows = {r.split("|")[1]: r.split("|")[2:] for r in blk if r.startswith("row|")}
    if (b"\r" in raw or "[20]\n" not in text or "lock|0" not in text or "used|3" not in blk or "kd|2.00" not in blk
            or "skill|200%" not in blk or rows.get("Reaction time", [None])[0] != "200%"
            or rows.get("Memory", [None, ""])[1] != "13 s"
            or len(rows) != len(scaling.PARAMS)):
        fails.append(f"6. the hover view for 3 games: {blk[:5]}, reaction {rows.get('Reaction time')}, {len(rows)} rows, "
                     f"CR in file {chr(13).encode() in raw}")
    # 7. the Advanced tab's file
    sini = os.path.join(tempfile.mkdtemp(), "scaling.ini")
    open(sini, "w").write("lock=1\nrating=900\nuse=2\nprofile=A|reaction=50\nprofile=Aim first|aim=150|turn=80\n")
    cfg = scaling.settings(sini)
    if not (cfg["lock"] and close(cfg["rating"], 9.0) and cfg["name"] == "Aim first"
            and cfg["weights"] == {"aim": 1.5, "turn": 0.8}):
        fails.append(f"7. settings(): {cfg}")
    if scaling.settings(sini + ".missing") != dict(lock=False, rating=None, name="", weights={}):
        fails.append("7. no file: not Standard and unlocked")
    st = scaling.update(d8, n=3, cfg=cfg)
    if not (close(st["play"], 9.0) and close(st["skill"], 2.0) and close(scaling.load(d8)["skill"], 2.0)):
        fails.append(f"7. locked: plays {st['play']} (want 9.0), the games' rating {st['skill']} (want 2.0, kept)")
    wv, base = scaling.values(2.0, cfg["weights"]), scaling.values(2.0)
    if not (close(wv["aim_err"], base["aim_err"] / 1.5) and close(wv["reaction"], base["reaction"])
            and close(wv["turn"], TURN["average"] * 1.6)):
        fails.append("7. a weight moves more than its own setting, or not that one")
    # 8. the panel's table of settings
    cpp = open(os.path.join(HERE, "..", "native", "bots_panel.cpp"), encoding="utf-8").read()

    def arr(name):
        m = re.search(name + r"\[SP_N\] = \{(.*?)\};", cpp, re.S)
        return re.findall(r'"([^"]*)"', m.group(1)) if m else []
    if arr("SP_KEY") != [k for k, _, _ in scaling.PARAMS] or arr("SP_LABEL") != [lb for _, lb, _ in scaling.PARAMS]:
        fails.append(f"8. the panel's SP_KEY / SP_LABEL are not PARAMS': {arr('SP_KEY')}")
    # 9
    from brain.bot import Bot
    src = inspect.getsource(sys.modules[Bot.__module__])   # (Aim reads the tremor)
    from brain import director
    if any(f'extra or {{}}).get("{k}"' not in src for k in ("head_aim", "ram_err", "tremor_k", "dry_shots"))             or 'extra or {}).get("hear"' not in inspect.getsource(director):
        fails.append("9. the brain does not read head_aim / ram_err / tremor_k / dry_shots / hear from profile.extra")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("scaling OK (Legendary's game, rated hands and game sense up to the bots' best, held there, comes back down, lock and profiles, "
          "panel in step)")


if __name__ == "__main__":
    main()
