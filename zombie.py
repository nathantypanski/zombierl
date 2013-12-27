#!/usr/bin/python

#  zombie.py is a simple zombie-themed roguelike game.
#  Copyright (C) 2013  Nathan Typanski
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from libtcod import libtcodpy as libtcod
import bspgen
import character as C
import object as O
import map_vars as M
import status as S
import console as cons
import player as P
import rendering as R
import math
import random
import pprint
import os
pp = pprint.PrettyPrinter(indent=4)

##################
## Game objects ##
##################

class Item (O.Object):
  def __init__ (self,
                name,
                x, y,
                char,
                color,
                gun=None,
                money=None,
                health=None):
    self.name = name
    self.x = x
    self.y = y
    self.char = char
    self.color = color
    self.gun = gun
    self.money = money
    self.health = health
    M.gameworld[self.x][self.y].items.append(self)
    if self.gun:
      self.gun.owner = self
      self.name = self.name + ' (' + str(self.gun.ammo) + ')'
      if self.money:
        self.money.owner = self
        if self.health:
          self.health.owner = self


class Health ():
  def __init__ (self, value):
    self.value=value


class Money ():
  def __init__ (self, value):
    self.value = value


class Gun ():
  def __init__ (self, damage=10, accuracy=0.5, ammo=15):
    self.damage = damage
    self.accuracy = accuracy
    self.ammo=ammo

  def fire(self, x, y, dx, dy):
    # The distance this bullet has traveled.
    steps = 0
    shot_accuracy=self.accuracy
    libtcod.map_compute_fov (P.player.fov, x, y, int(P.player.view_distance*1.5),
                             True,libtcod.FOV_SHADOW)
    R.render()
    libtcod.line_init(x, y, dx, dy)
    lx,ly=libtcod.line_step()
    while (not lx is None):
      steps = steps + 1
      if not M.gameworld[lx][ly].characters:
        libtcod.console_set_char_background(
          cons.game_console,
          lx,
          ly,
          libtcod.white,
          libtcod.BKGND_OVERLAY)
        libtcod.console_blit(cons.game_console,0,0,M.MAP_WIDTH,M.MAP_HEIGHT,0,0,0,1)
        libtcod.console_flush()
        lx,ly=libtcod.line_step()
      else:
        if random.random() <= shot_accuracy:
          S.add_status("You hit!")
          libtcod.console_set_char_background(
            cons.game_console,
            lx,
            ly,
            libtcod.red,
            libtcod.BKGND_OVERLAY)
          libtcod.console_blit(cons.game_console,0,0,M.MAP_WIDTH,M.MAP_HEIGHT,0,0,0,1)
          libtcod.console_flush()
          M.gameworld[lx][ly].characters[-1].take_damage(
            int(self.damage*random.uniform(self.accuracy, 1.0)))
        else:
          S.add_status("You fire and miss!")
          break
          self.ammo = self.ammo-1
          self.owner.name = self.owner.name.rsplit('(')[0] + '(' + str(self.ammo) + ')'
          P.player.compute_fov()


#####################################
# Show player stats, item menus, etc
#####################################

