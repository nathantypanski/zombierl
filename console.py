import os

from libtcod import libtcodpy as libtcod

import map_vars as M

# Set the fps.
libtcod.sys_set_fps(45)
# Font path
font = os.path.join(b'data', b'fonts', b'consolas10x10_gs_tc.png')
# Set the custom font.
libtcod.console_set_custom_font(font,
                                libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
# Initialize the root console.
libtcod.console_init_root (M.SCREEN_WIDTH, M.SCREEN_HEIGHT, b'zombie.py', False)
# Create the game console.
game_console = libtcod.console_new(M.MAP_WIDTH, M.MAP_HEIGHT)
gun_console  = libtcod.console_new(M.MAP_WIDTH, M.MAP_HEIGHT)
# Make the background of gun_console transparent on black.
libtcod.console_set_key_color(gun_console,libtcod.black)
# Create an items console
items_console = libtcod.console_new(30, 40)
menu_console = libtcod.console_new(M.SCREEN_WIDTH, M.SCREEN_HEIGHT)
