from DoubanAlg import get_rivendell_store
import numpy as np

store = get_rivendell_store()
data = store.execute("select hid from hash_track_temp")
data = np.array(data).flatten()

np.save("hid_in_hash_track_temp", data)
data = list(data.sort())

length = len(data)
step = 10

for i in range(step):
    print "The breaking point is ", data[length/step*(i+1)]


print "Hoorry, done:)"

