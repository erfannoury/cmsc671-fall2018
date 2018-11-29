import os
import sys
from argparse import ArgumentParser

from agent import RandomAgent
from agent import HumanAgent
from driver import GameDriver


def main(args):
    parser = ArgumentParser(description='')

    parser.add_argument('--height', type=int, required=True,
                        help='Heigth of the map')
    parser.add_argument('--width', type=int, required=True,
                        help='Width of the map')
    parser.add_argument('--num-powerups', type=int, required=True,
                        help='Number of powerups to put in the game map')
    parser.add_argument('--num-monsters', type=int, required=True,
                        help='Number of monsters to put in the game map')
    parser.add_argument('--initial-strength', default=100, type=int,
                        help='Initial strength of each agent')
    parser.add_argument('--save-dir', type=str,
                        help='Save directory for saving the map')
    parser.add_argument('--map-file', type=str,
                        help='Path to the map JSON file')
    parser.add_argument('--verbose', action='store_true',
                        help='Whether to be verbose when playing game')

    args = parser.parse_args(args)

    # TODO: Change how agents are populated
    agent = RandomAgent()	# <-- change this to switch agents, for now

    game_driver = GameDriver(
        height=args.height, width=args.width,
        num_powerups=args.num_powerups,
        num_monsters=args.num_monsters,
        agents=[agent],
        initial_strength=args.initial_strength,
        save_dir=args.save_dir, map_file=args.map_file)

    print('Starting game')
    game_driver.play(verbose=args.verbose)


if __name__ == '__main__':
    main(sys.argv[1:])
