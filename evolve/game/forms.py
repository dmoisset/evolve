from django import forms

from evolve.rules.models import Variant
from evolve.game.models import Game

class NewGameForm(forms.ModelForm):

    allowed_variants = forms.ModelMultipleChoiceField(queryset=Variant.objects.all())

    class Meta:
        model = Game
        fields = ()

