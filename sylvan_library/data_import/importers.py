"""
Module for data import shims
"""
import json
import logging
import os
from datetime import date
from typing import List

from data_import.staging import StagedSet
from data_import import _paths

logger = logging.getLogger("django")


class JsonImporter:
    """
    Class for the json data importer
    """

    def __init__(self):
        self.sets = list()

    def import_data(self):
        """
        Imports data from the list of set files
        """
        for set_file_path in [
            os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)
        ]:
            if not set_file_path.endswith(".json"):
                continue

            with open(set_file_path, "r", encoding="utf8") as set_file:
                set_data = json.load(set_file, encoding="UTF-8")
                self.add_set(set_data["code"], set_data)

        self.sets.sort(key=lambda s: s.get_release_date() or str(date.max))

        if not self.sets:
            logger.warning("No set files were found, you may need to run fetch_data")

    def add_set(self, code: str, json_set: dict):
        """
        Adds a set to this importer
        :param code: The set's code
        :param json_set: The dict of set data
        """
        staged_set = StagedSet(code, json_set)
        self.sets.append(staged_set)

    def get_staged_sets(self) -> List[StagedSet]:
        """
        Gets the staged sets of this
        :return:
        """
        return self.sets
