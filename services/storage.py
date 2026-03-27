import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_FILE = os.path.join(BASE_DIR, "configs", "data.json")


def get_data_file():
    return os.getenv("DRAFT_DATA_FILE", DEFAULT_DATA_FILE)


def load_data():
    data_file = get_data_file()
    if not os.path.exists(data_file):
        return {}
    with open(data_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def save_data(data):
    data_file = get_data_file()
    data_dir = os.path.dirname(data_file)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)

    with open(data_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    data = load_data()
    print(data)
