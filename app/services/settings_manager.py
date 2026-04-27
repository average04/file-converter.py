import json
from pathlib import Path

_DEFAULTS = {
    "backup_path": str(Path.home() / "Documents" / "iPhoneBackups"),
    "wifi_enabled": True,
}


class SettingsManager:
    def __init__(self, path: Path = None):
        self._path = path or (Path(__file__).parent.parent.parent / "settings.json")
        self._data = dict(_DEFAULTS)
        if self._path.exists():
            self._data.update(json.loads(self._path.read_text()))

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._path.write_text(json.dumps(self._data, indent=2))

    def all(self) -> dict:
        return dict(self._data)
