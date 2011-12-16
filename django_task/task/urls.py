from django.conf.urls.defaults import *

urlpatterns = patterns('task.views',
        (r'^$', 'index'),
        (r'^add_task/', 'add_task'),
        (r'^done_task/(?P<task_id>\d+)/$', 'done_task'),
        )
