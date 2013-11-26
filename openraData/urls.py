from django.conf.urls import patterns, url

from openraData import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index')
)
