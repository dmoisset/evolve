from django import forms

from evolve.rules.models import Variant
from evolve.game.models import Game

class NewGameForm(forms.ModelForm):

    class Meta:
        model = Game
        fields = ('allowed_variants',)

class JoinForm(forms.Form):
    pass
