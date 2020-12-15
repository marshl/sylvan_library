"""
Module for staging classes
"""
import datetime
import math
import re
from typing import List, Optional, Dict, Any

import arrow

from cards.models import Card, Colour

#
# COLOUR_TO_SORT_KEY = {
#     0: 0,
#     int(Card.colour_flags.white): 1,
#     int(Card.colour_flags.blue): 2,
#     int(Card.colour_flags.black): 3,
#     int(Card.colour_flags.red): 4,
#     int(Card.colour_flags.green): 5,
#     int(Card.colour_flags.white | Card.colour_flags.blue): 6,
#     int(Card.colour_flags.blue | Card.colour_flags.black): 7,
#     int(Card.colour_flags.black | Card.colour_flags.red): 8,
#     int(Card.colour_flags.red | Card.colour_flags.green): 9,
#     int(Card.colour_flags.green | Card.colour_flags.white): 10,
#     int(Card.colour_flags.white | Card.colour_flags.black): 11,
#     int(Card.colour_flags.blue | Card.colour_flags.red): 12,
#     int(Card.colour_flags.black | Card.colour_flags.green): 13,
#     int(Card.colour_flags.red | Card.colour_flags.white): 14,
#     int(Card.colour_flags.green | Card.colour_flags.blue): 15,
#     int(Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black): 16,
#     int(Card.colour_flags.blue | Card.colour_flags.black | Card.colour_flags.red): 17,
#     int(Card.colour_flags.black | Card.colour_flags.red | Card.colour_flags.green): 18,
#     int(Card.colour_flags.red | Card.colour_flags.green | Card.colour_flags.white): 19,
#     int(Card.colour_flags.green | Card.colour_flags.white | Card.colour_flags.blue): 20,
#     int(
#         Card.colour_flags.white | Card.colour_flags.black | Card.colour_flags.green
#     ): 21,
#     int(Card.colour_flags.blue | Card.colour_flags.red | Card.colour_flags.white): 22,
#     int(Card.colour_flags.black | Card.colour_flags.green | Card.colour_flags.blue): 23,
#     int(Card.colour_flags.red | Card.colour_flags.white | Card.colour_flags.black): 24,
#     int(Card.colour_flags.green | Card.colour_flags.blue | Card.colour_flags.red): 25,
#     int(
#         Card.colour_flags.white
#         | Card.colour_flags.blue
#         | Card.colour_flags.black
#         | Card.colour_flags.red
#     ): 26,
#     int(
#         Card.colour_flags.blue
#         | Card.colour_flags.black
#         | Card.colour_flags.red
#         | Card.colour_flags.green
#     ): 27,
#     int(
#         Card.colour_flags.black
#         | Card.colour_flags.red
#         | Card.colour_flags.green
#         | Card.colour_flags.white
#     ): 28,
#     int(
#         Card.colour_flags.red
#         | Card.colour_flags.green
#         | Card.colour_flags.white
#         | Card.colour_flags.blue
#     ): 29,
#     int(
#         Card.colour_flags.green
#         | Card.colour_flags.white
#         | Card.colour_flags.blue
#         | Card.colour_flags.black
#     ): 30,
#     int(
#         Card.colour_flags.white
#         | Card.colour_flags.blue
#         | Card.colour_flags.black
#         | Card.colour_flags.red
#         | Card.colour_flags.green
#     ): 31,
# }


def convert_number_field_to_numerical(val: str) -> float:
    """
    Converts the stringy value of a number field (Power, Toughness, Loyalty)
    to the numerical representation (e.g. 1+* becomes 1, * becomes 0)
    :param val: The stringy field value
    :return: The numerical representation of that field
    """
    if val is None:
        return 0.0

    if val == "\u221e":
        return math.inf

    match = re.search(r"(-?[\d.]+)", str(val))
    if match:
        return float(match.group())

    return 0.0


