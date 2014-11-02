import os
import json
from django.conf import settings
from django.http import StreamingHttpResponse
from django.template import RequestContext, loader
from django.http import HttpResponseRedirect, Http404
from django.db import connection
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User
from openraData.models import Maps

@csrf_exempt
def jRating(request):
	if request.method == 'POST':
		if request.POST.get('action', "").strip() == "rating":
			arData = {}
			arData['item_type'] = request.POST.get('idBox', "").split("_")[0]
			arData['item_id'] = request.POST.get('idBox', "").split("_")[1]
			arData['rate'] = request.POST.get('rate', "")
			arData['user_id'] = request.user.id
			response = StreamingHttpResponse(json.dumps(arData, indent=4), content_type="application/javascript")
			return response
		else:
			response = StreamingHttpResponse(json.dumps({'status': 'error'}), content_type="application/javascript")
		return response
	else:
		response = StreamingHttpResponse(json.dumps({'status': 'error'}), content_type="application/javascript")
		return response