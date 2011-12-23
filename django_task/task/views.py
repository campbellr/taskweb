import datetime
import os

from django.http import HttpResponse,  HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
import settings

import taskw

from task import tables, forms

TASK_NAME = 'taskdb'
TASK_ROOT = os.path.join(settings.MEDIA_ROOT, TASK_NAME)
TASK_URL = os.path.join(settings.MEDIA_URL, TASK_NAME)

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
        end = task.get('end')
        if end:
            ftask['end'] = datetime.datetime.fromtimestamp(int(end))
        due = task.get('due')
        if due:
            ftask['due'] = datetime.datetime.fromtimestamp(int(due))

        formatted.append(ftask)

    return formatted

def _get_tasks(status, request, template, table_class):
    all_tasks = taskw.load_tasks()
    tasks = _reformat(all_tasks[status])
    table = table_class(tasks, order_by=request.GET.get('sort'))
    return render_to_response(template, {'table': table, 'task_url': TASK_URL},
                              context_instance=RequestContext(request))


def pending_tasks(request, template='task/index.html'):
    return _get_tasks('pending', request, template, tables.TaskTable)

def completed_tasks(request, template='task/index.html'):
    return _get_tasks('completed', request, template, tables.CompletedTaskTable)

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

def upload(request, template='task/upload.html'):
    if request.method == "POST":
        form = forms.TaskDbUploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_db(request.FILES)
            return HttpResponseRedirect('/')
    else:
        form = forms.TaskDbUploadForm()

    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))

def handle_uploaded_db(files):
    if not os.path.exists(TASK_ROOT):
        os.mkdir(TASK_ROOT)

    for filename in ('completed', 'pending'):
        destination = os.path.join(settings.MEDIA_ROOT, filename + ".data")
        with open(destination, 'w') as f:
            for chunk in files[filename].chunks():
                f.write(chunk)


