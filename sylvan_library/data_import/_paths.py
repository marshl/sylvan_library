"""
A module for centralising all file paths and ensuring their existence.
"""

from pathlib import Path

# The root directory for all data_import files and folders.
DATA_DIR = Path(__file__).parent.resolve() / "data"

# Define primary data folders
DOWNLOADS_DIR = DATA_DIR / "downloads"
SETS_DIR = DATA_DIR / "sets"
IMPORT_DIR = DATA_DIR / "import"

# --- MTGJSON Download URLs ---
JSON_ZIP_DOWNLOAD_URL = "https://mtgjson.com/api/v5/AllSetFiles.zip"
PRICES_ZIP_DOWNLOAD_URL = "https://mtgjson.com/api/v5/AllPrices.json.zip"
TYPES_DOWNLOAD_URL = "https://mtgjson.com/api/v5/CardTypes.json.zip"
META_DOWNLOAD_URL = "https://mtgjson.com/api/v5/Meta.json"

# --- Local File Paths ---

# Downloaded zip files
JSON_ZIP_PATH = DOWNLOADS_DIR / "AllSetFiles.zip"
PRICES_ZIP_PATH = DOWNLOADS_DIR / "AllPrices.json.zip"
TYPES_ZIP_PATH = DOWNLOADS_DIR / "CardTypes.json.zip"

# Extracted/processed JSON files
META_JSON_PATH = DOWNLOADS_DIR / "Meta.json"
PRICES_JSON_PATH = IMPORT_DIR / "AllPrices.json"
TYPES_JSON_PATH = IMPORT_DIR / "CardTypes.json"

# Static data files
LANGUAGE_JSON_PATH = DATA_DIR / "languages.json"
COLOUR_JSON_PATH = DATA_DIR / "colours.json"
RARITY_JSON_PATH = DATA_DIR / "rarities.json"
FORMAT_JSON_PATH = DATA_DIR / "formats.json"
FRAME_EFFECT_JSON_PATH = DATA_DIR / "frame_effects.json"


def get_set_files() -> list[Path]:
    """
    Gets all json files in the set data directory
    :return: A list of Path objects for the set files
    """
    return list(SETS_DIR.glob("*.json"))
