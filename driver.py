import os
import json
from itertools import cycle, product

import numpy as np

import utils
from agent import BaseAgent
from util_functions import print_map


class GameDriver(object):
    """
    Game driver implementing the whole game logic

    Parameters
    ----------
    height: int
        Height of the game map
    width: int
        Width of the game map
    num_powerups: int
        Number of powerups to use in the game
    num_monsters:
        Number of monsters to use in the game
    agents: list
        A list of agents
    initial_strength: int
        Initial strength of each agent
    show_map: bool
        Whether to show the map at each step of the game
    map_type: str
        Map type to use. Choices are {ascii, emoji}
    save_dir: str
        Directory in which to save the generated map
    map_file: (optional) str
        Map (JSON) file to load the game map

    """

    def __init__(self, height, width, num_powerups, num_monsters, agents,
                 initial_strength, show_map, map_type,
                 save_dir=None, map_file=None):
        assert (num_monsters + num_powerups + 1) <= height * width, \
            'Number of objects in the map should be less than the number of ' \
            'tiles in the map'

        self.width = width
        self.height = height
        self.num_powerups = num_powerups
        self.num_monsters = num_monsters

        if not isinstance(agents, list):
            agents = [agents]
        assert all(isinstance(ag, BaseAgent) for ag in agents), \
            'Agents should be a subclass of BaseAgent'
        self.agents = agents

        self.game_map = None
        self.objects = {}

        self.agent_maps = []
        self.agent_objects = []
        self.agent_locations = []
        self.agent_strengths = [initial_strength] * len(agents)
        self.agent_max_strengths = [initial_strength] * len(agents)

        self.map_file = map_file
        self.show_map = show_map
        self.map_type = map_type

        print('Initializing the game')
        self.initialize_game()
        if save_dir is not None:
            self.save_map(save_dir)

    def play(self, verbose=False):
        for step, agent in enumerate(cycle(self.agents)):
            idx = step % len(self.agents)
            current_loc = self.agent_locations[idx]

            if verbose:
                print('-' * 40)
                print(f'Playing step {step + 1} for {self.agents[idx].name}')
                print('\tCurrent location is', current_loc)
                print('\tCurrent strength is', self.agent_strengths[idx])

            # update map for agents
            for i, j in product(*[[-1, 0, 1]] * 2):
                new_i = current_loc[0] + i
                new_j = current_loc[1] + j

                if 0 <= new_i < self.height and 0 <= new_j < self.width:
                    if self.agent_maps[idx][new_i, new_j] == utils.MapTiles.U:
                        self.agent_maps[idx][new_i, new_j] = \
                            self.game_map[new_i, new_j]
                if (new_i, new_j) in self.objects:
                    self.agent_objects[idx][(new_i, new_j)] = \
                        self.objects[(new_i, new_j)]

            if self.show_map:
                print_map(self.agent_maps[idx], self.map_type)

            direction = agent.step(
                location=self.agent_locations[idx],
                strength=self.agent_strengths[idx],
                game_map=self.agent_maps[idx],
                map_objects=self.agent_objects[idx])

            if verbose:
                print('{} selected to move in the {} direction.'.format(
                    self.agents[idx].name, direction.name))

            assert isinstance(direction, utils.Directions), \
                'Wrong type of direction returned'

            if direction == utils.Directions.NORTH:
                dst_loc = (current_loc[0] - 1, current_loc[1])
            elif direction == utils.Directions.WEST:
                dst_loc = (current_loc[0], current_loc[1] - 1)
            elif direction == utils.Directions.SOUTH:
                dst_loc = (current_loc[0] + 1, current_loc[1])
            else:
                dst_loc = (current_loc[0], current_loc[1] + 1)

            if not (0 <= dst_loc[0] < self.height and
                    0 <= dst_loc[1] < self.width):
                final_loc = current_loc
                self.agent_strengths[idx] -= 1
            elif self.game_map[dst_loc[0], dst_loc[1]] == utils.MapTiles.WALL:
                final_loc = current_loc
                self.agent_strengths[idx] -= 1
            elif (self.agent_strengths[idx] <
                  utils.tile_cost[self.game_map[dst_loc[0], dst_loc[1]]]):
                final_loc = current_loc
                self.agent_strengths[idx] -= 1
            else:
                final_loc = dst_loc
                self.agent_strengths[idx] -= \
                    utils.tile_cost[self.game_map[dst_loc[0], dst_loc[1]]]

            if final_loc in self.objects:
                if isinstance(self.objects[final_loc], utils.PowerUp):
                    self.agent_strengths[idx] += self.objects[final_loc].delta
                    del self.objects[final_loc]
                    for i in range(len(self.agents)):
                        if final_loc in self.agent_objects[i]:
                            del self.agent_objects[i][final_loc]
                elif isinstance(self.objects[final_loc], utils.StaticMonster):
                    # fight
                    win_chance = self.agent_strengths[idx] / \
                        (self.agent_strengths[idx] +
                         self.objects[final_loc].strength)
                    if np.random.random() < win_chance:
                        # agent wins
                        if verbose:
                            print('Agent {} won the fight against {}'.format(
                                self.agents[idx].name,
                                self.objects[final_loc].label))
                        self.agent_max_strengths[idx] += \
                            self.objects[final_loc].strength
                        self.agent_strengths[idx] = self.agent_max_strengths[idx]
                        del self.objects[final_loc]
                        for i in range(len(self.agents)):
                            if final_loc in self.agent_objects[i]:
                                del self.agent_objects[i][final_loc]
                    else:
                        # agent loses
                        if verbose:
                            print('Agent {} lost the fight against {}'.format(
                                self.agents[idx].name,
                                self.objects[final_loc].label))
                        self.agent_strengths[idx] = 0

            self.agent_locations[idx] = final_loc
            if self.agent_strengths[idx] <= 0:
                print(f'Agent {self.agents[idx].name} died!')
                break
            elif final_loc == self.goal_loc:
                print(f'Agent {self.agents[idx].name} won the game!')
                break

    def initialize_game(self):
        """
        This function will generate a random map with the given size and
        initialize other required objects
        """
        if self.map_file is None:
            # generate the game map
            self.generate_map()
        else:
            self.load_map(self.map_file)

        for _ in self.agents:
            # create game maps for each agent
            self.agent_maps.append(
                np.full((self.height, self.width), utils.MapTiles.UNKNOWN))

            # create empty object dictionary for each agent
            self.agent_objects.append({})

    def generate_map(self):
        # TODO: Create a better function for generating the map
        self.game_map = np.random.choice(
            list(utils.MapTiles)[1:], (self.height, self.width),
            p=[0.4, 0.3, 0.2, 0.1])
        nonwall_indices = np.where(self.game_map != utils.MapTiles.WALL)
        # generate objects in the game map
        object_indices = np.random.choice(
            len(nonwall_indices[0]),
            self.num_monsters + self.num_powerups + 1,  # extra for the boss
            replace=False)
        for cnt, idx in enumerate(object_indices[1:]):
            i = nonwall_indices[0][idx]
            j = nonwall_indices[1][idx]
            if cnt < self.num_powerups:
                self.objects[(i, j)] = utils.PowerUp()
            else:
                self.objects[(i, j)] = utils.StaticMonster()
        # the boss
        i = nonwall_indices[0][object_indices[0]]
        j = nonwall_indices[1][object_indices[0]]
        self.objects[(i, j)] = utils.Boss()
        self.goal_loc = (i, j)

        remaining_indices = [[]] * 2

        remaining_indices[0] = [i for idx, i in enumerate(nonwall_indices[0])
                                if idx not in object_indices]
        remaining_indices[1] = [j for idx, j in enumerate(nonwall_indices[1])
                                if idx not in object_indices]

        assert len(remaining_indices[0]) >= len(self.agents), \
            'Not enough empty tiles are left'

        # initial locations for agents
        for i in range(len(self.agents)):
            idx = np.random.choice(len(remaining_indices[0]))
            loc = (remaining_indices[0][idx], remaining_indices[1][idx])
            while (loc == self.goal_loc or
                   any(loc == prev_loc for prev_loc in self.agent_locations)):
                idx = np.random.choice(len(remaining_indices[0]))
                loc = (remaining_indices[0][idx], remaining_indices[1][idx])
            self.agent_locations.append(loc)

    def save_map(self, save_dir):
        """
        Save the game map in a JSON file named `map.json` in the given
        directory

        Parameters
        ----------
        save_dir: str
            Path to the directory for saving the map file
        """
        os.makedirs(save_dir, exist_ok=True)
        json_file = os.path.join(save_dir, 'map.json')

        map_dict = {}
        map_dict['height'] = self.height
        map_dict['width'] = self.width
        map_dict['game_map'] = list(map(
            lambda t: t.value, self.game_map.flatten().tolist()))
        map_dict['objects'] = [[*list(map(int, k)), v.label]
                               for k, v in self.objects.items()]
        map_dict['agent_locations'] = [list(map(int, k))
                                       for k in self.agent_locations]

        json.dump(map_dict, open(json_file, 'w'))


    def load_map(self, map_file):
        """
        Load a previously saved game map.

        Parameters
        ----------
        map_file: str
            Address of the `map.json` file for loading the map
        """
        if not os.path.exists(map_file):
            raise FileNotFoundError('The given map file does not exist')

        map_dict = json.load(open(map_file, 'r'))

        assert map_dict['height'] == self.height, \
            'Map heights do not match'
        assert map_dict['width'] == self.width, \
            'Map widths do not match'
        assert len(map_dict['agent_locations']) == len(self.agents), \
            'Number of agents in the game do not match'

        self.game_map = np.asarray(
            list(map(lambda t: utils.MapTiles(t), map_dict['game_map']))
        ).reshape(self.height, self.width)

        for obj in map_dict['objects']:
            if obj[-1] == 'boss':
                self.objects[tuple(obj[:2])] = utils.Boss()
                self.goal_loc = tuple(obj[:2])
            elif obj[-1] == 'medkit':
                self.objects[tuple(obj[:2])] = utils.PowerUp()
            elif obj[-1] == 'skeleton':
                self.objects[tuple(obj[:2])] = utils.StaticMonster()
            else:
                raise ValueError('Undefined object type')

        self.agent_locations = [tuple(loc) for loc in
                                map_dict['agent_locations']]

    def display_map(self):
        pass
