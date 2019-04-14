from vector import Vector
from forcediagram import ForceDiagram
from copy import deepcopy

# finds maximum y value in list coords
def _maxy(coords):
    maxy = 0.0
    for coord in coords:
        if coord.y() > maxy:
            maxy = coord.y()
    return maxy

# finds minimum y value in list coords
def _miny(coords):
    miny = coords[0]
    for coord in coords:
        if coord.y() < miny:
            miny = coord.y()
    return miny

class GraphicStatics:

    # creates GraphicStatics object. L is length, xs is list of x
    # coordinates where there are applied forces, Fs is list of applied
    # forces, and H is horizontal force in arch
    def __init__(self, L, xs, Fs, H):
        self._L = L
        self._xs = deepcopy(xs)
        self._xs.append(L)
        self._Fs = deepcopy(Fs)
        self._H = H
        self._forceDiagram = ForceDiagram(self._Fs, H)
        self._graphicStatics()
        assert not self._forceDiagram.isTest()
        self._xy = True

    # returns a form diagram using the force diagram
    def _forceToForm(self):
        o = self._forceDiagram.getO()
        forceCoords = self._forceDiagram.getDownCoords()
        formCoords = [Vector()]
        for i in range(len(self._xs)):
            forceVect = o - forceCoords[i]
            formY = forceVect.intersect(formCoords[i], self._xs[i])
            formCoords.append(Vector(self._xs[i], formY))
        return formCoords

    # returns the coordinates of the test form
    def _testForm(self):
        assert self._forceDiagram.isTest()
        self._testFormCoords = self._forceToForm()
        length = len(self._testFormCoords)
        return self._testFormCoords[length-1] - self._testFormCoords[0]

    # gets final force diagram and form diagram coordinates
    def _graphicStatics(self):
        testV = self._testForm()
        self._forceDiagram.findReactions(testV)
        self._formCoords = self._forceToForm()

    # returns test form coordinates
    def getTestForm(self):
        return self._testFormCoords

    # returns form coordinates
    def getForm(self):
        return self._formCoords

    # returns ForceDiagram object
    def getForceDiagram(self):
        return self._forceDiagram

    # returns length
    def getL(self):
        return self._L

    # returns list of positions where forces are applied
    def getXs(self):
        return self._xs

    # returns list of applied force magnitudes
    def getFs(self):
        return self._Fs

    # returns horizontal force in arch
    def getH(self):
        return self._H

    # returns True if graphic statics is in xy-plane
    def isXY(self):
        return self._xy

    # translates force and form diagrams from xy-plane to xz-plane
    def xytoxz(self):
        assert self._xy
        assert self._forceDiagram.isXY()
        for i in range(len(self._formCoords)):
            self._formCoords[i].xytoxz()
        for i in range(len(self._testFormCoords)):
            self._testFormCoords[i].xytoxz()
        self._forceDiagram.xytoxz()
        self._xy = False

    # returns height of form
    def getHeight(self):
        return _maxy(self._formCoords) - _miny(self._formCoords)