def show_player_stats():
  player_stats=libtcod.console_new(20,20)
  libtcod.console_set_default_background(player_stats,libtcod.darkest_grey)
  libtcod.console_set_default_foreground(player_stats, libtcod.white)
  #  libtcod.console_clear(player_stats)
  libtcod.console_print_frame(player_stats,
                              0, 0,
                              libtcod.console_get_width(player_stats),
                              libtcod.console_get_height(player_stats),
                              clear=True)
  height=0
  libtcod.console_print_rect(player_stats, 1, 1,
                             libtcod.console_get_width(player_stats)-2,
                             libtcod.console_get_height(player_stats)-2,
                             "Name: %s \nHealth: %s/%s\nView distance: %s\nStrength: %s\nTo hit: %s\nExp: %s"#
                             %(P.player.name,P.player.health,P.player.max_health, P.player.view_distance,
                               P.player.strength,P.player.to_hit,P.player.exp))
  libtcod.console_print_ex(player_stats,
                           libtcod.console_get_width(player_stats)//2,
                           0,
                           libtcod.BKGND_DEFAULT,
                           libtcod.CENTER,
                           "Player Stats")
  libtcod.console_print_ex(player_stats,
                           libtcod.console_get_width(player_stats)//2,
                           libtcod.console_get_height(player_stats)-1,
                           libtcod.BKGND_DEFAULT,
                           libtcod.CENTER,
                           "[spacebar]")
  libtcod.console_blit(player_stats,0,0,
                       libtcod.console_get_width(player_stats),
                       libtcod.console_get_height(player_stats),
                       0,5,5,
                       1.0,0.1)
  key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)
  while not (libtcod.KEY_SPACE==key.vk):
    key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)
    libtcod.console_blit(player_stats,0,0,
                         libtcod.console_get_width(player_stats),
                         libtcod.console_get_height(player_stats),
                         0,5,5,
                         1.0,0.1)
    libtcod.console_flush()
    R.render()

#################
# Item functions
#################

# Takes an item and adds it to the current items list
def add_item(item):
  global tile_items
  tile_items.append(item)

# Add any items on the current player's tile to the available items list.
def add_items():
  for item in M.gameworld[P.player.x][P.player.y].items:
    add_item(item)

# Returns True if there are items on the player's current tile.
def items_here():
  global tile_items
  if tile_items:
    return True
    return False

def current_items():
  global tile_items
  return tile_items


# Resets the items list for the current title, called e.g. when the player
# moves to a new tile.
def clear_items():
  global tile_items
  tile_items = list()


# Draws the current items list to the screen
def draw_items():
  height = 0
  libtcod.console_set_default_background(cons.items_console, libtcod.red)
  libtcod.console_set_default_foreground(cons.items_console, libtcod.white)
  libtcod.console_clear(cons.items_console)
  for item in tile_items:
    height+=libtcod.console_print_rect_ex(cons.items_console,
                                          0,
                                          height,
                                          libtcod.console_get_width(cons.items_console),
                                          libtcod.console_get_height(cons.items_console),
                                          libtcod.BKGND_NONE,
                                          libtcod.LEFT,
                                          item.name)

  libtcod.console_blit(cons.items_console,0,0,
                       libtcod.console_get_width(cons.items_console),
                       height,
                       0,1,1,
                       1.0,0.5)
  libtcod.console_flush()

############
# Game run #
############


# Returns an unoccupied tile.
def find_open_tile():
  x = random.randint(0,M.MAP_WIDTH-1)
  y = random.randint(0,M.MAP_HEIGHT-1)
  while not M.gameworld[x][y].is_floor() or M.gameworld[x][y].characters:
    x = random.randint(0,M.MAP_WIDTH-1)
    y = random.randint(0,M.MAP_HEIGHT-1)
    return [x,y]


# Returns an open tile that the player can't see.
def find_blind_open_tile():
  x,y=find_open_tile()
  while libtcod.map_is_in_fov (P.player.fov, x, y):
    x,y=find_open_tile()
    return [x,y]


