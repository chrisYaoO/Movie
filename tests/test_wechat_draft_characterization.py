import os
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from services.draft_selection import DraftMovie, DraftPeriod
from services.wechat_service import build_html, upload_images, upload_to_draft
from services.wechat_client import (
    DraftCreationResultUnknown,
    WeChatApiError,
    WeChatClient,
    WeChatConfiguration,
)
from utils.google_sheets import extract


TEST_CONFIG = WeChatConfiguration(
    app_id="app-id",
    app_secret="app-secret",
    author="看电影的",
    thumb_media_id="thumb-id",
    source_url="https://example.com",
)


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

            preview = Path(temp_dir, "outputs", "movie_wechat.html")
            html = build_html(
                movies,
                template_path=Path(templates_dir, "movie_template.html"),
                preview_path=preview,
            )
            self.assertEqual(
                html,
                "<h1>Movie A:https://mmbiz.qpic.cn/movie-a</h1>",
            )
            self.assertEqual(preview.read_text(encoding="utf-8"), html)


class WechatUploadCharacterizationTest(unittest.TestCase):
    @patch("services.wechat_client.requests.post")
    @patch("services.wechat_service.get_access_token", return_value="access-token")
    def test_upload_to_draft_sends_single_news_article_and_returns_media_id(
        self,
        get_access_token,
        post,
    ):
        post.return_value.json.return_value = {"media_id": "draft-media-id"}

        with patch(
            "services.wechat_service.WeChatConfiguration.load",
            return_value=TEST_CONFIG,
        ):
            media_id = upload_to_draft(
                "<p>article</p>", "digest text", "Draft title"
            )

        self.assertEqual(media_id, "draft-media-id")
        get_access_token.assert_called_once_with()
        url = post.call_args.args[0]
        body = json.loads(post.call_args.kwargs["data"].decode("utf-8"))
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
        self.assertEqual(post.call_args.kwargs["timeout"], 20)
        self.assertEqual(
            post.call_args.kwargs["headers"],
            {"Content-Type": "application/json; charset=utf-8"},
        )

    def test_create_draft_sends_unicode_title_as_json(self):
        http = Mock()
        http.get.return_value.json.return_value = {"access_token": "access-token"}
        http.post.return_value.json.return_value = {"media_id": "draft-media-id"}
        client = WeChatClient(
            WeChatConfiguration(
                app_id="app-id",
                app_secret="app-secret",
                author="看电影的",
                thumb_media_id="thumb-id",
                source_url="https://example.com",
            ),
            http=http,
        )

        client.create_draft("<p>article</p>", "摘要", "2026 6月观影")

        payload = http.post.call_args.kwargs["data"]
        article = json.loads(payload.decode("utf-8"))["articles"][0]
        self.assertEqual(article["title"], "2026 6月观影")
        self.assertEqual(article["digest"], "摘要")
        self.assertEqual(article["author"], "看电影的")
        self.assertIn("2026 6月观影".encode("utf-8"), payload)

    @patch("services.wechat_client.requests.post")
    @patch("services.wechat_service.load_poster", return_value=b"poster-bytes")
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

        with patch(
            "services.wechat_service.WeChatConfiguration.load",
            return_value=TEST_CONFIG,
        ):
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


