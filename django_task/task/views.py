import datetime
import os
import mimetypes

from django.core.servers.basehttp import FileWrapper
from django.http import (HttpResponse,  HttpResponseRedirect,
                        HttpResponseNotAllowed,
                        HttpResponseNotFound, HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
import settings

import taskw

from task import tables, forms
from task.decorators import logged_in_or_basicauth
from task.grids import TaskDataGrid
from task.models import Task

TASK_URL = 'taskdb'
TASK_ROOT = settings.TASKDATA_ROOT

TASK_FNAMES = ('undo.data', 'completed.data', 'pending.data')


def pending_tasks(request, template='task/index.html'):
    return TaskDataGrid(request,
         queryset=Task.objects.filter(status='pending')).render_to_response(template)


def completed_tasks(request, template='task/index.html'):
    return TaskDataGrid(request,
         queryset=Task.objects.filter(status='completed')).render_to_response(template)


@login_required
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

            taskw.task_add(desc, location=TASK_ROOT, **data)
            return HttpResponseRedirect('/')
    else:
        form = forms.TaskForm()

    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))


def done_task(request, task_id, template='task/done.html'):
    return HttpResponse("This is the 'done task %s' page." % task_id)


def edit_task(request, task_id, template='task/edit.html'):
    return HttpResponse("This is the 'edit task %s' page." % task_id)


def detail_task(request, task_id, template='task/detail.html'):
    return HttpResponse("This is the 'detail task %s' page." % task_id)


@login_required
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


def get_taskdb(request, filename):
    fullpath = os.path.join(settings.TASKDATA_ROOT, filename)
    if not os.path.isfile(fullpath):
        return HttpResponseNotFound('Not found!')

    f = file(fullpath, 'r')
    wrapper = FileWrapper(f)
    response = HttpResponse(wrapper, mimetype=mimetypes.guess_type(filename))
    response['Content-Length'] = os.path.getsize(fullpath)
    return response


def put_taskdb(request, filename):
    return post_taskdb(request, filename)


def post_taskdb(request, filename):
    if filename not in TASK_FNAMES:
        return HttpResponseForbidden('Forbidden!')

    data = request.raw_post_data
    fullpath = os.path.join(settings.TASKDATA_ROOT, filename)
    with open(fullpath, 'w') as f:
        f.write(data)

    return HttpResponse()


@logged_in_or_basicauth()
def taskdb(request, filename):
    """ Serve {undo, completed, pending}.data files as requested.

        I't probably better to serve outside of django, but
        this is much more flexible for now.
    """
    if request.method == 'GET':
        return get_taskdb(request, filename)

    elif request.method == 'POST':
        return post_taskdb(request, filename)

    elif request.method == 'PUT':
        return put_taskdb(request, filename)
    else:
        return HttpResponseNotAllowed(['GET', 'PUT', 'POST'])
