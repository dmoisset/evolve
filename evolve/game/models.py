import random

from django.db import models
from django.contrib.auth.models import User

from evolve.rules.models import City, Variant, Age, Building, BuildOption
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

    def join(self, user):
        """Make the given user join to this game"""
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
        

    @models.permalink
    def get_absolute_url(self):
        return ('game-detail', [], {'game_id': self.id})

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

    class Meta:
        unique_together = (
            ('city', 'game'), # No two players can have the same city at the same game
            ('user', 'game'), # A usar can't play as two players (this can be changed, but there's a UI limitation right now)
        )
        order_with_respect_to = 'game'

class BattleResult(models.Model):
    """
    Result of a battle where a player fought.
    If there was no victory nor a defeat, no battle tokens are given.
    """
    owner = models.ForeignKey(Player)
    age = models.ForeignKey(Age)
    direction = models.CharField(max_length=1, choices=constants.DIRECTIONS)
    result = models.CharField(max_length=1, choices=(('v', 'Victory'),('d','Defeat')))


