"""Every sim mode on representative maps of every game.

Each (mode, map) runs 4 v 4 Legendary in the offline sim (brain/sim.py, brain/sim_modes.py) for a few seeds. Per run:
each team's points a minute, the objective's takes per team (CTF flag pulls and captures, hill or ball seconds and
takes, territories taken, bombs picked up and planted, Stockpile flags, skulls banked, Invasion phases and cores, VIP
kills), kills a minute per team, and the share of living bot time
  fight   its goal is a fight or a retreat from one, or it fires
  obj     it carries the objective or its goal is the objective (walking to it, holding it)
  walk    moving (over 0.5 u/s) on another goal (hunting, items, roaming)
  idle    standing on another goal
  stuck   its unstuck wiggle is on (Bot.unstuck: it pushed and went nowhere)
Verdict per run, the worst of its seeds for the row:
  SCORING     the score moved (any team)
  AGGRESSIVE  no score, but both teams kill at least KPM_BAR a minute
  BROKEN      neither
A row flags "one-sided" when one team never scored in any seed (Slayer aside), "low fight" when a team kills under
KPM_BAR a minute, and "idle" when idle + stuck is over IDLE_BAR of the bots' time.

usage: python -I mode_matrix.py [--modes ctf,king] [--games ce,h3] [--maps a,b] [--seeds 2] [--seconds S]
                                [--per-team 4] [--tier top] [--procs 2] [--out logs/mode_matrix.md] [--resume] [--table-only]
       -> one line per run as it ends (kept in <out>.runs.jsonl: --resume skips those), then the table to --out
          (overwritten) and its rows to <out>.json
"""
import argparse
import json
import multiprocessing
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

KPM_BAR = 2.0      # kills a minute a team, 4 v 4: half a person's Team Slayer pace (about 1 a player a minute)
IDLE_BAR = 0.30
# representative maps by game (in-game names: The Pit = h3_cyberdyne, Avalanche = h3_sidewinder, Spire = reach_35_island)
GAMES = {
    "ce": ["bloodgulch", "beavercreek", "prisoner"],
    "h2": ["h2_ascension", "h2_beavercreek", "h2_lockout"],
    "h3": ["h3_cyberdyne", "h3_sidewinder", "h3_construct"],
    "reach": ["reach_30_settlement", "reach_35_island", "reach_70_boneyard"],
    "h4": ["h4_ca_warhouse", "h4_ca_tower", "h4_ca_canyon"],
    "h2a": ["h2a_ca_ascension", "h2a_ca_lockout", "h2a_ca_coagulation"],
}
# carry modes run longer: a capture is a trip there and back (the first 180 s pass: 4 of 18 CTF games scored; the
# player's live Halo 3 CTF games ran 676 and 1,294 s)
LONG = {"ctf": 300.0, "one_flag": 300.0, "assault": 300.0, "stockpile": 300.0, "invasion": 300.0}
MODES = ["slayer", "ctf", "one_flag", "king", "crazy_king", "oddball", "vip", "territories", "assault", "stockpile", "headhunter",
         "invasion"]


def objects(name):
    """The map's scenario objects with Halo 3's names made Reach's (as brain/maps.load_map), without its terrain: the
    parent process stays small (a run of the whole matrix died of OpenBLAS out of memory with every map loaded in
    each process)."""
    from brain.maps import H3_TYPES
    objs = json.load(open(os.path.join(ROOT, "maps", name, "objects.json"), encoding="utf-8"))
    for f in objs.get("netgame_flags", []):
        f["type"] = H3_TYPES.get(f["type"], f["type"])
    return objs


def supports(mode, objs, name=""):
    """Whether the map's data lets the sim play the mode (King and Oddball fall back to the mid: always)."""
    from brain import modes as MD
    if mode in ("slayer", "king", "crazy_king", "oddball", "vip"):
        return True
    if mode in ("ctf", "one_flag"):
        return {f["id"] for f in objs.get("netgame_flags", []) if f["type"] == "ctf - flag"} >= {0, 1}
    if mode == "invasion":
        from brain import invasion
        return invasion.layout(objs) is not None
    lay = MD.layout(objs)
    if mode == "territories":
        return bool(lay.get("territory"))
    if mode == "assault":
        # (the CTF stands stand in for Halo 3's bombs only: Halo 4 has no Assault, Halo 2's names its own places)
        return bool(lay.get("bomb") or (name.startswith("h3_") and lay.get("ctf_stand"))) and bool(lay.get("bomb_goal"))
    if mode == "stockpile":
        return bool(lay.get("stockpile_flag")) and bool(lay.get("stockpile_goal"))
    if mode == "headhunter":
        return bool(lay.get("drop_point"))
    return False


def side_of(text):
    """The team an objective event is about: "team N ...", a player's name (R.. / B..), "attackers" (sim team 1)."""
    m = re.match(r"team (\d)", text)
    if m:
        return int(m.group(1))
    if text.startswith("attackers"):
        return 1
    if text[:1] in "RB" and text[1:2].isdigit():
        return "RB".index(text[0])
    return None


