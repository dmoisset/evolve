from django.http import HttpResponse

def home(request):
    # / : if not logged in, redirect to /login/
    #     if logged in redirect to /game/
    return HttpResponse()
    
def login(request):
    # /login/ : login, redirect to /game/ ; link to /register/
    return HttpResponse()
    
def register(request):
    # /register/ : register and redirect to /game/
    return HttpResponse()
    
    
