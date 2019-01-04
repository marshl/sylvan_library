import json, ijson
from datetime import date

from data_import.staging import *
from data_import import _paths


class DataImporter:
    def __init__(self):
        self.staged_sets = list()

    def parse_json(self):
        f = open(_paths.json_data_path, 'r', encoding="utf8")
        json_data = json.load(f, encoding='UTF-8')
        f.close()
        return json_data

    def get_cards(self):
        f = open(_paths.json_data_path, 'r', encoding="utf8")
        json_data = ijson.items(f, 'item')
        for card_json in json_data:
            yield StagedCard(card_json)

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

    def import_sets(self):
        f = open(_paths.json_set_data_path, 'r', encoding="utf8")
        json_data = ijson.items(f, 'data.item')
        for json_set in json_data:
            self.add_set(json_set)

    def add_set(self, json_set):
        s = StagedSet(json_set)
        self.staged_sets.append(s)
