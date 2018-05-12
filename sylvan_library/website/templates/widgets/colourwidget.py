import django.forms as forms
from django.forms import widgets
from django.utils.safestring import mark_safe


class ColourWidget(widgets.MultiWidget):
    def __init__(self, attrs=None, white=False, blue=False, black=False, red=False, green=False):
        _widgets = (widgets.CheckboxInput(attrs=attrs),
                    widgets.CheckboxInput(attrs=attrs),
                    widgets.CheckboxInput(attrs=attrs),
                    widgets.CheckboxInput(attrs=attrs),
                    widgets.CheckboxInput(attrs=attrs),
                    )

        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value & 1, value & 2, value & 4, value & 8, value & 16]
        return [None, None, None, None, None]

    def format_output(self, rendered_widgets):
        return u'wasd'.join(rendered_widgets)

    def render(self, name, value, attrs=None, renderer=None):
        # return 'wasd'
        # return self.decompress(value)
        # values = decompress[value]
        html = 'wasd'.join([w.render(name, True) for w in self.widgets])
        # html = super(widgets.Widget, self).render(name, value, attrs, renderer)
        return mark_safe(html)

    def value_from_datadict2(self, data, files, name):
        boollist = [widget.value_from_datadict(data, files, name + '_%s' % i) \
                    for i, widget in enumerate(self.widgets)]
        return boollist


class ColourField(forms.MultiValueField):
    widget = ColourWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = (
            forms.BooleanField(),
            forms.BooleanField(),
            forms.BooleanField(),
            forms.BooleanField(),
            forms.BooleanField(),
        )

    def compress(self, data_list):
        return ' '.join(data_list)
