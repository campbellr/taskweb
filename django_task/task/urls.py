from django.conf.urls.defaults import *

urlpatterns = patterns('task.views',
        (r'^$', 'pending_tasks'),
        (r'^completed/$', 'completed_tasks'),
        (r'^add_task/', 'add_task'),
        (r'^done_task/(?P<task_id>\d+)/$', 'done_task'),
        (r'^upload/$', 'upload'),
        (r'^taskdb/(?P<filename>.*)$', 'taskdb')
        )
