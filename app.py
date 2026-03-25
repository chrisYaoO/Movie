import os
import threading
import time
import webbrowser
from threading import Timer
from flask import Flask, jsonify
from routes.movie_routes import movie_bp

app = Flask(__name__)
app.register_blueprint(movie_bp)
APP_URL = "http://127.0.0.1:5000/"
last_client_ping = None
shutdown_lock = threading.Lock()


def client_monitor():
    global last_client_ping
    while True:
        time.sleep(1)
        with shutdown_lock:
            if last_client_ping and time.time() - last_client_ping > 5:
                os._exit(0)

def open_browser():
    webbrowser.open_new(APP_URL)


@app.post("/api/client-ping")
def client_ping():
    global last_client_ping
    with shutdown_lock:
        last_client_ping = time.time()
    return jsonify({"message": "ok"}), 200

if __name__ == "__main__":
    threading.Thread(target=client_monitor, daemon=True).start()
    Timer(1, open_browser).start()
    app.run(debug=True, use_reloader=False)
