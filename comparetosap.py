import openpyxl
from vector import Vector
import os
import matplotlib.pyplot as plt
import math

# get column-row string ('A1') from col string and row index
def _i(col, row=0):
    return col + str(row + 4)

# for member n in sheet in the result Excel workbook, return a 
# dictionary containing the forces
def memberForces(sheet, n):

    count = 0.
    i = 0
    V2max = 0.
    V3max = 0.
    Tmax = 0.
    M2max = 0.
    M3max = 0.
    Psum = 0.

    while sheet[_i('A', i)].value != None:
        sheetN = sheet[_i('A', i)].value
        if  sheetN == str(n) or sheetN == n:
            count += 1.
            Psum += sheet[_i('E', i)].value
            V2 = sheet[_i('F', i)].value
            if abs(V2) > abs(V2max):
                V2max = V2
            V3 = sheet[_i('G', i)].value
            if abs(V3) > abs(V3max):
                V3max = V3
            T = sheet[_i('H', i)].value
            if abs(T) > abs(Tmax):
                Tmax = T
            M2 = sheet[_i('I', i)].value
            if abs(M2) > abs(M2max):
                M2max = M2
            M3 = sheet[_i('J', i)].value
            if abs(M3) > abs(M3max):
                M3max = M3
        i += 1

    if count <= 0.:
        return 

    return {'P': Psum / count, 'V2': V2max, 'V3': V3max,
            'T': Tmax, 'M2': M2max, 'M3': M3max}

# for reaction at row gsRow in gs file, find reaction in result sheet
# write results in compFile, and return dictionary of results
def reaction(sheet, gsRow, compFile):

    gsR = Vector(float(gsRow[1][1:-1]), 
                 float(gsRow[2][:-1]), 
                 float(gsRow[3][:-1]))

    row = int(gsRow[0][1:]) + 1
    sapR = Vector(sheet[_i('D', row)].value,
                  sheet[_i('E', row)].value,
                  sheet[_i('F', row)].value)

    diffR = gsR - sapR

    fsReact = '{0:2}  {1}  {2}  {3}\n'
    compFile.write(fsReact.format(gsRow[0], gsR.fstr(), sapR.fstr(), 
                                        diffR.fstr()))
    
    return {'Rgs': gsR, 'Rsap': sapR, 'Rdiff': diffR}

# for result file with identifier name, compare SAP to SGSM, write data
# in text file and return dictionary
def comp(name):

    if not os.path.isfile('./gs_' + name + '.txt'):
        return
    gs = open("gs_" + name + ".txt")
    gsl = gs.readlines()
    gsls = map(lambda x: x.split(), gsl)

    result = openpyxl.load_workbook('result_' + name + '.xlsx')
    elmtForces = result.get_sheet_by_name('Element Forces - Frames')
    reactions = result.get_sheet_by_name('Joint Reactions')

    compFile = open("comp_" + name + ".txt", "w")
    compFile.write("m   P (gs)   P (sap)  P diff   V2       V3       T"
                    + "        M2       M3\n")  
    fsMember = '{0:2d}  {1:7.2f}  {2:7.2f}  {3:7.2f}  {4:7.2f}  '\
                + '{5:7.2f}  {6:7.2f}  {7:7.2f}  {8:7.2f}\n'

    membersInfo = {}
    for l in gsls[:-2]:

        n = int(l[0])
        gsP = float(l[1])
        forces = memberForces(elmtForces, n)
        if forces == None:
            raise Exception("Error reading result_" + name + ".xlsx")

        diffP = gsP - forces['P']
        forces['Pgs'] = gsP
        forces['Pdiff'] = diffP

        compFile.write(fsMember.format(n, gsP, forces['P'], diffP,
                                        forces['V2'], forces['V3'],
                                        forces['T'], forces['M2'],
                                        forces['M3']))
        membersInfo[n] = forces

    R1 = reaction(reactions, gsls[len(gsls)-2], compFile)
    R2 = reaction(reactions, gsls[len(gsls)-1], compFile)
    membersInfo['R1'] = R1
    membersInfo['R2'] = R2

    return membersInfo

