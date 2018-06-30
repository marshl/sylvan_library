from django import forms
from cardsearch import parameters


class SearchForm(forms.Form):
    card_name = forms.CharField(required=False)
    rules_text = forms.CharField(required=False)
    cmc = forms.IntegerField(required=False)
    cmc_operator = forms.ChoiceField(parameters.NUMERICAL_OPERATOR_CHOICES, required=False)

    exclude_colours = forms.BooleanField(required=False)
    match_colours = forms.BooleanField(required=False)

    exclude_colours_identity = forms.BooleanField(required=False)
    match_colours_identity = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        for colour in ['white', 'blue', 'black', 'red', 'green', 'colourless']:
            self.fields['colour_' + colour] = forms.BooleanField(required=False)
            self.fields['colourid_'] = forms.BooleanField(required=False)

    def colour_fields(self):
        for colour, symbol in {
            'white': 'w',
            'blue': 'u',
            'black': 'b',
            'red': 'r',
            'green': 'g',
            'colourless': 'c'
        }.items():
            yield {'field': self['colour_' + colour], 'symbol': symbol}
            # for name in self.fields:
            #    if name.startswith('colour_'):
            #        yield {'field': self[name], 'symbol': 'r'}
