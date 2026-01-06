"""
Module for the update_prices command
"""

import datetime
import logging
import os
import typing
import zipfile
from collections import defaultdict
from typing import Any

import arrow
import ijson
from django.core.management.base import BaseCommand
from django.db import transaction, connection

from sylvan_library.cards.models.card_price import CardPrice
from data_import import _paths
from sylvan_library.data_import.management.commands import download_file

logger = logging.getLogger("django")


def download_prices(start_of_week: datetime.date) -> bool:
    logger.info("Checking for up-to-date price files")
    if os.path.isfile(_paths.PRICES_JSON_PATH):
        with open(_paths.PRICES_JSON_PATH, "r", encoding="utf8") as prices_file:
            meta = ijson.items(prices_file, "meta")
            meta_data = next(meta)
            date = arrow.get(meta_data["date"]).date()
            if date >= arrow.get(start_of_week).shift(weeks=-1).date():
                logger.info(
                    "The price file is up to date, no need to download them again"
                )
                return False
    logger.info("Downloading prices")
    download_file(_paths.PRICES_ZIP_DOWNLOAD_URL, _paths.PRICES_ZIP_PATH)

    logger.info("Extracting price file")
    with zipfile.ZipFile(_paths.PRICES_ZIP_PATH) as prices_zip_file:
        prices_zip_file.extractall(_paths.IMPORT_FOLDER_PATH)

    return True


def set_latest_prices():
    logger.info("Setting latest prices")
    with connection.cursor() as cursor:
        cursor.execute(
            """
UPDATE cards_cardprinting
SET latest_price_id = latest_price.id
FROM (
    SELECT *
    FROM (
        SELECT cardprice.*,
        RANK() OVER (PARTITION BY card_printing_id ORDER BY date DESC) rnk
        FROM cards_cardprice cardprice
    ) ranked_prices
    WHERE rnk = 1
) latest_price
WHERE latest_price.card_printing_id = cards_cardprinting.id
"""
        )


def set_cheapest_prices():
    with connection.cursor() as cursor:
        logger.info("Unsetting cheapest prices")
        cursor.execute(
            """
UPDATE cards_cardprice
SET cheapest_card_id = NULL
"""
        )

        logger.info("Setting cheapest prices")
        cursor.execute(
            """
UPDATE cards_cardprice
SET cheapest_card_id = cheapest_price.card_id
FROM (
	SELECT DISTINCT
	price_rank.price_id,
	price_rank.card_id
	FROM cards_card
	JOIN (
		SELECT
		cards_cardprinting.card_id,
		RANK() OVER (
			PARTITION BY cards_cardprinting.card_id
			ORDER BY cards_cardprice.paper_value ASC,
			cards_set.release_date ASC,
			cards_cardprinting.id) rnk,
		cards_cardprice.paper_value,
		cards_cardprice.id price_id
		FROM cards_cardprinting
		JOIN cards_cardprice
		ON cards_cardprice.id = cards_cardprinting.latest_price_id
		JOIN cards_set
		ON cards_set.id = cards_cardprinting.set_id
		WHERE cards_cardprice.paper_value IS NOT NULL
	) price_rank
	ON cards_card.id = price_rank.card_id
	WHERE price_rank.rnk = 1
) cheapest_price
WHERE cards_cardprice.id = cheapest_price.price_id
"""
        )


def update_prices(start_of_week: datetime.date):
    logger.info("Querying DB for most recent prices")
    with connection.cursor() as cursor:
        cursor.execute(
            """
SELECT
card_printing.id,
face_printing.uuid,
latest_price.date
FROM cards_cardprinting card_printing
JOIN cards_cardfaceprinting face_printing
ON face_printing.card_printing_id = card_printing.id
LEFT JOIN cards_cardprice latest_price
ON latest_price.id = card_printing.latest_price_id
"""
        )
        recent_price_map = {
            uuid: (printing_id, most_recent_date)
            for printing_id, uuid, most_recent_date in cursor.fetchall()
        }

    logger.info("Updating prices")
    # We need to check which printings we've already done in case there are two faces
    # and therefore two price rows the same printing and we don't want to duplicate the prices
    updated_printings = set()
    with open(_paths.PRICES_JSON_PATH, "r", encoding="utf8") as prices_file:
        cards = ijson.kvitems(prices_file, "data")
        for uuid, price_data in cards:
            if uuid not in recent_price_map:
                logger.warning("No printing found for %s", uuid)
                continue

            printing_id, latest_price = recent_price_map[uuid]

            if printing_id in updated_printings:
                logger.info("Already updated %s. Skipping...", uuid)
                continue

            logger.info("Updating prices for %s", uuid)
            apply_printing_prices(start_of_week, price_data, printing_id, latest_price)
            updated_printings.add(printing_id)


PAPER_FOIL = (True, True)
MTGO_FOIL = (True, False)
PAPER = (False, True)
MTGO = (False, False)


def apply_printing_prices(
    start_of_week: datetime.date,
    card_data: dict,
    printing_id: int,
    latest_price_date: typing.Optional[datetime.date],
) -> None:
    prices = defaultdict(lambda: defaultdict(list))
    for stock_type, stock_data in card_data.items():
        is_paper = stock_type == "paper"
        # We don't care about different stores, so just the data from every store and average it
        for store_name, store_data in stock_data.items():
            # There have been problems with "cardsphere" having greatly inflated prices over that
            # of the other retailers. Potentially they are using foil prices for non-foil data
            # So we will ignore any data not from the Big 3
            if store_name not in ("cardkingdom", "cardmarket", "tcgplayer"):
                continue

            if store_data.get("currency") != "USD":
                continue

            retail_data = store_data.get("retail", {})
            for foil_type, foil_data in retail_data.items():
                is_foil = foil_type != "normal"
                for price_date_str, price_value in foil_data.items():
                    price_date = datetime.date.fromisoformat(price_date_str)
                    # Round down the nearest week
                    price_date -= datetime.timedelta(days=price_date.weekday())
                    if price_date >= start_of_week:
                        continue

                    if (
                        latest_price_date is not None
                        and price_date <= latest_price_date
                    ):
                        continue

                    prices[price_date][(is_foil, is_paper)].append(price_value)

    new_prices = []
    for price_date, stock_types in prices.items():
        new_price = CardPrice(card_printing_id=printing_id, date=price_date)
        if PAPER in stock_types:
            new_price.paper_value = sum(stock_types[PAPER]) / len(stock_types[PAPER])

        if PAPER_FOIL in stock_types:
            new_price.paper_foil_value = sum(stock_types[PAPER_FOIL]) / len(
                stock_types[PAPER_FOIL]
            )

        if MTGO in stock_types:
            new_price.mtgo_value = sum(stock_types[MTGO]) / len(stock_types[MTGO])

        if MTGO_FOIL in stock_types:
            new_price.mtgo_foil_value = sum(stock_types[MTGO_FOIL]) / len(
                stock_types[MTGO_FOIL]
            )
        new_prices.append(new_price)

    CardPrice.objects.bulk_create(new_prices)


class Command(BaseCommand):
    """
    Command for updating card prices from the MTGJSON price files
    """

    help = (
        "Finds printings that may have had their UID (printing.json_id) changed, "
        "and the prompts the user to fix them."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        # We want to get the average for a weeks prices into a single lump
        # So the latest date that can be considered is the start of this week
        # The data for that week will be lumped into the date of the start of the previous week
        start_of_week = arrow.utcnow().floor("week").date()
        with transaction.atomic():
            if not download_prices(start_of_week):
                return
            update_prices(start_of_week)
            set_latest_prices()
            set_cheapest_prices()
