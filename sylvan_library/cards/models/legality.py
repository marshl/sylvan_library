from django.db import models

from sylvan_library.cards.models.card import Card
from sylvan_library.cards.models.sets import Format

CARD_LEGALITY_RESTRICTION_CHOICES = (
    ("Legal", "Legal"),
    ("Banned", "Banned"),
    ("Restricted", "Restricted"),
)


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
