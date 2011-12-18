import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.template.defaultfilters import timesince

import taskw
import django_tables2 as tables

def _reformat(task_list):
    """ Return the data in task_list formatted in a django-tables2-friendly
        format.
    """
    formatted = list()
    for id_, task in enumerate(task_list, 1):
        ftask = dict()
        ftask['id'] = id_
        ftask['desc'] = task['description']
        ftask['priority'] = task.get('priority')
        ftask['date'] = datetime.datetime.fromtimestamp(int(task['entry']))
        ftask['project'] = task.get('project')
        ftask['depends'] = task.get('depends')
        ftask['tags'] = task.get('tags')
        formatted.append(ftask)

    return formatted

class Attr(object):
    def __init__(self, attr):
        self.attr = attr

    def as_html(self):
        return " ".join(["%s=\"%s\"" % (k, v) for k, v in self.attr.items()])

class Column(tables.Column):
    def __init__(self, *args, **kwargs):
        self.attrs = Attr(kwargs.pop('attrs', {}))
        super(Column, self).__init__(*args, **kwargs)

    def render(self, value):
        return  mark_safe("<td %s>%s</td>" % (self.attrs.as_html(), value))

class DateTimeSinceColumn(Column):
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

def index(request, template='task/index.html'):
    all_tasks = taskw.load_tasks()
    tasks = _reformat(all_tasks['pending'])
    table = TaskTable(tasks, order_by=request.GET.get('sort'))
    return render_to_response(template, {'table': table},
                              context_instance=RequestContext(request))

def add_task(request, template='task/add.html'):
    return HttpResponse("This is the 'add task' page.")

def done_task(request, task_id, template='task/done.html'):
    return HttpResponse("This is the 'done task %s' page." % task_id)

def edit_task(request, task_id, template='task/edit.html'):
    return HttpResponse("This is the 'edit task %s' page." % task_id)

