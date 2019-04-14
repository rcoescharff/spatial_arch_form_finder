from vector import Vector
from forcediagram import ForceDiagram 
from graphicstatics import GraphicStatics 
from copy import deepcopy

# creates Vector that with y from vxy and z from vxz
def _construct(vxy, vxz):
    assert vxy.x() == vxz.x()
    return Vector(vxy.x(), vxy.y(), vxz.z())

# applies _construct to arrays vxys and vxzs
def _constructArray(vxys, vxzs):
    assert len(vxys) == len(vxzs)
    a = []
    for i in range(len(vxys)):
        a.append(_construct(vxys[i], vxzs[i]))
    return a

class SGSM:

    # creates SGSM object that has y-coordinates of GraphicStatics 
    # object gsxy and z-coordinates of GraphicStatics object gsxz 
    # (gsxz should be in xy-plane, it is translated later)
    def __init__(self, gsxy, gsxz):

        if (not gsxy.isXY()) or (not gsxz.isXY()): 
            raise Exception('Graphic statics not in xy plane')
        if gsxy.getH() != gsxz.getH():
            raise Exception('Mismatched horizontal forces')
        if len(gsxy.getFs()) != len(gsxz.getFs()):
            raise Exception('Mismatched force arrays')
        if gsxy.getL() != gsxz.getL():
            raise Exception('Mismatched lengths')
        if gsxy.getXs() != gsxz.getXs():
            raise Exception('Mismatched xs')

        self._gsxy = gsxy
        self._gsxzInXY = deepcopy(gsxz)
        gsxz.xytoxz()
        self._gsxz = gsxz
        self._formCoords = _constructArray(self._gsxy.getForm(), 
                                           self._gsxz.getForm())  

        forceXY = self._gsxy.getForceDiagram()
        forceXZ = self._gsxz.getForceDiagram()
        self._forceDownCoords = _constructArray(forceXY.getDownCoords(),
                                                forceXZ.getDownCoords())
        self._forceUpCoords = _constructArray(forceXY.getUpCoords(),
                                              forceXZ.getUpCoords())
        self._o = _construct(forceXY.getO(), forceXZ.getO())

        FsXY = self._gsxy.getFs()
        FsXZ = self._gsxz.getFs()
        self._Fs = []
        for i in range(len(FsXY)):
            self._Fs.append(Vector(0., FsXY[i], FsXZ[i]))

    # returns GraphicStatics object in xy-plane
    def getGSxy(self):
        return self._gsxy

    # returns GraphicStatics object in xz-plane
    def getGSxz(self):
        return self._gsxz

    # returns GraphicStatics object representing xz-plane in xy-plane
    def getGSxzInXY(self):
        return self._gsxzInXY

    # returns form coordinates
    def getForm(self):
        return self._formCoords

    # returns coordinates of applied forces in force diagram
    def getForceDownCoords(self):
        return self._forceDownCoords

    # return coordinates of reaction forces in force diagram
    def getForceUpCoords(self):
        return self._forceUpCoords

    # returns coordinates of O, the point where all internal forces 
    # intersect
    def getO(self):
        return self._o

    # returns list of applied force vectors
    def getFs(self):
        return self._Fs

    # returns number of segments in arch
    def segments(self):
        return len(self._formCoords) - 1

    # returns list of internal force magnitudes
    def getForces(self):
        H = self._gsxy.getH()
        sign = 1.
        if H > 0.:
            sign = -1.
        forces = []
        for v in self._forceDownCoords:
            forces.append((v - self._o).length() * sign)
        return forces
    

    