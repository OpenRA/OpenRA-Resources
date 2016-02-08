from django.conf.urls import patterns, url, include
from django.views.generic import RedirectView
from registration.forms import RegistrationFormUniqueEmail
from registration.backends.default.views import RegistrationView

from openraData import views, api, ajax

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),

	url(r'^maps/?$', views.maps, name='maps'),
	url(r'^maps/(?P<arg>\d+)/?$', views.displayMap, name='displayMap'),
	url(r'^maps/(?P<arg>\d+)/minimap/?$', views.serveMinimap, name='serveMinimap'),
	url(r'^maps/(?P<arg>\d+)/render/?$', views.serveRender, name='serveRender'),
	url(r'^maps/(?P<arg>\d+)/oramap/?$', views.serveOramap, name='serveOramap'),
	url(r'^maps/(?P<arg>\d+)/oramap/(?P<sync>\w+)/?$', views.serveOramap, name='serverSyncOramap'),
	url(r'^maps/(?P<arg>\d+)/delete/?$', views.DeleteMap, name='DeleteMap'),
	url(r'^maps/(?P<arg>\d+)/setdownloadingstatus/?$', views.SetDownloadingStatus, name='SetDownloadingStatus'),
	url(r'^maps/(?P<arg>\d+)/changersyncstatus/?$', views.ChangeRsyncStatus, name='ChangeRsyncStatus'),
	url(r'^maps/(?P<arg>\d+)/add(?P<item>\w+)sc/?$', views.addScreenshot, name='addScreenshot'),
	url(r'^maps/(?P<arg>\d+)/revisions/?$', views.MapRevisions, name='MapRevisions'),
	url(r'^maps/(?P<arg>\d+)/revisions/page/(?P<page>\d+)/?$', views.MapRevisions, name='MapRevisions'),
	url(r'^(?P<item_type>\w+)/(?P<arg>\d+)/unsubscribe/?$', views.unsubscribe_from_comments, name='Unsubscribe from comments to item'),
	url(r'^maps/author/(?P<author>[^/]+)/?$', views.mapsFromAuthor, name='mapsFromAuthor'),
	url(r'^maps/author/(?P<author>[^/]+)/page/(?P<page>\d+)/?$', views.mapsFromAuthor, name='mapsFromAuthor'),
	url(r'^maps/page/(?P<page>\d+)/?$', views.maps, name='maps_paged'),
	url(r'^maps/page/(?P<page>\d+)/filter/(?P<filter>\w+)/?$', views.maps, name='maps_paged_filtered'),
	url(r'^maps/filter/(?P<filter>\w+)/?$', views.maps, name='maps_filtered'),
	url(r'^maps/(?P<arg>\d+)/yaml/?$', views.serveYaml, name='printYaml'),
	url(r'^maps/(?P<arg>\d+)/rules/?$', views.serveYamlRules, name='printYamlRules'),
	url(r'^maps/(?P<arg>\d+)/lua/(?P<name>[^/]+)/?$', views.serveLua, name='printLua'),
	url(r'^maps/(?P<arg>\d+)/shp/(?P<name>[^/]+)/(?P<request_type>[^/]+)/?$', views.serveMapSHP, name='printMapSHP'),
	url(r'^maps/random/?$', views.randomMap, name='randomMap'),
	url(r'^maps/mostRated/?$', views.mostRatedMap, name='mostRatedMap'),
	url(r'^maps/mostViewed/?$', views.mostViewedMap, name='mostViewedMap'),
	url(r'^maps/mostCommented/?$', views.mostCommentedMap, name='mostCommentedMap'),
	url(r'^maps/mostDownloaded/?$', views.mostDownloadedMap, name='mostDownloadedMap'),
	url(r'^maps/activelyDeveloped/?$', views.activelyDevelopedMap, name='activelyDevelopedMap'),

	url(r'^upload/map/?$', views.uploadMap, name='uploadMap'),
	url(r'^upload/map/(?P<previous_rev>\d+)/?$', views.uploadMap, name='uploadMap'),

	url(r'^upload/replay/?$', views.uploadReplay, name='uploadReplay'),

	url(r'^units/?$', views.units, name='units'),
	url(r'^units/upload/?$', views.uploadUnit, name='uploadUnit'),

	url(r'^mods/?$', views.mods, name='mods'),
	url(r'^mods/upload/?$', views.uploadMod, name='uploadMod'),

	url(r'^palettes/?$', views.mods, name='palettes'),
	url(r'^palettes/upload/?$', views.uploadPalette, name='uploadPalette'),

	url(r'^screenshots/?$', views.screenshots, name='screenshots'),
	url(r'^screenshots/(?P<itemid>\d+)/?$', views.serveScreenshot, name='serveScreenshot'),
	url(r'^screenshots/(?P<itemid>\d+)/delete/?$', views.deleteScreenshot, name='deleteScreenshot'),
	url(r'^screenshots/(?P<itemid>\d+)/(?P<itemname>\w+)/?$', views.serveScreenshot, name='serveScreenshot'),

	url(r'^comments/?$', views.comments, name='comments'),
	url(r'^comments/page/(?P<page>\d+)/?$', views.comments, name='comments_paged'),
	url(r'^comments/user/(?P<arg>\d+)/?$', views.comments_by_user, name='comments_by_user'),
	url(r'^comments/user/(?P<arg>\d+)/page/(?P<page>\d+)/?$', views.comments_by_user, name='comments_by_user_paged'),

	url(r'^assets/?$', views.assets, name='assets'),

	url(r'^replays/?$', views.replays, name='replays'),
	url(r'^replays/page/(?P<page>\d+)/?$', views.replays, name='replays_paged'),

	url(r'^replays/(?P<arg>\d+)/?$', views.displayReplay, name='displayReplay'),
	url(r'^replays/(?P<arg>\d+)/orarep/?$', views.serveReplay, name='serveReplay'),

	url(r'^(?P<name>\w+)/(?P<arg>\d+)/cancelreport/?$', views.cancelReport, name='cancelReport'),

	url(r'^deletecomment/(?P<arg>\d+)/(?P<item_type>\w+)/(?P<item_id>\w+)/?$', views.deleteComment, name='deleteComment'),

	url(r'^accounts/register/?$', RegistrationView.as_view(form_class=RegistrationFormUniqueEmail),
		name='registration_register'), 
	url(r'^accounts/', include('registration.backends.default.urls')),
	url(r'^logout/?$', views.logoutView, name='logoutView'),
	url(r'^accounts/profile/?$', views.profile, name='profile'),
	url(r'^accounts/password/?$', views.profile, name='profile'),

	url(r'^news/feed.rss?$', views.feed, name='feed'),
	url(r'^search/', views.search, name='search'),

	url(r'^panel/?$', views.ControlPanel, name='ControlPanel'),
	url(r'^panel/mymaps/?$', views.ControlPanel, name='ControlPanel'),
	url(r'^panel/mymaps/page/(?P<page>\d+)/?$', views.ControlPanel, name='maps_paged'),
	url(r'^panel/mymaps/page/(?P<page>\d+)/filter/(?P<filter>\w+)/?$', views.ControlPanel, name='maps_paged_filtered'),
	url(r'^panel/mymaps/filter/(?P<filter>\w+)/?$', views.ControlPanel, name='maps_filtered'),
	
	url(r'^faq/?$', views.faq, name='faq'),
	url(r'^links/?$', views.links, name='links'),
	url(r'^contacts/?$', views.contacts, name='contacts'),
	url(r'^contacts/sent/?$', views.contacts_sent, name='contacts_sent'),
	
	url(r'^map/(?P<arg>\w+)/?$', api.mapAPI, name='mapAPI_download'),
	url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/?$', api.mapAPI, name='mapAPI'), 
	url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/?$', api.mapAPI, name='mapAPI_list'),
	url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/(?P<arg3>[^/]+)/?$', api.mapAPI, name='mapAPI_list_strict'),
	url(r'^map/(?P<arg>\w+)/(?P<arg1>[^/]+)/(?P<arg2>\-?\w+)/(?P<arg3>[^/]+)/(?P<arg4>\w+)/?$', api.mapAPI, name='mapAPI_list_strict'),
	
	url(r'^crashlogs/?$', api.CrashLogs, name='CrashLogs'),
	url(r'^crashlogs/(?P<crashid>\w+)/(?P<logfile>\w+)/?$', api.CrashLogsServe, name='CrashLogsServe'),

	url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
	url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
	url(r'^sitemap\.xml$', RedirectView.as_view(url='/static/sitemap.xml')),

	url(r'^ajax/jRating/(?P<arg>\w+)/?$', ajax.jRating, name='ajax.jRating'),

	url(r'^.*$', views.handle404, name='handle404'),
)