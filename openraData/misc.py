from django.core import mail
from django.conf import settings
from django.contrib.auth.models import User

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
	body = "Item: http://%s  By user_id: %s  Reason: %s  Infringement: %s" % (args['addr'], args['user_id'], args['reason'], args['infringement'])
	email = mail.EmailMessage('OpenRA Resource Center - New Report', body, settings.ADMIN_EMAIL,
                          [settings.ADMIN_EMAIL], connection=connection)
	email.send()
	connection.close()

def send_email_to_user_OnReport(args):
	mail_addr = User.objects.get(pk=args['owner_id']).email
	if mail_addr == "":
		return False
	connection = mail.get_connection()
	connection.open()
	body = "Your %s has been reported: %s  |  Reason: %s" % (args['resource_type'], args['addr'], args['reason'])
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