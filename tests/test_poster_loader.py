import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from PIL import Image

from services.poster_loader import compress_poster, load_poster


def image_bytes(format_name="PNG"):
    buffer = BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format=format_name)
    return buffer.getvalue()


class PosterLoaderTest(unittest.TestCase):
    def test_compress_poster_returns_jpeg(self):
        result = compress_poster(image_bytes())

        self.assertEqual(Image.open(BytesIO(result)).format, "JPEG")

    @patch("services.poster_loader.requests.get")
    def test_load_poster_skips_non_image_response(self, get):
        non_image = Mock()
        non_image.headers = {"Content-Type": "text/html"}
        non_image.raise_for_status.return_value = None
        image = Mock()
        image.headers = {"Content-Type": "image/webp"}
        image.content = image_bytes("WEBP")
        image.raise_for_status.return_value = None
        get.side_effect = [non_image, image]

        result = load_poster("movie-id", "image-id")

        self.assertEqual(Image.open(BytesIO(result)).format, "JPEG")
        self.assertEqual(get.call_count, 2)

    @patch("services.poster_loader.requests.get")
    def test_load_poster_reports_movie_when_all_candidates_fail(self, get):
        import requests

        get.side_effect = requests.Timeout("timed out")

        with self.assertRaisesRegex(RuntimeError, "movie-id"):
            load_poster("movie-id", "image-id")


if __name__ == "__main__":
    unittest.main()
