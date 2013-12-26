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
import math, random, pprint, os
pp = pprint.PrettyPrinter(indent=4)


##################
## Game objects ##
##################


class Player(C.Character):

  def __init__ (self, name, max_health, x, y, char, color, view_distance=10,
      strength=5, to_hit=0.8):
    self.name = name
    self.health = max_health
    self.max_health = max_health
    self.x = x
    self.y = y
    self.char = char
    self.color = color
    self.items = []
    self.equipped = list()
    self.hand = None
    self.view_distance = view_distance
    self.strength = strength
    self.to_hit = to_hit
    self.fov = libtcod.map_new(M.MAP_WIDTH, M.MAP_HEIGHT)
    self.npc = False
    self.exp = 0
    M.gameworld[self.x][self.y].characters.append(self)
    self.compute_fov()

  def move (self, dx, dy):
    if (M.gameworld [self.x + dx][self.y + dy].characters
    or not M.gameworld[self.x + dx][self.y + dy].is_floor()):
      characters = M.gameworld[self.x + dx][self.y + dy].characters
      if characters:
        for object in characters:
          self.attack(object)
    else:
      M.gameworld[self.x][self.y].characters.remove(self)
      self.x = self.x + dx
      self.y = self.y + dy
      M.gameworld[self.x][self.y].characters.append(self)
#      for item in M.gameworld[self.x][self.y].items:
#        add_status("A %s."% (item.name))
    self.compute_fov()

  def show_inventory(self):
    if self.items:
      count = item_selector(self.items, equipped=self.equipped)
      if not count == -1:
        item = self.items[count]
        if item.health:
          self.health = self.health+item.health.value
          if self.health > self.max_health:
            self.health = self.max_health
            S.add_status("%s health added." % (item.health.value))
          self.items.remove(item)
        else:
          if not item in self.equipped:
            self.equipped.append(item)
            S.add_status("%s equipped." % (item.name))
          else:
            S.add_status("%s unequipped." % (item.name))
            self.equipped.remove(item)


  def pick_up(self):
    if M.gameworld[self.x][self.y].items:
      if len(M.gameworld[self.x][self.y].items) > 1:
        count = item_selector(M.gameworld[self.x][self.y].items)
      else:
        count = 0
      if not count==-1:
        item = M.gameworld[self.x][self.y].items[count]
        M.gameworld[self.x][self.y].items.remove(item)
        if item.money:
          self.money = self.money + item.money.value
        else:
          self.items.append(item)
        S.add_status ("%s picked up %s." % (self.name, item.name))
    else:
      S.add_status ("Nothing to pick up!")

  def drop(self):
    if self.items:
      items = self.items[:]
      if self.equipped:
        for i in self.equipped:
          items.remove(i)
      if items:
        count = item_selector(items, title="DROP ITEM")
        if not count==-1:
          item = items[count]
          self.items.remove(item)
          M.gameworld[self.x][self.y].items.append(item)
          S.add_status("%s dropped %s." % (self.name, item.name))
      else:
        S.add_status("Nothing to drop!")

  # Aim and shoot the player's gun.
  def shoot(self):
    gun = -1
    for i in range(len(self.equipped)):
      if self.equipped[i].gun and self.equipped[i].gun.ammo > 0:
        gun = i
    if not gun==-1:
      class Target:
       def __init__(self, x, y):
          self.x = x
          self.y = y
      target = Target(self.x, self.y)
      libtcod.console_blit(cons.game_console,0,0,M.MAP_WIDTH,M.MAP_HEIGHT,0,0,0,1)
      libtcod.console_flush()
      key = libtcod.console_wait_for_keypress(True)
      while not key.vk == libtcod.KEY_SPACE:
        render()
        if key.pressed:
          if ord('k') == key.c:
            target.y=target.y-1
          elif ord('j') == key.c:
            target.y=target.y+1
          elif ord('h') == key.c:
            target.x=target.x-1
          elif ord('l') == key.c:
            target.x=target.x+1
          elif ord('y') == key.c:
            target.x=target.x-1
            target.y=target.y-1
          elif ord('u') == key.c:
            target.x=target.x+1
            target.y=target.y-1
          elif ord('i') == key.c:
            target.x=target.x-1
            target.y=target.y+1
          elif ord('o') == key.c:
            target.x=target.x+1
            target.y=target.y+1
        libtcod.line_init(self.x, self.y, target.x, target.y)
        x,y=libtcod.line_step()

        # Clear the console that shows our target line.
        libtcod.console_clear(cons.gun_console)
        # Draw the target line on the gun console.
        while (not x is None):
          if (M.gameworld[x][y].is_floor() and
              libtcod.map_is_in_fov (player.fov, x, y)
             ):
            libtcod.console_set_char_background(cons.gun_console, x, y,
                libtcod.white, libtcod.BKGND_OVERLAY)
            target.x=x
            target.y=y
            x,y=libtcod.line_step()
          else:
            break
        # Draw the gun console to the root console.
        libtcod.console_blit(cons.gun_console,0,0,M.MAP_WIDTH,M.MAP_HEIGHT,0,0,0,0,0.5)
        libtcod.console_flush()
        key = libtcod.console_wait_for_keypress(True)
      self.equipped[gun].gun.fire(self.x, self.y, target.x, target.y)
    else:
      S.add_status("No gun in hand!")

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
    libtcod.map_compute_fov (player.fov, x, y, int(player.view_distance*1.5),
                              True,libtcod.FOV_SHADOW)
    render()
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
    player.compute_fov()


