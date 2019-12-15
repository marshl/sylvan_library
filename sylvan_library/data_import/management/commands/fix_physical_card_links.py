"""
Module for the update_printing_uids command
"""
import logging
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from _query import query_yes_no
from cards.models import CardPrinting, PhysicalCard
from data_import.staging import StagedCard, StagedCardPrinting
from data_import.management.commands import get_all_set_data
from collections import defaultdict

from _query import query_yes_no

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = ()

    def add_arguments(self, parser):
        pass

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
