"""The launcher's update check: it looks for new versions on GitHub, with when it last looked, and installs them on its
own (automatic updates, on unless the player turns them off: tools/launcher.py auto_update); off, it says so and the
Update button installs.

GitHub's latest release of the public repository is read at most every CHECK_EVERY (or when asked); the result and the
player's choice are kept in user/update.json (kept by updates and Repair). An update is the release's Windows Setup,
downloaded to user/updates and run silently over this folder (/UPDATE=1: the installer opens the launcher again after).
Nothing is installed while MCC runs; with automatic updates off, nothing without the Update button.

usage: python -I updater.py            prints what it finds     python -I updater.py --selftest
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RELEASES = "https://github.com/AyoItzKye/project-proving-grounds/releases"
REPO = RELEASES.split("github.com/")[1].rsplit("/releases", 1)[0]
API = f"https://api.github.com/repos/{REPO}/releases/latest"
CHECK_EVERY = 6 * 3600          # seconds between automatic checks
RETRY_S = 300                   # seconds after a failed download or install before the next try
STATE = os.path.join(ROOT, "user", "update.json")
DOWNLOADS = os.path.join(ROOT, "user", "updates")
# a release updated in place (same-day fixes) keeps its version: each build has a stamp (BUILD beside VERSION), the
# release's notes carry it (<!-- build: ... -->, tools/release_notes.py), and a newer stamp of the same version is an
# update too. What is new comes from that release's own docs/UPDATES.md, all of it since the player's copy: every version
# newer than ours, and of ours every item stamped after our build (one section per version, its items stamped)
NOTES = f"https://api.github.com/repos/{REPO}/contents/docs/UPDATES.md?ref={{tag}}"   # (not raw.githubusercontent.com:
#   it keeps a moved tag's old file for 5 minutes)
BUILD_MARK = re.compile(r"<!--\s*build:\s*(\d{8}-\d{4})\s*-->")
SECTION = re.compile(r"<summary><b>(.*?)</b>(.*?)</summary>(.*?)</details>", re.S)
_lock = threading.Lock()
_job = dict(state="idle", done=0, total=0, error="")   # idle, downloading, ready (downloaded, MCC runs), installing, failed


def current():
    try:
        return open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
    except OSError:
        return "dev"


def build():
    """This copy's build stamp (BUILD, "20261106-2245"); "" for one built before stamps (older than any stamped)."""
    try:
        return open(os.path.join(ROOT, "BUILD"), encoding="utf-8").read().strip()
    except OSError:
        return ""


def parse_updates(md):
    """docs/UPDATES.md as [dict(name, key, title, items=[dict(head, build, text)])], newest first: each version's
    <details> section (one per version, "0.2.2"), its "+ Added" / "- Fixed" lists, every top-level item with the build
    stamp at its start (<!-- build: ... -->: the build, or in-place update, it came in; "" before stamps)."""
    out = []
    for name, title, body in SECTION.findall(md or ""):
        items, head = [], ""
        for line in body.splitlines():
            h = re.match(r"#{2,6}\s+(.*)", line)
            if h:
                head = h.group(1).strip()
            elif line.startswith("- "):
                m = BUILD_MARK.search(line)
                items.append(dict(head=head, build=m.group(1) if m else "",
                                  text="- " + BUILD_MARK.sub("", line[2:]).strip()))
            elif items and line.strip():
                items[-1]["text"] += "\n" + line.rstrip()     # (its sub-items)
        out.append(dict(name=name.strip(), key=version_key(name), title=title.strip(" :\n"), items=items))
    return out


def items_text(items):
    """Items as markdown under their headings, in their order."""
    out, head = [], None
    for i in items:
        if i["head"] != head:
            head = i["head"]
            out.append(("\n" if out else "") + f"### {head}")
        out.append(i["text"])
    return "\n".join(out).strip()


def news(md, cur, cur_build):
    """What is new for a copy of version cur and build cur_build: [dict(title, text)], newest first: every version
    newer than cur, whole; of cur's own version (the same major.minor.patch: one section per version, its builds and
    in-place updates in it), the items stamped after cur_build; for a copy from before build stamps all of it when the
    version has stamped items (updated since), else nothing."""
    ck = version_key(cur)
    out = []
    for sec in parse_updates(md):
        if not ck or not sec["key"]:
            continue
        if sec["key"][:3] > ck[:3]:
            out.append(dict(title=f"{sec['name']}{(' ' + sec['title']) if sec['title'] else ''}",
                            text=items_text(sec["items"])))
        elif sec["key"][:3] == ck[:3]:
            # (a copy from before stamps: all of it if the version was updated in place since, else it is this version)
            stamped = any(i["build"] for i in sec["items"])
            newer = [i for i in sec["items"] if (i["build"] > cur_build if cur_build else stamped)]
            if newer:
                out.append(dict(title=f"{sec['name']}: updated since your copy", text=items_text(newer)))
    return out


