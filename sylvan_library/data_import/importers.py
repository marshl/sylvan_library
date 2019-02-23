"""
Module for data import shims
"""
import json
import os
from datetime import date

from data_import.staging import (
    StagedSet,
)
from data_import import _paths


class JsonImporter:
    """
    Class for the json data importer
    """

    def __init__(self):
        self.sets = list()

    def import_data(self):
        for set_file_path in [os.path.join(_paths.SET_FOLDER, s)
                              for s in os.listdir(_paths.SET_FOLDER)]:
            if not set_file_path.endswith('.json'):
                continue

            with open(set_file_path, 'r', encoding="utf8") as set_file:
                set_data = json.load(set_file, encoding='UTF-8')
                self.add_set(set_data['code'], set_data)

        self.sets.sort(key=lambda s: s.get_release_date() or str(date.max))

    def add_set(self, code, json_set):
        staged_set = StagedSet(code, json_set)
        self.sets.append(staged_set)

    def get_staged_sets(self):
        return self.sets
