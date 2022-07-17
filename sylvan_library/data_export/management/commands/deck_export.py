"""
The module for the deck_export command
"""

import logging
import os
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from cards.models.decks import Deck
from website.templatetags.deck_templatetags import deck_card_group_count

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for exporting user decks
    """

    help = "Exports user owned decks"

    def add_arguments(self, parser) -> None:
        # Positional arguments
        parser.add_argument(
            "username",
            nargs=1,
            type=str,
            help="The user whose decks should be exported",
        )

    def handle(self, *args, **options):

        output_directory = os.path.join("data_export", "output")
        username = options.get("username")[0]

        if not os.path.exists(output_directory):
            logger.error("Could not find directory %s", output_directory)
            return

        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            logger.error("User with name %s could not be found", username)
            return

        output_directory = os.path.join(output_directory, slugify(user.username))

        os.makedirs(output_directory, exist_ok=True)

        self.export_decks(output_directory, user)

    def export_decks(self, output_directory: str, user: get_user_model()):
        deck: Deck
        for deck in user.decks.filter(is_prototype=False):
            deck_slug = slugify(f"{deck.date_created.isoformat()} {deck.name}")
            filename = os.path.join(output_directory, f"{deck_slug}.txt")
            print(deck.name, filename)
            # if os.path.exists(filename):
            #     continue

            deck = Deck.objects.prefetch_related("cards__card").get(id=deck.id)

            with open(filename, "w", encoding="utf-8") as file:
                file.write(f"// Name: {deck.name}\n")
                file.write(f"// Date: {deck.date_created.isoformat()}\n")
                if deck.description:
                    # Add // to newlines
                    commented_description = re.sub(
                        r"^(.+?)$", r"// \1", deck.description, flags=re.MULTILINE
                    )
                    # Remove only carriage returns
                    commented_description = re.sub(
                        r"\r", r"\n", commented_description, flags=re.MULTILINE
                    )
                    # Remove blank lines
                    commented_description = re.sub(
                        r"\n\s*\n", "\n", commented_description, flags=re.MULTILINE
                    )
                    file.write(f"// Description: \n{commented_description}\n")
                if deck.format:
                    pretty_format = next(
                        (f[1] for f in Deck.FORMAT_CHOICES if f[0] == deck.format),
                        deck.format,
                    )
                    file.write(f"// Format: {pretty_format}\n")

                file.write("\n")

                for card_group in deck.get_card_groups():
                    if not card_group["cards"]:
                        continue
                    file.write(f"// {deck_card_group_count(card_group['cards'])} {card_group['name']}\n")
                    for card in card_group["cards"]:
                        file.write(f"{card.as_deck_text()}\n")

                sideboard = deck.get_cards("side")
                if sideboard:
                    file.write("\n")
                    file.write("// Sideboard:\n")
                    for card in sideboard:
                        file.write(f"{card.as_deck_text()}\n")
