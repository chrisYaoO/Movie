import html
import json
import os
import re
import time
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_driver():
    options = Options()
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin

    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = "eager"
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if chromedriver_path:
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    return driver


def keep_english(text: str) -> str:
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
    has_english = bool(re.search(r"[A-Za-z]", text))

    if has_chinese and has_english:
        english_parts = re.findall(r"[A-Za-z]+(?:[ -][A-Za-z]+)*", text)
        return " ".join(english_parts).strip()

    return text


def parse_movie_url(text: str) -> str:
    movie_id_match = re.search(r"\b(\d+)\b", text.strip())
    if movie_id_match:
        return f"{movie_id_match.group(1)}"

    raise ValueError("Invalid movie id")


def movie_info_crawler(url):
    driver = create_driver()
    try:
        real_url = "https://movie.douban.com/subject/"+parse_movie_url(url)

        driver.get(real_url)

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            )
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        script_tag = soup.find("script", type="application/ld+json")
        if not script_tag:
            return None

        raw_json = script_tag.get_text()
        # Douban's ld+json may contain literal newlines/control characters
        # inside strings, which are invalid in strict JSON parsing.
        raw_json = re.sub(r"[\x00-\x1f]+", " ", raw_json)
        data = json.loads(raw_json)

        name = data.get("name")
        name = html.unescape(name) if name else None

        image_link = data.get("image")
        image_id = parse_image_url(image_link) if image_link else None

        director = None
        directors = data.get("director")
        if isinstance(directors, list) and directors:
            director = directors[0].get("name")
        elif isinstance(directors, dict):
            director = directors.get("name")

        date_published = data.get("datePublished")
        year = date_published[:4] if date_published else None

        return {
            "name": name,
            "year": int(year),
            "director": keep_english(director),
            "image": image_id,
        }
    finally:
        driver.quit()


def parse_image_url(text: str) -> str:
    match = re.search(r"p(\d+)", text)
    if match:
        image_id = match.group(1)
        return str(image_id)

    raise ValueError("Invalid image id")


def webp_to_png(content, target_size_mb=1.0):
    target_size_bytes = target_size_mb * 1024 * 1024

    img = Image.open(BytesIO(content))

    # convert to RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    quality = 100
    step = 5
    min_quality = 50

    while quality >= min_quality:
        temp_buffer = BytesIO()
        img.save(temp_buffer, format="JPEG", quality=quality, optimize=True)

        current_size = temp_buffer.tell()

        if current_size <= target_size_bytes:
            return temp_buffer.getvalue()

        quality -= step

    raise ValueError("reached min quality, still too big")


def image_crawler(movie_id, image_id):
    # save_path = f"images/{movie_id}.jpeg"

    # if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
    #     return

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://movie.douban.com/",
    }

    try:
        response = None
        last_error = None
        candidate_urls = [
            f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.webp",
            f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.jpg",
            f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.jpeg",
            f"https://img2.doubanio.com/view/photo/l/public/p{image_id}.png",
        ]

        for img_url in candidate_urls:
            try:
                candidate_response = requests.get(
                    img_url,
                    headers=headers,
                    timeout=20,
                    allow_redirects=True,
                )
                candidate_response.raise_for_status()

                content_type = candidate_response.headers.get(
                    "Content-Type", ""
                ).lower()
                if content_type.startswith("image/"):
                    response = candidate_response
                    break

                last_error = ValueError(
                    f"unexpected content type for {img_url}: "
                    f"{content_type or 'unknown'}"
                )
            except requests.exceptions.RequestException as e:
                last_error = e

        if response is None:
            raise last_error or ValueError("failed to fetch a valid image")

        png_image = webp_to_png(response.content, target_size_mb=1.0)

        # with open(save_path, "wb") as f:
        #     f.write(jpeg_image)
        return png_image

    except requests.exceptions.HTTPError as e:
        raise Exception(f"failed to request: {e}")
    except Exception as e:
        raise Exception(f"failed to crawl image{movie_id}: {e}")


if __name__ == "__main__":
    # start = time.time()
    # url = "https://movie.douban.com/subject/1291992/"

    # movie_info = {
    #     "sheetname": "2026",
    #     "date": "2026/3/19",
    #     "rating": 4.2,
    #     "comments": "test comment",
    #     "quality": "1080p",
    # }
    # movie_info.update(movie_info_crawler(url))
    # print(movie_info)
    # print(time.time() - start)
    # id = "movie/1291992&&&sdfjskdfjsdk1234"
    # print(parse_url(id))

    start = time.time()
    url = "1291992"
    movie_info = movie_info_crawler(url)
    image_crawler(movie_id=url, image_id=movie_info["image"])
    print(time.time() - start)