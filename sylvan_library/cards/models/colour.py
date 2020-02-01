"""
Models for Colour objects
"""
from typing import List
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
