from django.core.management.base import BaseCommand

import decimal
import json
import ijson
import logging
import requests
import zipfile
from os import path
from ijson import ObjectBuilder

from data_import.importers import JsonImporter
from data_import import _paths, _query


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        if path.isfile(_paths.json_data_path) and False:
            overwrite = _query.query_yes_no(
                '{0} already exists, overwrite?'.format(_paths.json_zip_path))

            if overwrite:
                logging.info('Downloading json file from {0}'
                             .format(_paths.json_zip_download_url))
                stream = requests.get(_paths.json_zip_download_url)

                logging.info('Writing json data to file {0}'
                             .format(_paths.json_zip_path))
                with open(_paths.json_zip_path, 'wb') as output:
                    output.write(stream.content)

                json_zip_file = zipfile.ZipFile(_paths.json_zip_path)
                json_zip_file.extractall(_paths.data_folder)

        # importer = JsonImporter()
        # json_data = importer.parse_json()

        f = open(_paths.json_data_path, 'r', encoding="utf8")
        # json_data = json.load(f, encoding='UTF-8')
        #
        # sets = ijson.parse(f)
        #
        # for set in sets:
        #     print(set)

        def decimal_default(obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            raise TypeError

        for set_data in self.parse_sets(f):
            # print(set)
            # pass
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

        # for set_code, set_data in json_data.items():
        #     with open(path.join(_paths.set_folder, '_' + set_code + '.json'), 'w', encoding='utf8') as set_file:
        #         set_file.write(json.dumps(
        #             set_data,
        #             sort_keys=True,
        #             indent=2,
        #             separators=(',', ': ')))

    def parse_sets(self, f):
        prefixed_events = ijson.parse(f)
        prefixed_events = iter(prefixed_events)
        prefix = None  # '10E'
        # current_set = None

        while True:
            current, event, value = next(prefixed_events)
            # if not prefix:
            #    prefix = current  # current_set = current
            # print(f'current:{current} prefix:{prefix}')
            # if current == prefix or not prefix:
            if event in ('start_map', 'start_array'):
                builder = ObjectBuilder()
                end_event = event.replace('start', 'end')
                while (current, event) != (prefix, end_event):
                    # if prefix:
                    # print(f'current:{current}   prefix:{prefix}   event:{event}   value:{value}')
                    if current:
                        builder.event(event, value)
                    current, event, value = next(prefixed_events)
                    if not prefix:
                        prefix = current
                prefix = None
                yield builder.value
                # else:
                #     prefix = None
                #     yield value
