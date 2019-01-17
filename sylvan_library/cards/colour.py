"""
Utility class for colours
"""


class ColourUtils:
    white = 1
    blue = 2
    black = 4
    red = 8
    green = 16

    all = white | blue | black | red | green
    none = 0

    colour_name_to_flag = {
        'white': white,
        'blue': blue,
        'black': black,
        'red': red,
        'green': green,
    }

    colour_code_to_flag = {
        'w': white,
        'u': blue,
        'b': black,
        'r': red,
        'g': green,
    }

    @staticmethod
    def colour_names_to_flags(colour_names: list) -> int:
        flags = 0
        for colour in colour_names:
            flags |= ColourUtils.colour_name_to_flag[colour.lower()]

        return flags

    @staticmethod
    def colour_codes_to_flags(colour_codes: list) -> int:
        flags = 0
        for colour in colour_codes:
            flags |= ColourUtils.colour_code_to_flag[colour.lower()]

        return flags
