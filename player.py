from libtcod import libtcodpy as libtcod
import character as C
import console as cons
import status as S
import map_vars as M
import rendering as R
import items as I

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
            count = I.item_selector(self.items, equipped=self.equipped)
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
                R.render()
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

# Places the player character on a non-wall tile.
def place_player():
    x,y = find_open_tile()
    P.player = P.Player ('Player', 500, x, y, "@", libtcod.white,
        view_distance = 15)
    Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))
    #Item ('silver revolver', x, y, 'r', libtcod.cyan, gun=Gun(15, 0.9))

player = None
