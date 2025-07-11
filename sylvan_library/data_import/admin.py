"""
Data import admin
"""

from django import forms
from django.contrib import admin

from data_import.models import (
    UpdateBlock,
    UpdateSet,
    UpdateCard,
    UpdateCardFace,
    UpdateCardRuling,
    UpdateCardLegality,
    UpdateCardFaceLocalisation,
    UpdateCardLocalisation,
    UpdateCardFacePrinting,
    UpdateCardPrinting,
)


@admin.register(UpdateBlock)
class UpdateBlockAdmin(admin.ModelAdmin):
    """
    Admin for UpdateBlock
    """


@admin.register(UpdateSet)
class UpdateSetAdmin(admin.ModelAdmin):
    """
    Admin for an UpdateSet object
    """

    search_fields = ["field_data"]
    list_filter = ["update_mode"]


@admin.register(UpdateCard)
class UpdateCardAdmin(admin.ModelAdmin):
    """
    Admin for an UpdateCard object
    """

    list_filter = ["update_mode"]


@admin.register(UpdateCardFace)
class UpdateCardFaceAdmin(admin.ModelAdmin):
    """
    Admin for the UpdateCardFace model
    """

    search_fields = ["face_name"]
    list_filter = ["update_mode"]


class UpdateCardRulingModelForm(forms.ModelForm):
    """
    Form for a card ruling change
    """

    ruling_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = UpdateCardRuling
        fields = [
            "update_mode",
            "card_name",
            "scryfall_oracle_id",
            "ruling_date",
            "ruling_text",
        ]


@admin.register(UpdateCardRuling)
class UpdateCardRulingAdmin(admin.ModelAdmin):
    """
    Admin for updating a CardRuling object
    """

    search_fields = ["card_name"]
    form = UpdateCardRulingModelForm


@admin.register(UpdateCardLegality)
class UpdateCardLegalityAdmin(admin.ModelAdmin):
    search_fields = ["card_name"]
    list_filter = ["update_mode"]


@admin.register(UpdateCardPrinting)
class UpdateCardPrintingAdmin(admin.ModelAdmin):
    search_fields = ["card_name", "card_scryfall_oracle_id", "scryfall_id", "set_code"]


@admin.register(UpdateCardFacePrinting)
class UpdateCardFacePrintingAdmin(admin.ModelAdmin):
    """
    Admin for a change to a card face printing
    """

    search_fields = ["card_name", "scryfall_id", "scryfall_oracle_id", "printing_uuid"]


@admin.register(UpdateCardLocalisation)
class UpdateCardLocalisationAdmin(admin.ModelAdmin):
    """
    Admin for the UPdateCardLocalisation model
    """

    search_fields = ["card_name", "printing_scryfall_id"]


@admin.register(UpdateCardFaceLocalisation)
class UpdateCardFaceLocalisationAdmin(admin.ModelAdmin):
    search_fields = [
        "face_name",
        "face_printing_uuid",
        "update_mode",
        "printing_scryfall_id",
    ]
    list_filter = ["update_mode", "language_code"]
