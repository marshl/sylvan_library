"""
Django sell commands for data_import
"""
import json
import os
from datetime import date
from typing import Generator, Dict, Any, List, Optional

from data_import import _paths


def get_all_set_data(
    set_codes: Optional[List[str]]
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
        if set_codes and set_code not in set_codes or set_code in ("PPRE", "PREL"):
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
