"""Builds and runs native/tests/test_faults.cpp: the failure paths of botcore's Halo 4 / H2A guards (native/h4f.cpp) on
fake game memory: a fault in a bot's boarding caught and logged with its bot, a faulting command reported and completed,
a fault anywhere else in the players-update hook caught, and H2A's first-tick hold giving up after 4 s with no bots.
Needs the VS 2022 Build Tools native/build.bat uses.

usage: python -I test_native_faults.py      -> "native faults OK"
"""
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "native", "tests", "test_faults.cpp"))
VCVARS = paths.vcvars()


def main():
    if not os.path.exists(VCVARS):
        sys.exit(f"FAIL: no VS 2022 Build Tools at {VCVARS} (native/build.bat needs them too)")
    out = tempfile.mkdtemp()
    exe = os.path.join(out, "test_faults.exe")
    build = subprocess.run(f'call "{VCVARS}" >nul && cl /nologo /O2 /W3 /EHsc /MT "{SRC}" user32.lib /Fe:"{exe}" /Fo:"{out}\\\\"',
                           shell=True, capture_output=True, text=True, timeout=300)
    if build.returncode or not os.path.exists(exe):
        sys.exit("FAIL: build\n" + build.stdout[-3000:] + build.stderr[-2000:])
    run = subprocess.run([exe], capture_output=True, text=True, timeout=60)
    if run.returncode:
        sys.exit("FAIL\n" + run.stdout[-3000:])
    print("native faults OK:", run.stdout.strip())


if __name__ == "__main__":
    main()
