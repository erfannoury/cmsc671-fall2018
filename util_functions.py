from utils import MapTiles
from utils import Directions
import emoji as em
import numpy as np

MAP_TYPES = ['ascii', 'emoji']


def map_to_text(game_map, type='a'):
    """
    Convert a map in the game format to something human-readable.
    By default, prints an ASCII map, 'a' for ASCII, 'u' for Unicode,
    'e' for emoji, 'c' for color-coded ASCII. ASCII should work for anything.
    """
    ascii_dict = {MapTiles.PATH: 'P', MapTiles.SAND: 'S',
                  MapTiles.MOUNTAIN: 'M', MapTiles.WALL: 'W',
                  MapTiles.UNKNOWN: 'U'}

    emoji_dict = {
        MapTiles.UNKNOWN: em.emojize(':white_large_square:'),
        MapTiles.MOUNTAIN: em.emojize(':mountain:'),
        MapTiles.SAND: em.emojize(':palm_tree:'),
        MapTiles.PATH: em.emojize(':motorway:'),
        MapTiles.WALL: em.emojize(':construction:', use_aliases=True)}

    printable_map = np.full((len(game_map), len(game_map[0])), "x")

    assert type in MAP_TYPES
    if type == 'ascii':
        chosen_dict = ascii_dict
    elif type == 'colorascii':
        raise NotImplementedError(
            'Color ASCII map display not yet implemented')
        # chosen_dict = color_ascii_dict
    elif type == 'unicode':
        raise NotImplementedError('Unicode map display not yet implemented')
        # chosen_dict = unicode_dict
    elif type == 'emoji':
        chosen_dict = emoji_dict

    for i in range(len(game_map)):
        for j in range(len(game_map[i])):
            printable_map[i][j] = chosen_dict[game_map[i][j]]

    return printable_map


def print_map(game_map, type='ascii'):
    """
    Takes a game map populated with map values, prints that map to terminal.
    Can optionally take an argument specifying the type of character printed
    (ascii, emoji, colorascii, or unicode).
    """
    printable_map = map_to_text(game_map, type)
    for i in range(len(game_map)):
        row = ""
        for j in range(len(game_map[i])):
            row += printable_map[i][j]
            row += ' '
        print(row)
