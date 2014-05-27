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
