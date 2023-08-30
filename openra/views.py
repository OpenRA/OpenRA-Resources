import os
import math
import datetime
import re
import shutil
import random
import json
import cgi
import base64
from urllib.parse import urlencode
import urllib.request
from dependency_injector.wiring import Provide, inject
# from dependency_injector.wiring import Provide, inject

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.http.response import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone

from django.db.models import F
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from openra import content, handlers, misc
from openra.auth import ExceptionLoginFailed, set_session_to_remember_auth, try_login
from openra.classes.screenshot_resource import ScreenshotResource
from openra.models import Maps, Lints, Screenshots, Reports, Rating, Comments, UnsubscribeComments
from openra.services.map_search import MapSearch
from openra.classes.pagination import Pagination
from openra.services.screenshot_repository import ScreenshotRepository

# TODO: Fix the code and reenable some of these warnings
# pylint: disable=invalid-name
# pylint: disable=line-too-long
# pylint: disable=missing-docstring
# pylint: disable=bare-except


def standard_view(request, template, template_args):
    template = loader.get_template(template)

    return HttpResponse(
        template.render(
            template_args,
            request
        )
    )


def index(request):
    return standard_view(
        request,
        'index.html',
        {
            'content': 'index_content.html',
            'request': request,
            'title': content.titles['home'],
            'screenshots': Screenshots.objects.filter(ex_name="maps").order_by('-posted')[0:5]
        }
    )


