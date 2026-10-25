"""
Serializers for decks
"""

from typing import List, Optional

from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.settings import api_settings

from sylvan_library.cards.deck_text import BOARDS, get_board_text, get_deck_cards
from sylvan_library.cards.models.card import Card, CardPrinting
from sylvan_library.cards.models.colour import Colour
from sylvan_library.cards.models.decks import Deck, DeckCard
from sylvan_library.cards.serializers import (
    printing_back_image_url,
    printing_image_url,
)


def owner_preferred_printing(deck_card: DeckCard) -> Optional[CardPrinting]:
    """
    The latest printing of a card the deck owner owned when the deck was made,
    falling back to the card's latest printing
    """
    owned = (
        deck_card.card.printings.filter(
            localisations__ownerships__owner=deck_card.deck.owner,
            set__release_date__lte=deck_card.deck.date_created,
        )
        .order_by("set__release_date")
        .last()
    )
    return owned or deck_card.card.printings.order_by("set__release_date").last()


def card_is_sideways(card: Card) -> bool:
    """
    Whether the front of a card is printed sideways: split cards (including rooms),
    planes, phenomena and battles. Aftermath and flip cards are only partly turned, so
    they count as upright.
    """
    if card.layout in ("split", "planar"):
        return True
    front = card.faces.order_by("side").first()
    return front is not None and front.types.filter(name="Battle").exists()


def deck_card_icon(deck_card: DeckCard) -> Optional[str]:
    """
    The mana-font icon shown next to some deck cards (companions, MDFC lands etc.)
    """
    card = deck_card.card
    if deck_card.is_companion:
        return "ability-companion"
    if card.layout == "modal_dfc" and card.is_land():
        return "land"
    if card.layout == "adventure":
        return "ability-adventure"
    if card.layout == "transform" and card.is_land():
        return "dfc-enchantment"
    return None


class DeckCardSerializer(serializers.ModelSerializer):
    """
    A card in a deck, with what's needed to show it in a deck list
    """

    card_id = serializers.IntegerField(source="card.id")
    card_name = serializers.CharField(source="card.name")
    layout = serializers.CharField(source="card.layout")
    side = SerializerMethodField()
    icon = SerializerMethodField()
    image_url = SerializerMethodField()
    back_image_url = SerializerMethodField()
    sideways = SerializerMethodField()

    class Meta:
        model = DeckCard
        fields = (
            "id",
            "count",
            "board",
            "is_commander",
            "card_id",
            "card_name",
            "layout",
            "side",
            "icon",
            "image_url",
            "back_image_url",
            "sideways",
        )

    def get_side(self, obj: DeckCard) -> Optional[str]:
        face = obj.card.faces.first()
        return face.side if face else None

    def get_icon(self, obj: DeckCard) -> Optional[str]:
        return deck_card_icon(obj)

    def preferred_printing(self, obj: DeckCard) -> Optional[CardPrinting]:
        """
        The printing to show for a deck card, looked up once for both of its images
        """
        cache = self.__dict__.setdefault("_preferred_printings", {})
        if obj.id not in cache:
            cache[obj.id] = owner_preferred_printing(obj)
        return cache[obj.id]

    def get_image_url(self, obj: DeckCard) -> str:
        return printing_image_url(self.preferred_printing(obj))

    def get_back_image_url(self, obj: DeckCard) -> Optional[str]:
        return printing_back_image_url(self.preferred_printing(obj))

    def get_sideways(self, obj: DeckCard) -> bool:
        return card_is_sideways(obj.card)


class DeckListSerializer(serializers.ModelSerializer):
    """
    The summary of a deck shown in the deck list
    """

    class Meta:
        model = Deck
        fields = (
            "id",
            "name",
            "subtitle",
            "description",
            "date_created",
            "format",
            "is_prototype",
            "is_private",
        )


class DeckDetailSerializer(serializers.ModelSerializer):
    """
    A deck with its cards grouped by type, and the text of each board for editing
    """

    format_display = serializers.CharField(source="get_format_display")
    card_groups = SerializerMethodField()
    sideboard = SerializerMethodField()
    mainboard_count = serializers.IntegerField(source="get_mainboard_count")
    total_land_count = SerializerMethodField()
    boards = SerializerMethodField()

    class Meta:
        model = Deck
        fields = (
            "id",
            "name",
            "subtitle",
            "description",
            "date_created",
            "last_modified",
            "format",
            "format_display",
            "exclude_colours",
            "is_prototype",
            "is_private",
            "card_groups",
            "sideboard",
            "mainboard_count",
            "total_land_count",
            "boards",
        )

    def get_card_groups(self, obj: Deck) -> List[dict]:
        return [
            {
                "name": group["name"],
                "code": group["code"],
                "count": sum(card.count for card in group["cards"]),
                "cards": DeckCardSerializer(group["cards"], many=True).data,
            }
            for group in obj.get_card_groups()
            if group["cards"]
        ]

    def get_sideboard(self, obj: Deck) -> List[dict]:
        return DeckCardSerializer(
            obj.get_cards("side").order_by("card__name"), many=True
        ).data

    def get_total_land_count(self, obj: Deck) -> int:
        # get_total_land_count sums None when there are no lands
        try:
            return obj.get_total_land_count()
        except TypeError:
            return 0

    def get_boards(self, obj: Deck) -> dict:
        return get_board_text(obj)


class DeckWriteSerializer(serializers.ModelSerializer):
    """
    Creates or updates a deck from its fields and the text of each of its boards.
    Unless skip_validation is set or the deck is a prototype, the deck is also checked
    against the rules of its format, and nothing is saved if that fails.
    """

    exclude_colours = serializers.PrimaryKeyRelatedField(
        queryset=Colour.objects.all(), many=True, required=False
    )
    boards = serializers.DictField(child=serializers.CharField(allow_blank=True))
    skip_validation = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = Deck
        fields = (
            "id",
            "date_created",
            "name",
            "subtitle",
            "format",
            "exclude_colours",
            "description",
            "is_prototype",
            "is_private",
            "boards",
            "skip_validation",
        )

    def validate_boards(self, boards: dict) -> dict:
        unknown = set(boards) - set(BOARDS)
        if unknown:
            raise serializers.ValidationError(
                f"Unknown boards: {', '.join(sorted(unknown))}"
            )
        return boards

    def save(self, **kwargs) -> Deck:
        data = {**self.validated_data, **kwargs}
        boards = data.pop("boards")
        skip_validation = data.pop("skip_validation")
        exclude_colours = data.pop("exclude_colours", None)

        deck = self.instance or Deck()
        for field, value in data.items():
            setattr(deck, field, value)

        try:
            deck.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {
                    (
                        api_settings.NON_FIELD_ERRORS_KEY
                        if field == NON_FIELD_ERRORS
                        else field
                    ): messages
                    for field, messages in error.message_dict.items()
                }
            ) from error

        try:
            with transaction.atomic():
                deck.save()
                if exclude_colours is not None:
                    deck.exclude_colours.set(exclude_colours)
                deck.cards.all().delete()
                for deck_card in get_deck_cards(boards, deck):
                    deck_card.full_clean()
                    deck_card.save()
                if not skip_validation and not deck.is_prototype:
                    deck.validate_format()
        except DjangoValidationError as error:
            if self.instance is None:
                # The rolled back insert still set an ID on the unsaved deck
                deck.id = None
            raise serializers.ValidationError({"cards": error.messages}) from error

        self.instance = deck
        return deck
