"""
Module for the download_card_images command
"""
import os
import logging
import random
import time
import requests

from django.core.management.base import BaseCommand

from cards.models import CardPrinting, CardPrintingLanguage, Language

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

        downloaded_paths = []

        for printing in CardPrinting.objects.all():
            if not printing.scryfall_id:
                continue

            image_uri = None

            logger.info(f'Downloading images for {printing}')

            for printed_language in printing.printed_languages.all():
                if printed_language.language.code is None:
                    continue

                image_path = os.path.join('website', 'static', printed_language.get_image_path())
                if image_path in downloaded_paths:
                    logger.warning(f'\tImage has already been downloaded: {image_path}')
                    continue

                downloaded_paths.append(image_path)
                if os.path.exists(image_path):
                    logger.info(f'\tSkipping {printed_language}')
                    continue

                logger.info(f'\t{printed_language}')

                if image_uri is None:
                    url = 'https://api.scryfall.com/cards/' + printing.scryfall_id
                    resp = requests.get(url=url)
                    data = resp.json()
                    image_uri = data['image_uris']['normal']

                localised_image_uri = image_uri.replace('/en/',
                                                        '/' + printed_language.language.code + '/')
                stream = requests.get(localised_image_uri)
                try:
                    stream.raise_for_status()
                except requests.exceptions.HTTPError:
                    logger.warning(
                        f'\tCould not download {printed_language} ({localised_image_uri})')
                else:
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    with open(image_path, 'wb') as output:
                        output.write(stream.content)
                finally:
                    time.sleep(random.random())
