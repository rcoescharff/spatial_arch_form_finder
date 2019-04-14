from vector import Vector
from sgsm import SGSM
import operator as op 
import math

class Bridge:

    # creates Bridge object using list of deck coordinates deckCoords
    # and either SGSM object sgsm or list of arch coordinates archCoords
    def __init__(self, sgsm=None, deckCoords=None, archCoords=None):

        if sgsm != None and archCoords != None:
            if sgsm.getForm() != archCoords:
                raise Exception("sgsm and arch are not consistent")
        if archCoords == None:
            form = sgsm.getForm()
        else:
            form = archCoords

        if len(form) != len(deckCoords):
            raise Exception("sgsm and deck coords not consistent")
        for i in range(len(form)):
            if form[i].x() != deckCoords[i].x():
                raise Exception("sgsm and deck coords not consistent")

        self._sgsm = sgsm
        self._deckCoords = deckCoords
        self._archCoords = form

    # returns SGSM object (None if defined with arch coords)
    def getSGSM(self):
        return self._sgsm

    # returns horizontal force (H) if self defined with SGSM
    def getH(self):
        if self._sgsm == None:
            raise Exception("bridge not defined with SGSM")
        return self._sgsm.getGSxy().getH()

    # returns length (L)
    def getL(self):
        l = len(self._deckCoords)
        return self._deckCoords[l-1].x() - self._deckCoords[0].x()

    # returns list arch coordinates
    def getArch(self):
        return self._archCoords

    # returns list of deck coordinates
    def getDeck(self):
        return self._deckCoords

    # returns anchor offset
    def getAnchOff(self):
        return self._archCoords[0].y() - self._deckCoords[0].y() 

    # returns number of segments in arch
    def segments(self):
        return len(self._deckCoords) - 1

    # returns arch height (h_arch)
    def archHeight(self):
        maxZ = self._archCoords[0].z()
        minZ = self._archCoords[0].z()
        for v in self._archCoords:
            minZ = min(minZ, v.z())
            maxZ = max(maxZ, v.z())
        return maxZ - minZ

    # returns arch depth (d_arch)
    def archDepth(self):
        maxY = self._archCoords[0].y()
        minY = self._archCoords[0].y()
        for v in self._archCoords:
            minY = min(minY, v.y())
            maxY = max(maxY, v.y())
        return maxY - minY

    # returns arch angle of inclination (theta)
    def archAngle(self):

        hArch = self.archHeight()
        maxY = self._archCoords[0].y()
        minY = self._archCoords[0].y()

        for v in self._archCoords:
            minY = min(minY, v.y())
            maxY = max(maxY, v.y())

        if abs(abs(minY) - abs(maxY)) < .01:
            return math.pi / 2.
        elif abs(maxY) > abs(minY):
            theta = math.atan(hArch / maxY)
        else:
            theta = math.atan(hArch / minY)

        if theta < 0.:
            theta += math.pi

        return theta

    # returns arch radial length (r)
    def archRadius(self):

        hArch = self.archHeight()
        maxY = self._archCoords[0].y()
        minY = self._archCoords[0].y()

        for v in self._archCoords:
            minY = min(minY, v.y())
            maxY = max(maxY, v.y())

        if abs(abs(minY) - abs(maxY)) < .01:
            return hArch
        elif abs(maxY) > abs(minY):
            return math.sqrt(hArch**2 + maxY**2)
        else:
            return math.sqrt(hArch**2 + minY**2)

    # returns list of internal arch force maginitudes if self is 
    # defined with SGSM
    def getArchForces(self):
        if self._sgsm == None:
            raise Exception("bridge not defined with SGSM")
        return self._sgsm.getForces()

    # returns maximum absolute value of internal arch force magnitude if 
    # self is defined with SGSM
    def maxArchForce(self):
        return max(map(abs, self.getArchForces()))

    # returns tuple of reaction vectors using q_arch value qArch
    def getArchReactions(self, qArch):
        if self._sgsm == None:
            raise Exception("bridge not defined with SGSM")
        upCoords = self._sgsm.getForceUpCoords()
        R1 = upCoords[1] - upCoords[0]
        R2 = upCoords[2] - upCoords[1]
        H = self._sgsm.getGSxy().getH()
        arch = self.getArch()
        tribL1 = (arch[1] - arch[0]).length() / 2.
        tribL2 = (arch[len(arch)-1] - arch[len(arch)-2]).length() / 2.
        R1 = Vector(H, R1.y(), R1.z() + tribL1 * qArch)
        R2 = Vector(-H, R2.y(), R2.z() + tribL2 * qArch)
        return (R1, R2)

    # returns list of force vectors in cables using q
    def getCableVectorForces(self, q):

        arch = self.getArch()
        deck = self.getDeck()
        forces = []

        for i in range(1, self.segments()):
            tribL1 = (deck[i] - deck[i-1]).length()
            tribL2 = (deck[i+1] - deck[i]).length()
            tribL = (tribL1 + tribL2) / 2.
            Pz = q * tribL
            F =  deck[i] - arch[i]
            Py = F.y() * Pz / F.z()
            forces.append(Vector(0.0, Py, Pz))

        return forces

    # returns list of force maginitudes in cables using q
    def getCableForces(self, q):
        vectorForces = self.getCableVectorForces(q)
        return map(lambda x: x.length(), vectorForces)

    # returns maximum force maginitude in cables using q
    def maxCableForce(self, q):
        return max(self.getCableForces(q))

    # returns list of x-coordinates of nodes
    def getXs(self):
        return map(lambda v: v.x(), self._archCoords)

    # returns list values in moment diagram of deck
    def getDeckMomentZ(self, q):

        cableForces = map(lambda a: a.y(), self.getCableVectorForces(q))
        xs = self.getXs()
        Ms = []
        M = 0.
        Vtot = -reduce(op.add, cableForces)
        MsR1 = map(lambda i: xs[i+1] * abs(cableForces[i]), 
                    range(len(cableForces)))
        MtotR1 = reduce(op.add, MsR1)
        V = Vtot - MtotR1 / self.getL()

        for i in range(1, self.segments()):
            segL = xs[i] - xs[i - 1]
            M += V * segL
            Ms.append(M)
            V += cableForces[i-1]

        return Ms

    # returns absolute value of maximum moment value in deck
    def maxDeckMomentZ(self, q):
        return max(map(abs, self.getDeckMomentZ(q)))

    # returns list lengths of arch segments
    def getArchLengths(self):
        archLens = []
        for i in range(1, len(self._archCoords)):
            v = self._archCoords[i] - self._archCoords[i-1]
            archLens.append(v.length())
        return archLens

    # returns list of lengths of cables
    def getCableLengths(self):
        cableLens = []
        for i in range(1, len(self._archCoords) - 1):
            v = self._archCoords[i] - self._deckCoords[i]
            cableLens.append(v.length())
        return cableLens

    # returns load path where load is q, relative arch strength is 
    # sigArch, and relative cable strength is sigCab
    def loadPath(self, q, sigArch=1., sigCab=1.):

        archForces = self.getArchForces()
        cableForces = self.getCableForces(q)
        archLengths = self.getArchLengths()
        cableLengths = self.getCableLengths()

        lp = 0.
        for i in range(len(archForces)):
            lp += abs(archForces[i]) * archLengths[i] / sigArch
        for i in range(len(cableForces)):
            lp += abs(cableForces[i]) * cableLengths[i] / sigCab

        return lp 

    # returns string with deck and arch coordinates
    def __str__(self):
        s = 'Deck: ' + str(map(str, self.getDeck())) + "\n"
        s += 'Arch: ' + str(map(str, self.getArch()))
        return s