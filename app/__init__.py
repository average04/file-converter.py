from flask import Flask
from app.services.settings_manager import SettingsManager
from app.services.device_detector import DeviceDetector
from app.services.backup_service import BackupService
from pathlib import Path

_settings = SettingsManager()
_detector = DeviceDetector()
_backup = BackupService(
    backup_dir=Path(_settings.get("backup_path")),
)


def get_settings() -> SettingsManager:
    return _settings


def get_detector() -> DeviceDetector:
    return _detector


def get_backup() -> BackupService:
    return _backup


def create_app() -> Flask:
    app = Flask(__name__)

    _detector.start()

    from app.routes.settings import bp as settings_bp
    from app.routes.device import bp as device_bp
    from app.routes.backup import bp as backup_bp

    app.register_blueprint(settings_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(backup_bp)

    return app
