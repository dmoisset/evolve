import random
import collections

from django.db import models
from django.contrib.auth.models import User

from evolve.rules.models import (
    City, CitySpecial, Variant, Age, Building, BuildOption, Effect, PERSONALITY, TRADEABLE
)
from evolve.rules import constants, economy


# Game models where state is kept

class Game(models.Model):
    """A single match of the game, including all global game status"""
    # game settings
    allowed_variants = models.ManyToManyField(Variant)

    # game state
    age = models.ForeignKey(Age, default=Age.first)
    turn = models.PositiveIntegerField(default=1)
    discards = models.ManyToManyField(BuildOption, blank=True, null=True)
    
    # status for the join/play/finish cycle
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    special_use_discards_turn = models.BooleanField(default=False) # set when a player is picking from the discard pile

    def is_joinable(self, user=None):
        """True if the game has still room for more players and user, is specified, isn't already playing"""
        available_cities = City.objects.exclude(player__game=self)
        user_not_playing = user is None or not self.get_player(user)
        return not self.started and bool(available_cities) and bool(user_not_playing)

    def join(self, user):
        """Make the given user join to this game"""
        assert self.is_joinable()
        # Pick a city
        available_cities = list(City.objects.exclude(player__game=self))
        variants = list(self.allowed_variants.all())
        assert variants # should be at least one, by modeling
        if not available_cities:
            raise City.DoesNotExist
        # Create player
        player = Player(
            user=user,
            game=self,
            variant=random.choice(variants),
            city=random.choice(available_cities),
        )
        player.save()
        # TODO: if all cities assigned, game should auto-start?
        
    def is_startable(self):
        """True if game can be started"""
        return not self.started and self.player_set.count() >= constants.MINIMUM_PLAYERS

    def start(self):
        """Put the game in its initial state, and ready to play"""
        assert self.is_startable()
        assert not self.finished
        assert self.age == Age.first()
        assert self.discards.count() == 0
        assert self.turn == 1
        # Start!
        self.started = True
        self.save()
        # Shuffle build options for this age
        self.shuffle()
    start.alters_data = True

    def shuffle(self):
        """Assign to each player the build options"""
        assert self.started
        assert not self.finished

        n = self.player_set.count()
        required_options = n * constants.INITIAL_OPTIONS

        options = list(BuildOption.objects.filter(
            age=self.age,
            players_needed__lte=n
        ).exclude(
            building__kind__name=PERSONALITY
        ).order_by('?'))
        personalities = list(BuildOption.objects.filter(
            age=self.age,
            players_needed__lte=n,
            building__kind__name=PERSONALITY
        ).order_by('?'))

        # Check that there are enough options for everyone
        if len(options)+len(personalities) < required_options:
            raise BuildOption.DoesNotExist

        # Figure out how many personalities to use
        required_personalities = required_options - len(options)
        recommended_personalities = 2+n
        #   actual = Clip recommended in range [required..available]
        actual_personalities = min(max(recommended_personalities, required_personalities), len(personalities))

        # Remove unused personalities
        del personalities[actual_personalities:]
        # Remove unused options, relpace by personalities
        options[required_options-len(personalities):] = personalities
        
        # Now the set of options is built. Assign
        assert len(options) == required_options
        for p in self.player_set.all():
            assert not p.current_options.all() # No options when shuffling
            p.current_options.add(*options[:constants.INITIAL_OPTIONS])
            del options[:constants.INITIAL_OPTIONS]
    shuffle.alters_data = True

    def get_player(self, user):
        """Return player for user, or None if user not part of this game"""
        try:
            return self.player_set.get(user=user)
        except Player.DoesNotExist:
            return None

    def end_of_turn(self):
        for p in self.player_set.all():
            p.reset_action()
    end_of_turn.alters_data = True

    def turn_check(self):
        """Checks if we need to do end of turn"""
        missing_players = self.player_set.filter(action='')
        if not missing_players:
            self.end_of_turn()
    turn_check.alters_data = True

    @models.permalink
    def get_absolute_url(self):
        return ('game-detail', [], {'pk': self.id})


