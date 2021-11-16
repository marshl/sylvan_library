"""
Module for the generate_deck_colour_report command
"""

import datetime
import os
from datetime import date
from typing import List, Optional, Dict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from django.core.management.base import BaseCommand, OutputWrapper
from django.db.models import Sum
from django.db.models.query import QuerySet

from cards.models import Deck, User, Colour, DeckCard
from sylvan_library.reports.management.commands import download_tournament_decks


class Command(BaseCommand):
    """
    The command for generating the deck colour report
    """

    help = (
        "Generates an SVG showing deck colour ratios for all decks downloaded by the "
        "download_tournament_decks_report command"
    )

    def __init__(
        self,
        stdout: Optional[OutputWrapper] = None,
        stderr: Optional[OutputWrapper] = None,
        no_color: bool = False,
    ) -> None:
        self.colours = Colour.objects.all().order_by("display_order")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def handle(self, *args, **options) -> None:
        image_path = os.path.join("reports", "output", "deck_colour_progression")
        owner = User.objects.get(
            username=download_tournament_decks.Command.deck_owner_username
        )
        decks = Deck.objects.filter(owner=owner).prefetch_related("cards__card")
        dates = self.get_dates(decks)
        rows = self.get_colour_ratio_rows(dates, decks)
        dataframe = self.generate_dataframe(rows)
        self.generate_plot(dataframe, image_path)

    @staticmethod
    def get_dates(decks: QuerySet) -> List[date]:
        """
        Gets the unique list of dates for the given list of decks
        :param decks: The list of decks to get te date for
        :return: The list of dates
        """
        dates = list(decks.values_list("date_created", flat=True).distinct())
        return sorted(dates)

    def get_colour_ratio_rows(
        self, dates: List[date], decks: QuerySet
    ) -> Dict[date, Dict[str, int]]:
        rows = {}
        for created_date in dates:
            date_decks = decks.filter(date_created=created_date)
            row = {}
            for colour in self.colours:
                cards = (
                    DeckCard.objects.filter(deck__in=date_decks)
                    .filter(card__colour_flags=colour.bit_value)
                    .exclude(card__type__contains="Land")
                )
                row[colour.symbol] = cards.aggregate(Sum("count"))["count__sum"] or 0
            rows[created_date] = row

        return rows

    def generate_dataframe(
        self, rows: Dict[datetime.date, Dict[str, int]]
    ) -> pd.DataFrame:
        """
        Gets the dataframe from the given rows of dates to ownership counts
        :param rows:
        :return:
        """
        dataframe = pd.DataFrame.from_dict(rows).transpose()
        dataframe = dataframe.divide(dataframe.sum(axis=1), axis=0)
        dataframe.index = pd.to_datetime(dataframe.index)
        dataframe = dataframe.resample("3M").mean()
        dataframe = dataframe.interpolate(method="linear")
        return dataframe

    def generate_plot(self, data: pd.DataFrame, output_path: str) -> None:
        """
        Generates am image plot for the given dataframe
        :param data: The dataframe to generate the plot for
        :param output_path: THe file output path
        """
        sns.set(rc={"figure.figsize": (18, 5)}, style="white")
        plt.stackplot(
            data.index,
            [data[c.symbol] for c in self.colours],
            labels=[c.name for c in self.colours],
            colors=[c.chart_colour for c in self.colours],
        )
        # for c in self.colours:
        #     plt.plot(data[c.symbol], color=c.chart_colour)
        plt.ylabel("Proportion of deck")
        plt.subplots_adjust(left=0.05, right=0.975)
        sns.despine()

        plt.savefig(output_path + ".png")
        plt.savefig(output_path + ".svg")
"""

WITH ownerships AS (
	SELECT card.id, card.name, SUM(ownedcard.count) ownership_count
	FROM cards_card card
	JOIN cards_cardprinting cardprinting
	ON cardprinting.card_id = card.id
	JOIN cards_cardlocalisation localisation
	ON localisation.card_printing_id = cardprinting.id
	JOIN cards_userownedcard ownedcard
	ON ownedcard.card_localisation_id = localisation.id
	WHERE ownedcard.owner_id = 5
	GROUP BY card.id 
), changes AS (
	SELECT card.id, card.name, SUM(cardchange.difference) change_count
	FROM cards_card card
	JOIN cards_cardprinting cardprinting
	ON cardprinting.card_id = card.id
	JOIN cards_cardlocalisation localisation
	ON localisation.card_printing_id = cardprinting.id
	JOIN cards_usercardchange cardchange
	ON cardchange.card_localisation_id = localisation.id
	WHERE cardchange.owner_id = 5
	AND cardchange.date > DATE '2011-01-01'
	GROUP BY card.id 
	HAVING SUM(cardchange.difference) > 0
), cards_as_of AS (
	SELECT 
	ownerships.id, 
	ownerships.name, 
	ownerships.ownership_count - COALESCE(changes.change_count, 0) total
	FROM ownerships LEFT JOIN changes
	ON ownerships.id = changes.id
	ORDER BY total DESC
)
SELECT COUNT(*) FROM cards_as_of WHERE total > 0
--SELECT * FROM cards_as_of
"""