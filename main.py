import sys
import socket
import threading
import time

import webview
from app import create_app

PORT = 5757
LOCK_PORT = 19823
URL = f"http://127.0.0.1:{PORT}"


def _acquire_lock() -> socket.socket | None:
    """Use a bound socket as a single-instance guard."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", LOCK_PORT))
        sock.listen(1)
        return sock
    except OSError:
        return None


def _start_flask(app) -> None:
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


def main() -> None:
    lock = _acquire_lock()
    if lock is None:
        print("iPhone Backup is already running.")
        sys.exit(0)

    app = create_app()

    flask_thread = threading.Thread(target=_start_flask, args=(app,), daemon=True)
    flask_thread.start()

    # Give Flask a moment to start before opening the window
    time.sleep(1)

    webview.create_window(
        title="iPhone Backup",
        url=URL,
        width=960,
        height=700,
        min_size=(800, 600),
    )
    webview.start()

    lock.close()


if __name__ == "__main__":
    main()
