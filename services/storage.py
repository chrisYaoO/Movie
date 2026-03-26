import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "configs", "data.json")

def load_data():
    if not os.path.exists(DATA_DIR):
        return {}
    with open(DATA_DIR, "r",encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_data(data):
    with open(DATA_DIR, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    data = load_data()
    print(data)

