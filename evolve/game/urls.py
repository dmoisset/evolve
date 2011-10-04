from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('evolve.game.views',
    url(r'^$', 'game_list', name='games'),
    url(r'^new/$', 'new_game', name='new-game'),
    url(r'^(?P<pk>\d+)/$', 'game_detail', name='game-detail'),
    url(r'^(?P<pk>\d+)/join/$', 'game_join', name='game-join'),
    url(r'^(?P<pk>\d+)/start/$', 'game_start', name='game-start'),
    url(r'^(?P<pk>\d+)/play/$', 'game_play', name='game-play'),
    url(r'^(?P<pk>\d+)/wait-turn/$', 'game_wait', name='game-wait'),
)

# /1/ : Main game screen, redirects according to state: If game...
#       - is not started and not joined, join/
#       - is not started and joined, wait-start/ (link to start/ if owner)
#       - is finished, score/
#       - is in progress, and haven't played play/
#       - is in progress, and have already played wait-turn/
#       - in special turn, wait-turn/ (discard or extra turn)

