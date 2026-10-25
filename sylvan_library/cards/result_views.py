"""
API views for the tabs on a card search result
"""

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from sylvan_library.cards.links import get_card_links
from sylvan_library.cards.models.card import (
    Card,
    CardLocalisation,
    CardPrinting,
    UserCardChange,
    UserOwnedCard,
)
from sylvan_library.cards.models.decks import DeckCard
from sylvan_library.cards.models.language import Language


def _localisation_summary(localisation: CardLocalisation) -> dict:
    printing = localisation.card_printing
    return {
        "localisation_id": localisation.id,
        "language": localisation.language.name,
        "set_code": printing.set.code,
        "set_name": printing.set.name,
        "keyrune_code": printing.get_set_keyrune_code(),
        "rarity": printing.rarity.name,
        "number": printing.number,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def card_rulings(request: Request, card_id: int) -> Response:
    """
    Gets the rulings of a card
    """
    card = get_object_or_404(Card, pk=card_id)
    return Response(
        [
            {"date": ruling.date, "text": ruling.text}
            for ruling in card.rulings.order_by("date", "id")
        ]
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def printing_languages(request: Request, printing_id: int) -> Response:
    """
    Gets the localisations of a printing, English first
    """
    printing = get_object_or_404(CardPrinting, pk=printing_id)
    english_id = Language.english().id
    localisations = sorted(
        printing.localisations.select_related("language"),
        key=lambda l: (l.language_id != english_id, l.language.name),
    )
    return Response(
        [
            {
                "id": localisation.id,
                "language": localisation.language.name,
                "card_name": localisation.card_name,
            }
            for localisation in localisations
        ]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def card_ownership(request: Request, card_id: int) -> Response:
    """
    Gets the printings of a card the user owns, and their history of changes to it
    """
    card = get_object_or_404(Card, pk=card_id)
    related = (
        "card_localisation__language",
        "card_localisation__card_printing__set",
        "card_localisation__card_printing__rarity",
    )
    ownerships = (
        UserOwnedCard.objects.filter(owner=request.user)
        .filter(card_localisation__card_printing__card=card)
        .select_related(*related)
        .order_by("card_localisation__card_printing__set__release_date")
    )
    changes = (
        UserCardChange.objects.filter(owner=request.user)
        .filter(card_localisation__card_printing__card=card)
        .select_related(*related)
        .order_by("date")
    )
    return Response(
        {
            "card_name": card.name,
            "ownerships": [
                {
                    "count": ownership.count,
                    **_localisation_summary(ownership.card_localisation),
                }
                for ownership in ownerships
            ],
            "changes": [
                {
                    "date": change.date,
                    "difference": change.difference,
                    **_localisation_summary(change.card_localisation),
                }
                for change in changes
            ],
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_card_ownership(request: Request) -> Response:
    """
    Adds or removes a number of cards from the user's collection
    """
    try:
        count = int(request.data.get("count"))
        localisation_id = int(request.data.get("localisation"))
    except (TypeError, ValueError):
        return Response(
            {"detail": "count and localisation must be integers"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if count == 0:
        return Response(
            {"detail": "count can't be 0"}, status=status.HTTP_400_BAD_REQUEST
        )

    localisation = get_object_or_404(CardLocalisation, pk=localisation_id)
    with transaction.atomic():
        changed = localisation.apply_user_change(count, request.user)
    if not changed:
        # apply_user_change refuses to remove cards the user doesn't have
        return Response(
            {"detail": "You don't own any of that card to remove"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response({"result": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def card_decks(request: Request, card_id: int) -> Response:
    """
    Gets the user's decks that use a card
    """
    card = get_object_or_404(Card, pk=card_id)
    deck_cards = (
        DeckCard.objects.filter(deck__owner=request.user, card=card)
        .select_related("deck")
        .order_by("-deck__date_created")
    )
    totals = deck_cards.aggregate(card_count=Sum("count"), deck_count=Count("deck_id"))
    return Response(
        {
            "card_count": totals["card_count"] or 0,
            "deck_count": totals["deck_count"],
            "deck_cards": [
                {
                    "deck_id": deck_card.deck_id,
                    "deck_name": deck_card.deck.name,
                    "deck_subtitle": deck_card.deck.subtitle,
                    "date_created": deck_card.deck.date_created,
                    "count": deck_card.count,
                    "board": deck_card.board,
                    "board_display": deck_card.get_board_display(),
                }
                for deck_card in deck_cards
            ],
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def card_links(request: Request, card_id: int) -> Response:
    """
    Gets links to other sites for a card
    """
    card = get_object_or_404(Card, pk=card_id)
    return Response(get_card_links(card))


@api_view(["GET"])
@permission_classes([AllowAny])
def printing_prices(request: Request, printing_id: int) -> Response:
    """
    Gets the latest prices of a printing and its paper price history, foil and non-foil
    """
    printing = get_object_or_404(
        CardPrinting.objects.select_related("latest_price"), pk=printing_id
    )
    latest = printing.latest_price
    return Response(
        {
            "latest": (
                {
                    "date": latest.date,
                    "paper": latest.paper_value,
                    "paper_foil": latest.paper_foil_value,
                    "mtgo": latest.mtgo_value,
                    "mtgo_foil": latest.mtgo_foil_value,
                }
                if latest
                else None
            ),
            "paper_history": [
                {
                    "date": price.date,
                    "paper": price.paper_value,
                    "paper_foil": price.paper_foil_value,
                }
                for price in printing.prices.filter(
                    Q(paper_value__isnull=False) | Q(paper_foil_value__isnull=False)
                ).order_by("date")
            ],
        }
    )
