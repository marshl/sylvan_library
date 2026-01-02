"""
Django admin config for card app
"""

from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from sylvan_library.cardsearch.models import CardSearchMetadata, CardFaceSearchMetadata


@admin.register(CardSearchMetadata)
class CardSearchMetadataAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["card"]


@admin.register(CardFaceSearchMetadata)
class CardFaceSearchMetadataAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["card_face"]
