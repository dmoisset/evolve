from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from evolve.rules.models import (
    BuildingKind, Resource, Science, Variant,
    Age, City, CitySpecial, Building, BuildOption, Cost, CostLine, Effect,
    Building, BuildOption
)
from evolve.rules.forms import EffectForm

site=AdminSite('rules')

site.register(BuildingKind)
site.register(Resource)
site.register(Science)
site.register(Variant)
site.register(Age)

class CitySpecialInline(admin.TabularInline):
    model = CitySpecial

class CityAdmin(admin.ModelAdmin):
    inlines = [CitySpecialInline]

class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'cost','effect')
    list_filter = ('kind',)

class BuildOptionAdmin(admin.ModelAdmin):
    list_display = ('building', 'players_needed', 'age')
    list_filter = ('players_needed','age')

class EffectAdmin(admin.ModelAdmin):
    form = EffectForm

admin.site.register(City, CityAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(BuildOption, BuildOptionAdmin)

class CostLineInline(admin.TabularInline):
    model = CostLine

class CostAdmin(admin.ModelAdmin):
    inlines = [CostLineInline]

admin.site.register(Cost, CostAdmin)
admin.site.register(Effect, EffectAdmin)



