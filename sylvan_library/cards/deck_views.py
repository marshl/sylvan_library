"""
API views for decks
"""

import random

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from sylvan_library.cards.deck_serializers import (
    DeckDetailSerializer,
    DeckListSerializer,
    DeckWriteSerializer,
)
from sylvan_library.cards.deck_stats import (
    get_colour_info,
    get_unused_cards,
    get_unused_commanders,
    get_unused_partner_commanders,
)
from sylvan_library.cards.models.card import Card
from sylvan_library.cards.models.colour import Colour
from sylvan_library.cards.models.decks import Deck
from sylvan_library.cards.models.user import UserProps
from sylvan_library.cards.serializers import printing_image_url


class DeckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the current user's decks. The list can be filtered with
    ?is_prototype=true or false.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Deck.objects.filter(owner=self.request.user).order_by(
            "-date_created", "-last_modified", "-id"
        )
        is_prototype = self.request.query_params.get("is_prototype")
        if self.action == "list" and is_prototype in ("true", "false"):
            queryset = queryset.filter(is_prototype=is_prototype == "true")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return DeckListSerializer
        if self.action in ("create", "update", "partial_update"):
            return DeckWriteSerializer
        return DeckDetailSerializer

    def perform_create(self, serializer: DeckWriteSerializer) -> None:
        serializer.save(owner=self.request.user)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"id": serializer.instance.id}, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"id": serializer.instance.id})

    @action(detail=True, url_path="colour-weights")
    def colour_weights(self, request: Request, pk=None) -> Response:
        """
        The number of each coloured mana symbol in the costs of the deck's cards, and
        how many of the deck's lands can make each colour
        """
        deck = self.get_object()
        colours = get_colour_info()
        return Response(
            {
                key: [
                    {"count": count, **colours[symbol]}
                    for symbol, count in counts.items()
                ]
                for key, counts in (
                    ("mana_symbols", deck.get_cost_symbol_counts()),
                    ("land_symbols", deck.get_land_symbol_counts()),
                )
            }
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def deck_options(request: Request) -> Response:
    """
    The choices for the format and excluded colours fields on the deck form
    """
    return Response(
        {
            "formats": [
                {"value": value, "label": label} for value, label in Deck.FORMAT_CHOICES
            ],
            "colours": [
                {"id": colour.id, "name": colour.name, "symbol": colour.symbol}
                for colour in Colour.objects.order_by("display_order")
            ],
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def card_names(request: Request) -> Response:
    """
    Card names containing ?q, for autocompleting cards on the deck form. Names that
    start with the query come first.
    """
    query = request.query_params.get("q", "").strip()
    if len(query) < 2:
        return Response([])
    names = Card.objects.filter(name__icontains=query, is_token=False).values_list(
        "name", flat=True
    )
    lowered = query.lower()
    names = sorted(
        set(names),
        key=lambda name: (not name.lower().startswith(lowered), name.lower()),
    )
    return Response(names[:10])


def _stats_card(entry: dict) -> dict:
    return {
        "card_id": entry["card"].id,
        "name": entry["card"].name,
        "image_url": printing_image_url(entry["preferred_printing"]),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def deck_stats(request: Request) -> Response:
    """
    Some cards the user owns but has never put in a deck, and unused commander pairings
    """
    partner_pairs, background_pairs = get_unused_partner_commanders(request.user)
    return Response(
        {
            "deck_count": Deck.objects.filter(owner=request.user).count(),
            "unused_cards": [_stats_card(e) for e in get_unused_cards(request.user)],
            "unused_commanders": [
                _stats_card(e) for e in get_unused_commanders(request.user)
            ],
            "partner_pairs": [
                [_stats_card(pair["partner_1"]), _stats_card(pair["partner_2"])]
                for pair in partner_pairs
            ],
            "background_pairs": [
                [
                    _stats_card(pair["choose_background"]),
                    _stats_card(pair["background"]),
                ]
                for pair in background_pairs
            ],
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reroll_deck_stats(request: Request) -> Response:
    """
    Picks a different random set of unused cards for the deck stats
    """
    if not hasattr(request.user, "userprops"):
        UserProps.add_to_user(request.user)
    props = request.user.userprops
    props.unused_cards_seed = random.randint(
        0, abs(UserProps._meta.get_field("unused_cards_seed").validators[0].limit_value)
    )
    props.full_clean()
    props.save()
    return Response(status=status.HTTP_204_NO_CONTENT)
