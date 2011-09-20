from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin

from evolve.rules.admin import site as rules_admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'evolve.base.views.home', name='home'),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^register/$', 'evolve.base.views.register', name='register'),
    url(r'^game/', include('evolve.game.urls')),

    url(r'^rules-admin/', include(rules_admin.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
