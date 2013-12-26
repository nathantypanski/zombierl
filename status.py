from libtcod import libtcodpy as libtcod
import map_vars as M

# Create the game status console.
status = ''
status_console = libtcod.console_new(M.SCREEN_WIDTH, (M.SCREEN_HEIGHT - M.MAP_HEIGHT))

def add_status (new_status):
  global status
  status = ("%s %s" % (status, new_status))
#  display_status()

def clear_status ():
  status = ""
