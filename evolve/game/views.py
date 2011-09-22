from django.template.response import TemplateResponse
from django.views.generic.edit import CreateView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from evolve.game.models import Game, Player
from evolve.game.forms import NewGameForm, JoinForm

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

@login_required
def game_detail(request, pk):
    game = get_object_or_404(Game, id=pk)
    try:
        player = Player.objects.get(game=game, user=request.user)
        return # FIXME: view own game
    except Player.DoesNotExist:
        if game.is_joinable():
            return redirect('game-join', pk=pk)
        else:
            return # FIXME view game being waited to start

class GameJoinView(SingleObjectMixin, FormView):
    model = Game
    form_class = JoinForm
    template_name = 'game/join.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(GameJoinView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        game = self.object = self.get_object()
        if game.is_joinable(self.request.user):
            game.join(self.request.user)
            return redirect(game.get_absolute_url())
        else:
            return self.form_invalid(form)
    
game_join = login_required(GameJoinView.as_view())

