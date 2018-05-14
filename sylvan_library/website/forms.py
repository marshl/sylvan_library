from django import forms
from cardsearch import parameters


class SearchForm(forms.Form):
    card_name = forms.CharField(required=False)
    rules_text = forms.CharField(required=False)
    cmc = forms.IntegerField(required=False)
    cmc_operator = forms.ChoiceField(parameters.NUMERICAL_OPERATOR_CHOICES, required=False)

    colour_white = forms.BooleanField(required=False)
    colour_blue = forms.BooleanField(required=False)
    colour_black = forms.BooleanField(required=False)
    colour_red = forms.BooleanField(required=False)
    colour_green = forms.BooleanField(required=False)

    exclude_colours = forms.BooleanField(required=False)
    match_colours = forms.BooleanField(required=False)
