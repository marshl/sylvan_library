"""
API views for decks
"""

import random
from typing import Dict

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from django.db.models import Count, Q, QuerySet
from django.http import QueryDict
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from sylvan_library.cards.deck_serializers import (
    card_is_sideways,
    DeckCardChangeSerializer,
    DeckCheckSerializer,
    DeckDetailSerializer,
    DeckListSerializer,
    DeckWriteSerializer,
    owner_preferred_printing,
)
from sylvan_library.cards.deck_stats import (
    get_colour_info,
    get_unused_cards,
    get_unused_commanders,
    get_unused_partner_commanders,
)
from sylvan_library.cards.deck_text import (
    BOARDS,
    check_deck_text,
    validate_card_for_deck,
)
from sylvan_library.cards.models.card import Card
from sylvan_library.cards.models.colour import Colour
from sylvan_library.cards.models.decks import Deck, DeckCard
from sylvan_library.cards.models.rarity import Rarity
from sylvan_library.cards.models.user import UserProps
from sylvan_library.cards.serializers import (
    printing_back_image_url,
    printing_image_url,
)


def deck_card_counts(deck: Deck) -> dict:
    """
    The deck's name and board sizes, and how many of each card are in each board, keyed
    by card ID
    """
    cards: Dict[int, Dict[str, int]] = {}
    board_counts = {board: 0 for board in BOARDS}
    for card_id, board, count in deck.cards.values_list("card_id", "board", "count"):
        cards.setdefault(card_id, {})[board] = count
        board_counts[board] += count
    return {
        "id": deck.id,
        "name": deck.name,
        "is_prototype": deck.is_prototype,
        "board_counts": board_counts,
        "cards": cards,
    }


DECK_SORTS = {
    "newest": ("-date_created", "-last_modified", "-id"),
    "oldest": ("date_created", "last_modified", "id"),
    "name": ("name", "-date_created", "-id"),
}


class DeckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the current user's decks. The list can be filtered with:
    - q: text in the deck's name, subtitle or description
    - card: part of the name of a card in the deck, or its exact name if it starts
      with "!", like the card search
    - deck_format: the deck's format
    - year_from and year_to: the years the deck was created between
    - prototypes: "exclude" (the default), "include" or "only"
    - sort: "newest" (the default), "oldest" or "name"
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Deck.objects.filter(owner=self.request.user)
        if self.action == "list":
            queryset = self.filter_list(queryset, self.request.query_params)
        sort = self.request.query_params.get("sort")
        return queryset.order_by(*DECK_SORTS.get(sort, DECK_SORTS["newest"]))

    @staticmethod
    def filter_list(queryset: QuerySet, params: QueryDict) -> QuerySet:
        """
        Filters the deck list by the query params
        """
        if text := params.get("q", "").strip():
            queryset = queryset.filter(
                Q(name__icontains=text)
                | Q(subtitle__icontains=text)
                | Q(description__icontains=text)
            )
        if card := params.get("card", "").strip():
            if card.startswith("!"):
                deck_cards = DeckCard.objects.filter(
                    card__name__iexact=card[1:].strip()
                )
            else:
                deck_cards = DeckCard.objects.filter(card__name__icontains=card)
            queryset = queryset.filter(id__in=deck_cards.values("deck_id"))
        if deck_format := params.get("deck_format"):
            queryset = queryset.filter(format=deck_format)
        for param, lookup in (("year_from", "gte"), ("year_to", "lte")):
            try:
                year = int(params.get(param, ""))
            except ValueError:
                continue
            queryset = queryset.filter(**{f"date_created__year__{lookup}": year})

        prototypes = params.get("prototypes", "exclude")
        if prototypes == "only":
            queryset = queryset.filter(is_prototype=True)
        elif prototypes != "include":
            queryset = queryset.filter(is_prototype=False)
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

    @action(detail=False, methods=["post"])
    def check(self, request: Request) -> Response:
        """
        Checks the card text of a deck being edited without saving it: which lines
        can't be read, which were matched to a differently named card, how many cards
        each board has and which format rules the deck breaks
        """
        serializer = DeckCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            check_deck_text(
                serializer.validated_data["boards"],
                serializer.validated_data["format"],
                request.user,
            )
        )

    @action(detail=False)
    def formats(self, request: Request) -> Response:
        """
        The formats the user has decks in, most used first, for filtering the deck list
        """
        labels = dict(Deck.FORMAT_CHOICES)
        counts = (
            Deck.objects.filter(owner=request.user)
            .values("format")
            .annotate(count=Count("id"))
            .order_by("-count", "format")
        )
        return Response(
            [
                {
                    "value": row["format"],
                    "label": labels.get(row["format"], row["format"]),
                    "count": row["count"],
                }
                for row in counts
            ]
        )

    @action(detail=True, url_path="card-counts")
    def card_counts(self, request: Request, pk=None) -> Response:
        """
        How many of each card are in each of the deck's boards, for showing next to
        search results while the deck is being built
        """
        return Response(deck_card_counts(self.get_object()))

    @action(detail=True, methods=["post"])
    def cards(self, request: Request, pk=None) -> Response:
        """
        Adds copies of a card to one of the deck's boards, or takes them out, without
        checking the deck against its format. Returns the deck's new card counts.
        """
        deck: Deck = self.get_object()
        serializer = DeckCardChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = serializer.validated_data["card"]
        board = serializer.validated_data["board"]
        change = serializer.validated_data["change"]
        try:
            validate_card_for_deck(card)
        except DjangoValidationError as error:
            return Response(
                {"card": error.messages}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            deck_card = (
                deck.cards.select_for_update().filter(card=card, board=board).first()
            )
            if deck_card is None:
                if change > 0:
                    DeckCard.objects.create(
                        deck=deck, card=card, board=board, count=change
                    )
            elif deck_card.count + change > 0:
                deck_card.count += change
                deck_card.save()
            else:
                deck_card.delete()
            # Updates last_modified
            deck.save()
        return Response(deck_card_counts(deck))

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

    @action(detail=True, url_path="rarity-weights")
    def rarity_weights(self, request: Request, pk=None) -> Response:
        """
        The number of each rarity in the deck's cards
        """
        deck: Deck = self.get_object()
        rarities = {rarity.symbol: 0 for rarity in Rarity.objects.all()}
        for deck_card in deck.cards.exclude(card__faces__supertypes__name="Basic"):
            printing = owner_preferred_printing(deck_card)
            if printing is None:
                printing = deck_card.card.printings.first()
            rarities[printing.rarity.symbol] += deck_card.count

        colours = {
            "C": "#D8D0CD",
            "U": "#707883",
            "R": "#a58e4a",
            "M": "#bf4427",
        }

        return Response(
            [
                {
                    "symbol": rarity.symbol,
                    "count": rarities.get(rarity.symbol, 0),
                    "name": rarity.name,
                    "chart_colour": colours.get(rarity.symbol, None),
                }
                for rarity in Rarity.objects.order_by("display_order").all()
                if rarities.get(rarity.symbol)
            ]
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
        "back_image_url": printing_back_image_url(entry["preferred_printing"]),
        "sideways": card_is_sideways(entry["card"]),
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
