from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

from crawler import *
from append import *

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/app.js")
def app_js():
    return send_from_directory(BASE_DIR, "app.js")

@app.route("/api/movie", methods=["POST"])
def get_movie():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Request body must be valid JSON."}), 400

    url = data.get("url", "").strip()
    if not url:
        return jsonify({"message": "Missing movie URL."}), 400

    try:
        response = movie_info_crawler(url)
    except Exception as exc:
        return jsonify({
            "message": "Failed to parse movie information.",
            "error": str(exc)
        }), 500

    if response is None:
        return jsonify({"message": "Movie information was not found."}), 404

    response.update({"message": "success"})
    return jsonify(response), 200

@app.route("/api/submit", methods=["POST"])
def submit():
    submission = request.get_json(silent=True)
    if not submission:
        return jsonify({"message": "Request body must be valid JSON."}), 400

    if not submission["name"] or not submission["director"] or not submission["year"]:
        try:
            movie_info = movie_info_crawler(submission["url"])
        except Exception as exc:
            return jsonify({
                "message": "Failed to parse movie information.",
                "error": str(exc)
            }), 500

        if not movie_info:
            return jsonify({"message": "Movie information was not found."}), 404

        submission.update(movie_info)
    submission["sheetname"] = "Sheet1"

    try:
        response = append_row(submission, status="test")
    except ValueError as exc:
        return jsonify({
            "message": str(exc)
        }), 400
    except Exception as exc:
        return jsonify({
            "message": "Failed to append row.",
            "error": str(exc)
        }), 500

    return jsonify(response["message"]), 200

if __name__ == "__main__":
    app.run(debug=True)
