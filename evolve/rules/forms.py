from django import forms

from evolve.rules.models import Effect

class EffectForm(forms.ModelForm):
    class Meta:
        model = Effect

    def clean(self):
        cleaned_data = super(EffectForm, self).clean()
        # Check that the core_per_* are set along kinds_scored
        # This is done here instead of model validation because kinds_scored is M2M,
        # so it's not yet set during model validation
        has_score_1 = bool(cleaned_data['kinds_scored'])
        has_score_2 = cleaned_data['score_per_local_building'] > 0 or cleaned_data['score_per_neighbor_building'] > 0
        if has_score_1 != has_score_2:
            raise forms.ValidationError('Set kind_scored attribute along score_per_*')
        return cleaned_data
