import random
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