def kind_of(text):
    """The event without who did it or which zone: "took the ball", "took territory", "planted the bomb"."""
    text = re.sub(r"^(team \d |[RB]\d+-\S+ |attackers )", "", text)
    return re.sub(r"\s*\(?(territory )?\d+\)?$", "", re.sub(r" territory \d+", " territory", text))


def play(job):
    """One game: its numbers (a dict)."""
    mode, name, seed, seconds, n, tier = job
    from brain.core import TICK
    from brain.sim import Sim
    t0 = time.monotonic()
    sim = Sim("ctf" if mode == "one_flag" else mode, per_team=n, seed=seed, map_name=name, tiers=[tier])
    if mode == "one_flag":           # (master 5008de4: Sim.set_one_flag, the sides swap at a capture or 180 s)
        sim.set_one_flag(0, 180.0)
    act = dict(fight=0, obj=0, walk=0, idle=0, stuck=0)
    for _ in range(int(seconds / TICK)):
        sim.step()
        for p in sim.players:
            if not p.alive:
                continue
            b, a = sim.bots[p.id], sim.last_actions[p.id]
            g = b.goal[0] if isinstance(b.goal, tuple) else None
            if getattr(b, "wiggle_until", 0.0) > sim.now:
                act["stuck"] += 1
            elif g in ("fight", "retreat") or a.fire:
                act["fight"] += 1
            elif p.has_flag or g == "objective":
                act["obj"] += 1
            elif p.vel.flat() > 0.5:
                act["walk"] += 1
            else:
                act["idle"] += 1
    minutes = sim.now / 60.0
    kills = {0: 0, 1: 0}
    for pid, st in sim.stats.items():
        kills[sim.players[pid].team] += st["kills"]
    takes = {}
    for t, what, team in sim.flag_events:             # CTF
        takes.setdefault({"taken": "flag pulls", "captured": "captures", "returned": "returns",
                       "round": "rounds defended (ended)"}.get(what, what), [0, 0])[team] += 1
    om = sim.objmodes
    for t, text in (om.events if om is not None else []):
        team = side_of(text)
        if team is not None:
            takes.setdefault(kind_of(text), [0, 0])[team] += 1
    if om is not None and hasattr(om, "owned") and mode in ("king", "crazy_king", "oddball"):
        takes["hill s" if mode != "oddball" else "ball s"] = [round(om.owned[0]), round(om.owned[1])]
        if mode != "oddball":
            takes["contested s"] = [round(om.contested), round(om.contested)]
    live = max(1, sum(act.values()))
    score = dict(sim.score)
    kpm = [kills[0] / minutes, kills[1] / minutes]
    verdict = "SCORING" if sum(score.values()) > 0 else "AGGRESSIVE" if min(kpm) >= KPM_BAR else "BROKEN"
    return dict(mode=mode, map=name, seed=seed, seconds=round(sim.now), job=list(job), score=[score[0], score[1]],
                ppm=[round(score[0] / minutes, 2), round(score[1] / minutes, 2)], kpm=[round(x, 2) for x in kpm],
                takes=takes, share={k: round(v / live, 3) for k, v in act.items()}, verdict=verdict,
                wall=round(time.monotonic() - t0))


def game_of_map(name):
    return next(g for g, ms in GAMES.items() if name in ms) if any(name in ms for ms in GAMES.values()) else \
        name.split("_")[0] if "_" in name else "ce"


def rows_of(runs):
    """Runs by (mode, map): the row (means over seeds, takes summed, the worst verdict)."""
    order = ["BROKEN", "AGGRESSIVE", "SCORING"]
    by = {}
    for r in runs:
        by.setdefault((r["mode"], r["map"]), []).append(r)
    out = []
    for (mode, name), rs in by.items():
        mean = lambda f: [round(sum(f(r)[k] for r in rs) / len(rs), 2) for k in (0, 1)]
        takes = {}
        for r in rs:
            for k, v in r["takes"].items():
                t = takes.setdefault(k, [0, 0])
                t[0], t[1] = t[0] + v[0], t[1] + v[1]
        share = {k: round(sum(r["share"][k] for r in rs) / len(rs), 3) for k in rs[0]["share"]}
        verdict = min((r["verdict"] for r in rs), key=order.index)
        notes = []
        if mode != "slayer" and verdict == "SCORING" and min(sum(r["score"][k] for r in rs) for k in (0, 1)) == 0:
            notes.append("one-sided")
        if min(mean(lambda r: r["kpm"])) < KPM_BAR:
            notes.append("low fight")
        if share["idle"] + share["stuck"] > IDLE_BAR:
            notes.append("idle")
        out.append(dict(game=game_of_map(name), mode=mode, map=name, seeds=len(rs), score=mean(lambda r: r["score"]),
                        ppm=mean(lambda r: r["ppm"]), kpm=mean(lambda r: r["kpm"]), takes=takes, share=share,
                        verdict=verdict, notes=notes))
    games = list(GAMES)
    out.sort(key=lambda r: (MODES.index(r["mode"]) if r["mode"] in MODES else 99,
                            games.index(r["game"]) if r["game"] in games else 99, r["map"]))
    return out


