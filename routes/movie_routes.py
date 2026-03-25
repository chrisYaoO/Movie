from flask import Blueprint, request, jsonify, render_template
from services.movie_service import get_movie_info_service, submit_movie_service

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
