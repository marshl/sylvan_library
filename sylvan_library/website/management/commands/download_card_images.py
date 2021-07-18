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


SCRYFALL_API_SLEEP_SECONDS = 0.5


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
            get_images_for_set(card_set, [english])

        download_images(self.root_dir)


def download_images(root_dir: str) -> None:
    """
    Downloads images into the given directory
    :param root_dir: The path to the directory where the images should be placed
    """
    for card_image in CardImage.objects.filter(file_path__isnull=True):
        try:
            stream = requests.get(card_image.scryfall_image_url)
            stream.raise_for_status()
        except requests.HTTPError:
            logger.exception(
                "Could not download %s for %s",
                card_image.scryfall_image_url,
                card_image,
            )
            raise

        url_path = urlparse(card_image.scryfall_image_url).path
        url_parts = url_path.split("/")
        if "normal" not in url_parts:
            raise ValueError(f"Invalid image URL {card_image.scryfall_image_url}")

        url_parts = url_parts[url_parts.index("normal") :]

        image_rel_path = os.path.join("card_images", *url_parts)
        full_download_path = os.path.join(root_dir, image_rel_path)
        logger.info(
            "Downloading %s to %s", card_image.scryfall_image_url, full_download_path
        )
        os.makedirs(os.path.dirname(full_download_path), exist_ok=True)
        with open(full_download_path, "wb") as output:
            output.write(stream.content)
            card_image.file_path = image_rel_path
            card_image.save()


def get_images_for_set(card_set: Set, languages: List[Language]) -> None:
    """
    Gets the images for
    :param card_set:
    :param languages:
    :return:
    """
    logger.info("Checking set %s", card_set)
    faces_missing_images = (
        CardFaceLocalisation.objects.filter(localisation__card_printing__set=card_set)
        .filter(localisation__language__in=languages)
        .filter(image__isnull=True)
    )

    if not faces_missing_images.exists():
        logger.info("No missing images in %s", card_set)
        return

    try:
        card_data = get_scryfall_cards(card_set.code)
    except HTTPError:
        logger.warning("Could not get cards for %s", card_set)
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
            image_url = image_url.split("?")[0]
            logger.info(
                "Setting %s to have image %s",
                " & ".join(str(m) for m in matching_faces.all()),
                image_url,
            )
            with transaction.atomic():
                new_image, _ = CardImage.objects.get_or_create(
                    scryfall_image_url=image_url
                )
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
                    new_image = CardImage.objects.create(scryfall_image_url=image_url)
                    matching_face.update(image=new_image)
        else:
            raise ValueError(f"Unhandled card type: {scryfall_card}")

    if faces_missing_images.filter(image__isnull=True):
        logger.warning(
            "Did not end up finding images for the following cards: %s",
            ", ".join(str(face) for face in faces_missing_images),
        )


def get_scryfall_set(set_code: str) -> dict:
    """
    Gets a Set from the Scryfall API (and waits a bit to be nice)
    :param set_code: The code of the set to get the data for
    :return: The set JSON
    """
    url = f"https://api.scryfall.com/sets/{set_code}"
    logger.info("Getting set data from %s", url)
    response = requests.get(url)
    response.raise_for_status()
    time.sleep(SCRYFALL_API_SLEEP_SECONDS)
    return response.json()


def get_scryfall_cards(set_code: str) -> list:
    """
    Gets tne cards from the scryfall API for the given set
    :param set_code: The setcode to get teh cards for
    :return: The cards
    """
    set_info = get_scryfall_set(set_code)
    search_uri = set_info["search_uri"] + "&include_extras=true&include_variations=true"
    cards = []
    while True:
        logger.info("Searching for cards %s", search_uri)
        response = requests.get(search_uri)
        response.raise_for_status()
        response_json = response.json()
        cards += response_json["data"]
        if not response_json.get("has_more"):
            break

        search_uri = response_json["next_page"]
        time.sleep(SCRYFALL_API_SLEEP_SECONDS)
    return cards
