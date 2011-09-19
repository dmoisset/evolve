from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from evolve.rules.models import (
    BuildingKind, Resource, Science, Variant,
    Age, City, CitySpecial, Building, BuildOption, Cost, CostLine, Effect,
    Building, BuildOption
)
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

site.register(City, CityAdmin)
site.register(Building)
site.register(BuildOption)

class CostLineInline(admin.TabularInline):
    model = CostLine

class CostAdmin(admin.ModelAdmin):
    inlines = [CostLineInline]

site.register(Cost, CostAdmin)
site.register(Effect)



