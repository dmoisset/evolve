from django.contrib.admin.sites import AdminSite

from evolve.rules.models import BuildingKind, Resource, Science, Variant, Age

site=AdminSite('rules')

site.register(BuildingKind)
site.register(Resource)
site.register(Science)
site.register(Variant)
site.register(Age)

