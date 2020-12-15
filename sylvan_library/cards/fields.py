from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_text
from django.utils.text import capfirst

# 
# class BitFlagFormField(forms.MultipleChoiceField):
#     widget = forms.CheckboxSelectMultiple
# 
#     def __init__(self, *args, **kwargs):
#         super(BitFlagFormField, self).__init__(*args, **kwargs)
# 
# 
# class BitFlagField(models.Field):
#     # __metaclass__ = models.SubfieldBase
# 
#     def get_internal_type(self):
#         return "Integer"
# 
#     def get_choices_default(self):
#         return self.get_choices(include_blank=False)
# 
#     def _get_FIELD_display(self, field):
#         value = getattr(self, field.attname)
#         choicedict = dict(field.choices)
# 
#     def formfield(self, **kwargs):
#         # do not call super, as that overrides default widget if it has choices
#         defaults = {
#             "required": not self.blank,
#             "label": capfirst(self.verbose_name),
#             "help_text": self.help_text,
#             "choices": self.choices,
#         }
#         if self.has_default():
#             defaults["initial"] = self.get_default()
#         defaults.update(kwargs)
#         return BitFlagFormField(**defaults)
# 
#     def get_db_prep_value(self, value):
#         if isinstance(value, int):
#             return value
#         elif isinstance(value, list):
#             return sum(value)
# 
#     def to_python(self, value):
#         result = []
#         n = 1
#         while value > 0:
#             if (value % 2) > 0:
#                 result.append(n)
#             n *= 2
#             value /= 2
#         return sorted(result)
# 
#     def contribute_to_class(self, cls, name):
#         super(BitFlagField, self).contribute_to_class(cls, name)
#         if self.choices:
#             func = lambda self, fieldname=name, choicedict=dict(
#                 self.choices
#             ): " and ".join(
#                 [choicedict.get(value, value) for value in getattr(self, fieldname)]
#             )
#             setattr(cls, "get_%s_display" % self.name, func)


class BitFieldCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=(), renderer=None):
        real_value = []
        if isinstance(value, list):
            pass
            # value = [k for k in value if v]
        # value = int(value[0])
        else:
            div = 2
            for (k, v) in self.choices:
                if value % div != 0:
                    real_value.append(k)
                    value -= value % div
                div *= 2
            value = real_value
        print(name, value, attrs)
        # value = 10
        return super(BitFieldCheckboxSelectMultiple, self).render(
            name, value, attrs=attrs
        )

    def has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if initial != data:
            return True
        initial_set = set([force_text(value) for value in initial])
        data_set = set([force_text(value) for value in data])
        return data_set != initial_set


class BitFormField(forms.IntegerField):
    def __init__(
        self, choices=(), widget=BitFieldCheckboxSelectMultiple, *args, **kwargs
    ):

        # if isinstance(kwargs["initial"], int):
        #     iv = kwargs["initial"]
        #     iv_list = []
        #     for i in range(0, min(len(choices), 63)):
        #         if (1 << i) & iv > 0:
        #             iv_list += [choices[i][0]]
        #     kwargs["initial"] = iv_list
        self.widget = widget
        super(BitFormField, self).__init__(widget=widget, *args, **kwargs)
        self.choices = self.widget.choices = choices

    def clean(self, value):
        if not value:
            return 0

        # Assume an iterable which contains an item per flag that's enabled
        # result = BitHandler(0, [k for k, v in self.choices])
        # for k in value:
        #     try:
        #         setattr(result, str(k), True)
        #     except AttributeError:
        #         raise ValidationError("Unknown choice: %r" % (k,))
        # return int(result)
        return 5
