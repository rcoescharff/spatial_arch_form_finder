from bridge import Bridge
import rhinosgsm
import fromdeck
from vector import Vector
from sgsm import SGSM
import math

# draw deck with coordinates coords
def drawDeck(coords):
    for i in range(len(coords) - 1):
        rhinosgsm.drawLine(coords[i], coords[i + 1], 'Deck')

# draw arch with coordinates coords
def drawArch(coords):
    for i in range(len(coords) - 1):
        rhinosgsm.drawLine(coords[i], coords[i + 1], 'Form Diagram')

# draw cables between deck coordinates deckCoords and arch coordinates 
# archCoords, cables is number of cables, if cables=None there cables 
# between each segment
def drawCables(deckCoords, archCoords, cables=None):

    coords = len(deckCoords)
    if cables == None:
        cables = coords - 2
    if (coords - 1) % (cables + 1) != 0:
        raise Exception("cables + 1 must be a factor of segments")

    step = (coords - 1) // (cables + 1)
    for i in range(step, coords - step, step):
        rhinosgsm.drawLine(deckCoords[i], archCoords[i], 'Cables')

# draw bridge and force diagram with number of cables cables
def drawBridge(bridge, cables=None):
    rhinosgsm.fileSetup()
    drawDeck(bridge.getDeck())
    rhinosgsm.drawAll(bridge.getSGSM())
    drawCables(bridge.getDeck(), bridge.getArch(), cables)

# draw bridge with number of cables cables  
def drawForm(bridge, cables=None):
    rhinosgsm.fileSetup()
    drawDeck(bridge.getDeck())
    drawArch(bridge.getArch())
    drawCables(bridge.getDeck(), bridge.getArch(), cables)   