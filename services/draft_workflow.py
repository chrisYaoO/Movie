from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from jinja2 import Template

from services.draft_selection import DraftMovie, DraftPeriod, select_draft_movies
from services.poster_loader import load_poster
from services.wechat_client import WeChatClient, WeChatConfiguration
from utils.google_sheets import read_draft_sheet


DEFAULT_TEMPLATE_PATH = Path("templates/movie_template.html")
DEFAULT_PREVIEW_PATH = Path("outputs/movie_wechat.html")


def ignore_progress(message: str) -> None:
    pass


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
        poster_loader: Callable = load_poster,
        renderer: Callable = render_preview,
        preview_path: Path = DEFAULT_PREVIEW_PATH,
        progress: Callable[[str], None] = ignore_progress,
    ):
        self.client = client
        self.sheet_reader = sheet_reader
        self.poster_loader = poster_loader
        self.renderer = renderer
        self.preview_path = preview_path
        self.progress = progress

    def run(
        self,
        period: DraftPeriod,
        digest: str,
        sheet_status: str = "movie",
    ) -> DraftRunResult:
        self.progress(f"Reading Google Sheets for {period.title}...")
        headers, rows = self.sheet_reader(sheet_status, period.year)
        movies = select_draft_movies(headers, rows, period)
        self.progress(f"Selected {len(movies)} movies.")

        for index, movie in enumerate(movies, start=1):
            display_name = " ".join(
                part for part in (movie.name, movie.subname) if part
            )
            prefix = f"[{index}/{len(movies)}] {display_name}"
            self.progress(f"{prefix}: downloading poster...")
            poster = self.poster_loader(movie.movie_id, movie.image_id)
            self.progress(f"{prefix}: uploading poster to WeChat...")
            movie.image_url = self.client.upload_image(f"{movie.movie_id}.png", poster)
            self.progress(f"{prefix}: poster uploaded.")

        self.progress(f"Writing Preview to {self.preview_path}...")
        html = self.renderer(movies, preview_path=self.preview_path)
        self.progress("Creating WeChat draft...")
        media_id = self.client.create_draft(html, normalize_digest(digest), period.title)
        self.progress(f"Draft created: {media_id}")
        return DraftRunResult(
            title=period.title,
            movie_count=len(movies),
            preview_path=self.preview_path,
            media_id=media_id,
        )


def run_draft(
    period: DraftPeriod,
    digest: str,
    progress: Callable[[str], None] = ignore_progress,
) -> DraftRunResult:
    client = WeChatClient(WeChatConfiguration.load())
    return DraftWorkflow(client, progress=progress).run(period, digest)