class Player(models.Model):
    """Single player information for given game"""

    BUILD_ACTION= 'build'
    FREE_ACTION = 'free'
    SELL_ACTION = 'sell'
    SPECIAL_ACTION = 'spec'
    ACTIONS = (
        (BUILD_ACTION, 'Build'),
        (FREE_ACTION, 'Build(free, use special)'),
        (SELL_ACTION, 'Sell'),
        (SPECIAL_ACTION, 'Build special'),
    )
    
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)

    city = models.ForeignKey(City)
    variant = models.ForeignKey(Variant)

    # General information
    money = models.PositiveIntegerField(default=constants.INITIAL_MONEY)
    # All specials for the city/variant with order strictly lower than
    # specials_built are considered built.
    specials_built = models.PositiveIntegerField(default=0)
    # battle_result_set = results of battles
    buildings = models.ManyToManyField(Building, blank=True, null=True)
    # Ages where the special_free_bulding ability has been used already
    special_free_building_ages_used = models.ManyToManyField(Age, blank=True, null=True)

    # Private information, player decisions
    current_options = models.ManyToManyField(BuildOption, blank=True, null=True)
    option_picked = models.ForeignKey(BuildOption, blank=True, null=True, related_name='picker_set')
    action = models.CharField(max_length=5, choices=ACTIONS, blank=True)
    trade_left = models.PositiveIntegerField(default=0) # Money used in trade with left player
    trade_right = models.PositiveIntegerField(default=0) # Money used in trade with right player

    def active_effects(self):
        """The set of effects which apply to this player"""
        # City specials
        city_effects = Effect.objects.filter(cityspecial__city=self.city, cityspecial__variant=self.variant, cityspecial__order__lt=self.specials_built)
        # Building effects
        effects = city_effects | Effect.objects.filter(building__player=self)
        return effects

    def left_player(self):
        try:
            return self.get_previous_in_order()
        except:
            return self.game.player_set.order_by('-_order')[0]

    def right_player(self):
        try:
            return self.get_next_in_order()
        except:
            return self.game.player_set.order_by('_order')[0]
    
    def tradeable_resources(self):
        """
        List of resources that can be bought by neighbors; note that not
        every resource available is tradeable.
        
        This a [[(amount, resource)]]. Inner list are alternative resources
        """
        # Basic city resource is tradeable
        result = [[(1, self.city.resource.name)]]
        # Add in production of resources by tradeable kinds of buildings
        for b in self.buildings.filter(kind__in=TRADEABLE):
            if b.effect.production:
                result.append(b.effect.production.to_list())
        return result

    def trade_costs(self, direction):
        """
        Costs of trading with player in given direction ('l' or 'r')
        
        dict of resource_name -> money
        """
        assert direction in ('l', 'r')
        result = collections.defaultdict(lambda: constants.DEFAULT_TRADE_COST)
        for e in self.active_effects():
            if (direction=='l' and e.left_trade) or (direction=='r' and e.right_trade):
                cost = e.trade.money
                for _, resource in e.trade.to_list():
                    # Pick the better value for each resource
                    result[resource] = min(result[resource], cost)
        return result
        

    def local_production(self):
        """
        List of resources produced by every local effect (not counting trade)
        
        This a [[(amount, resource)]]. Inner list are alternative resources
        """
        # Basic city resource is local production
        result = [[(1, self.city.resource.name)]]
        # Add in production of resources by tradeable kinds of buildings
        for e in self.active_effects():
            if e.production:
                result.append(e.production.to_list())
        return result
    
    def can_play(self):
        return self.game.started and not self.game.finished and self.action == ''

    def can_build_free(self):
        """
        True if player can use the 'free building' effect. Needs to have the
        effect available, and not already used in this age.
        """
        # This only makes sense on started games
        if not self.game.started: return False
        # Check that the player has the free build ability
        if not self.active_effects().filter(free_building=True): return False
        # Check that the effect hasn't been already used
        if special_free_building_ages_used.filter(game=self.game): return False
        # Otherwise, the effect can be used
        return True

    def play(self, action, option, trade_left, trade_right):
        """
        Choose to play the given action with the given build option.
        
        Note that this is the selection of the option, the action is not applied
        until the end of turn (which is checked at the end of this method).
        
        Preconditions:
         - action is one of the Player.ACTIONS
         - option in self.current_options.all()
         - option == FREE_ACTION implies self.can_build_free()
         - option == SPECIAL_ACTION implies self.can_build_special()
         - option == BUILD_ACTION implies option.cost can be paid with given trade
        """
        assert action in (name for name,label in self.ACTIONS)
        assert option in self.current_options.all()
        assert option != self.FREE_ACTION or self.can_build_free()
        assert option != self.SPECIAL_ACTION or self.can_build_special()
        assert option != self.BUILD_ACTION or economy.can_pay(self.payment_options(option.cost), trade_left, trade_right)
        
        self.action = action
        self.option_picked = option
        self.trade_left = trade_left
        self.trade_right = trade_right
        self.save()
        
        self.game.turn_check()

    def reset_action(self):
        self.action = ''
        self.option_picked = None
        self.trade_left = 0
        self.trade_right = 0
        self.save()
    reset_action.alters_data = True

    def next_special(self):
        """
        Next special to build, None if all built
        """
        specials = CitySpecial.objects.filter(city=self.city, variant=self.variant, order__gte=self.specials_built).order_by('order')
        if specials:
            return specials[0]

    def can_build_special(self):
        """
        True if player can use the 'build special' action. Needs to have an
        available special, and resources to pay for it
        """
        # This only makes sense on started games
        if not self.game.started: return False
        # Check that there is a next special to build
        special = self.next_special()
        if special is None: return False
        # Check that the player can pay for the special
        return bool(self.payment_options(special.cost))

    def count(self, kind):
        """Number of buildings of a given kind"""
        return self.buildings.filter(kind=kind).count()
    
    def specials(self):
        """Number of specials built"""
        return self.specials_built

    def military(self):
        """Military power"""
        # Just the sum of the military powers of each effect
        return self.active_effects().aggregate(models.Sum('military'))

    def payment_options(self, cost):
        """List of ways of paying for cost. Empty if unpayable"""
        # FIXME: what about free chains?
        return economy.get_payments(
            cost.to_dict(),
            self.money,
            self.local_production(),
            self.left_player().tradeable_resources(),
            self.trade_costs('l'),
            self.right_player().tradeable_resources(),
            self.trade_costs('r'),
        )            

    class Meta:
        unique_together = (
            ('city', 'game'), # No two players can have the same city at the same game
            ('user', 'game'), # A user can't play as two players (this can be changed, but there's a UI limitation right now)
        )
        order_with_respect_to = 'game'

    def __unicode__(self):
        return unicode(self.user)

class BattleResult(models.Model):
    """
    Result of a battle where a player fought.
    If there was no victory nor a defeat, no battle tokens are given.
    """
    owner = models.ForeignKey(Player)
    age = models.ForeignKey(Age)
    direction = models.CharField(max_length=1, choices=constants.DIRECTIONS)
    result = models.CharField(max_length=1, choices=(('v', 'Victory'),('d','Defeat')))


