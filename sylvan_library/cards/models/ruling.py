"""
Card ruling models
"""

import datetime

from django.db import models

from sylvan_library.cards.models.card import Card


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
