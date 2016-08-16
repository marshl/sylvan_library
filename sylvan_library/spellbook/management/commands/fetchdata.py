from django.core.management.base import BaseCommand, CommandError
import zipfile
import requests
import json
from os import path
from . import _paths

def parse_json_data():
    f = open(_paths.json_data_path, 'r', encoding="utf8")
    json_data = json.load(f, encoding='UTF-8')
    f.close()
    return json_data

class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'
    
    def handle(self, *args, **options):
        
        stream = requests.get(_paths.json_zip_download_url)
        
        print('Downloading to ', path.abspath(_paths.json_zip_path))
        if path.isfile(_paths.json_data_path):
            print('Zip file already exists, overwriting')
        
        with open(_paths.json_zip_path, 'wb') as output:
            output.write(stream.content)
        
        json_zip_file = zipfile.ZipFile(_paths.json_zip_path)
        json_zip_file.extractall(_paths.output_data_folder)
        
        json_data = parse_json_data()
        pretty_file = open(_paths.pretty_json_path, 'w', encoding='utf8')
        pretty_file.write(json.dumps(json_data,
                           sort_keys=True,
                           indent=2,
                           separators=(',', ': ')))
        
        pretty_file.close()
