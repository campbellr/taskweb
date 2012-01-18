import sys
import datetime

from django.http import (HttpResponse,  HttpResponseRedirect,
                        HttpResponseNotAllowed,
                        HttpResponseNotFound, HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from taskw.reading import parse_line

from task import forms
from task.decorators import logged_in_or_basicauth
from task.grids import TaskDataGrid
from task.models import Task, Undo
import settings

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
            data = form.cleaned_data
            task = Task(description=data.get('description'),
                 priority=data.get('priority'),
                 project=data.get('project'),
                 user=request.user)

            task.save()
            for tag in data.get('tags', '').split(','):
                task.add_tag(tag)

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


def taskdict2orm(taskdata, user):
    task = Task(
            description=taskdata['description'],
            uuid=taskdata['uuid'],
            project=taskdata.get('project'),
            status=taskdata['status'],
            entry=datetime.datetime.fromtimestamp(int(taskdata['entry'])),
            priority=taskdata.get('priority'),
            user=user,
            )

    task.save(track=False)

    for tag in taskdata.get('tags', '').split(','):
        task.add_tag(tag)


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
    response['Content-Length'] = sys.getsizeof(taskstr)
    return response


def put_taskdb(request, filename):
    return post_taskdb(request, filename)


def post_taskdb(request, filename):
    if filename not in TASK_FNAMES:
        return HttpResponseForbidden('Forbidden!')

    user = request.user
    data = request.raw_post_data

    if filename in ['pending.data', 'completed.data']:
        parsed = [parse_line(line) for line in data.splitlines()]
        if filename == 'pending.data':
            tasks = Task.objects.filter(status='pending', user=user)
        elif filename == 'completed.data':
            tasks = Task.objects.filter(status__in=['completed', 'deleted'])

        tasks.delete()

        for task in parsed:
            taskdict2orm(task, user)

    elif filename == 'undo.data':
        parsed = parse_undo(data)
        undodict2orm(parsed, user)
    else:
        return HttpResponseNotFound()

    return HttpResponse()


def undodict2orm(parsed, user):
    for undo_info in parsed:
        undo = Undo(
                    user=user,
                    time=datetime.datetime.fromtimestamp(int(undo_info['time'])),
                    old=undo_info.get('old'),
                    new=undo_info['new'],
                    )
        undo.save()


def parse_undo(data):
    undo_list = []
    for segment in data.split('---'):
        parsed = {}
        undo = [line for line in segment.splitlines() if line.strip()]
        if not undo:
            continue

        parsed['time'] = undo[0].split(' ', 1)[1]
        if undo[1].startswith('old'):
            parsed['old'] = undo[1].split(' ', 1)[1]
            parsed['new'] = undo[2].split(' ', 1)[1]
        else:
            parsed['new'] = undo[1].split(' ', 1)[1]

        undo_list.append(parsed)

    return undo_list


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
