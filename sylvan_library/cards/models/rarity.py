"""
Models for rarity objects
"""

from django.db import models


class Rarity(models.Model):
    """
    Model for a card rarity
    """

    symbol: str = models.CharField(max_length=5, unique=True)
    name: str = models.CharField(max_length=30, unique=True)
    display_order: int = models.IntegerField(unique=True)

    def __str__(self) -> str:
        return self.name
