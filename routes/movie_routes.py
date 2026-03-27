from flask import Blueprint, jsonify, render_template, request

from services.movie_service import get_movie_info_service, submit_movie_service
from services.storage import load_data, save_data

movie_bp = Blueprint("movie", __name__)


@movie_bp.route("/")
def index():
    return render_template("index.html")


@movie_bp.route("/api/movie", methods=["POST"])
def get_movie():
    data = request.get_json(silent=True)

    body, status = get_movie_info_service(data)

    return jsonify(body), status


@movie_bp.route("/api/submit", methods=["POST"])
def submit():
    submission = request.get_json(silent=True)

    body, status = submit_movie_service(submission)

    return jsonify(body), status


@movie_bp.route("/api/load", methods=["GET"])
def load():
    data = load_data()
    return jsonify(data), 200


@movie_bp.route("/api/save", methods=["POST"])
def save():
    data = request.get_json(silent=True) or {}
    save_data(data)
    return jsonify({"message": "success"}), 200
