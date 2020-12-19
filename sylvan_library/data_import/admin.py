from django import forms
from django.contrib import admin

from data_import.models import (
    UpdateSet,
    UpdateCard,
    UpdateBlock,
    UpdateCardFace,
    UpdateCardRuling,
    UpdateCardLegality,
)


@admin.register(UpdateBlock)
class CreateBlockAdmin(admin.ModelAdmin):
    pass


# @admin.register(CreateSet)
# class CreateSetAdmin(admin.ModelAdmin):
#     pass


@admin.register(UpdateSet)
class UpdateSetAdmin(admin.ModelAdmin):
    pass


@admin.register(UpdateCard)
class UpdateCardAdmin(admin.ModelAdmin):
    pass


@admin.register(UpdateCardFace)
class UpdateCardFaceAdmin(admin.ModelAdmin):
    search_fields = ["face_name"]


# @admin.register(CreateCard)
# class CreateCardAdmin(admin.ModelAdmin):
#     pass


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