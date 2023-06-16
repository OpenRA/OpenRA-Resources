import os
import datetime
import pytz
from functools import reduce
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
from openra.models import Maps, MapCategories, Comments, UnsubscribeComments


def selectLicenceInfo(itemObject):
    creative_commons = itemObject.policy_cc
    commercial_use = itemObject.policy_commercial
    cc_adaptations = itemObject.policy_adaptations

    if not creative_commons:
        # no license selected
        return None, None

    if commercial_use and cc_adaptations.lower() == "yes":
        name = "Attribution 4.0 International"
        icons = 'by'
    if commercial_use and cc_adaptations.lower() == "no":
        name = "Attribution-NoDerivatives 4.0 International"
        icons = 'by-nd'
    if commercial_use and cc_adaptations.lower() == "yes and shared alike":
        name = "Attribution-ShareAlike 4.0 International"
        icons = 'by-sa'
    if not commercial_use and cc_adaptations.lower() == "yes":
        name = "Attribution-NonCommercial 4.0 International"
        icons = 'by-nc'
    if not commercial_use and cc_adaptations.lower() == "no":
        name = "Attribution-NonCommercial-NoDerivatives 4.0 International"
        icons = 'by-nc-nd'
    if not commercial_use and cc_adaptations.lower() == "yes and shared alike":
        name = "Attribution-NonCommercial-ShareAlike 4.0 International"
        icons = 'by-nc-sa'
    return name, icons


def send_email_contacts_form(name, email, message):
    connection = mail.get_connection()
    connection.open()

    email = mail.EmailMessage(
        'OpenRA Resource Center - Contacts form',
        'Name: %s\nEmail: %s\nMessage: %s\n' % (name, email, message),
        settings.ADMIN_EMAIL_FROM,
        [settings.ADMIN_EMAIL_TO],
        connection=connection)

    email.send()
    connection.close()


def send_email_to_admin_OnMapFail(tempname):
    connection = mail.get_connection()
    connection.open()
    email = mail.EmailMessage(
        'OpenRA Resource Center - Failed to upload map',
        'See attachment',
        settings.ADMIN_EMAIL_FROM,
        [settings.ADMIN_EMAIL_TO],
        connection=connection)
    email.attach_file(tempname)
    email.send()
    connection.close()


def send_email_to_admin_OnReport(args):
    connection = mail.get_connection()
    connection.open()
    body = "Item: http://%s  \nBy user_id: %s  \nReason: %s  \nInfringement: %s" % (args['addr'], args['user_id'], args['reason'], args['infringement'])
    email = mail.EmailMessage(
        'OpenRA Resource Center(to admin) - New Report',
        body,
        settings.ADMIN_EMAIL_FROM,
        [settings.ADMIN_EMAIL_TO],
        connection=connection)
    email.send()
    connection.close()


def send_email_to_user_OnReport(args):
    mail_addr = return_email(args['owner_id'])
    if mail_addr == "":
        return False
    connection = mail.get_connection()
    connection.open()
    body = "Your %s has been reported: %s \nReason: %s" % (args['resource_type'], args['addr'], args['reason'])
    email = mail.EmailMessage(
        'OpenRA Resource Center - Your content has been reported',
        body,
        settings.ADMIN_EMAIL_FROM,
        [mail_addr],
        connection=connection)
    email.send()
    connection.close()


def send_email_to_user_OnLint(email_addr, body):
    connection = mail.get_connection()
    connection.open()
    email = mail.EmailMessage(
        'OpenRA Resource Center - Lint failed',
        body,
        settings.ADMIN_EMAIL_FROM,
        [email_addr],
        connection=connection)
    email.send()
    connection.close()


def send_email_to_user_OnComment(item_type, item_id, email_addr, info=""):
    if not email_addr:
        return False
    http_host = 'http://resource.openra.net'
    connection = mail.get_connection()
    connection.open()
    if not info:
        body = "New comment on " + item_type.title()[:-1] + " you've commented: " + http_host + "/maps/" + item_id + "/#comments"
    elif info == "owner":
        body = "Your " + item_type.title()[:-1] + " has been commented: " + http_host + "/maps/" + item_id + "/#comments"
    email = mail.EmailMessage(
        'OpenRA Resource Center - New Comment',
        body,
        settings.ADMIN_EMAIL_FROM,
        [email_addr],
        connection=connection)
    email.send()
    connection.close()


