from django.core.management.base import BaseCommand

import os
import requests
import queue
import threading
import random
import time

from cards.models import CardPrintingLanguage, Language


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    download_thread_count = 8

    def add_arguments(self, parser):
        parser.add_argument(
            '--all-languages',
            action='store_true',
            dest='download_all_languages',
            default=False,
            help='Download all foreign languages (only English cards are downloaded by default)'
        )

        parser.add_argument(
            '--sleepy',
            action='store_true',
            dest='sleep_between_downloads',
            default=False,
            help='Sleep a random amount between each image to prevent overloading the image server'
        )

    def handle(self, *args, **options):

        if options['download_all_languages'] and not Language.objects.filter(name='English').exists():
            print('Only english card images are downloaded by default, but the English Language '
                  'object does not exist. Please run `update_database` first')
            return

        image_download_queue = queue.Queue()

        card_filter = CardPrintingLanguage.objects.filter(multiverse_id__isnull=False)
        if not options['download_all_languages']:
            card_filter = card_filter.filter(language=Language.objects.get(name='English'))

        for cpl in card_filter:
            image_download_queue.put(cpl)

        for i in range(1, self.download_thread_count):
            thread = ImageDownloadThread(image_download_queue, options['sleep_between_downloads'])
            thread.setDaemon(True)
            thread.start()

        image_download_queue.join()


class ImageDownloadThread(threading.Thread):
    def __init__(self, printlang_queue, random_sleep):
        threading.Thread.__init__(self)
        self.printlang_queue = printlang_queue
        self.has_random_sleep = random_sleep

    def run(self):
        while True:
            printing_language = self.printlang_queue.get()
            download_image_for_card(printing_language, self.has_random_sleep)
            self.printlang_queue.task_done()


def download_image_for_card(printing_language, random_sleep):
    image_path = printing_language.get_image_path()
    image_path = os.path.join('website', image_path)

    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    if os.path.exists(image_path):
        print(f'Already downloaded {printing_language} ({printing_language.multiverse_id})')
        return

    print(f'Downloading {printing_language} ({printing_language.multiverse_id})')

    image_download_url = 'http://gatherer.wizards.com' + \
                         '/Handlers/Image.ashx?multiverseid={0}&type=card'

    stream = requests.get(
        image_download_url.format(printing_language.multiverse_id))

    with open(image_path, 'wb') as output:
        output.write(stream.content)

    if random_sleep:
        time.sleep(random.random())
