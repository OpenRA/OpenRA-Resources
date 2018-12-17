import base64
import tempfile
import shutil
import os
import zipfile
from subprocess import Popen, PIPE

from django.conf import settings
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.contrib.auth.models import User
from openra.models import Maps, Lints, Screenshots
from openra import utility, misc

# pylint: disable=too-many-arguments
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-return-statements
# pylint: disable=too-many-locals
# pylint: disable=broad-except

class InvalidMapException(Exception):
    """Failed to parse or process an OpenRA map file"""
    def __init__(self, message):
        super().__init__()
        self.message = message


def add_map_revision(oramap_path, user,
                     parser, game_mod,
                     info, policy_options, posted_date,
                     revision=1, previous_revision_id=0):
    """ Parse and save a given oramap into the database.
        The input file is not modified, and must be cleaned up afterwards by the caller.
        Returns a Maps model or raises an InvalidMapException on error
    """
    print('Running --map-hash')
    hash_retcode, map_hash = utility.run_utility_command(parser, game_mod, [
        '--map-hash', oramap_path])

    if hash_retcode != 0 or not map_hash:
        raise InvalidMapException('Hash calculation failed')

    # Check if user has already uploaded the same map
    # TODO: Why do we prevent this for the same user, but not others?
    if Maps.objects.filter(user_id=user.id, map_hash=map_hash).exists():
        raise InvalidMapException("You've already uploaded this map.")

    # Parse metadata
    print('Parsing map.yaml metadata')
    metadata = utility.parse_map_metadata(oramap_path)
    if not metadata:
        misc.send_email_to_admin_OnMapFail(oramap_path)
        raise InvalidMapException('Unable to parse map metadata.')

    if int(metadata['mapformat']) < 10:
        raise InvalidMapException('Unable to import maps older than map format 10.')

    # Only attempt to parse rules for the default mods
    # This will be fixed properly once we move to mod-based parsing
    is_known_mod = metadata['game_mod'] in ['ra', 'cnc', 'd2k', 'ts']

    if is_known_mod:
        rules_retcode, custom_rules = utility.run_utility_command(parser, metadata['game_mod'], [
            '--map-rules', oramap_path])

        if rules_retcode != 0:
            misc.send_email_to_admin_OnMapFail(oramap_path)
            raise InvalidMapException('Failed to parse custom rules.')

        # TODO: Check against the game's Ruleset.DefinesUnsafeCustomRules code instead of line count
        advanced = len(custom_rules.split("\n")) > 8
        base64_rules = base64.b64encode(custom_rules.encode()).decode()
    else:
        base64_rules = ''
        advanced = False

    expect_metadata_keys = [
        'title', 'author', 'categories', 'players', 'game_mod',
        'width', 'height', 'bounds', 'mapformat', 'spawnpoints',
        'tileset', 'base64_players', 'lua'
    ]

    keyargs = {}
    for key in expect_metadata_keys:
        if key not in metadata:
            raise InvalidMapException('Map metadata missing required key: ' + key + '.')
        keyargs[key] = metadata[key]

    # Add record to Database
    item = Maps(
        map_hash=map_hash,
        revision=revision,
        pre_rev=previous_revision_id,
        next_rev=0,
        posted=posted_date,
        viewed=0,
        base64_rules=base64_rules,
        parser=parser,
        user=user,
        info=info,
        downloading=True,
        requires_upgrade=not is_known_mod,
        advanced_map=advanced,
        policy_cc=policy_options['cc'],
        policy_commercial=policy_options['commercial'],
        policy_adaptations=policy_options['adaptations'],
        description='', # Obsolete field
        map_type='', # Obsolete field
        shellmap=False, # Obsolete field
        legacy_map=False, # Obsolete field
        **keyargs
    )
    item.save()

    # Copy the updated map to its new data location
    item_path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
    item_content_path = os.path.join(item_path, 'content')
    if not os.path.exists(item_content_path):
        os.makedirs(item_content_path)

    item_map_path = os.path.join(item_path, os.path.basename(oramap_path))
    shutil.copy(oramap_path, item_map_path)

    if previous_revision_id:
        previous_item = Maps.objects.get(id=previous_revision_id)
        previous_item.next_rev = item.id
        previous_item.save()

    # Extract the oramap contents
    # TODO: Why do we need this?
    with zipfile.ZipFile(item_map_path, mode='a') as oramap:
        try:
            oramap.extractall(item_content_path)
        except Exception:
            pass

    if is_known_mod:
        print('Running --check-yaml')
        lint_retcode, lint_output = utility.run_utility_command(parser, item.game_mod, [
            '--check-yaml',
            item_map_path
        ])

        if lint_output:
            Lints(
                item_type='maps',
                map_id=item.id,
                version_tag=parser,
                pass_status=lint_retcode == 0,
                lint_output=lint_output,
                posted=timezone.now(),
            ).save()

        if lint_retcode == 0:
            item.requires_upgrade = False
            item.save()

    print("--- New revision: %s" % item.id)
    return item


