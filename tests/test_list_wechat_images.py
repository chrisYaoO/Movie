import unittest

from list_wechat_images import filter_materials, iter_image_materials


class FakeMaterialClient:
    def __init__(self):
        self.calls = []
        self.pages = {
            0: {
                "total_count": 2,
                "item": [
                    {
                        "media_id": "media-1",
                        "name": "cover.jpg",
                        "url": "https://mmbiz.qpic.cn/cover-1",
                    }
                ],
            },
            1: {
                "total_count": 2,
                "item": [
                    {
                        "media_id": "media-2",
                        "name": "poster.jpg",
                        "url": "https://mmbiz.qpic.cn/cover-2",
                    }
                ],
            },
        }

    def list_materials(self, material_type, offset, count):
        self.calls.append((material_type, offset, count))
        return self.pages[offset]


class ListWechatImagesTest(unittest.TestCase):
    def test_iter_image_materials_reads_all_pages(self):
        client = FakeMaterialClient()

        result = list(iter_image_materials(client))

        self.assertEqual([item["media_id"] for item in result], ["media-1", "media-2"])
        self.assertEqual(client.calls, [("image", 0, 20), ("image", 1, 20)])

    def test_filter_materials_matches_html_escaped_url_text(self):
        materials = [
            {"media_id": "media-1", "url": "https://mmbiz.qpic.cn/a?x=1&y=2"},
            {"media_id": "media-2", "url": "https://mmbiz.qpic.cn/b"},
        ]

        result = filter_materials(materials, "x=1&amp;y=2")

        self.assertEqual([item["media_id"] for item in result], ["media-1"])


if __name__ == "__main__":
    unittest.main()
