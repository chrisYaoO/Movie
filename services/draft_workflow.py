from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from jinja2 import Template

from crawlers.crawler import image_crawler
from services.draft_selection import DraftMovie, DraftPeriod, select_draft_movies
from services.wechat_client import WeChatClient, WeChatConfiguration
from utils.google_sheets import read_draft_sheet


DEFAULT_TEMPLATE_PATH = Path("templates/movie_template.html")
DEFAULT_PREVIEW_PATH = Path("outputs/movie_wechat.html")


def normalize_digest(digest: str) -> str:
    return " " if digest == "" else digest


def render_preview(
    movies: Sequence[DraftMovie],
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    preview_path: Path = DEFAULT_PREVIEW_PATH,
) -> str:
    template_source = template_path.read_text(encoding="utf-8")
    html = Template(template_source).render(items=movies)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text(html, encoding="utf-8")
    return html


@dataclass(frozen=True)
class DraftRunResult:
    title: str
    movie_count: int
    preview_path: Path
    media_id: str


class DraftWorkflow:
    def __init__(
        self,
        client: WeChatClient,
        sheet_reader: Callable = read_draft_sheet,
        poster_loader: Callable = image_crawler,
        renderer: Callable = render_preview,
        preview_path: Path = DEFAULT_PREVIEW_PATH,
    ):
        self.client = client
        self.sheet_reader = sheet_reader
        self.poster_loader = poster_loader
        self.renderer = renderer
        self.preview_path = preview_path

    def run(
        self,
        period: DraftPeriod,
        digest: str,
        sheet_status: str = "movie",
    ) -> DraftRunResult:
        headers, rows = self.sheet_reader(sheet_status, period.year)
        movies = select_draft_movies(headers, rows, period)

        for movie in movies:
            poster = self.poster_loader(movie.movie_id, movie.image_id)
            movie.image_url = self.client.upload_image(f"{movie.movie_id}.png", poster)

        html = self.renderer(movies, preview_path=self.preview_path)
        media_id = self.client.create_draft(html, normalize_digest(digest), period.title)
        return DraftRunResult(
            title=period.title,
            movie_count=len(movies),
            preview_path=self.preview_path,
            media_id=media_id,
        )


def run_draft(period: DraftPeriod, digest: str) -> DraftRunResult:
    client = WeChatClient(WeChatConfiguration.load())
    return DraftWorkflow(client).run(period, digest)
