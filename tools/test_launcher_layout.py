"""The launcher's layout (an empty block sat beside Play, Nov 13): tools/launcher.html's main holds two columns; the
left one Play then the tools in two columns, the right one First-time setup then the game folder, LiDAR scans and
settings; Play and First-time setup take the spare height so both columns end together.

usage: python -I test_launcher_layout.py      -> "launcher layout OK"
"""
import os
import re
import sys

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher.html")


def main():
    src = open(HTML, encoding="utf-8").read()
    body = src[src.index("<main>"):src.index("</main>")]
    cols = [m.start() for m in re.finditer(r'\n  <div class="col">', body)]
    fails = []
    if len(cols) != 2:
        fails.append(f"main has {len(cols)} columns, not 2")
    else:
        left, right = body[cols[0]:cols[1]], body[cols[1]:]
        order = lambda part, keys: [k for k in sorted(keys, key=lambda k: part.find(k)) if part.find(k) >= 0]
        want_l = ['class="card play-card"', 'class="card tools-sec"']
        want_r = ['id="setup-card"', 'id="folder-card"', 'id="scans-card"', 'id="settings-card"']
        if order(left, want_l) != want_l:
            fails.append(f"left column: {order(left, want_l)}")
        if order(right, want_r) != want_r:
            fails.append(f"right column: {order(right, want_r)}")
    css = src[:src.index("<main>")]
    for rule in (r"\.col\s*\{[^}]*flex-direction:\s*column", r"\.col > \.play-card, \.col > #setup-card\s*\{[^}]*flex: 1",
                 r"\.tools\s*\{[^}]*repeat\(2, minmax\(0, 1fr\)\)"):
        if not re.search(rule, css):
            fails.append(f"css missing: {rule}")
    if fails:
        print("FAIL\n" + "\n".join(fails))
        sys.exit(1)
    print("launcher layout OK")


if __name__ == "__main__":
    main()
