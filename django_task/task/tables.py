from django.utils.safestring import mark_safe
from django.template.defaultfilters import timesince

import django_tables2 as tables

class Attr(object):
    def __init__(self, attr):
        self.attr = attr

    def as_html(self):
        return " ".join(["%s=\"%s\"" % (k, v) for k, v in self.attr.items()])

class Column(tables.Column):
    """ A column that adds the ability to set attributes on the
        `td` element.
    """
    def __init__(self, *args, **kwargs):
        self.attrs = Attr(kwargs.pop('attrs', {}))
        super(Column, self).__init__(*args, **kwargs)

    def render(self, value):
        return  mark_safe("<td %s>%s</td>" % (self.attrs.as_html(), value))

class DateTimeSinceColumn(Column):
    """ A column that displays the time since the given value in
        a human-friendly format. Eg: "1 day", "4 minutes", etc...
    """
    def render(self, value):
        value = timesince(value).split(',')[0]
        return super(DateTimeSinceColumn, self).render(value)

class TaskTable(tables.Table):
    id = Column(verbose_name="ID", attrs={'class': 'id'})
    project = Column(verbose_name="Proj", attrs={'class': 'proj'}, default='')
    priority = Column(verbose_name="Pri", attrs={'class': 'pri'}, default='')
    tags = Column(verbose_name="Tags", attrs={'class': 'tags'}, default='')
    date = DateTimeSinceColumn(verbose_name='Age', attrs={'class': 'age'}, default='')
    desc = Column(verbose_name="Description", attrs={'class': 'desc'})

    class Meta:
        order_by = 'id'
        template = 'table.html'