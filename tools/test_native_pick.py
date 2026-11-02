"""Builds and runs native/tests/test_pick.cpp: botcore's choice of the loose weapon a bot's Use takes (native/shared.h
hb_pick_loose; live Spire: the nearest-within-0.6-u rule swapped a runner's rifle for a gun by the core it was looking
at) and when a bot's new unit moves to its Invasion spawn (hb_spawn_take). Needs the VS 2022 Build Tools
native/build.bat uses.

usage: python -I test_native_pick.py      -> "native pick OK"
"""
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "native", "tests", "test_pick.cpp"))
VCVARS = paths.vcvars()


def main():
    if not os.path.exists(VCVARS):
        sys.exit(f"FAIL: no VS 2022 Build Tools at {VCVARS} (native/build.bat needs them too)")
    out = tempfile.mkdtemp()
    exe = os.path.join(out, "test_pick.exe")
    build = subprocess.run(f'call "{VCVARS}" >nul && cl /nologo /O2 /EHsc "{SRC}" /Fe:"{exe}" /Fo:"{out}\\\\"',
                           shell=True, capture_output=True, text=True)
    if build.returncode or not os.path.exists(exe):
        sys.exit("FAIL: build\n" + build.stdout[-2000:] + build.stderr[-2000:])
    run = subprocess.run([exe], capture_output=True, text=True)
    if run.returncode:
        sys.exit("FAIL\n" + run.stdout)
    print("native pick OK")


if __name__ == "__main__":
    main()
