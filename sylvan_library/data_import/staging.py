"""
Module for staging classes
"""

import datetime
import math
import re
from typing import List, Optional, Dict, Any

import arrow
from django.db import models

from sylvan_library.cards.models.card import (
    CardFace,
    CardPrinting,
    CardFacePrinting,
    CardLocalisation,
    CardFaceLocalisation,
    Card,
)
from sylvan_library.cards.models.colour import Colour, COLOUR_TO_SORT_KEY
from sylvan_library.cards.models.sets import Set


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


class StagedObject:
    """
    The base staged object
    """

    def get_all_fields(self, fields_to_ignore: Optional[set] = None) -> Dict[str, Any]:
        """
        Converts any kind of staging object to a dictionary to save out to json
        :param fields_to_ignore:  Fields that shouldn't be serialized out
        :return: The staged object as a dictionary
        """
        result = {}
        for key in dir(self):
            if key.startswith("_") or (fields_to_ignore and key in fields_to_ignore):
                continue

            attr = getattr(self, key)
            if callable(attr):
                continue

            if isinstance(attr, datetime.date):
                result[key] = attr.strftime("%Y-%m-%d")
            elif attr == math.inf:
                result[key] = "\u221e"
            else:
                result[key] = attr
        return result

    def get_object_differences(
        self, old_object: models.Model, fields_to_ignore: Optional[set] = None
    ) -> dict:
        """
        Gets the differences between the fields of this staged object and its model object
        :param old_object: The old version of the object (stored in the database)
        :param fields_to_ignore: The fields to ignore from comparison
        :return: A dict of "field* => {"old" => "x", "new" => "y"} differences
        """
        if not fields_to_ignore:
            fields_to_ignore = set()
        fields_to_ignore.update(["id", "_state", "_prefetched_objects_cache"])

        differences = {}
        for field, old_val in old_object.__dict__.items():
            if field in fields_to_ignore:
                continue

            if not hasattr(self, field):
                raise Exception(
                    f"Could not find equivalent of {old_object.__class__.__name__}.{field} "
                    f"on {self.__class__.__name__}"
                )

            new_val = getattr(self, field)
            if (
                not isinstance(old_val, type(new_val))
                and not isinstance(old_val, type(None))
                and not isinstance(new_val, type(None))
            ):
                raise Exception(
                    f"Type mismatch for '{field}: was {old_val}, now {new_val} "
                    f"(was {type(old_val)}, now {type(new_val)})"
                )

            if old_val != new_val:
                differences[field] = {"from": old_val, "to": new_val}

        return differences

    def compare_related_list(self, existing_object: models.Model, field_name: str):
        """
        Compares the list from this staged object with the existing object
        :param existing_object:
        :param field_name:
        :return:
        """
        old_values = [
            related.name for related in getattr(existing_object, field_name).all()
        ]
        new_values = getattr(self, field_name)
        if set(old_values) != set(new_values):
            return {field_name: {"from": old_values, "to": new_values}}
        return {}


