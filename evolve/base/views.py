from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.views import login as auth_login

def home(request):
    if request.user.is_authenticated():
        return redirect('games')
    else:
        return redirect('login')
    
def login(request):
    return auth_login(request)
#    # /login/ : login, redirect to /game/ ; link to /register/
#    return HttpResponse()
    
def register(request):
    # /register/ : register and redirect to /game/
    return HttpResponse()
    
    
