from django import forms


class SearchForm(forms.Form):
    card_name = forms.CharField()
    rules_text = forms.CharField()
