import sqlite3
from collections import defaultdict
import numpy as np
from DoubanAlg import get_rivendell_store


def checkItem(item, length):
    if item.ndim != 1:
        raise ValueError, "Only one dimensional arrays are supported"
    if item.shape != (length, ):
        raise ValueError, "Array has wrong size"

def saveData(filename, landmarks):
    """
    Save the generated fingerprint of specific audio file into database
    filename: the name of the song in the INTEGER format
    landmarks: the 2D array with fingerprints in every row formatted as:
    (time started, freqency stared, freq-delta, time-delta)
    """
    store = get_rivendell_store()

    # Select proper # parallel table
    mod = 10
    num = filename % mod
    table = "hash_track_%d"%(num)

    hasht = [8,6,8]   # This is came from retrieval.py as definition for hash table
    length = 3

    for item in landmarks:
        checkItem(item[1:], length)
        if item[1]<256 and item[2]<64 and item[3]<256:
            hid = int((item[1]<<14)+(item[2]<<8)+item[3])
        else:
            raise ValueError, "The scope of find_landmarks and hashing length are not corresponding."
        # save one landmark of a track into database
        i = [int(k) for k in item]      # change numpy.int64 to int
        store.execute("INSERT IGNORE INTO %s (song_id, time, hid) VALUES (%d, %d, %d)"% (table, filename, i[0], hid))
    store.commit()

def saveDuplicated(filename, hits):
    """
    Save the potential duplicated song into TABLE hash_dup_temp.
    The table has two columns: original and duplicate
    """
    store = get_rivendell_store()
    for item in hits:
        store.execute("INSERT IGNORE INTO hash_dup_temp (original, duplicate) VALUES (%d, %d)" % (filename, item))
    store.commit()

def fetchTrack(filename):
    """
    Return the landmarks of a specific track
    Note that filename should be the unique int id of that track.
    """
    store = get_rivendell_store()

    # Select proper # parallel table
    mod = 10
    num = filename % mod
    table = "hash_track_%d"%(num)

    # Fetch the entire song
    data = store.execute("SELECT time, hid FROM %s WHERE song_id=%s" % (table, filename))
    return np.array(data)


def rearrange():
    """
    Rearrange the TABLE hash_dup_temp into more formal format,
    s.t. rooting from single track and no duplicated alarms.
    """
    store = get_rivendell_store()
    data = store.execute("SELECT * FROM hash_dup_temp")
    data = np.array(data)

    # Arrange the duplicated songs with the same root
    for item in data:
        former = item[0]
        latter = item[1]
        for itr in data:
            if itr[0]==latter:
                itr[0] = former
                if itr[1]==former:
                    itr[1] = latter

    # delete the duplicated entries
    output = set()
    for i in range(len(data)):
        output.add((data[i,0],data[i,1]))

    # input the result into database
    for item in output:
        store.execute("INSERT INGORE INTO hash_dup_songs (original, duplicate) VALUES (%d, %d)" % (item[0], item[1]))


