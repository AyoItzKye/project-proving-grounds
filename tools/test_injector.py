"""inject.exe put back when Windows Defender deletes it (and 23:52: native/bin/inject.exe gone, so no bot could load):
tools/botctl.py injector, used by tools/launch.py and tools/play.py.

1. present: its path, nothing restored
2. missing, the restore works: its path, and a line saying it was put back
3. missing, nothing works: None, and the player's message says what happened, why and what to do
4. the real thing: the project's inject.exe deleted (a copy kept aside) comes back from git, byte for byte

usage: python -I test_injector.py      -> "injector OK"
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botctl  # noqa: E402
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def call(root, restore):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        got = botctl.injector(root, restore)
    return got, out.getvalue()


def main():
    testdata.need("native/bin/inject.exe", why="build native first: native/build.bat")
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "native", "bin", "inject.exe")
        os.makedirs(os.path.dirname(exe))
        open(exe, "wb").write(b"MZ")
        got, said = call(tmp, lambda p: fails.append("restore called with the file there") or False)
        if got != exe or said:
            fails.append(f"present: {got!r}, said {said!r}")
        os.remove(exe)
        got, said = call(tmp, lambda p: open(p, "wb").write(b"MZ") > 0)
        if got != exe or "put it back" not in said:
            fails.append(f"missing, restored: {got!r}, said {said!r}")
        os.remove(exe)
        got, said = call(tmp, lambda p: False)
        if got is not None or not all(w in said for w in ("missing", "Windows Defender", "Protection history",
                                                          "native\\build.bat", "exclusion")):
            fails.append(f"missing for good: {got!r}, said {said!r} (want what, why, what to do)")
    real = os.path.join(HERE, "..", "native", "bin", "inject.exe")
    if not os.path.exists(real):
        fails.append("(the project's inject.exe is missing before the test)")
    else:
        keep = os.path.join(tempfile.mkdtemp(), "inject.exe")
        shutil.copy2(real, keep)
        try:
            os.remove(real)
            got, said = call(None, None)
            if got is None or not os.path.exists(real):
                fails.append(f"the real restore: {got!r}, said {said!r}")
        finally:
            if not os.path.exists(real):
                shutil.copy2(keep, real)              # (never left without it)
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("injector OK")


if __name__ == "__main__":
    main()
