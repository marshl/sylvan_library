import re

from django import template

register = template.Library()


@register.filter(name='replace_mtg_font_symbols')
def replace_mtg_font_symbols(value, scale=None):
    shadow = False

    if value is None:
        return None

    def get_colour_tag(symbol: str, phyrexian=False, split=False):

        if symbol == 't':
            symbol = 'tap'
        elif symbol == 'q':
            symbol = 'untap'

        classes = ['mi']

        if scale is not None:
            classes.append(f'mi-{scale}x')

        if shadow:
            classes.append('mi-shadow')

        if phyrexian:
            classes.append('mi-p')
            classes.append(f'mi-mana-{symbol}')
        else:
            classes.append(f'mi-{symbol}')

            if symbol not in ['chaos', 'e'] and not split:
                classes.append('mi-mana')

        return '<i class="' + ' '.join(classes) + '"></i>'

    def replace_symbol(match):
        grp = match.groups()[0].lower()
        if '/' in grp:
            if grp[-1] == 'p':
                return get_colour_tag(grp[0], phyrexian=True)
            else:
                return '<span class="mi-split">' + ' '.join([get_colour_tag(x, split=True) for x in grp.split('/')]) + '</span>'
        else:
            return get_colour_tag(grp)

    return re.sub(r'{(.+?)}', replace_symbol, value)
