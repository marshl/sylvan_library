from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from website.forms import QuerySearchForm
from website.pagination import get_page_buttons


def name_search(request: WSGIRequest) -> HttpResponse:
    """
    The view for when a user searches by card name
    :param request: The user's request
    :return: The HTTP Response
    """
    query_form = QuerySearchForm(request.GET)
    query_form.user = request.user
    search = query_form.get_search()
    return render(
        request,
        "website/simple_search.html",
        {
            "query_form": query_form,
            "results": search.results,
            "result_count": search.paginator.count,
            "page": search.page,
            "page_buttons": get_page_buttons(
                search.paginator, query_form.get_page_number(), 3
            ),
            "page_title": f"{search.query_string} - Sylvan Library"
            if search.query_string
            else "Sylvan Library",
            "pretty_query_message": search.get_pretty_str(),
            "error_message": search.error_message,
        },
    )

