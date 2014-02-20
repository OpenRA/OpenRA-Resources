from django.core import mail
from django.conf import settings

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

def send_email_to_admin_OnReport(body):
	connection = mail.get_connection()
	connection.open()
	email = mail.EmailMessage('OpenRA Resource Center - New Report', body, settings.ADMIN_EMAIL,
                          [settings.ADMIN_EMAIL], connection=connection)
	email.send()
	connection.close()