from django import forms
from django.template.loader import render_to_string
from django.conf import settings


class JQueryDateWidget(forms.DateInput):
    def __init__(self, *args, **kwargs):
        attrs = {'id': 'datepicker'}
        kwargs.setdefault('attrs', {}).update(attrs)
        super(JQueryDateWidget, self).__init__(*args, **kwargs)

    class Media:
        js = (
                settings.STATIC_URL + 'task/js/datepicker.js',
             )


class PopUpBaseWidget(object):
    def __init__(self, model=None, template='addnew.html', *args, **kwargs):
        self.model = model
        self.template = template
        super(PopUpBaseWidget, self).__init__(*args, **kwargs)

    def render(self, name, *args, **kwargs):
        html = super(PopUpBaseWidget, self).render(name, *args, **kwargs)

        if not self.model:
            self.model = name

        popupplus = render_to_string(self.template, {'field': name, 'model': self.model,
            'STATIC_URL': settings.STATIC_URL})
        return html + popupplus


class MultipleSelectWithPopUp(PopUpBaseWidget, forms.SelectMultiple):
    pass


class SelectWithPopUp(PopUpBaseWidget, forms.Select):
    pass

