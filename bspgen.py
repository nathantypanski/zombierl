from libtcod import libtcodpy as libtcod

# This uses BSP sample code from libtcod to generate bsp-based dungeons.

class Bsp:
    def __init__(self, MAP_WIDTH, MAP_HEIGHT, gameworld):
        self.MAP_WIDTH = MAP_WIDTH
        self.MAP_HEIGHT = MAP_HEIGHT
        self.bsp_depth = 8
        self.bsp_min_room_size = 10
        # a room fills a random part of the node or the maximum available space ?
        self.bsp_random_room = True
        # if true, there is always a wall on north & west side of a room
        self.bsp_room_walls = True
        self.bsp_map = None
        self.gameworld = gameworld
        self.bsp = None
        self.bsp_generate = True
        self.bsp_refresh = False


    #########################
    # BEGIN bsp sample code #
    #########################
    # draw a vertical line
    def vline(self, m, x, y1, y2):
        if y1 > y2:
            y1,y2 = y2,y1
            for y in range(y1,y2+1):
                m[x][y] = True

    # draw a vertical line up until we reach an empty space
    def vline_up(self, m, x, y):
        while y >= 0 and not m[x][y]:
            m[x][y] = True
            y -= 1

    # draw a vertical line down until we reach an empty space
    def vline_down(self, m, x, y):
        while y < self.MAP_HEIGHT and not m[x][y]:
            m[x][y] = True
            y += 1

    # draw a horizontal line
    def hline(self, m, x1, y, x2):
        if x1 > x2:
            x1,x2 = x2,x1
            for x in range(x1,x2+1):
                m[x][y] = True

    # draw a horizontal line left until we reach an empty space
    def hline_left(self, m, x, y):
        while x >= 0 and not m[x][y]:
            m[x][y] = True
            x -= 1

    # draw a horizontal line right until we reach an empty space
    def hline_right(self, m, x, y):
        while x < self.MAP_WIDTH and not m[x][y]:
            m[x][y]=True
            x += 1

    # the class building the dungeon from the bsp nodes
    def traverse_node(self, node, dat):
        if libtcod.bsp_is_leaf(node):
            # calculate the room size
            minx = node.x + 1
            maxx = node.x + node.w - 1
            miny = node.y + 1
            maxy = node.y + node.h - 1
            if not self.bsp_room_walls:
                if minx > 1:
                    minx -= 1
                    if miny > 1:
                        miny -=1
                        if maxx == self.MAP_WIDTH - 1:
                            maxx -= 1
                            if maxy == self.MAP_HEIGHT - 1:
                                maxy -= 1
                                if self.bsp_random_room:
                                    minx = libtcod.random_get_int(None, minx, maxx - self.bsp_min_room_size + 1)
                                    miny = libtcod.random_get_int(None, miny, maxy - self.bsp_min_room_size + 1)
                                    maxx = libtcod.random_get_int(None, minx + self.bsp_min_room_size - 1, maxx)
                                    maxy = libtcod.random_get_int(None, miny + self.bsp_min_room_size - 1, maxy)
                                    # resize the node to fit the room
                                    node.x = minx
                                    node.y = miny
                                    node.w = maxx-minx + 1
                                    node.h = maxy-miny + 1
                                    # dig the room
                                    for x in range(minx, maxx + 1):
                                        for y in range(miny, maxy + 1):
                                            self.bsp_map[x][y] = True
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
                                                    self.vline_up(self.bsp_map, x1, y - 1)
                                                    self.hline(self.bsp_map, x1, y, x2)
                                                    self.vline_down(self.bsp_map, x2, y + 1)
                                                else:
                                                    # straight vertical corridor
                                                    minx = max(left.x, right.x)
                                                    maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                                                    x = libtcod.random_get_int(None, minx, maxx)
                                                    self.vline_down(self.bsp_map, x, right.y)
                                                    self.vline_up(self.bsp_map, x, right.y - 1)
                                                else:
                                                    # horizontal corridor
                                                    if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
                                                        # no overlapping zone. we need a Z shaped corridor
                                                        y1 = libtcod.random_get_int(None, left.y, left.y + left.h - 1)
                                                        y2 = libtcod.random_get_int(None, right.y, right.y + right.h - 1)
                                                        x = libtcod.random_get_int(None, left.x + left.w, right.x)
                                                        self.hline_left(self.bsp_map, x - 1, y1)
                                                        self.vline(self.bsp_map, x, y1, y2)
                                                        self.hline_right(self.bsp_map, x + 1, y2)
                                                    else:
                                                        # straight horizontal corridor
                                                        miny = max(left.y, right.y)
                                                        maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                                                        y = libtcod.random_get_int(None, miny, maxy)
                                                        self.hline_left(self.bsp_map, right.x - 1, y)
                                                        self.hline_right(self.bsp_map, right.x, y)
                                                        return True

    def render_bsp(self):

        if self.bsp_generate or self.bsp_refresh:

            # dungeon generation
            if self.bsp is None:
                # create the bsp
                self.bsp = libtcod.bsp_new_with_size(0, 0, self.MAP_WIDTH,
                                                     self.MAP_HEIGHT)

            else:
                # restore the nodes size
                libtcod.bsp_resize(bsp, 0, 0, self.MAP_WIDTH,
                                   self.MAP_HEIGHT)

            self.bsp_map = list()

            for x in range(self.MAP_WIDTH):
                self.bsp_map.append([False] * self.MAP_HEIGHT)

            if self.bsp_generate:
                # build a new random bsp tree
                libtcod.bsp_remove_sons(self.bsp)
                if self.bsp_room_walls:
                    libtcod.bsp_split_recursive(self.bsp, 0, self.bsp_depth,
                                                self.bsp_min_room_size + 1,
                                                self.bsp_min_room_size + 1, 1.5, 1.5)

                else:
                    libtcod.bsp_split_recursive(self.bsp, 0, bsp_depth,
                                                self.bsp_min_room_size,
                                                self.bsp_min_room_size, 1.5, 1.5)

            # create the dungeon from the bsp
            libtcod.bsp_traverse_inverted_level_order(self.bsp, self.traverse_node)
            bsp_generate = False
            bsp_refresh = False

#        libtcod.console_set_default_foreground(game_console, libtcod.white)
rooms = 'OFF'

        if self.bsp_random_room:
            rooms = 'ON'

        if self.bsp_random_room:
            walls = 'OFF'

            if self.bsp_room_walls:
                walls ='ON'

        for y in range(self.MAP_HEIGHT):
            for x in range(self.MAP_WIDTH):
                if self.bsp_map[x][y]:
                    self.gameworld[x][y].unblock()

    #######################
    # END bsp sample code #
    #######################