def version_key(v):
    """(major, minor, patch, build) from "0.2.2-s165", "v0.2.2 s165", "0.2.1" (build 0); None for "dev" or junk."""
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?(?:\D+s?(\d+))?", str(v or ""))
    if not m:
        return None
    return tuple(int(x or 0) for x in m.groups())


def load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), indent=1)
    os.replace(tmp, STATE)


def check(force=False):
    """Reads GitHub's latest release (unless checked within CHECK_EVERY and not forced); returns info()."""
    st = load()
    if not force and time.time() - st.get("checked", 0) < CHECK_EVERY:
        return info()
    try:
        req = urllib.request.Request(API, headers={"User-Agent": "ProjectProvingGrounds-launcher",
                                                   "Accept": "application/vnd.github+json"})
        rel = json.load(urllib.request.urlopen(req, timeout=8))
        setup = next((a for a in rel.get("assets", []) if a.get("name", "").lower().endswith(".exe")
                      and "setup" in a["name"].lower()), None)
        linux = next((a for a in rel.get("assets", []) if re.search(r"-linux-.*\.tar\.gz$", a.get("name", "").lower())), None)
        body = rel.get("body") or ""
        st.update(checked=time.time(), latest=rel.get("tag_name", ""), title=rel.get("name", ""),
                  url=rel.get("html_url", RELEASES), setup_url=setup["browser_download_url"] if setup else "",
                  setup_name=setup["name"] if setup else "", setup_bytes=setup.get("size", 0) if setup else 0, error="",
                  linux_url=linux["browser_download_url"] if linux else "", linux_name=linux["name"] if linux else "",
                  linux_bytes=linux.get("size", 0) if linux else 0,
                  latest_build=max(BUILD_MARK.findall(body), default=""), body=body)
        try:                                        # what is new: that release's own notes (news); its body if not
            req = urllib.request.Request(NOTES.format(tag=st["latest"]), headers={"User-Agent": "ProjectProvingGrounds-launcher",
                                                                                  "Accept": "application/vnd.github.raw"})
            st["notes_md"] = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "replace")
        except Exception:
            st["notes_md"] = ""
    except Exception as e:                          # offline, GitHub down, rate limited: say so, keep the last answer
        st.update(checked_try=time.time(), error=f"Could not reach GitHub ({type(e).__name__}).")
    save(st)
    return info()


def is_newer(cur, cur_build, latest, latest_build):
    """A newer version, or the same version built later (a release updated in place: its notes' newest build stamp)."""
    ck, lk = version_key(cur), version_key(latest)
    if not (ck and lk):
        return False
    return lk > ck or (lk == ck and bool(latest_build) and latest_build > (cur_build or ""))


def info():
    st = load()
    cur, latest, mine, theirs = current(), st.get("latest", ""), build(), st.get("latest_build", "")
    available = is_newer(cur, mine, latest, theirs)
    same = available and version_key(cur) == version_key(latest)
    md = st.get("notes_md", "")
    if theirs and theirs not in md:                  # (its UPDATES.md not read, or an older copy of it)
        md = ""
    new = news(md, cur, mine) if available else []
    if available and not new and st.get("body"):     # then the release's own text; of our version, the updates after ours
        parts = BUILD_MARK.split(st["body"])          # [head, stamp, text, stamp, text ...]
        newer = [parts[k + 1].strip() for k in range(1, len(parts) - 1, 2) if parts[k] > mine] if same else []
        new = [dict(title=st.get("title") or latest, text="\n\n".join(newer) or BUILD_MARK.sub("", st["body"]).strip())]
    return dict(current=cur, latest=latest, title=st.get("title", ""), url=st.get("url", RELEASES),
                available=available, same_version=same, build=mine, latest_build=theirs, news=new,
                checked=st.get("checked", 0), error=st.get("error", ""),
                auto=bool(st.get("auto", True)), can_install=bool(asset(st)[0]), staged=bool(staged()),
                job=dict(_job))


def set_auto(on):
    st = load()
    st["auto"] = bool(on)
    save(st)
    return info()


def wine():
    """Steam Deck / Linux (Wine, Proton): the Windows Setup does not run there; the Linux tar.gz is what an update is."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from brain import paths
    return paths.wine()


def asset(st):
    """(url, name, bytes) of what an update here downloads: the release's Setup, or on Linux its tar.gz."""
    k = "linux" if wine() else "setup"
    return st.get(k + "_url", ""), st.get(k + "_name", ""), st.get(k + "_bytes", 0)


def staged():
    """The latest release's download for this system, whole in user/updates and waiting there (its size is the release
    asset's), or None."""
    _, name, size = asset(load())
    if not name:
        return None
    path = os.path.join(DOWNLOADS, os.path.basename(name))
    try:
        return path if os.path.getsize(path) == (size or os.path.getsize(path)) else None
    except OSError:
        return None


