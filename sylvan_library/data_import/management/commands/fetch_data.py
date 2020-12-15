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


class Command(BaseCommand):
    """
    Command to download the json files from MTG JSON and extract them into the sets folder
    """

    help = "Downloads the MtG JSON data files"

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.logger = logging.getLogger("django")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

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

    def pretty_print_json_file(self, set_file_path: str) -> None:
        with open(set_file_path, "r", encoding="utf8") as set_file:
            set_data = json.load(set_file, encoding="utf8")

        with open(set_file_path, "w", encoding="utf8") as set_file:
            json.dump(set_data, set_file, indent=2)

    def download_file(self, url: str, destination_path: str):
        self.logger.info("Downloading %s", url)
        response = requests.get(url, stream=True)
        total_length = response.headers.get("content-length")
        self.logger.info(
            "Writing json data to file %s: %s bytes", _paths.JSON_ZIP_PATH, total_length
        )
        with open(destination_path, "wb") as output:
            if total_length is None:  # no content length header
                output.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    output.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ("=" * done, " " * (50 - done)))
                    sys.stdout.flush()

    def handle(self, *args: Any, **options: Any) -> None:
        self.logger.info("Downloading set files from %s", _paths.JSON_ZIP_DOWNLOAD_URL)
        # self.download_file(_paths.JSON_ZIP_DOWNLOAD_URL, _paths.JSON_ZIP_PATH)
        # self.logger.info("Extracting set files")
        # json_zip_file = zipfile.ZipFile(_paths.JSON_ZIP_PATH)
        # json_zip_file.extractall(_paths.SET_FOLDER)
        #
        # # Prettify the json files
        # for set_file_path in self.get_json_files():
        #     self.pretty_print_json_file(set_file_path)
        #
        # self.download_file(
        #     _paths.ATOMIC_CARDS_DOWNLOAD_URL, _paths.ATOMIC_CARDS_ZIP_PATH
        # )
        # cards_zip_file = zipfile.ZipFile(_paths.ATOMIC_CARDS_ZIP_PATH)
        # cards_zip_file.extractall(_paths.ATOMIC_CARDS_FOLDER)
        # self.pretty_print_json_file(_paths.ATOMIC_CARDS_PATH)

        # self.download_file(_paths.TYPES_DOWNLOAD_URL, _paths.TYPES_ZIP_PATH)
        types_zip_file = zipfile.ZipFile(_paths.TYPES_ZIP_PATH)
        types_zip_file.extractall(_paths.DOWNLOADS_FOLDER_PATH)
        self.pretty_print_json_file(_paths.TYPES_JSON_PATH)
