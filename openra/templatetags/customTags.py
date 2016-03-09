import re
from HTMLParser import HTMLParser
from django import template
from openra import misc
from openra.models import Maps, ReplayPlayers


register = template.Library()

def convert_links(value):
	value = re.sub(r'(?P<urlmatch>https?:\/\/[^ <\n\r]*)', '<a href="\g<urlmatch>" target=_blank>\g<urlmatch></a>', value)
	return value
register.filter('convert_links', convert_links)

class MLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)

def strip_tags(value):
	s = MLStripper()
	s.feed(value)
	return s.get_data().replace("''","'")
register.filter('strip_tags', strip_tags)

def proper_space(value):
	return value.replace(" ", "%20")
register.filter('proper_space', proper_space)

def amount_comments(value, arg):
	return str(value[str(arg)])
register.filter('amount_comments', amount_comments)

def account_link(value, arg):
	account = misc.get_account_link(arg)
	if account != "":
		return "<a href='"+account+"' target='_blank'>"+value+"</a>"
	else:
		return value
register.filter('account_link', account_link)

def map_real_size(value):
	return "x".join(value.split(',')[2:])
register.filter('map_real_size', map_real_size)

def nl_to_br(value):
	return value.replace('\\n', '<br />')
register.filter('nl_to_br', nl_to_br)


def map_exists_by_hash(value):
	item = Maps.objects.filter(map_hash=value)
	if item:
		return True
	else:
		return False
register.filter('map_exists_by_hash', map_exists_by_hash)

def map_url_by_hash(value):
	item = Maps.objects.filter(map_hash=value)
	if item:
		return "/maps/" + str(item[0].id) + "/"
	else:
		return "#"
register.filter('map_url_by_hash', map_url_by_hash)

def map_minimap_by_hash(value):
	item = Maps.objects.filter(map_hash=value)
	if item:
		return "/maps/" + str(item[0].id) + "/minimap"
	else:
		return "#"
register.filter('map_minimap_by_hash', map_minimap_by_hash)

def map_title_by_hash(value):
	item = Maps.objects.filter(map_hash=value)
	if item:
		return str(item[0].title)
	else:
		return ""
register.filter('map_title_by_hash', map_title_by_hash)


def get_replay_players(value):
	replay_players = ReplayPlayers.objects.filter(replay_id=value)
	if replay_players:
		return replay_players
	return []
register.filter('get_replay_players', get_replay_players)

def map_id_of_rev(value, arg):
	seek_id_by_rev = misc.get_map_id_of_revision(arg, value)
	if seek_id_by_rev != 0:
		return "/maps/" + str(seek_id_by_rev) + "/"
	return "#"
register.filter('map_id_of_rev', map_id_of_rev)

def map_title_of_rev(value, arg):
	seek_title_by_rev = misc.get_map_title_of_revision(arg, value)
	return seek_title_by_rev
register.filter('map_title_of_rev', map_title_of_rev)

def item_name_by_type_id(value, arg):
	if arg == "maps":
		seek = Maps.objects.filter(id=value)
		if seek:
			return seek[0].title
	elif arg == "replays":
		seek = Replays.objects.filter(id=value)
		if seek:
			return seek[0].game_mod.upper() + ' by ' + seek[0].user.username + ' on ' + seek[0].posted
	return ""
register.filter('item_name_by_type_id', item_name_by_type_id)