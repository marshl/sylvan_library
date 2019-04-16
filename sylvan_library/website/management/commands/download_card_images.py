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

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.image_download_queue = queue.Queue()
        self.root_dir = os.path.join('website', 'static')
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):
        parser.add_argument(
            '--all-languages',
            action='store_true',
            dest='download_all_languages',
            default=False,
            help='Download all foreign languages (only English cards are downloaded by default)'
        )

    def handle(self, *args, **options):

        if options['download_all_languages'] \
                and not Language.objects.filter(name='English').exists():
            logger.info(
                'Only english card images are downloaded by default, but the English Language '
                'object does not exist. Please run `update_database` first')
            return

        all_printings = CardPrinting.objects \
            .filter(printed_languages__image__isnull=True) \
            .filter(scryfall_id__isnull=False) \
            .prefetch_related('set') \
            .prefetch_related('printed_languages__language') \
            .prefetch_related('printed_languages__image') \
            .distinct()

        for i in range(0, self.download_thread_count):
            logger.info('Starting thread %s', i)
            thread = ImageDownloadThread(i, self.image_download_queue)
            thread.setDaemon(True)
            thread.start()

        for printing in all_printings:
            self.download_images_for_printing(printing, download_all_languages=options[
                'download_all_languages'])

        self.image_download_queue.join()

    def download_images_for_printing(self, printing: CardPrinting,
                                     download_all_languages: bool = False):
        """
        Starts download threads fto get the images for the given printing
        :param printing: THe printing to download the images for
        :param download_all_languages: Whether all languages should be downloaded, or just English
        """
        base_image_uri = None

        for printed_language in printing.printed_languages.all():
            if printed_language.language.code is None:
                continue

            if hasattr(printed_language, 'image'):
                logger.info('\tSkipping %s, already downloaded', printed_language)
                continue

            if not download_all_languages and printed_language.language != Language.english():
                logger.info('\tSkipping %s, not English', printed_language)
                continue

            if base_image_uri is None:
                url = 'https://api.scryfall.com/cards/' + printing.scryfall_id
                logger.info('Queueing images for %s (%s): %s', printing,
                            self.image_download_queue.qsize(), url)
                resp = requests.get(url=url)
                resp.raise_for_status()
                data = resp.json()
                if 'image_uris' in data:
                    base_image_uri = data['image_uris']['normal'] \
                        .replace('/' + data['lang'] + '/', '/[language]/')
                elif 'card_faces' in data:
                    base_image_uri = next(card_face['image_uris']['normal']
                                          .replace('/' + data['lang'] + '/', '/[language]/')
                                          for card_face in data['card_faces']
                                          if card_face['name'] == printing.card.name
                                          and 'image_uris' in card_face)
                else:
                    raise Exception('Neither card_images or card_faces could be found')

                # Sleep after every request made to reduce server load
                time.sleep(random.random() * 0.5)

            image_path = os.path.join(self.root_dir, printed_language.get_image_path())
            localised_image_uri = base_image_uri.replace(
                '/[language]/',
                f'/{printed_language.language.code}/')
            self.image_download_queue.put((printed_language.id, localised_image_uri, image_path))

            while self.image_download_queue.qsize() > self.download_thread_count * 2:
                time.sleep(1)


class ImageDownloadThread(threading.Thread):
    """
    The thread object for downloading a card image
    """

    def __init__(self, thread_number: int, download_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.thread_number = thread_number
        self.download_queue = download_queue

    def run(self):
        while True:
            (printed_language_id, download_url, image_path) = self.download_queue.get()

            printed_language = CardPrintingLanguage.objects.get(id=printed_language_id)
            stream = requests.get(download_url)
            try:
                stream.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.warning(
                    '\t%s: Could not download %s (%s): %s',
                    self.thread_number, printed_language, download_url, err.response.status_code)

                card_image = CardImage(printed_language=printed_language, downloaded=False)
                card_image.save()
            else:
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'wb') as output:
                    output.write(stream.content)

                card_image = CardImage(printed_language=printed_language, downloaded=True)
                card_image.save()
                logger.info('\t%s: Downloaded %s (%s)',
                            self.thread_number, printed_language, download_url)

            self.download_queue.task_done()
