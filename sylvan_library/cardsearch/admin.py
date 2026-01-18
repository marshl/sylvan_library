"""
Django admin config for card app
"""

from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from cardsearch.search_metadata import (
    build_metadata_for_card,
    build_metadata_for_card_face,
)
from sylvan_library.cardsearch.models import CardSearchMetadata, CardFaceSearchMetadata


@admin.action(description="Rebuild search metadata")
def rebuild_card_metadata(modeladmin, request, queryset):
    for card_search_metadata in queryset.all():
        build_metadata_for_card(card_search_metadata.card)


@admin.action(description="Rebuild search metadata")
def rebuild_cardface_metadata(modeladmin, request, queryset):
    for card_search_metadata in queryset.all():
        build_metadata_for_card_face(card_search_metadata.card_face)


@admin.register(CardSearchMetadata)
class CardSearchMetadataAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["card"]
    search_fields = ["card__name"]
    actions = [rebuild_card_metadata]


@admin.register(CardFaceSearchMetadata)
class CardFaceSearchMetadataAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["card_face"]
    search_fields = ["card_face__name"]
    actions = [rebuild_cardface_metadata]
