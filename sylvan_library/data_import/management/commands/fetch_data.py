"""
Module for the fetch_data command
"""
import json
import logging
import os
import zipfile
from typing import List, Any

import requests

from django.core.management.base import BaseCommand

from data_import import _paths


class Command(BaseCommand):
    """
    Command to download the json files from MTG JSON and extract them into the sets folder
    """

    help = "Downloads the MtG JSON data files"

    @staticmethod
    def get_json_files() -> List[str]:
        """
        Gets all json  files in the set data directory
        :return: The list of set file full paths
        """
        return [
            os.path.join(_paths.SET_FOLDER, s)
            for s in os.listdir(_paths.SET_FOLDER)
            if s.endswith(".json")
        ]

    def handle(self, *args: Any, **options: Any) -> None:
        logging.info("Downloading json file from %s", _paths.JSON_ZIP_DOWNLOAD_URL)
        stream = requests.get(_paths.JSON_ZIP_DOWNLOAD_URL)

        logging.info("Writing json data to file %s", _paths.JSON_ZIP_PATH)
        with open(_paths.JSON_ZIP_PATH, "wb") as output:
            output.write(stream.content)

        for set_file in self.get_json_files():
            if set_file.endswith(".json"):
                os.remove(set_file)

        json_zip_file = zipfile.ZipFile(_paths.JSON_ZIP_PATH)
        json_zip_file.extractall(_paths.SET_FOLDER)

        # Prettify the json files
        for set_file_path in self.get_json_files():
            with open(set_file_path, "r", encoding="utf8") as set_file:
                set_data = json.load(set_file, encoding="utf8")

            with open(set_file_path, "w", encoding="utf8") as set_file:
                json.dump(set_data, set_file, indent=2)
