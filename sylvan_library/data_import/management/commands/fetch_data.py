"""
Module for the fetch_data command
"""
import decimal
import json
import logging
import os
import zipfile

import ijson
import requests

from django.core.management.base import BaseCommand

from data_import import _paths, _query


def decimal_default(obj):
    """
    Converts an object from decimal to float
    This prevents json parsing errors
    :param obj: The object to parse
    :return: The float value of the object
    """
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Command(BaseCommand):
    """
    The command to download the json from mtgjson and then split it into multiple files

    TODO: This could be improved by just downloaded every separate json
    file from https://mtgjson.com/json/
    """
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        if os.path.isfile(_paths.JSON_DATA_PATH):
            overwrite = _query.query_yes_no(
                '{0} already exists, overwrite?'.format(_paths.JSON_ZIP_PATH))

            if not overwrite:
                return

        logging.info('Downloading json file from {0}'
                     .format(_paths.JSON_ZIP_DOWNLOAD_URL))
        stream = requests.get(_paths.JSON_ZIP_DOWNLOAD_URL)

        logging.info('Writing json data to file {0}'
                     .format(_paths.JSON_ZIP_PATH))
        with open(_paths.JSON_ZIP_PATH, 'wb') as output:
            output.write(stream.content)

        json_zip_file = zipfile.ZipFile(_paths.JSON_ZIP_PATH)
        json_zip_file.extractall(_paths.DATA_FOLDER)

        for set_file in [os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)]:
            if set_file.endswith('.json'):
                os.remove(set_file)

        file = open(_paths.JSON_DATA_PATH, 'r', encoding="utf8")

        for set_data in self.parse_sets(file):
            filename = '_' + set_data['code'].upper() + '.json'
            print(f'Writing {filename}')
            file_path = os.path.join(_paths.SET_FOLDER, filename)
            with open(file_path, 'w', encoding='utf8') as set_file:
                set_file.write(json.dumps(
                    set_data,
                    sort_keys=True,
                    indent=2,
                    separators=(',', ': '),
                    default=decimal_default
                ))

        file.close()

    def parse_sets(self, file):
        """
        Parses a file and returns each set individually
        :param file: The file
        :return: Each set in the file
        """
        prefixed_events = ijson.parse(file)
        prefixed_events = iter(prefixed_events)
        prefix = None

        while True:
            # pylint: disable=stop-iteration-return
            current, event, value = next(prefixed_events)
            if event in ('start_map', 'start_array'):
                builder = ijson.ObjectBuilder()
                end_event = event.replace('start', 'end')
                while (current, event) != (prefix, end_event):
                    if current:
                        builder.event(event, value)
                    # pylint: disable=stop-iteration-return
                    current, event, value = next(prefixed_events)
                    if not prefix:
                        prefix = current
                prefix = None
                yield builder.value
