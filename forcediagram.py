from vector import Vector
from copy import deepcopy

class ForceDiagram:

    # creates self._downCoords array by making each item the cumulative
    # sum of previous items and the corresponding force in Fs
    def _addForces(self, Fs):
        self._downCoords = [Vector()]
        vsum = Vector()
        for f in Fs:
            vsum += Vector(y=f)
            self._downCoords.append(vsum)

    # produces test force diagram for forces Fs and horizontal force H
    def __init__(self, Fs, H):
        self._addForces(Fs)
        self._upCoords = []
        last = self._downCoords[len(self._downCoords) - 1]
        halfHeight = last.y() / 2.0
        self._o = Vector(H, halfHeight)
        self._testO = self._o
        self._H = H
        self._xy = True
        self._isTest = True

    # calculates reactions and shift to actual force diagram using v,
    # the direction vector between the supports 
    def findReactions(self, v):
        y = v.intersect(self._o, 0.0)
        top = self._downCoords[len(self._downCoords) - 1]
        self._upCoords = [Vector(), Vector(y=y), deepcopy(top)]
        self._o = Vector(self._H, y)
        self._isTest = False

    # returns coordinates of applied forces in diagram
    def getDownCoords(self):
        return self._downCoords

    # returns coordinates of reaction forces in diagram
    def getUpCoords(self):
        if self._isTest:
          raise Exception('must call findReactions() first')
        return self._upCoords

    # returns coordinates of O, the point where all internal forces 
    # intersect
    def getO(self):
        return self._o

    # returns coordinates of O in test diagram
    def getTestO(self):
        return self._testO

    # returns true if it is still test diagram
    def isTest(self):
        return self._isTest

    # returns true if diagram is on the xy-plane
    def isXY(self):
        return self._xy

    # translates diagram from xy-plane to xz-plane
    def xytoxz(self):
        assert self._xy
        for i in range(len(self._upCoords)):
            self._upCoords[i].xytoxz()
        for i in range(len(self._downCoords)):
            self._downCoords[i].xytoxz()
        self._o.xytoxz()
        self._testO.xytoxz()
        self._xy = False

    # returns internal force vectors
    def forces(self):
        forces = []
        for coord in self._downCoords:
            forceVect = coord - self._o
            forces.append(forceVect.length())
        return forces


    