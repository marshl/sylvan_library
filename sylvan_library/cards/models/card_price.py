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

    STOCK_TYPE_CHOICES = (("paper", "Paper"), ("mtgo", "MTGO"))

    TRADE_DIRECTION_CHOICES = (("retail", "Retail"), ("buylist", "Buylist"))

    printing = models.ForeignKey(
        CardPrinting, on_delete=models.CASCADE, related_name="prices"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    stock_type = models.CharField(max_length=10, choices=STOCK_TYPE_CHOICES)
    foil = models.BooleanField(default=False)
    # currency = models.CharField(max_length=5, default="USD")
    # store = models.CharField(max_length=50)
    # retail_type = models.CharField(max_length=10, default="buy", choices=TRADE_DIRECTION_CHOICES)

    class Meta:
        """
        Meta information for CardLocalisations
        """

        unique_together = ("date", "printing", "stock_type", "foil", "store", "retail_type")

    def __str__(self):
        dollars = round(float(self.price), 2)
        dollar_string = "%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
        if self.price_type.startswith("mtgo"):
            return "{} TIX".format(dollar_string)
        return "${}".format(dollar_string)
