from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

import taskw

def index(request, template='task/index.html'):
    all_tasks = taskw.load_tasks()
    return render_to_response(template, all_tasks,
                              context_instance=RequestContext(request))

def add_task(request, template='task/add.html'):
    return HttpResponse("This is the 'add task' page.")

def done_task(request, task_id, template='task/done.html'):
    return HttpResponse("This is the 'done task %s' page." % task_id)

def edit_task(request, task_id, template='task/edit.html'):
    return HttpResponse("This is the 'edit task %s' page." % task_id)

