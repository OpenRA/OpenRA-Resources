import os
import math
import re
import urllib.request
import datetime
import shutil
import random
import operator
import json
import cgi
import base64
import zipfile
from urllib.parse import urlencode
from io import BytesIO
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone

from django.db.models import F
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from openra import handlers, misc, utility
from openra.models import Maps, Lints, Screenshots, Reports, Rating, Comments, UnsubscribeComments, MapCategories


def index(request):
    scObject = Screenshots.objects.filter(ex_name="maps").order_by('-posted')[0:5]

    template = loader.get_template('index.html')
    template_args = {
        'content': 'index_content.html',
        'request': request,
        'title': '',
        'screenshots': scObject,
    }
    if settings.SITE_MAINTENANCE:
        template_args['content'] = 'service/maintenance.html'
        template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER
    return StreamingHttpResponse(template.render(template_args, request))


def loginView(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    errors = []

    username = request.POST.get('ora_username', '').strip()
    password = request.POST.get('ora_password', '').strip()
    remember = request.POST.get('ora_remember', '')
    input_referer = request.POST.get('referer', '/')

    if username != '' and password != '':

        if not remember:
            request.session.set_expiry(0)  # the user’s session cookie will expire when the user’s Web browser is closed.

        account = authenticate(username=username, password=password)
        if account is not None:
            if account.is_active:
                login(request, account)
                return HttpResponseRedirect(input_referer)
            else:
                errors.append("User is inactive, please activate account first.")
        else:
            errors.append("Incorrect username or password.")

    referer = request.META.get('HTTP_REFERER', '/')
    if input_referer != '/':
        referer = input_referer
    if 'auth' in referer or 'account' in referer:
        referer = '/'

    template = loader.get_template('auth/login.html')
    template_args = {
        'request': request,
        'title': 'OpenRA Resource Center - Sign In',
        'referer': referer if request.META['HTTP_HOST'] in referer else '/',
        'errors': errors,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def logoutView(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    if request.method == "POST":
        logout(request)
        return HttpResponseRedirect(request.POST.get('referer', '/'))

    referer = request.META.get('HTTP_REFERER', '/')

    template = loader.get_template('auth/logout.html')
    template_args = {
        'request': request,
        'title': 'OpenRA Resource Center - Sign Out',
        'referer': referer if request.META['HTTP_HOST'] in referer else '/',
    }
    return StreamingHttpResponse(template.render(template_args, request))


def feed(request):
    mapObject = Maps.objects.order_by("-posted")[0:20]
    d = datetime.datetime.utcnow()
    lastBuildDate = d.isoformat("T")
    template = loader.get_template('feed.html')
    template_args = {
        'request': request,
        'title': 'OpenRA Resource Center - RSS Feed',
        'lastBuildDate': lastBuildDate,
        'mapObject': mapObject,
    }
    return StreamingHttpResponse(template.render(template_args, request), content_type='text/xml')


def search(request, arg=""):

    if not arg:
        if request.method == 'POST':
            if request.POST.get('qsearch', "").strip() == "":
                return HttpResponseRedirect('/')
            return HttpResponseRedirect('/search/' + request.POST.get('qsearch', "").strip())
        else:
            return HttpResponseRedirect('/')

    search_request = arg

    global_search_request = {}
    global_search_request['maps'] = {'amount': 0, 'hash': None, 'title': None, 'info': None}

    s_by_hash = Maps.objects.filter(map_hash=search_request)
    global_search_request['maps']['hash'] = s_by_hash
    global_search_request['maps']['amount'] += len(s_by_hash)

    s_by_title = Maps.objects.filter(title__icontains=search_request)
    global_search_request['maps']['title'] = s_by_title
    global_search_request['maps']['amount'] += len(s_by_title)

    s_by_info = Maps.objects.filter(info__icontains=search_request)
    global_search_request['maps']['amount'] += len(s_by_info)

    s_by_description = Maps.objects.filter(description__icontains=search_request).exclude(info__icontains=search_request)
    global_search_request['maps']['amount'] += len(s_by_description)
    global_search_request['maps']['info'] = [s_by_info, s_by_description]

    s_by_author = Maps.objects.filter(author__icontains=search_request)
    global_search_request['maps']['author'] = s_by_author
    global_search_request['maps']['amount'] += len(s_by_author)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'search.html',
        'request': request,
        'title': ' - Search',
        'global_search_request': global_search_request,
        'search_request': search_request,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def ControlPanel(request, page=1, filter=""):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')
    perPage = 16
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)
    mapObject = Maps.objects.filter(user_id=request.user.id).filter(next_rev=0).order_by('-posted')
    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/panel/")

    comments = misc.count_comments_for_many(mapObject, 'maps')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'control_panel.html',
        'request': request,
        'title': ' - My Content',
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount_maps': amount,
        'comments': comments,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def maps(request, page=1):

    mapObject = Maps.objects.filter()
    mapObject, filter_prepare, selected_filter = misc.map_filter(request, mapObject)

    perPage = 20
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    amount_this_page = len(mapObject)
    if amount_this_page == 0 and int(page) != 1:
        if request.META['QUERY_STRING']:
            return HttpResponseRedirect("/maps/?" + request.META['QUERY_STRING'])
        return HttpResponseRedirect("/maps/")

    comments = misc.count_comments_for_many(mapObject, 'maps')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps.html',
        'request': request,
        'title': ' - Maps',
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
        'comments': comments,

        'filter_prepare': filter_prepare,
        'selected_filter': selected_filter,
    }

    if settings.SITE_MAINTENANCE:
        template_args['content'] = 'service/maintenance.html'
        template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

    return StreamingHttpResponse(template.render(template_args, request))


def maps_zip(request):

    mapObject = Maps.objects.filter()
    mapObject, filter_prepare, selected_filter = misc.map_filter(request, mapObject)

    s = BytesIO()
    zf = zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED)

    zip_filename = "resource_center_maps.zip"

    for item in mapObject:
        oramap = ""
        item_path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
        try:
            mapDir = os.listdir(item_path)
        except:
            continue
        for filename in mapDir:
            if filename.endswith(".oramap"):
                oramap = filename
                break
        if not oramap:
            continue

        zip_path = os.path.join('maps', item.game_mod, '%d.oramap' % item.id)

        zf.write(os.path.join(item_path, oramap), zip_path, zipfile.ZIP_DEFLATED)
    zf.close()

    response = HttpResponse(s.getvalue(), content_type='application/x-zip-compressed')
    response['Content-Disposition'] = 'attachment; filename = %s' % zip_filename
    response['Content-Length'] = s.tell()
    return response


