"""Offline check for the LiDAR 3D view's port (a stored view and a LiDAR match both served
127.0.0.1:8797 and the browser showed the stored map): a second stored view is refused, a live match
takes the port over from a stored view, and the page's /maps then answers from the live hub.

usage: python -I test_view_port.py      -> "view port OK"
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lidar  # noqa: E402

PORT = 8898


def mode():
    return json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/maps", timeout=30).read())["mode"]


def main():
    stored = lidar.Hub(lidar.Recorder("h2a_ca_lockout", count_run=False), "stored")
    a = lidar.serve(stored, PORT)
    assert a is not None and mode() == "stored", "stored view did not start"
    assert lidar.serve(lidar.Hub(lidar.Recorder("h2a_ca_lockout", count_run=False), "stored"), PORT) is None, \
        "a second stored view shared the port"
    live = lidar.Hub(lidar.Recorder("h2a_ca_lockout", count_run=False), "live")
    b = lidar.serve(live, PORT)
    assert b is not None, "the live match could not take the port"
    assert getattr(stored, "yielded", False), "the stored view did not yield"
    time.sleep(0.3)
    assert mode() == "live", "the page still gets the stored view"
    b.shutdown()
    b.server_close()
    print("view port OK")


if __name__ == "__main__":
    main()