def busy():
    """A download or an install is under way."""
    return _job["state"] in ("downloading", "installing")


def clean():
    """Downloads of an update that went in, left in user/updates (0.5 GB each), removed. Not while one is under way."""
    import shutil
    if busy() or not os.path.isdir(DOWNLOADS):
        return
    for f in os.listdir(DOWNLOADS):
        p = os.path.join(DOWNLOADS, f)
        try:
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        except OSError:
            pass


def retry_ok():
    """False for RETRY_S after a failed download or install: the launcher's look every few seconds while MCC runs does
    not hammer GitHub."""
    return not (_job["state"] == "failed" and time.time() - _job.get("failed_at", 0.0) < RETRY_S)


def stage():
    """Downloads the latest Setup now without running it (MCC runs: the bots are loaded into it, nothing is replaced
    under it); install() then runs it as soon as MCC is closed. True when a download started."""
    with _lock:
        if _job["state"] in ("downloading", "installing") or not retry_ok():
            return False
        if staged():
            _job.update(state="ready", error="")
            return False
        _job.update(state="downloading", done=0, total=0, error="")
    st = load()

    def run():
        try:
            download(*asset(st)[:2])
            _job["state"] = "ready"
        except Exception as e:
            _job.update(state="failed", failed_at=time.time(), error=f"The update could not be downloaded "
                        f"({type(e).__name__}). It tries again; or download it from the releases page.")
    threading.Thread(target=run, daemon=True).start()
    return True


def download(url, name):
    """The Setup into user/updates (a .part file renamed when whole); its path, or raises. Setups of other versions left
    there by earlier updates are removed (0.5 GB each)."""
    os.makedirs(DOWNLOADS, exist_ok=True)
    path = os.path.join(DOWNLOADS, os.path.basename(name))
    for old in os.listdir(DOWNLOADS):
        if os.path.join(DOWNLOADS, old) not in (path, path + ".part"):
            try:
                os.remove(os.path.join(DOWNLOADS, old))
            except OSError:
                pass
    req = urllib.request.Request(url, headers={"User-Agent": "ProjectProvingGrounds-launcher"})
    with urllib.request.urlopen(req, timeout=30) as r, open(path + ".part", "wb") as f:
        _job["total"] = int(r.headers.get("Content-Length") or 0)
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            _job["done"] += len(chunk)
    if _job["total"] and _job["done"] != _job["total"]:
        raise IOError("the download stopped early")
    os.replace(path + ".part", path)
    return path