# pylint: disable=too-many-instance-attributes
class StagedCard(StagedObject):
    """
    Class for staging a card record from json

    See data structure reference here: https://mtgjson.com/files/all-cards/#data-structure
    """

    def __init__(self, card_data: dict, is_token: bool = False) -> None:
        self.is_token: bool = is_token
        self.scryfall_oracle_id: str = card_data.get("identifiers", {}).get(
            "scryfallOracleId"
        )
        self.name: str = card_data["name"]
        self.mana_value: float = float(card_data.get("manaValue", 0.0) or 0)
        self.colour_identity: int = Colour.colour_codes_to_flags(
            card_data.get("colorIdentity", [])
        )
        self.colour_identity_count: int = bin(self.colour_identity).count("1")

        self.layout: str = card_data.get("layout", "normal")

        self.rulings: List[Dict[str, str]] = card_data.get("rulings", [])
        self.rulings.sort(key=lambda x: x["date"])

        self.legalities: Dict[str, str] = card_data.get("legalities", {})
        self.is_reserved: bool = bool(card_data.get("isReserved", False))

    def compare_with_card(self, existing_card: Card) -> Dict[str, Dict[str, Any]]:
        """
        Returns the differences between an existing Card object and the StagedCard version
        :param existing_card: The existing database Card object
        :return: A dict of differences between the two object
        """
        differences = self.get_object_differences(
            existing_card, {"id", "edh_rec_rank", "colour_identity"}
        )

        if self.colour_identity != int(existing_card.colour_identity):
            differences["colour_identity"] = {
                "from": int(existing_card.colour_identity),
                "to": self.colour_identity,
            }

        return differences

    def get_field_data(self):
        return super().get_all_fields(
            fields_to_ignore={
                "has_other_names",
                "legalities",
                "other_names",
                "rulings",
                "unique_rulings",
            }
        )

    @property
    def unique_rulings(self):
        return list({ruling["text"]: ruling for ruling in self.rulings}.values())


# pylint: disable=too-many-instance-attributes
class StagedCardFace(StagedObject):
    def __init__(self, card_data: dict) -> None:
        self.scryfall_oracle_id: str = card_data.get("identifiers", {}).get(
            "scryfallOracleId"
        )

        self.name: str = card_data.get("faceName", card_data["name"])
        self.side = card_data.get("side")

        self.mana_cost: str = card_data.get("manaCost")

        mana_value_text = card_data.get("faceManaValue", card_data.get("manaValue"))
        self.mana_value: float = float(mana_value_text) if mana_value_text else float(0)

        self.colour: int = Colour.colour_codes_to_flags(card_data.get("colors", []))
        self.colour_indicator: int = Colour.colour_codes_to_flags(
            card_data.get("colorIndicator", [])
        )
        self.colour_count: int = bin(self.colour).count("1")
        self.colour_sort_key: int = COLOUR_TO_SORT_KEY[self.colour]

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
        return int(self.mana_value - self.generic_mana_count)

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

    def get_card_face_differences(
        self, existing_card_face: CardFace
    ) -> Dict[str, Dict[str, Any]]:
        differences = self.get_object_differences(
            existing_card_face,
            fields_to_ignore={"card_id", "colour", "colour_indicator"},
        )

        # Colour flags need to be handled slightly explicitly because the database values aren't int
        if self.colour != int(existing_card_face.colour):
            differences["colour"] = {
                "from": int(existing_card_face.colour),
                "to": self.colour,
            }

        if self.colour_indicator != int(existing_card_face.colour_indicator):
            differences["colour_indicator"] = {
                "from": int(existing_card_face.colour_indicator),
                "to": self.colour_indicator,
            }

        differences.update(self.compare_related_list(existing_card_face, "types"))
        differences.update(self.compare_related_list(existing_card_face, "subtypes"))
        differences.update(self.compare_related_list(existing_card_face, "supertypes"))

        return differences

    def get_field_data(self):
        return self.get_all_fields(fields_to_ignore={"generic_mana_count"})


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class StagedSet(StagedObject):
    """
    Class for staging a Set record from MTGJSON
    """

    def __init__(self, set_data: dict, for_token: bool):
        self.set_data = set_data
        self.base_set_size: int = set_data["baseSetSize"]
        self.block_name: str = set_data.get("block")
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
        self.parent_set_code: str = set_data.get("parentCode")
        self.is_token_set: bool = for_token
        if self.is_token_set:
            self.code = "T" + self.code
            self.name += " Tokens"
            self.parent_set_code = set_data["code"]
            self.type = "token"
            self.total_set_size = self.base_set_size = len(set_data["tokens"])

    def get_cards(self) -> List[dict]:
        if self.is_token_set:
            return self.set_data.get("tokens") or self.set_data.get("cards", [])
        return self.set_data.get("cards", [])

    def get_scryfall_oracle_ids(self):
        return [
            card["identifiers"]["scryfallOracleId"]
            for card in self.get_cards()
            if "scryfallOracleId" in card["identifiers"]
        ]

    def compare_with_set(self, existing_set: Set) -> dict:
        """
        Compares this set with an existing Set object
        :param existing_set: The existing set to compare against
        :return:
        """
        differences = self.get_object_differences(
            existing_set,
            fields_to_ignore={
                "id",
                "release_date",
                "parent_set_id",
                "block_id",
                "set_data",
            },
        )
        if (not existing_set.block and self.block_name) or (
            existing_set.block and existing_set.block.name != self.block_name
        ):
            differences["block_name"] = {
                "from": existing_set.block.name if existing_set.block else None,
                "to": self.block_name,
            }

        if existing_set.release_date != self.release_date:
            differences["release_date"] = {
                "from": (
                    existing_set.release_date.strftime("%Y-%m-%d")
                    if existing_set.release_date
                    else None
                ),
                "to": self.release_date.strftime("%Y-%m-%d"),
            }
        return differences

    def get_field_data(self):
        return self.get_all_fields(fields_to_ignore={"set_data"})