# pylint: disable=too-many-instance-attributes
class StagedCard:
    """
    Class for staging a card record from json

    See data structure reference here: https://mtgjson.com/files/all-cards/#data-structure
    """

    def __init__(self, card_data: dict, is_token: bool = False) -> None:
        self.is_token: bool = is_token
        self.scryfall_oracle_id: str = card_data.get("identifiers", {}).get(
            "scryfallOracleId"
        )
        assert self.scryfall_oracle_id, "Staged cards must have a scryfall oracle ID"
        self.name: str = card_data["name"]
        self.converted_mana_cost: float = float(card_data.get("convertedManaCost", 0.0))
        self.colour_identity: int = Colour.colour_codes_to_flags(
            card_data.get("colorIdentity", [])
        )
        self.colour_identity_count: int = bin(self.colour_identity).count("1")

        self.layout: str = card_data.get("layout", "normal")

        self.rulings: List[Dict[str, str]] = card_data.get("rulings", [])
        self.legalities: Dict[str, str] = card_data.get("legalities", [])
        self.is_reserved: bool = bool(card_data.get("isReserved", False))


# pylint: disable=too-many-instance-attributes
class StagedCardFace:
    def __init__(self, card_data: dict) -> None:
        self.scryfall_oracle_id: str = card_data.get("identifiers", {}).get(
            "scryfallOracleId"
        )
        assert self.scryfall_oracle_id

        self.name: str = card_data.get("faceName", card_data["name"])
        self.side = card_data.get("side")

        self.mana_cost: str = card_data.get("manaCost")

        cmc_text = card_data.get(
            "faceConvertedManaCost", card_data.get("convertedManaCost")
        )
        self.converted_mana_cost: float = (
            float(cmc_text) if cmc_text is not None else float(0)
        )

        self.colour: int = Colour.colour_codes_to_flags(
            card_data.get("colors", [])
        )
        self.colour_indicator: int = Colour.colour_codes_to_flags(
            card_data.get("colorIndicator", [])
        )
        self.colour_count: int = bin(self.colour).count("1")
        # self.colour_sort_key: int = COLOUR_TO_SORT_KEY[int(self.colour_flags)]
        self.colour_sort_key: int = 0  # TODO: Colour sort keys

        self.power: Optional[str] = card_data.get("power")
        self.toughness: Optional[str] = card_data.get("toughness")
        self.loyalty: Optional[str] = card_data.get("loyalty")
        self.rules_text: Optional[str] = card_data.get("text")
        self.hand_modifier: str = card_data.get("hand")
        self.life_modifier: str = card_data.get("life")

        self.type_line: Optional[str] = card_data.get("type")
        self.types: List[str] = card_data.get("types", [])
        self.subtypes: List[str] = card_data.get("subtypes", [])
        self.supertypes: List[str] = card_data.get("supertypes", [])

    @property
    def colour_weight(self) -> int:
        """
        Gets the "colour weight" of the card, the number of coloured mana symbols te card has
        :return: The card's colour weight
        """
        return int(self.converted_mana_cost) - self.generic_mana_count

    @property
    def num_power(self) -> float:
        """
        Gets the numerical representation of the power of the card
        :return: The numerical power of this card
        """
        return convert_number_field_to_numerical(self.power)

    @property
    def num_toughness(self) -> float:
        """
        Gets the numerical representation of the toughness of the card
        :return: The numerical toughness of this card
        """
        return convert_number_field_to_numerical(self.toughness)

    @property
    def num_loyalty(self) -> float:
        """
        Gets the numerical representation  of the loyalty of this card
        :return: THe numerical loyalty of this card
        """
        return convert_number_field_to_numerical(self.loyalty)

    @property
    def num_hand_modifier(self) -> int:
        """
        Gets the numerical representation of the handmodifier of this card (for vanguard)
        :return: THe numerical hand modifier of this card
        """
        return int(convert_number_field_to_numerical(self.hand_modifier))

    @property
    def num_life_modifier(self) -> int:
        """
        Gets the numerical representation of the life modifier of this card (for vanguard)
        :return: THe numerical life modifier of this card
        """
        return int(convert_number_field_to_numerical(self.life_modifier))

    @property
    def generic_mana_count(self) -> int:
        """
        Gets the number for the generic mana symbol in this cards cost
        (if there is one, otherwise 0)
        :return: The amount of generic mana required to cast this card
        """
        if not self.mana_cost:
            return 0

        generic_mana = re.search(r"{(\d+)}", self.mana_cost)
        if generic_mana:
            return int(generic_mana.group(1))
        return 0


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class StagedSet:
    """
    Class for staging a Set record from MTGJSON
    """

    def __init__(self, set_data: dict, for_token: bool):
        self.base_set_size: int = set_data["baseSetSize"]
        self.block: str = set_data.get("block")
        self.code: str = set_data["code"]
        self.is_foil_only: bool = set_data["isFoilOnly"]
        self.is_foreign_only: bool = set_data.get("isForeignOnly", False)
        self.is_online_only: bool = set_data["isOnlineOnly"]
        self.is_partial_preview: bool = set_data.get("isPartialPreview", False)
        self.keyrune_code: str = set_data["keyruneCode"]
        self.magic_card_market_name: Optional[str] = set_data.get("mcmName")
        self.magic_card_market_id: Optional[str] = set_data.get("mcmId")
        self.mtgo_code: str = set_data.get("mtgoCode")
        self.name: str = set_data["name"]
        self.release_date: datetime.date = arrow.get(set_data["releaseDate"]).date()
        self.tcg_player_group_id: str = set_data.get("tcg_player_group_id")
        self.total_set_size: int = set_data["totalSetSize"]
        self.type: str = set_data["type"]
        self.parent_set_code = set_data.get("parentCode")

        if for_token:
            self.code = "T" + self.code
            self.name += " Tokens"
            self.parent_set_code = set_data["code"]
            self.type = "token"
            self.total_set_size = self.base_set_size = len(set_data["tokens"])

        self.scryfall_oracle_ids: List[str] = [
            card["identifiers"]["scryfallOracleId"]
            for card in set_data.get("cards", []) + set_data.get("tokens", [])
        ]


