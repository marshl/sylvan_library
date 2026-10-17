from django.core.handlers.wsgi import WSGIRequest


def get_page_number(request: WSGIRequest, param_name: str = "page") -> int:
    """
    Gets the page number of a given request
    :param param_name:
    :param request: The request to get the page from
    :return: The page number
    """
    try:
        return int(request.GET.get(param_name))
    except (TypeError, ValueError):
        return 1
