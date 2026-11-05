"""Builds the Windows installer for a GitHub release: ProjectProvingGrounds-Setup-<version>.exe, everything a player
needs in one file, so nobody has to install Python, build tools or anything else.

What goes in (staged in installer_build/payload beside this project's folder):
  - the public copy of the project (tools/make_release.py: the source, the map knowledge, the docs) and the map pack
  - the built mod: native/bin/botcore.dll and inject.exe (native/build.bat, Visual Studio's C++ tools)
  - the map tools: bsp2obj.exe and model2obj.exe with their runtime (the separate proving-grounds-map-tools project,
    found by brain/paths.map_tool) in tools/map_tools
  - Python: the official embeddable Python for Windows (the version this PC runs) in python/, with the packages the
    mod uses (numpy, scipy, Pillow, the versions this PC's tests pass with) in python/Lib/site-packages
then Inno Setup compiles installer/ProjectProvingGrounds.iss over it, and the same payload with installer/linux's
scripts becomes ProjectProvingGrounds-Linux-<version>.tar.gz (Linux and Steam Deck, through Proton).

Needs: the .NET-free map tools build, Visual Studio's C++ build tools, Inno Setup 6 (ISCC.exe), internet for the
embeddable Python and the packages the first time (cached in installer_build/cache).

usage: python -I build_installer.py [--skip-native]      (--skip-native: use the botcore.dll already built)
       python -I build_installer.py --linux-only       (only the Linux tar.gz, from the payload already staged)
"""
import glob
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import make_release  # noqa: E402
from brain import paths  # noqa: E402

BUILD = os.path.join(os.path.dirname(ROOT), "installer_build")
PAYLOAD = os.path.join(BUILD, "payload")
CACHE = os.path.join(BUILD, "cache")
PACKAGES = ("numpy==2.5.3", "scipy==1.18.1", "pillow==12.3.0")


def version():
    return open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()


def iscc():
    """Inno Setup's compiler, or None."""
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        for p in (os.path.join(base or "", "Programs", "Inno Setup 6", "ISCC.exe"),
                  os.path.join(base or "", "Inno Setup 6", "ISCC.exe")):
            if base and os.path.exists(p):
                return p
    return shutil.which("ISCC")


def step(msg):
    print(f"== {msg}", flush=True)


# in the public copy for developers, not in a player's install: the tests and their simulator, the build and release
# tools, the panel preview, and the repository's community files
DEV_ONLY = ("tools/test_*.py", "tools/run_tests.py", "tools/testdata.py", "tools/build_installer.py", "tools/make_release.py",
            "tools/human_data.py", "tools/baseline_compare.py", "tools/clean_bin.py", "tools/zoom_match.py",
            "brain/sim.py", "brain/sim_modes.py", "brain/simgear.py", "native/panel_preview.cpp", "native/build_preview.bat", "native/test_zoom.cpp",
            "native/tests/**", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "SECURITY.md", "requirements.txt",
            "requirements-dev.txt", ".gitignore", ".github/**", make_release.MARK)


def stage_project():
    """The public copy (less DEV_ONLY) and the map pack, merged into the payload."""
    step("public copy and map pack (tools/make_release.py)")
    out, pack = make_release.build(os.path.join(BUILD, "release"))
    if not make_release.report(out) or not make_release.report(pack):
        raise SystemExit("the privacy scan found private data: not building")
    for dp, _, fs in os.walk(out):
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), out).replace("\\", "/")
            if not any(make_release.match(rel, p) for p in DEV_ONLY):
                os.makedirs(os.path.join(PAYLOAD, os.path.dirname(rel)), exist_ok=True)
                shutil.copy2(os.path.join(dp, f), os.path.join(PAYLOAD, rel))
    shutil.copytree(pack, PAYLOAD, dirs_exist_ok=True, ignore=shutil.ignore_patterns(make_release.MARK))


def stage_native(skip_build):
    step("the mod: botcore.dll, inject.exe and the app window (ppg_window.exe)")
    nb = os.path.join(ROOT, "native", "bin")
    if not skip_build:
        for bat in ("build.bat", "build_window.bat"):
            r = subprocess.run(["cmd", "/c", os.path.join(ROOT, "native", bat)], cwd=os.path.join(ROOT, "native"),
                               capture_output=True, text=True, errors="replace")
            if "BUILD OK" not in r.stdout:
                raise SystemExit(f"native build ({bat}) failed:\n" + r.stdout[-2000:])
    dst = os.path.join(PAYLOAD, "native", "bin")
    os.makedirs(dst, exist_ok=True)
    for f in ("botcore.dll", "inject.exe", "ppg_window.exe"):
        shutil.copy2(os.path.join(nb, f), os.path.join(dst, f))


def stage_map_tools():
    step("the map tools (bsp2obj, model2obj)")
    exe = paths.need(paths.map_tool("model2obj"), "the map tools (build proving-grounds-map-tools first)")
    shutil.copytree(os.path.dirname(exe), os.path.join(PAYLOAD, "tools", "map_tools"), dirs_exist_ok=True)


def download(url, dst):
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        urllib.request.urlretrieve(url, dst + ".part")
        os.replace(dst + ".part", dst)
    return dst