# pylint: disable=too-many-instance-attributes
class StagedCardPrinting:
    """
    Class for staging a CardPrinting record from MTGJSON
    """

    def __init__(
        self, card_name: str, card_data: dict, staged_set: StagedSet, for_token: bool
    ):
        self.card_name = card_name

        self.artist = card_data.get("artist")
        self.border_colour = card_data.get("borderColor")
        self.duel_deck_side = card_data.get("duelDeck")
        self.flavour_text = card_data.get("flavorText")
        self.frame_effects = card_data.get("frameEffects", [])
        # TODO: Frame effect list
        self.frame_effect = self.frame_effects[0] if self.frame_effects else None
        self.frame_version = card_data.get("frameVersion")
        self.has_foil = card_data.get("hasFoil", True)
        self.has_non_foil = card_data.get("hasNonFoil", True)
        self.is_alternative = card_data.get("isAlternative", False)
        self.is_arena = "arena" in card_data.get("availability", [])
        self.is_full_art = card_data.get("isFullArt", False)
        self.is_mtgo = "mtgo" in card_data.get("availability", [])
        self.is_online_only = card_data.get("isOnlineOnly", False)
        self.is_oversized = card_data.get("isOversized", False)
        self.is_paper = card_data.get("isPaper", True)
        self.is_promo = card_data.get("isPromo", False)
        self.is_reprint = card_data.get("isReprint", False)
        self.is_starter = "starter" in card_data and card_data["starter"]
        self.is_story_spotlight = card_data.get("isStorySpotlight", False)
        self.is_textless = card_data.get("isTextless", False)
        self.is_timeshifted = (
            "isTimeshifted" in card_data and card_data["isTimeshifted"]
        )
        self.json_id = card_data.get("uuid")
        self.mtg_stocks_id = card_data.get("mtgStocksId")
        self.names = card_data.get("names", [])
        self.number = card_data.get("number")
        self.original_text = card_data.get("originalText")
        self.original_type = card_data.get("originalType")
        self.other_languages = card_data.get("foreignData", [])
        self.rarity = card_data.get("rarity", "common")

        self.mtgo_id = card_data.get("identifiers", {}).get("mtgoId")
        if self.mtgo_id:
            self.mtgo_id = int(self.mtgo_id)
        self.mtgo_foil_id = card_data.get("identifiers", {}).get("mtgoFoilId")
        if self.mtgo_foil_id:
            self.mtgo_foil_id = int(self.mtgo_foil_id)

        self.magic_card_market_id = card_data.get("identifiers", {}).get("mcmId")
        if self.magic_card_market_id:
            self.magic_card_market_id = int(self.magic_card_market_id)

        self.magic_card_market_meta_id = card_data.get("identifiers", {}).get(
            "mcmMetaId"
        )
        if self.magic_card_market_meta_id:
            self.magic_card_market_meta_id = int(self.magic_card_market_meta_id)

        self.multiverse_id = card_data.get("identifiers", {}).get("multiverseId")
        if self.multiverse_id is not None:
            self.multiverse_id = int(self.multiverse_id)

        self.scryfall_id = card_data.get("identifiers", {}).get("scryfallId")
        self.scryfall_illustration_id = card_data.get("identifiers", {}).get(
            "scryfallIllustrationId"
        )

        self.mtg_arena_id = card_data.get("identifiers", {}).get("mtgArenaId")
        if self.mtg_arena_id:
            self.mtg_arena_id = int(self.mtg_arena_id)

        self.set_code = staged_set.code
        self.tcg_player_product_id = card_data.get("identifiers", {}).get(
            "tcgPlayerProductId"
        )
        self.watermark = card_data.get("watermark")

        self.is_new = False

    @property
    def numerical_number(self) -> Optional[int]:
        if self.number is None:
            return None
        return int(convert_number_field_to_numerical(self.number))


