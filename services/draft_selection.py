from dataclasses import dataclass, field
from datetime import date, datetime
import re
from typing import Any, Mapping, Optional, Sequence


REQUIRED_DRAFT_MOVIE_FIELDS = (
    "date",
    "name",
    "director",
    "year",
    "rating",
    "comment",
    "movie_id",
    "image_id",
)


def split_name(name: str) -> tuple[str, str]:
    parts = name.split()
    foreign_pattern = r"[a-zA-Z\u3040-\u30FF\uAC00-\uD7AF]"
    split_index = len(parts)
    for index, part in enumerate(parts):
        if re.search(foreign_pattern, part):
            split_index = index
            break
    return " ".join(parts[:split_index]), " ".join(parts[split_index:])


@dataclass(frozen=True)
class DraftPeriod:
    year: str
    month_start: int
    month_end: int

    def __post_init__(self):
        if not self.year.isdigit():
            raise ValueError("Draft Period year must be an integer.")
        if self.month_start not in range(1, 13) or self.month_end not in range(1, 13):
            raise ValueError("Draft Period months must be between 1 and 12.")
        if self.month_start > self.month_end:
            raise ValueError("Draft Period start month must not be after end month.")

    @classmethod
    def from_inputs(
        cls,
        year_input: str,
        month_input: str,
        today: Optional[date] = None,
    ) -> "DraftPeriod":
        today = today or date.today()
        year_text = year_input.strip()
        month_text = month_input.strip()

        try:
            year = str(int(year_text)) if year_text else str(today.year)
            months = [int(value) for value in month_text.split()] if month_text else []
        except ValueError as error:
            raise ValueError("Draft Period year and month must be integers.") from error

        if not months:
            months = [today.month]
        if len(months) not in (1, 2) or any(month not in range(1, 13) for month in months):
            raise ValueError(f"Invalid Draft Period months: {month_text or months}")

        month_start = months[0]
        month_end = months[-1]
        return cls(year=year, month_start=month_start, month_end=month_end)

    @property
    def title(self) -> str:
        if self.month_start == self.month_end:
            return f"{self.year} {self.month_start}月观影"
        return f"{self.year} {self.month_start}-{self.month_end}月观影"

    def includes(self, month: int) -> bool:
        return self.month_start <= month <= self.month_end


@dataclass
class DraftMovie:
    sheet_row: int
    date: str
    name: str
    director: str
    year: str
    rating: str
    comment: str
    movie_id: str
    image_id: str
    subname: str = ""
    quality: str = ""
    image_url: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: Mapping[str, Any], sheet_row: int) -> "DraftMovie":
        missing = [
            field_name
            for field_name in REQUIRED_DRAFT_MOVIE_FIELDS
            if field_name not in row
            or (field_name != "comment" and str(row[field_name]).strip() == "")
        ]
        if missing:
            raise ValueError(
                f"Sheet row {sheet_row} is missing required fields: {', '.join(missing)}"
            )

        name, subname = split_name(str(row["name"]))
        known = set(REQUIRED_DRAFT_MOVIE_FIELDS) | {"quality"}
        return cls(
            sheet_row=sheet_row,
            date=str(row["date"]),
            name=name,
            subname=subname,
            director=str(row["director"]),
            year=str(row["year"]),
            rating=str(row["rating"]),
            comment=str(row["comment"]),
            movie_id=str(row["movie_id"]),
            image_id=str(row["image_id"]),
            quality=str(row.get("quality", "")),
            extra={key: value for key, value in row.items() if key not in known},
        )

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)


def select_draft_movies(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    period: DraftPeriod,
) -> list[DraftMovie]:
    normalized_headers = [str(header).strip().lower() for header in headers]
    missing_headers = [
        field_name
        for field_name in REQUIRED_DRAFT_MOVIE_FIELDS
        if field_name not in normalized_headers
    ]
    if missing_headers:
        raise ValueError(
            "Google Sheet is missing required headers: " + ", ".join(missing_headers)
        )

    selected = []
    for sheet_row, row in enumerate(rows, start=2):
        row_values = dict(zip(normalized_headers, row))
        raw_date = str(row_values.get("date", ""))
        try:
            month = datetime.strptime(raw_date, "%m/%d").month
        except (TypeError, ValueError):
            raise ValueError(f"Sheet row {sheet_row} has malformed date: {raw_date}")

        if period.includes(month):
            selected.append(DraftMovie.from_row(row_values, sheet_row))

    if not selected:
        raise ValueError(
            f"No movies found for Draft Period {period.year} "
            f"{period.month_start}-{period.month_end}."
        )
    return selected
