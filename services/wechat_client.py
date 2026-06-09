import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

import requests


DEFAULT_CONFIG_PATH = Path("configs/ids.json")
DEFAULT_TIMEOUT_SECONDS = 20
API_BASE_URL = "https://api.weixin.qq.com/cgi-bin"


class WeChatApiError(RuntimeError):
    def __init__(self, response: Mapping[str, Any]):
        self.response = dict(response)
        super().__init__(str(self.response))


class DraftCreationResultUnknown(RuntimeError):
    pass


@dataclass(frozen=True)
class WeChatConfiguration:
    app_id: str
    app_secret: str
    author: str
    thumb_media_id: str
    source_url: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "WeChatConfiguration":
        fields = {
            "app_id": values.get("AppID"),
            "app_secret": values.get("AppSecret"),
            "author": values.get("author"),
            "thumb_media_id": values.get("thumb_media_id"),
            "source_url": values.get("source_url"),
        }
        missing = [name for name, value in fields.items() if not value]
        if missing:
            raise ValueError(
                "Missing required WeChat configuration: " + ", ".join(missing)
            )
        return cls(**fields)

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> "WeChatConfiguration":
        with path.open(encoding="utf-8") as file:
            return cls.from_mapping(json.load(file))


class WeChatClient:
    def __init__(
        self,
        config: WeChatConfiguration,
        http=requests,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        access_token: Optional[str] = None,
    ):
        self.config = config
        self.http = http
        self.timeout_seconds = timeout_seconds
        self._access_token = access_token

    def get_access_token(self) -> str:
        if self._access_token is not None:
            return self._access_token

        response = self.http.get(
            f"{API_BASE_URL}/token",
            params={
                "grant_type": "client_credential",
                "appid": self.config.app_id,
                "secret": self.config.app_secret,
            },
            timeout=self.timeout_seconds,
        )
        result = self._response_json(response)
        self._access_token = self._required_value(result, "access_token")
        return self._access_token

    def upload_image(self, filename: str, image: bytes) -> str:
        response = self.http.post(
            self._authenticated_url("media/uploadimg"),
            files={"media": (filename, image, "image/png")},
            timeout=self.timeout_seconds,
        )
        return self._required_value(self._response_json(response), "url")

    def create_draft(self, html_content: str, digest: str, title: str) -> str:
        body = {
            "articles": [
                {
                    "article_type": "news",
                    "title": title,
                    "author": self.config.author,
                    "digest": digest,
                    "content": html_content,
                    "content_source_url": self.config.source_url,
                    "thumb_media_id": self.config.thumb_media_id,
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                    "pic_crop_235_1": "",
                    "pic_crop_1_1": "",
                }
            ]
        }
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        url = self._authenticated_url("draft/add")
        try:
            response = self.http.post(
                url,
                data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as error:
            raise DraftCreationResultUnknown(
                "Draft creation timed out. Check WeChat before rerunning."
            ) from error
        return self._required_value(self._response_json(response), "media_id")

    def get_draft(self, media_id: str) -> Mapping[str, Any]:
        response = self.http.post(
            self._authenticated_url("draft/get"),
            json={"media_id": media_id},
            timeout=self.timeout_seconds,
        )
        result = self._response_json(response)
        if "news_item" not in result:
            raise WeChatApiError(result)
        return result

    def _authenticated_url(self, endpoint: str) -> str:
        return f"{API_BASE_URL}/{endpoint}?access_token={self.get_access_token()}"

    @staticmethod
    def _required_value(result: Mapping[str, Any], key: str) -> str:
        if key not in result:
            raise WeChatApiError(result)
        return result[key]

    @staticmethod
    def _response_json(response) -> Mapping[str, Any]:
        content = getattr(response, "content", None)
        if isinstance(content, bytes) and content:
            return json.loads(content.decode("utf-8"))
        return response.json()
