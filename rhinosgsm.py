import rhinoscriptsyntax as rs
from vector import Vector
from graphicstatics import GraphicStatics
from forcediagram import ForceDiagram
from copy import deepcopy
from sgsm import SGSM 
import Rhino
import scriptcontext

# translates from Vector to Rhino.Geometry.Point3d
def vectToPt(v):
    return Rhino.Geometry.Point3d(v.x(), v.y(), v.z())
  
# translates from Rhino.Geometry.Point3d to Vector 
def ptToVect(p):
    return Vector(p.X, p.Y, p.Z)

# draws line from v1 to v2 in layer with name layer
def drawLine(v1, v2, layer):
    start = vectToPt(v1)
    end = vectToPt(v2)
    line = rs.AddLine(start, end)
    rs.ObjectLayer(line, layer)
  
# draws arrow from v1 to v2 in layer with name layer, code based on
# https://developer.rhino3d.com/samples/rhinocommon/
#       add-arrowheads-to-curves/
def drawArrow(v1, v2, layer):
    start = vectToPt(v1)
    end = vectToPt(v2)
    line = Rhino.Geometry.Line(start, end)
    attribs = scriptcontext.doc.CreateDefaultAttributes()
    attribs.ObjectDecoration = \
        Rhino.DocObjects.ObjectDecoration.EndArrowhead
    lineID = scriptcontext.doc.Objects.AddLine(line, attribs)
    scriptcontext.doc.Views.Redraw()
    rs.ObjectLayer(lineID, layer)

# draws form diagram for sgsm, forces are scaled by forceScale
def drawConstructedForm(sgsm, forceScale=1.0):

    form = sgsm.getForm()
    forces = map(lambda x: x * forceScale, sgsm.getFs()) 

    for i in range(len(form) - 1):
        drawLine(form[i], form[i + 1], 'Form Diagram')
        if i > 0:
            drawArrow(forces[i - 1] + form[i], form[i], 
                      'Applied Forces (Form)')

    Rs = map(lambda x: x * forceScale, sgsm.getForceUpCoords()) 
    start = form[0]
    drawArrow(start - Rs[1], start, 'Applied Forces (Form)')
    end = form[len(form) - 1]
    drawArrow(Rs[1] - Rs[2] + end, end, 'Applied Forces (Form)')

# draws force diagram for sgsm, forces are scaled by forceScale
def drawConstructedForce(sgsm, forceScale=1.0):

    o = sgsm.getO()

    downCoords = sgsm.getForceDownCoords()
    for i in range(len(downCoords)):
        if i < len(downCoords) - 1:
            drawArrow(downCoords[i+1], downCoords[i], 
                      'Applied Forces (Force)')
        drawLine(downCoords[i], o, 'Force Diagram')

    upCoords = sgsm.getForceUpCoords()
    for i in range(len(upCoords) - 1):
        drawArrow(upCoords[i], upCoords[i+1], 'Applied Forces (Force)')
    drawLine(upCoords[1], o, 'Force Diagram')

# draws sgsm, forces are scaled by forceScale
def drawAll(sgsm, forceScale=1.0):
    drawConstructedForm(sgsm, forceScale)
    drawConstructedForce(sgsm, forceScale)

# sets up file to have correct layers
def fileSetup():

    layers = rs.LayerNames(True)

    if 'Form Diagram' in layers:

        formChildren = rs.LayerChildren('Form Diagram')
        rs.LayerColor('Form Diagram', [0, 0, 0])

        if 'Projections (Form)' in formChildren:
            rs.LayerColor('Projections (Form)', [105, 105, 105])
        else: 
            rs.AddLayer('Projections (Form)', [105, 105, 105], 
                        parent='Form Diagram')

        if 'Applied Forces (Form)' in formChildren:
            rs.LayerColor('Applied Forces (Form)', [255, 0, 0])
        else: 
            rs.AddLayer('Applied Forces (Form)', [255, 0, 0], 
                        parent='Form Diagram')

        if 'Deck' in formChildren:
            rs.LayerColor('Deck', [0, 0, 0])
        else: 
            rs.AddLayer('Deck', [0, 0, 0], parent='Form Diagram')

        if 'Cables' in formChildren:
            rs.LayerColor('Cables', [105, 105, 105])
        else: 
            rs.AddLayer('Cables', [105, 105, 105], 
                        parent='Form Diagram')

    else:
        rs.AddLayer('Form Diagram')
        rs.AddLayer('Projections (Form)', [105, 105, 105], 
                    parent='Form Diagram')
        rs.AddLayer('Applied Forces (Form)', [255, 0, 0], 
                    parent='Form Diagram')
        rs.AddLayer('Deck', [0, 0, 0], parent='Form Diagram')
        rs.AddLayer('Cables', [105, 105, 105], parent='Form Diagram')

    if 'Force Diagram' in layers:

        forceChildren = rs.LayerChildren('Force Diagram')
        rs.LayerColor('Force Diagram', [0, 0, 0])

        if 'Projections (Force)' in formChildren:
            rs.LayerColor('Projections (Force)', [105, 105, 105])
        else: 
            rs.AddLayer('Projections (Force)', [105, 105, 105], 
                        parent='Force Diagram')

        if 'Applied Forces (Force)' in formChildren:
            rs.LayerColor('Applied Forces (Force)', [105, 105, 105])
        else: 
            rs.AddLayer('Applied Forces (Force)', [105, 105, 105], 
                        parent='Force Diagram')

    else:
        rs.AddLayer('Force Diagram')
        rs.AddLayer('Projections (Force)', [105, 105, 105], 
                    parent='Force Diagram')
        rs.AddLayer('Applied Forces (Force)', [255, 0, 0], 
                    parent='Force Diagram')