import os
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from services.wechat_service import build_html, upload_images, upload_to_draft
from utils.google_sheets import extract


class BuildHtmlCharacterizationTest(unittest.TestCase):
    def test_build_html_renders_movies_and_saves_preview(self):
        template = (
            "<h1>{% for item in items %}{{ item.name }}:"
            "{{ item.image_url }}{% endfor %}</h1>"
        )
        movies = [
            {
                "name": "Movie A",
                "image_url": "https://mmbiz.qpic.cn/movie-a",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir, "templates")
            templates_dir.mkdir()
            Path(templates_dir, "movie_template.html").write_text(
                template,
                encoding="utf-8",
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                html = build_html(movies)
            finally:
                os.chdir(original_cwd)

            preview = Path(templates_dir, "movie_wechat.html")
            self.assertEqual(
                html,
                "<h1>Movie A:https://mmbiz.qpic.cn/movie-a</h1>",
            )
            self.assertEqual(preview.read_text(encoding="utf-8"), html)


class WechatUploadCharacterizationTest(unittest.TestCase):
    @patch("services.wechat_service.requests.post")
    @patch("services.wechat_service.get_access_token", return_value="access-token")
    def test_upload_to_draft_sends_single_news_article_and_returns_media_id(
        self,
        get_access_token,
        post,
    ):
        post.return_value.json.return_value = {"media_id": "draft-media-id"}

        media_id = upload_to_draft("<p>article</p>", "digest text", "Draft title")

        self.assertEqual(media_id, "draft-media-id")
        get_access_token.assert_called_once_with()
        url = post.call_args.args[0]
        body = json.loads(post.call_args.kwargs["data"])
        self.assertEqual(
            url,
            "https://api.weixin.qq.com/cgi-bin/draft/add"
            "?access_token=access-token",
        )
        self.assertEqual(len(body["articles"]), 1)
        self.assertEqual(
            {
                "article_type": body["articles"][0]["article_type"],
                "title": body["articles"][0]["title"],
                "author": body["articles"][0]["author"],
                "digest": body["articles"][0]["digest"],
                "content": body["articles"][0]["content"],
            },
            {
                "article_type": "news",
                "title": "Draft title",
                "author": "看电影的",
                "digest": "digest text",
                "content": "<p>article</p>",
            },
        )

    @patch("services.wechat_service.requests.post")
    @patch("services.wechat_service.image_crawler", return_value=b"poster-bytes")
    @patch("services.wechat_service.get_access_token", return_value="access-token")
    def test_upload_images_adds_wechat_image_url_to_each_movie(
        self,
        get_access_token,
        image_crawler,
        post,
    ):
        movies = [
            {
                "movie_id": "1295644",
                "image_id": "2913554676",
                "name": "Movie A",
            }
        ]
        post.return_value.json.return_value = {
            "url": "https://mmbiz.qpic.cn/movie-a"
        }

        result = upload_images(movies)

        self.assertIs(result, movies)
        self.assertEqual(movies[0]["image_url"], "https://mmbiz.qpic.cn/movie-a")
        get_access_token.assert_called_once_with()
        image_crawler.assert_called_once_with("1295644", "2913554676")
        post.assert_called_once_with(
            "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
            "?access_token=access-token",
            files={
                "media": (
                    "1295644.png",
                    b"poster-bytes",
                    "image/png",
                )
            },
            timeout=20,
        )


class GoogleSheetsDraftExtractionCharacterizationTest(unittest.TestCase):
    @patch("utils.google_sheets.read_id", return_value="spreadsheet-id")
    @patch("utils.google_sheets.load_service_account_credentials")
    @patch("utils.google_sheets.build")
    @patch("utils.google_sheets.get_year_month", return_value=("2026", 3, 4))
    def test_extract_returns_movies_in_period_and_writes_full_sheet_backup(
        self,
        get_year_month,
        build,
        load_credentials,
        read_id,
    ):
        service = Mock()
        build.return_value = service
        service.spreadsheets.return_value.get.return_value.execute.return_value = {
            "sheets": [{"properties": {"title": "2026"}}]
        }
        service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
            "values": [
                [
                    "date",
                    "name",
                    "director",
                    "year",
                    "rating",
                    "quality",
                    "comment",
                    "movie_id",
                    "image_id",
                ],
                [
                    "3/10",
                    "霸王别姬 Farewell My Concubine",
                    "陈凯歌",
                    "1993",
                    "5",
                    "1080p",
                    "March comment",
                    "1291546",
                    "1910924635",
                ],
                [
                    "5/01",
                    "Movie Outside Period",
                    "Director",
                    "2020",
                    "4",
                    "1080p",
                    "May comment",
                    "100",
                    "200",
                ],
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "configs").mkdir()
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                movies, title = extract("movie")
            finally:
                os.chdir(original_cwd)

            backup = json.loads(
                Path(temp_dir, "configs", "backup_2026.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(title, "2026 3-4月观影")
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["name"], "霸王别姬")
        self.assertEqual(movies[0]["subname"], "Farewell My Concubine")
        self.assertEqual(len(backup), 2)
        read_id.assert_called_with("movie")


if __name__ == "__main__":
    unittest.main()