# pylint: disable=too-many-instance-attributes
class StagedCardPrinting(StagedObject):
    """
    Class for staging a CardPrinting record from MTGJSON
    """

    def __init__(self, card_data: dict, set_code: str):
        self.card_name = card_data["name"]
        self.scryfall_id = card_data["identifiers"]["scryfallId"]

        self.border_colour = card_data.get("borderColor")
        self.duel_deck_side = card_data.get("duelDeck")

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
        self.mtg_stocks_id = card_data.get("mtgStocksId")
        self.number = card_data.get("number")
        self.other_languages = card_data.get("foreignData", [])
        self.rarity = card_data.get("rarity", "common")

        identifiers = card_data.get("identifiers", {})
        self.mtgo_id = int(identifiers["mtgoId"]) if "mtgoId" in identifiers else None
        self.mtgo_foil_id = (
            int(identifiers["mtgoFoilId"]) if "mtgoFoilId" in identifiers else None
        )
        self.magic_card_market_id = (
            int(identifiers["mcmId"]) if "mcmId" in identifiers else None
        )
        self.magic_card_market_meta_id = (
            int(identifiers["mcmMetaId"]) if "mcmMetaId" in identifiers else None
        )

        self.scryfall_id = identifiers.get("scryfallId")

        self.mtg_arena_id = (
            int(identifiers.get("mtgArenaId")) if "mtgArenaId" in identifiers else None
        )

        self.set_code = set_code
        self.tcg_player_product_id = identifiers.get("tcgPlayerProductId")

    @property
    def numerical_number(self) -> Optional[int]:
        """

        :return:
        """
        if self.number is None:
            return None
        return int(convert_number_field_to_numerical(self.number))

    def compare_with_existing_card_printing(
        self, existing_printing: CardPrinting
    ) -> Dict[str, dict]:
        """
        Gets the differences between an existing printing and one from the json

        Most of the time there won't be any differences, but this will be useful for adding in new
        fields that didn't exist before
        :param existing_printing: The existing CardPrinting object
        :return: The dict of differences between the two objects
        """
        differences = self.get_object_differences(
            existing_printing,
            {"id", "set_id", "rarity_id", "card_id", "latest_price_id"},
        )
        if self.rarity.lower() != existing_printing.rarity.name.lower():
            differences["rarity"] = {
                "from": existing_printing.rarity.name.lower(),
                "to": self.rarity,
            }
        return differences

    def get_field_data(self):
        return self.get_all_fields(
            fields_to_ignore={
                "id",
                "set_id",
                "rarity_id",
                "card_id",
                "scryfall_id",
                "is_new",
                "other_languages",
            }
        )


