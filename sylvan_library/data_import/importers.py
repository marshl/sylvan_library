import json
import os
from datetime import date

from data_import.staging import *
from data_import import _paths


class JsonImporter:
    def __init__(self):
        self.sets = list()

    def import_data(self):
        for set_file in [os.path.join(_paths.set_folder, s) for s in os.listdir(_paths.set_folder)]:
            if not set_file.endswith('.json'):
                continue

            with open(set_file, 'r', encoding="utf8") as f:
                set_data = json.load(f, encoding='UTF-8')
                self.add_set(set_data['code'], set_data)

        self.sets.sort(key=lambda s: s.get_release_date() or str(date.max))

    def add_set(self, code, json_set):
        s = StagedSet(code, json_set)
        self.sets.append(s)

    def get_staged_sets(self):
        return self.sets

    def import_colours(self):
        file = open(_paths.colour_json_path, 'r', encoding='utf8')
        colours = json.load(file, encoding='UTF-8')
        file.close()

        return colours

    def import_rarities(self):
        file = open(_paths.rarity_json_path, 'r', encoding="utf8")
        rarities = json.load(file, encoding='UTF-8')
        file.close()

        return rarities

    def import_languages(self):
        f = open(_paths.language_json_path, 'r', encoding="utf8")
        languages = json.load(f, encoding='UTF-8')
        f.close()

        return languages
