from django.core.management.base import BaseCommand
from data_import import _paths

import json
import ijson
import subprocess
from subprocess import check_output

class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def add_arguments(self, parser):
        parser.add_argument('card_name', nargs='+')

    def handle(self, *args, **options):

        found_cards = []

        x = ''
        for card_name in options['card_name']:
            # f = open(_paths.json_data_path, 'r', encoding="utf8")
            out = check_output(["grep", card_name, _paths.json_data_path], shell=True)
            print(type(out))
            a = out.decode('utf-8').strip().split('\n')
            found_cards += a
            for b in a:
                print(b)
            #return
            #x += str(out.strip())
            #print(out)

            # json_data = ijson.items(f, 'item')
            # for card_json in json_data:
            #     if card_name.lower() in card_json['name'].lower():
            #         found_cards.append(card_json)

        #for x in found_cards:
        #    print(x)

        #x = '[' + x.strip(',') + ']'
        x = '[' + ''.join(found_cards).strip(',') + ']'
        print(x)
        pretty_file = open(_paths.find_results_path, 'w', encoding='utf8')
        d = json.loads(x)
        j = json.dumps(
            d,
            # found_cards,
            sort_keys=True,
            indent=2,
            separators=(',', ': '))
        print(j)
        pretty_file.write(j)
        pretty_file.close()

        return
        lines = []

        for card_name in options['card_name']:
            with open(_paths.json_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if card_name in line:
                        lines.append(line)

        print(''.join(lines))
        pretty_file = open(_paths.find_results_path, 'w', encoding='utf8')
        pretty_file.write(json.dumps(
            '[' + (''.join(lines)) + ']',
            sort_keys=True,
            indent=2,
            separators=(',', ': ')))

        pretty_file.close()