#####################################
# Show player stats, item menus, etc
#####################################

def show_player_stats():
  global player
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
      %(player.name,player.health,player.max_health, player.view_distance,
        player.strength,player.to_hit,player.exp))
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
    render()

# Displays the parsed string as a status message to the user.
# Doesn't display strings larger than SCREEN_WIDTH yet.
def display_status ():
  if S.status:
    libtcod.console_rect(S.status_console, 0, 0, M.SCREEN_WIDTH,
        (M.SCREEN_HEIGHT - M.MAP_HEIGHT), True)
    libtcod.console_set_default_foreground (S.status_console, libtcod.white)
    while len(S.status) > M.SCREEN_WIDTH*2:
      display_statusline(S.status[:M.SCREEN_WIDTH*2])
      key = libtcod.console_wait_for_keypress(True)
      while not key.vk == libtcod.KEY_SPACE:
        key = libtcod.console_wait_for_keypress(True)
      S.status = S.status[M.SCREEN_WIDTH*2:]
    display_statusline(S.status)
    libtcod.console_blit(S.status_console,0,0,M.SCREEN_WIDTH,
        (M.SCREEN_HEIGHT-M.MAP_HEIGHT-1),0,0,M.MAP_HEIGHT+1,1)
    libtcod.console_flush()
  else:
    display_statusline()
    libtcod.console_flush()

def display_statusline (message=""):
  display_player_stats()
  for x in range (libtcod.console_get_width(S.status_console)):
    libtcod.console_put_char (S.status_console, x, 0, ' ', libtcod.BKGND_NONE)
    libtcod.console_put_char (S.status_console, x, 1, ' ', libtcod.BKGND_NONE)
    libtcod.console_print_rect_ex(S.status_console, 1, 0,
        M.SCREEN_WIDTH, 2, libtcod.BKGND_NONE, libtcod.LEFT,
        message[:M.SCREEN_WIDTH*2].strip())
  libtcod.console_blit(S.status_console,0,0,M.SCREEN_WIDTH,
      (M.SCREEN_HEIGHT-M.MAP_HEIGHT-1),0,0,M.MAP_HEIGHT+1,1)
  libtcod.console_flush()

