"""The README's Release row (tools/build_installer.py readme_release): the version without its build tag and the day
of the last update from BUILD's stamp, rewritten in place by every installer build; the real README has the row.

usage: python -I test_readme_release.py      -> "readme release OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_installer  # noqa: E402


def main():
    fails = []
    old = ("x\n| | |\n|---|---|\n| **[Release](u)** | Version **0.1.0**, last updated **May 1, 2026**. Download it from the "
           "Releases page. <!-- release --> |\n| **[Updates](docs/UPDATES.md)** | y |\n")
    new = build_installer.readme_release(old, "0.2.3-s190", "20261109-0905")
    if "Version **0.2.3**, last updated **November 9, 2026**." not in new or "0.1.0" in new or "s190" in new:
        fails.append(f"Release row: {new.splitlines()[3]}")
    if new.count("<!-- release -->") != 1 or "| **[Updates](docs/UPDATES.md)** | y |" not in new:
        fails.append("Release row: the marker or the other rows changed")
    readme = open(os.path.join(HERE, "..", "README.md"), encoding="utf-8").read()
    if readme.count("<!-- release -->") != 1:
        fails.append("README.md: no single Release row (<!-- release -->)")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("readme release OK")


if __name__ == "__main__":
    main()
