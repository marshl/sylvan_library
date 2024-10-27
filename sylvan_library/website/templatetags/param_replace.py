"""
Module for the param_replace template tag
"""

from typing import Any

from django import template

# pylint: disable=invalid-name
from django.template import RequestContext

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context: RequestContext, **kwargs: Any) -> str:
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278

    Source:
    https://www.caktusgroup.com/blog/2018/10/18/filtering-and-pagination-django/
    """
    params = context["request"].GET.copy()
    for key, val in kwargs.items():
        params[key] = val

    for key in [key for key, val in params.items() if not val]:
        del params[key]

    return params.urlencode()