# get average differences for each file in files
def compSet(files):

    compInfo = {}

    for f in files:

        info = comp(f[7:-5])
        if info != None:
            ParchSum = 0.
            PcableSum = 0.
            archCount = 0
            cables = (len(info) - 2) // 2
            archMems = cables + 1

            for n, d in info.items():
                if n == 'R1' or n == 'R2':
                    continue
                elif archCount < archMems:
                    Pgs = d['Pgs']
                    Pdiff = d['Pdiff']
                    ParchSum += abs(Pdiff / Pgs)
                    archCount += 1
                else:
                    Pgs = d['Pgs']
                    Pdiff = d['Pdiff']
                    PcableSum += abs(Pdiff / Pgs)

            Parch = ParchSum / archMems * 100.
            Pcable = PcableSum / cables * 100.
            Rgs = info['R1']['Rgs']
            Rdiff = info['R1']['Rdiff']

            Rx = abs(Rdiff.x() / Rgs.x()) * 100.
            if Rgs.y() != 0.:
                Ry = abs(Rdiff.y() / Rgs.y()) * 100.
            elif Rdiff.y() != 0.:
                Ry = 100.
            else:
                Ry = 0.
            Rz = abs(Rdiff.z() / Rgs.z()) * 100.

            d = {'Parch': Parch, 'Pcable': Pcable,
                 'Rx': Rx, 'Ry': Ry, 'Rz': Rz}
            compInfo[f[7:-5]] = d

    return compInfo

# get tuple (variable name, variable value, dictionary) from tuple
# (file identifier, dictionary)
def _valFromName(tup):
    name = tup[0]
    ns = name.split("=")
    return (ns[0], float(ns[1]), tup[1])

# graph differences as a function of param
def graph(param):

    parameters = {'ao': ['anchor offset', ' (in)'], 
                  'd': ['depth of deck curvature', ' (in)'],
                  'H': ['horizontal force', ' (k)'],
                  'L': ['length', ' (in)'],
                  'q': ['load on deck', ' (k)'],
                  'segs': ['number of arch segments', '']}

    cwd = os.getcwd()
    files = os.listdir(cwd)
    isParamResult = lambda x: x[:7+len(param)] == 'result_' + param
    resultFiles = filter(isParamResult, files)
    info = compSet(resultFiles)

    xs = []
    Parch = []
    Pcable = []
    Rx = []
    Ry = []
    Rz = []

    infoSorted = sorted(map(_valFromName, info.items()))
    for f, n, d in infoSorted:
        xs.append(n)
        Parch.append(d['Parch'])
        Pcable.append(d['Pcable'])
        Rx.append(d['Rx'])
        Ry.append(d['Ry'])
        Rz.append(d['Rz'])

    plt.plot(xs, Parch, linestyle='-', 
                label='average axial force in arch')
    plt.plot(xs, Pcable, linestyle='--', 
                label='average axial force in cables')
    plt.plot(xs, Rx, linestyle='-.', 
                label='x component of arch reaction')
    plt.plot(xs, Ry, linestyle=':', 
                label='y component of arch reaction')
    plt.plot(xs, Rz, linestyle=(0,(1,3)), 
                label='z component of arch reaction')
    plt.legend()
    plt.xlabel(parameters[param][0] + parameters[param][1])
    plt.ylabel("percent difference between SAP2000 and SGSM")
    plt.title('Difference between SAP2000 and SGSM as a function of '
                + parameters[param][0])
    plt.show()

# get h_arch of structure in SAP spreadsheet wb
def sapArchHeight(wb):
    jc = wb.get_sheet_by_name("Joint Coordinates")
    i = 0
    maxz = 0.
    while jc[_i('A', i)].value != None:
        z = jc[_i('F', i)].value
        maxz = max(z, maxz)
        i += 1
    return maxz

# get d_arch of structure in SAP spreadsheet wb
def sapArchDepth(wb):
    jc = wb.get_sheet_by_name("Joint Coordinates")

# get L of structure in SAP spreadsheet wb
def sapL(wb):
    jc = wb.get_sheet_by_name("Joint Coordinates")
    i = 0
    maxz = 0.
    while jc[_i('A', i)].value != None:
        z = jc[_i('D', i)].value
        maxz = max(z, maxz)
        i += 1
    return maxz

