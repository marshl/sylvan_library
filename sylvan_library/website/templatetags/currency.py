"""
Module for a custom template filter to replace mana symbols such as {G} and {2/R} with mana tags
"""

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter(name="currency")
def currency(dollars: float, currency_unit="dollars"):
    dollars = round(float(dollars), 2)
    dollar_string = "%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
    if currency_unit == "tickets":
        return "{} TIX".format(dollar_string)
    return "${}".format(dollar_string)
