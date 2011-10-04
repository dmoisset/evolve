from django import forms

from evolve.rules.models import Variant, BuildOption
from evolve.game.models import Game, Player

class NewGameForm(forms.ModelForm):

    class Meta:
        model = Game
        fields = ('allowed_variants',)

class JoinForm(forms.Form):
    pass

class StartForm(forms.Form):
    pass

def _payment_coerce(value):
    if value[0]!='(' or value[-1]!=')': raise ValueError
    value = value[1:-1]
    id, l, r = map(int, value.split(','))
    return id,l,r

class PlayForm(forms.Form):

    option = forms.ModelChoiceField(
        queryset=BuildOption.objects.none(),
        empty_label=None,
        widget = forms.RadioSelect)
    action = forms.ChoiceField(Player.ACTIONS)
    payment = forms.TypedChoiceField(choices=(), coerce=_payment_coerce, empty_value=None)

    
