"""
Module for the fix_physical_card_links command
"""
import logging
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count

from cards.models import PhysicalCard

from _query import query_yes_no

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Finds two faced cards that have accidentally been linked to three different cards due
    to there now being sets like ELdraine where there are multiple printings of the
    same two-faced card in the same set, which can then get linked linked back to the
    first printing in that set, instead of being linked to their later version
    """

    help = "Finds ahd fixes erroneous triply linked two-faced cards"

    def handle(self, *args, **options):
        triple_cards = list(
            PhysicalCard.objects.annotate(printlang_count=Count("printed_languages"))
            .filter(printlang_count=3)
            .filter(layout="adventure")
            .prefetch_related("printed_languages__card_printing__card")
        )
        for triple_card in triple_cards:
            print(str(triple_card))
            number_counts = defaultdict(int)
            for printlang in triple_card.printed_languages.all():
                print(str(printlang))
                number_counts[printlang.card_printing.number] += 1

            odd_number = next(k for k, v in number_counts.items() if v == 1)
            odd_one_out = triple_card.printed_languages.get(
                card_printing__number=odd_number
            )

            print("Odd one out: ", odd_one_out)

            if query_yes_no(f"Delete {odd_one_out}?"):
                triple_card.printed_languages.remove(odd_one_out)
