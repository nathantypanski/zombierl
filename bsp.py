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
    libtcod.console_clear(game_console)
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
        libtcod.console_print(game_console, 1, 6,
                                   '2 : room walls %s' % walls)
    for y in range(MAP_HEIGHT):
      for x in range(MAP_WIDTH):
        if bsp_map[x][y]:
          gameworld[x][y].unblock()

#######################
# END bsp sample code #
#######################


