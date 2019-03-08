"""
Forms for the website module
"""

from django import forms
from django_select2.forms import Select2MultipleWidget

from cards.models import CardPrinting, Colour, Language, Rarity, Set


def get_physical_card_key_pair(physical_card, printing):
    return physical_card.id, f'{physical_card} ({printing.number})'


class ChangeCardOwnershipForm(forms.Form):
    count = forms.IntegerField()
    printed_language = forms.ChoiceField(widget=forms.Select)

    def __init__(self, printing: CardPrinting):
        super().__init__()
        if any(pl for pl in printing.printed_languages.all()
               if pl.language_id == Language.english().id):
            english_print = next(pl for pl in printing.printed_languages.all()
                                 if pl.language_id == Language.english().id)
            choices = [get_physical_card_key_pair(physical_card, printing)
                       for physical_card in english_print.physical_cards.all()]
            choices.extend([
                get_physical_card_key_pair(physical_card, printing)
                for lang in printing.printed_languages.all()
                for physical_card in lang.physical_cards.all()
                if lang.language_id != Language.english().id
            ])
        else:
            choices = [
                get_physical_card_key_pair(physical_card, printing)
                for lang in printing.printed_languages.all()
                for physical_card in lang.physical_cards.all()
            ]

        self.fields['printed_language'].choices = choices


class SearchForm(forms.Form):
    """
    The primary search form
    """
    card_name = forms.CharField(required=False)
    rules_text = forms.CharField(required=False)
    flavour_text = forms.CharField(required=False)
    type_text = forms.CharField(required=False)
    subtype_text = forms.CharField(required=False)

    min_cmc = forms.IntegerField(required=False)
    max_cmc = forms.IntegerField(required=False)

    min_power = forms.IntegerField(required=False)
    max_power = forms.IntegerField(required=False)

    min_toughness = forms.IntegerField(required=False)
    max_toughness = forms.IntegerField(required=False)

    exclude_colours = forms.BooleanField(required=False)
    match_colours = forms.BooleanField(required=False)

    exclude_colourids = forms.BooleanField(required=False)
    match_colourids = forms.BooleanField(required=False)

    match_rarity = forms.BooleanField(required=False)

    sets = forms.ModelMultipleChoiceField(queryset=Set.objects.all().order_by('-release_date'),
                                          widget=Select2MultipleWidget, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for colour in Colour.objects.all().order_by('display_order'):
            self.fields['colour_' + colour.symbol.lower()] = forms.BooleanField(required=False)
            self.fields['colourid_' + colour.symbol.lower()] = forms.BooleanField(required=False)

        for rarity in Rarity.objects.all().order_by('display_order'):
            self.fields['rarity_' + rarity.symbol.lower()] = forms.BooleanField(required=False)

    def colour_fields(self) -> dict:
        """
        Gets all the colour fields
        :return:
        """
        return {colour.symbol.lower(): self['colour_' + colour.symbol.lower()]
                for colour in Colour.objects.all().order_by('display_order')}

    def colourid_fields(self) -> dict:
        """
        Gets all the colour identity fields
        :return: A dictionary of fields
        """
        return {colour.symbol.lower(): self['colourid_' + colour.symbol.lower()]
                for colour in Colour.objects.all().order_by('display_order')}

    def is_colour_enabled(self) -> bool:
        return any(field.data for symbol, field in self.colour_fields().items())

    def is_colourid_enabled(self) -> bool:
        return any(field.data for symbol, field in self.colourid_fields().items())

    def rarity_fields(self) -> dict:
        """
        Gets a dictionary of the rarity fields
        :return:
        """
        return {r.symbol.lower(): self['rarity_' + r.symbol.lower()]
                for r in Rarity.objects.all().order_by('display_order')}

    def is_rarity_enabled(self) -> bool:
        """
        Gets whether any rarity fields are currently enabled
        :return: True if any rarity fields are set, otherwise False
        """
        return any(field.data for key, field in self.rarity_fields().items())