def display_player_stats():
  libtcod.console_print_ex(S.status_console, 1, 2, libtcod.BKGND_NONE,
      libtcod.LEFT, player.name)
  libtcod.console_print_ex(S.status_console, len(player.name)+2, 2,
      libtcod.BKGND_NONE, libtcod.LEFT, "HP: %s/%s" % (player.health,
                                                       player.max_health))

#################
# Item functions
#################

# Takes an item and adds it to the current items list
def add_item(item):
  global tile_items
  tile_items.append(item)

# Add any items on the current player's tile to the available items list.
def add_items():
  for item in M.gameworld[player.x][player.y].items:
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
  while libtcod.map_is_in_fov (player.fov, x, y):
    x,y=find_open_tile()
  return [x,y]


# Gets the key input and updates the game.
def handle_keys (key):
  global player, turncount

  # Has a turn been accomplished?
  turn=False

  # Exit the game on escape.
  if libtcod.KEY_ESCAPE == key.vk:
    return True
  if player.health > 0:
    if ord('h') == key.c:
      player.move (-1, 0)
      turn = True
    elif ord('j') == key.c :
      player.move (0, 1)
      turn = True
    elif ord('k') == key.c :
      player.move (0, -1)
      turn = True
    elif ord('l') == key.c :
      player.move (1, 0)
      turn = True
    elif ord('y') == key.c :
      player.move (-1, -1)
      turn = True
    elif ord('u') == key.c :
      player.move (1, -1)
      turn = True
    elif ord('i') == key.c :
      player.move (-1, 1)
      turn = True
    elif ord('o') == key.c :
      player.move (1, 1)
      turn = True
    elif ord('c') == key.c :
      show_player_stats()
    elif ord(',') == key.c :
      player.pick_up()
    elif ord('.') == key.c :
      player.show_inventory()
    elif ord('d') == key.c :
      player.drop()
    elif ord('z') == key.c :
      player.shoot()
      turn = True
    if turn:
      # Move all enemies toward the player.
      characters = []
      for y in range (M.MAP_HEIGHT):
        for x in range (M.MAP_WIDTH):
            for character in M.gameworld[x][y].characters:
              characters.append(character)

      for character in characters:
        if character.npc and player.health > 0 and random.random() <= M.ZOMBIE_MOVE_CHANCE:
          path = libtcod.path_new_using_map(player.fov)
          # Compute the path between the hostile object and the player.
          libtcod.path_compute(path, character.x, character.y,
            player.x, player.y)
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
      if player.health < player.max_health:
        player.heatlh = player.health + 1
  ## Add items in the current tile to the status.
  # for item in M.gameworld[player.x][player.y].items:
  #       add_status("A %s."% (item.name))
  ## Add items in the current tile to the items indicator.
  add_items()
  # Render events.
  render()
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


def render():
  global bsp_map, firstRun
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
        if (libtcod.map_is_in_fov (player.fov, x, y)
           and libtcod.map_is_walkable (player.fov, x, y)):
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
        elif libtcod.map_is_in_fov (player.fov, x, y):
          libtcod.console_set_char_background (cons.game_console, x, y,
              M.WALL_COLOR, libtcod.BKGND_SET)
          M.gameworld[x][y].explored=True
  # Blits the game console to the root console.
  libtcod.console_blit(cons.game_console,0,0,M.MAP_WIDTH,M.MAP_HEIGHT,0,0,0,1)


# Places the player character on a non-wall tile.
def place_player():
  x,y = find_open_tile()
  global player
  player = Player ('Player', 500, x, y, "@", libtcod.white,
      view_distance = 15)
  Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))
  #Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))

S.status=""
libtcod.console_set_alignment(S.status_console, libtcod.LEFT)

# Contains a list of items on the player's current tile
tile_items = list()

# This is the first run of the game.
firstRun = True
turncount = 0
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
    display_status()
    render()
    draw_items()
    clear_items()

  if handle_keys (key):
    break
  firstRun = False
  libtcod.console_flush ()
