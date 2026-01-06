# pylint: skip-file
from __future__ import absolute_import

from django import forms

from sylvan_library.bitfield.tests.models import BitFieldTestModel


class BitFieldTestModelForm(forms.ModelForm):
    class Meta:
        model = BitFieldTestModel
        exclude = tuple()
