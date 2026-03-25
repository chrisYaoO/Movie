import socket
import threading
import time
import webview
from app import app


def start_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def wait_for_server(host="127.0.0.1", port=5000, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


if __name__ == "__main__":
    threading.Thread(target=start_flask, daemon=True).start()
    if not wait_for_server():
        raise RuntimeError("Flask server did not start in time.")
    window = webview.create_window(
        "Movie Parser",
        "http://127.0.0.1:5000", 
        width=820, 
        height=1100, 
        resizable=False
    )
    webview.start()
