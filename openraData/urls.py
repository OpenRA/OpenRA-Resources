from django.conf.urls import patterns, url

from openraData import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^map/(?P<arg>\w+)/$', views.mapAPI, name='mapAPI_download'),
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/$', views.mapAPI, name='mapAPI')
)
