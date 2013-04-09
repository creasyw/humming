from DoubanAlg import gstore
import numpy as np

data = gstore.execute("SELECT * FROM radio_track_stats ORDER BY play_count DESC")

trackname = []
for item in data:
    trackname.append(int(item[0]))

trackname = np.array(trackname)
np.save("track_list", trackname)


