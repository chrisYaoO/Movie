from services.draft_workflow import render_preview
from services.poster_loader import load_poster
from services.wechat_client import WeChatClient, WeChatConfiguration


def build_html(movie_list):
    wechat_html = render_preview(movie_list)
    print("html saved")
    return wechat_html


def upload_to_draft(html_content, DIGEST, TITLE, client=None) -> str:

    if html_content is None:
        raise ValueError("no html content")

    client = client or _client_with_current_token()
    return client.create_draft(html_content, DIGEST, TITLE)


def get_access_token() -> str:
    return WeChatClient(WeChatConfiguration.load()).get_access_token()


def upload_images(movie_list, client=None):
    client = client or _client_with_current_token()

    for movie in movie_list:
        movie_id = movie["movie_id"]

        png_image = load_poster(movie_id, movie["image_id"])
        movie["image_url"] = client.upload_image(f"{movie_id}.png", png_image)
        print("Image uploaded for ", movie["name"])

    return movie_list


def _client_with_current_token():
    return WeChatClient(
        WeChatConfiguration.load(),
        access_token=get_access_token(),
    )

