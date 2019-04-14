from vector import Vector
from graphicstatics import GraphicStatics
from sgsm import SGSM
from bridge import Bridge
import math 

# returns SGSM with loading based on guess arch defined by archCoords, 
# deck form defined by deckCoords, H, q, and qArch (q_arch)
def deckToSGSM(archCoords, deckCoords, H, q, qArch):

    if len(archCoords) != len(deckCoords):
        raise Exception('Mismatched arrays')

    nodes = len(archCoords)
    for i in range(nodes):
        if archCoords[i].x() != deckCoords[i].x():
            raise Exception('Mismatched arrays')

    deckLengths = []
    archLengths = []
    for i in range(1, nodes):
        deckLengths.append((deckCoords[i] - deckCoords[i-1]).length())
        archLengths.append((archCoords[i] - archCoords[i-1]).length())

    FsXY = []
    FsXZ = []
    xs = []
    for i in range(1, nodes - 1):
        P = q * ((deckLengths[i-1] + deckLengths[i])/2.0) 
        PArch = qArch * ((archLengths[i-1] + archLengths[i])/2.0) 
        F = archCoords[i] - deckCoords[i]
        FsXY.append(F.y() * P / F.z())
        FsXZ.append(P + PArch)
        xs.append(deckCoords[i].x())

    L = archCoords[nodes - 1].x()

    gsxy = GraphicStatics(L, xs, FsXY, H)
    gsxz = GraphicStatics(L, xs, FsXZ, H)

    if archCoords[0].z() != 0.:
        zs = map(lambda v: v.z(), archCoords)
        if H > 0.:
            vertexHeight = max(zs)
        else:
            vertexHeight = min(zs)
        return SGSM(gsxy, gsxz, vertexHeight)

    return SGSM(gsxy, gsxz)

# determines whether all the the coordinates in coords1 and coords2
# are within tol of each other
def isSame(coords1, coords2, tol):
    assert len(coords1) == len(coords2)
    for i in range(len(coords2)):
        diff = coords1[i] - coords2[i]
        if diff.y() > tol or diff.z() > tol:
            return False
    return True

# iterates to get SGSM based on deck coordinates deckCoords, H, q, and 
# qArch. archCoords are the coordinates of the starting guess arch and
# tol is the distance between points at which two forms are considered
# to be the same
def iterate(archCoords, deckCoords, H, q, qArch, tol):

    prevCoords = archCoords
    sgsm = deckToSGSM(archCoords, deckCoords, H, q, qArch)
    coords = sgsm.getForm()
    i = 0

    while (not isSame(prevCoords, coords, tol)):
        if i > 2000: 
            print "exceeded iteration limit"
            break
        sgsm = deckToSGSM(coords, deckCoords, H, q, qArch)
        prevCoords = coords
        coords = sgsm.getForm()
        i += 1

    return sgsm

# returns list of deck coordinates base on dividing deck defined by deck
# function and length L into segments sections and shifting it by 
# anchorOffset
def getDeckCoords(deck, L, segments, anchorOffset):

    if abs(deck(0).z()) > 0.00001:
        raise Exception("deck must start at z=0")
    if abs(deck(0).y()) > 0.00001:
        raise Exception("deck must start at y=0")
    if abs(deck(L).z()) > 0.00001:
        raise Exception("deck must end at z=0")

    aoV = Vector(0., anchorOffset, 0.)
    deckCoords = [deck(0.) - aoV]

    for i in range(1, segments + 1):
        x = (L/segments) * i
        deckCoords.append(deck(x) - aoV)

    return deckCoords

# return starting guess arch based on deck coordinates deckCoords
def getStartingArch(deckCoords):
    L = deckCoords[len(deckCoords)-1].x() - deckCoords[0].x()
    f = lambda x: -(x - L/2.)**2 + (L/2.)**2
    archCoords = []
    for v in deckCoords:
        archCoords.append(Vector(v.x(), 0.0, f(v.x())))
    return archCoords

# return d_deck for deck with function deck and length L
def getDeckDepth(deck, L):
    deckCoords = getDeckCoords(deck, L, int(L * 5), 0.)
    deckCoordsY = map(lambda v: v.y(), deckCoords)
    dDeck = max(deckCoordsY) - min(deckCoordsY) 
    return dDeck

# return list of segment lengths for deck with function deck and length
# L that is divided into segs segments
def getDeckLengths(deck, L, segs):
    deckCoords = getDeckCoords(deck, L, segs, 0.)
    deckLens = []
    for i in range(1, len(deckCoords)):
        v = deckCoords[i] - deckCoords[i-1]
        deckLens.append(v.length())
    return deckLens

# returns a Bridge object for the funicular form of a bridge with 
# length L, anchor offset anchorOffset, horizontal force H, deck load 
# q, and arch weight qArch where deck is a function or a set of 
# coordinates, and number of segments is required if deck is a function 
def fromDeck(deck, L, anchorOffset, H, q, qArch, segments=None):

    if type(deck) == list: 
        deckCoords = map(lambda v: v - Vector(y=anchorOffset), deck)
    else:
        if segments == None:
            raise Exception("segments needed if deck is function")
        deckCoords = getDeckCoords(deck, L, segments, anchorOffset)

    archCoords = getStartingArch(deckCoords)
    sgsm = iterate(archCoords, deckCoords, H, q, qArch, .01)
    bridge = Bridge(sgsm, deckCoords)
    return bridge

# returns a parabolic deck with length L, d_deck d, and h_deck h
def parabolicDeck(L, d, h=0.):
    ay = d / ((L/2.)**2)
    az = h / ((L/2.)**2)
    parabola = lambda x, a: a * (-(x - L/2.)**2 + (L/2.)**2)
    arch = lambda x: Vector(x, parabola(x, ay), parabola(x, az))
    return arch

# returns a sinusoidal deck with length L, amplitude A, wavelength lmda,
# phase phi, and h_deck h.
def sineDeck(L, A, lmda, phi=0., h=0.):
    a = h / ((L/2.)**2)
    off = A * math.sin(phi)
    y = lambda x: A * math.sin(2 * math.pi / lmda * x + phi) - off
    z = lambda x: a * (-(x - L/2.)**2 + (L/2.)**2)
    deck = lambda x: Vector(x, y(x), z(x))
    return deck

# plots deck shape for function deck with length L
def plotDeck(deck, L):
    import matplotlib.pyplot as plt
    coords = getDeckCoords(deck, L, 100, 0.)
    xs = map(lambda v: v.x(), coords)
    ys = map(lambda v: v.y(), coords)
    plt.plot(xs, ys)
    plt.show()