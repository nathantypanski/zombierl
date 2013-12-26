from libtcod import libtcodpy as libtcod
import tile as T

# size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# These variables contain the size of the game map.
MAP_WIDTH = 80
MAP_HEIGHT = 40

# These are the lightened tile colors.
WALL_COLOR = libtcod.Color (95, 95, 95)
FLOOR_COLOR = libtcod.Color (127, 127, 127)
DOOR_COLOR = libtcod.orange

# These are the darkened tile colors.
DARK_WALL_COLOR = libtcod.Color (31, 31, 31)
DARK_FLOOR_COLOR = libtcod.Color(63, 63, 63)
DARK_DOOR_COLOR = libtcod.dark_orange


# Settings
ENEMY_SPAWN_CHANCE = 0.15
ZOMBIE_MOVE_CHANCE = 0.5

gameworld = [[T.Tile(floor=False) for y in range (MAP_HEIGHT)]
        for x in range (MAP_WIDTH)]
