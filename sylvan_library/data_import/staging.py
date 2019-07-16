"""
Module for staging classes
"""
import datetime
import math
import re
from typing import Dict, List, Optional

from cards.models import Card, Colour

COLOUR_TO_SORT_KEY = {
    0: 0,
    int(Card.colour_flags.white): 1,
    int(Card.colour_flags.blue): 2,
    int(Card.colour_flags.black): 3,
    int(Card.colour_flags.red): 4,
    int(Card.colour_flags.green): 5,
    int(Card.colour_flags.white | Card.colour_flags.blue): 6,
    int(Card.colour_flags.blue | Card.colour_flags.black): 7,
    int(Card.colour_flags.black | Card.colour_flags.red): 8,
    int(Card.colour_flags.red | Card.colour_flags.green): 9,
    int(Card.colour_flags.green | Card.colour_flags.white): 10,
    int(Card.colour_flags.white | Card.colour_flags.black): 11,
    int(Card.colour_flags.blue | Card.colour_flags.red): 12,
    int(Card.colour_flags.black | Card.colour_flags.green): 13,
    int(Card.colour_flags.red | Card.colour_flags.white): 14,
    int(Card.colour_flags.green | Card.colour_flags.blue): 15,
    int(Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black): 16,
    int(Card.colour_flags.blue | Card.colour_flags.black | Card.colour_flags.red): 17,
    int(Card.colour_flags.black | Card.colour_flags.red | Card.colour_flags.green): 18,
    int(Card.colour_flags.red | Card.colour_flags.green | Card.colour_flags.white): 19,
    int(Card.colour_flags.green | Card.colour_flags.white | Card.colour_flags.blue): 20,
    int(
        Card.colour_flags.white | Card.colour_flags.black | Card.colour_flags.green
    ): 21,
    int(Card.colour_flags.blue | Card.colour_flags.red | Card.colour_flags.white): 22,
    int(Card.colour_flags.black | Card.colour_flags.green | Card.colour_flags.blue): 23,
    int(Card.colour_flags.red | Card.colour_flags.white | Card.colour_flags.black): 24,
    int(Card.colour_flags.green | Card.colour_flags.blue | Card.colour_flags.red): 25,
    int(
        Card.colour_flags.white
        | Card.colour_flags.blue
        | Card.colour_flags.black
        | Card.colour_flags.red
    ): 26,
    int(
        Card.colour_flags.blue
        | Card.colour_flags.black
        | Card.colour_flags.red
        | Card.colour_flags.green
    ): 27,
    int(
        Card.colour_flags.black
        | Card.colour_flags.red
        | Card.colour_flags.green
        | Card.colour_flags.white
    ): 28,
    int(
        Card.colour_flags.red
        | Card.colour_flags.green
        | Card.colour_flags.white
        | Card.colour_flags.blue
    ): 29,
    int(
        Card.colour_flags.green
        | Card.colour_flags.white
        | Card.colour_flags.blue
        | Card.colour_flags.black
    ): 30,
    int(
        Card.colour_flags.white
        | Card.colour_flags.blue
        | Card.colour_flags.black
        | Card.colour_flags.red
        | Card.colour_flags.green
    ): 31,
}


def convert_number_field_to_numerical(val: str) -> float:
    """
    Converts the stringy value of a number field (Power, Toughness, Loyalty)
    to the numerical representation (e.g. 1+* becomes 1, * becomes 0)
    :param val: The stringy field value
    :return: The numerical representation of that field
    """
    if val == "\u221e":
        return math.inf

    match = re.search(r"(-?[\d.]+)", str(val))
    if match:
        return float(match.group())

    return 0.0


