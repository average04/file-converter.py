import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

try:
    from pymobiledevice3.lockdown import create_using_usbmux, create_using_tcp
    from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
    _PYMOBILE_AVAILABLE = True
except ImportError:
    _PYMOBILE_AVAILABLE = False
    create_using_usbmux = None
    create_using_tcp = None
    Mobilebackup2Service = None


class BackupService:
    def __init__(self, backup_dir: Path, history_path: Path = None):
        self._backup_dir = backup_dir
        self._history_path = history_path or (Path(__file__).parent.parent.parent / "backup_history.json")
        self._running = False
        self._cancelled = False
        self._lock = threading.Lock()
        self._progress_listeners: list[Callable] = []
        self._history: list[dict] = []
        if self._history_path.exists():
            try:
                self._history = json.loads(self._history_path.read_text())
            except Exception:
                self._history = []

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def history(self) -> list[dict]:
        return list(self._history)

    def add_progress_listener(self, fn: Callable) -> None:
        if fn not in self._progress_listeners:
            self._progress_listeners.append(fn)

    def _notify_progress(self, event: dict) -> None:
        for fn in self._progress_listeners:
            try:
                fn(event)
            except Exception:
                pass

    def _append_history(self, entry: dict) -> None:
        self._history.append(entry)
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        self._history_path.write_text(json.dumps(self._history, indent=2))

    def cancel(self) -> None:
        self._cancelled = True

    def start(self, device_info: dict, destination: Optional[Path] = None) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._cancelled = False

        dest = destination or self._backup_dir
        thread = threading.Thread(target=self._run, args=(device_info, dest), daemon=True)
        thread.start()

    def _run(self, device_info: dict, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        try:
            self._notify_progress({"status": "started", "percent": 0})

            if not _PYMOBILE_AVAILABLE:
                raise RuntimeError("pymobiledevice3 is not installed")

            connection = device_info.get("connection", "USB")
            if connection == "WiFi":
                lockdown = create_using_tcp(device_info["host"])
            else:
                lockdown = create_using_usbmux()

            with Mobilebackup2Service(lockdown) as mb2:
                last_percent = [0]

                def on_progress(percent: float) -> None:
                    if self._cancelled:
                        raise InterruptedError("Backup cancelled by user")
                    p = int(percent)
                    if p != last_percent[0]:
                        last_percent[0] = p
                        self._notify_progress({"status": "in_progress", "percent": p})

                mb2.backup(
                    full=True,
                    backup_directory=str(destination),
                    progress_callback=on_progress,
                )

            size = sum(f.stat().st_size for f in destination.rglob("*") if f.is_file())
            entry = {
                "device": device_info.get("name", "iPhone"),
                "date": datetime.now().isoformat(),
                "size": size,
                "path": str(destination),
            }
            self._append_history(entry)
            self._notify_progress({"status": "complete", "percent": 100, "entry": entry})

        except InterruptedError:
            self._notify_progress({"status": "cancelled", "percent": 0})
        except Exception as e:
            self._notify_progress({"status": "error", "message": str(e)})
        finally:
            with self._lock:
                self._running = False
