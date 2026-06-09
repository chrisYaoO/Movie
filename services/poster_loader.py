from io import BytesIO

import requests
from PIL import Image


def compress_poster(content: bytes, target_size_mb: float = 1.0) -> bytes:
    target_size_bytes = target_size_mb * 1024 * 1024
    image = Image.open(BytesIO(content))
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    for quality in range(100, 49, -5):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        if buffer.tell() <= target_size_bytes:
            return buffer.getvalue()
    raise ValueError("Poster is still too large at minimum quality.")


def load_poster(movie_id: str, image_id: str) -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://movie.douban.com/",
    }
    candidate_urls = [
        f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.webp",
        f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.jpg",
        f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.jpeg",
        f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.png",
    ]
    last_error = None

    for image_url in candidate_urls:
        try:
            response = requests.get(
                image_url,
                headers=headers,
                timeout=20,
                allow_redirects=True,
            )
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if content_type.startswith("image/"):
                return compress_poster(response.content)
            last_error = ValueError(
                f"Unexpected content type for {image_url}: "
                f"{content_type or 'unknown'}"
            )
        except requests.exceptions.RequestException as error:
            last_error = error

    raise RuntimeError(f"Failed to load poster for movie {movie_id}: {last_error}")
