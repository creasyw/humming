import csv
import re
from subprocess import call

find = re.compile("\d+")

data = csv.reader(open("merge_list.dat", 'r'))
original = []
duplicated = []
for row in data:
    temp = find.findall(row[0])
    if temp == []:
        continue
    original.append(int(temp[0]))
    duplicated.append(int(temp[1]))

count = 0
limit = 1000
for item in original:
    call("wget theoden:8001/data?track_id=%d -O %d.mp3"%(item, item), shell=True)
    count+=1
    if count>=1000:
        break

