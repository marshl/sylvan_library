"""
Models for Colour objects
"""
from functools import reduce
from typing import List, Dict
from django.db import models


class Colour(models.Model):
    """
    Model for a card's colour
    """

    symbol = models.CharField(max_length=1, unique=True)
    name = models.CharField(max_length=15, unique=True)
    display_order = models.IntegerField(unique=True)
    bit_value = models.IntegerField(unique=True)
    chart_colour = models.CharField(max_length=20)

    @staticmethod
    def white() -> "Colour":
        """
        Gets the colour object for white
        :return:
        """
        return Colour.objects.get(symbol="W")

    @staticmethod
    def blue() -> "Colour":
        """
        Gets the colour object for blue
        :return:
        """
        return Colour.objects.get(symbol="U")

    @staticmethod
    def black() -> "Colour":
        """
        Gets the colour object for black
        :return:
        """
        return Colour.objects.get(symbol="B")

    @staticmethod
    def red() -> "Colour":
        """
        Gets the colour object for red
        :return:
        """
        return Colour.objects.get(symbol="R")

    @staticmethod
    def green() -> "Colour":
        """
        Gets the colour object for green
        :return:
        """
        return Colour.objects.get(symbol="G")

    @staticmethod
    def colourless() -> "Colour":
        """
        Gets the colour object for green
        :return:
        """
        return Colour.objects.get(symbol="C")

    @staticmethod
    def colour_names_to_flags(colour_names: List[str]) -> int:
        """
        Converts a list of colour names into the combined flags of those colours
        :param colour_names:
        :return:
        """
        flags = 0
        for colour_name in colour_names:
            flags |= Colour.objects.get(name__iexact=colour_name).bit_value

        return flags

    @staticmethod
    def colour_codes_to_flags(colour_codes: List[str]) -> int:
        """
        Converts a list of colour codes to the combined flags of those colours
        :param colour_codes: A list of colour codes (single characters representing the colours)
        :return: The combined colour flags
        """
        flags = 0
        for symbol in colour_codes:
            flags |= Colour.objects.get(symbol__iexact=symbol).bit_value

        return flags

    def __str__(self) -> str:
        return self.name


ALL_COLOURS = list(Colour.objects.all().order_by("display_order"))
WHITE, BLUE, BLACK, RED, GREEN, COLOURLESS = ALL_COLOURS


def colours_to_int_flags(colours: List[Colour]) -> int:
    """
    Converts a list of colour flags to an int
    :param colours: The list of colours
    :return: The combined integer version of those flags
    Note that this will basically "remove" colourless
    """
    return reduce(lambda x, y: x.bit_value | y.bit_value, colours)


COLOUR_NAME_LOOKUP: Dict[str, List[Colour]] = {
    "colourless": [COLOURLESS],
    "c": [COLOURLESS],
    "white": [WHITE],
    "w": [WHITE],
    "blue": [BLUE],
    "u": [BLUE],
    "black": [BLACK],
    "b": [BLACK],
    "red": [RED],
    "r": [RED],
    "green": [GREEN],
    "g": [GREEN],
    "azorius": [WHITE, BLUE],
    "dimir": [BLUE, BLACK],
    "rakdos": [BLACK, RED],
    "gruul": [RED, GREEN],
    "selesnya": [GREEN, WHITE],
    "orzhov": [WHITE, BLACK],
    "izzet": [BLUE, RED],
    "golgari": [BLACK, GREEN],
    "boros": [RED, WHITE],
    "simic": [GREEN, BLUE],
    "esper": [WHITE, BLUE, BLACK],
    "grixis": [BLUE, BLACK, RED],
    "jund": [BLACK, RED, GREEN],
    "naya": [RED, GREEN, WHITE],
    "bant": [GREEN, WHITE, BLUE],
    "abzan": [WHITE, BLACK, GREEN],
    "jeskai": [BLUE, RED, WHITE],
    "sultai": [BLACK, GREEN, BLUE],
    "mardu": [RED, WHITE, BLACK],
    "temur": [GREEN, BLUE, RED],
    "chaos": [BLUE, BLACK, RED, GREEN],
    "aggression": [BLACK, RED, GREEN, WHITE],
    "altruism": [RED, GREEN, WHITE, BLUE],
    "growth": [GREEN, WHITE, BLUE, BLACK],
    "artifice": [WHITE, BLUE, BLACK, RED],
    "all": [WHITE, BLUE, BLACK, RED, GREEN],
}


def get_colours_for_nickname(colour_name: str) -> List[Colour]:
    """
    Converts text to a list of colour flag
    Raises a value error if the text doesn't match any known colours
    :param colour_name: The colour text to parse
    :return: The colours or'd together
    """
    text = colour_name.lower()
    if text in COLOUR_NAME_LOOKUP:
        return COLOUR_NAME_LOOKUP[text]

    result = []
    for char in text:
        if char not in COLOUR_NAME_LOOKUP:
            raise ValueError(f"Unknown colour {text}")

        result += COLOUR_NAME_LOOKUP[char]
    return result


def colours_to_symbols(colours: List[Colour]) -> str:
    """
    Converts colours flags to symbols
    :param colours: The colours to convert to symbols
    :return: The symbols of the given colours
    """
    return "".join(colour.symbol for colour in colours)
