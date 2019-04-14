import optimization as opt
import fromdeck as fd 
import matplotlib.pyplot as plt
from bridge import Bridge
import math

# dictionary of units used
units = {'f': '(k)', 'l': '(in)', 'm': '(k-in)', 'fpl': '(k/in)', 
         'a': '(degrees)'}

# graph func(bridge) vs. H where funcName a tuple (func name, 
# func units) and the other arguments are bridge parameters
def graphFuncH(deck, L, q, qArch, segs, anchOff, funcName, func):

    minH = 5.
    maxH = 55.
    steps = 50
    inc = (maxH - minH)/steps
    H = minH

    Hs = []
    results = []

    for i in range(steps):
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        Hs.append(H)
        results.append(func(bridge))
        H += inc

    plt.plot(Hs, results)
    plt.xlabel("horizontal force (H) " + units['f'])
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of H")
    plt.show()

# graph func(bridge) vs. anchor offset
def graphFuncAO(deck, L, q, qArch, segs, H, funcName, func):

    minAO = -90.
    maxAO = 400.
    steps = 50
    inc = (maxAO - minAO)/steps
    anchOff = minAO

    anchOffs = []
    results = []

    for i in range(steps):
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        anchOffs.append(anchOff)
        results.append(func(bridge))
        anchOff += inc

    plt.plot(anchOffs, results)
    plt.xlabel("anchor offset " + units['l'])
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of anchor offset")
    plt.show()

# graph func(bridge) vs. d_deck
def graphFuncdDeck(L, Q, qArch, segs, H, anchOffProp, funcName, func):

    mn = 0.
    mx = 700.
    steps = 50
    inc = (mx - mn)/steps
    d = mn

    ds = []
    results = []

    for i in range(steps):
        deck = fd.parabolicDeck(L, d)
        deckLen = sum(fd.getDeckLengths(deck, L, segs))
        q = Q / deckLen
        anchOff = anchOffProp * d
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        ds.append(d)
        results.append(func(bridge))
        d += inc

    plt.plot(ds, results)
    plt.xlabel("Deck depth (d_deck) " + units['l'])
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of d_deck")
    plt.show()

# graph func(bridge) vs. h_deck
def graphFunchDeck(L, d, q, qArch, segs, H, anchOff, funcName, func):

    mn = 0.
    mx = 500.
    steps = 50
    inc = (mx - mn)/steps
    h = mn

    hs = []
    results = []

    for i in range(steps):
        deck = fd.parabolicDeck(L, d, h)
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        hs.append(h)
        results.append(func(bridge))
        h += inc

    plt.plot(hs, results)
    plt.xlabel("Deck height (h_deck) " + units['l'])
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of h_deck")
    plt.show()

# graph func(bridge) vs. q
def graphFuncq(deck, L, qArch, segs, H, anchOff, funcName, func):

    mn = 0.05
    mx = 0.55
    steps = 50
    inc = (mx - mn)/steps
    q = mn

    qs = []
    results = []

    for i in range(steps):
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        qs.append(q)
        results.append(func(bridge))
        q += inc

    plt.plot(qs, results)
    plt.xlabel("Load on deck (q) " + units['fpl'])
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of q")
    plt.show()

# graph func(bridge) vs. q_arch
def graphFuncqArch(deck, L, q, segs, H, anchOff, funcName, func):

    mn = 0.01
    mx = 0.25
    steps = 50
    inc = (mx - mn)/steps
    qArch = mn

    qs = []
    results = []

    for i in range(steps):
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        qs.append(qArch)
        results.append(func(bridge))
        qArch += inc

    plt.plot(qs, results)
    plt.xlabel("Self-weight of arch (q_arch) " + units['fpl'])
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of q_arch")
    plt.show()

