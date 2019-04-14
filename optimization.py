import fromdeck
from vector import Vector
from bridge import Bridge
import math

# Optimization function, returns Bridge deck defined by deck function, 
# and parameters L, q, qArch (q_arch), and segs (segments). If H is
# None and anchOff (anchor offset) is given, H is changing variable,
# if anchOff is None and H is given, anchor offset is changing variable.
# isArch is true if H > 0, required when H = None. optGlob minimized the
# value of func(bridge).
def optGlob(deck, L, q, qArch, segs, func, isArch=None, H=None, anchOff=None):

    try:
        step = 10.

        if H == None:

            if isArch:
                startHmin = 0.
                startHmax = q * 10000
            else:
                startHmin = -q * 10000
                startHmax = 0.

            minB = None
            minBVal = float('inf')
            minBH = None
            Hmin = startHmin
            Hmax = startHmax

            while step > 0.001:
                H = Hmin + step
                while H < Hmax:
                    b = fromdeck.fromDeck(deck, L, anchOff, H, q, 
                                                qArch, segs)
                    if func(b) < minBVal:
                        minBVal = func(b)
                        minB = b
                        minBH = H
                    H += step
                Hmin = max(minBH - step, Hmin)
                Hmax = min(minBH + step, Hmax)
                step /= 10.

            if minBH <= startHmin + step * 10. \
                    or minBH >= startHmax - step * 10:
                print minBH
                print 'Exceeded Limit'
                return

        elif anchOff == None:
            
            dDeck = fromdeck.getDeckDepth(deck, L)
            startAOmin = -dDeck * 2
            startAOmax = dDeck * 2

            minB = None
            minBVal = float('inf')
            minBAO = None
            AOmin = startAOmin
            AOmax = startAOmax

            while step > 0.001:
                AO = AOmin + step
                while AO < AOmax:
                    b = fromdeck.fromDeck(deck, L, AO, H, q, qArch, 
                                            segs)
                    if func(b) < minBVal:
                        minBVal = func(b)
                        minB = b
                        minBAO = AO
                    AO += step
                AOmin = max(minBAO - step, AOmin)
                AOmax = min(minBAO + step, AOmax)
                step /= 10.

            if minBAO <= startAOmin + step*10. \
                    or minBAO >= startAOmax - step*10:
                print minBAO
                print 'Exceeded Limit'
                return

        return minB

    except Exception as e:
        print e

# returns dictionary of optimization input functions, input is required
# for functions that include those variables.
def optDict(q=None, qArch=None, sigArch=1., sigCab=1., h=None):
    d = {'cable force': (lambda x: x.maxCableForce(q), True, False),
          'arch force': (lambda x: x.maxArchForce(), True, True),
          'y react': (lambda x: abs(x.getArchReactions(qArch)[0].y()), 
                        True, False),
          'z react': (lambda x: abs(x.getArchReactions(qArch)[0].z()), 
                        True, False),
          'arch height': (lambda x: x.archHeight(), True, False),
          'arch depth': (lambda x: x.archDepth(), True, False),
          'arch radial length': (lambda x: x.archRadius(), True, False),
          'deck moment': (lambda x: x.maxDeckMomentZ(q), True, False),
          'axial force': 
                (lambda x: max(x.maxCableForce(q), x.maxArchForce()), 
                    True, True),
          'load path': (lambda x: x.loadPath(q, sigArch, sigCab), 
                            True, True),
          'select arch height': (lambda x: abs(h - x.archHeight()), 
                                    True, True)}
    return d

# returns list of input functions that have minimums for whichever of 
# the arguments are True
def optList(H=False, anchOff=False):
    dList = optDict().items()
    if H:
        dList = filter(lambda x: x[1][2], dList)
    if anchOff:
        dList = filter(lambda x: x[1][1], dList)
    l = map(lambda x: x[0], dList)
    return l

# returns optimization input function identified by string s
def optFunc(s, q=None, qArch=None, sigArch=1., sigCab=1., h=None):
    d = optDict(q, qArch, sigArch, sigCab, h)
    return d[s][0]

# runs optimization for all the built-in input functions and for each
# changing variable and returns a dictionary of results
def optAll(deck, L, q, qArch, segs, H, anchOff, h):

    if H > 0.: isArch = True
    else: isArch = False

    optD = optDict(q, qArch, h=h)
    d = {}
    for s, c in optD.items():
        d[s] = {}
        opt = c[0]
        if c[1]: 
            d[s]['AO'] = optGlob(deck, L, q, qArch, segs, opt, H=H)
        if c[2]:
            d[s]['H'] = optGlob(deck, L, q, qArch, segs, opt, isArch, 
                                    anchOff=anchOff)
    
    return d

# prints value of changing variable for bridge b and variable 
# identifier t
def _printInd(t, b):
    if t == 'H':
        return str(b.getH())
    elif t == 'AO':
        return str(b.getAnchOff())
    else:
        raise Exception('_printInd: t must equal "H" or "AO"')

# prints d, the results of optAll
def printOpts(d):
    for s, ts in d.items():
        print s
        for t, b in ts.items():
            if b != None:
                print t + "=" + _printInd(t, b)