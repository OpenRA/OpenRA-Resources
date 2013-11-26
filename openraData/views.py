from django.http import HttpResponse

def index(request):
    return HttpResponse("You are at the OpenRA Content Website index page.")
