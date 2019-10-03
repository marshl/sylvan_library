"""
Models for set related objects
"""
from django.db import models


class Block(models.Model):
    """
    Model for a block of sets
    """

    name = models.CharField(max_length=200, unique=True)
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name


class Format(models.Model):
    """
    Model for a format of cards
    """

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Set(models.Model):
    """
    Model for a set of cards
    """

    code = models.CharField(max_length=10, unique=True)
    release_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    total_set_size = models.IntegerField()
    base_set_size = models.IntegerField(default=0)
    keyrune_code = models.CharField(max_length=10)
    is_foreign_only = models.BooleanField(default=False)
    is_foil_only = models.BooleanField(default=False)
    is_online_only = models.BooleanField(default=False)
    is_partial_preview = models.BooleanField(default=False)
    magic_card_market_name = models.CharField(max_length=200, blank=True, null=True)
    magic_card_market_id = models.IntegerField(blank=True, null=True)
    mtgo_code = models.CharField(max_length=10, null=True, blank=True)
    tcg_player_group_id = models.IntegerField(blank=True, null=True)

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
