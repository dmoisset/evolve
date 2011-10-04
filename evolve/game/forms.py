from django import forms

from evolve.rules.models import Variant, BuildOption
from evolve.game.models import Game, ACTIONS

class NewGameForm(forms.ModelForm):

    class Meta:
        model = Game
        fields = ('allowed_variants',)

class JoinForm(forms.Form):
    pass

class StartForm(forms.Form):
    pass

def _payment_coerce(value):
    i, j = map(int, value.split(','))
    return i,j

class PlayForm(forms.Form):

    option = forms.ModelChoiceField(
        queryset=BuildOption.objects.none(),
        empty_label=None,
        widget = forms.RadioSelect)
    action = forms.ChoiceField(ACTIONS)
    payment = forms.TypedChoiceField(choices=(), coerce=_payment_coerce, empty_value=None)

