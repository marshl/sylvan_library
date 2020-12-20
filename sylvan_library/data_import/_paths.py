"""
Module for all useful file paths
"""
from os import path

JSON_ZIP_DOWNLOAD_URL = "https://mtgjson.com/api/v5/AllSetFiles.zip"
DATA_FOLDER = path.abspath("data_import/data")
SET_FOLDER = path.join(DATA_FOLDER, "sets")
DOWNLOADS_FOLDER_PATH = path.join(DATA_FOLDER, "downloads")

JSON_ZIP_PATH = path.join(DATA_FOLDER, "AllSetFiles.zip")
TYPES_DOWNLOAD_URL = "https://mtgjson.com/api/v5/CardTypes.json.zip"
TYPES_ZIP_PATH = path.join(DOWNLOADS_FOLDER_PATH, "CardTypes.json.zip")
TYPES_JSON_PATH = path.join(DOWNLOADS_FOLDER_PATH, "CardTypes.json")

ATOMIC_CARDS_DOWNLOAD_URL = "https://mtgjson.com/api/v5/AtomicCards.json.zip"
ATOMIC_CARDS_FOLDER = path.join(DATA_FOLDER, "cards")
ATOMIC_CARDS_ZIP_PATH = path.join(ATOMIC_CARDS_FOLDER, "AtomicCards.json.zip")
ATOMIC_CARDS_PATH = path.join(ATOMIC_CARDS_FOLDER, "AtomicCards.json")

LANGUAGE_JSON_PATH = path.join(DATA_FOLDER, "languages.json")
COLOUR_JSON_PATH = path.join(DATA_FOLDER, "colours.json")
RARITY_JSON_PATH = path.join(DATA_FOLDER, "rarities.json")
FORMAT_JSON_PATH = path.join(DATA_FOLDER, "formats.json")
FRAME_EFFECT_JSON_PATH = path.join(DATA_FOLDER, "frame_effects.json")

IMPORT_FOLDER = path.join(DATA_FOLDER, "import")
JSON_DIFF_PATH = path.join(IMPORT_FOLDER, "json_differences.json")


BLOCKS_TO_CREATE_PATH = path.join(IMPORT_FOLDER, "blocks_to_create.json")

SETS_TO_CREATE_PATH = path.join(IMPORT_FOLDER, "sets_to_create.json")
SETS_TO_UPDATE_PATH = path.join(IMPORT_FOLDER, "sets_to_update.json")

CARDS_TO_CREATE_PATH = path.join(IMPORT_FOLDER, "cards_to_create.json")
CARDS_TO_UPDATE = path.join(IMPORT_FOLDER, "cards_to_update.json")
CARDS_TO_DELETE = path.join(IMPORT_FOLDER, "cards_to_delete.json")

PRINTINGS_TO_CREATE = path.join(IMPORT_FOLDER, "printings_to_create.json")
PRINTINGS_TO_DELETE = path.join(IMPORT_FOLDER, "printings_to_delete.json")
PRINTINGS_TO_UPDATE = path.join(IMPORT_FOLDER, "printings_to_update.json")

PRINTLANGS_TO_CREATE = path.join(IMPORT_FOLDER, "printlangs_to_create.json")
PRINTLANGS_TO_UPDATE = path.join(IMPORT_FOLDER, "printlangs_to_update.json")

PHYSICAL_CARDS_TO_CREATE = path.join(IMPORT_FOLDER, "physical_cards_to_create.json")

RULINGS_TO_CREATE = path.join(IMPORT_FOLDER, "rulings_to_create.json")
RULINGS_TO_DELETE = path.join(IMPORT_FOLDER, "rulings_to_delete.json")

LEGALITIES_TO_CREATE = path.join(IMPORT_FOLDER, "legalities_to_create.json")
LEGALITIES_TO_DELETE = path.join(IMPORT_FOLDER, "legalities_to_delete.json")
LEGALITIES_TO_UPDATE = path.join(IMPORT_FOLDER, "legalities_to_update.json")

CARD_LINKS_TO_CREATE = path.join(IMPORT_FOLDER, "card_links_to_create.json")

