"""
Forms for the website module
"""

from django import forms
from cardsearch import parameters
from cards.models import CardPrinting, Language


def get_physical_card_key_pair(physical_card, printing):
    return physical_card.id, f'{physical_card} ({printing.number})'


class ChangeCardOwnershipForm(forms.Form):
    count = forms.IntegerField()
    printed_language = forms.ChoiceField(widget=forms.Select)

    def __init__(self, printing: CardPrinting):
        super().__init__()
        if any(pl for pl in printing.printed_languages.all()
               if pl.language_id == Language.english().id):
            english_print = next(pl for pl in printing.printed_languages if pl.language_id == Language.english().id)
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
    cmc = forms.IntegerField(required=False)
    cmc_operator = forms.ChoiceField(choices=parameters.NUMERICAL_OPERATOR_CHOICES, required=False)

    exclude_colours = forms.BooleanField(required=False)
    match_colours = forms.BooleanField(required=False)

    exclude_colours_identity = forms.BooleanField(required=False)
    match_colours_identity = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for colour in self.colour_list():
            self.fields['colour_' + colour] = forms.BooleanField(required=False)
            self.fields['colourid_' + colour] = forms.BooleanField(required=False)

    def colour_list(self) -> dict:
        """
        Gets the list of colours to be used in the form
        :return: A dict of colours
        """
        return {
            'white': 'w',
            'blue': 'u',
            'black': 'b',
            'red': 'r',
            'green': 'g',
            'colourless': 'c'
        }

    def colour_fields(self) -> dict:
        """
        Gets all the colour fields
        :return:
        """
        for colour, symbol in self.colour_list().items():
            yield {'field': self['colour_' + colour], 'symbol': symbol}

    def colour_identity_fields(self) -> dict:
        """
        Gets all the colour identity fields
        :return: A dictionary of fields
        """
        for colour, symbol in self.colour_list().items():
            yield {'field': self['colourid_' + colour], 'symbol': symbol}
