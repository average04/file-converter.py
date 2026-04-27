import threading
import time
from typing import Callable, Optional

try:
    from pymobiledevice3.lockdown import create_using_usbmux, create_using_tcp
    from pymobiledevice3.exceptions import NoDeviceConnectedError
    _PYMOBILE_AVAILABLE = True
except ImportError:
    _PYMOBILE_AVAILABLE = False
    create_using_usbmux = None
    create_using_tcp = None
    NoDeviceConnectedError = Exception

try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    _ZEROCONF_AVAILABLE = True
except ImportError:
    _ZEROCONF_AVAILABLE = False


class DeviceDetector:
    def __init__(self):
        self._device: Optional[dict] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._listeners: list[Callable] = []
        self._wifi_hosts: list[str] = []
        self._zeroconf: Optional[object] = None

    def current_device(self) -> Optional[dict]:
        with self._lock:
            return self._device

    def add_listener(self, fn: Callable) -> None:
        self._listeners.append(fn)

    def _notify(self, device: Optional[dict]) -> None:
        for fn in self._listeners:
            try:
                fn(device)
            except Exception:
                pass

    def _probe_usb(self) -> Optional[dict]:
        if not _PYMOBILE_AVAILABLE:
            return None
        try:
            lockdown = create_using_usbmux()
            storage = {}
            try:
                storage = lockdown.get_value("com.apple.disk_usage") or {}
            except Exception:
                pass
            return {
                "name": lockdown.display_name,
                "model": lockdown.product_type,
                "ios_version": lockdown.product_version,
                "udid": lockdown.udid,
                "storage": {
                    "TotalDataCapacity": storage.get("TotalDataCapacity", 0),
                    "TotalDataAvailable": storage.get("TotalDataAvailable", 0),
                },
                "connection": "USB",
            }
        except Exception:
            return None

    def _probe_wifi(self, host: str) -> Optional[dict]:
        if not _PYMOBILE_AVAILABLE:
            return None
        try:
            lockdown = create_using_tcp(host)
            storage = {}
            try:
                storage = lockdown.get_value("com.apple.disk_usage") or {}
            except Exception:
                pass
            return {
                "name": lockdown.display_name,
                "model": lockdown.product_type,
                "ios_version": lockdown.product_version,
                "udid": lockdown.udid,
                "storage": {
                    "TotalDataCapacity": storage.get("TotalDataCapacity", 0),
                    "TotalDataAvailable": storage.get("TotalDataAvailable", 0),
                },
                "connection": "WiFi",
                "host": host,
            }
        except Exception:
            return None

    def _start_wifi_discovery(self) -> None:
        if not _ZEROCONF_AVAILABLE:
            return

        detector = self

        class _Listener:
            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info and info.addresses:
                    import socket
                    host = socket.inet_ntoa(info.addresses[0])
                    if host not in detector._wifi_hosts:
                        detector._wifi_hosts.append(host)

            def remove_service(self, zc, type_, name):
                pass

            def update_service(self, zc, type_, name):
                pass

        self._zeroconf = Zeroconf()
        ServiceBrowser(self._zeroconf, "_apple-mobdev2._tcp.local.", _Listener())

    def _poll(self) -> None:
        while self._running:
            device = self._probe_usb()

            if not device:
                for host in list(self._wifi_hosts):
                    device = self._probe_wifi(host)
                    if device:
                        break

            with self._lock:
                changed = device != self._device
                self._device = device

            if changed:
                self._notify(device)

            time.sleep(3)

    def start(self) -> None:
        self._running = True
        self._start_wifi_discovery()
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._zeroconf:
            self._zeroconf.close()
