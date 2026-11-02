"""The Observer's name and its match export. Offline: tools/match_export.py's self-test (a person and a bot marked as
such, the user's folder in a path replaced, a real Xbox id and gamertag gone, a bot's row kept, --keep-names keeping
the name but not the Xbox id); the page and the server have the export; the old name "Bot Observer" is gone from
everything a person sees.

usage: python -I test_observer_export.py      -> "observer export OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)


def main():
    fails = []
    import match_export
    match_export.selftest()
    page = open(os.path.join(HERE, "observer.html"), encoding="utf-8").read()
    server = open(os.path.join(HERE, "observer.py"), encoding="utf-8").read()
    if 'id="exportbtn"' not in page or "/export?file=" not in page or 'u.path == "/export"' not in server:
        fails.append("the Observer page or server has no game export")
    launchers = any(f.endswith(".bat") for f in os.listdir(ROOT))     # (the public copy ships no root launchers)
    if launchers and (not os.path.exists(os.path.join(ROOT, "Observer.bat"))
                      or os.path.exists(os.path.join(ROOT, "Bot Observer.bat"))):
        fails.append("the launcher is not Observer.bat")
    seen = [f for f in ("README.md", "Observer.bat", "tools/observer.html", "tools/observer.py", "tools/collector.py",
                        "tools/player_stats.py", "native/bots_panel.cpp")
            if os.path.exists(os.path.join(ROOT, f)) and "Bot Observer" in open(os.path.join(ROOT, f), encoding="utf-8").read()
            .replace("named Bot Observer until Oct 24", "")]
    if seen:
        fails.append(f"'Bot Observer' still in {seen}")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("observer export OK")


if __name__ == "__main__":
    main()
