"""
Module for the verify_database command
"""
import os
from datetime import date
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from django.core.management.base import BaseCommand, OutputWrapper
from django.db.models.query import QuerySet
from pandas.plotting import register_matplotlib_converters

from cards.models import Deck, User
from sylvan_library.reports.management.commands import download_tournament_decks


class Command(BaseCommand):
    """
    The command for generating the deck rarity report
    """

    help = (
        "Generates an SVG showing deck rarity ratios for all decks downloaded by the "
        "download_tournament_decks_report"
    )

    def __init__(
        self,
        stdout: Optional[OutputWrapper] = None,
        stderr: Optional[OutputWrapper] = None,
        no_color: bool = False,
    ) -> None:
        self.rarities = ["C", "U", "R", "M"]
        register_matplotlib_converters()
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--exclude-lands",
            action="store_true",
            dest="exclude_lands",
            default=False,
            help='Exclude all cards with the "land" type from the result',
        )

    def handle(self, *args, **options) -> None:

        if not options["exclude_lands"]:
            self.rarities.insert(0, "L")

        output_path = os.path.join("reports", "output", "deck_rarity_progression.svg")
        if os.path.exists(output_path):
            os.remove(output_path)

        owner = User.objects.get(
            username=download_tournament_decks.Command.deck_owner_username
        )
        decks = Deck.objects.filter(
            owner=owner  # date_created__lte=date(1998, 1, 1)
        ).prefetch_related("cards__card__printings__set", "cards__card__faces")
        dates = self.get_dates(decks)
        rows = self.get_rarity_ratio_rows(dates, decks, options["exclude_lands"])
        dataframe = self.generate_dataframe(dates, rows)
        self.generate_plot(dataframe, output_path)

    @staticmethod
    def get_dates(decks: QuerySet) -> List[date]:
        """
        Gets the unique list of dates for the given list of decks
        :param decks: The list of decks to get te date for
        :return: The list of dates
        """
        return list(decks.values_list("date_created", flat=True).distinct())

    def get_rarity_ratio_rows(
        self, dates: List[date], decks: QuerySet, exclude_lands: bool = False
    ) -> List[List[float]]:
        """
        Gets the rows of rarity ratios for each of the given dates
        :param dates: The dates to create the rarity ratios for
        :param decks: The queryset of decks
        :param exclude_lands: Whether to exclude lands from the results
        :return: The rarity ratio rows
        """
        rows = []
        for created_date in dates:
            date_decks = decks.filter(date_created=created_date)
            row = [0] * len(self.rarities)
            deck_count = 0
            for deck in date_decks:
                if sum(x.count for x in deck.cards.all()) < 60:
                    continue

                rarity_ratios = self.get_deck_rarity_ratios(deck, exclude_lands)
                for idx, rarity in enumerate(self.rarities):
                    row[idx] += rarity_ratios[rarity] * 100

                deck_count += 1

            if deck_count > 0:
                row = [x / deck_count for x in row]
                rows.append(row)

        return rows

    def generate_dataframe(
        self, dates: List[date], rows: List[List[float]]
    ) -> pd.DataFrame:
        """
        Generates the sampled dataframe based on the dates and rows given
        :param dates: The tournament event dates
        :param rows: The rows
        :return: The pandas dataframe
        """
        sns.set(style="whitegrid")
        sns.set(rc={"figure.figsize": (10, 6)})
        sns.set(color_codes=True)

        date_index = pd.DatetimeIndex(dates)
        data = pd.DataFrame(rows, index=date_index, columns=self.rarities)
        data = data.resample("180D").mean()
        data = data.interpolate(method="cubic")
        return data

    @staticmethod
    def generate_plot(data: pd.DataFrame, output_path: str) -> None:
        """
        Generates am image plot for the given dataframe
        :param data: The dataframe to generate the plot for
        :param output_path: THe file output path
        """
        palette = {
            "L": "#875438",
            "C": "#0E0C0C",
            "U": "#8A8D91",
            "R": "#C1A15B",
            "M": "#EC7802",
        }
        data_perc = data.divide(data.sum(axis=1), axis=0)

        plt.stackplot(
            data_perc.index,
            [
                data_perc["L"],
                data_perc["C"],
                data_perc["U"],
                data_perc["R"],
                data_perc["M"],
            ],
            labels=["Basic Land", "Common", "Uncommon", "Rare", "Mythic Rare"],
            colors=palette.values(),
        )
        plt.legend(loc=3, fontsize="medium")
        plt.ylabel("Proportion of deck")

        plt.savefig(output_path)

    def get_deck_rarity_ratios(self, deck: Deck, exclude_lands: bool = False) -> dict:
        """
        Gets the rarity ratios for a single deck
        :param deck: The deck
        :param exclude_lands: Whether to exclude lands from the results or not
        :return: The rarity ratios
        """
        counts = {r: 0 for r in self.rarities}
        total_count = 0

        for deck_card in deck.cards.all():
            if exclude_lands and "Land" in deck_card.card.type:
                continue

            if "Basic" in deck_card.card.faces.all()[0].type_line:
                counts["L"] += deck_card.count
            else:
                closest_printing = None
                for printing in deck_card.card.printings.all():
                    if printing.set.type not in ["expansion", "core", "starter"]:
                        continue
                    if closest_printing is None or abs(
                        deck.date_created - printing.set.release_date
                    ) < abs(deck.date_created - closest_printing.set.release_date):
                        closest_printing = printing
                if not closest_printing:
                    raise Exception(f"Could not find a valid printing for {deck_card}")

                counts[closest_printing.rarity.symbol] += deck_card.count
            total_count += deck_card.count

        ratios = {key: value / total_count for key, value in counts.items()}
        return ratios
