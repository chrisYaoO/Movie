import tempfile
import unittest
from pathlib import Path

from services.draft_selection import DraftPeriod
from services.draft_workflow import DraftWorkflow, normalize_digest, render_preview


class FakeWeChatClient:
    def __init__(self, fail_upload_at=None):
        self.fail_upload_at = fail_upload_at
        self.uploads = []
        self.drafts = []

    def upload_image(self, filename, image):
        self.uploads.append((filename, image))
        if len(self.uploads) == self.fail_upload_at:
            raise RuntimeError("poster upload failed")
        return f"https://mmbiz.qpic.cn/{filename}"

    def create_draft(self, html, digest, title):
        self.drafts.append((html, digest, title))
        return "draft-media-id"


class DraftWorkflowTest(unittest.TestCase):
    headers = [
        "date",
        "name",
        "director",
        "year",
        "rating",
        "comment",
        "movie_id",
        "image_id",
    ]
    rows = [
        ["6/2", "Movie A", "Director A", "2020", "5", "A", "1", "11"],
        ["6/1", "Movie B", "Director B", "2021", "4", "B", "2", "22"],
    ]

    def test_complete_offline_draft_run_returns_structured_result(self):
        client = FakeWeChatClient()
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir, "movie_template.html")
            preview_path = Path(temp_dir, "outputs", "movie_wechat.html")
            template_source = (
                "{% for item in items %}{{ item.movie_id }}:"
                "{{ item.image_url }};{% endfor %}"
            )
            template_path.write_text(template_source, encoding="utf-8")

            workflow = DraftWorkflow(
                client=client,
                sheet_reader=lambda status, year: (self.headers, self.rows),
                poster_loader=lambda movie_id, image_id: f"{movie_id}:{image_id}".encode(),
                renderer=lambda movies, preview_path: render_preview(
                    movies,
                    template_path=template_path,
                    preview_path=preview_path,
                ),
                preview_path=preview_path,
            )

            result = workflow.run(DraftPeriod("2026", 6, 6), "")

            self.assertEqual(result.title, "2026 6月观影")
            self.assertEqual(result.movie_count, 2)
            self.assertEqual(result.preview_path, preview_path)
            self.assertEqual(result.media_id, "draft-media-id")
            self.assertEqual(
                preview_path.read_text(encoding="utf-8"),
                "1:https://mmbiz.qpic.cn/1.png;2:https://mmbiz.qpic.cn/2.png;",
            )
            self.assertEqual(template_path.read_text(encoding="utf-8"), template_source)

        self.assertEqual(client.drafts[0][1], " ")
        self.assertEqual(client.drafts[0][2], "2026 6月观影")

    def test_poster_upload_failure_stops_before_render_and_draft_creation(self):
        client = FakeWeChatClient(fail_upload_at=2)
        render_calls = []
        workflow = DraftWorkflow(
            client=client,
            sheet_reader=lambda status, year: (self.headers, self.rows),
            poster_loader=lambda movie_id, image_id: b"poster",
            renderer=lambda movies, preview_path: render_calls.append(movies),
        )

        with self.assertRaisesRegex(RuntimeError, "poster upload failed"):
            workflow.run(DraftPeriod("2026", 6, 6), "digest")

        self.assertEqual(len(client.uploads), 2)
        self.assertEqual(render_calls, [])
        self.assertEqual(client.drafts, [])

    def test_progress_reports_current_movie_and_major_stages(self):
        progress = []
        workflow = DraftWorkflow(
            client=FakeWeChatClient(),
            sheet_reader=lambda status, year: (self.headers, self.rows),
            poster_loader=lambda movie_id, image_id: b"poster",
            renderer=lambda movies, preview_path: "<p>preview</p>",
            progress=progress.append,
        )

        workflow.run(DraftPeriod("2026", 6, 6), "digest")

        self.assertEqual(progress[0], "Reading Google Sheets for 2026 6月观影...")
        self.assertIn("Selected 2 movies.", progress)
        self.assertIn("[1/2] Movie A: downloading poster...", progress)
        self.assertIn("[1/2] Movie A: uploading poster to WeChat...", progress)
        self.assertIn("[2/2] Movie B: poster uploaded.", progress)
        self.assertIn("Writing Preview to outputs\\movie_wechat.html...", progress)
        self.assertIn("Creating WeChat draft...", progress)
        self.assertEqual(progress[-1], "Draft created: draft-media-id")

    def test_named_digest_rule_preserves_nonempty_digest(self):
        self.assertEqual(normalize_digest("digest"), "digest")
        self.assertEqual(normalize_digest(""), " ")


if __name__ == "__main__":
    unittest.main()
