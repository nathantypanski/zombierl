from libtcod import libtcodpy as libtcod
import console as cons
#import player as P
import map_vars as M

# Create the game status console.
status = ''
status_console = libtcod.console_new(M.SCREEN_WIDTH, (M.SCREEN_HEIGHT - M.MAP_HEIGHT))
libtcod.console_set_alignment(status_console, libtcod.LEFT)

def add_status (new_status):
  global status
  status = ("%s %s" % (status, new_status))
  display_status()

def clear_status ():
  global status
  status = ""

# Displays the parsed string as a status message to the user.
# Doesn't display strings larger than SCREEN_WIDTH yet.
def display_status ():
  global status
  if status:
    libtcod.console_rect(status_console, 0, 0, M.SCREEN_WIDTH,
        (M.SCREEN_HEIGHT - M.MAP_HEIGHT), True)
    libtcod.console_set_default_foreground (status_console, libtcod.white)
    while len(status) > M.SCREEN_WIDTH*2:
      display_statusline(status[:M.SCREEN_WIDTH*2])
      key = libtcod.console_wait_for_keypress(True)
      while not key.vk == libtcod.KEY_SPACE:
        key = libtcod.console_wait_for_keypress(True)
      status = status[M.SCREEN_WIDTH*2:]
    display_statusline(status)
    libtcod.console_blit(status_console,0,0,M.SCREEN_WIDTH,
        (M.SCREEN_HEIGHT-M.MAP_HEIGHT-1),0,0,M.MAP_HEIGHT+1,1)
    libtcod.console_flush()
  else:
    display_statusline()
    libtcod.console_flush()

def display_statusline (message=""):
  global status
#  display_player_stats()
  for x in range (libtcod.console_get_width(status_console)):
    libtcod.console_put_char (status_console, x, 0, ' ', libtcod.BKGND_NONE)
    libtcod.console_put_char (status_console, x, 1, ' ', libtcod.BKGND_NONE)
    libtcod.console_print_rect_ex(status_console, 1, 0,
        M.SCREEN_WIDTH, 2, libtcod.BKGND_NONE, libtcod.LEFT,
        message[:M.SCREEN_WIDTH*2].strip())
  libtcod.console_blit(status_console,0,0,M.SCREEN_WIDTH,
      (M.SCREEN_HEIGHT-M.MAP_HEIGHT-1),0,0,M.MAP_HEIGHT+1,1)
  libtcod.console_flush()

  # Removed because of mutual imports
#def display_player_stats():
#  global status
#  libtcod.console_print_ex(status_console, 1, 2, libtcod.BKGND_NONE,
#      libtcod.LEFT, P.player.name)
#  libtcod.console_print_ex(status_console, len(P.player.name)+2, 2,
#      libtcod.BKGND_NONE, libtcod.LEFT, "HP: %s/%s" % (P.player.health,
#                                                       P.player.max_health))
