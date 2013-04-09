#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import re
import csv
import sys

finder = re.compile('http://.*?(\d+)', re.S|re.M,)

s = requests.session()
s.get(url="http://theoden.intra.douban.com:8001/radio")

def txt_wrap_by_all(begin, end, html):
    if not html:
        return ''
    result = []
    from_pos = 0
    while True:
        start = html.find(begin, from_pos)
        if start >= 0:
            start += len(begin)
            endpos = html.find(end, start)
            if endpos >= 0:
                result.append(html[start:endpos].strip())
                from_pos = endpos+len(end)
                continue
        break
    return result

def get_user_id(user_id):
    r= s.post(url="http://theoden.intra.douban.com:8001/data", data={"user_id":user_id, "rtype":"S","db":"elf_farm","dtype":"radio"})
    return r.content

def get_track_id(track_id):
    r= s.post(url="http://theoden.intra.douban.com:8001/data", data={"track_id":track_id, "dtype":"track"})
    return r.content

if __name__ == '__main__':

    candidates = set()
    songlist = set()
    tracklist = set()
    data = csv.reader(open("wannalist.csv",'r'))
    for row in data:
        candidates.add(int(row[0]))
    count = 0
    for item in candidates:
        for i in finder.findall(get_track_id(item)):
            if i in tracklist:
                continue
            else:
                tracklist.add(i)
            content =  get_user_id(i)
            ids = txt_wrap_by_all('id:','</br',content)
            for name in ids:
                songlist.add(name)
        count +=1
        sys.stdout.write("Download progress: %.2f%%   \r" % (100*count/float(len(candidates))) )

    w1 = open("wanna_songs.csv", 'w')
    for i in songlist:
        w1.write(i+'\n')
    w2 = open("wanna_albums.csv", 'w')
    for i in tracklist:
        w2.write(i+'\n')
    w1.close()
    w2.close()

