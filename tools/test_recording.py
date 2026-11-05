"""Match recordings (tools/recording.py): the newest unsaved games kept and saved ones never removed, the longest
recording kept as its last minutes on disk while it is written, and a bug report's own copy keeping its moment and the
match's end after the recording dropped its oldest minutes (tools/bug_reports.py catch_up).

usage: python -I test_recording.py      -> "recording tests OK"
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bug_reports  # noqa: E402
import recording  # noqa: E402


def main():
    recording.selftest()                     # rotation, saved games, settings, the time window
    tmp = tempfile.mkdtemp(prefix="halo_rec_test_")
    try:
        src, dst = os.path.join(tmp, "trace.jsonl"), os.path.join(tmp, "bug", "trace.jsonl")
        os.makedirs(os.path.dirname(dst))
        r = recording.RollingFile(src, 60.0)      # text mode, as the brain writes it (\r\n on Windows)
        r.slack, r.due = 20.0, 80.0
        r.write(json.dumps(dict(t=0.0, meta=dict(map="m", bot=dict(id=1)))) + "\n")
        for k in range(3000):                     # 300 s at 10 rows a second
            now = k / 10
            r.write(json.dumps(dict(t=now, id=1, pos=[k, 0, 0])) + "\n")
            if k in (500, 520):                   # two bug reports at 50 s and 52 s: the copy up to then
                r.write(json.dumps(dict(t=now, bug=f"r{k}", text="stuck")) + "\n")
                r.flush()
                bug_reports.catch_up(src, dst)
            r.tick(now)
            if r.job is not None:
                r.job.join()
                r.tick(now)
        r.close()
        rows = [json.loads(x) for x in open(src)]
        body = [x["t"] for x in rows if "pos" in x]
        assert body[0] >= 300 - 60 - 20 - 0.2 and body[-1] == 299.9, (body[0], body[-1])   # the last minute (+slack)
        bug_reports.catch_up(src, dst)            # the match's end (bug_reports.finish)
        copy = [json.loads(x) for x in open(dst)]                 # whole lines only (raises on a broken one)
        ts = [x["t"] for x in copy if "pos" in x]
        assert ts == sorted(ts) and len(ts) == len(set(ts)), "the bug report copy has rows twice or out of order"
        assert [x["bug"] for x in copy if "bug" in x] == ["r500", "r520"], "a report's moment left the copy"
        assert ts[0] == 0.0 and ts[-1] == 299.9 and 52.0 in ts, (ts[0], ts[-1])
        assert sum(1 for x in copy if "meta" in x) == 1, "the copy got the header lines again"
        # a copy brought up while the recording only grew: the plain append
        bug_reports.catch_up(src, dst)
        assert len(open(dst).readlines()) == len(copy), "a catch-up with nothing new wrote rows"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("recording tests OK")


if __name__ == "__main__":
    main()
