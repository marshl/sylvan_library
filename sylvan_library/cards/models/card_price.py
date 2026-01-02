"""
Models fo card pricing
"""

from django.db import models

from sylvan_library.cards.models.card import CardPrinting, Card


class CardPrice(models.Model):
    """
    A card price recorded at a certain dae for a certain printing
    """

    card_printing = models.ForeignKey(
        CardPrinting, on_delete=models.CASCADE, related_name="prices"
    )

    cheapest_card = models.OneToOneField(
        Card,
        on_delete=models.SET_NULL,
        related_name="cheapest_price",
        blank=True,
        null=True,
    )

    date = models.DateField()

    paper_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    paper_foil_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    mtgo_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    mtgo_foil_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        """
        Meta information for CardPrice
        """

        unique_together = ("date", "card_printing")

    def __str__(self):
        return f"Price of {self.card_printing} on {self.date}"
