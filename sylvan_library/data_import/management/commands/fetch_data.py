from django.core.management.base import BaseCommand

import json
import logging
import requests
import zipfile
from os import path

from data_import.importers import JsonImporter
from data_import import _paths, _query


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        if path.isfile(_paths.json_data_path):
            overwrite = _query.query_yes_no(
                '{0} already exists, overwrite?'.format(_paths.json_zip_path))

            if not overwrite:
                logging.info("The file {0} wasn't overwritten"
                             .format(_paths.json_zip_path))
                return

        logging.info('Downloading json file from {0}'
                     .format(_paths.json_zip_download_url))
        stream = requests.get(_paths.json_zip_download_url)

        logging.info('Writing json data to file {0}'
                     .format(_paths.json_zip_path))
        with open(_paths.json_zip_path, 'wb') as output:
            output.write(stream.content)

        json_zip_file = zipfile.ZipFile(_paths.json_zip_path)
        json_zip_file.extractall(_paths.data_folder)

        importer = JsonImporter()
        json_data = importer.parse_json()

        for set_code, set_data in json_data.items():
            with open(path.join(_paths.set_folder, '_' + set_code + '.json'), 'w', encoding='utf8') as set_file:
                set_file.write(json.dumps(
                    set_data,
                    sort_keys=True,
                    indent=2,
                    separators=(',', ': ')))
