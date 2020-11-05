"""
Module for a custom template filter to replace mana symbols such as {G} and {2/R} with mana tags
"""

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter(name="currency")
def currency(value: float, currency_unit="dollars"):
    """
    Converts a given monetary amount into a string
    :param value: The given monetary amount
    :param currency_unit: The monetary unit (pounds, dollars, tickets)
    :return: The formatted string
    """
    value = round(float(value), 2)
    value_string = "%s%s" % (intcomma(int(value)), ("%0.2f" % value)[-3:])
    if currency_unit == "tickets":
        return "{} TIX".format(value_string)
    return "${}".format(value_string)
