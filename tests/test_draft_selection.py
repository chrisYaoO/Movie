import unittest
from datetime import date

from services.draft_selection import DraftPeriod, select_draft_movies


class DraftMovieSelectionTest(unittest.TestCase):
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

    def test_blank_period_inputs_use_current_year_and_month(self):
        period = DraftPeriod.from_inputs("", "", today=date(2026, 6, 8))

        self.assertEqual(period, DraftPeriod("2026", 6, 6))

    def test_invalid_period_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be integers"):
            DraftPeriod.from_inputs("2026", "June")

    def test_reversed_period_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "start month"):
            DraftPeriod.from_inputs("2026", "7 6")

    def test_direct_period_construction_cannot_bypass_validation(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 12"):
            DraftPeriod("2026", 13, 13)

    def test_empty_period_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "No movies found"):
            select_draft_movies(
                self.headers,
                [["5/1", "A", "D", "2020", "5", "", "1", "2"]],
                DraftPeriod("2026", 6, 6),
            )

    def test_missing_headers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "image_id"):
            select_draft_movies(
                self.headers[:-1],
                [],
                DraftPeriod("2026", 6, 6),
            )

    def test_malformed_dates_include_sheet_row(self):
        with self.assertRaisesRegex(ValueError, "Sheet row 2.*malformed date"):
            select_draft_movies(
                self.headers,
                [["June", "A", "D", "2020", "5", "", "1", "2"]],
                DraftPeriod("2026", 6, 6),
            )

    def test_date_with_valid_month_but_invalid_day_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Sheet row 2.*malformed date"):
            select_draft_movies(
                self.headers,
                [["6/not-a-day", "A", "D", "2020", "5", "", "1", "2"]],
                DraftPeriod("2026", 6, 6),
            )

    def test_missing_director_defaults_to_space(self):
        movies = select_draft_movies(
            self.headers,
            [["6/1", "A", "", "2020", "5", "", "1", "2"]],
            DraftPeriod("2026", 6, 6),
        )

        self.assertEqual(movies[0].director, " ")

    def test_missing_director_header_defaults_to_space(self):
        movies = select_draft_movies(
            [header for header in self.headers if header != "director"],
            [["6/1", "A", "2020", "5", "", "1", "2"]],
            DraftPeriod("2026", 6, 6),
        )

        self.assertEqual(movies[0].director, " ")

    def test_comment_may_be_empty_and_quality_is_not_required(self):
        movies = select_draft_movies(
            self.headers,
            [["6/1", "A", "D", "2020", "5", "", "1", "2"]],
            DraftPeriod("2026", 6, 6),
        )

        self.assertEqual(movies[0].comment, "")
        self.assertEqual(movies[0].quality, "")

    def test_selected_movies_sort_by_date_after_filtering_period(self):
        movies = select_draft_movies(
            self.headers,
            [
                ["5/31", "Outside Period", "D", "2020", "5", "", "0", "0"],
                ["6/2", "Second Date", "D", "2020", "5", "", "1", "2"],
                ["6/1", "First Date", "D", "2020", "5", "", "3", "4"],
            ],
            DraftPeriod("2026", 6, 6),
        )

        self.assertEqual([movie.movie_id for movie in movies], ["3", "1"])
        self.assertEqual(
            [movie.subname for movie in movies],
            ["First Date", "Second Date"],
        )


if __name__ == "__main__":
    unittest.main()
