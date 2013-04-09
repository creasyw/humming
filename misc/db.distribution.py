import sqlite3
from figure import plot_histrogram
from random import randint
import numpy as np

def uniqueFirst(target):
    """Sort and then return the unique elements in target with their first appearance respectively."""
    target = np.sort(target)
    val = [target[0]]
    ind = [0]
    for i in range(len(target)):
        if target[i]!=val[-1]:
            val.append(target[i])
            ind.append(i)
    return val, ind


conn = sqlite3.connect("/home/wuqiong_intern/data/genre/RnB/songindex.db")
c = conn.cursor()

c.execute("SELECT DISTINCT song_id FROM track")
songid = c.fetchall()
filename = songid[randint(0,len(songid)-1)][0]
c.execute("SELECT time FROM track WHERE song_id=:song",{"song":filename})
time = np.array(c.fetchall())[:,0]
c.close()
conn.close()

val, ind = uniqueFirst(time)
counts = np.diff(np.hstack((ind, len(time))))

print "Cover ratio is ", float(len(val))/val[-1]

#plot_histrogram(counts)

