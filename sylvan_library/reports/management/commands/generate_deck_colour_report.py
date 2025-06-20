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
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, OutputWrapper
from django.db.models import Sum, F
from django.db.models.query import QuerySet

from cards.models.colour import Colour
from cards.models.decks import Deck, DeckCard
from reports.management.commands import download_tournament_decks


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
        decks = Deck.objects.filter(owner=owner, format="standard").prefetch_related(
            "cards__card"
        )
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
        """
        Gets the rows of the ratios of each colour
        :param dates: The dates
        :param decks: The query set of decks
        :return:
        """
        rows = {}
        for created_date in dates:
            date_decks = decks.filter(date_created=created_date)
            if date_decks.count() < 8:
                continue
            row = {}
            for colour in self.colours:
                if colour.symbol == "C":
                    cards = (
                        DeckCard.objects.filter(deck__in=date_decks)
                        .filter(card__faces__colour=0)
                        .exclude(card__faces__types__name="Land")
                    )
                else:
                    cards = (
                        DeckCard.objects.filter(deck__in=date_decks)
                        .annotate(
                            colour_filter=F("card__faces__colour").bitand(
                                colour.bit_value
                            )
                        )
                        .filter(colour_filter__gte=colour.bit_value)
                    )
                # print(cards.query)
                row[colour.symbol] = cards.aggregate(Sum("count"))["count__sum"] or 0
            rows[created_date] = row

        return rows

    def generate_dataframe(
        self, rows: Dict[datetime.date, Dict[str, int]]
    ) -> pd.DataFrame:
        dataframe = pd.DataFrame.from_dict(rows).transpose()
        dataframe = dataframe.divide(dataframe.sum(axis=1), axis=0) * 100
        dataframe.index = pd.to_datetime(dataframe.index)
        dataframe = dataframe.resample("4ME").mean()
        dataframe = dataframe.interpolate(method="linear")
        return dataframe

    def generate_plot(self, data: pd.DataFrame, output_path: str) -> None:
        """
        Generates am image plot for the given dataframe
        :param data: The dataframe to generate the plot for
        :param output_path: THe file output path
        """
        sns.set(rc={"figure.figsize": (18, 5)}, style="white")
        # plt.stackplot(
        #     data.index,
        #     [data[c.symbol] for c in self.colours],
        #     labels=[c.name for c in self.colours],
        #     colors=[c.chart_colour for c in self.colours],
        # )
        colour_map = {
            "W": "#D1CE78",
            "U": "#4D8DC1",
            "B": "#191919",
            "R": "#E03333",
            "G": "#42B569",
            "C": "#878281",
        }

        for c in self.colours:
            plt.plot(data[c.symbol], color=colour_map[c.symbol])
        plt.ylabel("% of deck")
        plt.subplots_adjust(left=0.05, right=0.975)
        sns.despine()

        plt.savefig(output_path + ".png")
        plt.savefig(output_path + ".svg")


"""
SELECT "cards_deckcard"."id", "cards_deckcard"."count", "cards_deckcard"."card_id", "cards_deckcard"."deck_id", "cards_deckcard"."board", "cards_deckcard"."is_commander", COUNT("cards_cardface"."id") AS "num_faces", ("cards_cardface"."colour" & -9) AS "colour_filter"
FROM "cards_deckcard" 
INNER JOIN "cards_card" ON ("cards_deckcard"."card_id" = "cards_card"."id") 
LEFT OUTER JOIN "cards_cardface" ON ("cards_card"."id" = "cards_cardface"."card_id") 
WHERE ("cards_deckcard"."deck_id" IN (SELECT U0."id" FROM "cards_deck" U0 WHERE (U0."format" = standard AND U0."owner_id" = 4 AND U0."date_created" = 2007-07-14))
 AND ("cards_cardface"."colour" & -9) = 0) 
 GROUP BY "cards_deckcard"."id", 8, EXISTS(SELECT 1 AS "a" FROM "cards_cardface" U2 INNER JOIN "cards_cardface_types" U3 ON (U2."id" = U3."cardface_id") INNER JOIN "cards_cardtype" U4 ON (U3."cardtype_id" = U4."id") WHERE (U4."name" = Land AND U2."card_id" = ("cards_deckcard"."card_id")) LIMIT 1) HAVING (NOT (EXISTS(SELECT 1 AS "a" FROM "cards_cardface" U2 INNER JOIN "cards_cardface_types" U3 ON (U2."id" = U3."cardface_id") INNER JOIN "cards_cardtype" U4 ON (U3."cardtype_id" = U4."id") WHERE (U4."name" = Land AND U2."card_id" = ("cards_deckcard"."card_id")) LIMIT 1)) OR COUNT("cards_cardface"."id") = 2)

"""