def stage_python():
    """The embeddable Python of this PC's version, with the mod's packages."""
    ver = platform.python_version()
    step(f"Python {ver} (embeddable) and {', '.join(PACKAGES)}")
    z = download(f"https://www.python.org/ftp/python/{ver}/python-{ver}-embed-amd64.zip",
                 os.path.join(CACHE, f"python-{ver}-embed-amd64.zip"))
    print(f"   {os.path.basename(z)} sha256 {hashlib.sha256(open(z, 'rb').read()).hexdigest()}", flush=True)
    py = os.path.join(PAYLOAD, "python")
    with zipfile.ZipFile(z) as f:
        f.extractall(py)
    site = os.path.join(py, "Lib", "site-packages")
    pth = glob.glob(os.path.join(py, "python*._pth"))[0]
    with open(pth, "w", encoding="utf-8") as f:     # the zip of the standard library, the folder, the packages
        f.write(f"python{sys.version_info.major}{sys.version_info.minor}.zip\n.\nLib\\site-packages\n")
    wheels = os.path.join(CACHE, "wheels")
    subprocess.run([sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--platform", "win_amd64",
                    "--python-version", f"{sys.version_info.major}.{sys.version_info.minor}", "-d", wheels,
                    "--disable-pip-version-check", *PACKAGES], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--find-links", wheels, "--target", site,
                    "--no-compile", "--disable-pip-version-check", *PACKAGES], check=True)
    r = subprocess.run([os.path.join(py, "python.exe"), "-I", "-c",
                        "import numpy, scipy.sparse.csgraph, PIL, ctypes, winreg, sqlite3; print('python ok')"],
                       capture_output=True, text=True)
    if "python ok" not in r.stdout:
        raise SystemExit("the bundled Python does not import the packages:\n" + r.stderr[-1500:])


def stage_texts():
    """Plain-text copies of the license and notices for the installer's license page."""
    with open(os.path.join(BUILD, "license.txt"), "w", encoding="utf-8") as f:
        f.write(open(os.path.join(ROOT, "NOTICE.md"), encoding="utf-8").read() + "\n\n")
        f.write(open(os.path.join(ROOT, "LICENSE.md"), encoding="utf-8").read())


def compile_setup():
    step("Setup.exe (Inno Setup)")
    exe = iscc() or sys.exit("Inno Setup 6 was not found (winget install JRSoftware.InnoSetup)")
    r = subprocess.run([exe, f"/DAppVersion={version()}", f"/DPayload={PAYLOAD}", f"/DBuildDir={BUILD}",
                        os.path.join(ROOT, "installer", "ProjectProvingGrounds.iss")], capture_output=True, text=True,
                       errors="replace")
    if r.returncode:
        raise SystemExit("Inno Setup failed:\n" + r.stdout[-3000:] + r.stderr[-1000:])
    out = os.path.join(BUILD, f"ProjectProvingGrounds-Setup-{version()}.exe")
    print(f"   {out}: {os.path.getsize(out) / 1048576:.0f} MB, sha256 "
          f"{hashlib.sha256(open(out, 'rb').read()).hexdigest()}", flush=True)
    return out


def zip_map_pack():
    """The map pack as its own download (developers unzip it over a source checkout): installer_build/
    project-proving-grounds-map-pack-<version>.zip."""
    step("map pack zip")
    src = os.path.join(BUILD, "release-map-pack")
    out = os.path.join(BUILD, f"project-proving-grounds-map-pack-{version()}.zip")
    with zipfile.ZipFile(out + ".part", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dp, _, fs in os.walk(src):
            for f in fs:
                if f != make_release.MARK:
                    p = os.path.join(dp, f)
                    z.write(p, os.path.relpath(p, src))
    os.replace(out + ".part", out)
    print(f"   {out}: {os.path.getsize(out) / 1048576:.0f} MB", flush=True)


def linux_bundle():
    """The Linux / Steam Deck download: installer_build/ProjectProvingGrounds-Linux-<version>.tar.gz, the same payload
    (the mod's Windows parts run through Proton) with installer/linux's install.sh and uninstall.sh beside it. Shell
    scripts get LF line endings and the executable bit (a Windows checkout may have CRLF)."""
    import io
    import tarfile
    step("Linux / Steam Deck tar.gz")
    top = f"ProjectProvingGrounds-Linux-{version()}"
    out = os.path.join(BUILD, top + ".tar.gz")

    def add(tar, path, name):
        info = tar.gettarinfo(path, name)
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        if info.isdir():
            info.mode = 0o755
            tar.addfile(info)
        elif name.endswith(".sh"):
            data = open(path, "rb").read().replace(b"\r\n", b"\n")
            info.size, info.mode = len(data), 0o755
            tar.addfile(info, io.BytesIO(data))
        else:
            info.mode = 0o644
            with open(path, "rb") as f:
                tar.addfile(info, f)

    with tarfile.open(out + ".part", "w:gz", compresslevel=6) as tar:
        for f in ("install.sh", "uninstall.sh"):
            add(tar, os.path.join(PAYLOAD, "installer", "linux", f), f"{top}/{f}")
        for dp, ds, fs in os.walk(PAYLOAD):
            rel = os.path.relpath(dp, PAYLOAD).replace("\\", "/")
            base = f"{top}/payload" + ("" if rel == "." else "/" + rel)
            add(tar, dp, base)
            for f in sorted(fs):
                add(tar, os.path.join(dp, f), f"{base}/{f}")
    os.replace(out + ".part", out)
    print(f"   {out}: {os.path.getsize(out) / 1048576:.0f} MB, sha256 "
          f"{hashlib.sha256(open(out, 'rb').read()).hexdigest()}", flush=True)
    return out


def main():
    if "--linux-only" in sys.argv:                   # (the tar.gz from the payload already staged)
        linux_bundle()
        return
    if os.path.exists(PAYLOAD):
        shutil.rmtree(PAYLOAD)
    os.makedirs(PAYLOAD)
    stage_project()
    stage_native("--skip-native" in sys.argv)
    stage_map_tools()
    stage_python()
    stage_texts()
    shutil.copy2(os.path.join(ROOT, "VERSION"), os.path.join(PAYLOAD, "VERSION"))
    compile_setup()
    linux_bundle()
    zip_map_pack()


if __name__ == "__main__":
    main()
