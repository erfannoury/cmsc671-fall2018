import numpy as np
from utils import Directions
import util_functions as uf


class BaseAgent(object):
    def __init__(self, name='base_agent'):
        """

        Parameters
        ----------
        name: str
            Name of the agent
        """
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
    def __init__(self, name='random_agent'):
        return super().__init__(name=name)

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
    def __init__(self, name='human_agent'):
        return super().__init__(name=name)

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
        
        dir_dict = {'N':Directions.NORTH,
                    'S':Directions.SOUTH,
                    'W':Directions.WEST,
                    'E':Directions.EAST}

        dirchar=''
        while not dirchar in ['N', 'S', 'W', 'E']:
            dirchar = input("Please enter a direction (N/S/E/W): ").upper()

        return dir_dict[dirchar]