class StagedCard:
    def __init__(self, json_data: dict, is_token: bool):
        self.is_token = is_token
        self.name = json_data.get("name")
        self.scryfall_oracle_id = json_data.get("scryfallOracleId")

        self.cost = json_data.get("manaCost")
        self.cmc = json_data.get("convertedManaCost", 0)
        self.colour_flags = (
            Colour.colour_codes_to_flags(json_data["colors"])
            if "colors" in json_data
            else 0
        )
        self.colour_identity_flags = (
            Colour.colour_codes_to_flags(json_data["colorIdentity"])
            if "colorIdentity" in json_data
            else 0
        )
        self.colour_count = bin(self.colour_flags).count("1")
        self.colour_sort_key = COLOUR_TO_SORT_KEY[int(self.colour_flags)]

        self.colour_weight = 0
        if self.cost:
            generic_mana = re.search(r"(\d+)", self.cost)
            if not generic_mana:
                self.colour_weight = int(self.cmc)
            else:
                self.colour_weight = int(self.cmc) - int(generic_mana.group(0))

        self.layout = json_data["layout"]

        self.power = json_data.get("power")
        self.num_power = float(
            convert_number_field_to_numerical(json_data["power"])
            if "power" in json_data
            else 0
        )
        self.toughness = json_data.get("toughness")
        self.num_toughness = float(
            convert_number_field_to_numerical(json_data["toughness"])
            if "toughness" in json_data
            else 0
        )
        self.loyalty = json_data.get("loyalty")
        self.num_loyalty = float(
            convert_number_field_to_numerical(json_data["loyalty"])
            if "loyalty" in json_data
            else 0
        )

        self.rules_text = json_data.get("text")

        self.type = None
        if self.is_token:
            if "type" in json_data:
                self.type = json_data["type"].split("—")[0].strip()
        elif "types" in json_data:
            self.type = " ".join(
                (json_data.get("supertypes") or []) + (json_data["types"])
            )

        self.subtype = None
        if self.is_token:
            if "type" in json_data:
                self.subtype = json_data["type"].split("—")[-1].strip()
        elif "subtypes" in json_data:
            self.subtype = " ".join(json_data.get("subtypes"))

        self.rulings = json_data.get("rulings", [])
        self.legalities = json_data.get("legalities")
        self.has_other_names = "names" in json_data
        self.other_names = (
            [n for n in json_data["names"] if n != self.name]
            if self.has_other_names
            else []
        )
        self.side = json_data.get("side")
        self.is_reserved = bool(json_data.get("isReserved", False))

    def to_dict(self) -> dict:
        return {
            "cmc": self.cmc,
            "colour_flags": self.colour_flags,
            "colour_count": self.colour_count,
            "colour_identity_flags": self.colour_identity_flags,
            "colour_sort_key": self.colour_sort_key,
            "cost": self.cost,
            "is_reserved": self.is_reserved,
            "is_token": self.is_token,
            "layout": self.layout,
            "loyalty": self.loyalty,
            "name": self.name,
            "num_loyalty": self.num_loyalty,
            "num_power": self.num_power,
            "num_toughness": self.num_toughness,
            "power": self.power,
            "rules_text": self.rules_text,
            "scryfall_oracle_id": self.scryfall_oracle_id,
            "side": self.side,
            "subtype": self.subtype,
            "toughness": self.toughness,
            "type": self.type,
        }


class StagedSet:
    def __init__(self, set_data: dict):
        self.base_set_size = set_data["baseSetSize"]
        self.block = set_data.get("block")
        self.code = set_data["code"]
        self.is_foil_only = set_data["isFoilOnly"]
        self.is_online_only = set_data["isOnlineOnly"]
        self.keyrune_code = set_data["keyruneCode"]
        self.mcm_id = set_data.get("mcmId")
        self.mcm_name = set_data.get("mcmName")
        self.mtg_code = set_data.get("mtgoCode")
        self.name = set_data["name"]
        self.release_date = set_data["releaseDate"]
        self.tcg_player_group_id = set_data.get("tcg_player_group_id")
        self.card_count = set_data["totalSetSize"]
        self.type = set_data["type"]

    def to_dict(self) -> dict:
        return {
            "base_set_size": self.base_set_size,
            "block": self.block,
            "card_count": self.card_count,
            "code": self.code,
            "is_foil_only": self.is_foil_only,
            "is_online_only": self.is_online_only,
            "keyrune_code": self.keyrune_code,
            "mcm_id": self.mcm_id,
            "mcm_name": self.mcm_name,
            "name": self.name,
            "release_date": self.release_date,
            "tcg_player_group_id": self.tcg_player_group_id,
            "type": self.type,
        }


