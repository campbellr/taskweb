from django.conf.urls.defaults import patterns, include, url
import settings

urlpatterns = patterns('',
    url(r'', include('task.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'media/(?P<path>.*)\?*$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
