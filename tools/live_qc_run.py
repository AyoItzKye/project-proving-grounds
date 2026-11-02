"""Start the lobby's current setup and let the bots play (tools/live_qc.py's second half, for a setup already picked by
hand): START, wait for the match, play MINUTES, end it, summarize to logs/live_qc.md.

usage: python -I live_qc_run.py [--minutes 5] [--label text]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live_qc  # noqa: E402


def main():
    a = sys.argv[1:]
    minutes = float(a[a.index("--minutes") + 1]) if "--minutes" in a else 5.0
    label = a[a.index("--label") + 1] if "--label" in a else ""
    live_qc.play(minutes, label)


if __name__ == "__main__":
    main()
