import os
import json
from typing import Generator

import _paths


def get_all_set_data() -> Generator[dict]:
    """
    Gets set data from the sets directory and returns each one as a parsed dict
    :return: The set data as a dict
    """

    for set_file_path in [
        os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)
    ]:
        if not set_file_path.endswith(".json"):
            continue

        with open(set_file_path, "r", encoding="utf8") as set_file:
            set_data = json.load(set_file, encoding="utf8")
            yield set_data
