import random
import urllib
from abc import ABC
from typing import Dict, Any

from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q

from cards.models.card import (
    Card,
    CardFace,
)
from cards.models.colour import Colour
from cards.models.user import UserProps


def get_page_number(request: WSGIRequest, param_name: str = "page") -> int:
    """
    Gets the page number of a given request
    :param param_name:
    :param request: The request to get the page from
    :return: The page number
    """
    try:
        return int(request.GET.get(param_name))
    except (TypeError, ValueError):
        return 1


def get_unused_cards(user: User):
    """
    Gets all cards that the given user has never used in a deck
    :param user: The user to get the unused cards for
    :return:
    """
    users_deck_cards = Card.objects.filter(
        deck_cards__deck__owner=user,
        deck_cards__deck__is_prototype=False,
        deck_cards__board="main",
    )
    users_cards = (
        Card.objects.filter(printings__localisations__ownerships__owner=user)
        .filter(is_token=False)
        .distinct()
    )
    if not hasattr(user, "userprops"):
        UserProps.add_to_user(user)

    rand = random.Random(user.userprops.unused_cards_seed)
    unused_cards = list(users_cards.exclude(id__in=users_deck_cards).order_by("id"))
    rand.shuffle(unused_cards)
    unused_cards = unused_cards[:10]
    unused_cards = [
        {
            "card": card,
            "preferred_printing": card.printings.filter(
                localisations__ownerships__owner=user
            )
            .order_by("set__release_date")
            .last(),
        }
        for card in unused_cards
    ]
    return unused_cards


def get_unused_commanders(user: User):
    """
    Gets the commanders that haven't been used in any deck by the given user
    :param user: The user to get unused commands for
    :return: A list of dicts containing the unused cards
    """
    users_deck_cards = Card.objects.filter(
        deck_cards__deck__owner=user,
        deck_cards__deck__is_prototype=False,
        deck_cards__is_commander=True,
    )
    commander_cards = (
        Card.objects.filter(is_token=False)
        .filter(
            faces__in=CardFace.objects.filter(
                Q(side__isnull=True) | Q(side="a")
            ).filter(
                (Q(supertypes__name="Legendary") & Q(types__name="Creature"))
                | Q(rules_text__contains="can be your commander")
            )
        )
        .distinct()
    )

    users_commanders = Card.objects.filter(
        printings__localisations__ownerships__owner=user, id__in=commander_cards
    ).distinct()
    rand = random.Random(user.userprops.unused_cards_seed)
    unused_cards = list(
        users_commanders.exclude(id__in=users_deck_cards).order_by("id")
    )
    rand.shuffle(unused_cards)
    unused_cards = unused_cards[:10]
    unused_cards = [
        {
            "card": card,
            "preferred_printing": card.printings.filter(
                localisations__ownerships__owner=user
            )
            .order_by("set__release_date")
            .last(),
        }
        for card in unused_cards
    ]
    return unused_cards


def get_unused_partner_commanders(user: User):
    user_owned_cards = Card.objects.filter(
        printings__localisations__ownerships__owner=user
    ).distinct()

    partner_cards = list(
        user_owned_cards.filter(faces__rules_text__regex="Partner\W").exclude(
            faces__rules_text__contains="Partner with"
        )
    )
    background_cards = list(user_owned_cards.filter(faces__subtypes__name="Background"))
    choose_background_cards = list(
        user_owned_cards.filter(faces__rules_text__contains="Choose a Background")
    )

    rand = random.Random(user.userprops.unused_cards_seed)
    rand.shuffle(partner_cards)
    rand.shuffle(background_cards)
    rand.shuffle(choose_background_cards)
    partner_cards = partner_cards[:20]
    background_limit = min([len(background_cards), len(choose_background_cards), 10])
    background_cards = background_cards[:background_limit]
    choose_background_cards = choose_background_cards[:background_limit]

    partner_pairs = []
    for partner_a, partner_b in zip(partner_cards[0::2], partner_cards[1::2]):
        if partner_a and partner_b:
            partner_pairs.append({"partner_1": partner_a, "partner_2": partner_b})

    background_pairs = [
        {
            "choose_background": choose_background_cards[x],
            "background": background_cards[x],
        }
        for x in range(background_limit)
    ]

    return partner_pairs, background_pairs


def get_colour_info() -> Dict[int, Dict[str, Any]]:
    """
    Gets information about all colours
    :return: The colour information as a dict
    """
    return {
        colour.symbol: {
            "name": colour.name,
            "symbol": colour.symbol,
            "display_order": colour.display_order,
            "chart_colour": colour.chart_colour,
        }
        for colour in Colour.objects.all().order_by("display_order")
    }


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
        return {"search_query": f"({card.name} token)" if card.is_token else card.name}


class ScryfallLink(LinkBuilder):
    def get_name(self) -> str:
        return "Search on Scryfall"

    def get_base_url(self) -> str:
        return "https://scryfall.com/search"

    def get_params(self, card: Card) -> dict:
        return {"q": urllib.parse.urlencode({"name": card.name})}


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
