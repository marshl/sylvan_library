"""
Module for Card related models
"""
import random
from typing import List

from django.db import models
from django.db.models import Sum, IntegerField, Case, When
from django.contrib.auth.models import User
from bitfield import BitField


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
)


# pylint: disable=too-many-instance-attributes
class Card(models.Model):
    """
    Model for a unique card
    """

    name = models.CharField(max_length=200, unique=True)
    display_name = models.CharField(max_length=200)

    cost = models.CharField(max_length=50, blank=True, null=True)
    cmc = models.FloatField()
    colour_flags = BitField(flags=("white", "blue", "black", "red", "green"))
    colour_identity_flags = BitField(flags=("white", "blue", "black", "red", "green"))
    colour_count = models.IntegerField()
    colour_sort_key = models.IntegerField()
    colour_weight = models.IntegerField()

    type = models.CharField(max_length=100, blank=True, null=True)
    subtype = models.CharField(max_length=100, blank=True, null=True)

    power = models.CharField(max_length=20, blank=True, null=True)
    num_power = models.FloatField()
    toughness = models.CharField(max_length=20, blank=True, null=True)
    num_toughness = models.FloatField()
    loyalty = models.CharField(max_length=20, blank=True, null=True)
    num_loyalty = models.FloatField()

    rules_text = models.CharField(max_length=1000, blank=True, null=True)
    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)
    side = models.CharField(max_length=1, blank=True, null=True)
    is_reserved = models.BooleanField()
    scryfall_oracle_id = models.CharField(max_length=36, blank=True, null=True)
    is_token = models.BooleanField()
    links = models.ManyToManyField("self")

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
        return delimiter.join(s.name for s in self.get_all_sides(sort=True))

    @property
    def is_wide(self):
        return self.layout == "planar"
