from django.conf.urls import patterns, url, include
from django.views.generic import RedirectView
from registration.forms import RegistrationFormUniqueEmail
from registration.backends.default.views import RegistrationView

from openraData import views
from openraData import api

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),

    url(r'^maps/?$', views.maps, name='maps'),
    url(r'^maps/(?P<arg>\d+)/?$', views.displayMap, name='displayMap'),
    url(r'^maps/(?P<arg>\d+)/minimap/?$', views.serveMinimap, name='serveMinimap'),
    url(r'^maps/(?P<arg>\d+)/render/?$', views.serveRender, name='serveRender'),
    url(r'^maps/(?P<arg>\d+)/lintlog/?$', views.serveLintLog, name='serveLintLog'),
    url(r'^maps/(?P<arg>\d+)/oramap/?$', views.serveOramap, name='serveOramap'),
    url(r'^maps/(?P<arg>\d+)/oramap/(?P<sync>\w+)/?$', views.serveOramap, name='serverSyncOramap'),
    url(r'^maps/upload/?$', views.uploadMap, name='uploadMap'),
    url(r'^maps/page/(?P<page>\d+)/?$', views.maps, name='maps_paged'),
    url(r'^maps/page/(?P<page>\d+)/filter/(?P<filter>\w+)/?$', views.maps, name='maps_paged_filtered'),
    url(r'^maps/filter/(?P<filter>\w+)/?$', views.maps, name='maps_filtered'),

    url(r'^units/?$', views.units, name='units'),
    url(r'^units/upload/?$', views.uploadUnit, name='uploadUnit'),

    url(r'^mods/?$', views.mods, name='mods'),
    url(r'^mods/upload/?$', views.uploadMod, name='uploadMod'),

    url(r'^palettes/?$', views.mods, name='palettes'),
    url(r'^palettes/upload/?$', views.uploadPalette, name='uploadPalette'),

    url(r'^screenshots/?$', views.screenshots, name='screenshots'),

    url(r'^assets/?$', views.assets, name='assets'),

    url(r'^replays/?$', views.replays, name='replays'),

    url(r'^login/?$', views.loginView, name='loginView'),
    url(r'^login/register/?$', RegistrationView.as_view(form_class=RegistrationFormUniqueEmail),
        name='registration_register'), 
    url(r'^login/', include('registration.backends.default.urls')),
    url(r'^logout/?$', views.logoutView, name='logoutView'),
    url(r'^news/feed/?$', views.feed, name='feed'),
    url(r'^search/', views.search, name='search'),

    url(r'^panel/?$', views.ControlPanel, name='ControlPanel'),
    url(r'^profile/?$', views.profile, name='profile'),
    url(r'^faq/?$', views.faq, name='faq'),
    url(r'^links/?$', views.links, name='links'),
    
    url(r'^map/(?P<arg>\w+)/?$', api.mapAPI, name='mapAPI_download'),
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/?$', api.mapAPI, name='mapAPI'), 
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/(?P<apifilter>\-?\w+)/?$', api.mapAPI, name='mapAPI_list'),
    url(r'^map/(?P<arg>\w+)/(?P<value>\w+)/(?P<apifilter>\-?\w+)/(?P<filtervalue>\w+)/?$', api.mapAPI, name='mapAPI_list_strict'),
    
    url(r'^crashlogs/?$', api.CrashLogs, name='CrashLogs'),
    url(r'^crashlogs/(?P<crashid>\w+)/(?P<logfile>\w+)/?$', api.CrashLogsServe, name='CrashLogsServe'),

    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
    url(r'^sitemap\.xml$', RedirectView.as_view(url='/static/sitemap.xml')),

    url(r'^.*$', views.handle404, name='handle404'),
)
