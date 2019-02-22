"""
Module for the fetch_data command
"""
import logging
import os
import zipfile

import requests

from django.core.management.base import BaseCommand

from data_import import _paths


class Command(BaseCommand):
    """
    Command to download the json files from MTG JSON and extract them into the sets folder
    """
    help = 'Downloads the MtG JSON data files'

    def handle(self, *args, **options):
        logging.info('Downloading json file from %s', _paths.JSON_ZIP_DOWNLOAD_URL)
        stream = requests.get(_paths.JSON_ZIP_DOWNLOAD_URL)

        logging.info('Writing json data to file %s', _paths.JSON_ZIP_PATH)
        with open(_paths.JSON_ZIP_PATH, 'wb') as output:
            output.write(stream.content)

        for set_file in [os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)]:
            if set_file.endswith('.json'):
                os.remove(set_file)

        json_zip_file = zipfile.ZipFile(_paths.JSON_ZIP_PATH)
        json_zip_file.extractall(_paths.SET_FOLDER)
