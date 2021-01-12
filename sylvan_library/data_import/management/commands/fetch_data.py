"""
Module for the fetch_data command
"""
import json
import logging
import os
import sys
import zipfile
from typing import List, Any

import requests

from django.core.management.base import BaseCommand

from data_import import _paths
from management.commands import download_file, pretty_print_json_file

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Command to download the json files from MTG JSON and extract them into the sets folder
    """

    help = "Downloads the MtG JSON data files"

    def get_json_files(self) -> List[str]:
        """
        Gets all json  files in the set data directory
        :return: The list of set file full paths
        """
        return [
            os.path.join(_paths.SET_FOLDER, s)
            for s in os.listdir(_paths.SET_FOLDER)
            if s.endswith(".json")
        ]

    def remove_old_set_files(self) -> None:
        for set_file in self.get_json_files():
            if set_file.endswith(".json"):
                os.remove(set_file)

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Downloading set files from %s", _paths.JSON_ZIP_DOWNLOAD_URL)
        download_file(_paths.JSON_ZIP_DOWNLOAD_URL, _paths.JSON_ZIP_PATH)
        logger.info("Extracting set files")
        json_zip_file = zipfile.ZipFile(_paths.JSON_ZIP_PATH)
        json_zip_file.extractall(_paths.SET_FOLDER)

        # Prettify the json files
        for set_file_path in self.get_json_files():
            pretty_print_json_file(set_file_path)

        download_file(_paths.TYPES_DOWNLOAD_URL, _paths.TYPES_ZIP_PATH)
        types_zip_file = zipfile.ZipFile(_paths.TYPES_ZIP_PATH)
        types_zip_file.extractall(_paths.IMPORT_FOLDER_PATH)
        pretty_print_json_file(_paths.TYPES_JSON_PATH)
