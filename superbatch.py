from subprocess import call
import numpy as np
from batchprocess import batchprocess
import csv
from collections import defaultdict


data = np.load("track_list.npy")[:74468]
step = 160
length = len(data)
round = length/step+1

table = "temp.csv"
mode = 2

if mode == 2:
    input_table = csv.reader(open(table, 'r'))
    loaded = defaultdict(lambda:[])
    
    for id in input_table:
        loaded[int(id[2])].append([int(id[0]), int(id[1])])


for i in range(round):
    if mode == 2:
        slice = data[step*i:min(length,step*(i+1))]
        batchprocess(slice, loaded, mode)
    else:
        np.save("track_temp", slice)
        # for checking
        #call("python batchprocess.py -m process -p 10", shell=True)
        # Real working command
        call("sudo -u alg python batchprocess.py -m mesos -p 10", shell=True)
        call("rm track_temp.npy", shell=True)

