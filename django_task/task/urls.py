from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

urlpatterns = patterns('task.views',
        (r'^$', redirect_to, {'url': '/pending/'}),
        (r'^pending/$', 'pending_tasks'),
        (r'^completed/$', 'completed_tasks'),
        (r'^add/', 'add_task'),
        (r'^done/(?P<task_id>\d+)/$', 'done_task'),
        (r'^edit/(?P<task_id>\d+)/$', 'edit_task'),
        (r'^detail/(?P<task_id>\d+)/$', 'detail_task'),
        (r'^upload/$', 'upload'),
        (r'^taskdb/(?P<filename>.*)$', 'taskdb')
        )
