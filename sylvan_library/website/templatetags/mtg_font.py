"""
Module for custom template filter to replace mana symbols such as {G} and {2/R} with MTGFont tags
"""

import re

from django import template

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name='replace_mtg_font_symbols')
def replace_mtg_font_symbols(text: str, scale: str = None) -> str:
    """
    Converts any mana symbols in the given string with CSS images
    :param text: The text to replace the
    :param scale: The size of the image (either lg, 2x, 3x, 4x or 5x)
    :return: The text with all mana symbols converted to icons
    """
    shadow = False

    if text is None:
        return None

    def get_colour_tag(symbol: str, is_phyrexian: bool = False, is_split: bool = False) -> str:
        """
        Converts a single colour string into it's corresponding tag

        :param symbol: The symbol to replace (e.g. {B}, {11}, {W/P}
        :param is_phyrexian: Whether this symbol is phyrexian or not
        :param is_split: Whether this is a split symbol or not
        :return:
        """
        if symbol == 't':
            symbol = 'tap'
        elif symbol == 'q':
            symbol = 'untap'

        classes = ['mi']

        if scale is not None:
            classes.append(f'mi-{scale}x')

        if shadow:
            classes.append('mi-shadow')

        if is_phyrexian:
            classes.append('mi-p')
            classes.append(f'mi-mana-{symbol}')
        else:
            classes.append(f'mi-{symbol}')

            if symbol not in ['chaos', 'e'] and not is_split:
                classes.append('mi-mana')

        return '<i class="' + ' '.join(classes) + '"></i>'

    def replace_symbol(match):
        """
        Replaces the given symbol with its colour tag
        (or multiple colour tags in the case of hybrid mana)

        This function is nested so that it can access the values of the outer function,
        and it can't have arguments passed in as it is used in an re.sub() call
        :param match: The tet match to be replaced
        :return: The resulting symbol
        """
        grp = match.groups()[0].lower()
        if '/' in grp:
            if grp[-1] == 'p':
                return get_colour_tag(grp[0], is_phyrexian=True)
            else:
                return '<span class="mi-split">' + ' '.join(
                    [get_colour_tag(x, is_split=True) for x in grp.split('/')]) + '</span>'
        else:
            return get_colour_tag(grp)

    return re.sub(r'{(.+?)}', replace_symbol, text)
