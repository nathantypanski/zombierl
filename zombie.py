#!/usr/bin/python3
import libtcodpy as libtcod
import math, random, pprint, os
pp = pprint.PrettyPrinter(indent=4)

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

# Set the fps.
libtcod.sys_set_fps(45)

# Font path
font = os.path.join(b'data', b'fonts', b'consolas10x10_gs_tc.png')
# Set the custom font.
libtcod.console_set_custom_font(font,
    libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
# Initialize the root console.
libtcod.console_init_root (SCREEN_WIDTH, SCREEN_HEIGHT, b'zombie.py', False)
# Create the game console.
game_console = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
# Create the game status console.
status_console = libtcod.console_new(SCREEN_WIDTH, (SCREEN_HEIGHT - MAP_HEIGHT))
# Create an items console
items_console = libtcod.console_new(30, 40)
menu_console = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

##################
## Game objects ##
##################

# This is a gameworld tile object.
class Tile:
  def __init__ (self, floor=True):
    self.floor = floor
    self.characters = []
    self.items = []
    self.explored = False

  # This returns true if the tile is blocked (i.e. it is a wall),
  # otherwise it returns false.
  def is_floor (self):
    return self.floor

  # This blocks the tile.
  def block (self):
    self.floor = False

  def unblock (self):
    self.floor = True

# This is a generic game object.
class Object:

  def __init__ (self, name, x, y, char, color):
    self.name = name
    self.x = x
    self.y = y
    self.char = char
    self.color = color
    gameworld[self.x][self.y].items.append(self)

  def is_hostile (self):
    return False

  def get_x (self):
    return self.x

  def get_y (self):
    return self.y

class Character (Object):

  def __init__ (self, name, max_health, x, y, char, color, npc=False,
      strength=5, to_hit=0.8):
    self.name = name
    self.health = max_health
    self.max_health = max_health
    self.x = x
    self.y = y
    self.char = char
    self.color = color
    self.items = []
    self.hand = None
    self.npc = npc
    self.strength = strength
    self.to_hit = to_hit
    gameworld[self.x][self.y].characters.append(self)

  def move (self, dx, dy):
    if gameworld[self.x + dx][self.y + dy].characters or not gameworld[self.x + dx][self.y + dy].is_floor():
      characters = gameworld[self.x + dx][self.y + dy].characters
      if characters:
        for character in characters:
          if not character.npc:
            self.attack(character)
    else:
      gameworld[self.x][self.y].characters.remove(self)
      self.x = self.x + dx
      self.y = self.y + dy
      gameworld[self.x][self.y].characters.append(self)

  def pick_up(self):
    if gameworld[self.x][self.y].items:
      item = gameworld[self.x][self.y].items.pop()
      self.items.append(item)

  def drop(self):
    if self.items:
      item = self.items.pop()
      gameworld[self.x][self.y].items.append(item)

  def drop_all(self):
    for item in self.items:
      self.items.remove(item)
      gameworld[self.x][self.y].items.append(item)

  # Moves toward coordinates. Only moves one step.
  def move_to_coordinates (self, dx, dy):
    if dx > self.x:
      newx = 1
    elif dx < self.x:
      newx = -1
    else:
      newx = 0
    if dy > self.y:
      newy = 1
    elif dy < self.y:
      newy = -1
    else:
      newy = 0
    self.move(newx, newy)

  # Set the character's health.
  def set_health (self, health):
    self.health = health

  def attack (self, character):
    damage = self.strength*random.randint(self.strength//2, self.strength*2)
    if random.random() <= self.to_hit:
      add_status("%s hits %s!" % (self.name, character.name))
      if damage > (0.5*character.max_health):
        add_status("It's super effective!")
      character.take_damage(damage)
    else:
      add_status("%s swings and misses." % (self.name))

  def take_damage (self, damage):
    self.health -= damage

    if 0 > self.health:
      add_status("%s is killed!" % (self.name))
      self.health = 0
      gameworld[self.x][self.y].characters.remove(self)
      self.drop_all()

class Player(Character):

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
    self.fov = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    self.npc = False
    self.exp = 0
    gameworld[self.x][self.y].characters.append(self)
    self.compute_fov()

  def move (self, dx, dy):
    if gameworld[self.x + dx][self.y + dy].characters or not gameworld[self.x + dx][self.y + dy].is_floor():
      characters = gameworld[self.x + dx][self.y + dy].characters
      if characters:
        for object in characters:
          self.attack(object)
    else:
      gameworld[self.x][self.y].characters.remove(self)
      self.x = self.x + dx
      self.y = self.y + dy
      gameworld[self.x][self.y].characters.append(self)
#      for item in gameworld[self.x][self.y].items:
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
            add_status("%s health added." % (item.health.value))
          self.items.remove(item)
        else:
          if not item in self.equipped:
            self.equipped.append(item)
            add_status("%s equipped." % (item.name))
          else:
            add_status("%s unequipped." % (item.name))
            self.equipped.remove(item)

  def compute_fov(self):
    for x in range (MAP_WIDTH):
      for y in range (MAP_HEIGHT):
        if gameworld[x][y].is_floor():
         libtcod.map_set_properties (self.fov, x , y, True, True)
    libtcod.map_compute_fov (self.fov, self.x, self.y, self.view_distance,
                            True,libtcod.FOV_DIAMOND)

  def pick_up(self):
    if gameworld[self.x][self.y].items:
      if len(gameworld[self.x][self.y].items) > 1:
        count = item_selector(gameworld[self.x][self.y].items)
      else:
        count = 0
      if not count==-1:
        item = gameworld[self.x][self.y].items[count]
        gameworld[self.x][self.y].items.remove(item)
        if item.money:
          self.money = self.money + item.money.value
        else:
          self.items.append(item)
        add_status ("%s picked up %s." % (self.name, item.name))
    else:
      add_status ("Nothing to pick up!")
#
#  def drop(self):
#    if self.items:
#      items = self.items[:]
#      if self.hand:
#        items.remove(self.hand)
#      if items:
#        item = item_selector(items)
#        if item:
#          self.items.remove(item)
#          gameworld[self.x][self.y].items.append(item)
#          add_status("%s dropped %s." % (self.name, item.name))
#      else:
#        add_status("Nothing to drop!")
#
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
      libtcod.console_blit(game_console,0,0,MAP_WIDTH,MAP_HEIGHT,0,0,0,1)
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
        while (not x is None):
          if gameworld[x][y].is_floor() and libtcod.map_is_in_fov (player.fov, x, y):
            libtcod.console_set_char_background(game_console, x, y,
                libtcod.white, libtcod.BKGND_OVERLAY)
            target.x=x
            target.y=y
            x,y=libtcod.line_step()
          else:
            break
        libtcod.console_blit(game_console,0,0,MAP_WIDTH,MAP_HEIGHT,0,0,0,1)
        libtcod.console_flush()
        key = libtcod.console_wait_for_keypress(True)
      self.equipped[gun].gun.fire(self.x, self.y, target.x, target.y)
    else:
      add_status("No gun in hand!")


class Item (Object):
  def __init__ (self, name, x, y, char, color, gun=None, money=None, health=None):
    self.name = name
    self.x = x
    self.y = y
    self.char = char
    self.color = color
    self.gun = gun
    self.money = money
    self.health = health
    gameworld[self.x][self.y].items.append(self)
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
      if not gameworld[lx][ly].characters:
        libtcod.console_set_char_background(game_console, lx, ly, libtcod.white, libtcod.BKGND_OVERLAY)
        libtcod.console_blit(game_console,0,0,MAP_WIDTH,MAP_HEIGHT,0,0,0,1)
        libtcod.console_flush()
        lx,ly=libtcod.line_step()
      else:
        if random.random() <= shot_accuracy:
          add_status("You hit!")
          gameworld[lx][ly].characters[-1].take_damage(int(self.damage*random.uniform(self.accuracy, 1.0)))
        else:
          add_status("You fire and miss!")
        break
    self.ammo = self.ammo-1
    self.owner.name = self.owner.name.rsplit('(')[0] + '(' + str(self.ammo) + ')'
    player.compute_fov()
#########################
# BEGIN bsp sample code #
#########################
bsp_depth = 8
bsp_min_room_size = 10
# a room fills a random part of the node or the maximum available space ?
bsp_random_room = True
# if true, there is always a wall on north & west side of a room
bsp_room_walls = True
bsp_map = None
gameworld = [[Tile(floor=False) for y in range (MAP_HEIGHT)]
                for x in range (MAP_WIDTH)]
# draw a vertical line
def vline(m, x, y1, y2):
    if y1 > y2:
        y1,y2 = y2,y1
    for y in range(y1,y2+1):
        m[x][y] = True

# draw a vertical line up until we reach an empty space
def vline_up(m, x, y):
    while y >= 0 and not m[x][y]:
        m[x][y] = True
        y -= 1

# draw a vertical line down until we reach an empty space
def vline_down(m, x, y):
    while y < MAP_HEIGHT and not m[x][y]:
        m[x][y] = True
        y += 1

# draw a horizontal line
def hline(m, x1, y, x2):
    if x1 > x2:
        x1,x2 = x2,x1
    for x in range(x1,x2+1):
        m[x][y] = True

# draw a horizontal line left until we reach an empty space
def hline_left(m, x, y):
    while x >= 0 and not m[x][y]:
        m[x][y] = True
        x -= 1

# draw a horizontal line right until we reach an empty space
def hline_right(m, x, y):
    while x < MAP_WIDTH and not m[x][y]:
        m[x][y]=True
        x += 1

# the class building the dungeon from the bsp nodes
def traverse_node(node, dat):
    global bsp_map
    if libtcod.bsp_is_leaf(node):
        # calculate the room size
        minx = node.x + 1
        maxx = node.x + node.w - 1
        miny = node.y + 1
        maxy = node.y + node.h - 1
        if not bsp_room_walls:
            if minx > 1:
                minx -= 1
            if miny > 1:
                miny -=1
        if maxx == MAP_WIDTH - 1:
            maxx -= 1
        if maxy == MAP_HEIGHT - 1:
            maxy -= 1
        if bsp_random_room:
            minx = libtcod.random_get_int(None, minx, maxx - bsp_min_room_size + 1)
            miny = libtcod.random_get_int(None, miny, maxy - bsp_min_room_size + 1)
            maxx = libtcod.random_get_int(None, minx + bsp_min_room_size - 1, maxx)
            maxy = libtcod.random_get_int(None, miny + bsp_min_room_size - 1, maxy)
        # resize the node to fit the room
        node.x = minx
        node.y = miny
        node.w = maxx-minx + 1
        node.h = maxy-miny + 1
        # dig the room
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                bsp_map[x][y] = True
    else:
        # resize the node to fit its sons
        left = libtcod.bsp_left(node)
        right = libtcod.bsp_right(node)
        node.x = min(left.x, right.x)
        node.y = min(left.y, right.y)
        node.w = max(left.x + left.w, right.x + right.w) - node.x
        node.h = max(left.y + left.h, right.y + right.h) - node.y
        # create a corridor between the two lower nodes
        if node.horizontal:
            # vertical corridor
            if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:
                # no overlapping zone. we need a Z shaped corridor
                x1 = libtcod.random_get_int(None, left.x, left.x + left.w - 1)
                x2 = libtcod.random_get_int(None, right.x, right.x + right.w - 1)
                y = libtcod.random_get_int(None, left.y + left.h, right.y)
                vline_up(bsp_map, x1, y - 1)
                hline(bsp_map, x1, y, x2)
                vline_down(bsp_map, x2, y + 1)
            else:
                # straight vertical corridor
                minx = max(left.x, right.x)
                maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                x = libtcod.random_get_int(None, minx, maxx)
                vline_down(bsp_map, x, right.y)
                vline_up(bsp_map, x, right.y - 1)
        else:
            # horizontal corridor
            if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
                # no overlapping zone. we need a Z shaped corridor
                y1 = libtcod.random_get_int(None, left.y, left.y + left.h - 1)
                y2 = libtcod.random_get_int(None, right.y, right.y + right.h - 1)
                x = libtcod.random_get_int(None, left.x + left.w, right.x)
                hline_left(bsp_map, x - 1, y1)
                vline(bsp_map, x, y1, y2)
                hline_right(bsp_map, x + 1, y2)
            else:
                # straight horizontal corridor
                miny = max(left.y, right.y)
                maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                y = libtcod.random_get_int(None, miny, maxy)
                hline_left(bsp_map, right.x - 1, y)
                hline_right(bsp_map, right.x, y)
    return True

bsp = None
bsp_generate = True
bsp_refresh = False
#def render_bsp(first, key, mouse):
def render_bsp():
    global bsp, bsp_generate, bsp_refresh, bsp_map, gameworld
    global bsp_random_room, bsp_room_walls, bsp_depth, bsp_min_room_size
    if bsp_generate or bsp_refresh:
        # dungeon generation
        if bsp is None:
            # create the bsp
            bsp = libtcod.bsp_new_with_size(0, 0, MAP_WIDTH,
                                            MAP_HEIGHT)
        else:
            # restore the nodes size
            libtcod.bsp_resize(bsp, 0, 0, MAP_WIDTH,
                               MAP_HEIGHT)
        bsp_map = list()
        for x in range(MAP_WIDTH):
            bsp_map.append([False] * MAP_HEIGHT)
        if bsp_generate:
            # build a new random bsp tree
            libtcod.bsp_remove_sons(bsp)
            if bsp_room_walls:
                libtcod.bsp_split_recursive(bsp, 0, bsp_depth,
                                            bsp_min_room_size + 1,
                                            bsp_min_room_size + 1, 1.5, 1.5)
            else:
                libtcod.bsp_split_recursive(bsp, 0, bsp_depth,
                                            bsp_min_room_size,
                                            bsp_min_room_size, 1.5, 1.5)
        # create the dungeon from the bsp
        libtcod.bsp_traverse_inverted_level_order(bsp, traverse_node)
        bsp_generate = False
        bsp_refresh = False
    libtcod.console_set_default_foreground(game_console, libtcod.white)
    rooms = 'OFF'
    if bsp_random_room:
        rooms = 'ON'
    ''''
    libtcod.console_print(game_console, 1, 1,
                               "ENTER : rebuild bsp\n"
                               "SPACE : rebuild dungeon\n"
                               "+-: bsp depth %d\n"
                               "*/: room size %d\n"
                               "1 : random room size %s" % (bsp_depth,
                               bsp_min_room_size, rooms))
    '''
    if bsp_random_room:
        walls = 'OFF'
        if bsp_room_walls:
            walls ='ON'
    for y in range(MAP_HEIGHT):
      for x in range(MAP_WIDTH):
        if bsp_map[x][y]:
          gameworld[x][y].unblock()

#######################
# END bsp sample code #
#######################
######################
## Status functions ##
######################

# Displays the parsed string as a status message to the user.
# Doesn't display strings larger than SCREEN_WIDTH yet.
def display_status ():
  global status
  if status:
    libtcod.console_rect(status_console, 0, 0, SCREEN_WIDTH,
        (SCREEN_HEIGHT - MAP_HEIGHT), True)
    libtcod.console_set_default_foreground (status_console, libtcod.white)
    while len(status) > SCREEN_WIDTH*2:
      display_statusline(status[:SCREEN_WIDTH*2])
      key = libtcod.console_wait_for_keypress(True)
      while not key.vk == libtcod.KEY_SPACE:
        key = libtcod.console_wait_for_keypress(True)
      status = status[SCREEN_WIDTH*2:]
    display_statusline(status)
    libtcod.console_blit(status_console,0,0,SCREEN_WIDTH,
        (SCREEN_HEIGHT-MAP_HEIGHT-1),0,0,MAP_HEIGHT+1,1)
  else:
    display_statusline()

def display_statusline (message=""):
  display_player_stats()
  for x in range (libtcod.console_get_width(status_console)):
    libtcod.console_put_char (status_console, x, 0, ' ', libtcod.BKGND_NONE)
    libtcod.console_put_char (status_console, x, 1, ' ', libtcod.BKGND_NONE)
    libtcod.console_print_rect_ex(status_console, 1, 0,
        SCREEN_WIDTH, 2, libtcod.BKGND_NONE, libtcod.LEFT,
        message[:SCREEN_WIDTH*2].strip())
  libtcod.console_blit(status_console,0,0,SCREEN_WIDTH,
      (SCREEN_HEIGHT-MAP_HEIGHT-1),0,0,MAP_HEIGHT+1,1)
  libtcod.console_flush()

def display_player_stats():
  libtcod.console_print_ex(status_console, 1, 2, libtcod.BKGND_NONE,
      libtcod.LEFT, player.name)
  libtcod.console_print_ex(status_console, len(player.name)+2, 2,
      libtcod.BKGND_NONE, libtcod.LEFT, "HP: %s/%s" % (player.health,
        player.max_health))

def add_status (new_status):
  global status
  status = ("%s %s" % (status, new_status))

def clear_status ():
  global status
  status = ""

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
#    self.name = name
#    self.health = max_health
#    self.max_health = max_health
#    self.x = x
#    self.y = y
#    self.char = char
#    self.color = color
#    self.items = []
#    self.equipped = []
#    self.hand = None
#    self.view_distance = view_distance
#    self.strength = strength
#    self.to_hit = to_hit
#    self.fov = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
#    self.npc = False
#    self.exp = 0

#################
# Item functions
#################

# Takes an item and adds it to the current items list
def add_item(item):
  global tile_items
  tile_items.append(item)

# Add any items on the current player's tile to the available items list.
def add_items():
  for item in gameworld[player.x][player.y].items:
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

def clear_items():
  global tile_items
  tile_items = list()

# Draws the current items list to the screen
def draw_items():
  height = 0
  libtcod.console_set_default_background(items_console, libtcod.red)
  libtcod.console_set_default_foreground(items_console, libtcod.white)
  libtcod.console_clear(items_console)
#  pp.pprint(tile_items)
  for item in tile_items:
    height+=libtcod.console_print_rect_ex(items_console,
        0,
        height,
        libtcod.console_get_width(items_console),
        libtcod.console_get_height(items_console),
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        item.name)

  libtcod.console_blit(items_console,0,0,
      libtcod.console_get_width(items_console),
      height,
      0,1,1,
      1.0,0.5)
  libtcod.console_flush()

def item_selector(items, default=None, equipped=[]):
  libtcod.console_clear(menu_console)
  libtcod.console_set_default_background(menu_console, libtcod.black)
  libtcod.console_set_default_foreground(menu_console, libtcod.white)
  libtcod.console_rect(menu_console, 0, 0, MAP_WIDTH, MAP_HEIGHT, True)
  libtcod.console_print_ex(menu_console,
      40, 0, libtcod.BKGND_NONE, libtcod.CENTER, "INVENTORY")
  libtcod.console_print_ex(menu_console,
      1, SCREEN_HEIGHT-1, libtcod.LEFT,
    libtcod.BKGND_NONE,
    "[j / k]: Highlight item     [SPACEBAR]: Select     [q]: quit")
  count = 0
  for item in items:
    libtcod.console_print_ex(menu_console,
        1, count+3, libtcod.BKGND_NONE, libtcod.LEFT, item.name)
    if item in equipped:
      libtcod.console_print_ex(menu_console,
          libtcod.console_get_width(menu_console)-1,
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
      libtcod.console_set_char_background(menu_console,
          i+1,
          count+3,
          libtcod.white)
      libtcod.console_set_char_foreground(menu_console,
          i+1,
          count+3,
          libtcod.black)
    if key.pressed and key.c == ord('k') and count > 0:
      for i in range(len(items[count].name)):
        libtcod.console_set_char_background(menu_console,
            i+1,
            count+3,
            libtcod.black)
        libtcod.console_set_char_foreground(menu_console,
            i+1,
            count+3,
            libtcod.white)
      count = count -1
    elif key.pressed and key.c == ord('j') and count < len(items)-1:
      for i in range(len(items[count].name)):
        libtcod.console_set_char_background(menu_console,
            i+1,
            count+3,
            libtcod.black)
        libtcod.console_set_char_foreground(menu_console,
            i+1,
            count+3,
            libtcod.white)
      count = count +1
    key = libtcod.console_check_for_keypress(True)
    libtcod.console_blit(menu_console,0,0,SCREEN_WIDTH,SCREEN_HEIGHT,0,0,0,1)
    libtcod.console_flush()

  if ord('q') == key.c:
    count=-1

  return count

############
# Game run #
############

# Returns an unoccupied tile.
def find_open_tile():
  x = random.randint(0,MAP_WIDTH-1)
  y = random.randint(0,MAP_HEIGHT-1)
  while not gameworld[x][y].is_floor() or gameworld[x][y].characters:
    x = random.randint(0,MAP_WIDTH-1)
    y = random.randint(0,MAP_HEIGHT-1)
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
    elif ord('z') == key.c :
      turn = True
      player.shoot()
    if turn:
      # Move all enemies toward the player.
      characters = []
      for y in range (MAP_HEIGHT):
        for x in range (MAP_WIDTH):
            for character in gameworld[x][y].characters:
              characters.append(character)

      for character in characters:
        if character.npc and player.health > 0 and random.random() <= ZOMBIE_MOVE_CHANCE:
          path = libtcod.path_new_using_map(player.fov)
          # Compute the path between the hostile object and the player.
          libtcod.path_compute(path, character.get_x(), character.get_y(),
            player.get_x(), player.get_y())
          if libtcod.path_size(path) < 100:
            libtcod.path_walk(path, True)
            character.move_to_coordinates(libtcod.path_get_origin(path)[0], libtcod.path_get_origin(path)[1])
      #spawn a new zombie
      if random.random() <= ENEMY_SPAWN_CHANCE:
        x,y=find_blind_open_tile()
        Character('Zombie', random.randint(5,20), x, y, "Z", libtcod.black, npc=True)
        if random.random() <= 0.20:
          Item ('cheap revolver', x, y, 'r', libtcod.red, gun=Gun(5, 0.6))
          gameworld[x][y].characters[0].pick_up()
        if random.random() <= 0.02:
          Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))
          gameworld[x][y].characters[0].pick_up()
        if random.random() <= 0.10:
          Item ('medkit', x, y, 'H', libtcod.red, health=Health(100))
          gameworld[x][y].characters[0].pick_up()
      turncount = turncount + 1
      if player.health < player.max_health:
        player.heatlh = player.health + 1


  ## Add items in the current tile to the status.
  # for item in gameworld[player.x][player.y].items:
  #       add_status("A %s."% (item.name))

  ## Add items in the current tile to the items indicator.
  add_items()
  # Show the statusbar.
  display_status()
  # Clear the status string.
  if turn:
    clear_status()
  # Render events.
  render()
  # If there are items on the player's current tile, draw them to the screen.
  if items_here():
    draw_items()
  # Clear the list of current tile items.
  clear_items()

  # Return False if the game should still play.
  return False

def render():
  global bsp_map, firstRun, gameworld
  libtcod.console_rect(game_console, 0, 0, MAP_WIDTH, MAP_HEIGHT, True)
  for y in range (MAP_HEIGHT):
      for x in range (MAP_WIDTH):

        # Draw black for all areas the player has not seen yet
        if not gameworld[x][y].explored:
          libtcod.console_set_char_background(game_console, x, y,
              libtcod.black, libtcod.BKGND_SET)

        # Draw all the floors.
        if gameworld[x][y].is_floor () and gameworld[x][y].explored:
          libtcod.console_set_char_background (game_console, x, y,
              DARK_FLOOR_COLOR, libtcod.BKGND_SET)

        # Draw all the walls.
        elif gameworld[x][y].explored:
          libtcod.console_set_char_background(game_console, x, y,
              DARK_WALL_COLOR, libtcod.BKGND_SET)

        # Draw all the light floors.
        if (libtcod.map_is_in_fov (player.fov, x, y)
           and libtcod.map_is_walkable (player.fov, x, y)):
          libtcod.console_set_char_background (game_console, x, y,
              FLOOR_COLOR, libtcod.BKGND_SET)
          for item in gameworld[x][y].items:
            libtcod.console_set_default_foreground (game_console, item.color)
            libtcod.console_put_char (game_console, x, y,
                item.char, libtcod.BKGND_NONE)
          for character in gameworld[x][y].characters:
            libtcod.console_set_default_foreground (game_console,
                character.color)
            libtcod.console_put_char (game_console, x, y,
                character.char, libtcod.BKGND_NONE)
          gameworld[x][y].explored=True

        # Draw all the light walls.
        elif libtcod.map_is_in_fov (player.fov, x, y):
          libtcod.console_set_char_background (game_console, x, y,
              WALL_COLOR, libtcod.BKGND_SET)
          gameworld[x][y].explored=True
  # Blits the game console to the root console.
  libtcod.console_blit(game_console,0,0,MAP_WIDTH,MAP_HEIGHT,0,0,0,1)

# Places the player character on a non-wall tile.
def place_player():
  x,y = find_open_tile()
  global player
  player = Player ('Player', 10000, x, y, "@", libtcod.white,
      view_distance = 15)
  Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))
  Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))

status=""
libtcod.console_set_alignment(status_console, libtcod.LEFT)

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
    render_bsp()
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
