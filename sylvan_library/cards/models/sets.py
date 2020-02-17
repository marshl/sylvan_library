"""
Models for set related objects
"""
import datetime

from django.db import models


class Block(models.Model):
    """
    Model for a block of sets
    """

    name: str = models.CharField(max_length=200, unique=True)
    release_date: datetime.date = models.DateField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Format(models.Model):
    """
    Model for a format of cards
    """

    name: str = models.CharField(max_length=100, unique=True)
    code: str = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Set(models.Model):
    """
    Model for a set of cards
    """

    code: str = models.CharField(max_length=10, unique=True)
    release_date: datetime.datetime = models.DateField(blank=True, null=True)
    name: str = models.CharField(max_length=200, unique=True)
    type: str = models.CharField(max_length=50, blank=True, null=True)
    total_set_size: int = models.IntegerField()
    base_set_size: int = models.IntegerField(default=0)
    keyrune_code: str = models.CharField(max_length=50)
    is_foreign_only: bool = models.BooleanField(default=False)
    is_foil_only: bool = models.BooleanField(default=False)
    is_online_only: bool = models.BooleanField(default=False)
    is_partial_preview: bool = models.BooleanField(default=False)
    magic_card_market_name: str = models.CharField(
        max_length=200, blank=True, null=True
    )
    magic_card_market_id: int = models.IntegerField(blank=True, null=True)
    mtgo_code: str = models.CharField(max_length=10, null=True, blank=True)
    tcg_player_group_id: int = models.IntegerField(blank=True, null=True)

    parent_set = models.ForeignKey(
        "Set",
        blank=True,
        null=True,
        related_name="child_sets",
        on_delete=models.CASCADE,
    )

    block = models.ForeignKey(
        Block, null=True, blank=True, related_name="sets", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
