"""
Django shell commands for data_import
"""

import datetime
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Generator, Dict, Any, List, Optional

import requests

from cards.models.sets import Set
from data_import import _paths

logger = logging.getLogger("django")


SET_CODES_TO_SKIP = [
    "AAFR",
    "AMH2",
    "ASTX",
    "Alchemy: Innistrad",
    "DA1",
    "FMB1",
    "HTR",
    "HTR16",
    "HTR17",
    "HTR18",
    "HTR19",
    "HTR20",
    "MB1",
    "MZNR",
    "OC21",
    "PAGL",
    "PBOOK",
    "PCTB",
    "PDCI",
    "PDWA",
    "PHED",
    "PHJ",
    "PLGS",
    "PLIST",
    "PPOD",
    "PRES",
    "PWCQ",
    "PWP09",
    "PWP10",
    "PWP11",
    "PWP12",
    "PWP21",
    "UPLIST",
    "YMID",
]


class SimpleSet:
    def __init__(
        self, set_code: str, name: str, path: str, release_date: datetime.date
    ):
        self.set_code = set_code
        self.name = name
        self.path = path
        self.release_date = release_date


def get_all_set_data(
    set_codes: Optional[List[str]] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Gets set data from the sets directory and returns each one as a parsed dict
    :return: The set data as a dict
    """
    set_list: List[SimpleSet] = []

    for set_file_path in [
        os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)
    ]:
        if not set_file_path.endswith(".json"):
            continue

        set_code = os.path.basename(set_file_path).split(".")[0].strip("_")
        if set_codes and set_code not in set_codes:
            continue

        set_obj = parse_set(set_file_path)
        if set_obj is not None:
            set_list.append(set_obj)

    if not set_codes:
        check_for_duplicate_sets(set_list)
        check_for_setcode_mismatches(set_list)
        check_for_missing_sets(set_list)
        check_for_name_duplicates(set_list)

    set_list.sort(key=lambda s: s.release_date)
    for card_set in set_list:
        with open(card_set.path, "r", encoding="utf8") as set_file:
            set_data = json.load(set_file)
        yield set_data.get("data")


def parse_set(set_file_path: str) -> Optional[SimpleSet]:
    with open(set_file_path, "r", encoding="utf8") as set_file:
        set_data = json.load(set_file).get("data")

    set_code = set_data["code"]
    set_name = set_data["name"]
    if (
        set_data.get("isPreview")
        or set_data.get("isPartialPreview")
        or set_name.endswith("Minigames")
        or set_name.endswith("Art Series")
        or set_code in SET_CODES_TO_SKIP
    ):
        return None

    return SimpleSet(
        set_code=set_code,
        name=set_name,
        path=set_file_path,
        release_date=set_data.get("releaseDate", str(datetime.date.max)),
    )


def check_for_duplicate_sets(set_list: List[SimpleSet]):
    name_dict = defaultdict(list)
    for set_obj in set_list:
        name_dict[set_obj.name].append(set_obj.set_code)

    name_dict = {
        set_name: set_codes
        for set_name, set_codes in name_dict.items()
        if len(set_codes) > 1
    }
    if name_dict:
        raise Exception(f"The following sets have duplicate names: {name_dict}")


def check_for_setcode_mismatches(set_list: List[SimpleSet]):
    for simple_set in set_list:
        try:
            actual_set = Set.objects.get(name=simple_set.name)
            if actual_set.code != simple_set.set_code:
                raise Exception(
                    f'Existing set "{actual_set}" has setcode {actual_set.code} '
                    f"but new set with same name has setcode {simple_set.set_code}"
                )
        except Set.DoesNotExist:
            continue


def check_for_missing_sets(set_list: List[SimpleSet]) -> None:
    for set_obj in Set.objects.all():
        if set_obj.type == "token":
            continue
        matching_simple_sets = [s for s in set_list if s.name == set_obj.name]
        if len(matching_simple_sets) == 0:
            raise Exception(
                f'Set "{set_obj.name}" ({set_obj.code}) doesn\'t have any matching set files.'
            )


def check_for_name_duplicates(set_list: List[SimpleSet]):
    set_names = set()
    for simple_set in set_list:
        if simple_set.name in set_names:
            raise Exception(f"Duplicate set {simple_set.name}")
        set_names.add(simple_set.name)


def pretty_print_json_file(set_file_path: str) -> None:
    """
    Reads, pretty prints, and writes out the chosen file back into itself
    :param set_file_path:
    :return:
    """
    with open(set_file_path, "r", encoding="utf8") as set_file:
        set_data = json.load(set_file)

    with open(set_file_path, "w", encoding="utf8") as set_file:
        json.dump(set_data, set_file, indent=2)


def download_file(url: str, destination_path: str, timeout_seconds: int = 180) -> None:
    """
    Downloads a file from the given URL to the given destination
    :param url: The download URL
    :param destination_path: The path for where the file should go
    :param timeout_seconds: The number of seconds to wait for the request before raising an error
    """
    logger.info("Downloading %s", url)
    response = requests.get(url, stream=True, timeout=timeout_seconds)
    total_length = response.headers.get("content-length")
    logger.info(
        "Writing json data to file %s: %s bytes", destination_path, total_length
    )
    with open(destination_path, "wb") as output:
        if total_length is None:  # no content length header
            output.write(response.content)
        else:
            data_length = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                data_length += len(data)
                output.write(data)
                print_progress(data_length / total_length)
    sys.stdout.write("\n")


def print_progress(progress: float) -> None:
    """
    Print the current progress to stdout
    The current stdout line will be overwritten
    :param progress: The progress from 0 to 1
    """
    progress = max(min(progress, 1), 0)
    stars = 50
    done = int(stars * progress)
    sys.stdout.write(f'\r[{"=" * done}{" " * (stars - done)}]')
    sys.stdout.flush()
