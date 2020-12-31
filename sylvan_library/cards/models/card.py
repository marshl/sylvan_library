"""
Module for Card related models
"""
import datetime
import os
import random
import re
from typing import List, Optional

from bitfield import BitField

from cards.models.rarity import Rarity
from cards.models.sets import Set
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, IntegerField, Case, When

from cards.models.colour import Colour

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
    ("modal_dfc", "Modal DFC"),
)

FRAME_EFFECT_CHOICES = (
    ("colorshifted", "colorshifted"),
    ("companion", "Companion"),
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
    ("waxingandwaningmoondfc", "Waxing and Waning Moon DFC"),
    ("fullart", "Full Art"),
)


# pylint: disable=too-many-instance-attributes
class Card(models.Model):
    """
    Model for a unique card
    """

    scryfall_oracle_id = models.CharField(max_length=36, unique=True)
    name = models.CharField(max_length=200)
    converted_mana_cost = models.FloatField()
    layout = models.CharField(max_length=50)
    is_reserved = models.BooleanField(default=False)
    edh_rec_rank = models.IntegerField(blank=True, null=True)
    is_token = models.BooleanField(default=False)
    colour_identity = BitField(flags=Colour.FLAG_CHOICES)
    colour_identity_count = models.IntegerField()

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
                for localisation in card_printing.localisations.all()
                for ownership in localisation.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.printings.aggregate(
            card_count=Sum(
                Case(
                    When(
                        localisations__ownerships__owner=user,
                        then="localisations__ownerships__count",
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
        Returns whether or not this is an oversized card
        :return: True if this is an oversized card, otherwise False
        """
        return self.layout == "planar"

    def is_double_faced(self) -> bool:
        """
        Gets whether this card has another card on the back
        :return: True if this card has is dual-faced or not
        """
        return self.layout in ("transform", "meld", "modal_dfc")

    def has_other_half(self) -> bool:
        """
        Gets whether this card has another half (flip, split, transform etc)
        :return: True if this card has anther half, otherwise False
        """
        return self.layout in (
            "flip",
            "split",
            "transform",
            "meld",
            "aftermath",
            "adventure",
            "modal_dfc",
        )

    @property
    def is_land(self) -> bool:
        """
        Returns whether or not this is a land card
        :return: True if this is a land card, otherwise False
        """
        return "Land" in self.type


class CardType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class CardSupertype(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class CardSubtype(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class CardFace(models.Model):

    card = models.ForeignKey(Card, related_name="faces", on_delete=models.CASCADE)
    side = models.CharField(max_length=1, blank=True, null=True)

    name = models.CharField(max_length=200)

    mana_cost = models.CharField(max_length=50, blank=True, null=True)
    converted_mana_cost = models.FloatField()
    colour = BitField(flags=Colour.FLAG_CHOICES)
    colour_indicator = BitField(flags=Colour.FLAG_CHOICES)
    colour_count = models.IntegerField()
    colour_weight = models.IntegerField()
    colour_sort_key = models.IntegerField()

    power = models.CharField(max_length=20, blank=True, null=True)
    num_power = models.FloatField(default=0)
    toughness = models.CharField(max_length=20, blank=True, null=True)
    num_toughness = models.FloatField(default=0)
    loyalty = models.CharField(max_length=20, blank=True, null=True)
    num_loyalty = models.FloatField(default=0)

    type_line = models.CharField(max_length=200, blank=True, null=True)
    rules_text = models.CharField(max_length=1000, blank=True, null=True)

    hand_modifier = models.CharField(max_length=10, blank=True, null=True)
    num_hand_modifier = models.IntegerField(default=0)
    life_modifier = models.CharField(max_length=10, blank=True, null=True)
    num_life_modifier = models.IntegerField(default=0)

    types = models.ManyToManyField(CardType, related_name="card_faces")

    subtypes = models.ManyToManyField(
        CardSubtype, related_name="card_faces", blank=True
    )
    supertypes = models.ManyToManyField(
        CardSupertype, related_name="card_faces", blank=True
    )

    class Meta:
        unique_together = ("card", "side")
        ordering = ("side",)

    def __str__(self) -> str:
        if self.side:
            return f"{self.name} ({self.side})"
        return self.name


class CardPrinting(models.Model):
    """
    Model for a certain card printed in a certain set
    """

    scryfall_id = models.CharField(max_length=36, unique=True)
    scryfall_illustration_id = models.CharField(max_length=36, blank=True, null=True)
    number = models.CharField(max_length=10, blank=True, null=True)
    numerical_number = models.IntegerField(blank=True, null=True)

    # The border colour of the card if it differs from the border colour of the rest of the set
    # (e.g. basic lands in Unglued)
    border_colour = models.CharField(max_length=10, blank=True, null=True)

    frame_version = models.CharField(max_length=50, blank=True, null=True)

    set = models.ForeignKey(
        Set, related_name="card_printings", on_delete=models.CASCADE
    )
    card = models.ForeignKey(Card, related_name="printings", on_delete=models.CASCADE)
    rarity = models.ForeignKey(
        Rarity, related_name="printings", on_delete=models.CASCADE
    )

    # If the card is in a duel deck product, can be a (left) or b (right).
    duel_deck_side = models.CharField(max_length=1, blank=True, null=True)

    # Set to true if this card was only released as part of a core box set.
    # These are technically part of the core sets and are tournament
    # legal despite not being available in boosters.
    is_starter = models.BooleanField()

    is_timeshifted = models.BooleanField()

    # Can the card be found in foil?
    has_foil = models.BooleanField(default=True)
    # Can the card be found in non-foil?
    has_non_foil = models.BooleanField(default=True)

    # The card has some kind of alternative variation to its printed counterpart.
    is_alternative = models.BooleanField(default=False)

    # Is the card available in Magic: The Gathering Arena?
    is_arena = models.BooleanField(default=False)

    # Is the card available in Magic: The Gathering Online?
    is_mtgo = models.BooleanField(default=False)

    # Is the card only available online?
    is_online_only = models.BooleanField(default=False)

    # Is the card available in print?
    is_paper = models.BooleanField(default=True)

    # Does the card normally have a text box, but doesn't on this card?
    is_textless = models.BooleanField(default=False)

    # Is the card full artwork?
    is_full_art = models.BooleanField(default=False)

    # Is the card oversized?
    is_oversized = models.BooleanField(default=False)

    # Has the card been reprinted?
    is_reprint = models.BooleanField(default=False)

    # Is the card a promotional print?
    is_promo = models.BooleanField(default=False)

    # Does the card have a story spotlight?
    is_story_spotlight = models.BooleanField(default=False)

    # The Magic Card Market card ID.
    magic_card_market_id = models.IntegerField(null=True, blank=True)

    # The Magic Card Market card meta ID.
    magic_card_market_meta_id = models.IntegerField(null=True, blank=True)

    # The Magic: The Gathering Arena card ID.
    mtg_arena_id = models.IntegerField(null=True, blank=True)

    # The Magic: The Gathering Online card ID.
    mtgo_id = models.IntegerField(null=True, blank=True)

    # The Magic: The Gathering Online card foil ID.
    mtgo_foil_id = models.IntegerField(null=True, blank=True)

    # mtgstocks.com card ID.
    mtg_stocks_id = models.IntegerField(null=True, blank=True)

    # Numeric identifier for the card for TCGPlayer.
    tcg_player_product_id = models.IntegerField(null=True, blank=True)

    class Meta:
        """
        Metaclass for CardPrinting
        """

        ordering = ["set__release_date", "set__name"]

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
                for localisation in self.localisations.all()
                for ownership in localisation.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.localisations.aggregate(
            card_count=Sum(
                Case(
                    When(ownerships__owner=user, then="ownerships__count"),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )["card_count"]


class FrameEffect(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class CardFacePrinting(models.Model):
    uuid = models.CharField(max_length=40, unique=True)

    flavour_text = models.CharField(max_length=500, blank=True, null=True)

    artist = models.CharField(max_length=100, blank=True, null=True)

    # Text on the card as originally printed.
    original_text = models.CharField(max_length=1000, blank=True, null=True)

    # Type as originally printed. Includes any supertypes and subtypes.
    original_type = models.CharField(max_length=200, blank=True, null=True)
    watermark = models.CharField(max_length=100, blank=True, null=True)

    card_face = models.ForeignKey(
        CardFace, related_name="face_printings", on_delete=models.CASCADE
    )
    card_printing = models.ForeignKey(
        CardPrinting, related_name="face_printings", on_delete=models.CASCADE
    )

    frame_effects = models.ManyToManyField(FrameEffect, related_name="face_printings")

    class Meta:
        unique_together = ("card_face", "card_printing")

    def __str__(self) -> str:
        return f"{self.card_face.name} face of {self.card_printing}"


# class CardPrintingFaceFrameEffect(models.CharField):
#     name = models.CharField(max_length=50)
#     display_order = models.IntegerField()
#
#     card_printing_face = models.ForeignKey(
#         CardFacePrinting, on_delete=models.CASCADE, related_name="frame_effects"
#     )
#
#     class Meta:
#         unique_together = (
#             ("card_printing_face", "name"),
#             ("card_printing_face", "display_order"),
#         )


class CardLocalisation(models.Model):
    """
    Model for a card printed in a certain set of a certain language
    """

    language = models.ForeignKey(
        "Language", related_name="cards", on_delete=models.CASCADE
    )
    card_printing = models.ForeignKey(
        CardPrinting, related_name="localisations", on_delete=models.CASCADE
    )

    card_name = models.CharField(max_length=200)

    # An integer most cards have which Wizards of the Coast uses as a card identifier.
    multiverse_id = models.IntegerField(blank=True, null=True)

    class Meta:
        """
        Meta information for CardLocalisations
        """

        unique_together = ("language", "card_printing")

    def __str__(self):
        return f"{self.language} {self.card_printing}"

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
            existing_card = UserOwnedCard.objects.get(
                card_localisation=self, owner=user
            )
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
            new_card = UserOwnedCard(
                count=change_count, owner=user, card_localisation=self
            )
            new_card.clean()
            new_card.save()

        change = UserCardChange(
            card_localisation=self,
            owner=user,
            difference=change_count,
            date=datetime.datetime.now(),
        )
        change.clean()
        change.save()
        return True

    def get_image_path(self) -> str:
        return self.localised_faces.first().get_image_path()


class CardFaceLocalisation(models.Model):

    localisation = models.ForeignKey(
        CardLocalisation, related_name="localised_faces", on_delete=models.CASCADE
    )
    card_printing_face = models.ForeignKey(
        CardFacePrinting, related_name="localised_faces", on_delete=models.CASCADE
    )

    face_name = models.CharField(max_length=200)
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    text = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        """
        Meta information for CardLocalisations
        """

        unique_together = ("card_printing_face", "localisation")

    def __str__(self):
        return f"{self.face_name} {self.localisation} ({self.card_printing_face})"

    def get_image_path(self) -> Optional[str]:
        """
        Gets the relative file path of this prined language
        :return:
        """
        if self.localisation.language.code is None:
            return None
        # Replace any non-wordy characters (like a star symbol) with s
        image_name = re.sub(r"\W", "s", self.localisation.card_printing.number)
        if self.localisation.card_printing.card.layout in (
            "transform",
            "double_faced_token",
            "modal_dfc",
        ):
            image_name += "_" + self.card_printing_face.card_face.side

        if self.localisation.card_printing.card.is_token:
            image_name = "t" + image_name

        return os.path.join(
            "card_images",
            self.localisation.language.code.lower(),
            "_" + self.localisation.card_printing.set.code.lower(),
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

    count = models.PositiveIntegerField()
    card_localisation = models.ForeignKey(
        CardLocalisation, related_name="ownerships", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        User, related_name="owned_cards", on_delete=models.CASCADE
    )

    class Meta:
        """
        Meta information for the UserOwnedCard class
        """

        unique_together = ("card_localisation", "owner")

    def __str__(self):
        return f"{self.owner} owns {self.count} of {self.card_localisation}"


class UserCardChange(models.Model):
    """
    Model for a change in the number of cards that a user owns
    """

    date = models.DateTimeField()
    difference = models.IntegerField()

    card_localisation = models.ForeignKey(
        CardLocalisation, related_name="user_changes", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        User, related_name="card_changes", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.date} {self.difference} {self.card_localisation}"
