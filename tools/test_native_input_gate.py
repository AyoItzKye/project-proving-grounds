"""Builds and runs native/tests/test_input_gate.cpp: the BOTS panel's keys after a gap in listening (native/input_gate.h;
after an ODST match the panel ran on through its controls as if Right were held: its release came while botcore's UI
was not listening). Needs the VS 2022 Build Tools native/build.bat uses.

usage: python -I test_native_input_gate.py      -> "native input gate OK"
"""
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
NATIVE = os.path.normpath(os.path.join(HERE, "..", "native"))
IG = os.path.join(NATIVE, "third_party", "imgui")
SRC = [os.path.join(NATIVE, "tests", "test_input_gate.cpp")] + \
      [os.path.join(IG, f) for f in ("imgui.cpp", "imgui_draw.cpp", "imgui_tables.cpp", "imgui_widgets.cpp")]
VCVARS = paths.vcvars()


def main():
    if not os.path.exists(VCVARS):
        sys.exit(f"FAIL: no VS 2022 Build Tools at {VCVARS} (native/build.bat needs them too)")
    out = tempfile.mkdtemp()
    exe = os.path.join(out, "test_input_gate.exe")
    files = " ".join(f'"{s}"' for s in SRC)
    build = subprocess.run(f'call "{VCVARS}" >nul && cl /nologo /O2 /EHsc {files} /Fe:"{exe}" /Fo:"{out}\\\\"',
                           shell=True, capture_output=True, text=True)
    if build.returncode or not os.path.exists(exe):
        sys.exit("FAIL: build\n" + build.stdout[-2000:] + build.stderr[-2000:])
    run = subprocess.run([exe], capture_output=True, text=True)
    print(run.stdout.strip())
    if run.returncode:
        sys.exit("FAIL")
    print("native input gate OK")


if __name__ == "__main__":
    main()