def loginView(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    errors = []

    if request.method == 'POST':
        try:
            try_login(request)
            set_session_to_remember_auth(
                request,
                request.POST.get('ora_remember', False)
            )
            return HttpResponseRedirect('/')
        except ExceptionLoginFailed as exception:
            errors.append(
                content.auth[exception.reason]
            )

    return standard_view(
        request,
        'auth/login.html',
        {
            'request': request,
            'title': content.titles['login'],
            'errors': errors,
        }
    )


def logoutView(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    if request.method == "POST":
        logout(request)
        return HttpResponseRedirect('/')

    return standard_view(
        request,
        'auth/logout.html',
        {
            'request': request,
            'title': content.titles['logout']
        }
    )


def feed(request):
    template = loader.get_template('feed.html')

    return HttpResponse(
        template.render({
            'request': request,
            'title': content.titles['feed'],
            'lastBuildDate': datetime.datetime.utcnow().isoformat("T"),
            'mapObject': Maps.objects.order_by("-posted")[0:20]
        }, request),
        content_type='text/xml'
    )


@inject
def search(request, search_query="",
           map_search: MapSearch = Provide['map_search']
           ):

    if not search_query:
        if request.method == 'POST':
            if request.POST.get('qsearch', "").strip() == "":
                return HttpResponseRedirect('/')
            return HttpResponseRedirect('/search/' + request.POST.get('qsearch', "").strip())
        else:
            return HttpResponseRedirect('/')

    return standard_view(
        request,
        'search.html',
        {
            'request': request,
            'title': content.titles['search'],
            'search_results': map_search.run(search_query),
            'search_request': search_query,
        }
    )


def ControlPanel(request, page=1):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    perPage = 20
    slice_start = perPage * int(page) - perPage
    slice_end = perPage * int(page)
    mapObject = Maps.objects.filter(user_id=request.user.id).filter(next_rev=0).order_by('-posted')
    amount = mapObject.count()
    rowsRange = int(math.ceil(amount / float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/panel/")

    comments = misc.count_comments_for_many(mapObject)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'control_panel.html',
        'request': request,
        'title': content.titles['panel'],
        'maps': mapObject,
        'page': int(page),
        'range': [i + 1 for i in range(rowsRange)],
        'amount_maps': amount,
        'comments': comments,
    }
    return HttpResponse(template.render(template_args, request))


def maps(request, output_format=""):

    page = int(request.GET.get('page', 1))

    maps_query, filter_prepare, selected_filter = misc.map_filter(request, Maps.objects.filter())

    pagination = Pagination(maps_query, 20)

    maps_query = pagination.get_page(page)

    if output_format == 'json':
        return JsonResponse(misc.prepare_maps_for_json(maps_query))

    if len(maps_query) == 0 and page != 1:
        if request.META['QUERY_STRING']:
            return HttpResponseRedirect("/maps/?" + re.sub("page=\d+&?", "", request.META['QUERY_STRING']))

    comments = misc.count_comments_for_many(maps_query)

    return standard_view(
        request,
        'index.html',
        {
            'content': 'maps.html',
            'request': request,
            'title': content.titles['maps'],
            'maps': maps_query,
            'page': page,
            'pagination': pagination.get_links(page, request.META['QUERY_STRING']),
            'amount': pagination.total,
            'comments': comments,

            'filter_prepare': filter_prepare,
            'selected_filter': selected_filter,
        }
    )


def maps_author(request, author):

    page = int(request.GET.get('page', 1))

    maps_query, filter_prepare, selected_filter = misc.map_filter(
        request,
        Maps.objects.filter(
            author=author.replace("%20", " ")
        )
    )

    pagination = Pagination(maps_query, 20)

    maps_query = pagination.get_page(page)

    if len(maps_query) == 0 and page != 1:
        if request.META['QUERY_STRING']:
            return HttpResponseRedirect("/maps/author/%s/?%s" % (author, re.sub("page=\d+&?", "", request.META['QUERY_STRING'])))

    comments = misc.count_comments_for_many(maps_query)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_author.html',
        'request': request,
        'title': content.titles['maps_author'].format(author),
        'maps': maps_query,
        'page': page,
        'pagination': pagination.get_links(page, request.META['QUERY_STRING']),
        'amount': pagination.total,
        'author': author,
        'comments': comments,

        'filter_prepare': filter_prepare,
        'selected_filter': selected_filter,
    }
    return HttpResponse(template.render(template_args, request))


def maps_uploader(request, uploader):

    try:
        uploader_obj = User.objects.get(username=uploader)
        uploader_id = uploader_obj.id
    except User.DoesNotExist:
        uploader_obj = None
        uploader_id = None

    page = int(request.GET.get('page', 1))

    maps_query, filter_prepare, selected_filter = misc.map_filter(
        request,
        Maps.objects.filter(
            user__id=uploader_id
        )
    )

    pagination = Pagination(maps_query, 20)

    maps_query = pagination.get_page(page)

    if len(maps_query) == 0 and page != 1:
        if request.META['QUERY_STRING']:
            return HttpResponseRedirect("/maps/uploader/%s/?%s" % (uploader, re.sub("page=\d+&?", "", request.META['QUERY_STRING'])))

    comments = misc.count_comments_for_many(maps_query)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_uploader.html',
        'request': request,
        'title': content.titles['maps_uploader'].format(uploader),
        'maps': maps_query,
        'page': page,
        'pagination': pagination.get_links(page, request.META['QUERY_STRING']),
        'amount': pagination.total,
        'uploader': uploader,
        'arg': uploader,
        'comments': comments,

        'filter_prepare': filter_prepare,
        'selected_filter': selected_filter,
    }
    return HttpResponse(template.render(template_args, request))


def map_report(request, map_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    reason = request.POST.get('reportReason', "").strip()
    if reason != "":
        existing_reports_from_user = Reports.objects.filter(user_id=request.user.id, ex_id=map_id, ex_name='maps')
        if not existing_reports_from_user:
            infringement = request.POST.get('infringement', False)
            if infringement == "true":
                infringement = True
            report = Reports(
                user_id=request.user.id,
                reason=reason,
                ex_id=map_id,
                ex_name='maps',
                infringement=infringement,
                posted=timezone.now(),
            )
            report.save()
            Maps.objects.filter(id=map_id).update(amount_reports=Reports.objects.filter(ex_name='maps', ex_id=map_id).count())

            misc.send_email_to_admin_OnReport({'addr': request.META.get('HTTP_HOST', '') + '/maps/' + map_id, 'user_id': request.user.id, 'reason': request.POST['reportReason'].strip(), 'infringement': infringement})
            misc.send_email_to_user_OnReport({'addr': request.META.get('HTTP_HOST', '') + '/maps/' + map_id, 'owner_id': Maps.objects.get(id=map_id).user_id, 'reason': request.POST['reportReason'].strip(), 'resource_type': 'map'})
    return HttpResponseRedirect('/maps/' + map_id)


def map_update_map_info(request, map_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    map_info = request.POST.get('mapInfo', False)
    if map_info:
        map_info = map_info.strip()
        target_map = Maps.objects.get(id=map_id)
        if request.user.is_superuser or request.user.id == target_map.user_id:
            target_map.info = map_info
            target_map.save()
    return HttpResponseRedirect('/maps/' + map_id)


@inject
def map_upload_screenshot(request, map_id,
                          screenshot_repository: ScreenshotRepository = Provide['screenshot_repository']

                          ):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    if request.FILES.get('screenshot', False):

        target_map = Maps.objects.get(id=map_id)
        if request.user.is_superuser or request.user.id == target_map.user_id:
            screenshot_repository.create_from_uploaded_file(
                request.FILES.get('screenshot', False),
                request.user,
                ScreenshotResource(
                    'maps',
                    target_map.id,
                ),
                request.POST.get('map_preview', None) == 'on'
            )

    return HttpResponseRedirect('/maps/' + map_id)


def displayMap(request, arg):
    if request.method == 'POST':
        if request.POST.get('comment', "") != "":
            account_age = misc.user_account_age(request.user)
            if account_age < 24:
                template = loader.get_template('index.html')
                template_args = {
                    'content': 'new_user_action_blocked.html',
                    'hours_remaining': 24 - int(account_age),
                    'title': 'Action Blocked',
                }

                return StreamingHttpResponse(template.render(template_args, request))

            transac = Comments(
                item_type='maps',
                item_id=int(arg),
                user=request.user,
                content=request.POST['comment'].strip(),
                posted=timezone.now(),
                is_removed=False,
            )
            transac.save()

            commented_map_obj = Maps.objects.get(id=arg)
            if commented_map_obj.user != request.user:
                misc.send_email_to_user_OnComment('maps', arg, commented_map_obj.user.email, info="owner")

            comsObj = Comments.objects.filter(item_type='maps', item_id=arg, is_removed=False)
            if comsObj:
                for com in comsObj:
                    if com.user != request.user and com.user != commented_map_obj.user:

                        unsubObj = UnsubscribeComments.objects.filter(item_type='maps', item_id=arg, user=com.user)

                        if not unsubObj:
                            misc.send_email_to_user_OnComment('maps', arg, com.user.email)

            return HttpResponseRedirect('/maps/' + arg + '/')

    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
    oramap_filename = misc.first_oramap_in_directory(path)
    if not oramap_filename:
        return HttpResponseRedirect('/')

    try:
        mapObject = Maps.objects.get(id=arg)
    except BaseException:
        return HttpResponseRedirect('/')

    disk_size = os.path.getsize(os.path.join(path, oramap_filename))
    disk_size = misc.sizeof_fmt(disk_size)

    lints = []
    lintObject = Lints.objects.filter(map_id=mapObject.id, item_type='maps')
    lintObject = sorted(lintObject, key=lambda x: (x.posted), reverse=False)
    for lint_item in lintObject:
        lints.append([lint_item.version_tag, lint_item.pass_status, lint_item.lint_output])

    reportedByUser = False
    reports = []
    reportObject = Reports.objects.filter(ex_id=mapObject.id, ex_name='maps')
    for item in reportObject:
        try:
            usr = User.objects.get(pk=item.user_id)
            reports.append([usr.username, item.reason, item.infringement, item.posted])
        except BaseException:
            pass
        if item.user_id == request.user.id:
            reportedByUser = True

    luaNames = []

    listContent = os.listdir(os.path.join(path, 'content'))

    for fn in listContent:
        if fn.endswith('.lua'):
            luaNames.append(os.path.splitext(fn)[0])

    mapsFromAuthor = Maps.objects.filter(author=mapObject.author, next_rev=0).exclude(id=mapObject.id).distinct('map_hash').order_by('map_hash', '-posted').exclude(map_hash=mapObject.map_hash)
    if len(mapsFromAuthor) >= 8:
        mapsFromAuthor = random.sample(list(mapsFromAuthor), 8)
    else:
        mapsFromAuthor = random.sample(list(mapsFromAuthor), len(mapsFromAuthor))

    similarMaps = Maps.objects.filter(next_rev=0, game_mod=mapObject.game_mod, tileset=mapObject.tileset, players=mapObject.players, map_type=mapObject.map_type, width=mapObject.width, height=mapObject.height).exclude(map_hash=mapObject.map_hash)[0:8]

    duplicates = Maps.objects.filter(map_hash=mapObject.map_hash).exclude(id=mapObject.id)
    if duplicates:
        duplicates = True

    screenshots = Screenshots.objects.filter(ex_name="maps", ex_id=arg)

    try:
        played_counter = urllib.request.urlopen("http://master.openra.net/map_stats?hash=%s" % mapObject.map_hash).read().decode()
        played_counter = json.loads(played_counter)
        if played_counter:
            played_counter = played_counter["played"]
        else:
            played_counter = 0
    except BaseException:
        played_counter = 'unknown'

    ratesAmount = Rating.objects.filter(ex_id=mapObject.id, ex_name='map')
    ratesAmount = len(ratesAmount)

    comments = misc.get_comments_for_all_revisions(request, 'maps', arg)

    # showing upgrade map button
    show_upgrade_map_button = True

    if not (request.user == mapObject.user or request.user.is_superuser):
        show_upgrade_map_button = False

    if mapObject.next_rev != 0:
        show_upgrade_map_button = False  # upgrade only the latest revision

    if not any([mapObject.parser in v for v in settings.OPENRA_UPDATE_VERSIONS.values()]):
        show_upgrade_map_button = False  # no compatible update targets

    ###

    map_preview = None
    for sc_item in screenshots:
        if sc_item.map_preview:
            map_preview = sc_item

    license, icons = misc.selectLicenceInfo(mapObject)
    userObject = User.objects.get(pk=mapObject.user_id)
    Maps.objects.filter(id=mapObject.id).update(viewed=mapObject.viewed + 1)

    has_upgrade_logs = mapObject.mapupgradelogs_set.count() > 0

    template = loader.get_template('index.html')
    template_args = {
        'content': 'displayMap.html',
        'request': request,
        'title': 'Map details - ' + mapObject.title,
        'map': mapObject,
        'userid': userObject,
        'arg': arg,
        'license': license,
        'icons': icons,
        'reports': reports,
        'reported': reportedByUser,
        'luaNames': luaNames,
        'mapsFromAuthor': mapsFromAuthor,
        'similarMaps': similarMaps,
        'screenshots': screenshots,
        'disk_size': disk_size,
        'duplicates': duplicates,
        'played_counter': played_counter,
        'ratesAmount': ratesAmount,
        'REPORTS_PENALTY_AMOUNT': settings.REPORTS_PENALTY_AMOUNT,
        'lints': lints,
        'comments': comments,
        'show_upgrade_map_button': show_upgrade_map_button,
        'map_preview': map_preview,
        'last_parser': settings.OPENRA_VERSIONS[0],
        'has_upgrade_logs': has_upgrade_logs
    }
    return StreamingHttpResponse(template.render(template_args, request))


def updateMap(request, arg):

    mapObject = Maps.objects.filter(id=arg)
    if not mapObject or not mapObject[0]:
        return HttpResponseRedirect('/')

    source_map = mapObject[0]
    if source_map.user != request.user and not request.user.is_superuser:
        return HttpResponseRedirect('/maps/' + arg + '/')

    if source_map.next_rev != 0:
        return HttpResponseRedirect('/maps/' + arg + '/')  # update only the latest revision

    update_parsers = [k for k in settings.OPENRA_UPDATE_VERSIONS if source_map.parser in settings.OPENRA_UPDATE_VERSIONS[k]]
    if not update_parsers:
        return HttpResponseRedirect('/maps/' + arg + '/')  # no newer parsers can update from the current parser

    ##########
    update_failed = False
    if request.method == 'POST':
        target_parser = request.POST.get('target_parser', None)
        if target_parser and target_parser in settings.OPENRA_VERSIONS:
            try:
                updated_item = handlers.process_update(mapObject[0], target_parser)
                redirect = '/maps/' + str(updated_item.id) + '/'
                if updated_item.mapupgradelogs_set.count() > 0:
                    redirect += 'update_logs?updated'

                return HttpResponseRedirect(redirect)
            except handlers.InvalidMapException as exception:
                update_failed = True
                print('Update Failed: ' + exception.message)

    ##########

    template = loader.get_template('index.html')
    template_args = {
        'content': 'map_update.html',
        'request': request,
        'title': 'Update Map - ' + mapObject[0].title,
        'map': mapObject[0],
        'parsers': update_parsers,
        'update_failed': update_failed,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def updateMapLogs(request, arg):
    mapObject = Maps.objects.filter(id=arg)
    item = mapObject[0]
    logs = item.mapupgradelogs_set.all().order_by('-id')
    template = loader.get_template('index.html')
    template_args = {
        'content': 'map_update_logs.html',
        'request': request,
        'title': 'Map Update Log - ' + mapObject[0].title,
        'map': item,
        'logs': logs,
        'after_update_notice': 'updated' in request.GET.keys()
    }
    return StreamingHttpResponse(template.render(template_args, request))


def deleteScreenshot(request, itemid):
    scObject = Screenshots.objects.filter(id=itemid)
    if scObject:
        arg = str(scObject[0].ex_id)
        name = scObject[0].ex_name
        if request.user.is_superuser or scObject[0].user_id == request.user.id:
            path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'screenshots', itemid)
            try:
                shutil.rmtree(path)
            except BaseException:
                pass
            scObject[0].delete()
            return HttpResponseRedirect("/" + name + "/" + arg + "/")
    return HttpResponseRedirect("/")


def deleteComment(request, arg, item_type, item_id):
    comObject = Comments.objects.filter(id=arg)
    if comObject:
        if comObject[0].user == request.user or request.user.is_superuser:
            Comments.objects.filter(id=arg).update(is_removed=True)

            coms_exist_for_map_for_user = Comments.objects.filter(id=arg, is_removed=False, user=request.user.id)
            if not coms_exist_for_map_for_user:
                UnsubscribeComments.objects.filter(item_type=item_type, item_id=item_id, user=request.user.id).delete()

    return HttpResponseRedirect("/" + item_type + "/" + item_id + "/")


def unsubscribe_from_comments(request, item_type, arg):
    if request.user.is_authenticated:
        unsubObj = UnsubscribeComments.objects.filter(user=request.user.id)
        if not unsubObj:
            transac = UnsubscribeComments(
                user=request.user,
                item_type=item_type,
                item_id=arg,
                unsubscribed=timezone.now(),
            )
            transac.save()
        else:
            unsubObj.delete()

    return HttpResponseRedirect("/" + item_type + "/" + arg + "/")


def serveScreenshot(request, itemid, itemname=""):
    image = ""
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'screenshots', itemid)
    try:
        Dir = os.listdir(path)
    except BaseException:
        return HttpResponseRedirect("/")
    for fn in Dir:
        if "-mini." in fn:
            if itemname == "mini":
                image = os.path.join(path, fn)
                mime = fn.split('.')[1]
                break
        else:
            if itemname == "":
                image = os.path.join(path, fn)
                mime = fn.split('.')[1]
                break
    if image == "":
        return StreamingHttpResponse("")
    response = StreamingHttpResponse(open(image, 'rb'), content_type='image/' + mime)
    response['Content-Disposition'] = 'attachment; filename = %s' % fn
    return response


def serveMinimap(request, arg):
    minimap = ""
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
    try:
        contentDir = os.listdir(os.path.join(path, 'content'))
    except BaseException:
        return HttpResponseRedirect("/")
    for filename in contentDir:
        if filename == "map.png":
            minimap = filename
            serveImage = os.path.join(path, 'content', minimap)
            break
    if minimap == "":
        mapDir = os.listdir(path)
        for filename in mapDir:
            if filename.endswith("-mini.png"):
                minimap = filename
                serveImage = os.path.join(path, minimap)
                break
    if minimap == "":
        minimap = "nominimap.png"
        serveImage = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'static', 'images', 'nominimap.png')
    response = StreamingHttpResponse(open(serveImage, 'rb'), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename = %s' % minimap
    return response


def serveOramap(request, arg, sync=""):
    oramap = ""
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
    try:
        mapDir = os.listdir(path)
    except BaseException:
        return HttpResponseRedirect("/")
    for filename in mapDir:
        if filename.endswith(".oramap"):
            oramap = filename
            break
    if oramap == "":
        return HttpResponseRedirect('/maps/' + arg)
    else:
        serveOramap = os.path.join(path, oramap)
        if sync == "sync":
            oramap = arg + ".oramap"
        response = StreamingHttpResponse(open(serveOramap, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename = %s' % oramap
        response['Content-Length'] = os.path.getsize(serveOramap)
        Maps.objects.filter(id=arg).update(downloaded=F('downloaded') + 1)
        return response


def serveYaml(request, arg):
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg, 'content', 'map.yaml')
    response = StreamingHttpResponse(cgi.escape(open(path).read(), quote=None), content_type='application/plain')
    response['Content-Disposition'] = 'attachment; filename = map.yaml'
    return response


def serveYamlRules(request, arg):

    result = ""

    mapObject = Maps.objects.filter(id=arg).first()
    if mapObject:
        if int(mapObject.mapformat) < 10:
            path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg, 'content', 'map.yaml')
            start = False
            fn = open(path, 'r')
            lines = fn.readlines()
            fn.close()
            for line in lines:
                if "Rules:" in line:
                    start = True
                if start:
                    result += line
        else:
            result = base64.b64decode(mapObject.base64_rules).decode()
    else:
        HttpResponseRedirect('/')

    response = StreamingHttpResponse(cgi.escape(result, quote=None), content_type='application/plain')
    response['Content-Disposition'] = 'attachment; filename = advanced.%s' % arg
    return response


def serveLua(request, arg, name):
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg, 'content')
    fname = ""
    listdir = os.listdir(path)
    for fn in listdir:
        if fn.endswith('.lua'):
            if os.path.splitext(fn)[0] == name:
                fname = fn
                break
    if fname == "":
        raise Http404
    response = StreamingHttpResponse(cgi.escape(open(os.path.join(path, fname)).read(), quote=None), content_type='application/plain')
    response['Content-Disposition'] = 'attachment; filename = %s' % fname
    return response


def uploadMap(request, previous_rev=0):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/maps/')

    account_age = misc.user_account_age(request.user)
    if account_age < 24:
        template = loader.get_template('index.html')
        template_args = {
            'content': 'new_user_action_blocked.html',
            'hours_remaining': 24 - int(account_age),
            'title': 'Action Blocked',
        }

        return StreamingHttpResponse(template.render(template_args, request))

    error_message = None
    rev = 1
    previous_rev_title = ""
    user_id = request.user.id
    if previous_rev != 0:
        mapObject = Maps.objects.filter(id=previous_rev)
        if mapObject:
            rev = mapObject[0].revision + 1
            previous_rev_title = mapObject[0].title
            if request.user.is_superuser:
                user_id = mapObject[0].user_id

    if request.method == 'POST' and request.FILES.get('file', None) is not None:
        try:
            item = handlers.process_upload(user_id, request.FILES['file'], request.POST, rev, previous_rev)
            return HttpResponseRedirect('/maps/' + str(item.id) + "/")
        except handlers.InvalidMapException as exception:
            error_message = exception.message

    template = loader.get_template('index.html')
    template_args = {
        'content': 'uploadMap.html',
        'request': request,
        'title': 'Uploading Map',
        'previous_rev': previous_rev,
        'previous_rev_title': previous_rev_title,
        'rev': rev,
        'parsers': settings.OPENRA_VERSIONS,
        'error_response': error_message,
    }

    if settings.SITE_MAINTENANCE:
        template_args['content'] = 'service/maintenance.html'
        template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

    return StreamingHttpResponse(template.render(template_args, request))


def DeleteMap(request, arg):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/maps/')
    try:
        mapObject = Maps.objects.get(id=arg)
    except BaseException:
        return HttpResponseRedirect('/maps/')
    mapTitle = mapObject.title
    mapAuthor = mapObject.author
    if mapObject.user_id == request.user.id or request.user.is_superuser:
        path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
        try:
            shutil.rmtree(path)
        except BaseException:
            pass
        Screenshots.objects.filter(ex_id=mapObject.id, ex_name='maps').delete()
        Reports.objects.filter(ex_id=mapObject.id, ex_name='maps').delete()
        Comments.objects.filter(item_id=mapObject.id, item_type='maps').delete()
        UnsubscribeComments.objects.filter(item_id=mapObject.id, item_type='maps').delete()
        Lints.objects.filter(map_id=mapObject.id, item_type='maps').delete()
        Rating.objects.filter(ex_id=mapObject.id, ex_name='maps').delete()
        if mapObject.pre_rev != 0:
            Maps.objects.filter(id=mapObject.pre_rev).update(next_rev=mapObject.next_rev)
        if mapObject.next_rev != 0:
            Maps.objects.filter(id=mapObject.next_rev).update(pre_rev=mapObject.pre_rev)
        mapObject.delete()
    template = loader.get_template('index.html')
    template_args = {
        'content': 'deleteMap.html',
        'request': request,
        'title': 'Delete Map',
        'mapTitle': mapTitle,
        'mapAuthor': mapAuthor,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def SetDownloadingStatus(request, arg):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/maps/' + arg)
    try:
        mapObject = Maps.objects.get(id=arg)
    except BaseException:
        return HttpResponseRedirect('/maps/')
    if mapObject.user_id == request.user.id or request.user.is_superuser:
        if mapObject.downloading:
            Maps.objects.filter(id=arg).update(downloading=False)
        else:
            Maps.objects.filter(id=arg).update(downloading=True)
    return HttpResponseRedirect('/maps/' + arg)


def addScreenshot(request, arg, item):
    if item == 'map':
        Object = Maps.objects.filter(id=arg)
    if not (Object[0].user_id == request.user.id or request.user.is_superuser):
        return StreamingHttpResponse("")
    template = loader.get_template('addScreenshotForm.html')
    template_args = {
        'request': request,
        'arg': arg,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def maps_revisions(request, arg, page=1):
    perPage = 20
    slice_start = perPage * int(page) - perPage
    slice_end = perPage * int(page)

    try:
        tempObj = Maps.objects.get(id=arg)
    except BaseException:
        return HttpResponseRedirect('/')

    revisions = misc.all_revisions_for_map(arg)
    mapObject = Maps.objects.filter(id__in=revisions).order_by('-revision', '-posted')
    amount = len(mapObject)
    rowsRange = int(math.ceil(amount / float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/maps/%s/revisions/" % arg)

    comments = misc.count_comments_for_many(mapObject)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_revisions.html',
        'request': request,
        'title': 'Revisions',
        'maps': mapObject,
        'page': int(page),
        'range': [i + 1 for i in range(rowsRange)],
        'amount': amount,
        'arg': arg,
        'comments': comments,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def cancelReport(request, name, arg):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name=name).delete()
    Maps.objects.filter(id=arg).update(amount_reports=F('amount_reports') - 1)
    return HttpResponseRedirect('/' + name + '/' + arg)


def screenshots(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': 'screenshots.html',
        'request': request,
        'title': 'Screenshots',
    }
    return StreamingHttpResponse(template.render(template_args, request))


def comments(request, page=1):
    perPage = 20
    slice_start = perPage * int(page) - perPage
    slice_end = perPage * int(page)

    comments = Comments.objects.filter(is_removed=False).order_by('-posted')
    amount = len(comments)
    rowsRange = int(math.ceil(amount / float(perPage)))   # amount of rows
    comments = comments[slice_start:slice_end]
    amount_this_page = len(comments)

    if amount_this_page == 0 and int(page) != 1:
        return HttpResponseRedirect("/comments/")

    last_comment_id_seen = request.COOKIES.get('last_comment_id_seen', comments[0].id)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'comments.html',
        'request': request,
        'title': 'Comments',
        'comments': comments,
        'amount': amount,
        'amount_this_page': amount_this_page,
        'range': [i + 1 for i in range(rowsRange)],
        'page': int(page),
        'last_comment_id_seen': int(last_comment_id_seen),
    }
    response = StreamingHttpResponse(template.render(template_args, request))
    if int(page) == 1:
        response.set_cookie('last_comment_id_seen', comments[0].id, max_age=4320000)
    return response


def comments_by_user(request, arg, page=1):
    perPage = 20
    slice_start = perPage * int(page) - perPage
    slice_end = perPage * int(page)

    comments = Comments.objects.filter(is_removed=False, user=arg).order_by('-posted')
    amount = len(comments)
    rowsRange = int(math.ceil(amount / float(perPage)))   # amount of rows
    comments = comments[slice_start:slice_end]
    amount_this_page = len(comments)

    if amount_this_page == 0 and int(page) != 1:
        return HttpResponseRedirect("/comments/user/" + arg + "/")

    template = loader.get_template('index.html')
    template_args = {
        'content': 'comments.html',
        'request': request,
        'title': 'Comments by ' + request.user.username,
        'comments': comments,
        'amount': amount,
        'amount_this_page': amount_this_page,
        'range': [i + 1 for i in range(rowsRange)],
        'page': int(page),
        'comments_by_user': User.objects.filter(id=arg).first(),
    }
    return StreamingHttpResponse(template.render(template_args, request))


def handle404(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': '404.html',
        'request': request,
        'title': 'Page not found',
    }
    return StreamingHttpResponse(template.render(template_args, request), status=404)


def profile(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    mapObject = Maps.objects.filter(user_id=request.user.id, next_rev=0)
    amountMaps = len(mapObject)
    ifsocial = False
    social = SocialAccount.objects.filter(user=request.user.id)
    if len(social) != 0:
        ifsocial = True
    template = loader.get_template('index.html')
    template_args = {
        'content': 'profile.html',
        'request': request,
        'title': 'Profile',
        'amountMaps': amountMaps,
        'ifsocial': ifsocial,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def faq(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': 'faq.html',
        'request': request,
        'title': 'FAQ',
    }
    return StreamingHttpResponse(template.render(template_args, request))


def contacts(request):
    message_sent = False
    if request.method == 'POST':
        if request.POST.get('contacts_submit', "").strip() != "":
            name = request.POST.get('name', "")
            email = request.POST.get('email', "")
            message = request.POST.get('message', "")

            g_recaptcha_response = request.POST.get('g-recaptcha-response', "")
            if g_recaptcha_response:
                params = urlencode({
                    'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': g_recaptcha_response,
                    'remoteip': request.META.get("REMOTE_ADDR", ""),
                }).encode('utf-8')
                req = urllib.request.Request(
                    url="https://www.google.com/recaptcha/api/siteverify",
                    data=params,
                    headers={
                        "Content-type": "application/x-www-form-urlencoded",
                        "User-agent": "reCAPTCHA Python"
                    }
                )
                resp = urllib.request.urlopen(req).read().decode('utf-8')
                json_resp = json.loads(resp)
                if json_resp['success']:
                    misc.send_email_contacts_form(name, email, message)
                    return HttpResponseRedirect('/contacts/sent/')
            return HttpResponseRedirect('/contacts/')
    template = loader.get_template('index.html')
    template_args = {
        'content': 'contacts.html',
        'request': request,
        'title': 'Contacts',
        'message_sent': message_sent,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def contacts_sent(request):
    message_sent = True
    template = loader.get_template('index.html')
    template_args = {
        'content': 'contacts.html',
        'request': request,
        'title': 'Contacts',
        'message_sent': message_sent,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def robots(request):
    template = loader.get_template('service/robots.txt')
    template_args = {
        'request': request,
    }
    return StreamingHttpResponse(template.render(template_args, request), content_type='text/plain')
