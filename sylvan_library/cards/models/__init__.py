"""
Models for the card app
"""
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import IntegerField

from cards.models.card import (
    Card,
    CardFace,
    CARD_LAYOUT_CHOICES,
    CardPrintingLanguage,
    CardPrinting,
    UserOwnedCard,
    UserCardChange,
    CardType,
    CardSupertype,
    CardSubtype,
)
from cards.models.card_price import CardPrice
from cards.models.colour import Colour
from cards.models.decks import Deck, DeckCard
from cards.models.rarity import Rarity
from cards.models.sets import Block, Set, Format

CARD_LEGALITY_RESTRICTION_CHOICES = (
    ("Legal", "Legal"),
    ("Banned", "Banned"),
    ("Restricted", "Restricted"),
)


class CardRuling(models.Model):
    """
    Model for a ruling made on a card
    """

    date: datetime.datetime = models.DateField()
    text: str = models.CharField(max_length=4000)

    card: Card = models.ForeignKey(
        Card, related_name="rulings", on_delete=models.CASCADE
    )

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
        verbose_name_plural = "card legalities"

    def __str__(self):
        return f"{self.card} is {self.restriction} in {self.format}"


class CardTag(models.Model):
    """
    Model for a user owned tag that can be applied to many cards
    """

    name: str = models.CharField(max_length=200)
    owner: User = models.ForeignKey(
        User, related_name="card_tags", on_delete=models.CASCADE
    )
    cards: Card = models.ManyToManyField(Card, related_name="tags")

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
        "CardPrintingLanguage", related_name="image", on_delete=models.CASCADE
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
