"""
Models for deck objects
"""

import re
from collections import defaultdict
from typing import List, Dict

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Avg, Q
from django.contrib.auth import get_user_model

from cards.models.card import Card, CardType
from cards.models.colour import Colour
from cards.models.rarity import Rarity


class Deck(models.Model):
    """
    Model for a user owned deck of cards
    """

    FORMAT_CHOICES = (
        ("standard", "Standard"),
        ("legacy", "Legacy"),
        ("prerelease", "Pre-release"),
        ("mtgo", "MTGO"),
        ("unformat", "Unformat"),
        ("unknown", "Unknown"),
        ("heirloom", "Heirloom"),
        ("vintage", "Vintage"),
        ("edh", "Commander / EDH"),
        ("archenemy", "Archenemy"),
        ("planechase", "Planechase"),
        ("vanguard", "Vanguard"),
        ("modern", "Modern"),
        ("pauper", "Pauper"),
        ("noble", "Noble"),
        ("casual", "Casual"),
        ("hero", "Hero"),
        ("quest_magic_rpg", "Quest Magic RPGs"),
        ("quest_magic", "Quest Magic"),
        ("block_constructed", "Block Constructed"),
        ("limited", "Limited"),
        ("duel_commander", "Duel Commander"),
        ("tiny_leaders", "Tiny Leaders"),
        ("highlander", "Highlander"),
        ("magic_duels", "Magic Duels"),
        ("penny_dreadful", "Penny Dreadful"),
        ("frontier", "Frontier"),
        ("leviathan", "Leviathan"),
        ("1v1_commander", "1v1 Commander"),
        ("pauper_edh", "Pauper EDH"),
        ("canadian_highlander", "Canadian Highlander"),
        ("brawl", "Brawl"),
        ("arena", "Arena"),
        ("oathbreaker", "Oathbreaker"),
    )

    date_created = models.DateField()
    last_modified = models.DateField(auto_now=True)
    name = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        get_user_model(), related_name="decks", on_delete=models.CASCADE
    )
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES)
    exclude_colours = models.ManyToManyField(
        Colour, related_name="exclude_from_decks", blank=True
    )
    is_prototype = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    def get_cards(self, board: str) -> List["DeckCard"]:
        """
        Gets the cards in the given board
        :param board: The board to get the cards for
        :return: The cards in that board
        """
        return self.cards.filter(board=board)

    def get_sideboard(self) -> List["DeckCard"]:
        """
        Gets all the cards that are in the sideboard
        :return:
        """
        return self.get_cards("side")

    def get_total_land_count(self) -> int:
        """
        Gets the total number of lands in this deck including modal dual-faced cards
        :return: The total number of lands as an int
        """
        main_cards = self.cards.filter(board="main")
        land_cards = (
            main_cards.filter(card__faces__types__name="Land")
            .filter(
                Q(card__faces__side__isnull=True)
                | Q(card__faces__side="a")
                | Q(card__layout="modal_dfc")
            )
            .distinct()
        )
        return int(land_cards.aggregate(sum=Sum("count"))["sum"])

    def get_card_groups(self) -> List[dict]:
        """
        Gets the cards in this deck divided into type groups
        :return: A dict of the names of the groups to the groups of cards
        """
        board_cards = list(self.cards.filter(board="main"))
        groups = defaultdict(list)
        for deck_card in board_cards:
            if deck_card.is_commander:
                groups["commander"].append(deck_card)
                continue

            first_face_types = [
                _type.name for _type in deck_card.card.faces.first().types.all()
            ]

            if "Land" in first_face_types:
                groups["land"].append(deck_card)
                continue

            if "Creature" in first_face_types:
                groups["creature"].append(deck_card)
                continue

            if "Instant" in first_face_types:
                groups["instant"].append(deck_card)
                continue

            if "Sorcery" in first_face_types:
                groups["sorcery"].append(deck_card)
                continue

            if "Enchantment" in first_face_types:
                groups["enchantment"].append(deck_card)
                continue

            if "Artifact" in first_face_types:
                groups["artifact"].append(deck_card)
                continue

            if "Planeswalker" in first_face_types:
                groups["planeswalker"].append(deck_card)
                continue

            if "Battle" in first_face_types:
                groups["battle"].append(deck_card)
                continue

            groups["other"].append(deck_card)

        return [
            {
                "name": (
                    "Commander"
                    if len(groups.get("commander", [])) == 1
                    else "Commanders"
                ),
                "code": "commander",
                "cards": groups.get("commander", []),
            },
            {"name": "Lands", "cards": groups.get("land", []), "code": "land"},
            {
                "name": (
                    "Creature" if len(groups.get("creature", [])) == 1 else "Creatures"
                ),
                "code": "creature",
                "cards": groups.get("creature", []),
            },
            {
                "name": (
                    "Instant" if len(groups.get("instant", [])) == 1 else "Instants"
                ),
                "code": "instant",
                "cards": groups.get("instant", []),
            },
            {
                "name": (
                    "Sorcery" if len(groups.get("sorcery", [])) == 1 else "Sorceries"
                ),
                "code": "sorcery",
                "cards": groups.get("sorcery", []),
            },
            {
                "name": (
                    "Artifact" if len(groups.get("artifact", [])) == 1 else "Artifacts"
                ),
                "code": "artifact",
                "cards": groups.get("artifact", []),
            },
            {
                "name": (
                    "Enchantment"
                    if len(groups.get("enchantment", [])) == 1
                    else "Enchantments"
                ),
                "code": "enchantment",
                "cards": groups.get("enchantment", []),
            },
            {
                "name": (
                    "Planeswalker"
                    if len(groups.get("planeswalker", [])) == 1
                    else "Planeswalkers"
                ),
                "code": "planeswalker",
                "cards": groups.get("planeswalker", []),
            },
            {
                "name": "Battle" if len(groups.get("battle", [])) == 1 else "Battles",
                "code": "battle",
                "cards": groups.get("battle", []),
            },
            {"name": "Other", "cards": groups.get("other", []), "code": "other"},
        ]

    def get_land_symbol_counts(self) -> Dict[str, int]:
        """
        Gets a list of the number of each coloured mana symbol that lands in this deck can add
        :return: A list of counts from white  to colourless (colorus without any symbols will still
        be included)
        """
        land_type = CardType.objects.get(name="Land")
        deck_cards = list(
            self.cards.filter(board="main").prefetch_related("card__faces__types")
        )
        result = {}
        for colour in Colour.objects.exclude(
            id__in=self.exclude_colours.all()
        ).order_by("display_order"):
            symbol_regex = ":.*?add[^\n]*?{" + colour.symbol + "}"
            count = sum(
                [
                    deck_card.count
                    for deck_card in deck_cards
                    for card_face in deck_card.card.faces.all()
                    for card_type in card_face.types.all()
                    if card_face.rules_text
                    and card_type == land_type
                    and re.search(symbol_regex, card_face.rules_text, re.IGNORECASE)
                ]
            )
            if count > 0:
                result[colour.symbol] = count

        return result

    def get_cost_symbol_counts(self) -> Dict[str, int]:
        """
        Gets a list of the number of each coloured mana symbol in costs of cards in the deck
        :return: A list of counts from white to colourless (colorus without any symbols will still
        be included)
        """
        deck_cards = list(
            self.cards.filter(board="main").prefetch_related("card__faces")
        )
        result = {}
        for colour in Colour.objects.exclude(
            id__in=self.exclude_colours.all()
        ).order_by("display_order"):
            count = sum(
                card_face.mana_cost.count(colour.symbol) * deck_card.count
                for deck_card in deck_cards
                for card_face in deck_card.card.faces.all()
                if card_face.mana_cost
            )
            if count > 0:
                result[colour.symbol] = count

        colourless_count = sum(
            deck_card.count
            for deck_card in deck_cards
            if deck_card.card.faces.first().mana_cost
            and not any(
                colour.symbol in deck_card.card.faces.first().mana_cost
                for colour in Colour.objects.all()
            )
        )
        if colourless_count > 0:
            result[Colour.colourless().symbol] = colourless_count

        return result

    def deck_avg_mana_value(self) -> float:
        """
        Gets the average mana value of non-land cards in the deck
        :return: The average mana value
        """
        return (
            self.cards.filter(board="main")
            .exclude(card__type__contains="Land")
            .aggregate(Avg("card__cmd"))["card__mana_value__avg"]
        )

    def get_mainboard_count(self) -> int:
        """
        Gets the total number of cards in tbe mainboard
        :return: The number of cards
        """
        return self.get_card_count("main")

    def get_card_count(self, board: str = None) -> int:
        """
        Gets the total number of cards in the deck for the given board
        :param board: if specified, only the cards in that board will be counted,
                      otherwise all cards will be
        :return: The total card count in the given board
        """
        if board:
            return sum(
                deck_card.count for deck_card in self.cards.filter(board=board).all()
            )

        return sum(deck_card.count for deck_card in self.cards.all())

    def validate_format(self):
        """
        Validates that this deck passes the restrictions set by its format
        :return:
        """
        if self.format in ("edh", "dual_commander", "1v1_commander"):
            self.validate_card_limit(1)
            self.validate_commander("Legendary")
            self.validate_size(100)
            self.validate_board_limit("side", 0)

        if self.format in ("highlander",):
            self.validate_card_limit(1)
            self.validate_size(100)

        if self.format == "brawl":
            self.validate_card_limit(1)
            self.validate_size(60)
            self.validate_commander("Legendary")

        if self.format in (
            "standard",
            "legacy",
            "mtgo",
            "vintage",
            "planechase",
            "modern",
        ):
            self.validate_card_limit(4)
            self.validate_size(60)
            self.validate_board_limit("side", 15)

        if self.format in ("pauper",):
            self.validate_rarities(Rarity.objects.filter(symbol="C").all())

    def validate_card_limit(self, limit: int) -> None:
        """
        Validates that this deck doesn't have any cards more than the given limit
        :param limit: The card limit (4 for standard, 1 for EDH etc)
        """
        # We can exclude basic land and cards that you can have any number of (i.e. Relentless Rats)
        overcount_cards = (
            self.cards.exclude(count__lte=limit)
            .exclude(card__faces__supertypes__name="Basic")
            .exclude(
                card__faces__rules_text__icontains="A deck can have any number of cards named"
            )
        )
        if overcount_cards.exists():
            raise ValidationError(
                f"You have over {limit} of the following cards: "
                f"{', '.join(c.card.name for c in overcount_cards)}"
            )

    def validate_commander(self, validate_type: str) -> None:
        """
        Validates that this deck has a commander card
        :param validate_type: The card type that the commander should be
        """
        assert self.format in ("edh",)

        commanders = self.cards.filter(is_commander=True)
        if not commanders.exists():
            raise ValidationError("A commander deck should have at least one commander")

        if commanders.count() != 1:
            both_have_partner = (
                commanders.filter(card__faces__rules_text__icontains="partner").count()
                == 2
            )
            is_background_pair = (
                commanders.filter(
                    card__faces__rules_text__contains="Choose a Background"
                ).exists()
                and commanders.filter(card__faces__subtypes__name="Background").exists()
            )
            if not both_have_partner and not is_background_pair:
                raise ValidationError(
                    "A commander deck can only have multiple commanders if they have partner "
                    "or if they are a background pair"
                )

        if validate_type:
            if commanders.exclude(card__faces__supertypes__name=validate_type).exists():
                raise ValidationError(
                    "A commander deck should have a legend as the commander"
                )

    def validate_size(self, minimum_count: int) -> None:
        """
        Validates that this deck has at leas the given number of cards
        :param minimum_count: The minimum number of cards (60 for standard, 100 for highlander etc)
        """
        card_count = self.get_card_count("main")
        if card_count < minimum_count:
            raise ValidationError(
                f"Not enough cards for a {self.get_format_display()} "
                f"deck ({card_count}/{minimum_count})"
            )

    def validate_board_limit(self, board: str, max_count: int) -> None:
        """
        Validates that the deck doesn't haven't more than the given number of cards in the board
        :param board: The board to check (side, main etc)
        :param max_count: The maximum number of cards that can be in that board
        """
        card_count = self.get_card_count(board)
        if card_count > max_count:
            raise ValidationError(
                f"A {self.get_format_display()} deck can't have more than "
                f"{max_count} cards in the {board}board."
                if max_count > 0
                else f"A {self.get_format_display()} deck can't have any cards in the {board}board"
            )

    def validate_rarities(self, allowed_rarities: List[Rarity]) -> None:
        """
        Validates that the deck doesn't contain any cards that aren't of the given rarities
        :param allowed_rarities: The list of rarties that are allowed in the deck
        """
        disallowed_cards = self.cards.exclude(
            card__printings__rarity__id__in=allowed_rarities
        )
        if disallowed_cards.exists():
            raise ValidationError(
                f"A {self.get_format_display()} deck should only have "
                + ", ".join(r.name for r in allowed_rarities)
            )


class DeckCard(models.Model):
    """
    Model for a card in a Deck
    """

    BOARD_CHOICES = (
        ("main", "Main"),
        ("side", "Side"),
        ("maybe", "Maybe"),
        ("acquire", "Acquire"),
    )

    count = models.IntegerField()
    card = models.ForeignKey(Card, related_name="deck_cards", on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, related_name="cards", on_delete=models.CASCADE)
    board = models.CharField(max_length=20, choices=BOARD_CHOICES, default="main")
    is_commander = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.card} in {self.deck}"

    class Meta:
        """
        Metaclass for DeckCard
        """

        ordering = ["card__name"]

    def as_deck_text(self) -> str:
        """
        Converts this card to how it should appear in board text of the DeckForm
        :return: The text representation version of the card for use in the DeckForm
        """

        result = f"{self.count} {self.card.name}"
        if self.is_commander:
            result += " *CMDR*"
        return result

    @property
    def is_companion(self) -> bool:
        """
        Gets whether this card is a companion for the deck
        :return: A boolean
        """
        return (
            self.board == "side"
            and self.card.faces.filter(rules_text__contains="Companion — ").exists()
        )