def install(on_start=None):
    """Downloads the latest Setup and runs it over this folder, silently (the player asked: the Update button, or
    automatic updates on). on_start(): called once the installer runs (the launcher closes everything of the mod). A
    Setup already downloaded (stage) is not downloaded again."""
    with _lock:
        if _job["state"] in ("downloading", "installing"):
            return False
        _job.update(state="downloading", done=0, total=0, error="")
    st = load()

    def run():
        try:
            url, name, _ = asset(st)
            setup = staged() or download(url, name)
            _job["state"] = "installing"
            if wine():                                       # Steam Deck / Linux: the tar.gz's payload over this folder
                apply_linux(setup)
                relaunch_linux()
            else:
                subprocess.Popen([setup, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/UPDATE=1", f"/DIR={ROOT}", "/TASKS="],
                                 cwd=os.path.dirname(ROOT), creationflags=0x00000008)      # DETACHED_PROCESS
            if on_start:
                on_start()
        except Exception as e:
            _job.update(state="failed", failed_at=time.time(),
                        error=f"The update could not be installed ({type(e).__name__}). It tries again in a few "
                              "minutes; or download it from the releases page.")
    threading.Thread(target=run, daemon=True).start()
    return True


# Code and documents an update clears first (installer/linux/install.sh does the same, and the Windows installer): what
# the new version no longer has must not stay. The player's logs, maps, LiDAR scans, settings (user/) and the art the
# setup built are not touched.
LINUX_CLEAR_DIRS = ("docs", "ghidra", "native/tests", "tools/menu_titles", "tools/__pycache__", "brain/__pycache__")
LINUX_CLEAR_FILES = (("tools", (".py", ".html", ".ps1")), ("brain", (".py",)), ("native", (".cpp", ".h", ".bat")))


def apply_linux(archive, root=None, stage_dir=None):
    """The update on Steam Deck / Linux, as installer/linux/install.sh does it, in Python (Wine cannot run the shell
    script, and the old scripts a player has could not be taught new tricks): the tar.gz's payload/ unpacked beside the
    install (checked: a launcher, the Windows Python, the Linux scripts), the previous version's code and documents
    the payload copied over the folder, then what the new version lacks cleared; a file with the same bytes is left (the runtime,
    the models: most of the 1 GB). Nothing of the install is touched until the whole payload is unpacked and checked, nothing deleted until all of it is in, and
    a failed copy is picked up again by the next try (the same files are skipped). Not tested under Wine itself: the
    steps are the file operations of the Windows update's tests (tools/test_updater.py)."""
    import filecmp
    import shutil
    import tarfile
    root = root or ROOT
    stage_dir = stage_dir or os.path.join(DOWNLOADS, "linux_payload")
    shutil.rmtree(stage_dir, ignore_errors=True)
    os.makedirs(stage_dir)
    with tarfile.open(archive, "r:gz") as tf:
        for m in tf:
            parts = m.name.replace("\\", "/").split("/")
            if len(parts) < 3 or parts[1] != "payload" or ".." in parts or m.name.startswith("/") or not (m.isfile() or m.isdir()):
                continue
            dest = os.path.join(stage_dir, *parts[2:])
            if m.isdir():
                os.makedirs(dest, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with tf.extractfile(m) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
            os.utime(dest, (m.mtime, m.mtime))
    for must in ("tools/launcher.py", "python/python.exe", "installer/linux/common.sh", "VERSION", "BUILD"):
        if not os.path.isfile(os.path.join(stage_dir, *must.split("/"))):
            raise IOError(f"the update is not a Project Proving Grounds payload ({must} missing)")
    # (1) every file of the payload over the install: nothing of the old version is deleted until all of these went in,
    # so a copy that fails (a full disk) leaves the old files and the new ones, never a launcher missing; the next try
    # skips what went in
    new = set()
    for dp, _, fs in os.walk(stage_dir):
        rel = os.path.relpath(dp, stage_dir)
        os.makedirs(os.path.join(root, rel) if rel != "." else root, exist_ok=True)
        for f in fs:
            src, dst = os.path.join(dp, f), os.path.join(root, rel, f) if rel != "." else os.path.join(root, f)
            new.add(os.path.normcase(os.path.normpath(dst)))
            if os.path.isfile(dst) and os.path.getsize(src) == os.path.getsize(dst) and filecmp.cmp(src, dst, shallow=False):
                continue                               # (the same bytes: the runtime, the models: most of the 1 GB)
            if f.endswith(".sh"):                      # (a script is written over the old file: its +x stays)
                with open(src, "rb") as i, open(dst, "wb") as o:
                    shutil.copyfileobj(i, o, 1 << 20)
            else:                                      # (any other file beside it, then swapped in: a DLL a running MCC
                shutil.copyfile(src, dst + ".new")     # has loaded keeps the old file, it is not written through)
                os.replace(dst + ".new", dst)
            shutil.copystat(src, dst)

    # (2) then what the new version no longer has: the old code and documents install.sh clears
    def stale(path):
        return os.path.isfile(path) and os.path.normcase(os.path.normpath(path)) not in new
    for d in LINUX_CLEAR_DIRS:
        for dp, _, fs in os.walk(os.path.join(root, *d.split("/")), topdown=False):
            for f in fs:
                if stale(os.path.join(dp, f)):
                    os.remove(os.path.join(dp, f))
            if not os.listdir(dp):
                os.rmdir(dp)
    for d, exts in LINUX_CLEAR_FILES:
        base = os.path.join(root, d)
        for f in os.listdir(base) if os.path.isdir(base) else ():
            if f.lower().endswith(exts) and stale(os.path.join(base, f)):
                os.remove(os.path.join(base, f))
    shutil.rmtree(stage_dir, ignore_errors=True)
    try:
        os.remove(archive)
    except OSError:
        pass


def relaunch_linux():
    """The launcher again on the new files a few seconds from now (this one is closing: its port is free by then)."""
    code = ("import subprocess, sys, time; time.sleep(6); subprocess.Popen([sys.argv[1], '-I', sys.argv[2], '--no-window'], "
            "cwd=sys.argv[3])")
    p = subprocess.Popen([sys.executable, "-I", "-c", code, sys.executable, os.path.join(ROOT, "tools", "launcher.py"), ROOT],
                         cwd=ROOT)
    _keep.add(p.pid)


_keep = set()


def keep_pids():
    """Processes the launcher's closing for the update must leave running (the helper that starts it again)."""
    return set(_keep)


def selftest():
    assert version_key("0.2.2-s165") == (0, 2, 2, 165) and version_key("v0.2.2 s165") == (0, 2, 2, 165)
    assert version_key("0.2.1") == (0, 2, 1, 0) and version_key("dev") is None
    assert version_key("v0.2.2-s166") > version_key("0.2.2-s165") > version_key("0.2.1")
    assert version_key("v0.3.0") > version_key("0.2.9-s999")
    print("updater OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(json.dumps(check(force=True), indent=1))
