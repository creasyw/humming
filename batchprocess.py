from subprocess import call
import sys, os, csv
import numpy as np
from dpark import DparkContext
from dataviasqlite import rearrange

sys.path.append("/var/shire")
from corelib.doubanfs import fs

def calculate_single(id, dptable, mode):
    os.environ['MPLCONFIGDIR']='matplot/'
    from retrieval import RetrievalMusic
    if mode != 2:
        data = fs.get('/song/small/%s.mp3'%id)
        binfile = open("output/%s.mp3" % (id),"wb")
        binfile.write(data)
        binfile.close()
    
    m = RetrievalMusic(dptable, mode)
    m.retrieving('output/%s.mp3'%id)
    
    if mode != 2:
        call("rm output/%s.mp3" % (id), shell=True)


def batchprocess(song_id, loaded, mode):

#    dpark = DparkContext()
#    dptable = dpark.broadcast(loaded)
#    dpark.parallelize(song_id, 80).foreach(lambda(id):calculate_single(id, dptable, mode))
    for id in song_id:
        calculate_single(id, loaded, mode)
    
    if mode == 2:
        rearrange()

if __name__ == '__main__':
    song_id = np.load("track_temp.npy")
    mode = 1    # 1 for save, 2 for filter, and 0 for regular work
    dpark = DparkContext()
    dpark.parallelize(song_id, 50).foreach(lambda(id):calculate_single(id,0,mode))


