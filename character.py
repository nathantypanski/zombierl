from libtcod import libtcodpy as libtcod
import object as O
import map_vars as M
import status as S
import random

class Character (O.Object):
  def __init__ (self, name, max_health, x, y, char, color, npc=False,
      strength=5, to_hit=0.8, view_distance=10):
    self.name = name
    self.health = max_health
    self.max_health = max_health
    self._x = x
    self._y = y
    self.char = char
    self.color = color
    self.items = []
    self.hand = None
    self.npc = npc
    self.strength = strength
    self.to_hit = to_hit
    self.view_distance=view_distance
    M.gameworld[self.x][self.y].characters.append(self)

  def move (self, dx, dy):
    if (M.gameworld[self.x + dx][self.y + dy].characters
        or not M.gameworld[self.x + dx][self.y + dy].is_floor()):
      characters = M.gameworld[self.x + dx][self.y + dy].characters
      if characters:
        for character in characters:
          if not character.npc:
            self.attack(character)
    else:
      M.gameworld[self.x][self.y].characters.remove(self)
      self.x = self.x + dx
      self.y = self.y + dy
      M.gameworld[self.x][self.y].characters.append(self)

  def pick_up(self):
    if M.gameworld[self.x][self.y].items:
      item = M.gameworld[self.x][self.y].items.pop()
      self.items.append(item)

  def drop(self):
    if self.items:
      item = self.items.pop()
      M.gameworld[self.x][self.y].items.append(item)

  def drop_all(self):
    for item in self.items:
      self.items.remove(item)
      M.gameworld[self.x][self.y].items.append(item)

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
      S.add_status("%s hits %s!" % (self.name, character.name))
      if damage > (0.5*character.max_health):
        S.add_status("It's super effective!")
      character.take_damage(damage)
    else:
      S.add_status("%s swings and misses." % (self.name))

  def take_damage (self, damage):
    self.health -= damage

    if 0 > self.health:
      S.add_status("%s is killed!" % (self.name))
      self.health = 0
      M.gameworld[self.x][self.y].characters.remove(self)
      self.drop_all()

  def compute_fov(self):
    for x in range (M.MAP_WIDTH):
      for y in range (M.MAP_HEIGHT):
        if M.gameworld[x][y].is_floor():
         libtcod.map_set_properties (self.fov, x , y, True, True)
    libtcod.map_compute_fov (self.fov, self.x, self.y, self.view_distance,
                            True,libtcod.FOV_DIAMOND)
