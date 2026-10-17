"""
Stats about a user's collection compared to their decks
"""

import random
from typing import Dict, Any

from django.contrib.auth.models import User
from django.db.models import Q

from sylvan_library.cards.models.card import (
    Card,
    CardFace,
)
from sylvan_library.cards.models.colour import Colour
from sylvan_library.cards.models.user import UserProps


def _get_user_random(user: User) -> random.Random:
    """
    Gets a random generator seeded with the user's unused cards seed, so the same unused
    cards keep showing until the user rerolls the seed
    """
    if not hasattr(user, "userprops"):
        UserProps.add_to_user(user)
    return random.Random(user.userprops.unused_cards_seed)


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
    rand = _get_user_random(user)
    unused_cards = list(users_cards.exclude(id__in=users_deck_cards).order_by("id"))
    rand.shuffle(unused_cards)
    unused_cards = unused_cards[:25]
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
    rand = _get_user_random(user)
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
            .order_by("set__release_date", "-numerical_number")
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
        user_owned_cards.filter(faces__rules_text__regex="Partner(?!—)").exclude(
            faces__rules_text__contains="Partner with"
        )
    )
    background_cards = list(user_owned_cards.filter(faces__subtypes__name="Background"))
    choose_background_cards = list(
        user_owned_cards.filter(faces__rules_text__contains="Choose a Background")
    )

    rand = _get_user_random(user)
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
            partner_pairs.append(
                {
                    "partner_1": {
                        "card": partner_a,
                        "preferred_printing": partner_a.printings.filter(
                            localisations__ownerships__owner=user
                        )
                        .order_by("-set__release_date", "numerical_number")
                        .first(),
                    },
                    "partner_2": {
                        "card": partner_b,
                        "preferred_printing": partner_b.printings.filter(
                            localisations__ownerships__owner=user
                        )
                        .order_by("-set__release_date", "numerical_number")
                        .first(),
                    },
                }
            )

    background_pairs = [
        {
            "choose_background": {
                "card": choose_background_cards[x],
                "preferred_printing": choose_background_cards[x]
                .printings.filter(localisations__ownerships__owner=user)
                .order_by("-set__release_date", "numerical_number")
                .first(),
            },
            "background": {
                "card": background_cards[x],
                "preferred_printing": background_cards[x]
                .printings.filter(localisations__ownerships__owner=user)
                .order_by("-set__release_date", "numerical_number")
                .first(),
            },
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
