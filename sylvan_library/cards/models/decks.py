"""
Models for deck objects
"""

from typing import List, Dict

from django.db import models
from django.db.models import Sum, Avg
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from cards.models.card import Card
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
    owner = models.ForeignKey(User, related_name="decks", on_delete=models.CASCADE)
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES)
    exclude_colours = models.ManyToManyField(
        Colour, related_name="exclude_from_decks", blank=True
    )
    is_prototype = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_cards(self, board: str) -> List["DeckCard"]:
        """
        Gets the cards in the given board
        :param board: The board to get the cards for
        :return: The cards in that board
        """
        return self.cards.filter(board=board).order_by("card__name")

    def get_sideboard(self) -> List["DeckCard"]:
        """
        Gets all the cards that are in the sideboard
        :return:
        """
        return self.get_cards("side")

    def get_card_groups(self) -> Dict[str, List["DeckCard"]]:
        """
        Gets the cards in this deck divided into type groups
        :return: A dict of the names of the groups to the groups of cards
        """
        board_cards = self.cards.filter(board="main").order_by("card__name")
        commanders = board_cards.filter(is_commander=True)
        lands = board_cards.filter(card__type__contains="Land")
        creatures = board_cards.exclude(id__in=lands | commanders).filter(
            card__type__contains="Creature"
        )
        instants = board_cards.filter(card__type__contains="Instant")
        sorceries = board_cards.filter(card__type__contains="Sorcery")
        enchantments = board_cards.exclude(id__in=lands | creatures).filter(
            card__type__contains="Enchantment"
        )
        artifacts = board_cards.exclude(id__in=lands | creatures | enchantments).filter(
            card__type__contains="Artifact"
        )
        planeswalkers = board_cards.filter(card__type__contains="Planeswalker").exclude(
            id__in=commanders
        )
        other = board_cards.exclude(
            id__in=commanders
            | lands
            | creatures
            | instants
            | sorceries
            | artifacts
            | enchantments
            | planeswalkers
        )

        return {
            "Commander": commanders,
            "Land": lands,
            "Creature": creatures,
            "Instant": instants,
            "Sorcery": sorceries,
            "Artifact": artifacts,
            "Enchantment": enchantments,
            "Planeswalker": planeswalkers,
            "Other": other,
        }

    def get_land_symbol_counts(self) -> Dict[str, int]:
        """
        Gets a list of the number of each coloured mana symbol that lands in this deck can add
        :return: A list of counts from white  to colourless (colorus without any symbols will still
        be included)
        """
        land_cards = self.cards.filter(board="main", card__type__contains="Land")
        result = {}
        for colour in Colour.objects.exclude(
            id__in=self.exclude_colours.all()
        ).order_by("display_order"):
            count = (
                land_cards.filter(
                    card__rules_text__iregex=":.*?add[^\n]*?{" + colour.symbol + "}"
                ).aggregate(sum=Sum("count"))["sum"]
                or 0
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
        cards = self.cards.filter(board="main", card__cost__isnull=False)
        result = {}
        for colour in Colour.objects.exclude(
            id__in=self.exclude_colours.all()
        ).order_by("display_order"):
            count = sum(
                deck_card.card.cost.count(colour.symbol) * deck_card.count
                for deck_card in cards
            )
            if count > 0:
                result[colour.symbol] = count
        return result

    def deck_avg_cmc(self) -> float:
        """
        Gets the average converted mana cost of non-land cards in the deck
        :return: The average converted mana cost
        """
        return (
            self.cards.filter(board="main")
            .exclude(card__type__contains="Land")
            .aggregate(Avg("card__cmd"))["card__cmc__avg"]
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
            self.validate_commander("Legend")
            self.validate_size(100)
            self.validate_board_limit("side", 0)

        if self.format in ("highlander",):
            self.validate_card_limit(1)
            self.validate_size(100)

        if self.format == "brawl":
            self.validate_card_limit(1)
            self.validate_size(60)
            self.validate_commander("Legend")

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
            .exclude(card__type__contains="Basic")
            .exclude(
                card__rules_text__icontains="A deck can have any number of cards named"
            )
        )
        if overcount_cards.exists():
            raise ValidationError(
                "You have over {} of the following cards: {}".format(
                    limit, ", ".join(c.card.name for c in overcount_cards)
                )
            )

    def validate_commander(self, validate_type: str) -> None:
        """
        Validates that this deck has a commander card
        :param validate_type: The card type that the commander should be
        """
        assert self.format in ("edh",)

        commanders = self.cards.filter(is_commander=True)
        if not commanders.exists():
            raise ValidationError(
                f"A commander deck should have at least one commander"
            )

        if commanders.count() != 1:
            if commanders.exclude(card__rules_text__icontains="partner").exists():
                raise ValidationError(
                    f"A commander deck can only have multiple commanders if they have partner"
                )

        if validate_type:
            if commanders.exclude(card__type__contains=validate_type).exists():
                raise ValidationError(
                    f"A command deck should have a legend as the commander"
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

    def get_card_name(self) -> str:
        """
        Gets the name of the card. For most cards this will be the same as the name of the card,
        but split cards combine the names of both halves together
        :return:  The display name of the card
        """
        if self.card.layout == "split":
            return " // ".join(c.name for c in self.card.get_all_sides())
        return self.card.name

    def as_deck_text(self) -> str:
        """
        COnverts this card to how it should appear in board text of the DeckForm
        :return: The text representation version of the card for use in the DeckForm
        """

        result = f"{self.count}x {self.get_card_name()}"
        if self.is_commander:
            result += " *CMDR*"
        return result