# Gets the key input and updates the game.
def handle_keys (key):
  global turncount

  # Has a turn been accomplished?
  turn=False

  # Exit the game on escape.
  if libtcod.KEY_ESCAPE == key.vk:
    return True
    if P.player.health > 0:
      if ord('h') == key.c:
        P.player.move (-1, 0)
        turn = True
      elif ord('j') == key.c :
        P.player.move (0, 1)
        turn = True
      elif ord('k') == key.c :
        P.player.move (0, -1)
        turn = True
      elif ord('l') == key.c :
        P.player.move (1, 0)
        turn = True
      elif ord('y') == key.c :
        P.player.move (-1, -1)
        turn = True
      elif ord('u') == key.c :
        P.player.move (1, -1)
        turn = True
      elif ord('i') == key.c :
        P.player.move (-1, 1)
        turn = True
      elif ord('o') == key.c :
        P.player.move (1, 1)
        turn = True
      elif ord('c') == key.c :
        show_player_stats()
      elif ord(',') == key.c :
        P.player.pick_up()
      elif ord('.') == key.c :
        P.player.show_inventory()
      elif ord('d') == key.c :
        P.player.drop()
      elif ord('z') == key.c :
        P.player.shoot()
        turn = True
        if turn:
          # Move all enemies toward the player.
          characters = []
          for y in range (M.MAP_HEIGHT):
            for x in range (M.MAP_WIDTH):
              for character in M.gameworld[x][y].characters:
                characters.append(character)

      for character in characters:
        if character.npc and P.player.health > 0 and random.random() <= M.ZOMBIE_MOVE_CHANCE:
          path = libtcod.path_new_using_map(P.player.fov)
          # Compute the path between the hostile object and the player.
          libtcod.path_compute(path, character.x, character.y,
                               P.player.x, P.player.y)
          if libtcod.path_size(path) < 100:
            libtcod.path_walk(path, True)
            character.move_to_coordinates(libtcod.path_get_origin(path)[0],
                                          libtcod.path_get_origin(path)[1])
            #spawn a new zombie
            if random.random() <= M.ENEMY_SPAWN_CHANCE:
              x,y=find_blind_open_tile()
              C.Character('Zombie',
                          random.randint(5,20),
                          x, y,
                          "Z",
                          libtcod.black,
                          npc=True)
              if random.random() <= 0.20:
                Item ('cheap revolver', x, y, 'r', libtcod.red, gun=Gun(5, 0.6))
                M.gameworld[x][y].characters[0].pick_up()
                if random.random() <= 0.02:
                  Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))
                  M.gameworld[x][y].characters[0].pick_up()
                  if random.random() <= 0.10:
                    Item ('medkit', x, y, 'H', libtcod.red, health=Health(100))
                    M.gameworld[x][y].characters[0].pick_up()
                    turncount = turncount + 1
                    if P.player.health < P.player.max_health:
                      P.player.health = P.player.health + 1
                      ## Add items in the current tile to the status.
                      # for item in M.gameworld[player.x][player.y].items:
                      #       add_status("A %s."% (item.name))
                      ## Add items in the current tile to the items indicator.
                      add_items()
                      # Render events.
                      R.render()
                      # Clear the status string.
                      if turn:
                        S.clear_status()
                        # If there are items on the player's current tile, draw them to the screen.
                        if items_here():
                          draw_items()
                          # Clear the list of current tile items.
                          clear_items()
                          # Return False if the game should still play.
                          return False


# Places the player character on a non-wall tile.
def place_player():
  x,y = find_open_tile()
  P.player = P.Player ('Player', 500, x, y, "@", libtcod.white,
                       view_distance = 15)
  Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))
  #Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))

# Contains a list of items on the player's current tile
tile_items = list()

# This is the first run of the game.
firstRun = True
turncount = 0

## Changes the keyboard repeat delay.
# libtcod.console_set_keyboard_repeat(0, 0)
###############
## Game loop ##
###############

while not libtcod.console_is_window_closed ():
  if not firstRun:
    key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)
    #key = libtcod.console_wait_for_keypress(True)
  else:
    # If this is the first run of the game, then build a game world and place
    # the player on it.
    key = libtcod.console_check_for_keypress()
    #    M.gameworld = [[Tile(floor=False) for y in range (M.MAP_HEIGHT)]
    #        for x in range (M.MAP_WIDTH)]
    bsp = bspgen.Bsp(M.MAP_WIDTH,M.MAP_HEIGHT, M.gameworld)
    bsp.render_bsp()
    place_player()
    add_items()
    S.display_status()
    R.render()
    draw_items()
    clear_items()

  if handle_keys (key):
    break
    firstRun = False
    libtcod.console_flush ()
