from DoubanAlg import get_rivendell_store
import numpy as np

# Build a temporary table storing all of the data run by feature extraction
# Then record the largest rid (auto_increment) where it ends,
# so that the next time we have no need to start it all over again


numoftable = 10
store = get_rivendell_store()
retrievestep = 5000
store.execute("CREATE TABLE IF NOT EXISTS hash_track_temp LIKE hash_track_0")

ending = np.zeros(10)

table = "hash_track_0"
maxrid = store.execute("SELECT rid FROM %s ORDER BY rid DESC LIMIT 1"%(table))[0][0]
count = 0
while (count*retrievestep<=maxrid):
    start = count*retrievestep
    count +=1
    end = min(count*retrievestep, maxrid)
    store.execute("INSERT IGNORE INTO hash_track_temp (song_id, time, hid) SELECT song_id, time, hid FROM %s WHERE (rid>=%d) AND (rid<=%d) " % (table,start,end))

ending[i] = maxrid
print "Complete transfer %s (ending at rid=%d) to TABLE hash_track_temp." % (table, maxrid)

np.save("table_ending_points", ending)

