import argparse
import html
import json
from typing import Iterable, Mapping, Optional, Sequence

import requests

from services.wechat_client import (
    WeChatApiError,
    WeChatClient,
    WeChatConfiguration,
)


PAGE_SIZE = 20


def iter_image_materials(client: WeChatClient) -> Iterable[Mapping]:
    offset = 0
    while True:
        page = client.list_materials("image", offset=offset, count=PAGE_SIZE)
        items = page.get("item", [])
        yield from items
        offset += len(items)
        if not items or offset >= page["total_count"]:
            return


def filter_materials(
    materials: Iterable[Mapping],
    query: Optional[str],
) -> list[Mapping]:
    materials = list(materials)
    if not query:
        return materials

    query = html.unescape(query).lower()
    return [
        item
        for item in materials
        if query in json.dumps(item, ensure_ascii=False).lower()
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="List permanent WeChat image materials and their media_id."
    )
    parser.add_argument(
        "--match",
        help="Only show materials containing this text in their name, URL, or media_id.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print matching materials as JSON.",
    )
    args = parser.parse_args(argv)

    try:
        client = WeChatClient(WeChatConfiguration.load())
        materials = filter_materials(iter_image_materials(client), args.match)
    except (FileNotFoundError, ValueError, WeChatApiError, requests.RequestException) as error:
        parser.exit(1, f"Error: {error}\n")

    if args.as_json:
        print(json.dumps(materials, ensure_ascii=False, indent=2))
        return 0

    if not materials:
        print("No matching image materials found.")
        return 0

    print(f"Found {len(materials)} image materials.")
    for item in materials:
        print(f"media_id: {item.get('media_id', '')}")
        print(f"name: {item.get('name', '')}")
        print(f"url: {item.get('url', '')}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
