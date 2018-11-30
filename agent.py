import numpy as np
from utils import Directions
import util_functions as uf


class BaseAgent(object):
    def __init__(self, height, width, initial_strength, name='base_agent'):
        """
        Base class for a game agent

        Parameters
        ----------
        height: int
            Height of the game map
        width: int
            Width of the game map
        initial_strength: int
            Initial strength of the agent
        name: str
            Name of the agent
        """
        self.height = height
        self.width = width
        self.initial_strength = initial_strength
        self.name = name

    def step(self, location, strength, game_map, map_objects):
        """

        Parameters
        ----------
        location: tuple of int
            Current location of the agent in the map
        strength: int
            Current strength of the agent
        game_map: numpy.ndarray
            Map of the game as observed by the agent so far
        map_objects: dict
            Objects discovered by the agent so far


        Returns
        -------
        direction: Directions
            Which direction to move
        """
        pass


class RandomAgent(BaseAgent):
    """
    A random agent that moves in each direction randomly

    Parameters
    ----------
    height: int
        Height of the game map
    width: int
        Width of the game map
    initial_strength: int
        Initial strength of the agent
    name: str
        Name of the agent
    """

    def __init__(self, height, width, initial_strength, name='random_agent'):
        super().__init__(height=height, width=width,
                         initial_strength=initial_strength, name=name)

    def step(self, location, strength, game_map, map_objects):
        """
        Implementation of a random agent that at each step randomly moves in
        one of the four directions

        Parameters
        ----------
        location: tuple of int
            Current location of the agent in the map
        strength: int
            Current strength of the agent
        game_map: numpy.ndarray
            Map of the game as observed by the agent so far
        map_objects: dict
            Objects discovered by the agent so far

        Returns
        -------
        direction: Directions
            Which direction to move
        """
        return np.random.choice(list(Directions))


class HumanAgent(BaseAgent):
    """
    A human agent that that can be controlled by the user. At each time step
    the agent will prompt for an input from the user.

    Parameters
    ----------
    height: int
        Height of the game map
    width: int
        Width of the game map
    initial_strength: int
        Initial strength of the agent
    name: str
        Name of the agent
    """

    def __init__(self, height, width, initial_strength, name='human_agent'):
        super().__init__(height=height, width=width,
                         initial_strength=initial_strength, name=name)

    def step(self, location, strength, game_map, map_objects):
        """
        Implementation of an agent that at each step asks the user
        what to do

        Parameters
        ----------
        location: tuple of int
            Current location of the agent in the map
        strength: int
            Current strength of the agent
        game_map: numpy.ndarray
            Map of the game as observed by the agent so far
        map_objects: dict
            Objects discovered by the agent so far

        Returns
        -------
        direction: Directions
            Which direction to move
        """

        uf.print_map(game_map, 'a')

        dir_dict = {'N': Directions.NORTH,
                    'S': Directions.SOUTH,
                    'W': Directions.WEST,
                    'E': Directions.EAST}

        dirchar = ''
        while not dirchar in ['N', 'S', 'W', 'E']:
            dirchar = input("Please enter a direction (N/S/E/W): ").upper()

        return dir_dict[dirchar]
