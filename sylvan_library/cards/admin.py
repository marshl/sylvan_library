"""
Django admin config for card app
"""

from django import forms
from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from cards.models.card import (
    CardFace,
    CardPrinting,
    CardFacePrinting,
    CardLocalisation,
    CardFaceLocalisation,
    Card,
    CardType,
    CardSubtype,
    CardSupertype,
    CardImage,
    UserCardChange,
    UserOwnedCard,
    FrameEffect,
)
from cards.models.card_price import CardPrice
from cards.models.decks import DeckCard, Deck
from cards.models.legality import CardLegality
from cards.models.ruling import CardRuling
from cards.models.sets import Set, Block, Format


class SetInline(admin.TabularInline):
    """
    Admin config for Set object
    """

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
    """
    Inline model for CardFace in order to disable permissions
    """

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
    """
    Inline admin for CardPrinting
    """

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
    """
    Inline admin for CardFacePrinting
    """

    model = CardFacePrinting
    show_change_link = True
    fields = ("uuid", "card_face", "card_printing", "frame_effects")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserOwnedCardInline(admin.TabularInline):
    """
    Model Inline Admin for UserOwnedCard
    """

    model = UserOwnedCard

    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CardLocalisationInline(admin.TabularInline):
    """
    Inline admin for CardLocalisation
    """

    model = CardLocalisation
    show_change_link = True
    inlines = [UserOwnedCardInline]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CardFaceLocalisationInline(admin.TabularInline):
    """
    Inline admin for CardFaceLocalisation
    """

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
    """
    Admin for Card
    """

    search_fields = ["name"]
    inlines = [CardFaceInline, CardPrintingInline]


class CardFaceModelForm(forms.ModelForm):
    """
    Form for CardFace to override field widgets
    """

    rules_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CardFace
        fields = [
            "card",
            "name",
            "side",
            "mana_cost",
            "mana_value",
            "colour",
            "colour_indicator",
            "colour_count",
            "colour_weight",
            "colour_sort_key",
            "power",
            "num_power",
            "toughness",
            "num_toughness",
            "loyalty",
            "num_loyalty",
            "rules_text",
            "hand_modifier",
            "num_hand_modifier",
            "life_modifier",
            "num_life_modifier",
            "type_line",
            "types",
            "subtypes",
            "supertypes",
        ]


@admin.register(CardFace)
class CardFaceAdmin(admin.ModelAdmin):
    """
    Admin for CardFace
    """

    autocomplete_fields = ["card", "subtypes", "types", "supertypes"]
    search_fields = ["name"]
    form = CardFaceModelForm
    inlines = [CardFacePrintingInline]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """
    Admin for a set Block
    """

    inlines = [SetInline]
    list_display = ("__str__", "release_date")


@admin.register(Set)
class SetAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    """
    Admin for a card Set
    """

    search_fields = ["name", "code"]
    inlines = [CardPrintingInline]
    list_display = ["name", "code", "release_date", "type"]
    autocomplete_fields = ["parent_set"]


@admin.register(CardType)
class CardTypeAdmin(admin.ModelAdmin):
    """
    Admin for a card's Type (Creature, Enchantment etc.)
    """

    search_fields = ["name"]


@admin.register(CardSubtype)
class CardSubtypeAdmin(admin.ModelAdmin):
    """
    Admin for a card's subtype (Unicorn, Swamp, Equipment etc.)
    """

    search_fields = ["name"]


@admin.register(CardSupertype)
class CardSupertypeAdmin(admin.ModelAdmin):
    """
    Admin for a card's Supertype (Basic, Legendary etc.)
    """

    search_fields = ["name"]


class CardRulingModelForm(forms.ModelForm):
    """
    Form for a card's rulings (to override widgets and such)
    """

    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CardRuling
        fields = ["card", "date", "text"]


