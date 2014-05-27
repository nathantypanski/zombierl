# This is a generic game object.
class Object:

    def __init__ (self, name, x, y, char, color):
        self._name = name
        self._x = x
        self._y = y
        self._char = char
        self._color = color
        gameworld[self.x][self.y].items.append(self)

    def is_hostile (self):
        return False

    @property
    def x (self):
        return self._x

    @x.setter
    def x (self,x):
        self._x=x

    @property
    def y (self):
        return self._y

    @y.setter
    def y(self,y):
        self._y=y
