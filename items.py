from libtcod import libtcodpy as libtcod
import map_vars as M
import console as cons

def item_selector(items, default=None, equipped=[], title="INVENTORY"):
  libtcod.console_clear(cons.menu_console)
  libtcod.console_set_default_background(cons.menu_console, libtcod.black)
  libtcod.console_set_default_foreground(cons.menu_console, libtcod.white)
  libtcod.console_rect(cons.menu_console, 0, 0, M.MAP_WIDTH, M.MAP_HEIGHT, True)
  libtcod.console_print_ex(cons.menu_console,
      40, 0, libtcod.BKGND_NONE, libtcod.CENTER, title)
  libtcod.console_print_ex(cons.menu_console,
      1, M.SCREEN_HEIGHT-1, libtcod.LEFT,
    libtcod.BKGND_NONE,
    "[j / k]: Highlight item     [SPACEBAR]: Select     [q]: quit")
  count = 0
  for item in items:
    libtcod.console_print_ex(cons.menu_console,
        1, count+3, libtcod.BKGND_NONE, libtcod.LEFT, item.name)
    if item in equipped:
      libtcod.console_print_ex(cons.menu_console,
          libtcod.console_get_width(cons.menu_console)-1,
          count+3,
          libtcod.BKGND_NONE,
          libtcod.RIGHT,
          "(EQUIPPED)")
    count = count + 1
  if default:
    count = items.index(default)
  else:
    count = count -1
  key = libtcod.console_check_for_keypress(True)
  while not key.vk == libtcod.KEY_SPACE and not ord('q') == key.c:

    for i in range(len(items[count].name)):
      libtcod.console_set_char_background(cons.menu_console,
          i+1,
          count+3,
          libtcod.white)
      libtcod.console_set_char_foreground(cons.menu_console,
          i+1,
          count+3,
          libtcod.black)
    if key.pressed and key.c == ord('k') and count > 0:
      for i in range(len(items[count].name)):
        libtcod.console_set_char_background(cons.menu_console,
            i+1,
            count+3,
            libtcod.black)
        libtcod.console_set_char_foreground(cons.menu_console,
            i+1,
            count+3,
            libtcod.white)
      count = count -1
    elif key.pressed and key.c == ord('j') and count < len(items)-1:
      for i in range(len(items[count].name)):
        libtcod.console_set_char_background(cons.menu_console,
            i+1,
            count+3,
            libtcod.black)
        libtcod.console_set_char_foreground(cons.menu_console,
            i+1,
            count+3,
            libtcod.white)
      count = count +1
    key = libtcod.console_check_for_keypress(True)
    libtcod.console_blit(cons.menu_console,0,0,M.SCREEN_WIDTH,M.SCREEN_HEIGHT,0,0,0,1)
    libtcod.console_flush()

  if ord('q') == key.c:
    count=-1

  return count
