"""
Module for the fetch_data command
"""

import json
import logging
import sys
import zipfile
from typing import Any

import requests
from django.core.management.base import BaseCommand
from pathlib import Path

from data_import import _paths
from sylvan_library.data_import.management.commands import (
    pretty_print_json_file,
    download_file,
    print_progress,
)

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Command to download the json files from MTG JSON and extract them into the sets folder
    """

    help = "Downloads the MtG JSON data files"

    def remove_old_set_files(self) -> None:
        """
        Removes all .json files from the sets directory.
        """
        set_files = _paths.get_set_files()
        for idx, set_file in enumerate(set_files):
            set_file.unlink()
            print_progress((idx + 1) / len(set_files))
        sys.stdout.write("\n")

    def has_json_meta_changed(self) -> bool:
        """
        Checks if the MTGJSON meta version has changed since the last download.
        :return: True if a new version is available, False otherwise.
        """
        meta_response = requests.get(_paths.META_DOWNLOAD_URL)
        meta_response.raise_for_status()
        latest_meta = meta_response.json()
        latest_version = latest_meta["meta"]["version"]

        if not _paths.META_JSON_PATH.exists():
            logger.info("No local meta file found. A new version is available.")
            _paths.META_JSON_PATH.write_text(json.dumps(latest_meta, indent=2))
            return True

        local_version = json.loads(_paths.META_JSON_PATH.read_text())["meta"]["version"]

        logger.info(
            "Local meta version is '%s'. Latest version is %s",
            local_version,
            latest_version,
        )
        if latest_version > local_version:
            _paths.META_JSON_PATH.write_text(json.dumps(latest_meta, indent=2))
            return True

        return False

    def handle(self, *args: Any, **options: Any) -> None:
        if not self.has_json_meta_changed():
            logger.info("No update required.")
            return

        logger.info("Downloading set files from %s", _paths.JSON_ZIP_DOWNLOAD_URL)
        download_file(_paths.JSON_ZIP_DOWNLOAD_URL, _paths.JSON_ZIP_PATH)

        logger.info("Removing old set files")
        self.remove_old_set_files()

        logger.info("Extracting set files")
        with zipfile.ZipFile(_paths.JSON_ZIP_PATH) as json_zip_file:
            # Filter out directories and empty filenames
            valid_files = [
                member
                for member in json_zip_file.infolist()
                if not member.is_dir() and Path(member.filename).name
            ]

            for idx, member in enumerate(valid_files):
                # Construct the target path using pathlib
                target_path = _paths.SETS_DIR / Path(member.filename).name

                # Read from the zip and write pretty-printed JSON
                with json_zip_file.open(member) as source:
                    set_data = json.load(source)
                    target_path.write_text(json.dumps(set_data, indent=2))

                print_progress((idx + 1) / len(valid_files))
            sys.stdout.write("\n")

        logger.info("Downloading and extracting CardTypes")
        download_file(_paths.TYPES_DOWNLOAD_URL, _paths.TYPES_ZIP_PATH)
        with zipfile.ZipFile(_paths.TYPES_ZIP_PATH) as types_zip_file:
            types_zip_file.extractall(_paths.IMPORT_DIR)
        pretty_print_json_file(_paths.TYPES_JSON_PATH)

        logger.info("Done")
