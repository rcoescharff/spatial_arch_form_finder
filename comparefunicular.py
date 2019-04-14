import comparetosap
from copy import deepcopy
import matplotlib.pyplot as plt
import os
import openpyxl
from vector import Vector

# get column-row string ('A1') from col string and row index
def _i(col, row=0):
    return col + str(row + 4)

# get numbers of members in result sheet
def memberRange(sheet):
    rng = []
    i = 0
    n = sheet[_i('A', i)].value
    while n != '' and n != None:
        if n not in rng:
            rng.append(n)
        i += 1
        n = sheet[_i('A', i)].value
    return rng

# return reaction vector number n from sheet and write to file
def reaction(sheet, n, file):
    row = n - 1
    R = Vector(sheet[_i('D', row)].value,
               sheet[_i('E', row)].value,
               sheet[_i('F', row)].value)
    fsReact = '{0:2}  {1}\n'
    file.write(fsReact.format('R' + str(n), R.fstr()))
    return R

# get forces file with identifier name, return dictionary, write info
# to text file
def info(name):

    result = openpyxl.load_workbook('result_' + name + '.xlsx')
    elmtForces = result.get_sheet_by_name('Element Forces - Frames')
    reactions = result.get_sheet_by_name('Joint Reactions')
    infoFile = open("info_" + name + ".txt", "w")

    fHeader = '{0:2}  {1:7}  {2:7}  {3:7}  {4:7}  {5:7}  {6:7}\n'
    header = fHeader.format('m', 'P', 'V2', 'V3', 'T', 'M2', 'M3')
    infoFile.write(header)
    fsMember = '{0:2}  {1:7.2f}  {2:7.2f}  {3:7.2f}  {4:7.2f}  ' + \
                '{5:7.2f}  {6:7.2f}\n'

    membersInfo = {}
    memRange = memberRange(elmtForces)
    for n in memRange:

        forces = comparetosap.memberForces(elmtForces, n)
        if forces == None:
            raise Exception("Error reading result_" + name + ".xlsx")

        infoFile.write(fsMember.format(n, forces['P'], forces['V2'], 
                                        forces['V3'], forces['T'], 
                                        forces['M2'], forces['M3']))
        membersInfo[n] = forces

    R1 = reaction(reactions, 1, infoFile)
    R2 = reaction(reactions, 2, infoFile)
    membersInfo['R1'] = R1
    membersInfo['R2'] = R2

    return membersInfo

# get maximum forces for file with identifier name
def getMaxes(name):

    nInfo = info(name)
    if nInfo == None:
        return
    archCount = 0
    segs = (len(nInfo) + 1) // 3.
    cables = segs - 1
    maxes = {}

    for n, d in nInfo.items():

        if n == 'R1':
            maxes['R'] = d
            continue
        elif n == 'R2':
            continue
        elif int(n) <= segs:
            part = 'deck'
        elif int(n) <= segs * 2:
            part = 'arch'
        else:
            part = 'cable'

        for s, f in d.items():
            if maxes.has_key(s):
                if maxes[s].has_key(part):
                    maxes[s][part] = max(abs(maxes[s][part]), abs(f))
                else:
                    maxes[s][part] = abs(f)
            else:
                maxes[s] = {part: abs(f)}

    return maxes

# get a dictionary comparing the max forces in each file in files to 
# those in funicular
def compSet(files, funicular):

    funMaxes = getMaxes(funicular[7:-5])
    compFiles = {}

    for f in files:
        maxes = getMaxes(f[7:-5])
        if maxes != None:
            comp = {}
            for cat, d in maxes.items():
                if cat == 'R':
                    Rx = abs(d.x()) - abs(funMaxes[cat].x())
                    Ry = abs(d.y()) - abs(funMaxes[cat].y())
                    Rz = abs(d.z()) - abs(funMaxes[cat].z())
                    comp[cat] = {'x': Rx, 'y': Ry, 'z': Rz}
                else:
                    comp[cat] = {}
                    for part, force in d.items():
                        comp[cat][part] = abs(force) \
                            - abs(funMaxes[cat][part])
        compFiles[f[7:-5]] = comp

    return compFiles

# write text file with data from compDict
def comp(compDict):

    pairs = {'arch':'x', 'cable':'y', 'deck':'z'}
    caf = open('comp_fun.txt', 'w')
    sortedDict = sorted(map(comparetosap._valFromName, compDict.items()))
    formH = '{0:12}  {1:5} {2:8} {3:8} {4:8} {5:8} {6:8} {7:8}   {8:}\n'
    form = '{0:12}  {1:5} {2:8.2f} {3:8.2f} {4:8.2f} {5:8.2f} ' \
            + '{6:8.2f} {7:8.2f}   {8:}\n'
    header = sortedDict[0][2].keys()
    caf.write(formH.format('file', 'part', *header))

    parts = sortedDict[0][2]['P'].keys()
    for f, a, d in sortedDict:
        name = f + "=" + str(a)
        for p in parts:
            line = [p]
            for k in header:
                if k != 'R':
                    line.append(d[k][p])
                else:
                    dim = pairs[p]
                    l = '{0} {1:8.2f}'.format(dim, d[k][dim])
                    line.append(l)
            if p == 'arch':
                n = name
            else:
                n = ''
            caf.write(form.format(n, *line))

# graph data from compDict
def graph(compDict):

    k = ' (kips)'
    ki = ' (kip-in)'
    units = {'P': k, 'V2': k, 'V3': k, 'T': k, 'M2': ki, 
             'M3': ki, 'R': k}
    ls = {'arch': '-', 'deck': '--', 'cable':'-.', 
          'x':'-', 'y':'--', 'z':'-.'}

    graphDict = {}
    angles = []
    sortedDict = sorted(map(comparetosap._valFromName, compDict.items()))

    for f, a, d in sortedDict:
        angles.append(a)
        for cat, parts in d.items():
            if not graphDict.has_key(cat):
                graphDict[cat] = {}
            for part, force in parts.items():
                if not graphDict[cat].has_key(part):
                    graphDict[cat][part] = [force]
                else: 
                    graphDict[cat][part].append(force)

    for cat, parts in graphDict.items():
        for part, forces in parts.items():
            if cat != 'P' and part != 'cable':
                plt.plot(angles, forces, linestyle=ls[part], label=part)
            elif cat == 'P':
                plt.plot(angles, forces, linestyle=ls[part], label=part)
        plt.axvline(x=113.67, color='k', linestyle=':', 
                        label='base arch angle')
        plt.legend()
        plt.xlabel('arch angle (degrees)')
        plt.ylabel('difference in maximum ' + cat + ' from base' 
                    + units[cat])
        plt.title('Difference in ' + cat + 
                    ' between base and other forms')
        plt.show()

def main():
    cwd = os.getcwd()
    files = os.listdir(cwd)
    resultFiles = filter(lambda x: x[:10] == 'result_alt', files)
    funicular = 'result_funicular.xlsx'
    d = compSet(resultFiles, funicular)
    comp(d)
    graph(d)

if __name__ == '__main__':
    main()
