import random

from django.db import models
from django.contrib.auth.models import User

from evolve.rules.models import (
    City, Variant, Age, Building, BuildOption, PERSONALITY
)
from evolve.rules import constants

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
        

    def get_player(self, user):
        """Return player for user, or None if user not part of this game"""
        try:
            return self.player_set.get(user=user)
        except Player.DoesNotExist:
            return None

    @models.permalink
    def get_absolute_url(self):
        return ('game-detail', [], {'pk': self.id})

class Player(models.Model):
    """Single player information for given game"""
    
    ACTIONS = (
        ('build', 'Build'),
        ('free', 'Build(free, use special)'),
        ('sell', 'Sell'),
        ('spec', 'Build special'),
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
    # Ages whre the special_free_bulding ability has been used already
    special_free_building_ages_used = models.ManyToManyField(Age, blank=True, null=True)

    # Private information, player decisions
    current_options = models.ManyToManyField(BuildOption, blank=True, null=True)
    card_picked = models.ForeignKey(BuildOption, blank=True, null=True, related_name='picker_set')
    action = models.CharField(max_length=5, choices=ACTIONS, blank=True)
    trade_left = models.PositiveIntegerField(default=0) # Money used in trade with left player
    trade_right = models.PositiveIntegerField(default=0) # Money used in trade with right player

    def can_play(self):
        return self.game.started and not self.game.finished and self.action != ''

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


