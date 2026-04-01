from jinja2 import Template
from premailer import transform
import requests
import json
from utils.google_sheets import *
from crawlers.crawler import *


def build_html(movie_list):

    with open("templates/movie_template.html", "r", encoding="utf-8") as file:
        template = Template(file.read())

    raw_html = template.render(items=movie_list)

    # wechat_html = transform(raw_html)
    wechat_html = raw_html

    with open("templates/movie_wechat.html", "w", encoding="utf-8") as file:
        file.write(wechat_html)

    print("html saved")

    return wechat_html


def upload_to_draft(html_content, DIGEST, TITLE) -> str:

    if html_content is None:
        raise ValueError("no html content")

    ACCESS_TOKEN = get_access_token()

    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={ACCESS_TOKEN}"

    body = {
        "articles": [
            {
                "article_type": "news",
                "title": TITLE,
                "author": "看电影的",
                "digest": DIGEST,
                "content": html_content,
                "content_source_url": "https://github.com/chrisYaoO/Movie",
                "thumb_media_id": "uVfIVj0d8J5QAnKYpWVpGA10J74D3J_5HrgCmS-tWY-H0B-jYaSbaN8hUMxSCb9q",
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
                "pic_crop_235_1": "",
                "pic_crop_1_1": "",
            }
        ]
    }
    json_body = json.dumps(body, ensure_ascii=False)

    try:

        response = requests.post(url, data=json_body)
        result = response.json()

        if "media_id" in result:
            return result["media_id"]
        else:
            raise RuntimeError(f"Failed to upload to draft: {result}")

    except Exception as e:
        raise Exception(f"request error: {e}")


def get_access_token() -> str:
    url = "https://api.weixin.qq.com/cgi-bin/token"

    with open("configs/ids.json", "r", encoding="utf-8") as file:
        config = json.load(file)
    AppID = config["AppID"]
    AppSecret = config["AppSecret"]

    # print(AppID)
    # print(AppSecret)

    body = {
        "grant_type": "client_credential",
        "appid": AppID,
        "secret": AppSecret,
    }
    try:
        response = requests.get(url, params=body)
        result = response.json()

        if "access_token" in result:
            return result["access_token"]
        else:
            raise RuntimeError(f"Failed to get access token: {result}")
    except Exception as e:
        raise Exception(f"request error: {e}")


def upload_images(movie_list):

    ACCESS_TOKEN = get_access_token()

    url = (
        f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={ACCESS_TOKEN}"
    )

    for movie in movie_list:
        movie_id = movie["movie_id"]

        png_image = image_crawler(movie_id, movie["image_id"])

        files = {"media": (f"{movie_id}.png", png_image, "image/png")}
        response = requests.post(url, files=files, timeout=20)

        result = response.json()

        if "url" in result:
            movie["image_url"] = result["url"]
            print("Image uploaded for ", movie["name"])
        else:
            raise RuntimeError("Failed to upload image:", result)

    return movie_list

def get_media():
    ACCESS_TOKEN = get_access_token()

    url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={ACCESS_TOKEN}"

    body = {
        "type": "image",
        "offset": 0,
        "count": 1,
    }

    response = requests.post(url, json=body)

    result = response.json()

    if "item_count" in result:
        return result["item"][0]["media_id"]
    else:
        raise RuntimeError(f"Failed to upload thumb media: {result}")


