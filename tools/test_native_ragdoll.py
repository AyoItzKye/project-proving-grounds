"""Builds and runs native/tests/test_ragdoll.cpp: native/ce_ragdoll.cpp's rigid-body solver offline, a live CE pose
dying over a floor by a wall (bodies come to rest lying down and stay still, joints inside their limits, momentum kept
when thrown, the wall stops them). Needs the VS 2022 Build Tools native/build.bat uses.

usage: python -I test_native_ragdoll.py      -> "native ragdoll OK"
"""
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "native", "tests", "test_ragdoll.cpp"))
VCVARS = paths.vcvars()


def main():
    if not os.path.exists(VCVARS):
        sys.exit(f"FAIL: no VS 2022 Build Tools at {VCVARS} (native/build.bat needs them too)")
    out = tempfile.mkdtemp()
    exe = os.path.join(out, "test_ragdoll.exe")
    build = subprocess.run(f'call "{VCVARS}" >nul && cl /nologo /O2 /EHsc "{SRC}" /Fe:"{exe}" /Fo:"{out}\\\\"',
                           shell=True, capture_output=True, text=True)
    if build.returncode or not os.path.exists(exe):
        sys.exit("FAIL: build\n" + build.stdout[-2000:] + build.stderr[-2000:])
    run = subprocess.run([exe], capture_output=True, text=True)
    print(run.stdout.strip())
    if run.returncode:
        sys.exit("FAIL")
    print("native ragdoll OK")


if __name__ == "__main__":
    main()
