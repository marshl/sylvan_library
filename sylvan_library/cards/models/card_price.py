"""
Models fo card pricing
"""
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models

from cards.models.card import CardPrinting


class CardPrice(models.Model):
    """
    A card price recorded at a certain dae for a certain printing
    """

    card_printing = models.ForeignKey(
        CardPrinting, on_delete=models.CASCADE, related_name="prices"
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

    is_latest = models.BooleanField(default=False)

    class Meta:
        """
        Meta information for CardPrice
        """

        unique_together = ("date", "card_printing")
