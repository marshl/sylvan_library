from django.db import models

from cards.models import CardPrinting


class CardPrice(models.Model):

    PRICE_TYPE_CHOICES = (
        ("paper", "Paper"),
        ("paper_foil", "Paper Foil"),
        ("mtgo", "MTGO"),
        ("mtgo_foil", "MTGO Foil"),
    )

    printing = models.ForeignKey(
        CardPrinting, on_delete=models.CASCADE, related_name="prices"
    )
    price = models.FloatField()
    date = models.DateField()
    price_type = models.CharField(max_length=50, choices=PRICE_TYPE_CHOICES)
