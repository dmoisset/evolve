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

admin.site.register(City, CityAdmin)
admin.site.register(Building)
admin.site.register(BuildOption)

class CostLineInline(admin.TabularInline):
    model = CostLine

class CostAdmin(admin.ModelAdmin):
    inlines = [CostLineInline]

admin.site.register(Cost, CostAdmin)
admin.site.register(Effect)