def maps_author(request, author, page=1):

    mapObject = Maps.objects.filter(author=author.replace("%20", " "))
    mapObject, filter_prepare, selected_filter = misc.map_filter(request, mapObject)

    perPage = 20
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        if request.META['QUERY_STRING']:
            return HttpResponseRedirect("/maps/author/%s/?%s" % (author, request.META['QUERY_STRING']))
        return HttpResponseRedirect("/maps/author/%s/" % author)

    comments = misc.count_comments_for_many(mapObject, 'maps')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_author.html',
        'request': request,
        'title': ' - Maps From ' + author,
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
        'author': author,
        'comments': comments,

        'filter_prepare': filter_prepare,
        'selected_filter': selected_filter,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def maps_uploader(request, arg, page=1):

    mapObject = Maps.objects.filter(user__id=arg)
    if not mapObject:
        HttpResponseRedirect('/maps/')

    mapObject, filter_prepare, selected_filter = misc.map_filter(request, mapObject)

    perPage = 20
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        if request.META['QUERY_STRING']:
            return HttpResponseRedirect("/maps/uploader/%s/?%s" % (arg, request.META['QUERY_STRING']))
        return HttpResponseRedirect("/maps/uploader/%s/" % arg)

    comments = misc.count_comments_for_many(mapObject, 'maps')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_uploader.html',
        'request': request,
        'title': ' - Maps uploaded by ' + mapObject[0].user.username,
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
        'uploader': mapObject[0].user.username,
        'arg': arg,
        'comments': comments,

        'filter_prepare': filter_prepare,
        'selected_filter': selected_filter,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def maps_duplicates(request, maphash, page=1):

    mapObject = Maps.objects.filter(map_hash=maphash)
    if not mapObject:
        HttpResponseRedirect('/maps/')

    mapObject = sorted(mapObject, key=lambda x: (x.posted), reverse=True)

    perPage = 20
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/maps/duplicates/%s/" % maphash)

    comments = misc.count_comments_for_many(mapObject, 'maps')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_duplicates.html',
        'request': request,
        'title': ' - Duplicates of ' + mapObject[0].title,
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
        'maphash': maphash,
        'comments': comments,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def randomMap(request):
    mapObject = Maps.objects.filter(next_rev=0).distinct('map_hash')
    mapObject = random.choice(mapObject)
    return HttpResponseRedirect('/maps/'+str(mapObject.id)+'/')


