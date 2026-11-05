"""Builds and runs native/tests/test_film.cpp: native/film.cpp records a match's bots and plays them back in its
Theater film, with the recording found by any copy of the mod (the shared per-user folder; a Reach film recorded by the
working repo's botcore played with no bots under the install's, which looked only in its own logs\\films) and in a
copy's old logs\\films. Needs the VS 2022 Build Tools native/build.bat uses.

usage: python -I test_native_film.py      -> "native film OK"
"""
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "native", "tests", "test_film.cpp"))
VCVARS = paths.vcvars()


def main():
    if not os.path.exists(VCVARS):
        sys.exit(f"FAIL: no VS 2022 Build Tools at {VCVARS} (native/build.bat needs them too)")
    out = tempfile.mkdtemp()
    exe = os.path.join(out, "test_film.exe")
    build = subprocess.run(f'call "{VCVARS}" >nul && cl /nologo /O2 /EHsc "{SRC}" /Fe:"{exe}" /Fo:"{out}\\\\"',
                           shell=True, capture_output=True, text=True)
    if build.returncode or not os.path.exists(exe):
        sys.exit("FAIL: build\n" + build.stdout[-2000:] + build.stderr[-2000:])
    scratch = os.path.join(out, "films")
    os.makedirs(scratch)
    run = subprocess.run([exe, scratch], capture_output=True, text=True)
    if run.returncode:
        sys.exit("FAIL\n" + run.stdout)
    print("native film OK")


if __name__ == "__main__":
    main()
