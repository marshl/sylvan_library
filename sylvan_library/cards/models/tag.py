from django.contrib.auth.models import User
from django.db import models

from sylvan_library.cards.models import Card


class CardTag(models.Model):
    """
    Model for a user owned tag that can be applied to many cards
    """

    name: str = models.CharField(max_length=200)
    owner: User = models.ForeignKey(
        User, related_name="card_tags", on_delete=models.CASCADE
    )
    cards: Card = models.ManyToManyField(Card, related_name="tags")

    def __str__(self):
        return self.name
