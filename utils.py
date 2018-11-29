from enum import Enum


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
        pass


class StaticMonster(MapObject):
    def __init__(self):
        self.strength = 10
        self.label = 'skeleton'
        self.delta = -10


class PowerUp(MapObject):
    def __init__(self):
        self.label = 'medkit'
        self.delta = 10


class Boss(StaticMonster):
    def __init__(self):
        self.strength = 100
        self.label = 'boss'
        self.delta = -100
