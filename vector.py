import math

class Vector:
    
    # create vector object with components x, y, and z
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self._x = x
        self._y = y
        self._z = z

    # return vector sum of self and that
    def __add__(self, that):
        x = self._x + that.x()
        y = self._y + that.y()
        z = self._z + that.z()
        return Vector(x, y, z)

    # return vector difference of self and that
    def __sub__(self, that):
        x = self._x - that.x()
        y = self._y - that.y()
        z = self._z - that.z()
        return Vector(x, y, z)

    # return vector that is self scaled by a
    def __mul__(self, a):
        x = self._x * a
        y = self._y * a
        z = self._z * a
        return Vector(x, y, z)

    # return True if self and that are equal
    def __eq__(self, that):
        xeq = self._x == that.x()
        yeq = self._y == that.y()
        zeq = self._z == that.z()
        return xeq and yeq and zeq

    # return True if self and that are not equal
    def __ne__(self, that):
        return not(self == that)

    # hashing function so Vector can be key in dictionary
    def __hash__(self):
        return hash(tuple((self._x, self._y, self._z)))

    # return magnitude of vector
    def length(self):
        return math.sqrt(self._x**2 + self._y**2 + self._z**2)

    # return x component
    def x(self):
        return self._x

    # return y component
    def y(self):
        return self._y

    # return z component
    def z(self):
        return self._z

    # returns y where self intersects line x=vertLine if it starts at 
    # point
    def intersect(self, point, vertLine):
        assert self._z == 0.0
        return point.y() + self._y * ((vertLine - point.x()) / self._x)

    # shift a vector that is on the xy-plane to the xz-plane
    def xytoxz(self):
        if self._z != 0.0:
            raise Exception(str(self))
        self._z = self._y
        self._y = 0.0

    # return unit vector with the same direction as self
    def normalize(self):
        return self * (1.0 / self.length())

    # return a string of form (x, y, z) representing self
    def __str__(self):
        f = '({0}, {1}, {2})'
        return f.format(self._x, self._y, self._z)

    # return a string representing self that goes to 2 decimal points
    def fstr(self):
        f = '({0:.2f}, {1:.2f}, {2:.2f})'
        return f.format(self._x, self._y, self._z)
