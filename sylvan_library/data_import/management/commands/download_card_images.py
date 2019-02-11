"""
Module for the download_card_images command
"""
import os
import logging
import random
import queue
import threading
import time
import requests

from django.core.management.base import BaseCommand

from cards.models import CardPrinting, CardPrintingLanguage, Language, CardImage

logger = logging.getLogger('django')


class Command(BaseCommand):
    """
    The command for download card images from gatherer
    """
    help = 'Downloads card images from gatherer'

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

        if options['download_all_languages'] \
                and not Language.objects.filter(name='English').exists():
            logger.log(
                'Only english card images are downloaded by default, but the English Language '
                'object does not exist. Please run `update_database` first')
            return

        image_download_queue = queue.Queue()

        for i in range(1, self.download_thread_count):
            thread = ImageDownloadThread(image_download_queue)
            thread.setDaemon(True)
            thread.start()

        for printing in CardPrinting.objects.all():
            if not printing.scryfall_id:
                continue

            base_image_uri = None
            logger.info(f'Downloading images for {printing}')
            for printed_language in printing.printed_languages.all():
                if printed_language.language.code is None:
                    continue

                if CardImage.objects.filter(printed_language=printed_language).exists():
                    logger.info(f'\tSkipping {printed_language}')
                    continue

                image_path = os.path.join('website', 'static', printed_language.get_image_path())

                if os.path.exists(image_path):
                    logger.info(f'\tSkipping {printed_language}')
                    card_image = CardImage(printed_language=printed_language, downloaded=True)
                    card_image.save()

                    continue

                if base_image_uri is None:
                    url = 'https://api.scryfall.com/cards/' + printing.scryfall_id
                    resp = requests.get(url=url)
                    data = resp.json()
                    base_image_uri = data['image_uris']['normal']
                    # Sleep after every request made to reduce server load
                    time.sleep(random.random() * 0.25 + 0.1)

                localised_image_uri = base_image_uri.replace(
                    '/en/',
                    f'/{printed_language.language.code}/')
                image_download_queue.put((printed_language.id, localised_image_uri, image_path))

        image_download_queue.join()


class ImageDownloadThread(threading.Thread):
    """
    The thread object for downloading a card image
    """

    def __init__(self, download_queue):
        threading.Thread.__init__(self)
        self.download_queue = download_queue

    def run(self):
        while True:
            (printed_language_id, download_url, image_path) = self.download_queue.get()

            printed_language = CardPrintingLanguage.objects.get(id=printed_language_id)
            stream = requests.get(download_url)
            try:
                stream.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.warning(
                    f'\tCould not download {printed_language} ({download_url})')
                card_image = CardImage(printed_language=printed_language, downloaded=False)
                card_image.save()
            else:
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'wb') as output:
                    output.write(stream.content)

                card_image = CardImage(printed_language=printed_language, downloaded=True)
                card_image.save()
                logger.info(f'\tDownloaded {printed_language}')

            self.download_queue.task_done()
