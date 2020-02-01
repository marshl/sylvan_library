"""
MOdule for handling pagination of search results and decks
"""
from typing import List
from django.core.paginator import Paginator


# pylint: disable=too-few-public-methods
class PageButton:
    """
    Information about a single page button
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        number,
        is_enabled,
        is_active=False,
        is_previous=False,
        is_next=False,
        is_spacer=False,
    ):
        self.number = number
        self.enabled = is_enabled
        self.is_active = is_active
        self.is_previous = is_previous
        self.is_next = is_next
        self.is_spacer = is_spacer


def get_page_buttons(
    paginator: Paginator, current_page: int, page_span: int
) -> List[PageButton]:
    """
    Gets the page buttons that should appear for this search based on the number of pages
    in the results and hoa many pages the buttons should span
    :param current_page: The current page
    :param page_span: The number of pages to the left and right of the current page
    :return: A list of page buttons. Some of them can disabled padding buttons, and there will
    be a next and previous button at the start and end too
    """
    page_buttons: List[PageButton] = [
        PageButton(page_number, True, is_active=page_number == current_page)
        for page_number in paginator.page_range
        if abs(page_number - current_page) <= page_span
    ]

    # if the current page is great enough
    # put a  link to the first page at the start followed by a spacer
    if current_page - page_span > 1:
        page_buttons.insert(0, PageButton(None, False, is_spacer=True))
        page_buttons.insert(0, PageButton(1, True))

    if current_page + page_span <= paginator.num_pages - 2:
        page_buttons.append(PageButton(None, False, is_spacer=True))

    if current_page + page_span <= paginator.num_pages - 1:
        page_buttons.append(PageButton(paginator.num_pages, True))

    page_buttons.insert(
        0, PageButton(max(current_page - 1, 1), current_page != 1, is_previous=True)
    )
    page_buttons.append(
        PageButton(current_page + 1, current_page != paginator.num_pages, is_next=True)
    )

    return page_buttons