def mostCommentedMap(request):
    mapObject = Maps.objects.filter(next_rev=0)
    comments = misc.count_comments_for_many(mapObject, 'maps')
    mapid = max(comments.items(), key=operator.itemgetter(1))[0]
    return HttpResponseRedirect('/maps/'+mapid+'/')


def displayMap(request, arg):
    if request.method == 'POST':
        if request.POST.get('reportReason', "").strip() != "":
            checkReports = Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name='maps')
            if not checkReports:
                checkReports = Reports.objects.filter(ex_id=arg, ex_name='maps')
                infringement = request.POST.get('infringement', False)
                if infringement == "true":
                    infringement = True
                transac = Reports(
                    user_id=request.user.id,
                    reason=request.POST['reportReason'].strip(),
                    ex_id=arg,
                    ex_name='maps',
                    infringement=infringement,
                    posted=timezone.now(),
                )
                transac.save()
                Maps.objects.filter(id=arg).update(amount_reports=F('amount_reports')+1)
                misc.send_email_to_admin_OnReport({'addr': request.META['HTTP_HOST']+'/maps/'+arg, 'user_id': request.user.id, 'reason': request.POST['reportReason'].strip(), 'infringement': infringement})
                misc.send_email_to_user_OnReport({'addr': request.META['HTTP_HOST']+'/maps/'+arg, 'owner_id': Maps.objects.get(id=arg).user_id, 'reason': request.POST['reportReason'].strip(), 'resource_type': 'map'})
                return HttpResponseRedirect('/maps/'+arg)
        elif request.POST.get('mapInfo', False) is not False:
            if request.user.is_superuser:
                Maps.objects.filter(id=arg).update(info=request.POST['mapInfo'].strip())
            else:
                Maps.objects.filter(id=arg, user_id=request.user.id).update(info=request.POST['mapInfo'].strip())
            return HttpResponseRedirect('/maps/'+arg)
        elif request.FILES.get('screenshot', False) is not False:

                handlers.addScreenshot(request, arg, 'map')

        elif request.POST.get('comment', "") != "":
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

    contains_shp = False
    disk_size = 0
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
    try:
        mapDir = os.listdir(path)
        for filename in mapDir:
            if filename.endswith(".oramap"):
                disk_size = os.path.getsize(os.path.join(path, filename))
                disk_size = misc.sizeof_fmt(disk_size)
                break
        mapDir = os.listdir(os.path.join(path, 'content'))
        for filename in mapDir:
            if filename.endswith(".shp"):
                contains_shp = True
                break
    except FileNotFoundError as ex:
        print(ex)
        return HttpResponseRedirect('/')
    try:
        mapObject = Maps.objects.get(id=arg)
    except:
        return HttpResponseRedirect('/')

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
        except:
            pass
        if item.user_id == request.user.id:
            reportedByUser = True

    luaNames = []

    listContent = os.listdir(os.path.join(path, 'content'))

    for fn in listContent:
        if fn.endswith('.lua'):
            luaNames.append(os.path.splitext(fn)[0])

    shpNames = []
    for fn in listContent:
        if fn.endswith('.shp.gif'):
            shpNames.append(fn.split('.shp.gif')[0])

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
    except:
        played_counter = 'unknown'

    ratesAmount = Rating.objects.filter(ex_id=mapObject.id, ex_name='map')
    ratesAmount = len(ratesAmount)

    comments = misc.get_comments_for_all_revisions(request, 'maps', arg)

    # showing upgrade map button
    show_upgrade_map_button = True

    if not (request.user == mapObject.user or request.user.is_superuser):
        show_upgrade_map_button = False

    if 'git' in mapObject.parser:
        show_upgrade_map_button = False  # can't upgrade maps uploaded with bleed parser
    if mapObject.next_rev != 0:
        show_upgrade_map_button = False  # upgrade only the latest revision

    if mapObject.parser == list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]:
        show_upgrade_map_button = False  # map is up-to-date
    ###

    map_preview = None
    for sc_item in screenshots:
        if sc_item.map_preview:
            map_preview = sc_item

    last_parser = list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]

    license, icons = misc.selectLicenceInfo(mapObject)
    userObject = User.objects.get(pk=mapObject.user_id)
    Maps.objects.filter(id=mapObject.id).update(viewed=mapObject.viewed+1)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'displayMap.html',
        'request': request,
        'title': ' - Map details - ' + mapObject.title,
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
        'shpNames': shpNames,
        'disk_size': disk_size,
        'duplicates': duplicates,
        'played_counter': played_counter,
        'ratesAmount': ratesAmount,
        'REPORTS_PENALTY_AMOUNT': settings.REPORTS_PENALTY_AMOUNT,
        'lints': lints,
        'comments': comments,
        'show_upgrade_map_button': show_upgrade_map_button,
        'map_preview': map_preview,
        'contains_shp': contains_shp,
        'last_parser': last_parser,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def upgradeMap(request, arg):

    mapObject = Maps.objects.filter(id=arg)
    if not mapObject:
        return HttpResponseRedirect('/')
    if not mapObject[0]:
        return HttpResponseRedirect('/')
    if mapObject[0].user != request.user:
        if not request.user.is_superuser:
            return HttpResponseRedirect('/maps/' + arg + '/')

    if 'git' in mapObject[0].parser:
        return HttpResponseRedirect('/maps/' + arg + '/')  # can't upgrade maps uploaded with bleed parser

    if mapObject[0].next_rev != 0:
        return HttpResponseRedirect('/maps/' + arg + '/')  # upgrade only the latest revision

    parsers = list(reversed(list(settings.OPENRA_VERSIONS.values())))
    if 'bleed' in parsers:
        parsers.remove('bleed')

    if mapObject[0].parser == parsers[0]:
        return HttpResponseRedirect('/maps/' + arg + '/')  # map is up-to-date

    ##########
    no_effect = False
    failed_to_upgrade = False
    if request.method == 'POST':
        upgrade_to_parser = request.POST.get('upgrade_to_parser', None)

        if upgrade_to_parser:

            if int(mapObject[0].parser.split('-')[1]) >= int(upgrade_to_parser.split('-')[1]):
                no_effect = True
            else:

                upgrade_with_creating_new_rev = True
                upgrade_if_hash_matches = True
                upgrade_if_lint_fails = True
                upgrade_res = utility.map_upgrade(mapObject, mapObject[0].parser.split('-')[1], upgrade_to_parser, upgrade_with_creating_new_rev, upgrade_if_hash_matches, upgrade_if_lint_fails)
                if upgrade_res:
                    return HttpResponseRedirect('/maps/%s/' % upgrade_res[0])
                else:
                    failed_to_upgrade = True
    ##########

    template = loader.get_template('index.html')
    template_args = {
        'content': 'upgradeMap.html',
        'request': request,
        'title': ' - Upgrade Map - ' + mapObject[0].title,
        'map': mapObject[0],
        'parsers': parsers,
        'no_effect': no_effect,
        'failed_to_upgrade': failed_to_upgrade,
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
            except:
                pass
            scObject[0].delete()
            return HttpResponseRedirect("/"+name+"/"+arg+"/")
    return HttpResponseRedirect("/")


def deleteComment(request, arg, item_type, item_id):
    comObject = Comments.objects.filter(id=arg)
    if comObject:
        if comObject[0].user == request.user or request.user.is_superuser:
            Comments.objects.filter(id=arg).update(is_removed=True)

            coms_exist_for_map_for_user = Comments.objects.filter(id=arg, is_removed=False, user=request.user.id)
            if not coms_exist_for_map_for_user:
                UnsubscribeComments.objects.filter(item_type=item_type, item_id=item_id, user=request.user.id).delete()

    return HttpResponseRedirect("/"+item_type+"/"+item_id+"/")


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
    except:
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
    response = StreamingHttpResponse(open(image, 'rb'), content_type='image/'+mime)
    response['Content-Disposition'] = 'attachment; filename = %s' % fn
    return response


def serveMinimap(request, arg):
    minimap = ""
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
    try:
        contentDir = os.listdir(os.path.join(path, 'content'))
    except:
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
    except:
        return HttpResponseRedirect("/")
    for filename in mapDir:
        if filename.endswith(".oramap"):
            oramap = filename
            break
    if oramap == "":
        return HttpResponseRedirect('/maps/'+arg)
    else:
        serveOramap = os.path.join(path, oramap)
        if sync == "sync":
                oramap = arg + ".oramap"
        response = StreamingHttpResponse(open(serveOramap, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename = %s' % oramap
        response['Content-Length'] = os.path.getsize(serveOramap)
        Maps.objects.filter(id=arg).update(downloaded=F('downloaded')+1)
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


def serveMapSHP(request, arg, name, request_type='preview'):
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg, 'content')
    fname = ""
    try:
        listdir = os.listdir(path)
    except:
        raise Http404
    for fn in listdir:
        if request_type == 'preview':
            if fn.endswith('.shp.gif'):
                if fn.split('.shp.gif')[0] == name:
                    fname = fn
                    break
        elif request_type == 'fetch':
            if fn.endswith('.shp'):
                if fn.split('.shp')[0] == name:
                    fname = fn
                    break
    if fname == "":
        raise Http404
    response = StreamingHttpResponse(open(os.path.join(path, fname), 'rb'), content_type='image/gif')
    response['Content-Disposition'] = 'attachment; filename = %s' % fname
    return response


def uploadMap(request, previous_rev=0):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/maps/')
    error_response = False
    uid = False
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
    if request.method == 'POST':
        if request.FILES.get('file', None) is not None:
            uploadingMap = handlers.MapHandlers()
            error_response = uploadingMap.ProcessUploading(user_id, request.FILES['file'], request.POST, rev, previous_rev)
            if uploadingMap.UID:
                uid = str(uploadingMap.UID)
                if error_response is False:
                    return HttpResponseRedirect('/maps/' + uid + "/")

    parsers = list(reversed(list(settings.OPENRA_VERSIONS.values())))

    bleed_tag = None
    if (settings.OPENRA_BLEED_HASH_FILE_PATH != '' and os.path.isfile(settings.OPENRA_BLEED_HASH_FILE_PATH)):
        bleed_tag = open(settings.OPENRA_BLEED_HASH_FILE_PATH, 'r')
        bleed_tag = 'git-' + bleed_tag.readline().strip()[0:7]
    if 'bleed' in parsers:
        if not os.path.isfile(os.path.join(settings.OPENRA_BLEED_PARSER, 'OpenRA.Utility.exe')):
            parsers.remove('bleed')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'uploadMap.html',
        'request': request,
        'title': ' - Uploading Map',
        'uid': uid,
        'previous_rev': previous_rev,
        'previous_rev_title': previous_rev_title,
        'rev': rev,
        'parsers': parsers,
        'bleed_tag': bleed_tag,
        'error_response': error_response,
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
    except:
        return HttpResponseRedirect('/maps/')
    mapTitle = mapObject.title
    mapAuthor = mapObject.author
    if mapObject.user_id == request.user.id or request.user.is_superuser:
        path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', arg)
        try:
            shutil.rmtree(path)
        except:
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
        return HttpResponseRedirect('/maps/'+arg)
    try:
        mapObject = Maps.objects.get(id=arg)
    except:
        return HttpResponseRedirect('/maps/')
    if mapObject.user_id == request.user.id or request.user.is_superuser:
        if mapObject.downloading:
            Maps.objects.filter(id=arg).update(downloading=False)
        else:
            Maps.objects.filter(id=arg).update(downloading=True)
    return HttpResponseRedirect('/maps/'+arg)


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
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    try:
        tempObj = Maps.objects.get(id=arg)
    except:
        return HttpResponseRedirect('/')

    revs = misc.Revisions('maps')
    revisions = revs.GetRevisions(arg)
    mapObject = Maps.objects.filter(id__in=revisions).order_by('-revision', '-posted')
    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/maps/%s/revisions/" % arg)

    comments = misc.count_comments_for_many(mapObject, 'maps')

    template = loader.get_template('index.html')
    template_args = {
        'content': 'maps_revisions.html',
        'request': request,
        'title': ' - Revisions',
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
        'arg': arg,
        'comments': comments,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def cancelReport(request, name, arg):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name=name).delete()
    Maps.objects.filter(id=arg).update(amount_reports=F('amount_reports')-1) 
    return HttpResponseRedirect('/'+name+'/'+arg)


def screenshots(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': 'screenshots.html',
        'request': request,
        'title': ' - Screenshots',
    }
    return StreamingHttpResponse(template.render(template_args, request))


def comments(request, page=1):
    perPage = 20
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    comments = Comments.objects.filter(is_removed=False).order_by('-posted')
    amount = len(comments)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    comments = comments[slice_start:slice_end]
    amount_this_page = len(comments)

    if amount_this_page == 0 and int(page) != 1:
        return HttpResponseRedirect("/comments/")

    last_comment_id_seen = request.COOKIES.get('last_comment_id_seen', comments[0].id)

    template = loader.get_template('index.html')
    template_args = {
        'content': 'comments.html',
        'request': request,
        'title': ' - Comments',
        'comments': comments,
        'amount': amount,
        'amount_this_page': amount_this_page,
        'range': [i+1 for i in range(rowsRange)],
        'page': int(page),
        'last_comment_id_seen': int(last_comment_id_seen),
    }
    response = StreamingHttpResponse(template.render(template_args, request))
    if int(page) == 1:
        response.set_cookie('last_comment_id_seen', comments[0].id, max_age=4320000)
    return response


def comments_by_user(request, arg, page=1):
    perPage = 20
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)

    comments = Comments.objects.filter(is_removed=False, user=arg).order_by('-posted')
    amount = len(comments)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    comments = comments[slice_start:slice_end]
    amount_this_page = len(comments)

    if amount_this_page == 0 and int(page) != 1:
        return HttpResponseRedirect("/comments/user/"+arg+"/")

    template = loader.get_template('index.html')
    template_args = {
        'content': 'comments.html',
        'request': request,
        'title': ' - Comments by ' + request.user.username,
        'comments': comments,
        'amount': amount,
        'amount_this_page': amount_this_page,
        'range': [i+1 for i in range(rowsRange)],
        'page': int(page),
        'comments_by_user': User.objects.filter(id=arg).first(),
    }
    return StreamingHttpResponse(template.render(template_args, request))


def handle404(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': '404.html',
        'request': request,
        'title': ' - Page not found',
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
        'title': ' - Profile',
        'amountMaps': amountMaps,
        'ifsocial': ifsocial,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def faq(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': 'faq.html',
        'request': request,
        'title': ' - FAQ',
    }
    return StreamingHttpResponse(template.render(template_args, request))


def links(request):
    template = loader.get_template('index.html')
    template_args = {
        'content': 'links.html',
        'request': request,
        'title': ' - Links',
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
        'title': ' - Contacts',
        'message_sent': message_sent,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def contacts_sent(request):
    message_sent = True
    template = loader.get_template('index.html')
    template_args = {
        'content': 'contacts.html',
        'request': request,
        'title': ' - Contacts',
        'message_sent': message_sent,
    }
    return StreamingHttpResponse(template.render(template_args, request))


def robots(request):
    template = loader.get_template('service/robots.txt')
    template_args = {
        'request': request,
    }
    return StreamingHttpResponse(template.render(template_args, request), content_type='text/plain')