def send_email_to_admin(title, body):
    connection = mail.get_connection()
    connection.open()
    email = mail.EmailMessage(
        title,
        body,
        settings.ADMIN_EMAIL_FROM,
        [settings.ADMIN_EMAIL_TO],
        connection=connection)
    email.send()
    connection.close()


def return_email(userid):
    # it will have set value if it's social account and email is provided
    mail_addr = User.objects.get(pk=userid).email
    return mail_addr


def get_account_link(userid):
    obj = SocialAccount.objects.filter(user_id=userid)
    if obj:
        if obj[0].provider == "google":
            if 'link' in obj[0].extra_data:
                return obj[0].extra_data['link']
        elif obj[0].provider == "github":
            if 'html_url' in obj[0].extra_data:
                return obj[0].extra_data['html_url']
    return ""


def sizeof_fmt(disk_size):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if disk_size < 1024.0:
            return "%3.1f %s" % (disk_size, x)
        disk_size /= 1024.0


def count_comments_for_many(mapObject):
    comments = {}
    for item in mapObject:
        comments[str(item.id)] = 0
        revisions = all_revisions_for_map(item.id)
        for rev in revisions:
            comments[str(item.id)] += len(Comments.objects.filter(item_type='maps', item_id=rev, is_removed=False))
    return comments


def get_map_id_of_revision(item, seek_rev):
    revisions = all_revisions_for_map(item.id)
    for rev in revisions:
        mapObj = Maps.objects.get(id=rev)
        if mapObj.revision == seek_rev:
            return mapObj.id
    return 0


def get_map_title_of_revision(item, seek_rev):
    revisions = all_revisions_for_map(item.id)
    for rev in revisions:
        mapObj = Maps.objects.get(id=rev)
        if mapObj.revision == seek_rev:
            return mapObj.title
    return ""


def get_comments_for_all_revisions(request, item_type, item_id):
    comments = []

    revisions = all_revisions_for_map(item_id)
    for rev in revisions:
        current_user_commented = False
        current_rev = Maps.objects.get(id=rev)
        commentsObj = Comments.objects.filter(item_type=item_type, item_id=rev, is_removed=False).order_by('posted')

        for com in commentsObj:
            if com.user == request.user:
                current_user_commented = True

        unsubscribed = False
        if request.user.is_authenticated:
            unsubObj = UnsubscribeComments.objects.filter(item_type=item_type, item_id=rev, user=request.user.id)
            if unsubObj:
                unsubscribed = True

        comments.append([current_rev, commentsObj, current_user_commented, unsubscribed])
    return list(reversed(comments))


def all_revisions_for_map(item_id):
    # Seek back to root revision
    try:
        while True:
            item = Maps.objects.get(id=item_id)
            if item.pre_rev == 0:
                break
            item_id = item.pre_rev
    # Don't crash on broken references
    # TODO: Fix the models so this won't happen!
    except ObjectDoesNotExist:
        pass

    # Seek forwards yielding revisions
    try:
        while True:
            item = Maps.objects.get(id=item_id)
            yield item_id

            item_id = item.next_rev
            if item_id == 0:
                break
    except ObjectDoesNotExist:
        pass


