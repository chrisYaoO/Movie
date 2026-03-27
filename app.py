import os
import threading
import time
import webbrowser
from threading import Timer

from flask import Flask, jsonify

from routes.movie_routes import movie_bp

DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("PORT", "5000"))
RUN_MODE = os.getenv("APP_RUN_MODE", "server").strip().lower()
last_client_ping = None
shutdown_lock = threading.Lock()


def create_app():
    app = Flask(__name__)
    app.register_blueprint(movie_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.post("/api/client-ping")
    def client_ping():
        global last_client_ping
        with shutdown_lock:
            last_client_ping = time.time()
        return jsonify({"message": "ok"}), 200

    return app


app = create_app()


def client_monitor():
    global last_client_ping
    while True:
        time.sleep(1)
        with shutdown_lock:
            if last_client_ping and time.time() - last_client_ping > 5:
                os._exit(0)


def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{DEFAULT_PORT}/")


def run_desktop_mode():
    threading.Thread(target=client_monitor, daemon=True).start()
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=DEFAULT_PORT, debug=True, use_reloader=False)


def run_server_mode():
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    if RUN_MODE == "desktop":
        run_desktop_mode()
    else:
        run_server_mode()
