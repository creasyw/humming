import numpy as np
from DoubanAlg import get_rivendell_store

store = get_rivendell_store()
song_id = np.load("../track_list.npy")
song_id = list(song_id)
maxid = 0
songid = 0
for i in range(10):
    table = "hash_track_%d"%(i)
    stop = store.execute("SELECT song_id FROM %s ORDER BY rid DESC LIMIT 1" % (table))[0][0]
    lineid = song_id.index(stop)
    print "for %s, stop at SONG %s with index @ track_list %s" % (table, stop, lineid)
    if lineid > maxid:
        maxid = lineid
        songid = stop

print songid, maxid
print song_id.index(songid)

