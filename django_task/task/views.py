import datetime

from django.http import HttpResponse,  HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

import taskw

from task import tables, forms

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


def index(request, template='task/index.html'):
    all_tasks = taskw.load_tasks()
    tasks = _reformat(all_tasks['pending'])
    table = tables.TaskTable(tasks, order_by=request.GET.get('sort'))
    return render_to_response(template, {'table': table},
                              context_instance=RequestContext(request))

def add_task(request, template='task/add.html'):
    if request.method == 'POST':
        form = forms.TaskForm(request.POST)
        if form.is_valid():
            desc = form.cleaned_data['description']

            data = dict()
            pri = form.cleaned_data['priority']
            if pri:
                data['priority'] = pri
            proj = form.cleaned_data['project']
            if proj:
                data['project'] = proj
            tags = form.cleaned_data['tags']
            if tags:
                data['tags'] = tags

            taskw.task_add(desc, **data)
            return HttpResponseRedirect('/')
    else:
        form = forms.TaskForm()

    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))

def done_task(request, task_id, template='task/done.html'):
    return HttpResponse("This is the 'done task %s' page." % task_id)

def edit_task(request, task_id, template='task/edit.html'):
    return HttpResponse("This is the 'edit task %s' page." % task_id)

