import json
import queue
import threading
from pathlib import Path
from flask import Blueprint, jsonify, request, render_template, Response
from app import get_backup, get_detector, get_settings

bp = Blueprint("backup", __name__)

_sse_clients: list[queue.Queue] = []
_sse_lock = threading.Lock()
_listener_registered = False


def _push_progress(event: dict):
    msg = f"data: {json.dumps(event)}\n\n"
    with _sse_lock:
        for q in list(_sse_clients):
            q.put(msg)


def _ensure_listener():
    global _listener_registered
    if not _listener_registered:
        get_backup().add_progress_listener(_push_progress)
        _listener_registered = True


@bp.get("/backup")
def backup_page():
    return render_template("backup.html", active="dashboard")


@bp.get("/history")
def history_page():
    return render_template("history.html", active="history")


@bp.post("/api/backup/start")
def start_backup():
    _ensure_listener()
    device = get_detector().current_device()
    if not device:
        return jsonify({"error": "No device connected"}), 400

    if get_backup().is_running():
        return jsonify({"error": "Backup already in progress"}), 409

    data = request.get_json() or {}
    destination = Path(data["path"]) if data.get("path") else None

    get_backup().start(device_info=device, destination=destination)
    return jsonify({"status": "started"})


@bp.post("/api/backup/cancel")
def cancel_backup():
    get_backup().cancel()
    return jsonify({"status": "cancelled"})


@bp.get("/api/backup/stream")
def backup_stream():
    _ensure_listener()
    q: queue.Queue = queue.Queue()
    with _sse_lock:
        _sse_clients.append(q)

    def generate():
        try:
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


@bp.get("/api/backup/history")
def get_history():
    return jsonify(get_backup().history())
