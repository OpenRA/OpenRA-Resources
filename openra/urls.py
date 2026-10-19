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
    url(r'^maps/(?P<map_id>\d+)/?$', views.display_map, name='display_map'),
    url(r'^maps/(?P<arg>\d+)/minimap/?$', views.serve_minimap, name='serve_minimap'),
    url(r'^maps/(?P<arg>\d+)/oramap/?$', views.serve_oramap, name='serve_oramap'),
    url(r'^maps/(?P<arg>\d+)/oramap/(?P<sync>\w+)/?$', views.serve_oramap, name='server_sync_oramap'),
    url(r'^maps/(?P<arg>\d+)/delete/?$', views.delete_map, name='delete_map'),
    url(r'^maps/(?P<arg>\d+)/setdownloadingstatus/?$', views.set_downloading_status, name='set_downloading_status'),
    url(r'^maps/(?P<arg>\d+)/add(?P<item>\w+)sc/?$', views.add_screenshot, name='add_screenshot'),
    url(r'^maps/(?P<arg>\d+)/revisions/?$', views.maps_revisions, name='maps_revisions'),
    url(r'^maps/(?P<arg>\d+)/revisions/page/(?P<page>\d+)/?$', views.maps_revisions, name='maps_revisions_page'),
    url(r'^maps/(?P<arg>\d+)/update/?$', views.update_map, name='update_map'),
    url(r'^maps/(?P<arg>\d+)/update_logs/?$', views.update_map_logs, name='update_map_logs'),
    url(r'^(?P<item_type>\w+)/(?P<arg>\d+)/unsubscribe/?$', views.unsubscribe_from_comments, name='item_comments_unsubscribe'),
    url(r'^maps/author/(?P<author>.+?)/?$', views.maps_author, name='maps_author'),
    url(r'^maps/uploader/(?P<uploader>.+?)/?$', views.maps_uploader, name='maps_uploader'),
    url(r'^maps/(?P<arg>\d+)/yaml/?$', views.serve_yaml, name='print_yaml'),
    url(r'^maps/(?P<arg>\d+)/rules/?$', views.serve_yaml_rules, name='print_yaml_rules'),
    url(r'^maps/(?P<arg>\d+)/lua/(?P<name>[^/]+)/?$', views.serve_lua, name='print_lua'),

    url(r'^maps/(?P<map_id>\d+)/report', views.map_report, name='map_report'),
    url(r'^maps/(?P<map_id>\d+)/update-map-info', views.map_update_map_info, name='map_update_map_info'),
    url(r'^maps/(?P<map_id>\d+)/upload-screenshot', views.map_upload_screenshot, name='map_upload_screenshot'),
    url(r'^maps/(?P<map_id>\d+)/post-comment', views.map_post_comment, name='map_post_comment'),

    url(r'^upload/map/?$', views.upload_map, name='upload_map'),
    url(r'^upload/map/(?P<previous_rev>\d+)/?$', views.upload_map, name='upload_map_revision'),


    url(r'^screenshots/?$', views.screenshots, name='screenshots'),
    url(r'^screenshots/(?P<itemid>\d+)/?$', views.serve_screenshot, name='serve_screenshot'),
    url(r'^screenshots/(?P<itemid>\d+)/delete/?$', views.delete_screenshot, name='delete_screenshot'),
    url(r'^screenshots/(?P<itemid>\d+)/(?P<itemname>\w+)/?$', views.serve_screenshot, name='serve_item_screenshot'),

    url(r'^comments/?$', views.comments, name='comments'),
    url(r'^comments/page/(?P<page>\d+)/?$', views.comments, name='comments_paged'),
    url(r'^comments/user/(?P<arg>\d+)/?$', views.comments_by_user, name='comments_by_user'),
    url(r'^comments/user/(?P<arg>\d+)/page/(?P<page>\d+)/?$', views.comments_by_user, name='comments_by_user_paged'),


    url(r'^(?P<name>\w+)/(?P<arg>\d+)/cancelreport/?$', views.cancel_report, name='cancel_report'),

    url(r'^deletecomment/(?P<arg>\d+)/(?P<item_type>\w+)/(?P<item_id>\w+)/?$', views.delete_comment, name='delete_comment'),

    url(r'^auth/register/?$', RegistrationView.as_view(form_class=RegistrationFormUniqueEmail), name='registration_register'),
    url(r'^auth/', include('registration.backends.default.urls')),

    url(r'^login/?$', views.login_view, name='login_view'),
    url(r'^logout/?$', views.logout_view, name='logout_view'),

    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile/?$', views.profile, name='profile'),
    url(r'^accounts/actions-blocked/?$', views.user_actions_blocked, name='actions_blocked'),


    url(r'^news/feed.rss?$', views.feed, name='feed'),
    url(r'^search/?$', views.search, name='search'),
    url(r'^search/(?P<search_query>.+?)/?$', views.search, name='search_query'),

    url(r'^panel/?$', views.control_panel, name='control_panel'),

    url(r'^faq/?$', views.faq, name='faq'),

    url(r'^map/', include([
        url(r'^hash/(?P<map_hashes>[^/]+)/yaml/?$', api.map_info_from_hashes, {'yaml': True}, name='api_map_info_from_hashes_yaml'),
        url(r'^hash/(?P<map_hashes>[^/]+)/?$', api.map_info_from_hashes, name='api_map_info_from_hashes'),
        url(r'^id/(?P<map_ids>[^/]+)/yaml/?$', api.map_info_from_ids, {'yaml': True}, name='api_map_info_from_ids_yaml'),
        url(r'^id/(?P<map_ids>[^/]+)/?$', api.map_info_from_ids, name='api_map_info_from_ids'),
        url(r'^url/(?P<map_hashes>[^/]+)/yaml/?$', api.map_urlinfo_from_hashes, {'yaml': True}, name='api_map_urlinfo_from_hashes_yaml'),
        url(r'^url/(?P<map_hashes>[^/]+)/?$', api.map_urlinfo_from_hashes, name='api_map_urlinfo_from_hashes'),
        url(r'^lastmap/yaml/?$', api.latest_map_info, {'yaml': True}, name='api_latest_map_info_yaml'),
        url(r'^lastmap/?$', api.latest_map_info, name='api_latest_map_info'),
        url(r'^(?P<map_hash>\w+)/?$', api.download_map, name='api_download_map'),
    ])),

    url(r'^api/maps?$', views.maps, {'output_format': 'json'}, name='api_maps'),

    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(r'^robots.txt$', views.robots, name='robots_txt'),

    url(r'^ajax/jRating/(?P<arg>\w+)/?$', ajax.jRating, name='ajax_j_rating'),

    url(r'^.*$', views.handle_404, name='handle_404'),
]
