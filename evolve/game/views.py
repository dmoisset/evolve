from django.template.response import TemplateResponse

from evolve.game.models import Game

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
        my_games: my_games,
        open_games: open_games,
        started_games: started_games,
    })

def new_game(request):
    pass    
