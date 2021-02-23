"""
Models for helping perform searches by tracking card statistics that would be
hard/expensive to search for at run time
"""
from django.db import models

from cards.models import Card, CardFace


class CardFaceSearchMetadata(models.Model):
    """
    This object stores additional information a card face that is used during searches.
    This has a one to one relationship with a CardFace, and could be stored on the face itself,
    however it is probably better to reduce clutter on the main object where possible
    """

    card_face = models.OneToOneField(
        CardFace, related_name="search_metadata", on_delete=models.CASCADE
    )

    rules_without_reminders = models.CharField(max_length=1000, blank=True, null=True)

    symbol_count_w = models.IntegerField(default=0)
    symbol_count_u = models.IntegerField(default=0)
    symbol_count_b = models.IntegerField(default=0)
    symbol_count_r = models.IntegerField(default=0)
    symbol_count_g = models.IntegerField(default=0)
    symbol_count_c = models.IntegerField(default=0)
    symbol_count_s = models.IntegerField(default=0)
    symbol_count_x = models.IntegerField(default=0)
    symbol_count_w_u = models.IntegerField(default=0)
    symbol_count_u_b = models.IntegerField(default=0)
    symbol_count_b_r = models.IntegerField(default=0)
    symbol_count_r_g = models.IntegerField(default=0)
    symbol_count_g_w = models.IntegerField(default=0)
    symbol_count_w_b = models.IntegerField(default=0)
    symbol_count_u_r = models.IntegerField(default=0)
    symbol_count_b_g = models.IntegerField(default=0)
    symbol_count_r_w = models.IntegerField(default=0)
    symbol_count_g_u = models.IntegerField(default=0)
    symbol_count_2_w = models.IntegerField(default=0)
    symbol_count_2_u = models.IntegerField(default=0)
    symbol_count_2_b = models.IntegerField(default=0)
    symbol_count_2_r = models.IntegerField(default=0)
    symbol_count_2_g = models.IntegerField(default=0)
    symbol_count_w_p = models.IntegerField(default=0)
    symbol_count_u_p = models.IntegerField(default=0)
    symbol_count_b_p = models.IntegerField(default=0)
    symbol_count_r_p = models.IntegerField(default=0)
    symbol_count_g_p = models.IntegerField(default=0)

    symbol_count_generic = models.IntegerField(default=0)

    produces_w = models.BooleanField(default=False)
    produces_u = models.BooleanField(default=False)
    produces_b = models.BooleanField(default=False)
    produces_r = models.BooleanField(default=False)
    produces_g = models.BooleanField(default=False)
    produces_c = models.BooleanField(default=False)
