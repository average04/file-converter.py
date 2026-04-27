import json
import queue
import threading
from flask import Blueprint, jsonify, render_template, Response
from app import get_detector

bp = Blueprint("device", __name__)

_sse_clients: list[queue.Queue] = []
_sse_lock = threading.Lock()
_listener_registered = False


def _push_event(device):
    payload = json.dumps(device) if device else "null"
    msg = f"data: {payload}\n\n"
    with _sse_lock:
        for q in list(_sse_clients):
            q.put(msg)


def _ensure_listener():
    global _listener_registered
    if not _listener_registered:
        get_detector().add_listener(_push_event)
        _listener_registered = True


@bp.get("/")
def dashboard():
    _ensure_listener()
    return render_template("index.html", active="dashboard")


@bp.get("/api/device")
def get_device():
    device = get_detector().current_device()
    return jsonify(device)


@bp.get("/api/device/stream")
def device_stream():
    _ensure_listener()
    q: queue.Queue = queue.Queue()
    with _sse_lock:
        _sse_clients.append(q)

    def generate():
        try:
            device = get_detector().current_device()
            payload = json.dumps(device) if device else "null"
            yield f"data: {payload}\n\n"
            while True:
                msg = q.get()
                yield msg
        finally:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
