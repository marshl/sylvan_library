"""
Django sell commands for data_import
"""
import json
import logging
import os
import sys
from datetime import date
from typing import Generator, Dict, Any, List, Optional

import requests

from data_import import _paths

logger = logging.getLogger("django")


def get_all_set_data(
    set_codes: Optional[List[str]] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Gets set data from the sets directory and returns each one as a parsed dict
    :return: The set data as a dict
    """

    set_list: List[Dict[str, Any]] = []

    for set_file_path in [
        os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)
    ]:
        if not set_file_path.endswith(".json"):
            continue

        set_code = os.path.basename(set_file_path).split(".")[0].strip("_")
        if set_codes and set_code not in set_codes or set_code in ("MZNR",):
            continue

        with open(set_file_path, "r", encoding="utf8") as set_file:
            set_data = json.load(set_file, encoding="utf8").get("data")

        if set_data.get("isPreview") or set_data.get("isPartialPreview"):
            continue
        set_list.append(
            {"path": set_file_path, "date": set_data.get("releaseDate", str(date.max))}
        )

    set_list.sort(key=lambda s: s["date"])
    for card_set in set_list:
        with open(card_set["path"], "r", encoding="utf8") as set_file:
            set_data = json.load(set_file, encoding="utf8")
        yield set_data.get("data")


def pretty_print_json_file(set_file_path: str) -> None:
    with open(set_file_path, "r", encoding="utf8") as set_file:
        set_data = json.load(set_file, encoding="utf8")

    with open(set_file_path, "w", encoding="utf8") as set_file:
        json.dump(set_data, set_file, indent=2)


def download_file(url: str, destination_path: str):
    logger.info("Downloading %s", url)
    response = requests.get(url, stream=True)
    total_length = response.headers.get("content-length")
    logger.info(
        "Writing json data to file %s: %s bytes", destination_path, total_length
    )
    with open(destination_path, "wb") as output:
        if total_length is None:  # no content length header
            output.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                output.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" % ("=" * done, " " * (50 - done)))
                sys.stdout.flush()
