from django.core.management.base import BaseCommand

import os
import requests
import queue
import threading

from spellbook.models import CardPrintingLanguage, Language


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        image_download_queue = queue.Queue()

        for cpl in CardPrintingLanguage.objects.filter(multiverse_id__isnull=False).filter(
                language=Language.objects.get(name='English')):
            image_download_queue.put(cpl)

        for i in range(1, 8):
            thread = imageDownloadThread(image_download_queue)
            thread.setDaemon(True)
            thread.start()

        image_download_queue.join()


class imageDownloadThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            printing_language = self.queue.get()
            download_image_for_card(printing_language)
            self.queue.task_done()


def download_image_for_card(printing_language):
    image_path = printing_language.get_image_path()
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    if os.path.exists(image_path):
        print('Skipping {0}'.format(printing_language.multiverse_id))
        return

    print('Downloading {0}'.format(printing_language.multiverse_id))

    image_download_url = 'http://gatherer.wizards.com' + \
                         '/Handlers/Image.ashx?multiverseid={0}&type=card'

    stream = requests.get(
        image_download_url.format(printing_language.multiverse_id))

    with open(image_path, 'wb') as output:
        output.write(stream.content)
