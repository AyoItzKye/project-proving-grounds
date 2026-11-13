"""The update on Steam Deck / Linux (tools/updater.py apply_linux, asset, stage; the Windows Setup does not run there, the
player was sent to GitHub to "download, unzip and install again", Nov 12), and the update while MCC runs (stage, retry_ok):

1. apply_linux over an install: the new code and files in, the old version's code and documents gone (a tools .py the new
   version lacks, docs/), the player's files (user/, a map's LiDAR scan, logs) byte for byte as they were, a file the same size
   and time left alone (the Python runtime), a script written in place, the payload's own path traversal ignored
2. the same archive again: nothing changes (a failed copy is picked up by the next try)
3. an archive that is not a payload, or is cut short: an error before anything of the install is touched
4. asset / can_install: on Linux the release's tar.gz (not its Setup), on Windows the Setup; staged() needs the whole file
5. stage while MCC runs: the download only, the Setup kept; retry_ok holds off 5 minutes after a failure
6. conflicts.linux_mcc_running: a process folder with MCC's program in a command line

usage: python -I test_updater_linux.py      -> "updater linux OK"
"""
import io
import os
import shutil
import sys
import tarfile
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import conflicts  # noqa: E402
import updater  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def write(root, rel, data, mtime=None):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)
    if mtime:
        os.utime(p, (mtime, mtime))
    return p


def read(root, rel):
    try:
        return open(os.path.join(root, *rel.split("/")), "rb").read()
    except OSError:
        return None


def tree(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, root).replace("\\", "/")] = open(p, "rb").read()
    return out


def make_tar(path, files, top="PPG-Linux-9.9.9", extra=()):
    with tarfile.open(path, "w:gz") as tf:
        for rel, data, mtime in files:
            info = tarfile.TarInfo(f"{top}/payload/{rel}")
            info.size, info.mtime = len(data), mtime
            tf.addfile(info, io.BytesIO(data))
        for name, data in extra:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))


