
from vector import Vector
from bridge import Bridge 
import fromdeck
import math

def parabolicArch(L, d, h):
    ay = d / ((L/2.)**2)
    az = h / ((L/2.)**2)
    parabola = lambda x, a: a * (-(x - L/2.)**2 + (L/2.)**2)
    arch = lambda x: Vector(x, parabola(x, ay), parabola(x, az))
    return arch

def parabArchPolar(L, angle, r):
    d = r * math.cos(angle)
    h = r * math.sin(angle)
    return parabolicArch(L, d, h)



def getArchCoords(arch, L, segments):
    if arch(0.) != Vector():
        raise Exception("arch must intersect point (0,0,0)")
    if arch(L) != Vector(L):
        raise Exception("arch must intersect point (L,0,0)")
    archCoords = [arch(0.)]
    for i in range(1, segments + 1):
        x = (L/segments) * i
        archCoords.append(arch(x))
    return archCoords

def getBridge(arch, deck, L, segments, anchorOffset):
    archCoords = getArchCoords(arch, L, segments)
    deckCoords = fromdeck.getDeckCoords(deck, L, segments, anchorOffset)
    return Bridge(deckCoords=deckCoords, archCoords=archCoords)

def main():
    L = 10.
    arch = parabolicArch(L, 3., 5.)
    deck = fromdeck.parabolicDeck(L, 4.)
    segments = 10
    anchorOffset = 1.
    bridge = getBridge(arch, deck, L, segments, anchorOffset)
    print bridge

if __name__ == '__main__':
    main()
