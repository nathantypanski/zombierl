from libtcod import libtcodpy as libtcod
import map_vars as M
import console as cons
import player as P

def render():
  libtcod.console_rect(cons.game_console, 0, 0, M.MAP_WIDTH, M.MAP_HEIGHT, True)
  for y in range (M.MAP_HEIGHT):
      for x in range (M.MAP_WIDTH):

        # Draw black for all areas the player has not seen yet
        if not M.gameworld[x][y].explored:
          libtcod.console_set_char_background(cons.game_console, x, y,
              libtcod.black, libtcod.BKGND_SET)

        # Draw all the floors.
        if M.gameworld[x][y].is_floor () and M.gameworld[x][y].explored:
          libtcod.console_set_char_background (cons.game_console, x, y,
              M.DARK_FLOOR_COLOR, libtcod.BKGND_SET)

        # Draw all the walls.
        elif M.gameworld[x][y].explored:
          libtcod.console_set_char_background(cons.game_console, x, y,
              M.DARK_WALL_COLOR, libtcod.BKGND_SET)

        # Draw all the light floors.
        if (libtcod.map_is_in_fov (P.player.fov, x, y)
           and libtcod.map_is_walkable (P.player.fov, x, y)):
          libtcod.console_set_char_background (cons.game_console, x, y,
              M.FLOOR_COLOR, libtcod.BKGND_SET)
          for item in M.gameworld[x][y].items:
            libtcod.console_set_default_foreground (cons.game_console, item.color)
            libtcod.console_put_char (cons.game_console, x, y,
                item.char, libtcod.BKGND_NONE)
          for character in M.gameworld[x][y].characters:
            libtcod.console_set_default_foreground (cons.game_console,
                character.color)
            libtcod.console_put_char (cons.game_console, x, y,
                character.char, libtcod.BKGND_NONE)
          M.gameworld[x][y].explored=True

        # Draw all the light walls.
        elif libtcod.map_is_in_fov (P.player.fov, x, y):
          libtcod.console_set_char_background (cons.game_console, x, y,
              M.WALL_COLOR, libtcod.BKGND_SET)
          M.gameworld[x][y].explored=True
  # Blits the game console to the root console.
  libtcod.console_blit(cons.game_console,0,0,M.MAP_WIDTH,M.MAP_HEIGHT,0,0,0,1)