T = 1_700_000_000
tmp = tempfile.mkdtemp()
try:
    app = os.path.join(tmp, "app")
    # the installed version: old code, a tools file the new one lacks, docs, the python runtime, the player's files
    write(app, "tools/launcher.py", b"old launcher", T - 500)
    write(app, "tools/gone_in_new.py", b"old", T - 500)
    write(app, "brain/x.py", b"old brain", T - 500)
    write(app, "docs/a.md", b"old docs", T - 500)
    write(app, "VERSION", b"0.2.2", T - 500)
    write(app, "BUILD", b"20261112-1306", T - 500)
    write(app, "python/python.exe", b"RUNTIME", T)
    write(app, "installer/linux/common.sh", b"old sh", T - 500)
    mine = {"user/settings.ini": b"mine", "maps/h3_x/lidar.json": b"scan", "logs/launcher/linux.txt": b"log",
            "maps/h3_x/callouts.json": b"old callouts"}
    for rel, data in mine.items():
        write(app, rel, data, T - 100)
    new = [("tools/launcher.py", b"NEW launcher", T + 10), ("tools/new_tool.py", b"new tool", T + 10),
           ("brain/x.py", b"NEW brain", T + 10), ("VERSION", b"0.2.3", T + 10), ("BUILD", b"20261112-2117", T + 10),
           ("python/python.exe", b"RUNTIME", T), ("installer/linux/common.sh", b"NEW sh", T + 10),
           ("maps/h3_x/callouts.json", b"NEW callouts", T + 10), ("native/bin/botcore.dll", b"dll v2", T + 10)]
    archive = os.path.join(tmp, "PPG-Linux-9.9.9.tar.gz")
    make_tar(archive, new, extra=[("PPG-Linux-9.9.9/install.sh", b"#!/bin/sh"), ("../evil.txt", b"x"),
                                  ("PPG-Linux-9.9.9/payload/../../evil2.txt", b"x")])
    stage_dir = os.path.join(tmp, "stage")
    updater.apply_linux(archive, root=app, stage_dir=stage_dir)
    got = tree(app)
    check("1. the new code and files are in", all(read(app, rel) == data for rel, data, _ in new))
    check("1. the old version's code is gone, its documents too", read(app, "tools/gone_in_new.py") is None
          and read(app, "docs/a.md") is None)
    check("1. the player's files are as they were", all(read(app, rel) == data for rel, data in mine.items()
                                                        if rel != "maps/h3_x/callouts.json"))
    check("1. the runtime (same size and time) not rewritten", os.path.getmtime(os.path.join(app, "python", "python.exe")) == T)
    check("1. no half-written .new files, no staging, the archive used up",
          not any(k.endswith(".new") for k in got) and not os.path.exists(stage_dir) and not os.path.exists(archive), sorted(got)[:4])
    check("1. nothing written outside the install",
          not os.path.exists(os.path.join(tmp, "evil.txt")) and not os.path.exists(os.path.join(tmp, "evil2.txt")))

    # 2. again: nothing changes
    make_tar(archive, new)
    before = tree(app)
    updater.apply_linux(archive, root=app, stage_dir=stage_dir)
    check("2. the same update again: the same install", tree(app) == before)

    # 3. not a payload, cut short: an error and the install untouched
    before = tree(app)
    make_tar(archive, [("README", b"no launcher", T)])
    try:
        updater.apply_linux(archive, root=app, stage_dir=stage_dir)
        check("3. not a payload: refused", False)
    except IOError:
        check("3. not a payload: refused, the install untouched", tree(app) == before)
    make_tar(archive, new)
    data = open(archive, "rb").read()
    open(archive, "wb").write(data[:len(data) // 2])
    try:
        updater.apply_linux(archive, root=app, stage_dir=stage_dir)
        check("3. cut short: an error", False)
    except Exception:
        check("3. cut short: an error, the install untouched", tree(app) == before)

    # a copy that fails halfway (a full disk, a locked file): the launcher and the old code are still there, nothing deleted
    app2 = os.path.join(tmp, "app2")
    shutil.copytree(os.path.join(tmp, "app"), app2)
    write(app2, "tools/launcher.py", b"old launcher", T - 500)
    write(app2, "tools/gone_in_new.py", b"old", T - 500)
    write(app2, "brain/x.py", b"old brain", T - 500)
    write(app2, "VERSION", b"0.2.2", T - 500)
    shutil.rmtree(os.path.join(app2, "native"), ignore_errors=True)
    make_tar(archive, new)
    real_replace = os.replace

    def failing(a, b):
        if str(b).replace("\\", "/").endswith("brain/x.py") or str(b).replace("\\", "/").endswith("native/bin/botcore.dll"):
            raise PermissionError("locked")
        return real_replace(a, b)
    os.replace = failing
    try:
        updater.apply_linux(archive, root=app2, stage_dir=stage_dir)
        check("3. a copy that fails halfway: an error", False)
    except PermissionError:
        os.replace = real_replace
        check("3. a copy that fails halfway: an error, the launcher and the old code still there, nothing deleted",
              read(app2, "tools/launcher.py") is not None and read(app2, "tools/gone_in_new.py") == b"old"
              and read(app2, "user/settings.ini") == b"mine")
        updater.apply_linux(archive, root=app2, stage_dir=stage_dir)
        check("3. ... and the next try finishes it", read(app2, "brain/x.py") == b"NEW brain"
              and read(app2, "tools/gone_in_new.py") is None and read(app2, "tools/launcher.py") == b"NEW launcher")
    finally:
        os.replace = real_replace

    # 4. what an update is, here
    updater.DOWNLOADS = os.path.join(tmp, "updates")
    updater.STATE = os.path.join(tmp, "update.json")
    st = dict(setup_url="http://x/Setup.exe", setup_name="Setup-9.exe", setup_bytes=10, linux_url="http://x/L.tar.gz",
              linux_name="PPG-Linux-9.tar.gz", linux_bytes=8)
    updater.save(st)
    realwine = updater.wine
    updater.wine = lambda: True
    check("4. Linux: the tar.gz", updater.asset(st)[1] == "PPG-Linux-9.tar.gz" and updater.info()["can_install"])
    updater.save({k: v for k, v in st.items() if not k.startswith("linux")})
    check("4. Linux, a release without a tar.gz: nothing to install", not updater.info()["can_install"])
    updater.save(st)
    updater.wine = lambda: False
    check("4. Windows: the Setup", updater.asset(st)[1] == "Setup-9.exe")
    write(tmp, "updates/Setup-9.exe", b"12345")
    check("4. a part of the file is not staged", updater.staged() is None)
    write(tmp, "updates/Setup-9.exe", b"1234567890")
    check("4. the whole file is", updater.staged() is not None)

    # 5. stage while MCC runs: the Setup kept (never fetched again); a failure holds off the next try
    updater._job.update(state="idle", error="")
    check("5. a downloaded Setup: ready, nothing fetched", updater.stage() is False and updater._job["state"] == "ready")
    updater._job.update(state="failed", failed_at=time.time())
    check("5. just failed: wait", not updater.retry_ok() and updater.stage() is False)
    updater._job["failed_at"] = time.time() - 400
    check("5. five minutes on: try again", updater.retry_ok())
    updater._job.update(state="idle", error="")
    updater.clean()
    check("5. clean: the downloads of an update that went in are removed", not os.listdir(updater.DOWNLOADS))
    updater.wine = realwine

    # 6. Linux's process folder
    proc = os.path.join(tmp, "proc")
    write(proc, "123/cmdline", b"/usr/bin/python\x00run.py")
    check("6. no MCC in a command line", not conflicts.linux_mcc_running(proc))
    write(proc, "456/cmdline", b"Z:\\steam\\MCC\\Binaries\\Win64\\MCC-Win64-Shipping.exe\x00-x")
    check("6. MCC in one", conflicts.linux_mcc_running(proc))
    check("6. no such folder (Windows): not running", not conflicts.linux_mcc_running(os.path.join(tmp, "none")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("updater linux OK")
