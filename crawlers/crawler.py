import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import html

def keep_english(text: str) -> str:
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    has_english = bool(re.search(r'[A-Za-z]', text))

    if has_chinese and has_english:
        english_parts = re.findall(r'[A-Za-z]+(?:[ -][A-Za-z]+)*', text)
        return ' '.join(english_parts).strip()

    return text

def parse_url(text: str) -> str:
    movie_id_match = re.search(r"\b(\d+)\b", text.strip())
    if movie_id_match:
        return f"https://movie.douban.com/subject/{movie_id_match.group(1)}/"

    raise ValueError("Invalid movie id")
    
    

def movie_info_crawler(url):
    def create_driver():
        options = Options()
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

        prefs = {
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        return driver


    driver = create_driver()

    real_url = parse_url(url)

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

    # print(script_tag)
    
    raw_json = script_tag.get_text()
    # Douban's ld+json may contain literal newlines/control characters
    # inside strings, which are invalid in strict JSON parsing.
    raw_json = re.sub(r'[\x00-\x1f]+', ' ', raw_json)
    data = json.loads(raw_json)

    name = data.get("name")
    name = html.unescape(name) if name else None

    director = None
    directors = data.get("director")
    if isinstance(directors, list) and directors:
        director = directors[0].get("name")
    elif isinstance(directors, dict):
        director = directors.get("name")

    date_published = data.get("datePublished")
    year = date_published[:4] if date_published else None

    driver.quit()
    return {
        "name": name,
        "year": int(year),
        "director": keep_english(director)
    }

if __name__ == "__main__":
    start = time.time()
    url = "https://movie.douban.com/subject/1291992/"



    movie_info = {"sheetname": "2026",
                "date": "2026/3/19",
                "rating": 4.2,
                "comments": "test comment",
                "quality": "1080p"}
    movie_info.update(movie_info_crawler(url))
    print(movie_info)
    print(time.time() - start)
    # id = "movie/1291992&&&sdfjskdfjsdk1234"
    # print(parse_url(id))
