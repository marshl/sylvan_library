"""
Module for the verify_database command
"""

import csv
import datetime
import os
from typing import Optional

import arrow
import matplotlib.pyplot as plt
import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, OutputWrapper
from django.db import connection
from pandas.plotting import register_matplotlib_converters

from cards.models.decks import Deck
from data_import.management.commands import print_progress
from reports.management.commands import download_tournament_decks


class Command(BaseCommand):
    """
    The command for generating the deck rarity report
    """

    help = (
        "Generates an SVG showing deck complexity creep for all decks downloaded by the "
        "download_tournament_decks_report"
    )

    def handle(self, *args, **options) -> None:
        image_path = os.path.join("reports", "output", "modern_first_comparison")
        owner = get_user_model().objects.get(
            username=download_tournament_decks.Command.deck_owner_username
        )
        start_of_graph = start_arrow = arrow.get("2019-01-01")

        dates = []
        legality_ratios = []
        deck_usage_ratios = []
        with open(
            image_path + ".csv",
            "w",
            newline="\n",
            encoding="utf-8",
        ) as file:
            csvfile = csv.writer(file)
            csvfile.writerow(
                [
                    "month",
                    "modern_cards",
                    "modern_only_cards",
                    "deck_cards",
                    "modern_only_cards_used",
                ]
            )
            while start_arrow < arrow.now():
                end_arrow = start_arrow.ceil("month")
                cards_legal_in_modern = self.get_cards_legal_in_modern(
                    end_arrow.date(), modern_first_only=False
                )
                modern_only_legal_in_modern = self.get_cards_legal_in_modern(
                    end_arrow.date(), modern_first_only=True
                )
                total_cards_used = self.get_cards_used_in_month(
                    owner.id, start_arrow.date(), end_arrow.date()
                )
                modern_first_cards_used = (
                    self.get_cards_used_in_month(
                        owner.id,
                        start_arrow.date(),
                        end_arrow.date(),
                        modern_first_only=True,
                    )
                    or 0
                )
                if total_cards_used:
                    dates.append(start_arrow.date())
                    legality_ratios.append(
                        modern_only_legal_in_modern / cards_legal_in_modern * 100
                    )
                    deck_usage_ratios.append(
                        modern_first_cards_used / total_cards_used * 100
                    )
                    csvfile.writerow(
                        [
                            start_arrow.format("YYYY-MM-DD"),
                            cards_legal_in_modern,
                            modern_only_legal_in_modern,
                            total_cards_used,
                            modern_first_cards_used,
                        ]
                    )
                print_progress(
                    (start_arrow - start_of_graph).total_seconds()
                    / (arrow.now() - start_of_graph).total_seconds()
                )
                start_arrow = start_arrow.shift(months=+1)

        # Note that even in the OO-style, we use `.pyplot.figure` to create the Figure.
        fig, ax = plt.subplots(figsize=(5 * 1.5, 2.7 * 1.5), layout="constrained")
        ax.plot(
            dates,
            legality_ratios,
            label="% of Modern legal cards from Straight-to-Modern sets",
        )
        ax.plot(
            dates,
            deck_usage_ratios,
            label="% of cards in Modern decks from Straight-to-Modern sets",
        )
        # ax.set_title("Simple Plot")
        ax.legend(loc="upper left")
        plt.annotate(
            "%0.2f%%" % legality_ratios[-1],
            xy=(1, legality_ratios[-1]),
            xytext=(8, 0),
            xycoords=("axes fraction", "data"),
            textcoords="offset points",
        )
        plt.annotate(
            "%0.2f%%" % deck_usage_ratios[-1],
            xy=(1, deck_usage_ratios[-1]),
            xytext=(8, 0),
            xycoords=("axes fraction", "data"),
            textcoords="offset points",
        )
        plt.savefig(image_path + ".svg")
        plt.savefig(image_path + ".png")
        plt.show()

    def get_cards_legal_in_modern(
        self, before_date: datetime.date, modern_first_only=False
    ) -> int:
        cur = connection.cursor()
        query = f"""
SELECT COUNT(DISTINCT card.id)
FROM cards_card card
JOIN cards_cardprinting cardprinting
ON card.id = cardprinting.card_id
JOIN cards_set set
ON set.id = cardprinting.set_id
WHERE set.release_date <= %s
AND (set.type IN ('core', 'expansion') OR set.code IN ('MH1', 'MH2', 'MH3', 'LTR'))
AND set.release_date >= (SELECT release_date FROM cards_set WHERE code = '8ED')
AND (NOT %s OR card.id IN ({self.get_modern_first_query()}))
"""
        cur.execute(query, (before_date, modern_first_only))
        row = cur.fetchone()
        return row[0]

    def get_modern_first_query(self):
        return """
SELECT DISTINCT id FROM (
    SELECT
    cards_card.id,
    cards_card.name,
    cards_set.code,
    RANK() OVER (PARTITION BY cards_card.id ORDER BY cards_set.release_date ASC) rnk
    FROM cards_card
    JOIN cards_cardprinting
    ON cards_cardprinting.card_id = cards_card.id
    JOIN cards_set ON cards_set.id = cards_cardprinting.set_id
    WHERE (
        cards_set.type IN ('core', 'expansion')
        AND cards_set.release_date >= (SELECT release_date FROM cards_set WHERE code = '8ED')
    ) OR code IN ('MH1', 'MH2', 'MH3', 'LTR')
) t1
WHERE code IN ('MH1', 'MH2', 'MH3', 'LTR')
AND rnk = 1
"""

    def get_cards_used_in_month(
        self,
        user_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        modern_first_only: bool = False,
    ) -> int:
        cur = connection.cursor()
        query = f"""
SELECT SUM(deckcard.count)
FROM cards_deck deck
JOIN cards_deckcard deckcard
ON deckcard.deck_id = deck.id
WHERE format = 'modern'
AND deck.owner_id = %s
AND deck.date_created >= %s AND deck.date_created <= %s
AND (NOT %s OR deckcard.card_id IN ({self.get_modern_first_query()}))
"""
        cur.execute(query, (user_id, start_date, end_date, modern_first_only))
        row = cur.fetchone()
        return row[0]
