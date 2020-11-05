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

    PRICE_TYPE_CHOICES = (
        ("paper", "Paper"),
        ("paperFoil", "Paper Foil"),
        ("mtgo", "MTGO"),
        ("mtgoFoil", "MTGO Foil"),
    )

    printing = models.ForeignKey(
        CardPrinting, on_delete=models.CASCADE, related_name="prices"
    )
    price = models.FloatField()
    date = models.DateField()
    price_type = models.CharField(max_length=50, choices=PRICE_TYPE_CHOICES)

    class Meta:
        """
        Meta information for CardPrintingLanguages
        """

        unique_together = ("date", "printing", "price_type")

    def __str__(self):
        dollars = round(float(self.price), 2)
        dollar_string = "%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
        if self.price_type.startswith("mtgo"):
            return "{} TIX".format(dollar_string)
        return "${}".format(dollar_string)
