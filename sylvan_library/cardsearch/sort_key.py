import re

from django.utils.text import slugify

from sylvan_library.cards.models.card import Card, CardFace
from sylvan_library.cards.models.colour import (
    Colour,
    COLOUR_SYMBOLS_TO_CODES,
    COLOUR_TO_SORT_KEY,
)

RE_GENERIC_MANA = re.compile(r"{(\d+)}")


def get_sort_key(card: Card) -> str:
    return "-".join(
        [f"{part:02}" for part in get_sort_key_parts(card)] + [slugify(card.name)]
    )


def get_sort_key_parts(card: Card) -> list[int]:
    face_count = len(card.faces.all())
    is_split = face_count == 2 and card.layout in ("split", "room")
    sortable_faces = list(card.faces.all()) if is_split else [card.faces.all()[0]]

    is_land = any(
        _type.name == "Land" for face in sortable_faces for _type in face.types.all()
    )

    if is_land:
        return get_land_sort_key_parts(card, sortable_faces)
    return get_nonland_sort_key_parts(card, sortable_faces)


def get_land_sort_key_parts(card: Card, sortable_faces: list[CardFace]) -> list[int]:
    parts = [1]

    colour_identity = int(card.colour_identity)

    search_identity = 0

    for land_name, flag in {
        "Plains": Colour.WHITE,
        "Island": Colour.BLUE,
        "Swamp": Colour.BLACK,
        "Mountain": Colour.RED,
        "Forest": Colour.GREEN,
    }.items():
        for card_face in sortable_faces:
            if not card_face.rules_text:
                continue

            lower_rules = card_face.rules_text.lower()
            if (
                land_name in card_face.rules_text
                and "sacrifice" in lower_rules
                and "search" in lower_rules
                and "onto the battlefield" in lower_rules
            ):
                search_identity |= flag

    produces_mana = 0
    for symbol, flag in COLOUR_SYMBOLS_TO_CODES.items():
        for face in sortable_faces:
            result = re.search(
                r"adds?\W[^\n.]*?{" + symbol + "}", face.rules_text, re.IGNORECASE
            )
            if result:
                produces_mana |= flag

    is_basic = any(
        supertype.name == "Basic"
        for face in sortable_faces
        for supertype in face.supertypes.all()
    )

    parts.append(1 if is_basic else 0)
    parts.append(50 - COLOUR_TO_SORT_KEY[colour_identity | search_identity])
    parts.append(50 - COLOUR_TO_SORT_KEY[produces_mana | search_identity])

    return parts


def get_sort_colour_key(sortable_faces: list[CardFace], is_artifact: bool) -> int:
    colour_overrides = {
        "Urborg, Tomb of Yawgmoth": Colour.BLACK,
        "Yavimaya, Cradle of Growth": Colour.GREEN,
        "Crumbling Vestige": Colour.COLOURLESS,
        "Forgotten Monument": Colour.COLOURLESS,
    }

    if sortable_faces[0].name in colour_overrides:
        return colour_overrides[sortable_faces[0].name]

    sortable_colour = 0
    if (
        "Devoid" in (sortable_faces[0].rules_text or "")
        or sortable_faces[0].name == "Ghostfire"
    ):
        for symbol, colour in COLOUR_SYMBOLS_TO_CODES.items():
            if any(
                face.mana_cost and symbol in face.mana_cost for face in sortable_faces
            ):
                sortable_colour |= colour
    else:
        for face in sortable_faces:
            sortable_colour |= int(face.colour)

    if sortable_colour == 0:
        if is_artifact:
            return 32
        return 0
    return COLOUR_TO_SORT_KEY[sortable_colour]


def get_nonland_sort_key_parts(card: Card, sortable_faces: list[CardFace]) -> list[int]:
    parts = []
    is_hybrid = any("/" in face.mana_cost for face in sortable_faces if face.mana_cost)
    is_artifact = any(
        _type.name == "Artifact"
        for face in sortable_faces
        for _type in face.types.all()
    )
    is_creature = any(
        _type.name == "Creature"
        for face in sortable_faces
        for _type in face.types.all()
    )
    is_instant = any(
        _type.name == "Instant" for face in sortable_faces for _type in face.types.all()
    )
    is_sorcery = any(
        _type.name == "Sorcery" for face in sortable_faces for _type in face.types.all()
    )
    is_attachable = any(
        subtyoe.name in ("Aura", "Equipment")
        for face in sortable_faces
        for subtyoe in face.subtypes.all()
    )

    is_token = any(
        type_.name == "Token"
        for face in sortable_faces
        for type_ in face.supertypes.all()
    )

    if is_token:
        parts.append(2)
    else:
        parts.append(0)

    # Colour part
    parts.append(get_sort_colour_key(sortable_faces, is_artifact=is_artifact))

    # Put hybrid cards after multicoloured cards
    parts.append(1 if is_hybrid else 0)

    # Type part
    if is_creature:
        parts.append(0)
    if is_instant and is_sorcery:
        parts.append(3)
    elif is_instant:
        parts.append(1)
    elif is_sorcery:
        parts.append(2)
    elif not is_attachable:
        parts.append(4)
    else:
        parts.append(5)

    # Split cards (also rooms) go after all other cards
    parts.append(1 if len(sortable_faces) > 1 else 0)

    # Mana value
    x_count = sum(
        face.mana_cost.count("X") for face in sortable_faces if face.mana_cost
    )
    x_adjusted_mana_value = x_count * 20 + int(card.mana_value)
    parts.append(x_adjusted_mana_value)

    # Generic mana difference (5w < 4ww < 3www etc.)
    total_generic_mana = 0
    for face in sortable_faces:
        if face.mana_cost:
            generic_mana = RE_GENERIC_MANA.search(face.mana_cost)
            if generic_mana:
                total_generic_mana += int(generic_mana.group(1))

    parts.append(x_adjusted_mana_value - total_generic_mana)

    return parts
