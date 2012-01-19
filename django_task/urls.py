from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import settings

admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('task.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^admin/', include(admin.site.urls)),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
            (r'media/(?P<path>.*)\?*$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
            )
