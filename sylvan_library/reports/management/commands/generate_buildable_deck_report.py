from typing import Dict

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models.query import QuerySet

from cards.models.card import UserOwnedCard
from cards.models.decks import Deck
from reports.management.commands import download_tournament_decks


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "username",
            nargs=1,
            type=str,
            help="The username",
        )
        parser.add_argument(
            "--exclude-lands",
            action="store_true",
            dest="exclude_lands",
            default=False,
            help='Exclude all cards with the "land" type from the result',
        )

    def handle(self, *args, **options) -> None:
        input_user = get_user_model().objects.get(username=options.get("username")[0])

        mtgtop8_owner = get_user_model().objects.get(
            username=download_tournament_decks.Command.deck_owner_username
        )
        decks: QuerySet[Deck] = Deck.objects.filter(owner=mtgtop8_owner)
        exclude_lands = options["exclude_lands"]

        card_ownership: Dict[int, int] = {}

        for ownership in UserOwnedCard.objects.filter(owner=input_user):
            card_id = ownership.card_localisation.card_printing.card_id
            if card_id not in card_ownership:
                card_ownership[card_id] = ownership.count
            else:
                card_ownership[card_id] += ownership.count

        deck_ratios = []
        for deck in decks:
            have_cards = 0
            dont_have_cards = 0

            deck_cards = deck.cards.filter(board="main")
            if exclude_lands:
                deck_cards = deck_cards.filter(board="main").exclude(
                    card__faces__types__name="Land"
                )
            for deck_card in deck_cards:
                count = deck_card.count
                have = min(card_ownership.get(deck_card.card_id, 0), count)
                have_cards += have
                count -= have
                dont_have_cards += count

            if dont_have_cards + have_cards > 0:
                deck_ratios.append(
                    (have_cards / (have_cards + dont_have_cards), deck.id)
                )

        deck_ratios.sort(key=lambda x: x[0], reverse=True)

        for ratio, deck_id in deck_ratios[:100]:
            deck = Deck.objects.get(id=deck_id)
            print(deck.name, deck.description, ratio)
