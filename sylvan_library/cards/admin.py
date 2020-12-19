# from bitfield.forms import BitFieldCheckboxSelectMultiple
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django import forms
from django.contrib import admin
from django_admin_relation_links import AdminChangeLinksMixin

from cards.models import Block, Set, Card, CardFace, CardRuling, CardType, CardSupertype, CardSubtype


# class CardFaceInline(admin.TabularInline):
#     model = CardFace
#     def has_change_permission(self, request, obj=None):
#         return False
#
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False
# from fields import BitFieldCheckboxSelectMultiple
# from fields import BitFieldCheckboxSelectMultiple, BitFormField
from widgets import ColourWidget


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

    # class Meta:
    #     name = forms.IntegerField()


# class CardFaceAdminForm(forms.ModelForm):


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):  # AdminChangeLinksMixin,
    # form = CardAdminForm
    search_fields = ["name"]
    # changelist_links = ['faces']
    inlines = [CardFaceInline]


class CardFaceModelForm(forms.ModelForm):
    rules_text = forms.CharField(widget=forms.Textarea)
    # colour = forms.IntegerField(widget=ColourWidget)
    # colour = forms.IntegerField(
    #     widget=BitFieldCheckboxSelectMultiple(
    #         choices=((1, "W"), (2, "U"), (4, "B"), (8, "R"), (16, "G"))
    #     )
    # )
    # colour = BitFormField(choices=((1, "W"), (2, "U"), (4, "B"), (8, "R"), (16, "G")))
    # colour_indicator = forms.IntegerField(widget=BitFieldCheckboxSelectMultiple)

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
