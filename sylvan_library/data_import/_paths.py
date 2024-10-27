"""
Module for all useful file paths
"""

from os import path


JSON_ZIP_DOWNLOAD_URL = "https://mtgjson.com/api/v5/AllSetFiles.zip"
DATA_FOLDER = path.abspath("data_import/data")
SET_FOLDER = path.join(DATA_FOLDER, "sets")
DOWNLOADS_FOLDER_PATH = path.join(DATA_FOLDER, "downloads")
IMPORT_FOLDER_PATH = path.join(DATA_FOLDER, "import")
META_DOWNLOAD_URL = "https://mtgjson.com/api/v5/Meta.json"
META_JSON_PATH = path.join(DOWNLOADS_FOLDER_PATH, "Meta.json")

JSON_ZIP_PATH = path.join(DATA_FOLDER, "AllSetFiles.zip")
TYPES_DOWNLOAD_URL = "https://mtgjson.com/api/v5/CardTypes.json.zip"
TYPES_ZIP_PATH = path.join(DOWNLOADS_FOLDER_PATH, "CardTypes.json.zip")
TYPES_JSON_PATH = path.join(IMPORT_FOLDER_PATH, "CardTypes.json")

PRICES_ZIP_DOWNLOAD_URL = "https://mtgjson.com/api/v5/AllPrices.json.zip"
PRICES_ZIP_PATH = path.join(DOWNLOADS_FOLDER_PATH, "AllPrices.json.zip")
PRICES_JSON_PATH = path.join(IMPORT_FOLDER_PATH, "AllPrices.json")

LANGUAGE_JSON_PATH = path.join(DATA_FOLDER, "languages.json")
COLOUR_JSON_PATH = path.join(DATA_FOLDER, "colours.json")
RARITY_JSON_PATH = path.join(DATA_FOLDER, "rarities.json")
FORMAT_JSON_PATH = path.join(DATA_FOLDER, "formats.json")
FRAME_EFFECT_JSON_PATH = path.join(DATA_FOLDER, "frame_effects.json")
