import sqlite3
import re
import csv

if __name__ == '__main__':
    import sys

    def exit_with_usage():
        print "Usage: $ python findoutlier.py <db> <file list>"
        exit()

    if len(sys.argv)==3:
        dbfile = sys.argv[1]
        flist = sys.argv[2]
    else:
        exit_with_usage()

    # Eliminate the entry might be writing at that time
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute("SELECT DISTINCT song_id FROM track")
    song_id = c.fetchall()
    if song_id == None:
        print "The source database is empty!"
        exit()
    song = set()
    for i in song_id:
        song.add(i[0])

    result = []
    pool = set()
    f = open(flist, 'r')
    result.append(flist.replace('list.txt',''))
    for line in f:
        line = line.replace('.mp3', '')
        line = int(re.sub("[^0-9]", '', line))
        if line in pool:
            print "WARNING: There is duplicated song id %s in %s" % (line, flist)
        pool.add(line)
    f.close()
    
    for i in pool:
        if i not in song:
            result.append(i)

    if len(result)==1:
        print "Hoooory, there is no outlier in %s." % (dbfile)
    else:
        w = csv.writer(open("outliers.csv", "a"))
        w.writerow(result)
        print "Sadly, there are %s outliers in %s." % (len(result)-1, dbfile)


    c.close()
    conn.close()

    
