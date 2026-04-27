from flask import Blueprint, jsonify, request, render_template
from app import get_settings

bp = Blueprint("settings", __name__)

_ALLOWED_KEYS = {"backup_path", "wifi_enabled"}


@bp.get("/settings")
def settings_page():
    return render_template("settings.html", active="settings")


@bp.get("/api/settings")
def get_settings_route():
    return jsonify(get_settings().all())


@bp.post("/api/settings")
def update_settings():
    data = request.get_json() or {}
    for key, value in data.items():
        if key in _ALLOWED_KEYS:
            get_settings().set(key, value)
    return jsonify(get_settings().all())
