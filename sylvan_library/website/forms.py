from django import forms
from cardsearch import parameters


class SearchForm(forms.Form):
    card_name = forms.CharField(required=False)
    rules_text = forms.CharField(required=False)
    cmc = forms.IntegerField(required=False)
    cmc_operator = forms.ChoiceField(parameters.NUMERICAL_OPERATOR_CHOICES , required=False)
