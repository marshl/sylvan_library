"""
Models for Colour objects
"""
from functools import reduce
from typing import List, Dict, Optional
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

    WHITE = 1
    BLUE = 2
    BLACK = 4
    RED = 8
    GREEN = 16

    _white = None
    _blue = None
    _black = None
    _red = None
    _green = None
    _colourless = None

    @staticmethod
    def white() -> "Colour":
        """
        Gets the colour object for white
        :return:
        """
        if not Colour._white:
            Colour._white = Colour.objects.get(symbol="W")
        return Colour._white

    @staticmethod
    def blue() -> "Colour":
        """
        Gets the colour object for blue
        :return:
        """
        if not Colour._blue:
            Colour._blue = Colour.objects.get(symbol="U")
        return Colour._blue

    @staticmethod
    def black() -> "Colour":
        """
        Gets the colour object for black
        :return:
        """
        if not Colour._black:
            Colour._black = Colour.objects.get(symbol="B")
        return Colour._black

    @staticmethod
    def red() -> "Colour":
        """
        Gets the colour object for red
        :return:
        """
        if not Colour._red:
            Colour._red = Colour.objects.get(symbol="R")
        return Colour._red

    @staticmethod
    def green() -> "Colour":
        """
        Gets the colour object for green
        :return:
        """
        if not Colour._green:
            Colour._green = Colour.objects.get(symbol="G")
        return Colour._green

    @staticmethod
    def colourless() -> "Colour":
        """
        Gets the colour object for green
        :return:
        """
        # return Colour.objects.get(symbol="C")
        if not Colour._colourless:
            Colour._colourless = Colour.objects.get(symbol="C")
        return Colour._colourless

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
            flags |= COLOUR_SYMBOLS_TO_CODES[symbol.upper()]

        return flags

    def __str__(self) -> str:
        return self.name


COLOUR_SYMBOLS_TO_CODES = {
    "W": Colour.WHITE,
    "U": Colour.BLUE,
    "B": Colour.BLACK,
    "R": Colour.RED,
    "G": Colour.GREEN,
}


# ALL_COLOURS = list(Colour.objects.all().order_by("display_order"))
# WHITE, BLUE, BLACK, RED, GREEN, COLOURLESS = ALL_COLOURS


def colours_to_int_flags(colours: List[Colour]) -> int:
    """
    Converts a list of colour flags to an int
    :param colours: The list of colours
    :return: The combined integer version of those flags
    Note that this will basically "remove" colourless
    """
    return reduce(lambda x, y: x | y, (c.bit_value for c in colours))


_COLOUR_NAME_LOOKUP: Optional[Dict[str, List[Colour]]] = None


def get_colours_for_nickname(colour_name: str) -> List[Colour]:
    """
    Converts text to a list of colour flag
    Raises a value error if the text doesn't match any known colours
    :param colour_name: The colour text to parse
    :return: The colours or'd together
    """
    # pylint: disable=global-statement
    global _COLOUR_NAME_LOOKUP
    if not _COLOUR_NAME_LOOKUP:
        _COLOUR_NAME_LOOKUP = {
            "colourless": [Colour.colourless()],
            "c": [Colour.colourless()],
            "white": [Colour.white()],
            "w": [Colour.white()],
            "blue": [Colour.blue()],
            "u": [Colour.blue()],
            "black": [Colour.black()],
            "b": [Colour.black()],
            "red": [Colour.red()],
            "r": [Colour.red()],
            "green": [Colour.green()],
            "g": [Colour.green()],
            "azorius": [Colour.white(), Colour.blue()],
            "dimir": [Colour.blue(), Colour.black()],
            "rakdos": [Colour.black(), Colour.red()],
            "gruul": [Colour.red(), Colour.green()],
            "selesnya": [Colour.green(), Colour.white()],
            "orzhov": [Colour.white(), Colour.black()],
            "izzet": [Colour.blue(), Colour.red()],
            "golgari": [Colour.black(), Colour.green()],
            "boros": [Colour.red(), Colour.white()],
            "simic": [Colour.green(), Colour.blue()],
            "esper": [Colour.white(), Colour.blue(), Colour.black()],
            "grixis": [Colour.blue(), Colour.black(), Colour.red()],
            "jund": [Colour.black(), Colour.red(), Colour.green()],
            "naya": [Colour.red(), Colour.green(), Colour.white()],
            "bant": [Colour.green(), Colour.white(), Colour.blue()],
            "abzan": [Colour.white(), Colour.black(), Colour.green()],
            "jeskai": [Colour.blue(), Colour.red(), Colour.white()],
            "sultai": [Colour.black(), Colour.green(), Colour.blue()],
            "mardu": [Colour.red(), Colour.white(), Colour.black()],
            "temur": [Colour.green(), Colour.blue(), Colour.red()],
            "chaos": [Colour.blue(), Colour.black(), Colour.red(), Colour.green()],
            "aggression": [
                Colour.black(),
                Colour.red(),
                Colour.green(),
                Colour.white(),
            ],
            "altruism": [Colour.red(), Colour.green(), Colour.white(), Colour.blue()],
            "growth": [Colour.green(), Colour.white(), Colour.blue(), Colour.black()],
            "artifice": [Colour.white(), Colour.blue(), Colour.black(), Colour.red()],
            "all": [
                Colour.white(),
                Colour.blue(),
                Colour.black(),
                Colour.red(),
                Colour.green(),
            ],
        }

    text = colour_name.lower()
    if text in _COLOUR_NAME_LOOKUP:
        return _COLOUR_NAME_LOOKUP[text]

    result = []
    for char in text:
        if char not in _COLOUR_NAME_LOOKUP:
            raise ValueError(f"Unknown colour {text}")

        result += _COLOUR_NAME_LOOKUP[char]
    return result


def colours_to_symbols(colours: List[Colour]) -> str:
    """
    Converts colours flags to symbols
    :param colours: The colours to convert to symbols
    :return: The symbols of the given colours
    """
    return "".join(colour.symbol for colour in colours)