@admin.register(CardRuling)
class CardRulingAdmin(admin.ModelAdmin):
    """
    Admin for a card's Rulings
    """

    search_fields = ["card__name"]
    autocomplete_fields = ["card"]
    form = CardRulingModelForm


@admin.register(CardLegality)
class CardLegalityAdmin(admin.ModelAdmin):
    """
    Admin for a card's legalities
    """

    search_fields = ["card__name"]
    autocomplete_fields = ["card"]


@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    """
    Admin for a Format
    """


@admin.register(CardPrinting)
class CardPrintingAdmin(admin.ModelAdmin):
    """
    Admin for a Card Printing (card in a set)
    """

    autocomplete_fields = ["card", "set", "latest_price"]
    search_fields = ["card__name", "scryfall_id"]
    # readonly_fields = ["latest_price"]
    inlines = [CardFacePrintingInline, CardLocalisationInline]


class CardFacePrintingModelForm(forms.ModelForm):
    """
    Form for a Card Face Printing (one side of card, printed in a set)
    """

    flavour_text = forms.CharField(widget=forms.Textarea, required=False)
    original_text = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CardFacePrinting
        fields = [
            "uuid",
            "flavour_text",
            "artist",
            "scryfall_illustration_id",
            "original_text",
            "original_type",
            "watermark",
            "card_face",
            "card_printing",
            "frame_effects",
        ]


@admin.register(CardFacePrinting)
class CardFacePrintingAdmin(admin.ModelAdmin):
    """
    Admin for a Card Face Printing (one side of a card, printed in a set)
    """

    autocomplete_fields = ["card_face", "card_printing"]
    search_fields = ["card_face__card__name", "uuid", "scryfall_illustration_id"]
    form = CardFacePrintingModelForm
    inlines = [CardFaceLocalisationInline]


@admin.register(CardLocalisation)
class CardLocalisationAdmin(admin.ModelAdmin):
    """
    Admin for a card localisation (a card printed in a set with a certain language)
    """

    autocomplete_fields = ["card_printing"]
    search_fields = ["card_name", "multiverse_id", "card_printing__scryfall_id"]
    inlines = [CardFaceLocalisationInline]


class CardFaceLocalisationModelForm(forms.ModelForm):
    """
    Form for Card Face Localisation (a face of a card printed in some set in some language)
    """

    text = forms.CharField(widget=forms.Textarea)
    flavour_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CardFaceLocalisation
        fields = [
            "localisation",
            "card_printing_face",
            "face_name",
            "flavour_text",
            "type",
            "text",
            "image",
        ]


@admin.register(CardFaceLocalisation)
class CardFaceLocalisationAdmin(admin.ModelAdmin):
    """
    Admin for a Card Face Localisation (a face of a card printed in some set in some language)
    """

    autocomplete_fields = ["localisation", "card_printing_face", "image"]
    form = CardFaceLocalisationModelForm


@admin.register(CardImage)
class CardImageAdmin(admin.ModelAdmin):
    """
    Admin for a Card Image model
    """

    search_fields = ["file_path", "scryfall_image_url"]


@admin.register(CardPrice)
class CardPriceAdmin(admin.ModelAdmin):
    """
    Admin for a card's price at some time
    """

    autocomplete_fields = ["card_printing"]
    search_fields = ["card_printing"]


class DeckCardInline(admin.TabularInline):
    """
    Form for a card in a deck
    """

    model = DeckCard

    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Deck)
class DeckAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    """
    Admin for a deck of cards
    """

    search_fields = ["name", "cards__card__name", "owner__username"]
    list_display = ["name", "date_created", "owner", "format"]
    list_filter = ["owner", "format"]
    inlines = [DeckCardInline]


@admin.register(UserOwnedCard)
class UserOwnedCardAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["card_localisation", "owner"]


@admin.register(UserCardChange)
class UserCardChangeAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["card_localisation", "owner"]
    list_display = ["card_localisation", "date", "difference"]


@admin.register(FrameEffect)
class FrameEffectAdmin(admin.ModelAdmin):
    pass
