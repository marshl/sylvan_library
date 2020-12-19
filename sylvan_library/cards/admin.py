from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django import forms
from django.contrib import admin

from cards.models import (
    Block,
    Set,
    Card,
    CardFace,
    CardRuling,
    CardType,
    CardSupertype,
    CardSubtype,
    CardLegality,
    Format,
)


class CardFaceInline(admin.TabularInline):
    # Assume Image model has foreign key to Post
    model = CardFace
    show_change_link = True
    fields = ("name", "side", "mana_cost", "type_line", "rules_text")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):  # AdminChangeLinksMixin,
    search_fields = ["name"]
    inlines = [CardFaceInline]


class CardFaceModelForm(forms.ModelForm):
    rules_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CardFace
        exclude = []


@admin.register(CardFace)
class CardFaceAdmin(admin.ModelAdmin):
    autocomplete_fields = ["card", "subtypes", "types", "supertypes"]
    search_fields = ["name"]
    form = CardFaceModelForm
    formfield_overrides = {BitField: {"widget": BitFieldCheckboxSelectMultiple}}


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    pass


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    pass


@admin.register(CardType)
class CardTypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(CardSubtype)
class CardSubtypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(CardSupertype)
class CardSupertypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]


class CardRulingModelForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CardRuling
        exclude = []


@admin.register(CardRuling)
class CardRulingAdmin(admin.ModelAdmin):
    search_fields = ["card__name"]
    autocomplete_fields = ["card"]
    form = CardRulingModelForm


@admin.register(CardLegality)
class CardLegalityAdmin(admin.ModelAdmin):
    search_fields = ["card__name"]
    autocomplete_fields = ["card"]


@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    pass
