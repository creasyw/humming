import re
import numpy as np
import csv
import requests
from collections import defaultdict

s = requests.session()
s.get(url="http://theoden.intra.douban.com:8001/radio")

finder = re.compile("\d+")
aidfinder = re.compile('http://.*?(\d+)')
albfinder = re.compile('_blank\">(.*?)<\/a>')
titfinder = re.compile('title: (.*?)<\/li>')
artfinder = re.compile('artist: (.*?)<\/li>')
floatf = re.compile("\d+?\.\d+?e\+\d+")

def get_track_contents(track_id):
    r = s.post(url="http://theoden.intra.douban.com:8001/data", data={"track_id":track_id, "dtype":"track"})
    return r.content

def get_content(item):
    content = get_track_contents(item)
    if content == 'internal server error':
        return [0]
    album_id = int(aidfinder.findall(content)[0])
    album = albfinder.findall(content)[0]
    title = titfinder.findall(content)[0]
    artist = artfinder.findall(content)[0]
    return [item, album_id, album, title, artist]


if __name__ == '__main__':
    import getopt, sys

    def exit_with_usage():
        print "Usage: $ python cal_performance.py [result.csv] [detail.csv]"
        exit()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:t:")
    except getopt.GetoptError as ex:
        exit_with_usage()
    if len(args) != 2:
        exit_with_usage()
    infile = args[0]
    outfile = args[1]

data = csv.reader(open(infile,'r'))
result = {}
for row in data:
    temp = row
    hits = floatf.findall(temp[1])
    result[int(temp[0])] = [float(k) for k in hits]

empty = 0
first = 0
onlyhit = 0
wrong = 0

nduplicated= 0
duplicated = defaultdict(lambda:[])


length = float(len(result))
noreturn = []

for i in result:
    target = i
    hits = result[i]
    if len(hits)<4:
        empty += 1
        wrong += 1
    elif hits[0] == target:
        first += 1
    elif target in hits:
        onlyhit += 1
    else:
        wrong +=1
    if len(hits)>4:
        for j in range(0, len(hits), 4):
            duplicated[target].append(hits[j:j+4])
        nduplicated +=1
print "The length of the result is %s and no-return %s "%(length, empty)
print "First-hit=%.4f, Accuracy=%.4f, Among the errors No-return=%.4f." \
        %(first/length, 1-wrong/length, empty/length)
print "There are %s songs detected to have duplicated songs." % (nduplicated)

output = {}
count = 0

for i in duplicated:
    temp = duplicated[i]
    for item in temp:
        output[count] = item
        count +=1
    for item in temp:
        output[count] = get_content(int(item[0]))
        count +=1
    output[count] = []
    count +=1

output[count] = ["The rest of the potential duplicated songs are:"]
count +=1

w = csv.writer(open(outfile, 'w'))
for i in output:
    w.writerow(output[i])

print "Yeah!! everything is done."

