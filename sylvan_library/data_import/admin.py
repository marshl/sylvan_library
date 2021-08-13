from django import forms
from django.contrib import admin

from data_import.models import (
    UpdateSet,
    UpdateCard,
    UpdateBlock,
    UpdateCardFace,
    UpdateCardRuling,
    UpdateCardLegality,
    UpdateCardPrinting,
    UpdateCardFacePrinting,
    UpdateCardLocalisation,
    UpdateCardFaceLocalisation,
)


@admin.register(UpdateBlock)
class CreateBlockAdmin(admin.ModelAdmin):
    pass


@admin.register(UpdateSet)
class UpdateSetAdmin(admin.ModelAdmin):
    search_fields = ["field_data"]
    list_filter = ["update_mode"]


@admin.register(UpdateCard)
class UpdateCardAdmin(admin.ModelAdmin):
    pass


@admin.register(UpdateCardFace)
class UpdateCardFaceAdmin(admin.ModelAdmin):
    search_fields = ["face_name"]


class UpdateCardRulingModelForm(forms.ModelForm):
    ruling_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = UpdateCardRuling
        exclude = []


@admin.register(UpdateCardRuling)
class UpdateCardRulingAdmin(admin.ModelAdmin):
    search_fields = ["card_name"]
    form = UpdateCardRulingModelForm


@admin.register(UpdateCardLegality)
class UpdateCardLegalityAdmin(admin.ModelAdmin):
    search_fields = ["card_name"]


@admin.register(UpdateCardPrinting)
class UpdateCardPrintingAdmin(admin.ModelAdmin):
    search_fields = ["card_name", "card_scryfall_oracle_id", "scryfall_id", "set_code"]


@admin.register(UpdateCardFacePrinting)
class UpdateCardFacePrintingAdmin(admin.ModelAdmin):
    search_fields = ["card_name", "scryfall_id", "scryfall_oracle_id", "printing_uuid"]


@admin.register(UpdateCardLocalisation)
class UpdateCardLocalisationAdmin(admin.ModelAdmin):
    search_fields = ["card_name", "printing_scryfall_id"]


@admin.register(UpdateCardFaceLocalisation)
class UpdateCardFaceLocalisationAdmin(admin.ModelAdmin):
    search_fields = [
        "face_name",
        "face_printing_uuid",
        "update_mode",
        "printing_scryfall_id",
    ]
