import re
import numpy as np
import csv
from collections import defaultdict

data = csv.reader(open("3600original.csv", 'r'))
result = defaultdict(lambda:[])
count = 0
for row in data:
    temp = row
    result[count].append( int(temp[0]))
    result[count].append(int(temp[1]))
    result[count].append(np.fromstring(re.sub("[^0-9]",' ', temp[2]),dtype=int, sep=' '))
    count +=1

stat = np.loadtxt("3600result.csv", dtype=float, delimiter=',')

fp = 0
count = 0
i = 0
falsepositive = defaultdict(lambda:[])
duplicated = {}
for row in range(len(stat)):
    for col in range(1, len(stat[row])):
        if stat[row, col] == 1:
            if stat[row, col-1]==1:
                pre = result[row][2][col*2-2]
                cur = result[row][2][col*2]
                if pre not in duplicated and cur not in duplicated:
                    count +=1
                    duplicated[pre] = cur
                    print "%s.mp3, %s.mp3" % (pre, cur)
            else:
                fp += col
                falsepositive[i] = result[row][2][::2][:col]
                i +=1
                if stat[row, col+1]==1:
                    cur = result[row][2][col*2]
                    back = result[row][2][col*2+2]
                    if back not in duplicated and cur not in duplicated:
                        duplicated[cur] = back
                        print "%s.mp3, %s.mp3" % (cur, back)

print "There are %s FP and %s duplicated tracks" % (fp, count)
print "False Positives:"
print falsepositive