class WeChatClientTest(unittest.TestCase):
    def setUp(self):
        self.config = WeChatConfiguration(
            app_id="app-id",
            app_secret="app-secret",
            author="Draft Author",
            thumb_media_id="thumb-id",
            source_url="https://example.com/source",
        )
        self.http = Mock()
        self.client = WeChatClient(self.config, http=self.http)

    def test_get_access_token_returns_token_with_timeout(self):
        self.http.get.return_value.json.return_value = {
            "access_token": "access-token",
            "expires_in": 7200,
        }

        token = self.client.get_access_token()

        self.assertEqual(token, "access-token")
        self.http.get.assert_called_once_with(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": "app-id",
                "secret": "app-secret",
            },
            timeout=20,
        )

    def test_get_access_token_preserves_wechat_business_error(self):
        error = {"errcode": 40013, "errmsg": "invalid appid"}
        self.http.get.return_value.json.return_value = error

        with self.assertRaises(WeChatApiError) as raised:
            self.client.get_access_token()

        self.assertEqual(raised.exception.response, error)
        self.assertIn(str(error), str(raised.exception))

    def test_list_materials_queries_permanent_image_page(self):
        self.http.get.return_value.json.return_value = {
            "access_token": "access-token"
        }
        materials = {
            "total_count": 1,
            "item_count": 1,
            "item": [{"media_id": "cover-media-id"}],
        }
        self.http.post.return_value.json.return_value = materials

        result = self.client.list_materials()

        self.assertEqual(result, materials)
        self.http.post.assert_called_once_with(
            "https://api.weixin.qq.com/cgi-bin/material/batchget_material"
            "?access_token=access-token",
            json={"type": "image", "offset": 0, "count": 20},
            timeout=20,
        )

    def test_one_access_token_is_reused_for_image_and_draft_uploads(self):
        self.http.get.return_value.json.return_value = {
            "access_token": "access-token"
        }
        self.http.post.side_effect = [
            Mock(json=Mock(return_value={"url": "https://mmbiz.qpic.cn/poster"})),
            Mock(json=Mock(return_value={"media_id": "draft-media-id"})),
        ]

        image_url = self.client.upload_image("movie.png", b"poster")
        media_id = self.client.create_draft("<p>article</p>", "digest", "title")

        self.assertEqual(image_url, "https://mmbiz.qpic.cn/poster")
        self.assertEqual(media_id, "draft-media-id")
        self.http.get.assert_called_once()
        self.assertIn("access_token=access-token", self.http.post.call_args_list[0].args[0])
        self.assertIn("access_token=access-token", self.http.post.call_args_list[1].args[0])

    def test_create_draft_timeout_reports_unknown_result(self):
        import requests

        self.http.get.return_value.json.return_value = {
            "access_token": "access-token"
        }
        self.http.post.side_effect = requests.Timeout("timed out")

        with self.assertRaises(DraftCreationResultUnknown):
            self.client.create_draft("<p>article</p>", "digest", "title")

    def test_token_timeout_before_draft_request_is_a_definite_failure(self):
        import requests

        self.http.get.side_effect = requests.Timeout("token timed out")

        with self.assertRaises(requests.Timeout):
            self.client.create_draft("<p>article</p>", "digest", "title")

        self.http.post.assert_not_called()

    def test_create_draft_preserves_wechat_business_error(self):
        error = {"errcode": 40007, "errmsg": "invalid media_id"}
        self.http.get.return_value.json.return_value = {
            "access_token": "access-token"
        }
        self.http.post.return_value.json.return_value = error

        with self.assertRaises(WeChatApiError) as raised:
            self.client.create_draft("<p>article</p>", "digest", "title")

        self.assertEqual(raised.exception.response, error)
        self.assertIn(str(error), str(raised.exception))

    def test_get_draft_returns_existing_draft(self):
        self.http.get.return_value.json.return_value = {
            "access_token": "access-token"
        }
        draft = {"news_item": [{"title": "Draft title"}]}
        self.http.post.return_value.json.return_value = draft

        result = self.client.get_draft("draft-media-id")

        self.assertEqual(result, draft)
        self.http.post.assert_called_once_with(
            "https://api.weixin.qq.com/cgi-bin/draft/get"
            "?access_token=access-token",
            json={"media_id": "draft-media-id"},
            timeout=20,
        )

    def test_wechat_response_json_is_decoded_as_utf8(self):
        response = Mock()
        response.content = (
            '{"errcode":40001,"errmsg":"中文错误"}'.encode("utf-8")
        )

        result = WeChatClient._response_json(response)

        self.assertEqual(result["errmsg"], "中文错误")
        response.json.assert_not_called()

    def test_configuration_rejects_missing_required_values(self):
        with self.assertRaisesRegex(ValueError, "author, source_url"):
            WeChatConfiguration.from_mapping(
                {
                    "AppID": "app-id",
                    "AppSecret": "app-secret",
                    "thumb_media_id": "thumb-id",
                }
            )


class GoogleSheetsDraftExtractionCharacterizationTest(unittest.TestCase):
    @patch("utils.google_sheets.read_id", return_value="spreadsheet-id")
    @patch("utils.google_sheets.load_service_account_credentials")
    @patch("utils.google_sheets.build")
    def test_extract_returns_validated_movies_without_writing_backup(
        self,
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
                movies, title = extract("movie", DraftPeriod("2026", 3, 4))
            finally:
                os.chdir(original_cwd)

            backup_exists = Path(temp_dir, "configs", "backup_2026.json").exists()

        self.assertEqual(title, "2026 3-4月观影")
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["name"], "霸王别姬")
        self.assertEqual(movies[0]["subname"], "Farewell My Concubine")
        self.assertIsInstance(movies[0], DraftMovie)
        self.assertEqual(movies[0].sheet_row, 2)
        self.assertFalse(backup_exists)
        read_id.assert_called_with("movie")


if __name__ == "__main__":
    unittest.main()