# pylint: disable=too-few-public-methods
class StagedLegality:
    """
    Class for staging a CardLegality record from MTGJSON
    """

    def __init__(self, card_name: str, format_code: str, restriction: str):
        self.card_name = card_name
        self.format_code = format_code
        self.restriction = restriction


# pylint: disable=too-few-public-methods
class StagedRuling:
    """
    Class for staging a CardRuling record from MTGJSON
    """

    def __init__(self, card_name: str, text: str, ruling_date: str):
        self.card_name = card_name
        self.text = text
        self.date = ruling_date


class StagedBlock:
    """
    Class for staging a Block record from MTGJSON
    """

    def __init__(self, name: str, release_date: datetime.date):
        self.name = name
        self.release_date = release_date


# pylint: disable=too-few-public-methods
class StagedCardPrintingLanguage:
    """
    Class for staging a CardPrintingLanguage record from MTGJSON
    """

    def __init__(
        self,
        staged_card_printing: StagedCardPrinting,
        foreign_data: Dict[str, Any],
        card_data: Dict[str, Any],
    ):
        self.printing_uid = staged_card_printing.json_id

        self.language = foreign_data["language"]
        self.card_name = foreign_data.get("faceName", foreign_data["name"])

        self.multiverse_id = foreign_data.get("multiverseId")
        self.text = foreign_data.get("text")
        self.type = foreign_data.get("type")
        self.flavour_text = foreign_data.get("flavorText")

        self.has_other_names = (
            "names" in card_data and card_data["layout"] != "double_faced_token"
        )
        self.other_names = (
            [n for n in card_data["names"] if n != staged_card_printing.card_name]
            if self.has_other_names
            else []
        )

        self.base_name = card_data.get("faceName", card_data["name"])
        if self.base_name in self.other_names:
            self.other_names.remove(self.base_name)
        self.layout = card_data["layout"]
        self.side = card_data.get("side")
        self.number = card_data.get("number")
        self.set_code = staged_card_printing.set_code

        self.is_new = False
        self.has_physical_card = False


class StagedPhysicalCard:
    """
    Class for staging a PhysicalCard record from MTGJSON
    """

    def __init__(self, printing_uuids: List[str], language_code: str, layout: str):
        self.printing_uids = printing_uuids
        self.language = language_code
        self.layout = layout

    def __str__(self) -> str:
        return f"{'/'.join(self.printing_uids)} in {self.language} ({self.layout})"


class StagedCardPrice:
    """
    The staging record for a CardPrice
    """

    def __init__(
        self, printing_uuid: str, date_str: str, price: float, price_type: str
    ):
        self.printing_uuid = printing_uuid
        self.date = date_str
        self.price = price
        if price_type == "paperFoil":
            self.price_type = "paper_foil"
        elif price_type == "paper":
            self.price_type = "paper"
        elif price_type == "mtgo":
            self.price_type = "mtgo"
        elif price_type == "mtgoFoil":
            self.price_type = "mtgo_foil"
        else:
            raise Exception(
                f"Unknown card price price type: {price_type} for {printing_uuid}"
            )
