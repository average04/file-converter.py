from flask import Flask
from pathlib import Path

_window = None
_output_dir: Path = Path.home() / "Documents" / "FileConverter"


def set_window(window) -> None:
    global _window
    _window = window


def get_window():
    return _window


def get_output_dir() -> Path:
    return _output_dir


def set_output_dir(path: str) -> None:
    global _output_dir
    _output_dir = Path(path)
    _output_dir.mkdir(parents=True, exist_ok=True)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit

    from app.routes.converter import bp
    app.register_blueprint(bp)

    return app
