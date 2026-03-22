import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
    driver.get(url)

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        )
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    script_tag = soup.find("script", type="application/ld+json")
    if not script_tag:
        return None

    data = json.loads(script_tag.get_text(strip=True))

    name = data.get("name")

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
        "year": year,
        "director": director
    }

start = time.time()
url = "https://movie.douban.com/subject/35010610/"
print(movie_info_crawler(url))
print(time.time() - start)
