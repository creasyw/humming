import csv
import numpy as np
import re
from collections import defaultdict
from mlpy import LibSvm

finder = re.compile("\d+")

def reading_file(filename):
    """Reading file and return ndarray training data"""
    stream = csv.reader(open(filename, 'r'))
    data = []
    lastrow = 0
    ind = 0
    for row in stream:
        temp = [float(k) for k in row if k!='']
        ind +=1
        if len(temp)==4:
            if lastrow==0:
                lastrow = 1
            else:
                print "WARNING, there is something row in row ", ind
        elif len(temp)==0:
            lastrow = 0
        elif len(temp)==5:
            data.append([temp[1],temp[2],temp[4]])
            lastrow = 2
        else:
            print "WARNING, there is something row in row ", ind
    print "Loading complete!"
    print "The length of data is ", len(data)
    return np.array(data)

def preprocessing(data, scale=True):
    """
    Scale the data: tc,hc [-0.7 -- 1], dc [-.7 -- .78]
    Select the proper data and throw the outlier away
    Return two dataset of 1 and 0"""
    pos = []
    neg = []
    for i in data:
        item = data[i]
        if scale:
            tc = np.log10(min(1000,max(20,item[1])))-2
            hc = np.log10(min(1000,max(20,item[2])))-2
            dc = np.log10(min(6000,max(200,item[3])))-3
        if item[4]==1:
            pos.append([tc, hc, dc])
        elif item[4]==0:
            neg.append([tc, hc, dc])
        else:
            print "WARNING: there are some illegal classset input."
    return np.array(pos), np.array(neg)

def writefile(filename, pos, neg):
    w = open(filename, 'w')
    for item in pos:
        w.write("1 1:%s 2:%s 3:%s\n" %(item[0], item[1], item[2]))
    for item in neg:
        w.write("0 1:%s 2:%s 3:%s\n"%(item[0], item[1], item[2]))

def svmtrain(pos, neg):
    y = np.hstack((np.ones(len(pos),dtype=int),np.zeros(len(neg),dtype=int)))
    x = np.vstack((pos, neg))
    # The values of gamma and C come from grid.py in libsvm/tools
    svm = LibSvm(kernel_type='rbf', gamma=8.0, C=128.0)
    svm.learn(x,y)
    svm.save_model("svm.model")

#if __name__ == '__main__':
#    filename = "data_for_svm.csv"
#    data = reading_file(filename)
#    pos, neg = preprocessing(data)
#
#    w = open("trainset.csv", 'w')
#    for item in pos:
#        w.write("1 1:%s 2:%s\n" %(item[0], item[1]))
#    for item in neg:
#        w.write("0 1:%s 2:%s\n"%(item[0], item[1]))


if __name__ == '__main__':
    import getopt, sys

    def exit_with_usage():
        print "Usage: $ python cal_performance.py [input.csv] [output.csv]"
        exit()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:t:")
    except getopt.GetoptError as ex:
        exit_with_usage()
    if len(args) != 2:
        exit_with_usage()
    infile = args[0]
    outfile = args[1]

    data = csv.reader(open(infile,'r'))
    result = {}
    for row in data:
        temp = row
        hits = finder.findall(temp[1])
        result[int(temp[0])] = [int(k) for k in hits]
    
    empty = 0
    first = 0
    onlyhit = 0
    wrong = 0
    
    nduplicated= 0
    duplicated = defaultdict(lambda:[])
    
    
    length = float(len(result))
    noreturn = []
    
    for i in result:
        target = i
        hits = result[i]
        if len(hits)<4:
            empty += 1
            wrong += 1
        elif hits[0] == target:
            first += 1
        elif target in hits:
            onlyhit += 1
        else:
            wrong +=1
        if len(hits)>4:
            for j in range(0, len(hits), 4):
                duplicated[target].append(hits[j:j+4])
            nduplicated +=1
    print "The length of the result is %s and no-return %s "%(length, empty)
    print "First-hit=%.4f, Accuracy=%.4f, Among the errors No-return=%.4f." \
            %(first/length, 1-wrong/length, empty/length)
    print "There are %s songs detected to have duplicated songs." % (nduplicated)
    
    data = csv.reader(open("merge_real.csv", 'r'))
    original = defaultdict(lambda:[])
    count = 0
    for row in data:
        temp = finder.findall(row[0])
        if temp==[]:
            continue
        original[int(temp[0])].append(int(temp[1]))
        count +=1
    print "The benchmark has %s songs duplicated" % (len(original))
    
    # The format of the output is "songid time hit DTW right/wrong"
    output = {}
    count = 0
    # Min(time)=Min(hit)=20.
    #mtime = 0   # bigger is better
    #mhit = 0
    #maxdtw = 0    # smaller is better
    #mindtw = 5000
    
    for i in duplicated:
        # Omit the incorrect duplication list in the original merge_data
        if i not in original:
            continue
        temp = duplicated[i]
        benchmark = original[i]
        for item in temp:
            # Omit the COMPELETE duplicated songs
            if item[0] in benchmark or item[0]==i:
                output[count] = item+[1]
            else:
                output[count] = item+[0]
            count +=1
            
    #        if item[1]>mtime:
    #            mtime = item[1]
    #        if item[2]>mhit:
    #            mhit = item[2]
    #        if item[3]>maxdtw:
    #            maxdtw = item[3]
    #        elif item[3]<mindtw:
    #            mindtw = item[3]
    #
    #print "max time: ", mtime
    #print "max hit: " , mhit
    #print "max and min of DTW: ", maxdtw, mindtw
    
    pos, neg = preprocessing(output)
    writefile(outfile, pos, neg)
    svmtrain(pos, neg)
    print "Yeah! Everything is done:)"
    
