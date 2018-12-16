import os
import json
from itertools import cycle, product

import numpy as np
import scipy.signal as signal
import emoji as em

import utils
from agent import BaseAgent


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
    num_dynamic_monsters:
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

    def __init__(self, height, width, num_powerups, num_monsters,
                 num_dynamic_monsters, agents,
                 initial_strength, show_map, map_type,
                 save_dir=None, map_file=None):
        objects_count = num_monsters + num_powerups + num_dynamic_monsters + 1
        assert objects_count <= height * width, \
            'Number of objects in the map should be less than the number of ' \
            'tiles in the map'

        self.width = width
        self.height = height
        self.num_powerups = num_powerups
        self.num_monsters = num_monsters
        self.num_dynamic_monsters = num_dynamic_monsters

        if not isinstance(agents, list):
            agents = [agents]
        assert all(isinstance(ag, BaseAgent) for ag in agents), \
            'Agents should be a subclass of BaseAgent'
        self.agents = agents

        self.game_map = None
        self.objects = {}
        self.dynamic_monsters = {}

        self.agent_maps = []
        self.agent_objects = []
        self.agent_moving_objects = [{}] * len(agents)
        self.agent_locations = []
        self.agent_strengths = [initial_strength] * len(agents)
        self.agent_max_strengths = [initial_strength] * len(agents)
        self.agent_final_locs = [[]] * len(agents)

        self.map_file = map_file
        self.show_map = show_map
        self.map_type = map_type

        print('Initializing the game')
        self.initialize_game()
        if save_dir is not None:
            self.save_map(save_dir)

    def play(self, verbose=False):
        step = -1
        while True:
            step += 1
            for idx, agent in enumerate(self.agents):
                # check if the agent is still alive
                if self.agent_strengths[idx] <= 0:
                    # agent has died
                    continue
                # first update the map for each agent
                curr_loc = self.agent_locations[idx]
                self.agent_moving_objects[idx] = {}

                for i, j in product(*[[-1, 0, 1]] * 2):
                    new_i = curr_loc[0] + i
                    new_j = curr_loc[1] + j

                    if 0 <= new_i < self.height and 0 <= new_j < self.width:
                        if (self.agent_maps[idx][new_i, new_j] ==
                                utils.MapTiles.U):
                            if (i == -1 and j == -1 and
                                    self.nwblocks[curr_loc[0], curr_loc[1]] > 0):
                                # north west walls are blocking
                                continue
                            elif (i == -1 and j == 1 and
                                  self.neblocks[curr_loc[0], curr_loc[1]] > 0):
                                # north east walls are blocking
                                continue
                            elif (i == 1 and j == -1 and
                                  self.swblocks[curr_loc[0], curr_loc[1]] > 0):
                                # south west walls are blocking
                                continue
                            elif (i == 1 and j == 1 and
                                  self.seblocks[curr_loc[0], curr_loc[1]] > 0):
                                # south east walls are blocking
                                continue
                            # no walls are blocking
                            self.agent_maps[idx][new_i, new_j] = \
                                self.game_map[new_i, new_j]
                    if (new_i, new_j) in self.objects:
                        self.agent_objects[idx][(new_i, new_j)] = \
                            self.objects[(new_i, new_j)]
                    if (new_i, new_j) in self.dynamic_monsters:
                        self.agent_moving_objects[idx][(new_i, new_j)] = \
                            self.dynamic_monsters[(new_i), (new_j)]
                    for jdx in range(len(self.agents)):
                        if (jdx != idx and
                                self.agent_locations[jdx] == (new_i, new_j)):
                            # if the other agent is visible, add an agent
                            # placeholder to the list of objects for current
                            # agent
                            self.agent_moving_objects[idx][(new_i, new_j)] = \
                                utils.AgentPlaceholder(
                                    self.agent_strengths[jdx])

            for idx, agent in enumerate(self.agents):
                # check if the agent is still alive
                if self.agent_strengths[idx] <= 0:
                    # agent has died
                    continue
                # call each agent and find its final location
                if verbose:
                    print('-' * 40)
                    print(
                        f'Playing step {step + 1} for {self.agents[idx].name}')
                    print('\tCurrent location is', curr_loc)
                    print('\tCurrent strength is', self.agent_strengths[idx])
                if self.show_map:
                    self.display_map(idx)

                objects_to_pass = {}
                objects_to_pass.update(self.agent_objects[idx])
                objects_to_pass.update(self.agent_moving_objects[idx])
                direction = agent.step(
                    location=self.agent_locations[idx],
                    strength=self.agent_strengths[idx],
                    game_map=self.agent_maps[idx],
                    map_objects=objects_to_pass)

                if verbose:
                    print('{} selected to move in the {} direction.'.format(
                        self.agents[idx].name, direction.name))

                assert isinstance(direction, utils.Directions), \
                    'Wrong type of direction returned'

                if direction == utils.Directions.NORTH:
                    dst_loc = (curr_loc[0] - 1, curr_loc[1])
                elif direction == utils.Directions.WEST:
                    dst_loc = (curr_loc[0], curr_loc[1] - 1)
                elif direction == utils.Directions.SOUTH:
                    dst_loc = (curr_loc[0] + 1, curr_loc[1])
                else:
                    dst_loc = (curr_loc[0], curr_loc[1] + 1)

                if not (0 <= dst_loc[0] < self.height and
                        0 <= dst_loc[1] < self.width):
                    # agent tried to move outside of the map
                    final_loc = curr_loc
                    self.agent_strengths[idx] -= 1
                elif (self.game_map[dst_loc[0], dst_loc[1]] ==
                      utils.MapTiles.WALL):
                    # agent hit a wall
                    final_loc = curr_loc
                    self.agent_strengths[idx] -= 1
                elif (self.agent_strengths[idx] <
                      utils.tile_cost[self.game_map[dst_loc[0], dst_loc[1]]]):
                    # agent does not have enough strength to make the move
                    final_loc = curr_loc
                    self.agent_strengths[idx] -= 1
                else:
                    # agent moved normally
                    final_loc = dst_loc
                    self.agent_strengths[idx] -= \
                        utils.tile_cost[self.game_map[dst_loc[0], dst_loc[1]]]
                self.agent_final_locs[idx] = final_loc

            for curr_loc, dynmon in self.dynamic_monsters.items():
                # move the dynamic monsters to new locations
                direction = dynmon.move()

                if direction == utils.Directions.NORTH:
                    dst_loc = (curr_loc[0] - 1, curr_loc[1])
                elif direction == utils.Directions.WEST:
                    dst_loc = (curr_loc[0], curr_loc[1] - 1)
                elif direction == utils.Directions.SOUTH:
                    dst_loc = (curr_loc[0] + 1, curr_loc[1])
                else:
                    dst_loc = (curr_loc[0], curr_loc[1] + 1)

                if not (0 <= dst_loc[0] < self.height and
                        0 <= dst_loc[1] < self.width):
                    # dynamic monster tried to move outside of the map
                    final_loc = curr_loc
                elif (self.game_map[dst_loc[0], dst_loc[1]] ==
                      utils.MapTiles.WALL):
                    # dynamic monster hit a wall
                    final_loc = curr_loc
                elif dst_loc in self.dynamic_monsters:
                    # a dynamic monster is currently in this tile
                    final_loc = curr_loc
                else:
                    # dynamic monster moved normally
                    final_loc = dst_loc

                if final_loc != curr_loc:
                    # move the monster
                    self.dynamic_monsters[final_loc] = \
                        self.dynamic_monsters[curr_loc]
                    del self.dynamic_monsters[curr_loc]

            for idx in range(1, len(self.agents)):
                # check if the agent idx is still alive
                if self.agent_strengths[idx] <= 0:
                    # agent has died
                    continue

                for jdx in range(0, idx):
                    # check if the agent jdx is still alive
                    if self.agent_strengths[jdx] <= 0:
                        # agent has died
                        continue
                    # see if two agents decided to move to the same square
                    if self.agent_final_locs[idx] == self.agent_final_locs[jdx]:
                        # the two agents should fight
                        strength_denom = self.agent_strengths[idx] + \
                            self.agent_strengths[jdx]
                        if strength_denom == 0:
                            # the two agents have died
                            continue
                        idx_win_chance = \
                            self.agent_strengths[idx] / strength_denom
                        if np.random.random() < idx_win_chance:
                            # agent idx wins
                            if verbose:
                                print('Agent {} won the fight against agent {}'
                                      .format(
                                          self.agents[idx].name,
                                          self.agents[jdx].name))
                            self.agent_strengths[idx] += \
                                self.agent_strengths[jdx]
                            self.agent_strengths[jdx] = 0
                            self.agent_objects[jdx] = {}
                        else:
                            # agent jdx wins
                            if verbose:
                                print('Agent {} won the fight against agent {}'
                                      .format(
                                          self.agents[jdx].name,
                                          self.agents[idx].name))
                            self.agent_strengths[jdx] += \
                                self.agent_strengths[idx]
                            self.agent_strengths[idx] = 0
                            self.agent_objects[idx] = {}

            for idx in range(len(self.agents)):
                if self.agent_strengths[idx] <= 0:
                    # agent has died, skip it
                    continue
                # checking objects in the agent's destination tiles
                final_loc = self.agent_final_locs[idx]
                if final_loc in self.objects:
                    if isinstance(self.objects[final_loc], utils.PowerUp):
                        self.agent_strengths[idx] += \
                            self.objects[final_loc].delta
                        del self.objects[final_loc]
                        for i in range(len(self.agents)):
                            if final_loc in self.agent_objects[i]:
                                del self.agent_objects[i][final_loc]
                    elif isinstance(self.objects[final_loc],
                                    utils.StaticMonster):
                        # fight
                        win_chance = self.agent_strengths[idx] / \
                            (self.agent_strengths[idx] +
                             self.objects[final_loc].strength)
                        if np.random.random() < win_chance:
                            # agent wins
                            if verbose:
                                print('Agent {} won the fight against {}'
                                      .format(
                                          self.agents[idx].name,
                                          self.objects[final_loc].label))
                            self.agent_max_strengths[idx] += \
                                self.objects[final_loc].strength
                            self.agent_strengths[idx] = \
                                self.agent_max_strengths[idx]
                            del self.objects[final_loc]
                            for i in range(len(self.agents)):
                                if final_loc in self.agent_objects[i]:
                                    del self.agent_objects[i][final_loc]
                        else:
                            # agent loses
                            if verbose:
                                print('Agent {} lost the fight against {}'
                                      .format(
                                          self.agents[idx].name,
                                          self.objects[final_loc].label))
                            self.agent_strengths[idx] = 0
                if final_loc in self.dynamic_monsters:
                    # fight against the dynamic monster
                    # fight
                    win_chance = self.agent_strengths[idx] / \
                        (self.agent_strengths[idx] +
                            self.dynamic_monsters[final_loc].strength)
                    if np.random.random() < win_chance:
                        # agent wins
                        if verbose:
                            print('Agent {} won the fight against {}'.format(
                                self.agents[idx].name,
                                self.dynamic_monsters[final_loc].label))
                        self.agent_max_strengths[idx] += \
                            self.dynamic_monsters[final_loc].strength
                        self.agent_strengths[idx] = \
                            self.agent_max_strengths[idx]
                        del self.dynamic_monsters[final_loc]
                    else:
                        # agent loses
                        if verbose:
                            print('Agent {} lost the fight against {}'.format(
                                self.agents[idx].name,
                                self.dynamic_monsters[final_loc].label))
                        self.agent_strengths[idx] = 0

            for idx in range(len(self.agents)):
                self.agent_locations[idx] = self.agent_final_locs[idx]
                if self.agent_strengths[idx] <= 0:
                    print(f'Agent {self.agents[idx].name} has died!')
                    continue
                elif final_loc == self.goal_loc:
                    print(f'Agent {self.agents[idx].name} won the game!')
                    raise StopIteration('An agent won the game!')

            total_agent_strengths = np.sum(self.agent_strengths)
            if total_agent_strengths <= 0:
                raise StopIteration('All the agents have died!')

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
        walls = np.pad((self.game_map == utils.MapTiles.WALL), 1,
                       mode='constant', constant_values=1).astype(np.int32)
        nw_filters = np.asarray([[0, 0.5, 0], [0.5, 0, 0], [0] * 3])
        ne_filters = np.asarray([[0, 0.5, 0], [0, 0, 0.5], [0] * 3])
        se_filters = np.asarray([[0] * 3, [0, 0, 0.5], [0, 0.5, 0]])
        sw_filters = np.asarray([[0] * 3, [0.5, 0, 0], [0, 0.5, 0]])
        self.nwblocks = (signal.correlate2d(walls, nw_filters, mode='valid') >=
                         1).astype(np.int32)
        self.neblocks = (signal.correlate2d(walls, ne_filters, mode='valid') >=
                         1).astype(np.int32)
        self.seblocks = (signal.correlate2d(walls, se_filters, mode='valid') >=
                         1).astype(np.int32)
        self.swblocks = (signal.correlate2d(walls, sw_filters, mode='valid') >=
                         1).astype(np.int32)

        nonwall_indices = np.where(self.game_map != utils.MapTiles.WALL)
        # generate objects in the game map
        object_indices = np.random.choice(
            len(nonwall_indices[0]),
            self.num_monsters + self.num_powerups +
            self.num_dynamic_monsters + 1,  # extra for the boss
            replace=False)
        for cnt, idx in enumerate(object_indices[1:]):
            i = nonwall_indices[0][idx]
            j = nonwall_indices[1][idx]
            if cnt < self.num_powerups:
                self.objects[(i, j)] = utils.PowerUp()
            elif cnt < self.num_powerups + self.num_monsters:
                self.objects[(i, j)] = utils.StaticMonster()
            else:
                self.dynamic_monsters[(i, j)] = utils.DynamicMonster(i, j)

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

        if len(remaining_indices[0]) < len(self.agents):
            raise utils.InvalidMapError('Not enough empty tiles are left')

        # initial locations for agents
        for i in range(len(self.agents)):
            idx = np.random.choice(len(remaining_indices[0]))
            loc = (remaining_indices[0][idx], remaining_indices[1][idx])
            while (loc == self.goal_loc or
                   any(loc == prev_loc for prev_loc in self.agent_locations)):
                idx = np.random.choice(len(remaining_indices[0]))
                loc = (remaining_indices[0][idx], remaining_indices[1][idx])
            self.agent_locations.append(loc)

        for loc in self.agent_locations:
            wall_sum = self.nwblocks[loc[0], loc[1]] + \
                       self.neblocks[loc[0], loc[1]] + \
                       self.seblocks[loc[0], loc[1]] + \
                       self.swblocks[loc[0], loc[1]]
            if wall_sum >= 3:
                raise utils.InvalidMapError('The map is unsolvable')

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
        map_dict['dynamic_monsters'] = [
            [int(m.initial_i), int(m.initial_j)] for
            k, m in self.dynamic_monsters.items()]

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

        walls = np.pad((self.game_map == utils.MapTiles.WALL), 1,
                       mode='constant', constant_values=1).astype(np.int32)
        nw_filters = np.asarray([[0, 0.5, 0], [0.5, 0, 0], [0] * 3])
        ne_filters = np.asarray([[0, 0.5, 0], [0, 0, 0.5], [0] * 3])
        se_filters = np.asarray([[0] * 3, [0, 0, 0.5], [0, 0.5, 0]])
        sw_filters = np.asarray([[0] * 3, [0.5, 0, 0], [0, 0.5, 0]])
        self.nwblocks = (signal.correlate2d(walls, nw_filters, mode='valid') >=
                         1).astype(np.int32)
        self.neblocks = (signal.correlate2d(walls, ne_filters, mode='valid') >=
                         1).astype(np.int32)
        self.seblocks = (signal.correlate2d(walls, se_filters, mode='valid') >=
                         1).astype(np.int32)
        self.swblocks = (signal.correlate2d(walls, sw_filters, mode='valid') >=
                         1).astype(np.int32)

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

        for m in map_dict['dynamic_monsters']:
            self.dynamic_monsters[(m[0], m[1])] = \
                utils.DynamicMonster(m[0], m[1])

        self.agent_locations = [tuple(loc) for loc in
                                map_dict['agent_locations']]

    def display_map(self, agent_idx):
        ascii_dict = {utils.MapTiles.PATH: 'P', utils.MapTiles.SAND: 'S',
                      utils.MapTiles.MOUNTAIN: 'M', utils.MapTiles.WALL: 'W',
                      utils.MapTiles.UNKNOWN: 'U', 'other_agent': 'E',
                      'agent': 'X', 'dynamic_monster': 'D', 'monster': 'O',
                      'powerup': 'R', 'boss': 'B', 'deadagent': '-'}

        emoji_dict = {
            utils.MapTiles.UNKNOWN:
                em.emojize(':white_large_square:', use_aliases=True),
            utils.MapTiles.MOUNTAIN:
                em.emojize(':mountain:', use_aliases=True),
            utils.MapTiles.SAND:
                em.emojize(':palm_tree:', use_aliases=True),
            utils.MapTiles.PATH:
                em.emojize(':black_large_square:', use_aliases=True),
            utils.MapTiles.WALL:
                em.emojize(':construction:', use_aliases=True),
            'other_agent':
                em.emojize(':bust_in_silhouette:', use_aliases=True),
            'agent':
                em.emojize(':alien:', use_aliases=True),
            'dynamic_monster':
                em.emojize(':smiling_imp:', use_aliases=True),
            'monster':
                em.emojize(':imp:', use_aliases=True),
            'powerup':
                em.emojize(':heartpulse:', use_aliases=True),
            'boss':
                em.emojize(':guardsman:', use_aliases=True),
            'deadagent':
                em.emojize(':skull:', use_aliases=True)}

        printable_map = np.full(self.agent_maps[agent_idx].shape, "x")

        if self.map_type == 'ascii':
            chosen_dict = ascii_dict
        else:
            chosen_dict = emoji_dict

        for i in range(self.agent_maps[agent_idx].shape[0]):
            for j in range(self.agent_maps[agent_idx].shape[1]):
                if self.agent_locations[agent_idx] == (i, j):
                    printable_map[i, j] = chosen_dict['agent']
                elif (i, j) in self.agent_moving_objects[agent_idx]:
                    moving_obj = self.agent_moving_objects[agent_idx][(i, j)]
                    if isinstance(moving_obj, utils.AgentPlaceholder):
                        printable_map[i, j] = chosen_dict['other_agent']
                    if isinstance(moving_obj, utils.DynamicMonster):
                        printable_map[i, j] = chosen_dict['dynamic_monster']
                elif (i, j) in self.agent_objects[agent_idx]:
                    obj = self.agent_objects[agent_idx][(i, j)]
                    if isinstance(obj, utils.StaticMonster):
                        printable_map[i, j] = chosen_dict['monster']
                    elif isinstance(obj, utils.PowerUp):
                        printable_map[i, j] = chosen_dict['powerup']
                    elif isinstance(obj, utils.Boss):
                        printable_map[i, j] = chosen_dict['boss']
                else:
                    printable_map[i, j] = \
                        chosen_dict[self.agent_maps[agent_idx][i, j]]
        for i in range(self.agent_maps[agent_idx].shape[0]):
            print(' '.join(printable_map[i, :]))
        print()