class StagedCardFacePrinting(StagedObject):
    def __init__(self, card_data: dict):
        self.uuid = card_data["uuid"]
        self.artist = card_data.get("artist")
        self.flavour_text = card_data.get("flavorText")
        self.original_text = card_data.get("originalText")
        self.original_type = card_data.get("originalType")
        self.watermark = card_data.get("watermark")
        self.frame_effects = card_data.get("frameEffects", [])

        identifiers = card_data.get("identifiers", {})
        self.scryfall_illustration_id = identifiers.get("scryfallIllustrationId")

    def get_field_data(self):
        return self.get_all_fields(fields_to_ignore={"uuid"})

    def compare_with_existing_face_printing(
        self, existing_face_printing: CardFacePrinting
    ):
        differences = self.get_object_differences(
            existing_face_printing,
            fields_to_ignore={
                # "uuid",
                "scryfall_id",  # annotation
                "face_side",  # annotation
                "frame_effects",
                "card_face_id",
                "card_printing_id",
            },
        )
        old_frame_effects = [
            frame_effect.code
            for frame_effect in existing_face_printing.frame_effects.all()
        ]
        if set(self.frame_effects) != set(old_frame_effects):
            differences["frame_effects"] = {
                "from": old_frame_effects,
                "to": self.frame_effects,
            }

        return differences


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
# class StagedRuling(StagedObject):
#     """
#     Class for staging a CardRuling record from MTGJSON
#     """
#
#     def __init__(self, card_name: str, scryfall_oracle_id: str, text: str, ruling_date: str):
#         self.card_name = card_name
#         self.scryfall_oracle_id = scryfall_oracle_id
#         self.text = text
#         self.date = ruling_date


class StagedBlock:
    """
    Class for staging a Block record from MTGJSON
    """

    def __init__(self, name: str, release_date: datetime.date):
        self.name = name
        self.release_date = release_date


class StagedCardLocalisation(StagedObject):
    """
    Class for staging a CardLocalisation record from MTGJSON
    """

    def __init__(
        self, staged_card_printing: StagedCardPrinting, foreign_data: Dict[str, Any]
    ):
        self.printing_scryfall_id = staged_card_printing.scryfall_id

        self.language_name = foreign_data["language"]
        self.card_name = foreign_data["name"]
        self.multiverse_id = (
            int(foreign_data["multiverseId"])
            if "multiverseId" in foreign_data
            else None
        )

    def get_field_data(self):
        return self.get_all_fields(
            fields_to_ignore={"printing_scryfall_id", "language_name"}
        )

    def compare_with_existing_localisation(
        self, existing_card_localisation: CardLocalisation
    ):
        return self.get_object_differences(
            existing_card_localisation,
            fields_to_ignore={
                "card_printing_id",
                "language_id",
                "scryfall_id",  # annotation
            },
        )


class StagedCardFaceLocalisation(StagedObject):
    """
    A "staged" CardFaceLocalisation. A CardFaceLocalisation is the face of a card printed in some
    set of some language. Staged objects are used as temporaru versions of what is stored in the
    JSON that can then be compared to what is stored in the database.
    """

    def __init__(
        self,
        staged_card_printing: StagedCardPrinting,
        staged_face_printing: StagedCardFacePrinting,
        foreign_data: Dict[str, Any],
    ):
        self.printing_scryfall_id = staged_card_printing.scryfall_id
        self.face_printing_uuid = staged_face_printing.uuid

        self.language_name = foreign_data["language"]
        self.face_name = foreign_data.get("faceName", foreign_data["name"])

        self.text = foreign_data.get("text")
        self.type = foreign_data.get("type")
        self.flavour_text = foreign_data.get("flavorText")

    def get_field_data(self):
        return self.get_all_fields(
            fields_to_ignore={"printing_scryfall_id", "language_name"}
        )

    def compare_with_existing_face_localisation(
        self, existing_face_localisation: CardFaceLocalisation
    ):
        return self.get_object_differences(
            existing_face_localisation,
            fields_to_ignore={
                "scryfall_id",  # annotation
                "face_side",  # annotation
                "localisation_id",
                "card_printing_face_id",
                "image_id",
            },
        )
