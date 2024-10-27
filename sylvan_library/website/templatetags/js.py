"""
Template tags for converting objects to javascript
"""

import json
from typing import Any

from django.utils.safestring import mark_safe
from django import template


register = template.Library()


@register.filter(is_safe=True)
def to_json(obj: Any) -> str:
    """
    Template tag for converting objects to javascript
    :param obj: The object to convert
    :return: The converted object
    """
    return mark_safe(json.dumps(obj))
