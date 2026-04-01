from crawlers.crawler import *
from utils.google_sheets import *
import threading


def get_movie_info_service(data):
    if not data:
        return ({"message": "Request body must be valid JSON."}), 400

    url = data.get("url", "").strip()
    if not url:
        return ({"message": "Missing movie URL."}), 400

    try:
        response = movie_info_crawler(url)
    except Exception as exc:
        return (
            ({"message": "Failed to parse movie information.", "error": str(exc)}),
            500,
        )

    if response is None:
        return ({"message": "Movie information was not found."}), 404

    # thread = threading.Thread(
    #     target=image_crawler, args=(parse_movie_url(url), response["image"]), daemon=True
    # )
    # thread.start()

    
    response.update({"message": "success"})
    return (response), 200


def submit_movie_service(submission):
    if not submission:
        return ({"message": "Request body must be valid JSON."}), 400

    url = submission.get("url", "").strip()
    required_fields = {
        "url": url,
        "date": submission.get("date"),
        "quality": submission.get("quality"),
        "rating": submission.get("rating"),
    }
    missing_fields = [field for field, value in required_fields.items() if value in ("", None)]

    if missing_fields:
        return (
            {"message": f"Missing required fields: {', '.join(missing_fields)}."}
        ), 400

    if (
        not submission.get("name")
        or not submission.get("director")
        or not submission.get("year")
        or not submission.get("image")
    ):
        try:
            movie_info = movie_info_crawler(url)
        except Exception as exc:
            return (
                {"message": "Failed to parse movie information.", "error": str(exc)}
            ), 500

        if not movie_info:
            return ({"message": "Movie information was not found."}), 404

        submission.update(movie_info)

    # submission["sheetname"] =  "Sheet1"

    try:
        # response = append_row(submission, status="test")
        response = append_row(submission, status="movie")

    except ValueError as exc:
        return ({"message": str(exc)}), 400
    except Exception as exc:
        return ({"message": "Failed to append row.", "error": str(exc)}), 500

    return response, 200
