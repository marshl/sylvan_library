"""
Models for the card app
"""
import datetime
import os
import re
from typing import Optional

from django.db import models
from django.db.models import Sum, IntegerField, Case, When
from django.contrib.auth.models import User

from cards.models.card import Card, CARD_LAYOUT_CHOICES
from cards.models.sets import Block, Set, Format
from cards.models.rarity import Rarity
from cards.models.colour import Colour
from cards.models.decks import Deck, DeckCard


CARD_LEGALITY_RESTRICTION_CHOICES = (
    ("Legal", "Legal"),
    ("Banned", "Banned"),
    ("Restricted", "Restricted"),
)


class CardPrinting(models.Model):
    """
    Model for a certain card printed in a certain set
    """

    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    artist = models.CharField(max_length=100, blank=True, null=True)
    number = models.CharField(max_length=10, blank=True, null=True)
    original_text = models.CharField(max_length=1000, blank=True, null=True)
    original_type = models.CharField(max_length=200, blank=True, null=True)
    watermark = models.CharField(max_length=100, blank=True, null=True)

    # The unique identifier that mtgjson uses for the card
    # It is made up by doing an SHA1 hash of setCode + cardName + cardImageName
    json_id = models.CharField(max_length=40, unique=True)

    scryfall_id = models.CharField(max_length=40, blank=True, null=True)

    # The border colour of the card if it differs from the border colour of the rest of the set
    # (e.g. basic lands in Unglued)
    border_colour = models.CharField(max_length=10, blank=True, null=True)

    set = models.ForeignKey(
        Set, related_name="card_printings", on_delete=models.CASCADE
    )
    card = models.ForeignKey(Card, related_name="printings", on_delete=models.CASCADE)
    rarity = models.ForeignKey(
        Rarity, related_name="card_printings", on_delete=models.CASCADE
    )

    # Set to true if this card was only released as part of a core box set.
    # These are technically part of the core sets and are tournament
    # legal despite not being available in boosters.
    is_starter = models.BooleanField()

    is_timeshifted = models.BooleanField()

    class Meta:
        """
        Metaclass for CardPrinting
        """

        ordering = ["set__release_date", "set__name", "number"]

    def __str__(self):
        return f"{self.card} in {self.set}"

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

    def __str__(self):
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
            + " in "
            + base.card_printing.set.name
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

    language = models.ForeignKey(
        "Language", related_name="cards", on_delete=models.CASCADE
    )
    card_name = models.CharField(max_length=200)
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)
    multiverse_id = models.IntegerField(blank=True, null=True)

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
                if ownership.owner_id == user.id
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

    count = models.IntegerField()
    physical_card = models.ForeignKey(
        PhysicalCard, related_name="ownerships", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
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


class CardRuling(models.Model):
    """
    Model for a ruling made on a card
    """

    date = models.DateField()
    text = models.CharField(max_length=4000)

    card = models.ForeignKey(Card, related_name="rulings", on_delete=models.CASCADE)

    class Meta:
        """
        Meta configuration for the CardRuling class
        """

        unique_together = ("date", "text", "card")

    def __str__(self):
        return f"Ruling for {self.card}: {self.text}"


class CardLegality(models.Model):
    """
    Model for a restriction on the legality of a card in a format
    """

    card = models.ForeignKey(Card, related_name="legalities", on_delete=models.CASCADE)
    format = models.ForeignKey(
        Format, related_name="card_legalities", on_delete=models.CASCADE
    )
    restriction = models.CharField(
        max_length=50, choices=CARD_LEGALITY_RESTRICTION_CHOICES
    )

    class Meta:
        """
        Meta configuration for the CardLegality class
        """

        unique_together = ("card", "format", "restriction")

    def __str__(self):
        return f"{self.card} is {self.restriction} in {self.format}"


class CardTag(models.Model):
    """
    Model for a user owned tag that can be applied to many cards
    """

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, related_name="card_tags", on_delete=models.CASCADE)
    cards = models.ManyToManyField(Card, related_name="tags")

    def __str__(self):
        return self.name


class Language(models.Model):
    """
    Model for a language that a card could be printed in
    """

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, null=True, blank=True)

    ENGLISH = None

    def __str__(self):
        return self.name

    @staticmethod
    def english() -> "Language":
        """
        Gets the cached english language object (English is the default language, and it used
        quite a lot, so this reduces the number of queries made quite a bit)
        :return:
        """
        if not Language.ENGLISH:
            Language.ENGLISH = Language.objects.get(name="English")

        return Language.ENGLISH


class CardImage(models.Model):
    """
    Model for a CardPrintingLanguage's image download status
    (in the future, this might even contain the image itself)
    """

    printed_language = models.OneToOneField(
        CardPrintingLanguage, related_name="image", on_delete=models.CASCADE
    )

    downloaded = models.BooleanField()


class UserProps(models.Model):
    """
    Additional properties for the Django User model
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unused_cards_seed = IntegerField(default=0)

    @staticmethod
    def add_to_user(user: User) -> "UserProps":
        """
        Adds a new UserProps instance to the given user
        (user.userpops existence should be checked every time a value from it is used,
        and this function should be called it if doesn't exist)
        :param user: The user to add the props to
        """
        props = UserProps(user=user)
        props.full_clean()
        props.save()
        return props
