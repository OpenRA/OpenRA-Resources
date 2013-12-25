from django.conf.urls import patterns, url
from django.views.generic import RedirectView

from openraData import views
from openraData import api

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^maps$', views.maps, name='maps'),
    url(r'^maps/$', views.maps, name='maps'),
    url(r'^units$', views.units, name='units'),
    url(r'^units/$', views.units, name='units'),
    url(r'^mods$', views.mods, name='mods'),
    url(r'^mods/$', views.mods, name='mods'),
    url(r'^login$', views.login, name='login'),
    url(r'^login/$', views.login, name='login'),
    url(r'^map/(?P<arg>\w+)/$', api.mapAPI, name='mapAPI_download'),
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/$', api.mapAPI, name='mapAPI'), 
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/(?P<filter>\w+)/$', api.mapAPI, name='mapAPI_list'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico'))
)
