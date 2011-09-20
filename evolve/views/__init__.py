from django.http import HttpResponse
from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated():
        return redirect('games')
    else:
        return redirect('login')
        
    
def login(request):
    # /login/ : login, redirect to /game/ ; link to /register/
    return HttpResponse()
    
def register(request):
    # /register/ : register and redirect to /game/
    return HttpResponse()
    
    
