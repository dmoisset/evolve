from django.shortcuts import redirect

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.views.generic.edit import CreateView

def home(request):
    if request.user.is_authenticated():
        return redirect('games')
    else:
        return redirect('login')

def logout(request):
    logout(request)
    return redirect('login')

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'

    def form_valid(self, form):
        super(RegisterView, self).form_valid(form)
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'])
        assert user is not None # it was just created!
        assert user.is_active
        
        login(self.request, user)
        return redirect('games')

register = RegisterView.as_view()

