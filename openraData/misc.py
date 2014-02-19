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