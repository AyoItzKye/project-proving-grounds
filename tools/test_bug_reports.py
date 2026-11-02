"""Bug reports from the game (tools/bug_reports.py): reports saved during a match go into that match's one folder (one
recording, every report listed with its moment and everyone's place, a marker line each); a new match gets its own
folder; the whole match is copied at its end; an older match's report is left alone; old one-folder-per- report
reports migrate into their match; the Observer labels the match.

usage: python -I test_bug_reports.py      -> "bug reports OK"
"""
import json
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import bug_reports  # noqa: E402
import observer  # noqa: E402
from brain.core import Vec, Snapshot, PlayerState  # noqa: E402


class P:                                                 # a bot's profile and plan, as the brain holds them
    tier, personality = "top", "rusher"


class B:
    p, goal = P(), ("objective", Vec(5, 5, 3))

    class order:
        role, point = "runner", Vec(5, 5, 3)


def report(stamp, unix, text):
    folder = os.path.join(bug_reports.DIR, stamp)
    os.makedirs(folder)
    json.dump(dict(time="x", unix=unix, title=5, how="pause menu", description=text), open(os.path.join(folder, "report.json"), "w"))


def main():
    fails = []
    tmp = tempfile.mkdtemp()
    bug_reports.DIR = os.path.join(tmp, "bug_reports")
    try:
        t0 = time.time() - 100.0                         # the match started 100 s ago
        report("20261025-101500", time.time() - 4.0, 'Bot ran into the "rail"\nby red base')
        report("20261025-101530", time.time() - 2.0, "bot lost by the bridge")
        report("20261024-090000", t0 - 3600, "an older match")
        trace_path = os.path.join(tmp, "trace_reach_50_panopticon_20261025-101340.jsonl")
        trace = open(trace_path, "w")
        trace.write(json.dumps(dict(t=1.0, world=[])) + "\n")
        bot = PlayerState(3, 1, "Nova30", Vec(10, 20, 3), Vec(), 0.0, 0.0, True, 1, 1, "dmr", is_bot=True)
        person = PlayerState(0, 0, "PlayerOne", Vec(1, 2, 3), Vec(), 0.0, 0.0, True, 1, 1, "ar")
        # (the snapshot still raw, "slayer"; the mode the brain last read is the match's: Spire Invasion's flags of
        # were filed as "slayer")
        snap = Snapshot(100.0, [person, bot], mode="slayer", score={0: 1, 1: 0})
        got = bug_reports.attach_new(t0, 100.0, snap, "reach_50_panopticon", trace, trace_path, {3: B()}, mode="ctf")
        if got != ["20261025-101500", "20261025-101530"]:
            fails.append(f"filed {got}: want this match's two reports")
        match = os.path.join(bug_reports.DIR, "reach_50_panopticon_20261025-101340")
        folders = sorted(os.listdir(bug_reports.DIR))
        if folders != ["20261024-090000", "reach_50_panopticon_20261025-101340"]:
            fails.append(f"folders {folders}: want the match's one folder (and the older single report left alone)")
        rs = json.load(open(os.path.join(match, "reports.json")))
        if len(rs) != 2 or not 95.0 <= rs[0]["t"] <= 97.0 or rs[0]["description"] != 'Bot ran into the "rail"\nby red base':
            fails.append(f"reports: {[(r.get('stamp'), r.get('t')) for r in rs]}")
        if any(r.get("mode") != "ctf" for r in rs):
            fails.append(f"modes {[r.get('mode') for r in rs]}: want the mode the brain last read (ctf), not the raw one")
        b = next(p for p in rs[0]["players"] if p["bot"])
        if b["goal"][0] != "objective" or b["order"][0] != "runner" or b["tier"] != "top" or b["pos"] != [10, 20, 3]:
            fails.append(f"bot at the moment: {b}")
        if [p["bot"] for p in rs[0]["players"]] != [False, True]:
            fails.append("only the brain's own bots are bots")
        lines = open(os.path.join(match, "trace.jsonl")).read().splitlines()
        if sum(1 for l in lines if json.loads(l).get("bug")) != 2:
            fails.append("want two marker lines in the one recording")
        if sorted(os.listdir(match)) != ["reports.json", "trace.jsonl"]:
            fails.append(f"match folder holds {sorted(os.listdir(match))}")
        trace.write(json.dumps(dict(t=150.0, world=[])) + "\n")   # the match goes on, then ends
        trace.close()
        critic_path = os.path.join(tmp, "critique_reach_50_panopticon_20261025-101341.jsonl")   # the critic's notes
        open(critic_path, "w").write(json.dumps(dict(t=90.0, kind="director", team=1, answer=dict(bots=[dict(
            bot="b3 Nova30", verdict="poor", faults=[dict(id="B-33", what="sat on the flag", why="x", instead="patrol")])])))
            + "\n")
        open(critic_path[:-6] + ".md", "w").write("# Critique\n")
        bug_reports.finish(trace_path, critic_path)
        if len(open(os.path.join(match, "trace.jsonl")).read().splitlines()) != len(lines) + 1:
            fails.append("the whole match was not copied at the end")
        if not all(os.path.exists(os.path.join(match, f)) for f in ("critique.jsonl", "critique.md")):
            fails.append("the critic's notes are not in the match folder")
        near = bug_reports.critic_near("reach_50_panopticon_20261025-101340", 96.0)
        if not near or "B-33" not in near[0]:
            fails.append(f"critic notes near the report: {near}")
        # the next match: its own folder
        t1 = time.time() - 10.0
        report("20261025-103000", time.time() - 1.0, "next match")
        trace2 = os.path.join(tmp, "trace_reach_70_boneyard_20261025-102950.jsonl")
        with open(trace2, "w") as f:
            f.write(json.dumps(dict(t=1.0, world=[])) + "\n")
            bug_reports.attach_new(t1, 10.0, snap, "reach_70_boneyard", f, trace2, {3: B()})
        if not os.path.exists(os.path.join(bug_reports.DIR, "reach_70_boneyard_20261025-102950", "reports.json")):
            fails.append("the next match did not get its own folder")
        # an old one-folder-per-report report moves into its match
        old = os.path.join(bug_reports.DIR, "20261025-090000")
        os.makedirs(old)
        json.dump(dict(unix=1, description="old style"), open(os.path.join(old, "report.json"), "w"))
        json.dump(dict(stamp="20261025-090000", t=5.0, recording="trace_h2_lockout_20261025-085900.jsonl", players=[]),
                  open(os.path.join(old, "attached.json"), "w"))
        open(os.path.join(old, "trace.jsonl"), "w").write("{}\n")
        bug_reports.migrate()
        if os.path.exists(old) or not os.path.exists(os.path.join(bug_reports.DIR, "h2_lockout_20261025-085900", "trace.jsonl")):
            fails.append("old report not migrated into its match folder")
        label = observer.bug_label(os.path.join(match, "trace.jsonl"))
        if not label or "2 reports" not in label or "Bot ran into the" not in label:
            fails.append(f"Observer label: {label}")
        if "file=bug_reports/m/trace.jsonl&t=96" not in bug_reports.link("m", 96):
            fails.append(bug_reports.link("m", 96))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("bug reports OK")


if __name__ == "__main__":
    main()
