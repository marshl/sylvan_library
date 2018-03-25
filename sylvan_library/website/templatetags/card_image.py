from os import path
from django import template
from cards.models import Card, CardPrinting, CardPrintingLanguage, Language

register = template.Library()


def get_card_printing_language_url(printed_language: CardPrintingLanguage):
    ms = str(printed_language.multiverse_id)

    # Break up images over multiple folders to stop too many being placed in one folder
    return path.join('card_images',
                     ms[0:1],
                     ms[0:2] if len(ms) >= 2 else '',
                     ms[0:3] if len(ms) >= 3 else '',
                     ms + '.jpg')


@register.filter(name='card_printing_language_image_url')
def card_printing_language_image_url(printed_language: CardPrintingLanguage):
    return get_card_printing_language_url(printed_language)


@register.filter(name='card_printing_image_url')
def card_printing_image_url(card_printing: CardPrinting):
    printed_language = card_printing.printed_languages.get(language=Language.objects.get(name='English'))
    return get_card_printing_language_url(printed_language)


@register.filter(name='card_image_url')
def card_image_url(card: Card):
    printing = card.printings.order_by('-set__release_date').first()

    if not printing:
        return path.join('static', 'card_images', 'card_back.jpg')

    return card_printing_image_url(printing)
