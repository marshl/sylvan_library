"""
Module for a custom template filter to replace mana symbols such as {G} and {2/R} with mana tags
"""

import re

from django import template

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name='replace_loyalty_symbols')
def replace_loyalty_symbols(text: str, scale: str = None) -> str:
    """
    Converts any loyalty costs in the given string with CSS images
    :param text: The text to change
    :param scale: The size of the icons (either lg, 2x, 3x, 4x or 5x)
    :return: The text with all loyalty costs converted to icons
    """
    def replace_symbol(loyalty_match):
        """
        Replaces the given symbol with its loyalty tag

        This function is nested so that it can access the values of the outer function,
        and it can't have arguments passed in as it is used in an re.sub() call
        :param loyalty_match: The text match to be replaced
        :return: The resulting symbol
        """
        m = re.search('(?P<sign>[+−]?)(?P<number>[\dx]+)', loyalty_match.group())
        sign = m.group('sign')
        number = m.group('number')
        classes = ['ms', 'ms-loyalty-' + number, 'ms-2x']
        if scale is not None:
            classes.append(f'ms-{scale}')

        if sign == '−':
            classes.append('ms-loyalty-down')
        elif sign == '+':
            classes.append('ms-loyalty-up')
        else:
            classes.append('ms-loyalty-zero')

        return '<i class="' + ' '.join(classes) + '"></i>'

    return re.sub(r'([−+]?[\dx]+?)(?=:)', replace_symbol, text)


@register.filter(name='replace_mana_symbols')
def replace_mana_symbols(text: str, scale: str = None) -> str:
    """
    Converts any mana symbols in the given string with CSS images
    :param text: The text to replace the
    :param scale: The size of the image (either lg, 2x, 3x, 4x or 5x)
    :return: The text with all mana symbols converted to icons
    """

    if text is None:
        return ''

    def replace_symbol(match):
        """
        Replaces the given symbol with its colour tag

        This function is nested so that it can access the values of the outer function,
        and it can't have arguments passed in as it is used in an re.sub() call
        :param match: The text match to be replaced
        :return: The resulting symbol
        """
        classes = ['ms']

        if scale is not None:
            classes.append(f'ms-{scale}')

        grp = match.groups()[0].lower()
        symbol = grp
        if '/' in grp:
            if grp[-1] == 'p':
                classes.append('ms-p')
                symbol = grp[0]
            else:
                symbol = grp.replace('/', '')

        if symbol == 't':
            symbol = 'tap'
        elif symbol == 'q':
            symbol = 'untap'

        if len(symbol) == 2 and symbol[0].lower() == 'h':
            classes.append('ms-half')
            symbol = symbol[1]

        classes.append(f'ms-{symbol}')
        classes.append(f'ms-cost')

        return '<i class="' + ' '.join(classes) + '"></i>'

    return re.sub(r'{(.+?)}', replace_symbol, text)


@register.filter(name='shadowed')
def shadowed(text: str) -> str:
    """
    Adds a shadow to any mana symbols in the given text
    :param text: The text to replace the
    :return: The text with all mana icons with a shadow added
    """
    if text is None:
        return ''

    return text.replace('ms-cost', 'ms-cost ms-shadow')
