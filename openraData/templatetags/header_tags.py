from django import template
from openraData.models import Comments

register = template.Library()

def new_comments(value, arg):
	if value:
		seek = Comments.objects.filter(id__gt=int(value)).exclude(user=arg)
		if len(seek) != 0:
			return "+" + str(len(seek)) + " "
	return ""
register.filter('new_comments', new_comments)