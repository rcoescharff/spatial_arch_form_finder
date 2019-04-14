import openpyxl
import fromdeck
from bridge import Bridge
import math
import nonfunicular

# open template Excel spreadsheet
_wb = openpyxl.load_workbook('sap_template.xlsx')

# get column letter from index col
def _col(col):
    if col < 26:
        column = chr(col + 65)
    else:
        column = chr(col // 26 + 64)
        column += chr(col % 26 + 65)
    return column

# get column-row string ('A1') from col string and row index
def _i(col, row=0):
    return col + str(row + 4)

# get dictionary representing bridge with cables cables where key is 
# member number and value is its start and end coordinates
def getMembers(bridge, cables):
    
    segments = bridge.segments()
    assert(segments % (cables + 1) == 0)
    members = {}
    arch = bridge.getArch()
    deck = bridge.getDeck()

    for i in range(segments):
        members[i+1] = [deck[i], deck[i+1]]
        members[segments+i+1] = [arch[i], arch[i+1]]

    inc = segments // (cables + 1)
    for i in range(1, cables + 1):
        members[segments*2+i] = [arch[i*inc], deck[i*inc]]

    return members

# get dictionary from bridge where key is joint coordinates and value 
# is joint number
def getJoints(bridge):
    joints = {}
    for i in range(len(bridge.getDeck())):
        joints[bridge.getDeck()[i]] = i + 1
        joints[bridge.getArch()[i]] = i + len(bridge.getDeck()) + 1  
    return joints

# get length from start and end pair ends
def length(ends):
    return (ends[0] - ends[1]).length()

# get x-coordinate of centroid from start and end pair ends
def centX(ends):
    return (ends[0].x() + ends[1].x()) / 2.

# get y-coordinate of centroid from start and end pair ends
def centY(ends):
    return (ends[0].y() + ends[1].y()) / 2.

# get z-coordinate of centroid from start and end pair ends
def centZ(ends):
    return (ends[0].z() + ends[1].z()) / 2.

# get total length of all members in members
def totalLen(members):
    l = 0
    for i, m in members.items():
        l += length(m)
    return l

# get total weight based on total length totLen and part 'arch', 'deck', 
# or 'cable'
def totalWeight(totLen, part):

    matProp2 = _wb.get_sheet_by_name('MatProp 02 - Basic Mech Props')
    matList1 = _wb.get_sheet_by_name('Material List 1 - By Obj Type')
    frameProps01 = _wb.get_sheet_by_name('Frame Props 01 - General')
    cableSecDefs = _wb.get_sheet_by_name('Cable Section Definitions')

    if part == 'arch': 
        mat = matList1[_i('B')].value
        secArea = frameProps01[_i('J')].value
    elif part == 'deck':
        mat = matList1[_i('B')].value
        secArea = frameProps01[_i('J', 1)].value
    elif part == 'cable':
        mat = matList1[_i('B', 1)].value
        secArea = cableSecDefs[_i('E')].value
    else: raise Exception("invalid input")

    i = 0
    material = ""
    unitWeight = 0
    while matProp2[_i('A', i)].value != '':
        material = matProp2[_i('A', i)].value 
        if material == mat:
            unitWeight = matProp2[_i('B', i)].value 
            break
        i += 1

    if material == "":
        raise Exception("Materials not consistent")

    return unitWeight * secArea * totLen

# get total mass based on total length totLen and part
def totalMass(totLen, part):

    matProp2 = _wb.get_sheet_by_name('MatProp 02 - Basic Mech Props')
    matList1 = _wb.get_sheet_by_name('Material List 1 - By Obj Type')
    frameProps01 = _wb.get_sheet_by_name('Frame Props 01 - General')
    cableSecDefs = _wb.get_sheet_by_name('Cable Section Definitions')

    if part == 'arch': 
        mat = matList1[_i('B')].value
        secArea = frameProps01[_i('J')].value
    elif part == 'deck':
        mat = matList1[_i('B')].value
        secArea = frameProps01[_i('J', 1)].value
    elif part == 'cable':
        mat = matList1[_i('B', 1)].value
        secArea = cableSecDefs[_i('E')].value
    else: raise Exception("invalid input")

    i = 0
    material = ""
    unitMass = 0
    while matProp2[_i('A', i)].value != '':
        material = matProp2[_i('A', i)].value
        if material == mat:
            unitMass = matProp2[_i('C', i)].value
            break
        i += 1

    if material == "":
        raise Exception("Materials not consistent")

    return unitMass * secArea * totLen

# get Excel workbook based on members dictionary, joints dictionary, 
# list of cable loads cableLoads, load (q - deck weight), and file 
# identifier name
def getWorkBook(members, joints, segments, cableLoads, load, name):

    frames = segments * 2
    cables = len(members) - segments * 2
    if len(members) != frames + cables:
        raise Exception()

    deckMem = {i: members[i] for i in range(1, segments + 1)}
    archMem = {i: members[i] for i in 
                    range(segments + 1, segments*2 + 1)}
    cableMem = {i: members[i] for i in 
                    range(segments*2 + 1, len(members) + 1)}

    deckLen = totalLen(deckMem)
    archLen = totalLen(archMem)
    cableLen = totalLen(cableMem)

    deckWeight = totalWeight(deckLen, 'deck')
    archWeight = totalWeight(archLen, 'arch')
    cableWeight = totalWeight(cableLen, 'cable')

    deckMass = totalMass(deckLen, 'deck')
    archMass = totalMass(archLen, 'arch')
    cableMass = totalMass(cableLen, 'cable')

    frameConnect = _wb.get_sheet_by_name('Connectivity - Frame')
    cableOutput = _wb.get_sheet_by_name('Cable Output Station Assigns')
    cableSecAssign = _wb.get_sheet_by_name('Cable Section Assignments')
    cableSecDefs = _wb.get_sheet_by_name('Cable Section Definitions')
    cableShape = _wb.get_sheet_by_name('Cable Shape Data')
    cableConnect = _wb.get_sheet_by_name('Connectivity - Cable')
    frameAutoMesh = _wb.get_sheet_by_name('Frame Auto Mesh')
    frameDesign = _wb.get_sheet_by_name('Frame Design Procedures')
    frameLoadTrans = \
        _wb.get_sheet_by_name('Frame Load Transfer Options')
    frameLoads = _wb.get_sheet_by_name('Frame Loads - Distributed')
    frameOutput = _wb.get_sheet_by_name('Frame Output Station Assigns')
    frameSecAssign = _wb.get_sheet_by_name('Frame Section Assignments')
    frameProps01 = _wb.get_sheet_by_name('Frame Props 01 - General')
    groups3 = _wb.get_sheet_by_name('Groups 3 - Masses and Weights')
    jointCoords = _wb.get_sheet_by_name('Joint Coordinates')
    jointRestraints = \
        _wb.get_sheet_by_name('Joint Restraint Assignments')
    matList1 = _wb.get_sheet_by_name('Material List 1 - By Obj Type')
    matList2 = _wb.get_sheet_by_name('Material List 2 - By Sect Prop')
    overSteel = _wb.get_sheet_by_name('Over Steel - AISC 360-10')

    cableSec = cableSecDefs[_i('A')].value
    archRow = 0
    deckRow = 1

    cableSecDefs[_i('J')] = cableWeight
    cableSecDefs[_i('K')] = cableMass

    frameProps01[_i('Z', deckRow)] = deckWeight
    frameProps01[_i('AA', deckRow)] = deckMass
    frameProps01[_i('Z', archRow)] = archWeight
    frameProps01[_i('AA', archRow)] = archMass

    groups3[_i('B')] = deckMass + archMass + cableMass
    groups3[_i('C')] = deckWeight + archWeight + cableWeight
    groups3[_i('D')] = deckMass + archMass + cableMass
    groups3[_i('E')] = deckMass + archMass + cableMass
    groups3[_i('F')] = deckMass + archMass + cableMass

    jointRestraints[_i('A', 0)] = joints[members[1][0]]
    jointRestraints[_i('A', 1)] = joints[members[segments][1]]
    jointRestraints[_i('A', 2)] = joints[members[segments + 1][0]]
    jointRestraints[_i('A', 3)] = joints[members[segments * 2][1]]

    for i in range(4):
        jointRestraints[_i('B', i)] = 'Yes'
        jointRestraints[_i('C', i)] = 'Yes'
        jointRestraints[_i('D', i)] = 'Yes'
        jointRestraints[_i('E', i)] = 'No'
        jointRestraints[_i('F', i)] = 'No'
        jointRestraints[_i('G', i)] = 'No'

    matList1[_i('C', 0)] = deckWeight + archWeight
    matList1[_i('C', 1)] = cableWeight
    matList1[_i('D', 0)] = frames 
    matList1[_i('D', 1)] = cables 

    matList2[_i('C', 0)] = segments
    matList2[_i('C', 1)] = segments
    matList2[_i('C', 2)] = cables
    matList2[_i('D', 0)] = deckLen
    matList2[_i('D', 1)] = archLen
    matList2[_i('D', 2)] = cableLen
    matList2[_i('E', 0)] = archWeight
    matList2[_i('E', 1)] = deckWeight
    matList2[_i('E', 2)] = cableWeight

    i = 0
    for i in range(frames):

        frameConnect[_i('A', i)] = i + 1
        frameConnect[_i('B', i)] = joints[members[i+1][0]]
        frameConnect[_i('C', i)] = joints[members[i+1][1]]
        frameConnect[_i('D', i)] = 'No'
        frameConnect[_i('E', i)] = length(members[i+1])
        frameConnect[_i('F', i)] = centX(members[i+1])
        frameConnect[_i('G', i)] = centY(members[i+1])
        frameConnect[_i('H', i)] = centZ(members[i+1])

        frameAutoMesh[_i('A', i)] = i + 1
        frameAutoMesh[_i('B', i)] = 'Yes'
        frameAutoMesh[_i('C', i)] = 'Yes'
        frameAutoMesh[_i('D', i)] = 'No'
        frameAutoMesh[_i('E', i)] = 0
        frameAutoMesh[_i('F', i)] = 0
        frameAutoMesh[_i('G', i)] = 0

        frameDesign[_i('A', i)] = i + 1
        frameDesign[_i('B', i)] = 'From Material'

        frameLoadTrans[_i('A', i)] = i + 1
        frameLoadTrans[_i('B', i)] = 'Yes'

        if i < segments:
            frameLoads[_i('A', i)] = i + 1
            frameLoads[_i('B', i)] = 'DEAD'
            frameLoads[_i('C', i)] = 'GLOBAL'
            frameLoads[_i('D', i)] = 'Force'
            frameLoads[_i('E', i)] = 'Gravity'
            frameLoads[_i('F', i)] = 'RelDist'
            frameLoads[_i('G', i)] = 0
            frameLoads[_i('H', i)] = 1
            frameLoads[_i('I', i)] = 0
            frameLoads[_i('J', i)] = length(members[i+1])
            frameLoads[_i('K', i)] = load
            frameLoads[_i('L', i)] = load

        frameOutput[_i('A', i)] = i + 1
        if i < segments:
            frameOutput[_i('B', i)] = 'MaxStaSpcg'
            frameOutput[_i('D', i)] = 24
        else:
            frameOutput[_i('B', i)] = 'MinNumSta'
            frameOutput[_i('C', i)] = 3
        frameOutput[_i('E', i)] = 'Yes'
        frameOutput[_i('F', i)] = 'Yes'

        frameSecAssign[_i('A', i)] = i + 1
        if i < segments:
            row = deckRow    
        else:
            row = archRow
        frameSecAssign[_i('B', i)] = frameProps01[_i('C', row)].value
        frameSecAssign[_i('C', i)] = 'N.A.'
        frameSecAssign[_i('D', i)] = frameProps01[_i('A', row)].value
        frameSecAssign[_i('E', i)] = frameProps01[_i('A', row)].value
        frameSecAssign[_i('F', i)] = 'Default'

        overSteel[_i('A', i)] = i + 1
        for j in range(1, 45):
            overSteel[_i(_col(j), i)] = 0
        for c in ['B', 'C', 'V', 'W', 'AF', 'AG']:
            overSteel[_i(c, i)] = 'Program Determined'

    i = 0
    for i in range(cables):

        cableOutput[_i('A', i)] = i + frames + 1
        cableOutput[_i('B', i)] = 'MinNumSta'
        cableOutput[_i('C', i)] = 3
        cableOutput[_i('E', i)] = 'Yes'
        cableOutput[_i('F', i)] = 'Yes'

        cableSecAssign[_i('A', i)] = i + frames + 1
        cableSecAssign[_i('B', i)] = cableSec
        cableSecAssign[_i('C', i)] = 'Default'

        cableShape[_i('A', i)] = i + frames + 1
        cableShape[_i('B', i)] = 'Tension At I-End'
        cableShape[_i('C', i)] = 1
        cableShape[_i('D', i)] = cableLoads[i]
        cableShape[_i('H', i)] = 0
        cableShape[_i('I', i)] = length(members[i+frames+1])
        cableShape[_i('K', i)] = 0
        cableShape[_i('L', i)] = 0
        cableShape[_i('M', i)] = 'No'
        cableShape[_i('N', i)] = 'No'

        cableConnect[_i('A', i)] = i + frames + 1
        cableConnect[_i('B', i)] = joints[members[i+frames+1][0]]
        cableConnect[_i('C', i)] = joints[members[i+frames+1][1]]
        cableConnect[_i('D', i)] = length(members[i+frames+1])

    for p,n in joints.items():

        jointCoords[_i('A', n-1)] = n
        jointCoords[_i('B', n-1)] = 'GLOBAL'
        jointCoords[_i('C', n-1)] = 'Cartesian'
        jointCoords[_i('D', n-1)] = p.x()
        jointCoords[_i('E', n-1)] = p.y()
        jointCoords[_i('F', n-1)] = p.z()
        jointCoords[_i('G', n-1)] = 'No'
        jointCoords[_i('H', n-1)] = p.x()
        jointCoords[_i('I', n-1)] = p.y()
        jointCoords[_i('J', n-1)] = p.z()

    _wb.save('sap_' + name + '.xlsx')

# get unit weight of frames
def frameUnitWeight():

    matProp2 = _wb.get_sheet_by_name('MatProp 02 - Basic Mech Props')
    matList1 = _wb.get_sheet_by_name('Material List 1 - By Obj Type')

    mat = matList1[_i('B')].value
    i = 0
    material = ""
    unitWeight = 0

    while matProp2[_i('A', i)].value != '' \
            and matProp2[_i('A', i)].value != None:
        material = matProp2[_i('A', i)].value 
        if material == mat:
            unitWeight = matProp2[_i('B', i)].value 
            break
        i += 1

    if material == "":
        raise Exception("Materials not consistent")

    return unitWeight

# get Excel spreadsheet from bridge, q, number of cables, and file name
def toSAP(bridge, q, cables, name):

    frameProps01 = _wb.get_sheet_by_name('Frame Props 01 - General')
    secAreaDeck = frameProps01[_i('J', 1)].value
    qDeck = frameUnitWeight() * secAreaDeck
    load = q - qDeck
    if load < 0:
        raise Exception("load must be at least deck weight")

    members = getMembers(bridge, cables)
    joints = getJoints(bridge)
    cableForces = bridge.getCableForces(q)
    segments = bridge.segments()
    getWorkBook(members, joints, segments, cableForces, load, name)

# get Excel spreadsheet and text file with SGSM results for funicular 
# bridge based on typical input parameters, number of cables, and file 
# name
def toSAPfun(deck, L, anchorOffset, H, q, segments, cables, name):

    frameProps01 = _wb.get_sheet_by_name('Frame Props 01 - General')
    secAreaArch = frameProps01[_i('J')].value
    qArch = frameUnitWeight() * secAreaArch
    
    bridge = fromdeck.fromDeck(deck, L, anchorOffset, H, q, qArch, 
                                segments)
    toSAP(bridge, q, cables, name)

    cableForces = bridge.getCableForces(q)

    f = open("gs_" + name + ".txt", "w")
    forces = bridge.getArchForces()
    for i in range(segments):
        f.write(str(segments + i + 1) + "\t" + str(forces[i]) + "\n")
    for i in range(cables):
        f.write(str(segments*2 + 1 + i) + "\t" \
                        + str(cableForces[i]) + "\n")
    reactions = bridge.getArchReactions(qArch)
    for i in range(len(reactions)):
        f.write("R" + str(i+1) + "\t" + str(reactions[i]) + "\n")

    return bridge

# get Excel spreadsheet for non-funicular bridge based on arch function,
# deck function, length L, anchor offset, loading q, segments, number of 
# cables, and file name
def toSAPnonFun(arch, deck, L, anchorOffset, q, segments, cables, name):
    bridge = nonfunicular.getBridge(arch, deck, L, segments, 
                                        anchorOffset)
    toSAP(bridge, q, cables, name)
    return bridge  

# produce spreadsheets and data files for each bridge in Section 3.1
def testRanges():

    mind = 0.
    maxd = 700.
    minq = .05
    maxq = .55
    minH = 5.
    maxH = 55.
    minSegs = 5
    maxSegs = 55
    minAO = -90.
    maxAO = 210.
    
    incd = 50.
    incq = .02
    incH = 5.
    incSegs = 2
    incAO = 20.
    stL = 850.
    std = 250.
    stq = .15
    stH = 30.
    stSegs = 15
    stAO = 110.

    ao = minAO
    while ao <= maxAO:
        toSAPfun(fromdeck.parabolicDeck(stL, std), stL, ao, stH, stq, 
            stSegs, stSegs - 1, "ao=" + str(ao))
        ao += incAO

    d = mind
    while d <= maxd:
        toSAPfun(fromdeck.parabolicDeck(stL, d), stL, stAO, stH, stq, 
            stSegs, stSegs - 1, "d=" + str(d))
        d += incd

    H = minH
    while H <= maxH:
        toSAPfun(fromdeck.parabolicDeck(stL, std), stL, stAO, H, stq, 
            stSegs, stSegs - 1, "H=" + str(H))
        H += incH

    q = minq
    while q <= maxq:
        toSAPfun(fromdeck.parabolicDeck(stL, std), stL, stAO, stH, q, 
            stSegs, stSegs - 1, "q=" + str(q))
        q += incq

    segs = minSegs
    while segs <= maxSegs:
        toSAPfun(fromdeck.parabolicDeck(stL, std), stL, stAO, stH, stq, 
            segs, segs - 1, "segs=" + str(segs))
        segs += incSegs

# produce spreadsheets for each bridge in Section 3.2
def testNonFunicular():

    L = 850.
    deckD = 250.
    q = .15
    H = 30.
    segs = 15
    ao = 110.
    deck = fromdeck.parabolicDeck(L, deckD)

    fun = toSAPfun(deck, L, ao, H, q, segs, segs - 1, 'funicular')
    angleFun = fun.archAngle()
    print 'theta = {:.2f}'.format(angleFun * 180. / math.pi)
    r = fun.archRadius()
    print 'r = {:.2f}'.format(r)

    iterations = 11
    minAngle = max(angleFun - math.pi / 4., math.pi / 8.)
    maxAngle = min(angleFun + math.pi / 4., 7. * math.pi / 8.)
    incAngle = inc(minAngle, maxAngle, iterations)

    for i in range(iterations):
        angle = minAngle + i * incAngle
        arch = nonfunicular.parabArchPolar(L, angle, r)
        name = 'alt-a={:.2f}'.format(angle * 180. / math.pi)
        toSAPnonFun(arch, deck, L, ao, q, segs, segs - 1, name)

if __name__ == '__main__':
    testRanges()
    testNonFunicular()