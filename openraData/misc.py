import os
import shutil
import datetime
import time
from django.core import mail
from django.conf import settings
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from openraData.models import Maps, Units, Mods, Screenshots, Reports, Comments, UnsubscribeComments

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

def addSlash(path):
	if not path.endswith('/'):
		path += '/'
	return path

def send_email_contacts_form(name, email, message):
	connection = mail.get_connection()
	connection.open()

	email = mail.EmailMessage('OpenRA Resource Center - Contacts form', 'Name: %s\nEmail: %s\nMessage: %s\n' % (name, email, message), settings.ADMIN_EMAIL_FROM,
						  [settings.ADMIN_EMAIL_TO], connection=connection)

	email.send()
	connection.close()

def send_email_to_admin_OnMapFail(tempname):
	connection = mail.get_connection()
	connection.open()
	email = mail.EmailMessage('OpenRA Resource Center - Failed to upload map', 'See attachment', settings.ADMIN_EMAIL_FROM,
						  [settings.ADMIN_EMAIL_TO], connection=connection)
	email.attach_file(tempname)
	email.send()
	connection.close()

def send_email_to_admin_OnReport(args):
	connection = mail.get_connection()
	connection.open()
	body = "Item: http://%s  \nBy user_id: %s  \nReason: %s  \nInfringement: %s" % (args['addr'], args['user_id'], args['reason'], args['infringement'])
	email = mail.EmailMessage('OpenRA Resource Center(to admin) - New Report', body, settings.ADMIN_EMAIL_FROM,
						  [settings.ADMIN_EMAIL_TO], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnReport(args):
	mail_addr = return_email(args['owner_id'])
	if mail_addr == "":
		return False
	connection = mail.get_connection()
	connection.open()
	body = "Your %s has been reported: %s \nReason: %s" % (args['resource_type'], args['addr'], args['reason'])
	email = mail.EmailMessage('OpenRA Resource Center - Your content has been reported', body, settings.ADMIN_EMAIL_FROM,
						  [mail_addr], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnLint(email_addr, body):
	connection = mail.get_connection()
	connection.open()
	email = mail.EmailMessage('OpenRA Resource Center - Lint failed', body, settings.ADMIN_EMAIL_FROM,
						  [email_addr], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnComment(item_type, item_id, email_addr, info=""):
	if not email_addr:
		return False
	http_host = 'http://' + settings.HTTP_HOST
	connection = mail.get_connection()
	connection.open()
	if not info:
		body = "New comment on " + item_type.title()[:-1]+" you've commented: " + http_host + "/maps/" + item_id + "/#comments"
	elif info == "owner":
		body = "Your "+item_type.title()[:-1]+" has been commented: " + http_host + "/maps/" + item_id + "/#comments"
	email = mail.EmailMessage('OpenRA Resource Center - New Comment', body, settings.ADMIN_EMAIL_FROM,
						  [email_addr], connection=connection)
	email.send()
	connection.close()

def send_email_to_admin(title, body):
	connection = mail.get_connection()
	connection.open()
	email = mail.EmailMessage(title, body, settings.ADMIN_EMAIL_FROM, [settings.ADMIN_EMAIL_TO], connection=connection)
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
	for x in ['bytes','KB','MB','GB','TB']:
		if disk_size < 1024.0:
			return "%3.1f %s" % (disk_size, x)
		disk_size /= 1024.0

def count_comments_for_many(mapObject, item_type):
	comments = {}
	for item in mapObject:
		comments[str(item.id)] = 0
		revs = Revisions(item_type)
		revisions = revs.GetRevisions(item.id)
		for rev in revisions:
			comments[str(item.id)] += len(Comments.objects.filter(item_type=item_type.lower(), item_id=rev, is_removed=False))
	return comments

def get_map_id_of_revision(item, seek_rev):
	revs = Revisions('maps')
	revisions = revs.GetRevisions(item.id)
	for rev in revisions:
		mapObj = Maps.objects.get(id=rev)
		if mapObj.revision == seek_rev:
			return mapObj.id
	return 0

def get_map_title_of_revision(item, seek_rev):
	revs = Revisions('maps')
	revisions = revs.GetRevisions(item.id)
	for rev in revisions:
		mapObj = Maps.objects.get(id=rev)
		if mapObj.revision == seek_rev:
			return mapObj.title
	return ""

def get_comments_for_all_revisions(request, item_type, item_id):
	comments = []

	revs = Revisions(item_type)
	revisions = revs.GetRevisions(item_id)
	for rev in revisions:

		current_user_commented = False
		current_rev = Maps.objects.get(id=rev)
		commentsObj = Comments.objects.filter(item_type=item_type, item_id=rev, is_removed=False).order_by('posted')

		for com in commentsObj:
			if com.user == request.user:
				current_user_commented = True
		
		unsubscribed = False
		if request.user:
			unsubObj = UnsubscribeComments.objects.filter(item_type=item_type, item_id=rev, user=request.user)
			if unsubObj:
				unsubscribed = True

		comments.append([current_rev, commentsObj, current_user_commented, unsubscribed])
	return list(reversed(comments))

########## Revisions
class Revisions():

	def __init__(self, modelName):
		self.revisions = []
		self.modelName = modelName

	def GetRevisions(self, itemid, seek_next=False):
		if seek_next:
			if self.modelName.lower() == "maps":
				itemObject = Maps.objects.get(id=itemid)
			elif self.modelName.lower() == "units":
				itemObject = Units.objects.get(id=itemid)
			elif self.modelName.lower() == "mods":
				itemObject = Mods.objects.get(id=itemid)
			if itemObject.next_rev == 0:
				return
			self.revisions.append(itemObject.next_rev)
			self.GetRevisions(itemObject.next_rev, True)
			return
		self.revisions.insert(0, itemid)
		if self.modelName.lower() == "maps":
			itemObject = Maps.objects.get(id=itemid)
		elif self.modelName.lower() == "units":
			itemObject = Units.objects.get(id=itemid)
		elif self.modelName.lower() == "mods":
			itemObject = Mods.objects.get(id=itemid)
		if itemObject.pre_rev == 0:
			self.GetRevisions(self.revisions[-1], True)
			return self.revisions
		self.GetRevisions(itemObject.pre_rev)
		return self.revisions

	def GetLatestRevisionID(self, itemid):
		if self.modelName.lower() == "maps":
			itemObject = Maps.objects.get(id=itemid)
		elif self.modelName.lower() == "units":
			itemObject = Units.objects.get(id=itemid)
		elif self.modelName.lower() == "mods":
			itemObject = Mods.objects.get(id=itemid)
		if itemObject.next_rev == 0:
			return itemObject.id
		return self.GetLatestRevisionID(itemObject.next_rev)

def Log(data, channel="default"):
	if not os.path.isdir(os.getcwd() + "/logs/"):
		os.makedirs(os.getcwd() + "/logs/")
	logfile = open(os.getcwd() + "/logs/" + channel + ".log", "a")
	if data:
		today = datetime.datetime.today()
		timestamp = today.strftime('%Y/%m/%d %H:%M:%S') + ' [' + time.tzname[0] + ']:  '

		logfile.write(timestamp + data.strip() + "\n")
	logfile.close()
	return True

def copytree(src, dst, symlinks=False, ignore=None):
	if not os.path.exists(dst):
		os.makedirs(dst)
	for item in os.listdir(src):
		s = os.path.join(src, item)
		d = os.path.join(dst, item)
		if os.path.isdir(s):
			copytree(s, d, symlinks, ignore)
		else:
			if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
				shutil.copy2(s, d)
