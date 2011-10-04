from django.template.response import TemplateResponse
from django.views.generic.edit import CreateView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from evolve.game.models import Game, Player
from evolve.game.forms import NewGameForm, JoinForm, StartForm, PlayForm

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
        result = super(NewGameView, self).form_valid(form)
        # Join current user to the game
        self.object.join(self.request.user)
        return result

new_game = login_required(NewGameView.as_view())

@login_required
def game_detail(request, pk):
    game = get_object_or_404(Game, id=pk)
    player = game.get_player(request.user)
    if game.finished:
        print "finished"
        return # FIXME: show score
    elif player:
        if not game.started:
            return redirect('game-start', pk=pk)
        elif player.can_play():
            return redirect('game-play', pk=pk)
        else:
            print "waiting"
            return # FIXME: view own game
    else:
        if game.is_joinable():
            return redirect('game-join', pk=pk)
        else:
            print "observing"
            return # FIXME view game

class GameActionView(SingleObjectMixin, FormView):
    """Base class for actions that operate on games"""
    model = Game

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(GameActionView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(GameActionView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        result = super(GameActionView, self).get_context_data(**kwargs)
        result['player_in_game'] = self.object.get_player(self.request.user)
        return result

class GameJoinView(GameActionView):
    form_class = JoinForm
    template_name = 'game/join.html'

    def form_valid(self, form):
        game = self.object
        if game.is_joinable(self.request.user):
            game.join(self.request.user)
            return redirect(game.get_absolute_url())
        else:
            return self.form_invalid(form)

game_join = login_required(GameJoinView.as_view())

class GameStartView(GameActionView):
    form_class = StartForm
    template_name = 'game/start.html'

    def form_valid(self, form):
        game = self.object
        if game.is_startable and game.get_player(self.request.user) is not None:
            game.start()
            return redirect(game.get_absolute_url())
        else:
            return self.form_invalid(form)

game_start = login_required(GameStartView.as_view())

class GamePlayView(GameActionView):
    form_class = PlayForm
    template_name = 'game/play.html'

    def get_form(self, form_class):
        form = super(GamePlayView, self).get_form(form_class)
        player = self.object.get_player(self.request.user)
        # Set build options for the current player
        form.fields['option'].queryset = player.current_options.all()
        # Remove the free build option if not available
        actions = Player.ACTIONS
        if not player.can_build_free():
            actions = [(value, label) for (value, label) in actions if value != Player.FREE_ACTION]
        # remove the build special option if not available
        if not player.can_build_special():
            actions = [(value, label) for (value, label) in actions if value != Player.SPECIAL_ACTION]
        form.fields['action'].choices = actions
        return form

game_play = login_required(GamePlayView.as_view())

