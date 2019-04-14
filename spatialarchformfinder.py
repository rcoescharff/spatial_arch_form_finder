import rhinoscriptsyntax as rs
import math
import fromdeck as fd
import optimization as opt
import Rhino.Geometry as rg
import rhinobridge
import rhinosgsm

# get string from command line, exit on Esc
def getString(message=None, defaultString=None, strings=None):
    res = rs.GetString(message, defaultString, strings)
    if res == None:
        exit()
    else:
        return res

# get float from command line, exit on Esc
def getReal(message=None, number=None, minimum=None, maximum=None):
    res = rs.GetReal(message, number, minimum, maximum)
    if res == None:
        exit()
    else:
        return res

# get int from command line, exit on Esc       
def getInteger(message=None, number=None, minimum=None, maximum=None):
    res = rs.GetInteger(message, number, minimum, maximum)
    if res == None:
        exit()
    else:
        return res

# prompt user to enter information and draw resulting bridge
def main():
    
    # enter deck related attributes
    deckType = getString("Enter deck specification method", "parabolic",
                             ["parabolic", "sinusoidal", "custom"])
    objects = None

    if deckType == "parabolic":
        L = getReal("Enter deck length (L)", minimum=0.0001)
        d = getReal("Enter deck depth (d_deck)", minimum=0.)
        h = getReal("Enter deck height (h_deck)", 0.)
        deck = fd.parabolicDeck(L, d, h)
        segs = getInteger(
                    "Enter number of segments to approximate arch", 
                    minimum=2)

    elif deckType == "sinusoidal":
        L = getReal("Enter deck length (L)", minimum=0.0001)
        A = getReal("Enter deck amplitude (A)", minimum=0.)
        lmda = getReal("Enter deck wavelength (lambda)", L, minimum=0.0001)
        phi = getReal("Enter deck phase (phi)", 0., 0., 2 * math.pi)
        h = getReal("Enter deck height (h_deck)", 0.)
        deck = fd.sineDeck(L, A, lmda, phi, h)
        segs = getInteger(
                    "Enter number of segments to approximate arch", 
                    minimum=2)
    else:

        objects = rs.GetObjects("Select deck curve(s)", 
                                preselect=True, minimum_count=1)
        isValid = False
        for o in objects:
            end = rs.CurveEndPoint(o)
            start = rs.CurveStartPoint(o)
            if end.X < -0.0001 or start.X < -0.0001:
                isValid = False
                break
            elif abs(end.X) <= 0.0001:
                if abs(end.Y <= 0.0001) and abs(end.Z <= 0.0001):
                    isValid = True
                    break
            elif abs(start.X) <= 0.0001:
                if abs(start.Y <= 0.0001) and abs(start.Z <= 0.0001):
                    isValid = True
                    break

        if isValid == False:
            print "Deck must start at origin"
            exit()

        if len(objects) == 1:
            o = objects[0]
            deck = lambda x: rhinosgsm.ptToVect(rs.EvaluateCurve(o,
                               rs.CurveClosestPoint(o, [x,0.,0.])))
            L = rs.CurveEndPoint(o).X - rs.CurveStartPoint(o).X
            segs = getInteger(
                        "Enter number of segments to approximate arch", 
                        minimum=2)

        else:
            deck = [rhinosgsm.ptToVect(rs.CurveStartPoint(objects[0]))]
            for o in objects:
                deck.append(rhinosgsm.ptToVect(rs.CurveEndPoint(o)))
            xEnd = lambda o: max(rs.CurveStartPoint(o).X, 
                                 rs.CurveEndPoint(o).X)
            L = max(map(xEnd, objects))
            segs = None
    
    # enter loads
    q = getReal("Enter load on deck (q)", minimum=0.0001)
    qArch = getReal("Enter self-weight of arch (q_arch)", 
                        minimum=0.0001)
    
    # choose whether or not to optimize
    isOpt = getString("Do you want to use an optimization function?", 
                        "yes", ["yes", "no"])

    # produce optimized form
    if isOpt == "yes":

        var = getString("Enter the variable you want to change", 
                            strings=["H", "anchorOffset"])

        if var == "H":
            sign = getString("Enter the sign of H", "positive", 
                            strings=["positive", "negative"])
            if sign == "positive":
                isArch = True
            else:
                isArch = False
            anchOff = getReal("Enter anchor offset", 0.)
            H = None

        else:
            H = 0.
            while not H != 0.:
                H = getReal("Enter horizontal force (H)")
                if not H != 0.:
                    print "H may not equal 0.0"
            anchOff = None
            isArch = None
        
        optParam = rs.ListBox(opt.optList(var=="H", 
                                var=="anchorOffset"), 
                            "Select optimization parameter",
                            "Optimization Parameters")

        if optParam == "select arch height":
            hArch = getReal("Enter arch height", minimum=0.0001)
        else:
            hArch = None

        func = opt.optFunc(optParam, q, qArch, h=hArch)
        bridge = opt.optGlob(deck, L, q, qArch, segs, func, isArch, H, 
                                anchOff)
        
        if H == None:
            print "H =", bridge.getH()
        else:
            print "anchor offset =", bridge.getAnchOff()
    
    # produce non-optimized form
    else:
        H = 0.
        while not H != 0.:
            H = getReal("Enter horizontal force (H)")
            if not H != 0.:
                print "H may not equal 0.0"
        anchOff = getReal("Enter anchor offset", 0.)
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)

    if segs == None:
        segs = len(objects)
    
    # draw bridge
    cables = getInteger("Enter number of cables to draw", segs - 1, 1, 
                            segs - 1)
    
    if objects != None:
        rs.DeleteObjects(objects)

    rhinobridge.drawBridge(bridge, cables)

if __name__ == '__main__':
    main()