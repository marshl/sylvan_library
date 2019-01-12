from django.core.management.base import BaseCommand

import decimal
import json
import ijson
import logging
import requests
import zipfile
from os import path
import os
from ijson import ObjectBuilder

from data_import import _paths, _query


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        if path.isfile(_paths.json_data_path):
            overwrite = _query.query_yes_no(
                '{0} already exists, overwrite?'.format(_paths.json_zip_path))

            if not overwrite:
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

        for set_file in [os.path.join(_paths.set_folder, s) for s in os.listdir(_paths.set_folder)]:
            if set_file.endswith('.json'):
                os.remove(set_file)

        f = open(_paths.json_data_path, 'r', encoding="utf8")

        for set_data in self.parse_sets(f):
            filename = '_' + set_data['code'].upper() + '.json'
            print(f'Writing {filename}')
            file_path = path.join(_paths.set_folder, filename)
            with open(file_path, 'w', encoding='utf8') as set_file:
                set_file.write(json.dumps(
                    set_data,
                    sort_keys=True,
                    indent=2,
                    separators=(',', ': '),
                    default=decimal_default
                ))

        f.close()

    def parse_sets(self, f):
        prefixed_events = ijson.parse(f)
        prefixed_events = iter(prefixed_events)
        prefix = None

        while True:
            current, event, value = next(prefixed_events)
            if event in ('start_map', 'start_array'):
                builder = ObjectBuilder()
                end_event = event.replace('start', 'end')
                while (current, event) != (prefix, end_event):
                    if current:
                        builder.event(event, value)
                    current, event, value = next(prefixed_events)
                    if not prefix:
                        prefix = current
                prefix = None
                yield builder.value
