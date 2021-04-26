"""
Module for the download_card_images command
"""
import logging
import os
import queue
import time
from typing import Optional, List
from urllib.parse import urlparse

import requests
from django.core.management.base import BaseCommand, OutputWrapper
from django.db import transaction
from requests import HTTPError

from cards.models import Language, CardImage, Set, CardFaceLocalisation

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for download card images from gatherer
    """

    help = "Downloads card images from gatherer"

    download_thread_count = 8

    def __init__(
        self,
        stdout: Optional[OutputWrapper] = None,
        stderr: Optional[OutputWrapper] = None,
        no_color: bool = False,
    ) -> None:
        self.image_download_queue = queue.Queue()
        self.root_dir = os.path.join("website", "static")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-languages",
            action="store_true",
            dest="download_all_languages",
            default=False,
            help="Download all foreign languages (only English cards are downloaded by default)",
        )
        parser.add_argument(
            "--set",
            dest="set_codes",
            nargs="*",
            help="Get images for only the given list of sets",
        )

    def handle(self, *args, **options):

        # if (
        #     options["download_all_languages"]
        #     and not Language.objects.filter(name="English").exists()
        # ):
        #     logger.info(
        #         "Only english card images are downloaded by default, but the English Language "
        #         "object does not exist. Please run `update_database` first"
        #     )
        #     return

        set_codes = options.get("set_codes")
        sets = Set.objects.all()
        if set_codes:
            sets = sets.filter(code__in=set_codes)

        english = Language.objects.get(code="en")
        for card_set in sets.order_by("release_date").all():
            self.get_images_for_set(card_set, [english])

        self.download_images()

    def download_images(self):
        for card_image in CardImage.objects.filter(file_path__isnull=True):
            try:
                stream = requests.get(card_image.scryfall_image_url)
                stream.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.exception(
                    "\t%s: Could not download %s (%s): %s",
                    card_image.scryfall_image_url,
                )
                raise
            url_path = urlparse(card_image.scryfall_image_url).path
            url_parts = url_path.split("/")
            if "normal" not in url_parts:
                raise ValueError(f"Invalid image URL {card_image.scryfall_image_url}")

            url_parts = url_parts[url_parts.index("normal") :]

            image_path = os.path.join("card_images", *url_parts)
            download_path = os.path.join(self.root_dir, image_path)
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            logger.info(
                "Downloading %s to %s", card_image.scryfall_image_url, download_path
            )
            with open(download_path, "wb") as output:
                output.write(stream.content)
                card_image.file_path = image_path
                card_image.save()

    def get_images_for_set(self, card_set: Set, languages: List[Language]):
        logger.info("Parsing set %s", card_set)
        faces_missing_images = (
            CardFaceLocalisation.objects.filter(
                localisation__card_printing__set=card_set
            )
            .filter(localisation__language__in=languages)
            .filter(image__isnull=True)
        )

        if not faces_missing_images.exists():
            logger.info("No missing images in %s", card_set)
            return

        # if card_set.type == "token" and card_set.parent_set:
        #     card_data = get_scryfall_cards("t" + card_set.parent_set.code.lower())
        # else:
        try:
            card_data = get_scryfall_cards(card_set.code)
        except HTTPError:
            logger.warning("Could not get cards for %s", card_set)
            time.sleep(5)
            return

        for scryfall_card in card_data:
            scryfall_id = scryfall_card["id"]
            matching_faces = faces_missing_images.filter(
                card_printing_face__card_printing__scryfall_id=scryfall_id
            )
            if not matching_faces.exists():
                continue

            if "image_uris" in scryfall_card:
                image_url = scryfall_card["image_uris"]["normal"]
                logger.info(
                    "Setting %s to have image %s",
                    " & ".join(str(m) for m in matching_faces.all()),
                    image_url,
                )
                with transaction.atomic():
                    new_image = CardImage.objects.create(scryfall_image_url=image_url)
                    matching_faces.update(image=new_image)

            elif "card_faces" in scryfall_card:
                for scryfall_face in scryfall_card["card_faces"]:
                    matching_face = matching_faces.filter(
                        card_printing_face__scryfall_illustration_id=scryfall_face[
                            "illustration_id"
                        ]
                    ).filter(image__isnull=True)
                    if not matching_face.exists():
                        continue
                    image_url = scryfall_face["image_uris"]["normal"]
                    assert matching_face.all()
                    logger.info(
                        "Setting %s to have image %s",
                        " & ".join(str(m) for m in matching_face.all()),
                        image_url,
                    )

                    with transaction.atomic():
                        new_image = CardImage.objects.create(
                            scryfall_image_url=image_url
                        )
                        matching_face.update(image=new_image)
            else:
                raise Exception("???")
        # raise Exception()

        time.sleep(5)

        return


def get_scryfall_set(set_code: str) -> dict:
    response = requests.get(f"https://api.scryfall.com/sets/{set_code}")
    response.raise_for_status()
    return response.json()


def get_scryfall_cards(set_code: str) -> list:
    set_info = get_scryfall_set(set_code)
    search_uri = set_info["search_uri"]
    cards = []
    while True:
        response = requests.get(search_uri)
        response.raise_for_status()
        response_json = response.json()
        cards += response_json["data"]
        if not response_json.get("has_more"):
            break

        search_uri = response_json["next_page"]
    return cards
