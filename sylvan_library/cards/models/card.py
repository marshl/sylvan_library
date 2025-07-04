"""
Module for Card related models
"""

import datetime
import logging
import random
from typing import Optional


from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, IntegerField, Case, When

from bitfield import BitField
from cards.models.colour import Colour
from cards.models.language import Language
from cards.models.rarity import Rarity
from cards.models.sets import Set

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
    mana_value = models.FloatField()
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

    # pylint: disable=invalid-str-returned
    def __str__(self) -> str:
        return self.name

    def get_user_ownership_count(
        self, user: get_user_model(), prefetched: bool = False
    ) -> int:
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

    def is_land(self, only_land: bool = False) -> bool:
        """
        Returns whether or not this is a land card
        :return: True if this is a land card, otherwise False
        """
        generator = (
            any(_type.name == "Land" for _type in face.types.all())
            for face in self.faces.all()
        )
        if only_land:
            return all(generator)
        return any(generator)


class CardType(models.Model):
    """
    The type of any number of cards (e.g. Creature, Artifact, etc.)
    """

    name = models.CharField(max_length=50, unique=True)
    # Types that aren't listed in the MTGJSON type files are "automatically created"
    automatically_created = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class CardSupertype(models.Model):
    """
    The supertype of any number of cards (e.g. Legendary, Basic, etc.)
    """

    name = models.CharField(max_length=50, unique=True)
    # Types that aren't listed in the MTGJSON type files are "automatically created"
    automatically_created = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class CardSubtype(models.Model):
    """
    The subtype of any number of cards (e.g. Beast, Equipment, Aura etc.)
    """

    name = models.CharField(max_length=50, unique=True)
    # Types that aren't listed in the MTGJSON type files are "automatically created"
    automatically_created = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class CardFace(models.Model):
    """
    A face of a card. Most cards only have a single face, but any flip/split/transform or other
    cards will have 2 faces. Who//What//When//Where//Why will have 5.
    """

    card = models.ForeignKey(Card, related_name="faces", on_delete=models.CASCADE)
    side = models.CharField(max_length=1, blank=True, null=True)

    name = models.CharField(max_length=200)

    mana_cost = models.CharField(max_length=50, blank=True, null=True)
    mana_value = models.FloatField()
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
    rules_text = models.CharField(max_length=1500, blank=True, null=True)

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
    latest_price = models.ForeignKey(
        "CardPrice",
        related_name="latest_printing",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
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

        ordering = ["set__release_date", "set__name", "numerical_number"]

    def __str__(self):
        return f"{self.card} in {self.set.code} ({self.number})"

    def get_set_keyrune_code(self) -> str:
        """
        Gets the keyrune code that should be used for this printing
        In 99% of all cases, this will return the same value as printing.set.keyrune_code
        But for Guild Kit printings, the guild symbol should be used instead
        :return:
        """
        if self.set.code in ("GK1", "GK2") and len(self.face_printings.all()) == 1:
            first_face = self.face_printings.all()[0]
            if first_face.watermark:
                return first_face.watermark

        return self.set.keyrune_code.lower()

    def get_user_ownership_count(
        self, user: get_user_model(), prefetched: bool = False
    ) -> int:
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
    """
    The frame effect on any number of cards (e.g. legendary, bestow etc.)
    """

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class CardFacePrinting(models.Model):
    """
    The face of a card printed in a certain set (for example, Fire of Fire//Ice in Invasion)
    """

    uuid = models.CharField(max_length=40, unique=True)

    flavour_text = models.CharField(max_length=500, blank=True, null=True)

    artist = models.CharField(max_length=100, blank=True, null=True)
    scryfall_illustration_id = models.CharField(max_length=36, blank=True, null=True)

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

    frame_effects = models.ManyToManyField(
        FrameEffect, related_name="face_printings", blank=True
    )

    class Meta:
        unique_together = ("card_face", "card_printing")
        ordering = ("card_face__side",)

    def __str__(self) -> str:
        return f"{self.card_face.name} face of {self.card_printing}"


class CardLocalisation(models.Model):
    """
    Model for a card printed in a certain set of a certain language
    """

    language = models.ForeignKey(
        Language, related_name="cards", on_delete=models.CASCADE
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

    def apply_user_change(self, change_count: int, user: get_user_model()) -> bool:
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
            if change_count < 0:
                # You can't subtract cards when you don' have any
                return False
            new_ownership = UserOwnedCard(
                count=change_count, owner=user, card_localisation=self
            )
            new_ownership.clean()
            new_ownership.save()

        change = UserCardChange(
            card_localisation=self,
            owner=user,
            difference=change_count,
            date=datetime.datetime.now(),
        )
        change.clean()
        change.save()
        return True

    def get_image_path(self) -> Optional[str]:
        """
        Gets most fitting image path for this localisation (the first face if there are multiple
        :return: The image path
        """
        try:
            return self.localised_faces.all()[0].get_image_path()
        except IndexError:
            logging.exception("Failed to find an image for %s", self)
            return None


class CardImage(models.Model):
    """
    Model for a CardLocalisation's image download status
    (in the future, this might even contain the image itself)
    """

    scryfall_image_url = models.URLField(unique=True)
    file_path = models.FilePathField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.file_path or self.scryfall_image_url


class CardFaceLocalisation(models.Model):
    """
    A localised card face. That is, one that is tied to a specific language. For example, a Fire
    face of a Fire//Ice card that is printed in Apocalypse will have an English version, a Spanish
    version and so on.
    """

    localisation = models.ForeignKey(
        CardLocalisation, related_name="localised_faces", on_delete=models.CASCADE
    )
    card_printing_face = models.ForeignKey(
        CardFacePrinting, related_name="localised_faces", on_delete=models.CASCADE
    )

    face_name = models.CharField(max_length=200)
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    text = models.CharField(max_length=1500, blank=True, null=True)

    # Multiple CardFaceLocalisations can share the same image (split cards)
    # Transform cards will have one per side
    image = models.ForeignKey(
        CardImage, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        """
        Meta information for CardLocalisations
        """

        unique_together = ("card_printing_face", "localisation")
        ordering = ("card_printing_face__card_face__side",)

    def __str__(self):
        return f"{self.localisation} ({self.face_name})"

    def get_image_path(self) -> Optional[str]:
        """
        Gets the path of the image for this localisation
        :return: The image's file path
        """
        if not self.image or not self.image.file_path:
            return None
        return self.image.file_path


class UserOwnedCard(models.Model):
    """
    Model for a user owned a number of physical cards
    """

    count = models.PositiveIntegerField()
    card_localisation = models.ForeignKey(
        CardLocalisation, related_name="ownerships", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        get_user_model(), related_name="owned_cards", on_delete=models.CASCADE
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
        get_user_model(), related_name="card_changes", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.date} {self.difference} {self.card_localisation}"