class StagedCardPrinting:
    def __init__(self, card_name: str, card_data: dict, set_data: dict):
        self.card_name = card_name

        self.artist = card_data.get("artist")
        self.border_colour = card_data.get("borderColor")
        self.frame_version = card_data.get("frameVersion")
        self.has_foil = card_data.get("hasFoil")
        self.has_non_foil = card_data.get("hasNonFoil")
        self.number = card_data.get("number")
        self.rarity = card_data.get("rarity")
        self.scryfall_id = card_data.get("scryfallId")
        self.scryfall_illustration_id = card_data.get("scryfallIllustrationId")
        self.json_id = card_data.get("uuid")
        self.multiverse_id = card_data.get("multiverseId")
        self.other_languages = card_data.get("foreignData")
        self.names = card_data.get("names", [])
        self.is_timeshifted = (
            "isTimeshifted" in card_data and card_data["isTimeshifted"]
        )
        self.is_starter = "starter" in card_data and card_data["starter"]
        self.set_code = set_data["code"]
        self.watermark = card_data.get("watermark")
        self.original_type = card_data.get("originalType")
        self.original_text = card_data.get("originalText")
        self.flavour_text = card_data.get("flavorText")

        self.is_new = False

    def to_dict(self):
        return {
            "artist": self.artist,
            "border_colour": self.border_colour,
            "card_name": self.card_name,
            "flavour_text": self.flavour_text,
            "frame_version": self.frame_version,
            "has_non_foil": self.has_non_foil,
            "hasfoil": self.has_foil,
            "is_starter": self.is_starter,
            "is_timeshifted": self.is_timeshifted,
            "json_id": self.json_id,
            "multiverse_id": self.multiverse_id,
            "number": self.number,
            "original_text": self.original_text,
            "original_type": self.original_type,
            "rarity": self.rarity,
            "scryfall_id": self.scryfall_id,
            "scryfall_illustration_id": self.scryfall_illustration_id,
            "set_code": self.set_code,
        }


class StagedLegality:
    def __init__(self, card_name: str, format_code: str, restriction: str):
        self.card_name = card_name
        self.format_code = format_code
        self.restriction = restriction

    def to_dict(self) -> dict:
        return {
            "card_name": self.card_name,
            "format": self.format_code,
            "restriction": self.restriction,
        }


class StagedRuling:
    def __init__(self, card_name: str, text: str, ruling_date: str):
        self.card_name = card_name
        self.text = text
        self.ruling_date = ruling_date

    def to_dict(self) -> dict:
        return {
            "card_name": self.card_name,
            "text": self.text,
            "date": self.ruling_date,
        }


class StagedBlock:
    def __init__(self, name: str, release_date: datetime.date):
        self.name = name
        self.release_date = release_date

    def to_dict(self) -> dict:
        return {"name": self.name, "release_date": self.release_date}


class StagedCardPrintingLanguage:
    def __init__(
        self,
        staged_card_printing: StagedCardPrinting,
        foreign_data: dict,
        card_data: dict,
    ):
        self.printing_uuid = staged_card_printing.json_id

        self.language = foreign_data["language"]
        self.foreign_name = foreign_data["name"]

        self.multiverse_id = foreign_data.get("multiverseId")
        self.text = foreign_data.get("text")
        self.type = foreign_data.get("type")

        self.other_names = card_data.get("names", [])
        self.base_name = card_data["name"]
        if self.base_name in self.other_names:
            self.other_names.remove(self.base_name)
        self.layout = card_data["layout"]
        self.side = card_data.get("side")

        self.is_new = False
        self.has_physical_card = False

    def to_dict(self) -> dict:
        return {
            "printing_uid": self.printing_uuid,
            "language": self.language,
            "foreign_name": self.foreign_name,
            "multiverse_id": self.multiverse_id,
            "text": self.text,
            "type": self.type,
            "base_name": self.base_name,
        }


class StagedPhysicalCard:
    def __init__(self, printing_uuids: List[str], language_code: str, layout: str):
        self.printing_uids = printing_uuids
        self.language_code = language_code
        self.layout = layout

    def to_dict(self) -> dict:
        return {
            "printing_uids": self.printing_uids,
            "language": self.language_code,
            "layout": self.layout,
        }

    def __str__(self) -> str:
        return f"{'/'.join(self.printing_uids)} in {self.language_code} ({self.layout})"
