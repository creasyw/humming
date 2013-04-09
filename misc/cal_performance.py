import re
import numpy as np
import csv
import requests
from collections import defaultdict

s = requests.session()
s.get(url="http://theoden.intra.douban.com:8001/radio")

escapesongs = [679812, 442082, 668999, 775220, 443136, 1471128, 407999, 24818, 1458307, 1392718, 1073741, 1031917, 1386517, 1447978, 1409415, 1407360, 981777, 1426596]

finder = re.compile("\d+")
aidfinder = re.compile('http://.*?(\d+)', re.S|re.M)
albfinder = re.compile('_blank\">(.*?)<\/a>')
titfinder = re.compile('title: (.*?)<\/li>')
artfinder = re.compile('artist: (.*?)<\/li>')
floatf = re.compile("[+-]*\d+?\.\d+?e?[+-]\d+")

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

def readresult(filename):
    data = csv.reader(open(filename, 'r'))
    output = defaultdict(lambda:set())
    right = 0
    wrong = 0
    for row in data:
        item = int(row[0])
        output[item] = set([int(k) for k in finder.findall(row[1])])
        if item in output[item]:
            right +=1
        else:
            wrong +=1
    print "The testing hits %s items, and %s right among them" % (right+wrong, right)

    # Read benchmark file
    data = csv.reader(open("merge_list.csv", 'r'))
    original = defaultdict(lambda:set())
    for row in data:
        temp = finder.findall(row[0])
        if temp==[]:
            continue
        original[int(temp[0])].add(int(temp[1]))
    return output, original

def regroup(result, item):
    newcomer = set([])
    seeds = result[item]
    for i in seeds:
        if not result[i].issubset(result[item]):
            newcomer.update(result[i]-result[item])
    if newcomer != set([]):
        result[item].update(newcomer)
        regroup(result, item)
    else:
        return result

if __name__ == '__main__':
    import getopt, sys

    def exit_with_usage():
        print "Usage: $ python cal_performance.py [input.csv] [output.csv]"
        exit()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:t:")
    except getopt.GetoptError as ex:
        exit_with_usage()
    if len(args) != 2:
        exit_with_usage()
    infile = args[0]
    outfile = args[1]

    result, original = readresult(infile)

    # Rearrange the testing result according to benchmark list
    for item in original:
        regroup(result, item)
    for item in result:
        if item in original:
            continue
        hits = result[item]
        for i in hits:
            if i in original:
                result[i].update(result[item])
                break
    for i in escapesongs:
        del result[i]
        del original[i]

    output = {}
    count = 0

    length = 0
    for i in original:
        output[count] = get_content(i)
        count +=1
        for item in result[i]:
            output[count] = get_content(item)
            count +=1
            original[i].discard(item)
        output[count] = []
        count +=1

    output[count] = ["The rest of the potential duplicated songs are:"]
    count +=1
   
    length = len(original)
    fn = 0

    for i in original:
        if original[i] == set([]):
            continue
        else:
            output[count] = get_content(i)
            count +=1
            for item in original[i]:
                output[count] = get_content(item)
                count+=1
                fn +=1
    
    w = csv.writer(open(outfile, 'w'))
    for i in output:
        w.writerow(output[i])
    print "# of right hitted is %s within %s samples"%(length-fn, length)
    print "Horry. Done!:)"