def map_filter(request, maps_query):

    selected_filter = {}
    filter_prepare = {}

    filter_prepare['mods'] = sorted(Maps.objects.values_list('game_mod', flat=True).distinct())
    filter_prepare['categories'] = sorted(MapCategories.objects.values_list('category_name', flat=True))
    filter_prepare['formats'] = sorted(Maps.objects.values_list('mapformat', flat=True).distinct())
    filter_prepare['formats'] = [str(val) for val in filter_prepare['formats']]
    filter_prepare['parsers'] = sorted(Maps.objects.values_list('parser', flat=True).distinct())
    filter_prepare['tilesets'] = sorted(Maps.objects.values_list('tileset', flat=True).distinct())

    filter_prepare['sort_by'] = [
        ['latest', 'latest first'],
        ['oldest', 'oldest first'],
        ['title', 'title'],
        ['title_reversed', 'title in reverse'],
        ['players', 'players'],
        ['lately_commented', 'lately commented'],
        ['rating', 'rating'],
        ['views', 'views'],
        ['downloads', 'downloads'],
        ['revisions', 'upgrade activity']
    ]

    filter_prepare['with_problems'] = [
        ['show', 'Show'],
        ['hide_lint_failed', 'Hide if Lint failed'],
        ['show_only_lint_failed', 'Show only if Lint failed'],
        ['api_dl_disabled', 'API downloading disabled'],
        ['many_reports', 'Too many reports']
    ]

    selected_filter['mod'] = request.GET.getlist('mod', None)
    selected_filter['category'] = request.GET.getlist('category', None)
    selected_filter['format'] = request.GET.getlist('format', None)
    selected_filter['parser'] = request.GET.getlist('parser', None)
    selected_filter['tileset'] = request.GET.getlist('tileset', None)

    selected_filter['players'] = request.GET.get('players', None)
    try:
        selected_filter['players'] = int(selected_filter['players'])
        if selected_filter['players'] < 0:
            selected_filter['players'] = None
        elif selected_filter['players'] == 0:
            selected_filter['players'] = str(selected_filter['players'])
    except BaseException:
        selected_filter['players'] = None

    selected_filter['sort_by'] = request.GET.get('sort_by', None)

    selected_filter['with_problems'] = request.GET.get('with_problems', None)

    selected_filter['show_all_revisions'] = request.GET.get('show_all_revisions', None)

    selected_filter['show_with_reports'] = request.GET.get('show_with_reports', None)
    selected_filter['only_advanced'] = request.GET.get('only_advanced', None)
    selected_filter['only_lua'] = request.GET.get('only_lua', None)
    selected_filter['with_duplicates'] = request.GET.get('with_duplicates', None)
    selected_filter['outdated'] = request.GET.get('outdated', None)

    ####################
    ####################

    # Start Filtering/Sorting

    # filter by game mod
    if selected_filter['mod'] and 'any' not in selected_filter['mod']:
        maps_query = maps_query.filter(game_mod__in=selected_filter['mod'])

    # filter by map category
    if selected_filter['category'] and 'any' not in selected_filter['category']:
        query_category = MapCategories.objects.filter(category_name__in=selected_filter['category'])
        query_category = ['_' + str(cat.id) + '_' for cat in query_category]

        maps_query = maps_query.filter(reduce(lambda x, y: x | y, [Q(categories__contains=item) for item in query_category]))

    # filter by MapFormat
    if selected_filter['format'] and 'any' not in selected_filter['format']:
        maps_query = maps_query.filter(mapformat__in=selected_filter['format'])

    # filter by engine parser
    if selected_filter['parser'] and 'any' not in selected_filter['parser']:
        maps_query = maps_query.filter(parser__in=selected_filter['parser'])

    # filter by tileset
    if selected_filter['tileset'] and 'any' not in selected_filter['tileset']:
        maps_query = maps_query.filter(tileset__in=selected_filter['tileset'])

    # filter by amount of spawn slots
    if selected_filter['players']:
        maps_query = maps_query.filter(players=selected_filter['players'])

    # filter: show all revisions or only the latest
    if selected_filter['show_all_revisions'] != 'on':
        maps_query = maps_query.filter(next_rev=0)

    # filter: show only maps with reports
    if selected_filter['show_with_reports'] == 'on':
        maps_query = maps_query.exclude(amount_reports=0)

    # filter: show only advanced maps
    if selected_filter['only_advanced'] == 'on':
        maps_query = maps_query.filter(advanced_map=True)

    # filter: show only maps with Lua scripts
    if selected_filter['only_lua'] == 'on':
        maps_query = maps_query.filter(lua=True)

    # filter: show only maps with duplicates (by map_hash)
    if selected_filter['with_duplicates'] == 'on':
        dup_Ob = Maps.objects.values_list('map_hash', flat=True).annotate(Count('id')).order_by().filter(id__count__gt=1)
        maps_query = maps_query.filter(map_hash__in=[dup_it for dup_it in dup_Ob])

    # filter: show only last revisions of maps where parser is not equal to the latest official
    if selected_filter['outdated'] == 'on':
        latest_official_parser = settings.OPENRA_VERSIONS[0]
        maps_query = maps_query.filter(next_rev=0).exclude(parser=latest_official_parser)

    # filter options for maps with problems
    if selected_filter['with_problems'] and selected_filter['with_problems'] != 'show':
        if selected_filter['with_problems'] == 'hide_lint_failed':
            maps_query = maps_query.filter(requires_upgrade=False)
        elif selected_filter['with_problems'] == 'show_only_lint_failed':
            maps_query = maps_query.filter(requires_upgrade=True)
        elif selected_filter['with_problems'] == 'api_dl_disabled':
            maps_query = maps_query.filter(downloading=False)
        elif selected_filter['with_problems'] == 'many_reports':
            maps_query = maps_query.filter(amount_reports__gte=3)
    ####################
    ####################

    ####################
    # Sorting
    ####################
    if selected_filter['sort_by'] and selected_filter['sort_by'] != 'latest':
        if selected_filter['sort_by'] == 'oldest':
            maps_query = maps_query.order_by('posted')
        elif selected_filter['sort_by'] == 'title':
            maps_query = maps_query.order_by('title')
        elif selected_filter['sort_by'] == 'title_reversed':
            maps_query = maps_query.order_by('-title')
        elif selected_filter['sort_by'] == 'players':
            maps_query = maps_query.order_by('-players')
        elif selected_filter['sort_by'] == 'lately_commented':
            maps_query = maps_query.extra({'last_comment': 'SELECT coalesce(MAX(posted), \'1990-01-01 00:00:00\') FROM openra_comments WHERE openra_comments.item_id = openra_maps.id AND openra_comments.item_type = \'maps\' AND openra_comments.is_removed = False' }).order_by('-last_comment')
        elif selected_filter['sort_by'] == 'rating':
            maps_query = maps_query.order_by('-rating')
        elif selected_filter['sort_by'] == 'views':
            maps_query = maps_query.order_by('-viewed')
        elif selected_filter['sort_by'] == 'downloads':
            maps_query = maps_query.order_by('-downloaded')
        elif selected_filter['sort_by'] == 'revisions':
            maps_query = maps_query.order_by('-revision')
    else:
        maps_query = maps_query.order_by('-posted')

    ###################

    return [maps_query, filter_prepare, selected_filter]

def prepare_maps_for_json(maps_query):
    maps_query.prefetch_related('user')
    output = {}
    i = 0
    for current_map in maps_query:
        output[i] = {
            'id': current_map.id,
            'posted': str(current_map.posted),
            'uploader': current_map.user.username,
            'title': current_map.title,
            'description': current_map.description,
            'info': current_map.info,
            'author': current_map.author,
            'players': current_map.players,
            'game_mod': current_map.game_mod,
            'map_hash': current_map.map_hash,
            'width': current_map.width,
            'height': current_map.height,
            'bounds': current_map.bounds,
            'advanced_map': current_map.advanced_map,
            'lua': current_map.lua
        }
        i+=1

    return output

def user_account_age(user):
    """Returns the age of a user account in hours"""
    if not user or not user.is_authenticated():
        return 0

    return (timezone.now() - user.date_joined).total_seconds() / 3600


def first_oramap_in_directory(path):
    """Returns the first matching .oramap filename in a given path or None

       The returned string is not prefixed by the directory.

       TODO: This helper is a workaround for the filename not being stored in the model
       This really should be fixed, and then this helper removed!
    """
    for filename in os.listdir(path):
        if filename.endswith('.oramap'):
            return filename
    return None
