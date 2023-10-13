"""
Module for the verify_database command
"""
import os
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
from django.core.management.base import BaseCommand, OutputWrapper
from django.db import connection
from pandas.plotting import register_matplotlib_converters


class Command(BaseCommand):
    """
    The command for generating the deck rarity report
    """

    help = (
        "Generates an SVG showing deck complexity creep for all decks downloaded by the "
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

        output_path = os.path.join(
            "reports", "output", "deck_complexity_progression.svg"
        )
        dataframe = self.get_data()
        self.generate_plot(dataframe, output_path)

    @staticmethod
    def generate_plot(data: pd.DataFrame, output_path: str) -> None:
        """
        Generates am image plot for the given dataframe
        :param data: The dataframe to generate the plot for
        :param output_path: THe file output path
        """
        plt.plot(
            data["average_words"],
            label="Oracle text"
            # labels=[
            #     "Average oracle words",
            #     "Average oracle words w/o reminder text",
            #     "Average printed words",
            #     "Average printed words w/0 reminder text",
            # ],
        )
        plt.plot(
            data["average_original_words"],
            label="Printed text",
        )
        plt.plot(
            data["average_words_no_reminder"],
            label="Oracle text w/o reminder text",
        )
        plt.plot(
            data["average_original_words_no_reminder"],
            label="Printed text w/o reminder text",
        )
        plt.legend(loc=2, fontsize="medium")
        plt.ylabel("Average # of words per card")

        plt.savefig(output_path, bbox_inches="tight")

    def get_data(self):
        cur = connection.cursor()
        cur.execute(
            """\
SELECT
tournament_date,
AVG(average_words) average_words,
AVG(average_words_no_reminder) average_words_no_reminder,
AVG(average_original_words) average_original_words,
AVG(average_original_words_no_reminder) average_orignal_words_no_reminder
FROM (
	SELECT
	deck_id,
	tournament_date,
	SUM(word_count * card_count)::decimal / SUM(card_count) average_words,
	SUM(word_count_no_reminder * card_count)::decimal / SUM(card_count) average_words_no_reminder,
	SUM(original_word_count * card_count)::decimal / SUM(card_count) average_original_words,
	SUM(original_word_count_no_reminder * card_count)::decimal / SUM(card_count) average_original_words_no_reminder
	FROM (
		SELECT
		card_id,
		deck_id,
		tournament_date,
		card_count,
		REGEXP_COUNT(rules_text, '\s') AS word_count,
		REGEXP_COUNT(REGEXP_REPLACE(rules_text, '\(.+?\)', '', 'g'), '\s') AS word_count_no_reminder,
		REGEXP_COUNT(original_text, '\s') AS original_word_count,
		REGEXP_COUNT(REGEXP_REPLACE(original_text, '\(.+?\)', '', 'g'), '\s') AS original_word_count_no_reminder
		FROM (
			SELECT
			cards_card.id AS card_id,
			cards_deck.id AS deck_id,
			cards_deck.date_created AS tournament_date,
			cards_deckcard.count AS card_count,
			cards_set.name,
			STRING_AGG(cards_cardface.rules_text, ' ') AS rules_text,
			STRING_AGG(COALESCE(cards_cardfaceprinting.original_text, cards_cardface.rules_text), ' ') AS original_text,
			ROW_NUMBER() OVER (PARTITION BY cards_deckcard.id ORDER BY cards_set.release_date DESC) AS release_order
			FROM cards_deck
			JOIN cards_deckcard ON cards_deck.id = cards_deckcard.deck_id
			JOIN cards_card ON cards_deckcard.card_id = cards_card.id
			JOIN cards_cardface ON cards_card.id = cards_cardface.card_id
			JOIN cards_cardprinting ON cards_card.id = cards_cardprinting.card_id
			JOIN cards_cardfaceprinting ON cards_cardprinting.id = cards_cardfaceprinting.card_printing_id
			JOIN cards_set ON cards_cardprinting.set_id = cards_set.id
			WHERE cards_set.release_date <= cards_deck.date_created
			--AND cards_card.id = 1855
			AND cards_deck.format = 'standard'
			AND cards_deck.owner_id = 4
			--AND cards_deck.id = 292
			--AND (cards_cardface.rules_text IS NULL OR cards_cardfaceprinting.original_text IS NOT NULL)
			--AND cards_cardfaceprinting.original_type NOT LIKE '%Land%'
			--AND cards_cardface.type_line NOT LIKE '%Basic%'
			GROUP BY cards_deck.id, cards_deckcard.id, cards_card.id, cards_set.id, cards_cardprinting.id
		) AS card_counts
		WHERE card_counts.release_order = 1
		--AND deck_id = 252
		--ORDER BY tournament_date DESC, deck_id
	) AS card_counts2
	--WHERE tournament_date < DATE('2001-01-01')
	GROUP BY deck_id, tournament_date
	--ORDER BY 3 DESC
) AS deck_counts
GROUP BY tournament_date
ORDER BY tournament_date
"""
        )
        data = list(cur.fetchall())
        df = pd.DataFrame(
            data,
            columns=[
                "tournament_date",
                "average_words",
                "average_words_no_reminder",
                "average_original_words",
                "average_original_words_no_reminder",
            ],
        )

        df = df.set_index("tournament_date")
        df.set_index(pd.to_datetime(df.index, utc=True), inplace=True)

        # df = df.pivot_table(
        #     index="tournament_date", values="card_count", columns="rarity"
        # )
        # df = df.div(df.sum(axis=1), axis=0)
        df = df.resample("6M").mean()
        df = df.dropna()
        # df = df.fillna(0)
        # df = df.interpolate(method="linear")
        return df
