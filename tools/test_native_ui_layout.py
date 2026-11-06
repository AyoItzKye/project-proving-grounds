"""Builds and runs native/tests/test_ui_layout.cpp: where botcore's BOTS tile and pause-menu "Report bot bug" button go at
every window size (native/ui_layout.h; MCC's own tiles and footer measured from screenshots). It is built twice: as is
(must pass) and with /DUI_OLD, the layout before Nov 5 that was tailored to 3440x1440 (must fail, so the test is known to
catch it). Needs the VS 2022 Build Tools native/build.bat uses.

usage: python -I test_native_ui_layout.py      -> "native ui layout OK"
"""
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "native", "tests", "test_ui_layout.cpp"))
VCVARS = paths.vcvars()


def build_run(out, name, flags=""):
    exe = os.path.join(out, name + ".exe")
    b = subprocess.run(f'call "{VCVARS}" >nul && cl /nologo /O2 /W4 /EHsc {flags} "{SRC}" /Fe:"{exe}" /Fo:"{out}\\{name}.obj"',
                       shell=True, capture_output=True, text=True)
    if b.returncode or not os.path.exists(exe):
        sys.exit("FAIL: build\n" + b.stdout[-2000:] + b.stderr[-2000:])
    return subprocess.run([exe], capture_output=True, text=True)


def main():
    if not os.path.exists(VCVARS):
        sys.exit(f"FAIL: no VS 2022 Build Tools at {VCVARS} (native/build.bat needs them too)")
    out = tempfile.mkdtemp()
    new = build_run(out, "ui_new")
    if new.returncode:
        sys.exit("FAIL\n" + new.stdout)
    old = build_run(out, "ui_old", "/DUI_OLD")
    if not old.returncode:
        sys.exit("FAIL: the old 3440x1440-only layout passes too; the test catches nothing\n" + old.stdout)
    print(f"native ui layout OK (the old layout fails {old.stdout.count('FAIL ')} checks)")


if __name__ == "__main__":
    main()
