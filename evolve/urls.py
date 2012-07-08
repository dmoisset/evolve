from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from evolve.rules.admin import site as rules_admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'evolve.base.views.home', name='home'),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'evolve.base.views.logout', name='logout'),
    url(r'^register/$', 'evolve.base.views.register', name='register'),
    url(r'^game/', include('evolve.game.urls')),

    url(r'^rules-admin/', include(rules_admin.urls)),
    url(r'^admin/', include(admin.site.urls)),
) + staticfiles_urlpatterns()

