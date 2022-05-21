from typing import List

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render

from cards.models.sets import Set


def set_list(request: WSGIRequest):
    """
    View for the list of all sets
    """
    all_sets = list(Set.objects.order_by("-release_date"))
    root_sets = [card_set for card_set in all_sets if not card_set.parent_set_id]

    serialised_sets = [
        serialise_set(card_set, all_sets, depth=1) for card_set in root_sets
    ]

    return render(request, "website/set_list.html", {"set_tree": serialised_sets})


def serialise_set(card_set: Set, all_sets: List[Set], depth: int):
    """
    Serialises the data for a single set
    :param card_set:
    :param all_sets:
    :param depth:
    :return:
    """
    return {
        "name": card_set.name,
        "code": card_set.code,
        "size": card_set.total_set_size,
        "release_date": card_set.release_date,
        "depth": depth,
        "child_sets": [
            serialise_set(child_set, all_sets, depth + 1)
            for child_set in all_sets
            if child_set.parent_set_id == card_set.id
        ],
    }
