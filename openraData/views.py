from django.http import HttpResponse
from django.conf import settings

def index(request):
    return HttpResponse("You are at the OpenRA Content Website index page.")
