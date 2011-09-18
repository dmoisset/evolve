from django.db import models
from django.contrib.auth.models import User

from evolve.rules.models import City, Variant, Age, Building, BuildOption
from evolve.rules import constants

# Game models where state is kept

class Game(models.Model):
    """A single match of the game, including all global game status"""
    age = models.ForeignKey(Age)
    turn = models.PositiveIntegerField()

    discards = models.ManyToManyField(BuildOption, blank=True, null=True)
    
    # status
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    special_use_discards_turn = models.BooleanField(default=False) # set when a player is picking from the discard pile

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
    order = models.PositiveIntegerField() # Position between the other players. Less is "left" and more is "right"

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
    special_free_building_ages_used = models.ManyToManyField(Age)

    # Private information, player decisions
    current_options = models.ManyToManyField(BuildOption, blank=True, null=True)
    card_picked = models.ForeignKey(BuildOption, blank=True, null=True, related_name='picker_set')
    action = models.CharField(max_length=5, choices=ACTIONS, blank=True)
    trade_left = models.PositiveIntegerField() # Money used in trade with left player
    trade_right = models.PositiveIntegerField() # Money used in trade with right player

    class Meta:
        unique_together = (
            ('order', 'game'), # No two players can have the same order at the same game
            ('city', 'game'), # No two players can have the same city at the same game
            ('user', 'game'), # A usar can't play as two players (this can be changed, but there's a UI limitation right now)
        )

class BattleResult(models.Model):
    """
    Result of a battle where a player fought.
    If there was no victory nor a defeat, no battle tokens are given.
    """
    owner = models.ForeignKey(Player)
    age = models.ForeignKey(Age)
    direction = models.CharField(max_length=1, choices=constants.DIRECTIONS)
    result = models.CharField(max_length=1, choices=(('v', 'Victory'),('d','Defeat')))


