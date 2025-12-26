from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from website.forms import QuerySearchForm
from website.pagination import get_page_buttons


def card_search(request: HttpRequest) -> HttpResponse:
    """
    The view for when a user searches by card name
    :param request: The user's request
    :return: The HTTP Response
    """
    query_form = QuerySearchForm(request.GET)
    search, query_context = query_form.get_search(user=request.user)

    return render(
        request,
        "website/search.html",
        {
            "query_form": query_form,
            "results": search.results,
            "result_count": search.paginator.count,
            "page": search.page,
            "page_buttons": get_page_buttons(
                search.paginator, query_form.get_page_number(), 3
            ),
            "page_title": (
                f"{search.query_string} - Sylvan Library"
                if search.query_string
                else "Sylvan Library"
            ),
            "pretty_query_message": search.get_pretty_str(query_context),
            "error_message": search.error_message,
        },
    )
