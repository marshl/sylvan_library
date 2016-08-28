import json
from . import _paths


def parse_json_data():
    f = open(_paths.json_data_path, 'r', encoding="utf8")
    json_data = json.load(f, encoding='UTF-8')
    f.close()
    return json_data
