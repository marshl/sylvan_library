"""
Models for rarity objects
"""

from django.db import models


class Rarity(models.Model):
    """
    Model for a card rarity
    """

    symbol = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=30, unique=True)
    display_order = models.IntegerField(unique=True)

    def __str__(self):
        return self.name
