# pylint: skip-file
"""
django-bitfield
~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import

from sylvan_library.bitfield.models import (
    Bit,
    BitHandler,
    CompositeBitField,
    BitField,
)  # NOQA

default_app_config = "bitfield.apps.BitFieldAppConfig"

VERSION = "2.1.0"
