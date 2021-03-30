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
    CardPrinting,
    CardFacePrinting,
    CardLocalisation,
    CardFaceLocalisation,
    CardPrice,
)


class SetInline(admin.TabularInline):
    model = Set

    show_change_link = True
    fields = ("code", "name", "type", "release_date")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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


class CardPrintingInline(admin.TabularInline):
    model = CardPrinting
    show_change_link = True
    fields = ("card", "scryfall_id", "set", "rarity", "number")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CardFacePrintingInline(admin.TabularInline):
    model = CardFacePrinting
    show_change_link = True
    fields = ("uuid", "card_face", "card_printing", "frame_effects")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CardLocalisationInline(admin.TabularInline):
    model = CardLocalisation
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CardFaceLocalisationInline(admin.TabularInline):
    model = CardFaceLocalisation
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):  # AdminChangeLinksMixin,
    search_fields = ["name"]
    inlines = [CardFaceInline, CardPrintingInline]


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
    inlines = [CardFacePrintingInline]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    inlines = [SetInline]
    list_display = ("__str__", "release_date")


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    search_fields = ["name", "code"]
    inlines = [CardPrintingInline]


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


@admin.register(CardPrinting)
class CardPrintingAdmin(admin.ModelAdmin):
    autocomplete_fields = ["card", "set", "latest_price"]
    search_fields = ["card__name", "scryfall_id"]
    # readonly_fields = ["latest_price"]
    inlines = [CardFacePrintingInline, CardLocalisationInline]


class CardFacePrintingModelForm(forms.ModelForm):
    flavour_text = forms.CharField(widget=forms.Textarea, required=False)
    original_text = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CardFacePrinting
        exclude = []


@admin.register(CardFacePrinting)
class CardFacePrintingAdmin(admin.ModelAdmin):
    autocomplete_fields = ["card_face", "card_printing"]
    search_fields = ["card_face__card__name"]
    form = CardFacePrintingModelForm
    inlines = [CardFaceLocalisationInline]


@admin.register(CardLocalisation)
class CardLocalisationAdmin(admin.ModelAdmin):
    autocomplete_fields = ["card_printing"]
    search_fields = ["card_name", "multiverse_id", "card_printing__scryfall_id"]
    inlines = [CardFaceLocalisationInline]


class CardFaceLocalisationModelForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)
    flavour_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CardFaceLocalisation
        exclude = []


@admin.register(CardFaceLocalisation)
class CardFaceLocalisationAdmin(admin.ModelAdmin):
    autocomplete_fields = ["localisation", "card_printing_face"]
    form = CardFaceLocalisationModelForm


@admin.register(CardPrice)
class CardPriceAdmin(admin.ModelAdmin):
    autocomplete_fields = ["card_printing"]
    search_fields = ["card_printing"]
