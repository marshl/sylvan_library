"""
Module for the update_printing_uids command
"""
import datetime
import logging
import queue
import threading
import time
import typing
import zipfile
from typing import Any

import ijson
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

import _paths
from cards.models import CardPrice
from cards.models import CardPrinting, CardFacePrinting
from data_import.management.commands import get_all_set_data

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Command for updating the UIDs of card printings that changed in the json
    """

    help = (
        "Finds printings that may have had their UID (printing.json_id) changed, "
        "and the prompts the user to fix them."
    )

    def handle(self, *args: Any, **options: Any) -> None:

        # self.download_prices()

        price_update_queue = queue.Queue()

        for i in range(0, 10):
            logger.info("Starting thread %s", i)
            thread = ImageDownloadThread(i, price_update_queue)
            thread.setDaemon(True)
            thread.start()

        # start = time.time()
        update_count = 0
        with open(_paths.PRICES_JSON_PATH, "r", encoding="utf8") as prices_file:
            cards = ijson.kvitems(prices_file, "data")
            for uuid, price_data in cards:
                # update_card_prices(uuid, price_data)
                # update_count += 1
                # if update_count % 100 == 0:
                #     print(
                #     "Updated {}: {} per second".format(
                #         update_count, update_count / (time.time() - start)
                #     )
                # )
                update_count += 1
                price_update_queue.put((uuid, price_data))
                if update_count % 1000 == 0:
                    while price_update_queue.qsize() > 1000:
                        logger.info("Queue is full, waiting...")
                        time.sleep(0.1)

        price_update_queue.join()

    def download_prices(self):
        # download_file(_paths.PRICES_ZIP_DOWNLOAD_URL, _paths.PRICES_ZIP_PATH)
        prices_zip_file = zipfile.ZipFile(_paths.PRICES_ZIP_PATH)
        prices_zip_file.extractall(_paths.IMPORT_FOLDER_PATH)
        # if settings.DEBUG:
        #     pretty_print_json_file(_paths.PRICES_JSON_PATH)


class ImageDownloadThread(threading.Thread):
    """
    The thread object for downloading a card image
    """

    def __init__(self, thread_number: int, update_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.thread_number = thread_number
        self.update_queue = update_queue

    def run(self):
        while True:
            (printing_uid, price_data) = self.update_queue.get()
            update_card_prices(printing_uid, card_data=price_data)
            self.update_queue.task_done()


def update_card_prices(uuid: str, card_data: dict) -> None:
    try:
        # face = CardFacePrinting.objects.get(uuid=uuid)
        # card_printing = face.card_printing
        card_printing = CardPrinting.objects.get(face_printings__uuid=uuid)
    except CardPrinting.DoesNotExist:
        logger.warning(f"Could not find card {uuid}")
        return

    today = datetime.datetime.utcnow().date()

    latest_price_for_card: CardPrice = CardPrice.objects.filter(
        printing=card_printing
    ).order_by("-date").first()
    if latest_price_for_card:
        latest_price_date = latest_price_for_card.date
        if latest_price_date >= today:
            return
    else:
        latest_price_date = None

    new_prices = []

    logger.info("Creating prices for %s", card_printing)

    for stock_type, stock_data in card_data.items():
        for store_name, store_data in stock_data.items():
            currency = store_data.get("currency")
            for retail_type, retail_data in [
                ("retail", store_data.get("retail", {})),
                ("buylist", store_data.get("buylist", {})),
            ]:
                for foil_type, foil_data in retail_data.items():
                    is_foil = foil_type == "foil"
                    for price_date_str, price_value in foil_data.items():
                        price_date = time.strptime(price_date_str, '%Y-%m-%d')
                        if price_date.date().weekday() != 0:
                            continue

                        if latest_price_date and price_date <= str(latest_price_date):
                            continue
                        new_prices.append(
                            CardPrice(
                                printing_id=card_printing.id,
                                price=price_value,
                                date=price_date,
                                stock_type=stock_type,
                                foil=is_foil,
                                currency=currency,
                                store=store_name,
                                retail_type=retail_type,
                            )
                        )

    CardPrice.objects.bulk_create(new_prices)

    # return created, skipped


"""
{
    "mtgo": {
        "cardhoarder": {
            "currency": "USD",
            "retail": {
                "foil": {
                    "2020-10-08": Decimal("0.01"),
                    "2020-10-09": Decimal("0.01"),
                    "2020-10-10": Decimal("0.01"),
                    "2020-10-11": Decimal("0.01"),
                    "2020-10-12": Decimal("0.01"),
                    "2020-10-13": Decimal("0.01"),
                    "2020-10-14": Decimal("0.01"),
                    "2020-10-15": Decimal("0.01"),
                    "2020-10-16": Decimal("0.01"),
                    "2020-10-17": Decimal("0.01"),
                    "2020-10-18": Decimal("0.01"),
                    "2020-10-19": Decimal("0.01"),
                    "2020-10-20": Decimal("0.01"),
                    "2020-10-21": Decimal("0.01"),
                    "2020-10-22": Decimal("0.01"),
                    "2020-10-23": Decimal("0.01"),
                    "2020-10-24": Decimal("0.02"),
                    "2020-10-25": Decimal("0.02"),
                    "2020-10-26": Decimal("0.02"),
                    "2020-10-27": Decimal("0.02"),
                    "2020-10-28": Decimal("0.02"),
                    "2020-10-29": Decimal("0.02"),
                    "2020-10-30": Decimal("0.02"),
                    "2020-10-31": Decimal("0.02"),
                    "2020-11-01": Decimal("0.02"),
                    "2020-11-02": Decimal("0.02"),
                    "2020-11-03": Decimal("0.02"),
                    "2020-11-04": Decimal("0.02"),
                    "2020-11-05": Decimal("0.02"),
                    "2020-11-06": Decimal("0.02"),
                    "2020-12-15": Decimal("0.02"),
                    "2020-12-16": Decimal("0.02"),
                    "2020-12-17": Decimal("0.02"),
                    "2020-12-18": Decimal("0.02"),
                    "2020-12-19": Decimal("0.02"),
                    "2020-12-20": Decimal("0.02"),
                    "2021-01-04": Decimal("0.02"),
                    "2021-01-05": Decimal("0.02"),
                    "2021-01-06": Decimal("0.02"),
                    "2021-01-08": Decimal("0.02"),
                },
                "normal": {
                    "2020-10-08": Decimal("0.02"),
                    "2020-10-09": Decimal("0.02"),
                    "2020-10-10": Decimal("0.02"),
                    "2020-10-11": Decimal("0.02"),
                    "2020-10-12": Decimal("0.02"),
                    "2020-10-13": Decimal("0.02"),
                    "2020-10-14": Decimal("0.02"),
                    "2020-10-15": Decimal("0.02"),
                    "2020-10-16": Decimal("0.02"),
                    "2020-10-17": Decimal("0.02"),
                    "2020-10-18": Decimal("0.02"),
                    "2020-10-19": Decimal("0.02"),
                    "2020-10-20": Decimal("0.02"),
                    "2020-10-21": Decimal("0.02"),
                    "2020-10-22": Decimal("0.02"),
                    "2020-10-23": Decimal("0.02"),
                    "2020-10-24": Decimal("0.02"),
                    "2020-10-25": Decimal("0.02"),
                    "2020-10-26": Decimal("0.02"),
                    "2020-10-27": Decimal("0.02"),
                    "2020-10-28": Decimal("0.02"),
                    "2020-10-29": Decimal("0.02"),
                    "2020-10-30": Decimal("0.02"),
                    "2020-10-31": Decimal("0.02"),
                    "2020-11-01": Decimal("0.02"),
                    "2020-11-02": Decimal("0.02"),
                    "2020-11-03": Decimal("0.02"),
                    "2020-11-04": Decimal("0.02"),
                    "2020-11-05": Decimal("0.02"),
                    "2020-11-06": Decimal("0.02"),
                    "2020-12-15": Decimal("0.02"),
                    "2020-12-16": Decimal("0.02"),
                    "2020-12-17": Decimal("0.02"),
                    "2020-12-18": Decimal("0.02"),
                    "2020-12-19": Decimal("0.02"),
                    "2020-12-20": Decimal("0.02"),
                    "2021-01-04": Decimal("0.02"),
                    "2021-01-05": Decimal("0.02"),
                    "2021-01-06": Decimal("0.02"),
                    "2021-01-08": Decimal("0.02"),
                },
            },
        }
    },
    "paper": {
        "cardkingdom": {
            "buylist": {
                "foil": {
                    "2020-10-08": Decimal("0.06"),
                    "2020-10-09": Decimal("0.06"),
                    "2020-10-10": Decimal("0.06"),
                    "2020-10-11": Decimal("0.06"),
                    "2020-10-12": Decimal("0.06"),
                    "2020-10-13": Decimal("0.06"),
                    "2020-10-14": Decimal("0.06"),
                    "2020-10-15": Decimal("0.06"),
                    "2020-10-16": Decimal("0.06"),
                    "2020-10-17": Decimal("0.08"),
                    "2020-10-18": Decimal("0.08"),
                    "2020-10-19": Decimal("0.08"),
                    "2020-10-20": Decimal("0.08"),
                    "2020-10-21": Decimal("0.06"),
                    "2020-10-22": Decimal("0.06"),
                    "2020-10-23": Decimal("0.06"),
                    "2020-10-24": Decimal("0.06"),
                    "2020-10-25": Decimal("0.06"),
                    "2020-10-26": Decimal("0.06"),
                    "2020-10-27": Decimal("0.06"),
                    "2020-10-28": Decimal("0.06"),
                    "2020-10-29": Decimal("0.1"),
                    "2020-10-30": Decimal("0.1"),
                    "2020-10-31": Decimal("0.1"),
                    "2020-11-01": Decimal("0.13"),
                    "2020-11-02": Decimal("0.13"),
                    "2020-11-03": Decimal("0.13"),
                    "2020-11-04": Decimal("0.13"),
                    "2020-11-05": Decimal("0.13"),
                    "2020-11-06": Decimal("0.13"),
                    "2020-12-15": Decimal("0.16"),
                    "2020-12-16": Decimal("0.16"),
                    "2020-12-17": Decimal("0.16"),
                    "2020-12-18": Decimal("0.16"),
                    "2020-12-19": Decimal("0.16"),
                    "2020-12-20": Decimal("0.16"),
                    "2021-01-04": Decimal("0.16"),
                    "2021-01-05": Decimal("0.16"),
                    "2021-01-06": Decimal("0.16"),
                    "2021-01-08": Decimal("0.16"),
                },
                "normal": {
                    "2020-10-08": Decimal("0.05"),
                    "2020-10-09": Decimal("0.05"),
                    "2020-10-10": Decimal("0.05"),
                    "2020-10-11": Decimal("0.05"),
                    "2020-10-12": Decimal("0.05"),
                    "2020-10-13": Decimal("0.05"),
                    "2020-10-14": Decimal("0.05"),
                    "2020-10-15": Decimal("0.05"),
                    "2020-10-16": Decimal("0.05"),
                    "2020-10-17": Decimal("0.05"),
                    "2020-10-18": Decimal("0.05"),
                    "2020-10-19": Decimal("0.05"),
                    "2020-10-20": Decimal("0.05"),
                    "2020-10-21": Decimal("0.05"),
                    "2020-10-22": Decimal("0.05"),
                    "2020-10-23": Decimal("0.05"),
                    "2020-10-24": Decimal("0.05"),
                    "2020-10-25": Decimal("0.05"),
                    "2020-10-26": Decimal("0.05"),
                    "2020-10-27": Decimal("0.05"),
                    "2020-10-28": Decimal("0.05"),
                    "2020-10-29": Decimal("0.05"),
                    "2020-10-30": Decimal("0.05"),
                    "2020-10-31": Decimal("0.05"),
                    "2020-11-01": Decimal("0.05"),
                    "2020-11-02": Decimal("0.05"),
                    "2020-11-03": Decimal("0.05"),
                    "2020-11-04": Decimal("0.05"),
                    "2020-11-05": Decimal("0.05"),
                    "2020-11-06": Decimal("0.05"),
                    "2020-12-15": Decimal("0.05"),
                    "2020-12-16": Decimal("0.05"),
                    "2020-12-17": Decimal("0.05"),
                    "2020-12-18": Decimal("0.05"),
                    "2020-12-19": Decimal("0.05"),
                    "2020-12-20": Decimal("0.05"),
                    "2021-01-04": Decimal("0.05"),
                    "2021-01-05": Decimal("0.05"),
                    "2021-01-06": Decimal("0.05"),
                    "2021-01-08": Decimal("0.05"),
                },
            },
            "currency": "USD",
            "retail": {
                "foil": {
                    "2020-10-08": Decimal("0.35"),
                    "2020-10-09": Decimal("0.35"),
                    "2020-10-10": Decimal("0.35"),
                    "2020-10-11": Decimal("0.35"),
                    "2020-10-12": Decimal("0.35"),
                    "2020-10-13": Decimal("0.35"),
                    "2020-10-14": Decimal("0.35"),
                    "2020-10-15": Decimal("0.35"),
                    "2020-10-16": Decimal("0.35"),
                    "2020-10-17": Decimal("0.39"),
                    "2020-10-18": Decimal("0.39"),
                    "2020-10-19": Decimal("0.39"),
                    "2020-10-20": Decimal("0.39"),
                    "2020-10-21": Decimal("0.39"),
                    "2020-10-22": Decimal("0.39"),
                    "2020-10-23": Decimal("0.39"),
                    "2020-10-24": Decimal("0.39"),
                    "2020-10-25": Decimal("0.39"),
                    "2020-10-26": Decimal("0.39"),
                    "2020-10-27": Decimal("0.39"),
                    "2020-10-28": Decimal("0.39"),
                    "2020-10-29": Decimal("0.39"),
                    "2020-10-30": Decimal("0.39"),
                    "2020-10-31": Decimal("0.39"),
                    "2020-11-01": Decimal("0.49"),
                    "2020-11-02": Decimal("0.49"),
                    "2020-11-03": Decimal("0.49"),
                    "2020-11-04": Decimal("0.49"),
                    "2020-11-05": Decimal("0.49"),
                    "2020-11-06": Decimal("0.49"),
                    "2020-12-15": Decimal("0.79"),
                    "2020-12-16": Decimal("0.79"),
                    "2020-12-17": Decimal("0.79"),
                    "2020-12-18": Decimal("0.79"),
                    "2020-12-19": Decimal("0.79"),
                    "2020-12-20": Decimal("0.79"),
                    "2021-01-04": Decimal("0.79"),
                    "2021-01-05": Decimal("0.79"),
                    "2021-01-06": Decimal("0.79"),
                    "2021-01-08": Decimal("0.79"),
                },
                "normal": {
                    "2020-10-08": Decimal("0.25"),
                    "2020-10-09": Decimal("0.25"),
                    "2020-10-10": Decimal("0.25"),
                    "2020-10-11": Decimal("0.25"),
                    "2020-10-12": Decimal("0.25"),
                    "2020-10-13": Decimal("0.25"),
                    "2020-10-14": Decimal("0.25"),
                    "2020-10-15": Decimal("0.25"),
                    "2020-10-16": Decimal("0.25"),
                    "2020-10-17": Decimal("0.25"),
                    "2020-10-18": Decimal("0.25"),
                    "2020-10-19": Decimal("0.25"),
                    "2020-10-20": Decimal("0.25"),
                    "2020-10-21": Decimal("0.25"),
                    "2020-10-22": Decimal("0.25"),
                    "2020-10-23": Decimal("0.25"),
                    "2020-10-24": Decimal("0.25"),
                    "2020-10-25": Decimal("0.25"),
                    "2020-10-26": Decimal("0.25"),
                    "2020-10-27": Decimal("0.25"),
                    "2020-10-28": Decimal("0.25"),
                    "2020-10-29": Decimal("0.25"),
                    "2020-10-30": Decimal("0.25"),
                    "2020-10-31": Decimal("0.25"),
                    "2020-11-01": Decimal("0.25"),
                    "2020-11-02": Decimal("0.25"),
                    "2020-11-03": Decimal("0.25"),
                    "2020-11-04": Decimal("0.25"),
                    "2020-11-05": Decimal("0.25"),
                    "2020-11-06": Decimal("0.25"),
                    "2020-12-15": Decimal("0.25"),
                    "2020-12-16": Decimal("0.25"),
                    "2020-12-17": Decimal("0.25"),
                    "2020-12-18": Decimal("0.25"),
                    "2020-12-19": Decimal("0.25"),
                    "2020-12-20": Decimal("0.25"),
                    "2021-01-04": Decimal("0.25"),
                    "2021-01-05": Decimal("0.25"),
                    "2021-01-06": Decimal("0.25"),
                    "2021-01-08": Decimal("0.25"),
                },
            },
        },
        "cardmarket": {
            "currency": "EUR",
            "retail": {
                "foil": {
                    "2020-10-08": Decimal("0.5"),
                    "2020-10-09": Decimal("0.5"),
                    "2020-10-10": Decimal("0.5"),
                    "2020-10-11": Decimal("0.5"),
                    "2020-10-12": Decimal("0.5"),
                    "2020-10-13": Decimal("0.5"),
                    "2020-10-14": Decimal("0.5"),
                    "2020-10-15": Decimal("0.5"),
                    "2020-10-16": Decimal("0.5"),
                    "2020-10-17": Decimal("0.5"),
                    "2020-10-18": Decimal("0.5"),
                    "2020-10-19": Decimal("0.5"),
                    "2020-10-20": Decimal("0.5"),
                    "2020-10-21": Decimal("0.5"),
                    "2020-10-22": Decimal("0.5"),
                    "2020-10-23": Decimal("0.5"),
                    "2020-10-24": Decimal("0.5"),
                    "2020-10-25": Decimal("0.5"),
                    "2020-10-26": Decimal("0.5"),
                    "2020-10-27": Decimal("0.5"),
                    "2020-10-28": Decimal("0.5"),
                    "2020-10-29": Decimal("0.5"),
                    "2020-10-30": Decimal("0.5"),
                    "2020-10-31": Decimal("0.5"),
                    "2020-11-01": Decimal("0.5"),
                    "2020-11-02": Decimal("0.5"),
                    "2020-11-03": Decimal("0.5"),
                    "2020-11-04": Decimal("0.39"),
                    "2020-11-05": Decimal("0.39"),
                    "2020-11-06": Decimal("0.39"),
                    "2020-12-15": Decimal("0.2"),
                    "2020-12-16": Decimal("0.2"),
                    "2020-12-17": Decimal("0.2"),
                    "2020-12-18": Decimal("0.2"),
                    "2020-12-19": Decimal("0.2"),
                    "2020-12-20": Decimal("0.2"),
                    "2021-01-04": Decimal("0.2"),
                    "2021-01-05": Decimal("0.2"),
                    "2021-01-06": Decimal("0.2"),
                    "2021-01-08": Decimal("0.2"),
                },
                "normal": {
                    "2020-10-08": Decimal("0.15"),
                    "2020-10-09": Decimal("0.15"),
                    "2020-10-10": Decimal("0.15"),
                    "2020-10-11": Decimal("0.25"),
                    "2020-10-12": Decimal("0.25"),
                    "2020-10-13": Decimal("0.25"),
                    "2020-10-14": Decimal("0.08"),
                    "2020-10-15": Decimal("0.55"),
                    "2020-10-16": Decimal("0.1"),
                    "2020-10-17": Decimal("0.03"),
                    "2020-10-18": Decimal("0.03"),
                    "2020-10-19": Decimal("0.15"),
                    "2020-10-20": Decimal("0.15"),
                    "2020-10-21": Decimal("0.49"),
                    "2020-10-22": Decimal("0.02"),
                    "2020-10-23": Decimal("0.02"),
                    "2020-10-24": Decimal("0.02"),
                    "2020-10-25": Decimal("0.04"),
                    "2020-10-26": Decimal("0.04"),
                    "2020-10-27": Decimal("0.04"),
                    "2020-10-28": Decimal("0.2"),
                    "2020-10-29": Decimal("0.2"),
                    "2020-10-30": Decimal("0.02"),
                    "2020-10-31": Decimal("0.12"),
                    "2020-11-01": Decimal("0.1"),
                    "2020-11-02": Decimal("0.1"),
                    "2020-11-03": Decimal("0.1"),
                    "2020-11-04": Decimal("0.05"),
                    "2020-11-05": Decimal("0.02"),
                    "2020-11-06": Decimal("0.13"),
                    "2020-12-15": Decimal("0.25"),
                    "2020-12-16": Decimal("0.25"),
                    "2020-12-17": Decimal("0.25"),
                    "2020-12-18": Decimal("0.12"),
                    "2020-12-19": Decimal("0.12"),
                    "2020-12-20": Decimal("0.12"),
                    "2021-01-04": Decimal("0.05"),
                    "2021-01-05": Decimal("0.02"),
                    "2021-01-06": Decimal("0.02"),
                    "2021-01-08": Decimal("0.02"),
                },
            },
        },
        "tcgplayer": {
            "buylist": {
                "foil": {
                    "2020-10-08": Decimal("0.01"),
                    "2020-10-09": Decimal("0.01"),
                    "2020-10-10": Decimal("0.05"),
                    "2020-10-11": Decimal("0.05"),
                    "2020-10-12": Decimal("0.05"),
                    "2020-10-13": Decimal("0.01"),
                    "2020-10-14": Decimal("0.02"),
                    "2020-10-15": Decimal("0.03"),
                    "2020-10-16": Decimal("0.03"),
                    "2020-10-17": Decimal("0.02"),
                    "2020-10-18": Decimal("0.02"),
                    "2020-10-19": Decimal("0.03"),
                    "2020-10-20": Decimal("0.01"),
                    "2020-10-21": Decimal("0.01"),
                    "2020-10-22": Decimal("0.01"),
                    "2020-10-23": Decimal("0.01"),
                    "2020-10-24": Decimal("0.01"),
                    "2020-10-25": Decimal("0.01"),
                    "2020-10-26": Decimal("0.01"),
                    "2020-10-27": Decimal("0.01"),
                    "2020-10-28": Decimal("0.01"),
                    "2020-10-29": Decimal("0.01"),
                    "2020-10-30": Decimal("0.01"),
                    "2020-10-31": Decimal("0.01"),
                    "2020-11-01": Decimal("0.01"),
                    "2020-11-02": Decimal("0.01"),
                    "2020-11-03": Decimal("0.01"),
                    "2020-11-04": Decimal("0.01"),
                    "2020-11-05": Decimal("0.02"),
                    "2020-11-06": Decimal("0.02"),
                    "2020-12-15": Decimal("0.06"),
                    "2020-12-16": Decimal("0.06"),
                    "2020-12-17": Decimal("0.06"),
                    "2020-12-18": Decimal("0.06"),
                    "2020-12-19": Decimal("0.06"),
                    "2020-12-20": Decimal("0.06"),
                    "2021-01-04": Decimal("0.05"),
                    "2021-01-05": Decimal("0.06"),
                    "2021-01-06": Decimal("0.06"),
                    "2021-01-08": Decimal("0.09"),
                }
            },
            "currency": "USD",
            "retail": {
                "foil": {
                    "2020-10-08": Decimal("0.53"),
                    "2020-10-09": Decimal("0.53"),
                    "2020-10-10": Decimal("0.53"),
                    "2020-10-11": Decimal("0.53"),
                    "2020-10-12": Decimal("0.53"),
                    "2020-10-13": Decimal("0.53"),
                    "2020-10-14": Decimal("0.53"),
                    "2020-10-15": Decimal("0.53"),
                    "2020-10-16": Decimal("0.53"),
                    "2020-10-17": Decimal("0.53"),
                    "2020-10-18": Decimal("0.53"),
                    "2020-10-19": Decimal("0.53"),
                    "2020-10-20": Decimal("0.53"),
                    "2020-10-21": Decimal("0.53"),
                    "2020-10-22": Decimal("0.53"),
                    "2020-10-23": Decimal("0.53"),
                    "2020-10-24": Decimal("0.53"),
                    "2020-10-25": Decimal("0.52"),
                    "2020-10-26": Decimal("0.52"),
                    "2020-10-27": Decimal("0.52"),
                    "2020-10-28": Decimal("0.52"),
                    "2020-10-29": Decimal("0.52"),
                    "2020-10-30": Decimal("0.52"),
                    "2020-10-31": Decimal("0.52"),
                    "2020-11-01": Decimal("0.51"),
                    "2020-11-02": Decimal("0.51"),
                    "2020-11-03": Decimal("0.51"),
                    "2020-11-04": Decimal("0.51"),
                    "2020-11-05": Decimal("0.51"),
                    "2020-11-06": Decimal("0.51"),
                    "2020-12-15": Decimal("0.55"),
                    "2020-12-16": Decimal("0.55"),
                    "2020-12-17": Decimal("0.55"),
                    "2020-12-18": Decimal("0.55"),
                    "2020-12-19": Decimal("0.55"),
                    "2020-12-20": Decimal("0.55"),
                    "2021-01-04": Decimal("0.55"),
                    "2021-01-05": Decimal("0.55"),
                    "2021-01-06": Decimal("0.55"),
                    "2021-01-08": Decimal("0.55"),
                },
                "normal": {
                    "2020-10-08": Decimal("0.17"),
                    "2020-10-09": Decimal("0.17"),
                    "2020-10-10": Decimal("0.17"),
                    "2020-10-11": Decimal("0.17"),
                    "2020-10-12": Decimal("0.17"),
                    "2020-10-13": Decimal("0.17"),
                    "2020-10-14": Decimal("0.17"),
                    "2020-10-15": Decimal("0.17"),
                    "2020-10-16": Decimal("0.16"),
                    "2020-10-17": Decimal("0.16"),
                    "2020-10-18": Decimal("0.16"),
                    "2020-10-19": Decimal("0.16"),
                    "2020-10-20": Decimal("0.17"),
                    "2020-10-21": Decimal("0.17"),
                    "2020-10-22": Decimal("0.17"),
                    "2020-10-23": Decimal("0.17"),
                    "2020-10-24": Decimal("0.17"),
                    "2020-10-25": Decimal("0.17"),
                    "2020-10-26": Decimal("0.17"),
                    "2020-10-27": Decimal("0.17"),
                    "2020-10-28": Decimal("0.17"),
                    "2020-10-29": Decimal("0.17"),
                    "2020-10-30": Decimal("0.17"),
                    "2020-10-31": Decimal("0.17"),
                    "2020-11-01": Decimal("0.17"),
                    "2020-11-02": Decimal("0.17"),
                    "2020-11-03": Decimal("0.17"),
                    "2020-11-04": Decimal("0.17"),
                    "2020-11-05": Decimal("0.17"),
                    "2020-11-06": Decimal("0.17"),
                    "2020-12-15": Decimal("0.17"),
                    "2020-12-16": Decimal("0.17"),
                    "2020-12-17": Decimal("0.17"),
                    "2020-12-18": Decimal("0.17"),
                    "2020-12-19": Decimal("0.17"),
                    "2020-12-20": Decimal("0.17"),
                    "2021-01-04": Decimal("0.17"),
                    "2021-01-05": Decimal("0.17"),
                    "2021-01-06": Decimal("0.17"),
                    "2021-01-08": Decimal("0.17"),
                },
            },
        },
    },
}
"""
