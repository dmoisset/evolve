from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin

from evolve.rules.admin import site as rules_admin

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'evolve.views.home', name='home'),
    # url(r'^evolve/', include('evolve.foo.urls')),

    url(r'^rules-admin/', include(rules_admin.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
