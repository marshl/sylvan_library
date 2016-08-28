
colour_name_to_flag = {
    'white': 1,
    'blue': 2,
    'black': 4,
    'red': 8,
    'green': 16,
}

colour_code_to_flag = {
    'w': 1,
    'u': 2,
    'b': 4,
    'r': 8,
    'g': 16,
}


def get_colour_flags_from_names(colour_names):
    flags = 0
    for colour in colour_names:
        flags |= colour_name_to_flag[colour.lower()]

    return flags


def get_colour_flags_from_codes(colour_codes):
    flags = 0
    for colour in colour_codes:
        flags |= colour_code_to_flag[colour.lower()]

    return flags
