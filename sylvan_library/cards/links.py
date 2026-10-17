"""
Links to other sites for a card
"""

import urllib.parse
from abc import ABC
from typing import List, Dict

from sylvan_library.cards.models.card import Card, CardLocalisation
from sylvan_library.cards.models.language import Language


class LinkBuilder(ABC):
    def get_name(self) -> str:
        raise NotImplementedError

    def get_base_url(self) -> str:
        raise NotImplementedError

    def get_params(self, card: Card) -> dict:
        raise NotImplementedError

    def build_link(self, card: Card):
        return {
            "name": self.get_name(),
            "url": f"{self.get_base_url()}?{urllib.parse.urlencode(self.get_params(card))}",
        }


class TCGPlayerLink(LinkBuilder):
    def get_name(self):
        return "TCGPlayer Decks"

    def get_base_url(self) -> str:
        return "https://decks.tcgplayer.com/magic/deck/search"

    def get_params(self, card: Card) -> dict:
        return {"contains": card.name, "page": 1}


class EDHRecLink(LinkBuilder):
    def get_name(self) -> str:
        return "Card Analysis on EDHREC"

    def get_base_url(self) -> str:
        return "https://edhrec.com/route/"

    def get_params(self, card: Card) -> dict:
        return {"cc": card.faces.first().name}


class DeckStatsLink(LinkBuilder):
    def get_name(self) -> str:
        return "Search on DeckStats"

    def get_base_url(self) -> str:
        return "https://deckstats.net/decks/search/"

    def get_params(self, card: Card) -> dict:
        return {"search_cards[]": card.name}


class MTGTop8Link(LinkBuilder):
    def get_name(self) -> str:
        return "MTGTop8 Decks"

    def get_base_url(self) -> str:
        return "https://mtgtop8.com/search"

    def get_params(self, card: Card) -> dict:
        return {"MD_check": 1, "SB_check": 1, "cards": card.faces.first().name}


class StarCityGamesLink(LinkBuilder):
    def get_name(self) -> str:
        return "Search on Starcity Games"

    def get_base_url(self) -> str:
        return "https://starcitygames.com/search/"

    def get_params(self, card: Card) -> dict:
        # https://starcitygames.com/search/?card_name=Assault%20Formation&sort=priceasc
        return {
            "card_name": f"({card.name} token)" if card.is_token else card.name,
            "sort": "priceasc",
        }


class ScryfallLink(LinkBuilder):
    def get_name(self) -> str:
        return "Search on Scryfall"

    def get_base_url(self) -> str:
        return "https://scryfall.com/search"

    def get_params(self, card: Card) -> dict:
        return {"q": f'name="{card.name}"'}


class CardKingdomLink(LinkBuilder):
    def get_name(self) -> str:
        return "Card Kingdom"

    def get_base_url(self) -> str:
        return "https://www.cardkingdom.com/catalog/search"

    def get_params(self, card: Card) -> dict:
        if not card.is_token:
            if card.layout in ("aftermath", "split"):
                face_names = [f.name for f in card.faces.all()]
                search = " // ".join(face_names)
            else:
                search = card.faces.first().name
        elif card.faces.filter(types__name="Emblem").exists():
            first_name = card.name.split(" ")[0]
            return {
                "search": "mtg_advanced",
                "filter[name]": first_name,
                "filter[card_type][10]": "emblem",
            }
        else:
            search = f"{card.name} token"

        return {"search": "header", "filter[name]": search}


def get_card_links(card: Card) -> List[Dict[str, str]]:
    """
    Gets the links to other sites for the given card, with Gatherer first if the card has
    an English multiverse ID
    :param card: The card to get links for
    :return: A list of dicts with the name and url of each link
    """
    link_builders = [
        TCGPlayerLink(),
        EDHRecLink(),
        DeckStatsLink(),
        MTGTop8Link(),
        StarCityGamesLink(),
        ScryfallLink(),
        CardKingdomLink(),
    ]
    links = [link_builder.build_link(card) for link_builder in link_builders]

    localisation = (
        CardLocalisation.objects.filter(card_printing__card=card)
        .filter(multiverse_id__isnull=False)
        .filter(language=Language.english())
        .order_by("card_printing__set__release_date")
        .last()
    )
    if localisation:
        links.insert(
            0,
            {
                "name": "View on Gatherer",
                "url": f"https://gatherer.wizards.com/Pages/Card/Details.aspx?{urllib.parse.urlencode({'multiverseid': localisation.multiverse_id})}",
            },
        )
    return links
