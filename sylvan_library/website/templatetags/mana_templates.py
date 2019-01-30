"""
Module for a custom template filter to replace mana symbols such as {G} and {2/R} with mana tags
"""

import re

from django import template

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name='replace_mana_symbols')
def replace_mana_symbols(text: str, scale: str = None) -> str:
    """
    Converts any mana symbols in the given string with CSS images
    :param text: The text to replace the
    :param scale: The size of the image (either lg, 2x, 3x, 4x or 5x)
    :return: The text with all mana symbols converted to icons
    """
    shadow = False

    if text is None:
        return ''

    def replace_symbol(match):
        """
        Replaces the given symbol with its colour tag
        (or multiple colour tags in the case of hybrid mana)

        This function is nested so that it can access the values of the outer function,
        and it can't have arguments passed in as it is used in an re.sub() call
        :param match: The tet match to be replaced
        :return: The resulting symbol
        """
        classes = ['ms']

        if scale is not None:
            classes.append(f'ms-{scale}x')

        if shadow:
            classes.append('ms-shadow')

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

        classes.append(f'ms-{symbol}')
        classes.append(f'ms-cost')

        return '<i class="' + ' '.join(classes) + '"></i>'

    return re.sub(r'{(.+?)}', replace_symbol, text)