# graph func(bridge) vs. segments
def graphFuncSegs(deck, L, q, qArch, H, anchOff, funcName, func):

    mn = 3
    mx = 100
    steps = 50
    inc = (mx - mn)/steps
    segs = mn

    segss = []
    results = []

    for i in range(steps):
        bridge = fd.fromDeck(deck, L, anchOff, H, q, qArch, segs)
        segss.append(segs)
        results.append(func(bridge))
        segs += inc

    plt.plot(segss, results)
    plt.xlabel("Number of segments")
    plt.ylabel(funcName[0] + " " + funcName[1])
    plt.title(funcName[0] + " as a function of number of segments")
    plt.show()

# graph all built-in optimization functions against H and anchor offset
def graphOptFuncs(deck, L, q, qArch, segs, H, anchOff):

    names = {'cable force': ("Maximum force in cables", units['f']),
              'arch force': ("Maximum axial force in arch", units['f']),
              'y react': ("y reaction", units['f']),
              'z react': ("z reaction", units['f']),
              'arch height': ("Arch height (h_arch)", units['l']),
              'arch depth': ("Arch depth (d_arch)", units['l']),
              'arch radial length': 
                    ("Arch radial length (r)", units['l']),
              'deck moment': ("Maximum moment in deck", units['m']),
              'axial force': ("Maximum axial force", units['f']),
              'load path': ("Load path", units['m'])}

    optD = opt.optDict(q, qArch)
    for n, t in optD.items():
        if n != 'select arch height':
            graphFuncH(deck, L, q, qArch, segs, anchOff, names[n], t[0])
            graphFuncAO(deck, L, q, qArch, segs, H, names[n], t[0])

# graph func(bridge) vs. each of the parameters
def graphParameters(L, d, q, qArch, segs, H, anchOff, funcName, func):

    deck = fd.parabolicDeck(L, d)
    deckLen = sum(fd.getDeckLengths(deck, L, segs))
    Q = q * deckLen
    lmda = L
    phi = 0.
    anchOffProp = anchOff / d

    graphFuncH(deck, L, q, qArch, segs, anchOff, funcName, func)
    graphFuncAO(deck, L, q, qArch, segs, H, funcName, func)
    graphFuncdDeck(L, Q, qArch, segs, H, anchOffProp, funcName, func)
    graphFuncA(L, lmda, phi, Q, qArch, segs, H, anchOff, funcName, func)
    graphFunchDeck(L, d, q, qArch, segs, H, anchOff, funcName, func)
    graphFuncq(deck, L, qArch, segs, H, anchOff, funcName, func)
    graphFuncqArch(deck, L, q, segs, H, anchOff, funcName, func)
    graphFuncSegs(deck, L, q, qArch, H, anchOff, funcName, func)

def main():

    segs = 50
    L = 850.
    d = 250.
    H = 30.
    anchOff = 110.
    q = .15
    qArch = .0321
    deck = fd.parabolicDeck(L, d)

    h = opt.optFunc('arch height')
    hn = ("Arch height (h_arch)", units['l'])
    theta = lambda x: x.archAngle() * 180. / math.pi
    thetan = ('Arch angle (theta)', units['a'])
    graphParameters(L, d, q, qArch, segs, H, anchOff, hn, h)
    graphParameters(L, d, q, qArch, segs, H, anchOff, thetan, theta)

    h1 = 500.
    h2 = 660.
    selhArchN1 = ("Difference between h_arch and " + str(h1), 
                    units['l'])
    selhArchN2 = ("Difference between h_arch and " + str(h2), 
                    units['l'])
    selhArchF1 = opt.optFunc("select arch height", h=h1)
    selhArchF2 = opt.optFunc("select arch height", h=h2)
    graphFuncH(deck, L, q, qArch, segs, anchOff, selhArchN1, selhArchF1)
    graphFuncH(deck, L, q, qArch, segs, anchOff, selhArchN2, selhArchF2)
    graphFuncAO(deck, L, q, qArch, segs, H, selhArchN1, selhArchF1)
    graphFuncAO(deck, L, q, qArch, segs, H, selhArchN2, selhArchF2)

    graphOptFuncs(deck, L, q, qArch, segs, H, anchOff)

if __name__ == '__main__':
    main()