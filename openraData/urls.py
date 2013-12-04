from django.conf.urls import patterns, url
from django.views.generic import RedirectView

from openraData import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^map/(?P<arg>\w+)/$', views.mapAPI, name='mapAPI_download'),
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/$', views.mapAPI, name='mapAPI'), 
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/(?P<filter>\w+)/$', views.mapAPI, name='mapAPI_list'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico'))
)
