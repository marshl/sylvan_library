"""
Module for the verify_database command
"""
import datetime
import os
from datetime import date
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, OutputWrapper
from django.db import connection
from django.db.models.query import QuerySet
from pandas.plotting import register_matplotlib_converters

from cards.models.decks import Deck
from reports.management.commands import download_tournament_decks


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
            "--rebuild",
            action="store_true",
            dest="rebuild",
            default=False,
            help="Whether to regenerate the dataframe",
        )
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
        # if os.path.exists(output_path):
        #     os.remove(output_path)

        dataframe = self.get_data()
        # return
        # dataframe = self.get_dataframe(options["rebuild"], options["exclude_lands"])
        self.generate_plot(dataframe, output_path)

    #
    # def get_dataframe(self, rebuild_data=False, exclude_lands=False):
    #     dataframe_cache_path = os.path.join(
    #         "reports", "output", "deck_rarity_progression.csv"
    #     )
    #     if not rebuild_data and os.path.exists(dataframe_cache_path):
    #         df = pd.read_csv(dataframe_cache_path).set_index("date")
    #         return df
    #
    #     owner = User.objects.get(
    #         username=download_tournament_decks.Command.deck_owner_username
    #     )
    #     decks = Deck.objects.filter(
    #         owner=owner  # , date_created__lte=date(1998, 1, 1)
    #     ).prefetch_related("cards__card__printings__set", "cards__card__faces")
    #     dates = self.get_dates(decks)
    #     rows = self.get_rarity_ratio_rows(dates, decks, exclude_lands)
    #     date_index = pd.DatetimeIndex(dates)
    #     df = pd.DataFrame(rows, index=date_index, columns=self.rarities)
    #     df = df.resample("1M").mean()
    #     df = df.interpolate(method="linear")
    #     df.to_csv(dataframe_cache_path, index_label="date")
    #     return df

    @staticmethod
    def get_dates(decks: QuerySet) -> List[date]:
        """
        Gets the unique list of dates for the given list of decks
        :param decks: The list of decks to get te date for
        :return: The list of dates
        """
        return list(decks.values_list("date_created", flat=True).distinct())

    #
    # def get_rarity_ratio_rows(
    #     self, dates: List[date], decks: QuerySet, exclude_lands: bool = False
    # ) -> List[List[float]]:
    #     """
    #     Gets the rows of rarity ratios for each of the given dates
    #     :param dates: The dates to create the rarity ratios for
    #     :param decks: The queryset of decks
    #     :param exclude_lands: Whether to exclude lands from the results
    #     :return: The rarity ratio rows
    #     """
    #     rows = []
    #     for created_date in dates:
    #         date_decks = decks.filter(date_created=created_date)
    #         row = [0] * len(self.rarities)
    #         deck_count = 0
    #         for deck in date_decks:
    #             if sum(x.count for x in deck.cards.all()) < 60:
    #                 continue
    #
    #             rarity_ratios = self.get_deck_rarity_ratios(deck, exclude_lands)
    #             for idx, rarity in enumerate(self.rarities):
    #                 row[idx] += rarity_ratios[rarity] * 100
    #
    #             deck_count += 1
    #
    #         if deck_count > 0:
    #             row = [x / deck_count for x in row]
    #             rows.append(row)
    #
    #     return rows

    @staticmethod
    def generate_plot(data: pd.DataFrame, output_path: str) -> None:
        """
        Generates am image plot for the given dataframe
        :param data: The dataframe to generate the plot for
        :param output_path: THe file output path
        """

        # penguins = sns.load_dataset("penguins")
        # plot = sns.displot(
        #     penguins, x="flipper_length_mm", hue="species", kind="kde", multiple="stack"
        # )
        # plot = sns.displot(
        #     data, x="tournament_date", hue="rarity", kind="kde", multiple="stack"
        # )
        #
        # plot.savefig(output_path)
        # return

        # sns.set_theme(style="whitegrid")

        # Load the diamonds dataset
        # diamonds = sns.load_dataset("diamonds")
        # df = data.reset_index()
        # sns.set(style="whitegrid")
        # sns.set(rc={"figure.figsize": (10, 6)})
        # sns.set(color_codes=True)
        # # Plot the distribution of clarity ratings, conditional on carat
        # plot = sns.displot(
        #     # data=diamonds,
        #     data=df,
        #     x="tournament_date",
        #     # hue="cut",
        #     # hue="rarity",
        #     kind="kde",
        #     height=6,
        #     multiple="fill",
        #     clip=(0, None),
        #     palette="ch:rot=-.25,hue=1,light=.75",
        # )
        # plot.savefig(output_path)
        # return

        palette = {
            # "L": "#474040",
            "C": "#1a1718",
            "U": "#707883",
            "R": "#a58e4a",
            "M": "#bf4427",
        }
        plt.figure(figsize=(15, 5))
        plt.stackplot(
            data.index,
            [
                # data["L"],
                data["C"],
                data["U"],
                data["R"],
                data["M"],
            ],
            labels=["Common", "Uncommon", "Rare", "Mythic"],
            colors=palette.values(),
        )
        plt.legend(loc=3, fontsize="medium")
        plt.ylabel("Proportion of deck")
        # plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
        plt.savefig(output_path, bbox_inches="tight")
        plt.show()

    #
    # def get_deck_rarity_ratios(self, deck: Deck, exclude_lands: bool = False) -> dict:
    #     """
    #     Gets the rarity ratios for a single deck
    #     :param deck: The deck
    #     :param exclude_lands: Whether to exclude lands from the results or not
    #     :return: The rarity ratios
    #     """
    #     counts = {r: 0 for r in self.rarities}
    #     total_count = 0
    #
    #     for deck_card in deck.cards.all():
    #         if exclude_lands and "Land" in deck_card.card.type:
    #             continue
    #
    #         if "Basic" in deck_card.card.faces.all()[0].type_line:
    #             counts["L"] += deck_card.count
    #         else:
    #             closest_printing = None
    #             for printing in deck_card.card.printings.all():
    #                 if printing.set.type not in ["expansion", "core", "starter"]:
    #                     continue
    #                 if printing.rarity.symbol not in counts:
    #                     continue
    #
    #                 if closest_printing is None or abs(
    #                     deck.date_created - printing.set.release_date
    #                 ) < abs(deck.date_created - closest_printing.set.release_date):
    #                     closest_printing = printing
    #             if not closest_printing:
    #                 raise Exception(f"Could not find a valid printing for {deck_card}")
    #
    #             counts[closest_printing.rarity.symbol] += deck_card.count
    #         total_count += deck_card.count
    #
    #     ratios = {key: value / total_count for key, value in counts.items()}
    #     return ratios
    def get_data(self):
        cur = connection.cursor()
        cur.execute(
            """\
SELECT tournament_date, symbol, SUM(card_total)
FROM (
  SELECT
  card_counts.card_id,
  card_counts.card_total,
  card_counts.tournament_date,
  cards_rarity.symbol,
  ROW_NUMBER() OVER (PARTITION BY cards_card.id ORDER BY cards_set.release_date DESC) AS release_order
  FROM (
    SELECT
    cards_deckcard.card_id,
    SUM(cards_deckcard.count) card_total,
    cards_deck.date_created tournament_date
    FROM cards_deck
    JOIN cards_deckcard ON cards_deck.id = cards_deckcard.deck_id
    WHERE cards_deck.format = 'standard'
    AND cards_deck.owner_id = 4
    GROUP BY cards_deckcard.card_id, cards_deck.date_created
  ) AS card_counts
  JOIN cards_card ON cards_card.id = card_counts.card_id
  JOIN cards_cardprinting ON cards_cardprinting.card_id = cards_card.id
  JOIN cards_set ON cards_set.id = cards_cardprinting.set_id
  JOIN cards_rarity ON cards_cardprinting.rarity_id = cards_rarity.id
  WHERE cards_set.release_date <= card_counts.tournament_date
  AND cards_set.type IN ('expansion', 'core', 'starter')
  AND NOT cards_set.is_online_only
  AND cards_card.name NOT IN ('Plains', 'Island', 'Mountain', 'Swamp', 'Forest')
  AND cards_rarity.symbol != 'S'
) AS ranked_counts
WHERE ranked_counts.release_order = 1
GROUP BY tournament_date, symbol
ORDER BY tournament_date ASC 
"""
        )
        # for tournament_date, rarity, card_total in cur.fetchall():
        #     print(tournament_date, rarity, card_total)
        data = list(cur.fetchall())
        df = pd.DataFrame(data, columns=["tournament_date", "rarity", "card_count"])

        # date_index = pd.DatetimeIndex(dates)
        # df = pd.DataFrame(rows, index=date_index, columns=self.rarities)
        # df.set_index(pd.to_datetime(df.index, utc=True), inplace=True)
        df = df.set_index("tournament_date")
        df.set_index(pd.to_datetime(df.index, utc=True), inplace=True)
        # gb = df.groupby(["rarity"])
        # df = gb.resample("5Min")

        df = df.pivot_table(
            index="tournament_date", values="card_count", columns="rarity"
        )
        df = df.fillna(0.0)
        df = df.div(df.sum(axis=1), axis=0)
        df = df.resample("3ME").mean()
        df = df.interpolate(method="linear")
        # df = df.interpolate(method="cubic")
        return df
        # df.to_csv(dataframe_cache_path, index_label="date")
