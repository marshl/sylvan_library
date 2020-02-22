"""
Module for Card related models
"""
import random
from typing import List, Optional
import datetime
import os
import re

from django.db import models
from django.db.models import Sum, IntegerField, Case, When
from django.contrib.auth.models import User
from bitfield import BitField

from cards.models.sets import Set
from cards.models.rarity import Rarity


CARD_LAYOUT_CHOICES = (
    ("normal", "Normal"),
    ("split", "Split"),
    ("flip", "Flip"),
    ("transform", "Transform"),
    ("token", "Token"),
    ("planar", "Planar"),
    ("scheme", "Scheme"),
    ("leveler", "Leveler"),
    ("vanguard", "Vanguard"),
    ("meld", "Meld"),
    ("host", "Host"),
    ("augment", "Augment"),
    ("saga", "Saga"),
    ("emblem", "Emblem"),
    ("double_faced_token", "Double-faced Token"),
    ("aftermath", "Aftermath"),
    ("adventure", "Adventure"),
)


# pylint: disable=too-many-instance-attributes
class Card(models.Model):
    """
    Model for a unique card
    """

    name: str = models.CharField(max_length=200, unique=True)
    display_name: str = models.CharField(max_length=200)

    cost: str = models.CharField(max_length=50, blank=True, null=True)
    cmc: float = models.FloatField()
    face_cmc: float = models.FloatField(blank=True, null=True)
    colour_flags: BitField = BitField(flags=("white", "blue", "black", "red", "green"))
    colour_identity_flags: int = BitField(
        flags=("white", "blue", "black", "red", "green")
    )
    colour_indicator_flags: int = BitField(
        flags=("white", "blue", "black", "red", "green")
    )
    colour_count: int = models.IntegerField()
    colour_identity_count: int = models.IntegerField()
    colour_sort_key: int = models.IntegerField()
    colour_weight: int = models.IntegerField()

    type: str = models.CharField(max_length=100, blank=True, null=True)
    subtype: str = models.CharField(max_length=100, blank=True, null=True)

    power: str = models.CharField(max_length=20, blank=True, null=True)
    num_power: int = models.FloatField(default=0)
    toughness: str = models.CharField(max_length=20, blank=True, null=True)
    num_toughness: int = models.FloatField(default=0)
    loyalty: str = models.CharField(max_length=20, blank=True, null=True)
    num_loyalty: int = models.FloatField(default=0)

    rules_text: str = models.CharField(max_length=1000, blank=True, null=True)
    layout: str = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)
    side: str = models.CharField(max_length=1, blank=True, null=True)

    hand_modifier: str = models.CharField(max_length=10, blank=True, null=True)
    num_hand_modifier: int = models.IntegerField(default=0)
    life_modifier: str = models.CharField(max_length=10, blank=True, null=True)
    num_life_modifier: int = models.IntegerField(default=0)

    is_reserved: bool = models.BooleanField(default=False)
    scryfall_oracle_id: int = models.CharField(max_length=36, blank=True, null=True)
    # Card rank on EDHRec.
    edh_rec_rank: int = models.IntegerField(default=0)
    is_token: bool = models.BooleanField(default=False)
    links: List["Card"] = models.ManyToManyField("self")

    @staticmethod
    def get_random_card() -> "Card":
        """
        Gets a card chosen at random
        :return:
        """
        last = Card.objects.count() - 1
        index = random.randint(0, last)
        return Card.objects.all()[index]

    def __str__(self):
        return self.name

    def get_user_ownership_count(self, user: User, prefetched: bool = False) -> int:
        """
        Returns the total number of cards that given user owns of this card
        :param prefetched: Whether to use prefetched data, or to get it from the database again
        :param user: The user who should own the card
        :return: The ownership total
        """
        if prefetched:
            return sum(
                ownership.count
                for card_printing in self.printings.all()
                for printed_language in card_printing.printed_languages.all()
                for physical_card in printed_language.physical_cards.all()
                for ownership in physical_card.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.printings.aggregate(
            card_count=Sum(
                Case(
                    When(
                        printed_languages__physical_cards__ownerships__owner=user,
                        then="printed_languages__physical_cards__ownerships__count",
                    ),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )["card_count"]

    def get_all_sides(self, sort: bool = False) -> List["Card"]:
        """
        Gets a list of all the sides of this card, including the front
        :return: A list of all the sides in side order
        """
        results = Card.objects.filter(pk=self.id) | self.links.order_by("side")
        if sort:
            return results.order_by("side")
        return results

    def get_linked_name(self, delimiter: str = " / "):
        """
        Gets all the names of this card joined together with the given delimiter
        :return: THe names of this card joined together (.e.g Assault / Battery)
        """
        return delimiter.join(s.display_name for s in self.get_all_sides(sort=True))

    @property
    def is_wide(self) -> bool:
        """
        Returns whether or not this is an oversized cardd
        :return: True if this is an oversized card, otherwise False
        """
        return self.layout == "planar"


class CardPrinting(models.Model):
    """
    Model for a certain card printed in a certain set
    """

    FRAME_EFFECT_CHOICES = (
        ("colorshifted", "colorshifted"),
        ("compasslanddfc", "compasslanddfc"),
        ("devoid", "devoid"),
        ("draft", "draft"),
        ("extendedart", "extendedart"),
        ("inverted", "inverted"),
        ("legendary", "legendary"),
        ("miracle", "miracle"),
        ("mooneldrazidfc", "mooneldrazidfc"),
        ("nyxborn", "nyxborn"),
        ("nyxtouched", "nyxtouched"),
        ("originpwdfc", "originpwdfc"),
        ("showcase", "showcase"),
        ("sunmoondfc", "sunmoondfc"),
        ("tombstone", "tombstone"),
    )

    flavour_text: str = models.CharField(max_length=500, blank=True, null=True)
    artist: str = models.CharField(max_length=100, blank=True, null=True)
    number: str = models.CharField(max_length=10, blank=True, null=True)

    # Text on the card as originally printed.
    original_text: str = models.CharField(max_length=1000, blank=True, null=True)

    # Type as originally printed. Includes any supertypes and subtypes.
    original_type: str = models.CharField(max_length=200, blank=True, null=True)
    watermark: str = models.CharField(max_length=100, blank=True, null=True)

    # The unique identifier that mtgjson uses for the card
    # It is made up by doing an SHA1 hash of setCode + cardName + cardImageName
    json_id: str = models.CharField(max_length=40, unique=True)

    scryfall_id: str = models.CharField(max_length=40, blank=True, null=True)

    scryfall_illustration_id: str = models.CharField(
        max_length=36, blank=True, null=True
    )

    # The border colour of the card if it differs from the border colour of the rest of the set
    # (e.g. basic lands in Unglued)
    border_colour: str = models.CharField(max_length=10, blank=True, null=True)

    frame_effect: str = models.CharField(
        max_length=50, blank=True, null=True, choices=FRAME_EFFECT_CHOICES
    )
    frame_version: str = models.CharField(max_length=50, blank=True, null=True)

    set: Set = models.ForeignKey(
        Set, related_name="card_printings", on_delete=models.CASCADE
    )
    card: Card = models.ForeignKey(
        Card, related_name="printings", on_delete=models.CASCADE
    )
    rarity: Rarity = models.ForeignKey(
        Rarity, related_name="card_printings", on_delete=models.CASCADE
    )

    # If the card is in a duel deck product, can be a (left) or b (right).
    duel_deck_side: str = models.CharField(max_length=1, blank=True, null=True)

    # Set to true if this card was only released as part of a core box set.
    # These are technically part of the core sets and are tournament
    # legal despite not being available in boosters.
    is_starter: bool = models.BooleanField()

    is_timeshifted: bool = models.BooleanField()

    # Can the card be found in foil?
    has_foil: bool = models.BooleanField(default=True)
    # Can the card be found in non-foil?
    has_non_foil: bool = models.BooleanField(default=True)

    # The card has some kind of alternative variation to its printed counterpart.
    is_alternative: bool = models.BooleanField(default=False)

    # Is the card available in Magic: The Gathering Arena?
    is_arena: bool = models.BooleanField(default=False)

    # Is the card available in Magic: The Gathering Online?
    is_mtgo: bool = models.BooleanField(default=False)

    # Is the card only available online?
    is_online_only: bool = models.BooleanField(default=False)

    # Is the card available in print?
    is_paper: bool = models.BooleanField(default=True)

    # Is the card full artwork?
    is_full_art: bool = models.BooleanField(default=False)

    # Is the card oversized?
    is_oversized: bool = models.BooleanField(default=False)

    # Does the card normally have a text box, but doesn't on this card?
    is_textless: bool = models.BooleanField(default=False)

    # Has the card been reprinted?
    is_reprint: bool = models.BooleanField(default=False)

    # Is the card a promotional print?
    is_promo: bool = models.BooleanField(default=False)

    # Does the card have a story spotlight?
    is_story_spotlight: bool = models.BooleanField(default=False)

    # The Magic Card Market card ID.
    magic_card_market_id: int = models.IntegerField(null=True, blank=True)

    # The Magic Card Market card meta ID.
    magic_card_market_meta_id: int = models.IntegerField(null=True, blank=True)

    # The Magic: The Gathering Arena card ID.
    mtg_arena_id: int = models.IntegerField(null=True, blank=True)

    # The Magic: The Gathering Online card ID.
    mtgo_id: int = models.IntegerField(null=True, blank=True)

    # The Magic: The Gathering Online card foil ID.
    mtgo_foil_id: int = models.IntegerField(null=True, blank=True)

    # mtgstocks.com card ID.
    mtg_stocks_id: int = models.IntegerField(null=True, blank=True)

    # Numeric identifier for the card for TCGPlayer.
    tcg_player_product_id: int = models.IntegerField(null=True, blank=True)

    class Meta:
        """
        Metaclass for CardPrinting
        """

        ordering = ["set__release_date", "set__name", "number"]

    def __str__(self):
        return f"{self.card} in {self.set} ({self.number})"

    def get_set_keyrune_code(self) -> str:
        """
        Gets the keyrune code that should be used for this printing
        In 99% of all cases, this will return the same value as printing.set.keyrune_code
        But for Guild Kit printings, the guild symbol should be used instead
        :return:
        """
        if self.set.code in ("GK1", "GK2") and self.watermark:
            return self.watermark.lower()

        return self.set.keyrune_code.lower()

    def get_user_ownership_count(self, user: User, prefetched: bool = False) -> int:
        """
        Returns the total number of cards that given user owns of this printing
        :param prefetched: Whether to use prefetched data, or to get it from the database again
        :param user: The user who should own the card
        :return: The ownership total
        """
        if prefetched:
            return sum(
                ownership.count
                for printed_language in self.printed_languages.all()
                for physical_card in printed_language.physical_cards.all()
                for ownership in physical_card.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.printed_languages.aggregate(
            card_count=Sum(
                Case(
                    When(
                        physical_cards__ownerships__owner=user,
                        then="physical_cards__ownerships__count",
                    ),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )["card_count"]


class PhysicalCard(models.Model):
    """
    Model for joining one or more CardPrintingLanguages into a single card that can be owned
    """

    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)

    def __str__(self) -> str:
        return "//".join([str(x) for x in self.printed_languages.all()])

    def get_simple_string(self) -> str:
        """
        Gets a simple representation of this Physical Card
        :return:
        """
        if self.printed_languages.count() == 1:
            return str(self.printed_languages.first())

        base = self.printed_languages.first()
        return (
            base.language.name
            + " "
            + "//".join(p.card_printing.card.name for p in self.printed_languages.all())
        )

    def get_display_for_adding(self) -> str:
        """
        Gets a simple representation of this Physical card without card names
        :return:
        """
        if self.printed_languages.count() == 1:
            printlang = self.printed_languages.first()
            return f"{printlang.language}"

        return self.get_simple_string()

    def apply_user_change(self, change_count: int, user: User) -> bool:
        """
        Applies a change of the number of cards a user owns (can add or subtract cards)
        :param change_count: The number of cards that should be added/removed
        :param user: The user that the cards should be added/removed to
        :return: True if the change was successful, otherwise False
        """
        if user is None or change_count == 0:
            return False

        try:
            existing_card = UserOwnedCard.objects.get(physical_card=self, owner=user)
            if change_count < 0 and abs(change_count) >= existing_card.count:
                # If the count is below 1 than there is no point thinking that the user "owns"
                # the card anymore, so just delete the record
                change_count = -existing_card.count
                existing_card.delete()
            else:
                existing_card.count += change_count
                existing_card.clean()
                existing_card.save()
        except UserOwnedCard.DoesNotExist:
            if change_count <= 0:
                # You can't subtract cards when you don' have any
                return False
            new_card = UserOwnedCard(count=change_count, owner=user, physical_card=self)
            new_card.clean()
            new_card.save()

        change = UserCardChange(
            physical_card=self,
            owner=user,
            difference=change_count,
            date=datetime.datetime.now(),
        )
        change.clean()
        change.save()
        return True


class CardPrintingLanguage(models.Model):
    """
    Model for a card printed in a certain set of a certain language
    """

    language: "Language" = models.ForeignKey(
        "Language", related_name="cards", on_delete=models.CASCADE
    )
    card_name = models.CharField(max_length=200)
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    # An integer most cards have which Wizards of the Coast uses as a card identifier.
    multiverse_id = models.IntegerField(blank=True, null=True)
    text = models.CharField(max_length=1000, blank=True, null=True)

    card_printing = models.ForeignKey(
        CardPrinting, related_name="printed_languages", on_delete=models.CASCADE
    )

    physical_cards = models.ManyToManyField(
        PhysicalCard, related_name="printed_languages"
    )

    class Meta:
        """
        Meta information for CardPrintingLanguages
        """

        unique_together = ("language", "card_name", "card_printing")

    def __str__(self):
        return f"{self.language} {self.card_printing}"

    def get_image_path(self) -> Optional[str]:
        """
        Gets the relative file path of this prined language
        :return:
        """
        if self.language.code is None:
            return None
        image_name = re.sub(r"\W", "s", self.card_printing.number)
        if self.card_printing.card.layout in ("transform", "double_faced_token"):
            image_name += "_" + self.card_printing.card.side

        if self.card_printing.card.is_token:
            image_name = "t" + image_name

        return os.path.join(
            "card_images",
            self.language.code.lower(),
            "_" + self.card_printing.set.code.lower(),
            image_name + ".jpg",
        )

    def get_user_ownership_count(self, user: User, prefetched: bool = False) -> int:
        """
        Returns the total number of cards that given user owns of this printed language
        :param user: The user who should own the card
        :param prefetched: Whether to use prefetched data, or to get it from the database again
        :return: The ownership total
        """
        if prefetched:
            return sum(
                ownership.count
                for physical_card in self.physical_cards.all()
                for ownership in physical_card.ownerships.all()
                if ownership.owner == user
            )

        return self.physical_cards.aggregate(
            card_count=Sum(
                Case(
                    When(ownerships__owner=user, then="ownerships__count"),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )["card_count"]


class UserOwnedCard(models.Model):
    """
    Model for a user owned a number of physical cards
    """

    count: int = models.IntegerField()
    physical_card: PhysicalCard = models.ForeignKey(
        PhysicalCard, related_name="ownerships", on_delete=models.CASCADE
    )
    owner: User = models.ForeignKey(
        User, related_name="owned_cards", on_delete=models.CASCADE
    )

    class Meta:
        """
        Meta information for the UserOwnedCard class
        """

        unique_together = ("physical_card", "owner")

    def __str__(self):
        return f"{self.owner} owns {self.count} of {self.physical_card}"


class UserCardChange(models.Model):
    """
    Model for a change in the number of cards that a user owns
    """

    date = models.DateTimeField()
    difference = models.IntegerField()

    physical_card = models.ForeignKey(
        PhysicalCard, related_name="user_changes", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        User, related_name="card_changes", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.date} {self.difference} {self.physical_card}"
