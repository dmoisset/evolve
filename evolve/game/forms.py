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


class OptionField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "%s / cost=%s / effect=%s" % (obj.building, obj.building.cost, obj.building.effect)

class PlayForm(forms.Form):

    option = OptionField(
        queryset=BuildOption.objects.none(),
        empty_label=None,
        widget = forms.RadioSelect)
    action = forms.ChoiceField(Player.ACTIONS)
    payment = forms.TypedChoiceField(choices=(), coerce=_payment_coerce, empty_value=None)

    def clean(self):
        payment = self.cleaned_data.get('payment')
        option = self.cleaned_data.get('option')
        action = self.cleaned_data.get('action')
        if payment and option and action:
            if (payment[0] == -1 and action != Player.SPECIAL_ACTION) or (option.id != payment[0] and action==Player.BUILD_ACTION):
                raise forms.ValidationError("That is not a valid payment for the selected option")
        return self.cleaned_data
