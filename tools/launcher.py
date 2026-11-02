"""Project Proving Grounds' launcher: the window the Start Menu shortcut opens. It shows what is ready (the game, the
first-time setup, the map tools, mapped maps, mods that can clash), starts MCC with the bots, runs the first-time setup
and opens the tools (Observer, LiDAR Simulator, LiDAR Viewer, nav painter), each in its own app window
(tools/appwindow.py).

A small local server (127.0.0.1 only) serves tools/launcher.html and runs the tasks as their own processes, with
this Python. It stops a while after its window closes, unless a task it started is still running. Starting it again
while it runs just opens its window again.

usage: python -I launcher.py [--port 8793] [--no-window] [--setup]   (--setup: runs the first-time setup if needed)
"""
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import appwindow  # noqa: E402
import conflicts  # noqa: E402
import setup  # noqa: E402
from brain import paths  # noqa: E402

PORT = 8793
IDLE_STOP = 20.0          # seconds without a ping from the window before the server stops (no task running)
LOGS = os.path.join(ROOT, "logs", "launcher")
# task: (script and its arguments, keeps running on its own after it opened its window)
TASKS = {
    "play": (["launch.py"], False),
    "setup": (["setup.py"], False),
    "setup_force": (["setup.py", "--force"], False),
    "observer": (["observer.py", "serve", "--open"], True),
    "lidar_sim": (["lidar_sim.py", "--open"], True),
    "lidar_view": (["lidar.py", "--view", "--open"], True),
    "paint": (["paint.py", "--open"], True),
}
procs = {}                # task: Popen
last_ping = [time.time()]


def version():
    try:
        return open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
    except OSError:
        return "dev"


def lidar_counts():
    """(maps with a LiDAR scan, maps the mod knows)."""
    maps = os.path.join(ROOT, "maps")
    known = [d for d in os.listdir(maps) if not d.startswith("_") and os.path.isdir(os.path.join(maps, d))]
    return sum(os.path.exists(os.path.join(maps, d, "lidar.json")) for d in known), len(known)


def status():
    found = conflicts.scan()
    mapped, total = lidar_counts()
    return dict(version=version(), mcc=paths.mcc(), mcc_running=conflicts.mcc_running(),
                setup=setup.status()[1:], map_tools=bool(paths.map_tool("model2obj")),
                lidar=dict(mapped=mapped, total=total), workshop=conflicts.workshop_count(),
                conflicts=[dict(file=os.path.relpath(p, paths.mcc()), why=w) for p, w in found],
                running={t: p.poll() is None for t, p in procs.items()})


def start(task, clean=False):
    """Starts a task; (ok, message)."""
    if task not in TASKS:
        return False, "unknown task"
    if task in procs and procs[task].poll() is None:
        return True, "already running"
    if task == "play" and clean:
        moved = conflicts.turn_off()
        if moved:                                    # put back once MCC has come and gone (its own process)
            subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "conflicts.py"), "--restore-after-mcc"],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), cwd=ROOT)
    args, _ = TASKS[task]
    os.makedirs(LOGS, exist_ok=True)
    log = open(os.path.join(LOGS, task + ".txt"), "w", encoding="utf-8")
    procs[task] = subprocess.Popen([sys.executable, "-u", "-I", os.path.join(HERE, args[0]), *args[1:]], cwd=ROOT,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return True, "started"


def log_lines(task, skip=0):
    if task not in TASKS:                            # (a known task's log only: the name goes into a path)
        return dict(lines=[], next=0, running=False, code=None)
    try:
        lines = open(os.path.join(LOGS, task + ".txt"), encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        lines = []
    p = procs.get(task)
    return dict(lines=lines[skip:], next=len(lines), running=bool(p and p.poll() is None),
                code=None if not p or p.poll() is None else p.returncode)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, body, ctype="application/json", code=200):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/":
            self.send(open(os.path.join(HERE, "launcher.html"), "rb").read(), "text/html; charset=utf-8")
        elif path == "/status":
            self.send(status())
        elif path.startswith("/log/"):
            skip = int(query.split("=")[1]) if query.startswith("from=") and query[5:].isdigit() else 0
            self.send(log_lines(path[5:], skip))
        else:
            self.send({"error": "not found"}, code=404)

    def do_POST(self):
        if self.headers.get("X-Launcher") != "1":    # only the launcher's own page (a plain form post cannot set it)
            return self.send({"error": "refused"}, code=403)
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        if self.path == "/ping":
            last_ping[0] = time.time()
            self.send({"ok": True})
        elif self.path.startswith("/run/"):
            ok, msg = start(self.path[5:], bool(body.get("clean")))
            self.send({"ok": ok, "message": msg}, code=200 if ok else 400)
        elif self.path == "/folder":
            os.startfile(ROOT)
            self.send({"ok": True})
        elif self.path == "/docs":
            os.startfile(os.path.join(ROOT, "README.md"))
            self.send({"ok": True})
        else:
            self.send({"error": "not found"}, code=404)


def watch_idle(srv):
    """Stops the server once the window has been closed a while and no task of its own is still working."""
    while True:
        time.sleep(2)
        busy = any(p.poll() is None and not TASKS[t][1] for t, p in procs.items())
        if not busy and time.time() - last_ping[0] > IDLE_STOP:
            srv.shutdown()
            return


def main():
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else PORT
    url = f"http://127.0.0.1:{port}/" + ("?setup=1" if "--setup" in sys.argv else "")
    conflicts.restore()                              # (files a clean launch moved aside, if the PC went off since)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:                                  # it runs already: show its window again
        if "--no-window" not in sys.argv:
            appwindow.open_window(url, (1040, 700))
        return
    threading.Thread(target=watch_idle, args=(srv,), daemon=True).start()
    if "--no-window" not in sys.argv:
        appwindow.open_window(url, (1040, 700))
    srv.serve_forever()


if __name__ == "__main__":
    main()