# get dictionary with h_arch, d_arch, L, r, and theta for each file in
# files
def getShapeData(files):

    data = {}
    for f in files:

        n = f[7:-5]
        wb = openpyxl.load_workbook('sap_' + n + '.xlsx')
        jc = wb.get_sheet_by_name("Joint Coordinates")

        i = 0
        maxz = 0.
        minz = 0.
        maxx = 0.
        while jc[_i('A', i)].value != None:
            z = jc[_i('F', i)].value
            maxz = max(z, maxz)
            minz = min(z, minz)
            x = jc[_i('D', i)].value
            maxx = max(x, maxx)
            i += 1

        h = maxz - minz
        L = maxx
        archStart = i // 2

        miny = 0.
        maxy = 0.
        for j in range(archStart, i):
            y = jc[_i('E', j)].value
            miny = min(y, miny)
            maxy = max(y, maxy)

        if abs(maxy) > abs(miny):
            d = maxy
            theta = math.atan(h / d)
        elif miny != 0.:
            d = abs(miny)
            theta = math.atan(h / miny) + math.pi 
        else:
            d = 0.
            theta = math.pi / 2.

        theta = theta * 180. / math.pi
        r = math.sqrt(h**2 + d**2)

        data[n] = {'h': h, 'd': d, 'r': r, 'theta': theta, 'L': L}

    return data

# graph differences against form attributes
def graphForm():

    cwd = os.getcwd()
    files = os.listdir(cwd)
    resultFiles = filter(lambda x: x[:7] == 'result_', files)
    resultFiles = filter(lambda x: x[7] != 'L', resultFiles)
    resultFiles = filter(lambda x: x[7] != 's', resultFiles)
    results = compSet(resultFiles)
    shapes = getShapeData(resultFiles)

    hL = []
    theta = []
    rL = []
    Parch = []
    Pcable = []
    Rx = []
    Ry = []
    Rz = []

    for f, d in results.items():
        hL.append(shapes[f]['h']/shapes[f]['L'])
        theta.append(shapes[f]['theta'])
        rL.append(shapes[f]['r']/shapes[f]['L'])
        Parch.append(d['Parch'])
        Pcable.append(d['Pcable'])
        Rx.append(d['Rx'])
        Ry.append(d['Ry'])
        Rz.append(d['Rz'])

    ms = 5

    plt.scatter(hL, Parch, s=ms, label='average axial force in arch')
    plt.scatter(hL, Pcable, s=ms, marker='^', 
                    label='average axial force in cables')
    plt.legend()
    plt.xlabel('Ratio of arch height to length (h_arch/L)')
    plt.ylabel("Percent difference between SAP2000 and SGSM")
    plt.title('Difference between SAP2000 and SGSM as a function of '
                + 'h_arch/L')
    plt.show()

    plt.scatter(theta, Parch, s=ms, label='average axial force in arch')
    plt.scatter(theta, Pcable, s=ms, marker='^', 
                    label='average axial force in cables')
    plt.legend()
    plt.xlabel('arch angle (theta) (degrees)')
    plt.ylabel("percent difference between SAP2000 and SGSM")
    plt.title('Difference between SAP2000 and SGSM as a function of '
                + 'theta')
    plt.show()


    plt.scatter(rL, Parch, s=ms, label='average axial force in arch')
    plt.scatter(rL, Pcable, s=ms, marker='^', 
                    label='average axial force in cables')
    plt.legend()
    plt.xlabel('Ratio of arch radius to length (r/L)')
    plt.ylabel("Percent difference between SAP2000 and SGSM")
    plt.title('Difference between SAP2000 and SGSM as a function of '
                + 'r/L')
    plt.show()

# get text file with table of differences for all result files
def compAll():

    cwd = os.getcwd()
    files = os.listdir(cwd)
    resultFiles = filter(lambda x: x[:7] == 'result_', files)
    caf = open('comp_all.txt', 'w')
    headerf = '{0:8}  {1:6}  {2:6}  {3:6}  {4:6}  {5:6}\n'
    header = headerf.format('file', 'Parch', 'Pcable', 'Rx', 'Ry', 'Rz')
    caf.write(header)
    linef = '{0:8}  {1:5.2f}%  {2:5.2f}%  {3:5.2f}%  {4:5.2f}%' + \
                '  {5:5.2f}%\n'

    allInfo = compSet(resultFiles)
    infoSorted = sorted(map(_valFromName, allInfo.items()))
    for f, n, d in infoSorted:
        if f == 'segs':
            n = int(n)
        caf.write(linef.format(f + "=" + str(n), d['Parch'], 
                                d['Pcable'], d['Rx'], d['Ry'], 
                                d['Rz']))

if __name__ == '__main__':
    compAll()
    graph('ao')
    graph('d')
    graph('H')
    graph('L')
    graph('q')
    graph('segs')
    graphForm()
