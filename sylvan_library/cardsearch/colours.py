import re

from sylvan_library.cards.models.card import CardFace

RE_GENERIC_MANA = re.compile(r"{(\d+)}")

MANA_SYMBOLS = [
    "W",
    "U",
    "B",
    "R",
    "G",
    "C",
    "S",
    "X",
    "W/U",
    "U/B",
    "B/R",
    "R/G",
    "G/W",
    "W/B",
    "U/R",
    "B/G",
    "R/W",
    "G/U",
    "2/W",
    "2/U",
    "2/B",
    "2/R",
    "2/G",
    "W/P",
    "U/P",
    "B/P",
    "R/P",
    "G/P",
]

RE_PRODUCES_MAP = {
    symbol: re.compile(r"adds?\W[^\n.]*?{" + symbol.upper() + "}", re.IGNORECASE)
    for symbol in ["w", "u", "b", "r", "g", "c"]
}

RE_PRODUCES_ANY = re.compile(
    r"adds?\W[^\n.]*?(any (combination of )?color|chosen color)", re.IGNORECASE
)


def get_card_face_produces(card_face: CardFace) -> dict[str, bool]:
    produces = {key: False for key in RE_PRODUCES_MAP}
    if not card_face.rules_text:
        return produces
    produces_every_colour = bool(RE_PRODUCES_ANY.search(card_face.rules_text))
    for symbol, regex in RE_PRODUCES_MAP.items():
        if produces_every_colour and symbol != "c":
            does_produce_colour = True
        else:
            does_produce_colour = bool(regex.search(card_face.rules_text))
        produces[symbol] = does_produce_colour
    return produces
