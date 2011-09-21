from django.template.response import TemplateResponse
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required

from evolve.game.models import Game
from evolve.game.forms import NewGameForm

def game_list(request):
    if request.user.is_authenticated():
        my_games = Game.objects.filter(player__user=request.user)
        open_games = Game.objects.exclude(player__user=request.user).filter(started=False)
        started_games = Game.objects.exclude(player__user=request.user).filter(started=True, finished=False)
    else:
        my_games = Game.objects.none()
        open_games = Game.objects.filter(started=False)
        started_games = Game.objects.filter(started=True, finished=False)
            
    return TemplateResponse(request, 'game/list.html', {
        'my_games': my_games,
        'open_games': open_games,
        'started_games': started_games,
    })

class NewGameView(CreateView):
    form_class = NewGameForm
    template_name = 'game/new.html'

new_game = login_required(NewGameView.as_view())

def game_detail(request, game_id):
    pass
