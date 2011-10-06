# encoding: utf-8
"""
Basic "rule" models. These are loaded from fixtures and not changed
during play
"""
import collections

from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError

from evolve.rules import constants

# Basic listings. This probably will always be fixed and won't be changed
# even while balancing. Adding items to any of these models would probably
# imply a large impact on gameplay

PERSONALITY = 'per' # Kind for personalities which are assigned in a special way
KINDS = (
    ('mil','Military'),
    ('civ','Civilian'),
    ('bas','Basic Resource'),
    ('cpx','Complex Resource'),
    ('eco','Economic'),
    ('sci','Scientific'),
    (PERSONALITY,'Personality'),
)

TRADEABLE = ('bas','cpx')

class BuildingKind(models.Model):
    """Possible building kinds"""

    name = models.CharField(max_length=5, choices=KINDS, primary_key=True)

    def __unicode__(self):
        return self.get_name_display()

    class Meta:
        ordering = ('name',)
    

class Resource(models.Model):
    """Each of the possible resources to collect"""
    name = models.CharField(max_length=30, unique=True)
    is_basic = models.BooleanField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('is_basic', 'name',)


class Science(models.Model):
    """Each of the available sciences"""
    name = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Variant(models.Model):
    """
    One instance of this model exists per possible variant of cities.
    Typically only one or two globally.
    """
    label = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return self.label

    class Meta:
        ordering = ('label',)


class Age(models.Model):
    """
    Each of the phases in a game
    """
    name = models.CharField(max_length=30, unique=True)
    order = models.PositiveIntegerField(unique=True) # Phases are played from lower to higher
    direction = models.CharField(max_length=1, choices=constants.DIRECTIONS)
    victory_score = models.IntegerField() # Score given at this phase per military victory
    defeat_score = models.IntegerField(default=-1) # Score given at this phase per military defeat

    @classmethod
    def first(cls):
        """First Age"""
        return cls.objects.order_by('order')[0]

    def next(self):
        """Returns next age, or none if this is the last one"""
        try:
            return Age.objects.filter(order__gt=self.order).get()
        except Age.DoesNotExist:
            return None

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)

# Other listings that can be tuned to balance or add slight variations to
# the gameplay

class Cost(models.Model):
    """Representation of the cost of something and related operations.
    
    Also used to represent other sets of resources+money
    """
    money = models.PositiveIntegerField(default=0)
    # costline_set =  set of resource costs [reverse]

    def items(self):
        """Artially prettyprinted version of cost lines. An iterator on strings"""
        return [unicode(l) for l in self.costline_set.all()]

    def to_dict(self):
        """
        Dict representation needed in the helper functions on economy.
        
        The conversion is a better idea than using the object directly: a lot
        of copies are created on that functions, and it doesn't make sense
        to have copies of django models that will never get to the DB
        """
        result = collections.defaultdict(lambda:0)
        result['$'] = self.money
        for l in self.costline_set.all():
            result[l.resource.name] = l.amount
        return result

    def to_list(self):
        """
        List representation needed in the helper functions on economy.
        
        list of pairs( amount, resource); money is not included, because 
        this is used for production
        """
        result = []
        for l in self.costline_set.all():
            result.append(tuple(l.amount, l.resource.name))
        return result

    def __unicode__(self):
        elements = ["$%d" % self.money] if self.money else []
        elements.extend(self.items())
    
        return ", ".join(elements) if elements else "Free"

    class Meta:
        ordering = ('money',)


class CostLine(models.Model):
    """An item inside a cost description"""
    cost = models.ForeignKey(Cost)
    amount = models.PositiveIntegerField(validators=[validators.MinValueValidator(1)])
    resource = models.ForeignKey(Resource)

    def __unicode__(self):
        if self.amount == 1:
            return unicode(self.resource)
        else:
            return u"%d×%s" % (self.amount, self.resource)

    class Meta:
        unique_together = (
            ('cost', 'resource'), # Normalize: resources appear only once per cost
        )
        ordering = ('resource', 'amount')


class City(models.Model):
    """A city where a player builds"""
    name = models.CharField(max_length=30, unique=True)
    resource = models.ForeignKey(Resource)
    # city_special_set = set of specials

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'cities'


