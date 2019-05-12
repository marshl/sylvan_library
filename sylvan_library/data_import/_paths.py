"""
Module for all useful file paths
"""
from os import path

JSON_ZIP_DOWNLOAD_URL = "https://mtgjson.com/v4/json/AllSetFiles.zip"
DATA_FOLDER = path.abspath("data_import/data")
SET_FOLDER = path.join(DATA_FOLDER, "sets")
JSON_ZIP_PATH = path.join(DATA_FOLDER, "AllSetFiles.zip")

LANGUAGE_JSON_PATH = path.join(DATA_FOLDER, "languages.json")
COLOUR_JSON_PATH = path.join(DATA_FOLDER, "colours.json")
RARITY_JSON_PATH = path.join(DATA_FOLDER, "rarities.json")
FORMAT_JSON_PATH = path.join(DATA_FOLDER, "formats.json")
