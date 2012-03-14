import logging

from django.http import (HttpResponse,  HttpResponseRedirect,
                        HttpResponseNotAllowed,
                        HttpResponseNotFound, HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.html import escape

from taskw import decode_task

from task import forms
from task.decorators import logged_in_or_basicauth
from task.grids import TaskDataGrid
from task.models import Task, Undo
from task.util import parse_undo
from django.conf import settings

TASK_URL = 'taskdb'
TASK_ROOT = settings.TASKDATA_ROOT

TASK_FNAMES = ('undo.data', 'completed.data', 'pending.data')


def pending_tasks(request, template='task/index.html'):
    pending = Task.objects.filter(status='pending')
    task_url = "http://%s/taskdb/" % request.get_host()
    grid = TaskDataGrid(request, queryset=pending)
    return grid.render_to_response(template,
            extra_context={'task_url': task_url})


def completed_tasks(request, template='task/index.html'):
    completed = Task.objects.filter(status='completed')
    task_url = "http://%s/taskdb/" % request.get_host()
    grid = TaskDataGrid(request, queryset=completed)
    return grid.render_to_response(template,
            extra_context={'task_url': task_url})


@login_required
def add_task(request, template='task/add.html'):
    if request.method == 'POST':
        task = Task(user=request.user)
        form = forms.TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            # silly extra save to create
            # undo object for m2m fields
            task.save()
            return HttpResponseRedirect('/')
    else:
        form = forms.TaskForm(initial={'user': request.user})

    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))


@login_required
def add_tag(request):
    return add_model(request, forms.TagForm, 'tags')


@login_required
def add_project(request):
    return add_model(request, forms.ProjectForm, 'project')


def add_model(request, form_cls, name, template="popup.html"):
    if request.method == 'POST':
        form = form_cls(request.POST)
        if form.is_valid():
            new_obj = form.save()
            return HttpResponse('<script type="text/javascript">'
                                'opener.dismissAddAnotherPopup(window, "%s", "%s");'
                                '</script>' %
                                (escape(new_obj._get_pk_val()), escape(new_obj)))
    else:
        form = form_cls()

    page_context = {'form': form, 'field': name}
    return render_to_response("popup.html", page_context, context_instance=RequestContext(request))


def done_task(request, task_id, template='task/done.html'):
    return HttpResponse("This is the 'done task %s' page." % task_id)


def edit_task(request, task_id, template='task/edit.html'):
    return HttpResponse("This is the 'edit task %s' page." % task_id)


def detail_task(request, task_id, template='task/detail.html'):
    return HttpResponse("This is the 'detail task %s' page." % task_id)


#@login_required
#def upload(request, template='task/upload.html'):
#    if request.method == "POST":
#        form = forms.TaskDbUploadForm(request.POST, request.FILES)
#        if form.is_valid():
#            handle_uploaded_db(request.FILES, request.user)
#            return HttpResponseRedirect('/')
#    else:
#        form = forms.TaskDbUploadForm()
#
#    return render_to_response(template, {'form': form},
#                              context_instance=RequestContext(request))


def get_taskdb(request, filename):
    if filename == 'pending.data':
        taskstr = Task.serialize('pending')
    elif filename == 'completed.data':
        taskstr = Task.serialize('completed')
    elif filename == 'undo.data':
        taskstr = Undo.serialize()
    else:
        return HttpResponseNotFound()

    response = HttpResponse(taskstr, mimetype='text/plain')
    response['Content-Length'] = len(taskstr)
    return response


def put_taskdb(request, filename):
    return post_taskdb(request, filename)


def post_taskdb(request, filename):
    if filename not in TASK_FNAMES:
        return HttpResponseForbidden('Forbidden!')

    user = request.user
    data = request.raw_post_data

    if filename in ['pending.data', 'completed.data']:
        parsed = [decode_task(line) for line in data.splitlines()]
        if filename == 'pending.data':
            tasks = Task.objects.filter(status='pending', user=user)
        elif filename == 'completed.data':
            tasks = Task.objects.filter(status__in=['completed', 'deleted'])

        tasks.delete()

        for task in parsed:
            task.update({'user': user})
            Task.fromdict(task)

    elif filename == 'undo.data':
        Undo.objects.all().delete()
        parsed = parse_undo(data)
        for undo_dict in parsed:
            undo_dict.update({'user': user})
            Undo.fromdict(undo_dict)
    else:
        return HttpResponseNotFound()

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
