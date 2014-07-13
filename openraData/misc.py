from django.core import mail
from django.conf import settings
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from threadedcomments.models import ThreadedComment
from openraData.models import Maps, Units, Mods, Screenshots, Reports

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

def send_email_to_admin_OnMapFail(tempname):
	connection = mail.get_connection()
	connection.open()
	email = mail.EmailMessage('OpenRA Resource Center - Failed to upload map', 'See attachment', settings.ADMIN_EMAIL,
						  [settings.ADMIN_EMAIL], connection=connection)
	email.attach_file(tempname)
	email.send()
	connection.close()

def send_email_to_admin_OnReport(args):
	connection = mail.get_connection()
	connection.open()
	body = "Item: http://%s  \nBy user_id: %s  \nReason: %s  \nInfringement: %s" % (args['addr'], args['user_id'], args['reason'], args['infringement'])
	email = mail.EmailMessage('OpenRA Resource Center(to admin) - New Report', body, settings.ADMIN_EMAIL,
						  [settings.ADMIN_EMAIL], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnReport(args):
	mail_addr = return_email(args['owner_id'])
	if mail_addr == "":
		return False
	connection = mail.get_connection()
	connection.open()
	body = "Your %s has been reported: %s \nReason: %s" % (args['resource_type'], args['addr'], args['reason'])
	email = mail.EmailMessage('OpenRA Resource Center - Your content has been reported', body, mail_addr,
						  [mail_addr], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnLint(email_addr, body):
	connection = mail.get_connection()
	connection.open()
	email = mail.EmailMessage('OpenRA Resource Center - Lint failed', body, email_addr,
						  [email_addr], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnComment(itemtype, itemid, email_addr, info=""):
	http_host = 'http://resource.openra.net'
	connection = mail.get_connection()
	connection.open()
	if not info:
		body = itemtype.title()+" you've commented, has some activity : " + http_host + "/maps/" + itemid
	elif info == "owner":
		body = "Your "+itemtype.title()+" has been commented: " + http_host + "/maps/" + itemid
	email = mail.EmailMessage('OpenRA Resource Center - New Comment', body, email_addr,
						  [email_addr], connection=connection)
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
			return obj[0].extra_data['link']
		elif obj[0].provider == "github":
			return obj[0].extra_data['html_url']
	else:
		return ""

def sizeof_fmt(disk_size):
	for x in ['bytes','KB','MB','GB','TB']:
		if disk_size < 1024.0:
			return "%3.1f %s" % (disk_size, x)
		disk_size /= 1024.0

def count_comments_for_many(mapObject, content):
	comments = {}
	for item in mapObject:
		comments[str(item.id)] = 0
		revs = Revisions(content)
		revisions = revs.GetRevisions(item.id)
		for rev in revisions:
			comments[str(item.id)] = len(ThreadedComment.objects.filter(title=content.lower(), object_pk=str(rev)))
	return comments

########## Revisions
class Revisions():

	def __init__(self, modelName):
		self.revisions = []
		self.modelName = modelName

	def GetRevisions(self, itemid, seek_next=False):
		if seek_next:
			if self.modelName.lower() == "map":
				itemObject = Maps.objects.get(id=itemid)
			elif self.modelName.lower() == "unit":
				itemObject = Units.objects.get(id=itemid)
			elif self.modelName.lower() == "mod":
				itemObject = Mods.objects.get(id=itemid)
			if itemObject.next_rev == 0:
				return
			self.revisions.append(itemObject.next_rev)
			self.GetRevisions(itemObject.next_rev, True)
			return
		self.revisions.insert(0, itemid)
		if self.modelName.lower() == "map":
			itemObject = Maps.objects.get(id=itemid)
		elif self.modelName.lower() == "unit":
			itemObject = Units.objects.get(id=itemid)
		elif self.modelName.lower() == "mod":
			itemObject = Mods.objects.get(id=itemid)
		if itemObject.pre_rev == 0:
			self.GetRevisions(self.revisions[-1], True)
			return self.revisions
		self.GetRevisions(itemObject.pre_rev)
		return self.revisions

	def GetLatestRevisionID(self, itemid):
		if self.modelName.lower() == "map":
			itemObject = Maps.objects.get(id=itemid)
		elif self.modelName.lower() == "unit":
			itemObject = Units.objects.get(id=itemid)
		elif self.modelName.lower() == "mod":
			itemObject = Mods.objects.get(id=itemid)
		if itemObject.next_rev == 0:
			return itemObject.id
		return self.GetLatestRevisionID(itemObject.next_rev)