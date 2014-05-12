import re
from HTMLParser import HTMLParser
from django import template

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
	return s.get_data()
register.filter('strip_tags', strip_tags)

def proper_space(value):
	return value.replace(" ", "%20")
register.filter('proper_space', proper_space)

def amount_comments(value, arg):
	return str(value[str(arg)])
register.filter('amount_comments', amount_comments)