class Effect(models.Model):
    """
    The effect of a card or special. Note that typically only one of the
    fields will be used, but multiple can be
    """

    # Production here is a "Cost" but acts as an "income". money income is
    # instantaneous (when the effect is applied), and when more than one
    # resource is at the cot, it means that at most one of the resources is
    # produced.
    production = models.ForeignKey(Cost, blank=True, null=True, related_name='payed_effect_set')
    score = models.PositiveIntegerField(default=0) # Score given by the effect
    military = models.PositiveIntegerField(default=0) # military power of the effect

    # An effect can provide many kind of sciences. Only one of them will have
    # to be selected for scoring purposes
    sciences = models.ManyToManyField(Science, blank=True, null=True)
    
    # Trade: again a "cost" used in a special way. The money amount is the
    # cost of trading. Only one of the resources in the cost can be traded
    trade = models.ForeignKey(Cost, blank=True, null=True, related_name='trade_benefit_on_effect_set')
    left_trade = models.BooleanField()
    right_trade = models.BooleanField()
    
    # This effect produces a certain amount of money
    # per building of the kind "kind payed" built by 2 neighbours and/or player
    kind_payed = models.ForeignKey(BuildingKind, blank=True, null=True, related_name='money_benefiting_effects')
    money_per_neighbor_building = models.PositiveIntegerField(default=0)
    money_per_local_building = models.PositiveIntegerField(default=0)
    
    # This effect produces a certain amount of score
    # per building of the kinds "kinds_scored" built by 2 neighbours and/or player
    kinds_scored = models.ManyToManyField(BuildingKind, blank=True, null=True, related_name='score_benefiting_effects')
    score_per_neighbor_building = models.PositiveIntegerField(default=0)
    score_per_local_building = models.PositiveIntegerField(default=0)
    
    # Effects that give bonus money (instant) or score depending on the number
    # of special builts (local and/or by neighbors)
    money_per_local_special = models.PositiveIntegerField(default=0)
    score_per_local_special = models.PositiveIntegerField(default=0)
    money_per_neighbor_special = models.PositiveIntegerField(default=0)
    score_per_neighbor_special = models.PositiveIntegerField(default=0)

    # extra score per neighbor defeats 
    score_per_neighbor_defeat = models.PositiveIntegerField(default=0)

    # Special effects
    free_building = models.BooleanField()
    extra_turn = models.BooleanField()
    use_discards = models.BooleanField()
    copy_personality = models.BooleanField()
    
    def clean(self):
        # trade should be set iff a direction is
        has_trade_1 = self.trade is not None
        has_trade_2 = self.left_trade or self.right_trade
        if has_trade_1 != has_trade_2:
            raise ValidationError('Set trade attribute along left_trade and/or right_trade')
        # pay per building type should be set if money is
        has_pay_1 = self.kind_payed is not None
        has_pay_2 = self.money_per_local_building > 0 or self.money_per_neighbor_building > 0
        if has_pay_1 != has_pay_2:
            raise ValidationError('Set kind_payed attribute along money_per_*')
        # score per building type should be set if score_per is
        if self.pk is not None: # Avoid checking before first save
            has_score_1 = bool(self.kinds_scored.all())
            has_score_2 = self.score_per_local_building > 0 or self.score_per_neighbor_building > 0
            if has_score_1 != has_score_2:
                raise ValidationError('Set kind_scored attribute along score_per_*')
    
    def __unicode__(self):
        items = []
        if self.production is not None:
            if self.production.money > 0:
                items.append("$%d" % self.production.money)
            resources = self.production.items()
            if resources:
                items.append("/".join(resources))
        if self.score:
            items.append("%d pts" % self.score)
        if self.military:
            items.append("%d army" % self.military)
        if self.sciences.all():
            items.append("/".join(unicode(s) for s in self.sciences.all()))
        if self.left_trade or self.right_trade:
            assert self.trade is not None # Validation rule
            trade = "< "if self.left_trade else ""
            trade += "(%d) " % self.trade.money
            trade += "/".join(self.trade.items())
            trade += " >" if self.right_trade else ""
            items.append(trade)
        # TODO: Score/money per specials
        # TODO: score per defeats
        # TODO: specials

        return ", ".join(items)

class CitySpecial(models.Model):
    """
    A special effect that can be built in a single city/variant of a city
    """
    city = models.ForeignKey(City)
    variant = models.ForeignKey(Variant)
    order = models.PositiveIntegerField() # Order in which the special needs to be built (specials are always built from lower to higher). 0-based
    cost = models.ForeignKey(Cost)
    effect = models.ForeignKey(Effect)

    def __unicode__(self):
        return "%s(%s) / %d" % (self.city, self.variant, self.order+1)
    
    class Meta:
        unique_together = (
            ('city', 'variant', 'order'),
        )
        ordering = ('city', 'variant', 'order')

class Building(models.Model):
    """
    What a player can put in cities to have its effects applied
    """
    name = models.CharField(max_length=30, unique=True)
    kind = models.ForeignKey(BuildingKind)
    effect = models.ForeignKey(Effect)

    cost = models.ForeignKey(Cost)
    free_having = models.ForeignKey('self', blank=True, null=True) # This models is free when having other bulding

    def __unicode__(self):        
        return self.name

    class Meta:
        ordering = ('name',)

class BuildOption(models.Model):
    """An item allowing to create a specific bulding on a phase"""
    players_needed = models.PositiveIntegerField(default=3)
    building = models.ForeignKey(Building)
    age = models.ForeignKey(Age)
    
    def __unicode__(self):        
        return "%s (+%d)" % (self.building, self.players_needed)

    class Meta:
        ordering = ('building',)

    
