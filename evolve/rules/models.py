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

class Score(collections.namedtuple('Score', 'treasury military special civilian economy science personality')):
    
    @classmethod
    def new(cls):
        return cls(0,0,0,0,0,0,0)

    def __add__(self, other):
        sums = [x+y for x,y in zip(self, other)]
        return Score(*sums)

    def total(self):
        return sum(self._asdict().values())

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
            return Age.objects.filter(order__gt=self.order)[0]
        except IndexError:
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
        # Not covered by tests; used only auxiliarly by Effect.__unicode__
        # and in Cost.__unicode__

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
            result.append((l.amount, l.resource.name))
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
    
    def get_score(self, local, left, right):
        """
        Score (as an int, not a Score() instance) produced by this effect
        
        local, left, right are Player-like objects, i.e., they just need to have
        the following methods:
           - count(kind): returning number of buildings of given kind
           - specials(): number of specials built        
           - defeats(): number of defeats suffered        
        """
        result = self.score
        for k in self.kinds_scored.all():
            result += self.score_per_local_building * local.count(k)
            result += self.score_per_neighbor_building * left.count(k)
            result += self.score_per_neighbor_building * right.count(k)
        result += self.score_per_local_special * local.specials()
        result += self.score_per_neighbor_special * (left.specials() + right.specials())
        result += self.score_per_neighbor_defeat * (left.defeats() + right.defeats())
        return result
    
    def money(self, local, left, right):
        """
        Money produced by this effect for local when its neighbors are left
        and right.
        
        local, left, right are Player-like objects, i.e., they just need to have
        the following methods:
           - count(kind): returning number of buildings of given kind
           - specials(): number of specials built
        """
        result = 0
        if self.production:
            result += self.production.money
        if self.money_per_neighbor_building:
            result += self.money_per_neighbor_building * (left.count(self.kind_payed)+right.count(self.kind_payed))
        if self.money_per_local_building:
            result += self.money_per_local_building * local.count(self.kind_payed)
        if self.money_per_neighbor_special:
            result += self.money_per_neighbor_special * (left.specials()+right.specials())
        if self.money_per_local_special:
            result += self.money_per_local_special * local.specials()
        return result
    
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
        # score per building type should be set if score_per is. but
        # kinds_scored is M2M, which are set after clean() so we can't validate
        # here. That step is checked during form validation
    
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
        if self.money_per_local_building:
            items.append("$%d/%s v" % (self.money_per_local_building, self.kind_payed))
        if self.money_per_neighbor_building:
            items.append("$%d/%s < >" % (self.money_per_neighbor_building, self.kind_payed))
        if self.score_per_local_building:
            items.append("%dpt/%s v" % (self.score_per_local_building, ','.join(unicode(k) for k in self.kinds_scored.all())))
        if self.score_per_neighbor_building:
            items.append("%dpt/%s < >" % (self.score_per_neighbor_building, ','.join(unicode(k) for k in self.kinds_scored.all())))
        if self.money_per_local_special or self.score_per_local_special:
            items.append("($%d+%dpt)/Special" % (self.money_per_local_special, self.score_per_local_special))
        if self.money_per_neighbor_special or self.score_per_neighbor_special:
            items.append("($%d+%dpt)/Special < >" % (self.money_per_neighbor_special, self.score_per_neighbor_special))
        if self.score_per_neighbor_defeat:
            items.append("%dpt/defeat < >" % self.score_per_neighbor_defeat)
        if self.free_building:
            items.append("1 Free building per age")
        if self.extra_turn:
            items.append("Can build last option")
        if self.use_discards:
            items.append("Build one discarded option")
        if self.copy_personality:
            items.append("Apply one personality option from a neighbor")

        return ", ".join(items)
        # not tested. This is mildly used in the admin, but the UI should
        # find a better representation

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
    free_having = models.ManyToManyField('self', blank=True, null=True, symmetrical=False) # This models is free when having other bulding

    def score(self, local, left, right):
        """
        Score() object for this building
        """
        amount = self.effect.get_score(local, left, right)
        if self.kind.name == 'eco': # FIXME: hardcoded constant
            return Score.new()._replace(economy=amount)
        elif self.kind.name == 'civ': # FIXME: hardcoded constant
            return Score.new()._replace(civilian=amount)
        elif self.kind.name == PERSONALITY:
            return Score.new()._replace(personality=amount)
        else:
            assert amount == 0
            return Score.new()

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

    
