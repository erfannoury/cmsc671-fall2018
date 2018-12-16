from enum import Enum

import numpy as np


class InvalidMapError(Exception):
    """
    Custom Exception for when an invalid map was created
    """
    pass


class Directions(Enum):
    EAST = 0
    E = 0

    NORTH = 1
    N = 1

    WEST = 2
    W = 2

    SOUTH = 3
    S = 3


class MapTiles(Enum):
    U = -1
    UNKNOWN = -1

    P = 0
    PATH = 0

    S = 1
    SAND = 1

    M = 2
    MOUNTAIN = 2

    W = 3
    WALL = 3


tile_cost = {
    MapTiles.PATH: 1,
    MapTiles.SAND: 3,
    MapTiles.MOUNTAIN: 10}


class MapObject(object):
    def __init__(self):
        self.strength = 0
        self.label = 'mapobject'
        self.delta = 0

    def move(self):
        """

        Returns
        -------
        direction: Directions
            Which direction to move
        """
        pass


class AgentPlaceholder(MapObject):
    """
    A placeholder for an agent for when an agent appears in another agent's
    visible part of the map
    """

    def __init__(self, strength):
        super().__init__()
        self.strength = strength
        self.label = 'agent'
        self.delta = -strength


class StaticMonster(MapObject):
    def __init__(self):
        super().__init__()
        self.strength = 10
        self.label = 'skeleton'
        self.delta = -10


class DynamicMonster(MapObject):
    def __init__(self, initial_i, initial_j):
        super().__init__()
        self.initial_i = initial_i
        self.initial_j = initial_j
        self.strength = 10
        self.label = 'skeleton'
        self.delta = -10

    def move(self):
        """

        Returns
        -------
        direction: Directions
            Which direction to move
        """
        return np.random.choice(list(Directions))


class PowerUp(MapObject):
    def __init__(self):
        super().__init__()
        self.label = 'medkit'
        self.delta = 10


class Boss(StaticMonster):
    def __init__(self):
        super().__init__()
        self.strength = 100
        self.label = 'boss'
        self.delta = -100
