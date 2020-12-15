from django import forms


class ColourWidget(forms.widgets.NumberInput):
    # pass
    template_name = "forms/widgets/number.html"
