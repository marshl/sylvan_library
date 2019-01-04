from django.core.management.base import BaseCommand

import logging
import urllib.request
from os import path

from data_import import _paths, _query


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        if path.isfile(_paths.json_data_path) or path.isfile(_paths.json_set_data_path):
            overwrite = _query.query_yes_no(
                f'Data files already exist, do you wish to overwrite them?')

            if not overwrite:
                logging.info(f'User cancelled')
                return

        # urllib.request.urlretrieve(_paths.json_download_url, _paths.json_data_path)

        self.download_file(_paths.json_set_download_url, _paths.json_set_data_path)
        self.download_file(_paths.json_download_url, _paths.json_data_path)

    def download_file(self, url, output_path):
        u = urllib.request.urlopen(url)
        f = open(output_path, 'wb')
        print(f'Downloading: {url} to {output_path}')

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            print("{:,} bytes".format(file_size_dl), end='\r')

        f.close()
