from django.template.response import TemplateResponse
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required

from evolve.game.models import Game
from evolve.game.forms import NewGameForm

def game_list(request):
    games = Game.objects.filter(finished=False) # Only non finished games   
    if request.user.is_authenticated():
        my_games = games.filter(player__user=request.user)
        open_games = games.exclude(player__user=request.user).filter(started=False)
        started_games = games.exclude(player__user=request.user).filter(started=True)
    else:
        my_games = games.none()
        open_games = games.filter(started=False)
        started_games = games.filter(started=True)
            
    return TemplateResponse(request, 'game/list.html', {
        'my_games': my_games,
        'open_games': open_games,
        'started_games': started_games,
    })

class NewGameView(CreateView):
    form_class = NewGameForm
    template_name = 'game/new.html'

    def form_valid(self, form):
        # Create game
        super(NewGameView, self).form_valid(form)
        # Join current user to the game
        self.object.join(self.request.user)

new_game = login_required(NewGameView.as_view())

def game_detail(request, game_id):
    pass
