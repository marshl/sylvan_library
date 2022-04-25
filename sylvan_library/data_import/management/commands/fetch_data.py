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
from data_import.management.commands import (
    pretty_print_json_file,
    download_file,
)

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

    def has_json_meta_changed(self) -> bool:
        meta_response = requests.get(_paths.META_DOWNLOAD_URL)
        meta_response.raise_for_status()
        latest_version = meta_response.json()["meta"]["version"]

        if not os.path.exists(_paths.META_JSON_PATH):
            logger.info("No local meta file found for version check.")
            with open(_paths.META_JSON_PATH, "wb") as output:
                output.write(meta_response.content)
            return True

        with open(_paths.META_JSON_PATH, "r") as meta_file:
            meta_json = json.load(meta_file)
            local_version = meta_json["meta"]["version"]

        logger.info(
            "Local meta version is '%s'. Latest version is %s",
            local_version,
            latest_version,
        )
        if latest_version > local_version:
            with open(_paths.META_JSON_PATH, "wb") as output:
                output.write(meta_response.content)
            return True
        return False

    def handle(self, *args: Any, **options: Any) -> None:
        if not self.has_json_meta_changed():
            logger.info("No update required.")
            return

        logger.info("Downloading set files from %s", _paths.JSON_ZIP_DOWNLOAD_URL)
        download_file(_paths.JSON_ZIP_DOWNLOAD_URL, _paths.JSON_ZIP_PATH)
        logger.info("Extracting set files")
        with zipfile.ZipFile(_paths.JSON_ZIP_PATH) as json_zip_file:
            json_zip_file.extractall(_paths.SET_FOLDER)

        # Prettify the json files
        for set_file_path in self.get_json_files():
            pretty_print_json_file(set_file_path)

        download_file(_paths.TYPES_DOWNLOAD_URL, _paths.TYPES_ZIP_PATH)
        types_zip_file = zipfile.ZipFile(_paths.TYPES_ZIP_PATH)
        types_zip_file.extractall(_paths.IMPORT_FOLDER_PATH)
        pretty_print_json_file(_paths.TYPES_JSON_PATH)