def table(rows):
    head = ("| game | mode | map | seeds | score (mean) | pts/min | kills/min | objective (summed over seeds, team 0-1) "
            "| fight / obj / walk / idle / stuck % | verdict |\n|---|---|---|---|---|---|---|---|---|---|\n")
    pc = lambda s: " / ".join(f"{100 * s[k]:.0f}" for k in ("fight", "obj", "walk", "idle", "stuck"))
    lines = [f"| {r['game']} | {r['mode']} | {r['map']} | {r['seeds']} | {r['score'][0]:g}-{r['score'][1]:g} | "
             f"{r['ppm'][0]:g} / {r['ppm'][1]:g} | {r['kpm'][0]:g} / {r['kpm'][1]:g} | "
             + ("; ".join(f"{k} {v[0]}-{v[1]}" for k, v in r["takes"].items()) or "-")
             + f" | {pc(r['share'])} | **{r['verdict']}**{(' (' + ', '.join(r['notes']) + ')') if r['notes'] else ''} |"
             for r in rows]
    return head + "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--games", default=",".join(GAMES))
    ap.add_argument("--maps", help="these maps instead of the games' representative ones")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--seconds", type=float, help="every mode this long (default 180 s, LONG's modes 300 s)")
    ap.add_argument("--per-team", type=int, default=4)
    ap.add_argument("--tier", default="top")
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "mode_matrix.md"))
    ap.add_argument("--resume", action="store_true", help="keep the runs already in <out>.runs.jsonl")
    ap.add_argument("--table-only", action="store_true", help="no new runs: the table from <out>.runs.jsonl")
    a = ap.parse_args()
    if os.name == "nt":            # below normal: other engineers' runs and a live brain share the CPU
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    names = a.maps.split(",") if a.maps else [n for g in a.games.split(",") for n in GAMES[g]]
    jobs, skipped = [], []
    for mode in a.modes.split(","):
        for name in names:
            if supports(mode, objects(name), name):
                jobs += [(mode, name, seed, a.seconds or LONG.get(mode, 180.0), a.per_team, a.tier) for seed in range(1, a.seeds + 1)]
            else:
                skipped.append(f"{mode} on {name}")
    t0 = time.monotonic()
    done_path = os.path.splitext(a.out)[0] + ".runs.jsonl"     # each run as it ends: --resume picks up after a crash
    runs = []
    if (a.resume or a.table_only) and os.path.exists(done_path):
        runs = [r for r in map(json.loads, open(done_path, encoding="utf-8")) if tuple(r["job"]) in jobs]
        have = {(r["mode"], r["map"], r["seed"]) for r in runs}
        jobs = [j for j in jobs if j[:3] not in have]
    elif os.path.exists(done_path):
        os.remove(done_path)
    print(f"{len(jobs)} runs on {a.procs} processes ({len(runs)} kept); no data for: {', '.join(skipped) or 'none'}",
          flush=True)
    # a fresh process a run: a process keeps every map it loaded (brain/maps.py caches), 18 maps ran it out of memory
    if a.table_only:
        skipped += [f"{j[0]} on {j[1]} seed {j[2]} (not run)" for j in jobs]
        jobs = []
    with multiprocessing.Pool(a.procs, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(play, jobs):
            runs.append(r)
            with open(done_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(r) + "\n")
            print(f"{r['mode']:11s} {r['map']:22s} seed {r['seed']}: score {r['score']} kpm {r['kpm']} "
                  f"{r['verdict']:10s} {r['takes']} {r['share']} ({r['wall']} s)", flush=True)
    rows = rows_of(runs)
    head = (f"# Mode matrix {time.strftime('%Y-%m-%d %H:%M')}: {a.per_team} v {a.per_team} {a.tier}, "
            f"{f'{a.seconds:.0f} s' if a.seconds else '180 s (' + ', '.join(LONG) + ' 300 s)'}, "
            f"{a.seeds} seeds, {len(runs)} runs ({time.monotonic() - t0:.0f} s wall)\n\n"
            f"Verdicts: SCORING the score moved; AGGRESSIVE no score but both teams kill {KPM_BAR}+ a minute; BROKEN "
            f"neither. one-sided: a team never scored; low fight: a team under {KPM_BAR} kills a minute; idle: idle + stuck over {IDLE_BAR:.0%} of bot time.\n"
            f"No map data (not run): {', '.join(skipped) or 'none'}\n\n")
    count = {v: sum(r["verdict"] == v for r in rows) for v in ("SCORING", "AGGRESSIVE", "BROKEN")}
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(head + table(rows) + f"\n{count}\n")
    with open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(dict(rows=rows, runs=runs, skipped=skipped), f, indent=1)
    print(table(rows))
    print(count, "->", a.out)


if __name__ == "__main__":
    main()
