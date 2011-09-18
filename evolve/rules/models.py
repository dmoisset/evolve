from django.db import models

# Basic "rule" models. These are typically loaded from fixtures and not changed

class Resource(models.Model):
    """Each of the possible resources to collect"""
    name = models.CharacterField(max_length=30, unique=True)
    is_basic = models.BooleanField()

class Cost(models.Model):
    """Representation of the cost of something and related operations"""
    money = models.IntegerField(default=0)
    # No other fields, essentially a collection of CostLine

class CostLine(models.Model):
    cost = models.ForeignKey(Cost)

class Variant(models.Model):
    """
    One instance of this model exists per possible variant of cities.
    Typically only one or two globally.
    """
    label = models.CharacterField(max_length=30, unique=True)

class City(models.Model):
    """A city where a player builds"""
    name = models.CharacterField(max_length=30)
    resource = models.ForeignKey(Resource)

class CitySpecial(models.Model):
    """
    A special effect that can be built in a single city/variant of a city
    """
    city = models.ForeignKey(City)
    variant = models.ForeignKey(Variant)
    order = models.IntegerField() # Order in which the special needs to be built (specials are always built from lower to higher)
    cost = models.ForeignKey(Cost)
    
    class Meta:
        unique_together = (
            ('city', 'variant', 'order'),
        )


