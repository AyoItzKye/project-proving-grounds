"""Simulated games of the objective modes (brain/sim.py with brain/sim_modes.py rules) on every map that has the mode's
places in its scenario: score, kills and the objective events (phases taken, captures, plants, banks), one line per
game, to logs/mode_sims.md. A game whose objective never moves is flagged (bots ignoring the game type).

usage: python -I mode_sims.py [mode ...] [--maps a,b] [--seconds 240] [--per-team 4]
"""
import argparse
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)

NEEDS = {"invasion": ("inv_objective",), "territories": ("terr_object",), "assault": ("as_bomb", "as_goal"),
         "stockpile": ("stp_flag", "stp_goal"), "headhunter": ("hh_drop_point",)}


def maps_with(mode):
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "maps", "reach_*", "objects.json"))):
        name = os.path.basename(os.path.dirname(f))
        if name.startswith("reach_ff") or not os.path.exists(os.path.join(os.path.dirname(f), "heightmap.npz")):
            continue
        types = {x["type"] for x in json.load(open(f, encoding="utf-8")).get("netgame_flags", [])}
        if all(t in types for t in NEEDS[mode]):
            out.append(name)
    return out


def play_here(mode, name, seconds, per_team, seed=5):
    from brain.sim import Sim
    t0 = time.time()
    sim = Sim(mode, per_team=per_team, seed=seed, map_name=name)
    sim.run(seconds)
    ev = sim.objmodes.events
    kills = sum(v["kills"] for v in sim.stats.values())
    return dict(map=name, mode=mode, score={str(k): v for k, v in sim.score.items()}, kills=kills, events=len(ev),
                first=ev[:4], moved=bool(ev), real=round(time.time() - t0))


def play(mode, name, seconds, per_team, seed=5):
    """One game in its own process: memory goes back after each (a run of 79 games in one process ran the machine out of
    commit)."""
    import subprocess
    r = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), mode, "--maps", name, "--seconds", str(seconds),
                        "--per-team", str(per_team), "--one"], capture_output=True, text=True, timeout=1800)
    line = next((l for l in r.stdout.splitlines() if l.startswith("{")), None)
    if line is None:
        raise RuntimeError((r.stdout + r.stderr).strip()[-300:])
    return json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modes", nargs="*", default=list(NEEDS))
    ap.add_argument("--maps")
    ap.add_argument("--seconds", type=float, default=240)
    ap.add_argument("--per-team", type=int, default=4)
    ap.add_argument("--one", action="store_true", help="(internal) play one game here, print it as JSON")
    o = ap.parse_args()
    if o.one:
        print(json.dumps(play_here(o.modes[0], o.maps, o.seconds, o.per_team)))
        return
    rows = []
    with open(os.path.join(ROOT, "logs", "mode_sims.md"), "a", encoding="utf-8") as log:
        log.write(f"\n## Mode sims {time.strftime('%Y-%m-%d %H:%M')} ({o.seconds:.0f} s, {o.per_team}v{o.per_team})\n\n"
                  "| mode | map | score | kills | objective events | first events | real s |\n|---|---|---|---|---|---|---|\n")
        for mode in o.modes:
            names = o.maps.split(",") if o.maps else maps_with(mode)
            for name in names:
                try:
                    r = play(mode, name, o.seconds, o.per_team)
                except Exception as e:
                    import traceback
                    r = dict(map=name, mode=mode, error=f"{type(e).__name__}: {e}", tb=traceback.format_exc(limit=-4))
                rows.append(r)
                line = (f"| {mode} | {name} | " + (f"FAILED {r['error']} |" if "error" in r else
                        f"{r['score']} | {r['kills']} | {r['events']}{'' if r['moved'] else ' (NOTHING MOVED)'} | "
                        f"{'; '.join(e[1] for e in r['first'])} | {r['real']} |"))
                print(line, flush=True)
                if "tb" in r:
                    print(r["tb"], flush=True)
                log.write(line + "\n")
                log.flush()
    stuck = [r for r in rows if "error" in r or not r.get("moved")]
    print(f"{len(rows) - len(stuck)}/{len(rows)} games moved their objective")
    sys.exit(1 if stuck else 0)


if __name__ == "__main__":
    main()
