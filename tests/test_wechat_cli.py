import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from services.draft_selection import DraftPeriod
from services.wechat_client import DraftCreationResultUnknown, WeChatApiError
from wechat import main


class WeChatCliTest(unittest.TestCase):
    @patch("wechat.input", return_value="digest")
    @patch("wechat.prompt_draft_period", side_effect=ValueError("Invalid Draft Period"))
    def test_validation_error_is_displayed_without_starting_workflow(
        self,
        prompt_draft_period,
        input_mock,
    ):
        output = io.StringIO()
        with redirect_stdout(output):
            main()

        self.assertIn("Invalid Draft Period", output.getvalue())

    @patch("wechat.prompt_draft_period", return_value=DraftPeriod("2026", 6, 6))
    @patch("wechat.input", return_value="digest")
    @patch("wechat.run_draft")
    def test_business_error_response_is_displayed_directly(
        self,
        run_draft,
        input_mock,
        prompt_draft_period,
    ):
        error = {"errcode": 40007, "errmsg": "invalid media_id"}
        run_draft.side_effect = WeChatApiError(error)

        output = io.StringIO()
        with redirect_stdout(output):
            main()

        self.assertIn(str(error), output.getvalue())

    @patch("wechat.prompt_draft_period", return_value=DraftPeriod("2026", 6, 6))
    @patch("wechat.input", return_value="digest")
    @patch("wechat.run_draft")
    def test_unknown_result_reminds_user_to_check_wechat(
        self,
        run_draft,
        input_mock,
        prompt_draft_period,
    ):
        run_draft.side_effect = DraftCreationResultUnknown(
            "Draft creation timed out. Check WeChat before rerunning."
        )

        output = io.StringIO()
        with redirect_stdout(output):
            main()

        self.assertIn("Check WeChat before rerunning", output.getvalue())


if __name__ == "__main__":
    unittest.main()
