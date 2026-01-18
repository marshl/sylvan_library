"""
Module for the build_metadata command
"""

import logging
import math
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from sylvan_library.cardsearch.search_metadata import (
    build_metadata_for_card_face,
    build_metadata_for_card,
)
from sylvan_library.cards.models.card import CardFace, Card

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for updating search metadata
    """

    help = "Rebuilds the search metadata. This should be run after each call to apply_changes"

    def add_arguments(self, parser) -> None:
        # Positional arguments
        parser.add_argument(
            "cardname",
            nargs="*",
            type=str,
            help="Any specific cards to ",
        )

    def handle(self, *args: Any, **options: Any):
        if options.get("cardname"):
            cards = Card.objects.filter(name__in=options["cardname"])
            card_faces = CardFace.objects.filter(card__name__in=options["cardname"])
        else:
            cards = Card.objects.all()
            card_faces = CardFace.objects.all()

        card_face_count = card_faces.count()
        card_count = cards.count()

        card_face_change_count = 0
        card_change_count = 0

        with transaction.atomic():
            for idx, card_face in enumerate(
                card_faces.prefetch_related("search_metadata").all()
            ):
                card_face_change_count += build_metadata_for_card_face(card_face)
                if (
                    idx % int(math.ceil(card_face_count / 10)) == 0
                    or idx == card_face_count
                ):
                    logger.info(
                        "Indexed %s of %s card faces (%s changed)",
                        idx + 1,
                        card_face_count,
                        card_face_change_count,
                    )

            for idx, card in enumerate(
                cards.prefetch_related(
                    "search_metadata",
                    "faces",
                    "faces__types",
                    "faces__supertypes",
                    "faces__subtypes",
                ).all()
            ):
                card_change_count += build_metadata_for_card(card)
                if idx % int(math.ceil(card_count / 10)) == 0 or idx == card_count:
                    logger.info(
                        "Indexed %s of %s cards (%s cards changed)",
                        idx + 1,
                        card_count,
                        card_change_count,
                    )
