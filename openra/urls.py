"""openra URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from django.views.generic import RedirectView
from registration.forms import RegistrationFormUniqueEmail
from registration.backends.default.views import RegistrationView

from openra import views, api, ajax


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', views.index, name='index'),

    url(r'^maps/?$', views.maps, name='maps'),
    url(r'^maps/(?P<arg>\d+)/?$', views.displayMap, name='displayMap'),
    url(r'^maps/(?P<arg>\d+)/minimap/?$', views.serveMinimap, name='serveMinimap'),
    url(r'^maps/(?P<arg>\d+)/oramap/?$', views.serveOramap, name='serveOramap'),
    url(r'^maps/(?P<arg>\d+)/oramap/(?P<sync>\w+)/?$', views.serveOramap, name='serverSyncOramap'),
    url(r'^maps/(?P<arg>\d+)/delete/?$', views.DeleteMap, name='DeleteMap'),
    url(r'^maps/(?P<arg>\d+)/setdownloadingstatus/?$', views.SetDownloadingStatus, name='SetDownloadingStatus'),
    url(r'^maps/(?P<arg>\d+)/add(?P<item>\w+)sc/?$', views.addScreenshot, name='addScreenshot'),
    url(r'^maps/(?P<arg>\d+)/revisions/?$', views.maps_revisions, name='maps_revisions'),
    url(r'^maps/(?P<arg>\d+)/revisions/page/(?P<page>\d+)/?$', views.maps_revisions, name='maps_revisions'),
    url(r'^maps/(?P<arg>\d+)/upgrade/?$', views.upgradeMap, name='upgradeMap'),
    url(r'^(?P<item_type>\w+)/(?P<arg>\d+)/unsubscribe/?$', views.unsubscribe_from_comments, name='Unsubscribe from comments to item'),
    url(r'^maps/author/(?P<author>.+?)/page/(?P<page>\d+)/?$', views.maps_author, name='maps_author'),
    url(r'^maps/author/(?P<author>.+?)/?$', views.maps_author, name='maps_author'),
    url(r'^maps/uploader/(?P<arg>\d+)/?$', views.maps_uploader, name='maps_uploader'),
    url(r'^maps/uploader/(?P<arg>\d+)/page/(?P<page>\d+)/?$', views.maps_uploader, name='maps_uploader'),
    url(r'^maps/duplicates/(?P<maphash>[^/]+)/?$', views.maps_duplicates, name='maps_duplicates'),
    url(r'^maps/duplicates/(?P<maphash>[^/]+)/page/(?P<page>\d+)/?$', views.maps_duplicates, name='maps_duplicates'),
    url(r'^maps/page/(?P<page>\d+)/?$', views.maps, name='maps_paged'),
    url(r'^maps/(?P<arg>\d+)/yaml/?$', views.serveYaml, name='printYaml'),
    url(r'^maps/(?P<arg>\d+)/rules/?$', views.serveYamlRules, name='printYamlRules'),
    url(r'^maps/(?P<arg>\d+)/lua/(?P<name>[^/]+)/?$', views.serveLua, name='printLua'),
    url(r'^maps/(?P<arg>\d+)/shp/(?P<name>[^/]+)/(?P<request_type>[^/]+)/?$', views.serveMapSHP, name='printMapSHP'),
    url(r'^maps/mostCommented/?$', views.mostCommentedMap, name='mostCommentedMap'),

    url(r'^upload/map/?$', views.uploadMap, name='uploadMap'),
    url(r'^upload/map/(?P<previous_rev>\d+)/?$', views.uploadMap, name='uploadMap'),


    url(r'^screenshots/?$', views.screenshots, name='screenshots'),
    url(r'^screenshots/(?P<itemid>\d+)/?$', views.serveScreenshot, name='serveScreenshot'),
    url(r'^screenshots/(?P<itemid>\d+)/delete/?$', views.deleteScreenshot, name='deleteScreenshot'),
    url(r'^screenshots/(?P<itemid>\d+)/(?P<itemname>\w+)/?$', views.serveScreenshot, name='serveScreenshot'),

    url(r'^comments/?$', views.comments, name='comments'),
    url(r'^comments/page/(?P<page>\d+)/?$', views.comments, name='comments_paged'),
    url(r'^comments/user/(?P<arg>\d+)/?$', views.comments_by_user, name='comments_by_user'),
    url(r'^comments/user/(?P<arg>\d+)/page/(?P<page>\d+)/?$', views.comments_by_user, name='comments_by_user_paged'),


    url(r'^(?P<name>\w+)/(?P<arg>\d+)/cancelreport/?$', views.cancelReport, name='cancelReport'),

    url(r'^deletecomment/(?P<arg>\d+)/(?P<item_type>\w+)/(?P<item_id>\w+)/?$', views.deleteComment, name='deleteComment'),

    url(r'^auth/register/?$', RegistrationView.as_view(form_class=RegistrationFormUniqueEmail), name='registration_register'),
    url(r'^auth/', include('registration.backends.default.urls')),

    url(r'^login/?$', views.loginView, name='loginView'),
    url(r'^logout/?$', views.logoutView, name='logoutView'),

    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile/?$', views.profile, name='profile'),


    url(r'^news/feed.rss?$', views.feed, name='feed'),
    url(r'^search/?$', views.search, name='search'),
    url(r'^search/(?P<arg>.+?)/?$', views.search, name='search'),

    url(r'^panel/?$', views.ControlPanel, name='ControlPanel'),
    url(r'^panel/mymaps/?$', views.ControlPanel, name='ControlPanel'),
    url(r'^panel/mymaps/page/(?P<page>\d+)/?$', views.ControlPanel, name='maps_paged'),
    url(r'^panel/mymaps/page/(?P<page>\d+)/filter/(?P<filter>\w+)/?$', views.ControlPanel, name='maps_paged_filtered'),
    url(r'^panel/mymaps/filter/(?P<filter>\w+)/?$', views.ControlPanel, name='maps_filtered'),

    url(r'^faq/?$', views.faq, name='faq'),
    url(r'^contacts/?$', views.contacts, name='contacts'),
    url(r'^contacts/sent/?$', views.contacts_sent, name='contacts_sent'),


    url(r'^map/(?P<arg>\w+)/?$', api.mapAPI, name='mapAPI_download'),
    url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/?$', api.mapAPI, name='mapAPI'),
    url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/?$', api.mapAPI, name='mapAPI_list'),
    url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/(?P<arg3>[^/]+)/?$', api.mapAPI, name='mapAPI_list_strict'),
    url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/(?P<arg3>[^/]+)/(?P<arg4>\w+)/?$', api.mapAPI, name='mapAPI_list_strict'),
    url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/(?P<arg3>[^/]+)/(?P<arg4>\w+)/?/(?P<arg5>\w+)/?$', api.mapAPI, name='mapAPI_search'),


    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(r'^robots.txt$', views.robots, name='robots.txt'),

    url(r'^ajax/jRating/(?P<arg>\w+)/?$', ajax.jRating, name='ajax.jRating'),

    url(r'^.*$', views.handle404, name='handle404'),
]