def process_upload(user_id, file, post, revision=1, previous_revision=0):
    """Upload a new revision of a map
       Returns the updated map revision or raises an InvalidMapException on error
    """
    parser = settings.OPENRA_VERSIONS[0]
    if post.get("parser", None) is not None:
        if post['parser'] not in settings.OPENRA_VERSIONS:
            raise InvalidMapException('Invalid parser.')
        parser = post['parser']

    user = User.objects.get(pk=user_id)

    # Check whether we can upload a new revision
    # and propagate the license info
    policy = {
        'cc': False,
        'commercial': False,
        'adaptations': ''
    }

    if previous_revision:
        query = Maps.objects.filter(id=previous_revision, user_id=user.id)
        if not query:
            raise InvalidMapException('Map is owned by another user.')

        previous_item = query[0]
        if previous_item.next_rev != 0:
            raise InvalidMapException('Map already has a later revision.')

        policy['cc'] = previous_item.policy_cc
        policy['commercial'] = previous_item.policy_commercial
        policy['adaptations'] = previous_item.policy_adaptations
    else:
        if post['policy_cc'] == 'cc_yes':
            policy['cc'] = True
            if post['commercial'] == "com_yes":
                policy['commercial'] = True
            if post['adaptations'] == "adapt_yes":
                policy['adaptations'] = "yes"
            elif post['adaptations'] == "adapt_no":
                policy['adaptations'] = "no"
            else:
                policy['adaptations'] = "yes and shared alike"

    # Create a temporary working directory and copy the oramap to it
    # Directory is automatically deleted when exiting the context manager
    with tempfile.TemporaryDirectory() as working_path:
        print('Temporary working directory: {}'.format(working_path))

        # Django's get_valid_filename makes the name safe
        upload_path = os.path.join(working_path, get_valid_filename(file.name))
        upload_ext = os.path.splitext(upload_path)[1].lower()
        with open(upload_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        mime_retcode, mime_type = utility.detect_mimetype(upload_path)
        if mime_retcode != 0 or not (
                (mime_type == 'application/zip' and upload_ext == '.oramap') or
                (mime_type == 'text/plain' and upload_ext in ['.mpr', '.ini'])):
            raise InvalidMapException('Unsupported file type: ' + mime_type)

        # TODO: Support importing from cnc/d2k/ts.
        # Note that cnc maps contain *two* files which must both be present
        if mime_type == 'text/plain':
            import_path = os.path.splitext(upload_path)[0] + '.oramap'

            # Ignore command output and retcode, we know it worked if an oramap is saved
            utility.run_utility_command(parser, 'ra', [
                '--import-ra-map', upload_path], cwd=working_path)

            if os.path.exists(import_path):
                upload_path = import_path
            else:
                misc.send_email_to_admin_OnMapFail(upload_path)
                raise InvalidMapException('Failed to import legacy map.')

        # TODO: Replace hardcoded RA with the parser mod when that rewrite happens
        return add_map_revision(upload_path, user, parser, 'ra',
                                post['info'].strip(), policy, timezone.now(),
                                revision, previous_revision)


def process_update(item, parser=settings.OPENRA_VERSIONS[0]):
    """Create a new revision of a map by running the OpenRA.Utility
       update command using a given parser version

       Returns the updated map revision or raises an InvalidMapException on error
    """
    print('Starting map update action on map {}. Using parser: {}'.format(item.id, parser))
    if item.next_rev != 0:
        raise InvalidMapException('A newer revision of this map already exists')

    # Find the oramap file in the data directory
    source_path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
    oramap_filename = misc.first_oramap_in_directory(source_path)
    if not oramap_filename:
        raise InvalidMapException('Map directory does not contain an .oramap package')

    # Create a temporary working directory and copy the oramap to it
    # Directory is automatically deleted when exiting the context manager
    with tempfile.TemporaryDirectory() as working_path:
        print('Temporary working directory: {}'.format(working_path))
        oramap_path = os.path.join(working_path, oramap_filename)
        shutil.copy(os.path.join(source_path, oramap_filename), oramap_path)

        # Run OpenRA.Utility to do the actual update
        print('Running --update-map')
        update_retcode, update_output = utility.run_utility_command(parser, item.game_mod, [
            '--update-map',
            oramap_path,
            item.parser,
            '--apply'
        ])

        # Error code if the command crashed, usage line on invalid arguments
        if update_retcode != 0 or update_output.startswith('--update-map MAP SOURCE'):
            raise InvalidMapException('OpenRA.Utility --update-map returned an error')

        if not update_output:
            raise InvalidMapException('OpenRA.Utility --update-map returned no output')

        if update_output.startswith('No such command'):
            raise InvalidMapException('OpenRA.Utility --update-map command missing')

        policy = {
            'cc': item.policy_cc,
            'commercial': item.policy_commercial,
            'adaptations': item.policy_adaptations
        }

        return add_map_revision(oramap_path, item.user,
                                parser, item.game_mod,
                                item.info, policy,
                                item.posted, # preserve original date to avoid reordering map list
                                item.revision + 1, item.id)


def addScreenshot(request, arg, item):
    if item == 'map':
        Object = Maps.objects.filter(id=arg)
        if not Object:
            return False
        if not (Object[0].user_id == request.user.id or request.user.is_superuser):
            return False
    else:
        return False
    tempname = '/tmp/screenshot.temp'
    with open(tempname, 'wb+') as destination:
        for chunk in request.FILES['screenshot'].chunks():
            destination.write(chunk)

    command = 'file -b --mime-type %s' % tempname
    proc = Popen(command.split(), stdout=PIPE).communicate()
    mimetype = proc[0].decode().strip()
    if mimetype not in ['image/jpeg', 'image/png', 'image/gif']:
        return False

    map_preview = False
    preview = request.POST.get('map_preview', None)
    if preview == 'on':
        map_preview = True

    transac = Screenshots(
        user=Object[0].user,
        ex_id=int(arg),
        ex_name=item+"s",
        posted=timezone.now(),
        map_preview=map_preview,
        )
    transac.save()

    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data',
                        'screenshots', str(transac.id))
    if not os.path.exists(path):
        os.makedirs(path)

    sc_full_name = os.path.join(path, arg + "." + mimetype.split('/')[1])
    sc_mini_name = os.path.join(path, arg + "-mini." + mimetype.split('/')[1])

    shutil.move(tempname, sc_full_name)

    command = 'convert -resize 250x -quality 100 -sharpen 1.0 %s %s' % (sc_full_name, sc_mini_name)
    proc = Popen(command.split(), stdout=PIPE).communicate()
