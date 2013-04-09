from find_landmarks import find_landmark
from segmentaxis import segment_axis
from waveform import waveform, downsample
from dataviasqlite import saveData, saveDuplicated, fetchTrack
from mlpy import LibSvm
from operator import itemgetter
import numpy as np
import re
import csv
import sqlite3
from DoubanAlg import get_rivendell_store

find = re.compile("(\d+).mp3")

class RetrievalMusic:
    """
    Maintain an interface between LSH core algorithm and music file,
    as well as linking the preprocessing functionalities
    """

    def __init__(self, dictionary, mode):
        """
        Initial the Retrival Object, including parameters (sample rate, hashing density,
        freqency offset, number of keys used in hashing) and initializing hashing table.
        """
        self.sr = 8000
        # the target hashes-per-sec
        self.density = 20
        # number of hash keys are corresponded to the composition of landmarks
        # They are <freq-bin number, delta frequency, delta time span>
        self.nkey = 3
        # The fist two elements relate with spectrumgram and FFT bands
        # The last is relevant with the targetdt in find_landmarks
        # The calculate of hashlength is log2(original value)
        self.hashlength = [8,6,8]
        # time span for sampling
        self.hopt = 0.01
        # Configures for extract time slot from database
        self.window = 4500      # extract features within 45s
        self.step = 20          # the searching step is 200ms
        # load the trained SVM classifier
        self.svm = LibSvm.load_model("svm.model")
        # Take frequncy offset into consideration
        self.freqoffset = 4

        self.numoftable = 10
        self.dict = dictionary
        self.mode = mode

    def _preprocessing(self, filename, start=0, end=float('inf')):
        """
        Return the sub-fingerprint matrix from featureExtract.py
        overlap: For the sake of avoiding unpleasant segmentation in the retrieving procedure.
        """
        if start != 0:
            start = int(float(start)*1000)
        if end != float('inf'):
            end = int(float(end)*1000)
        pcm, samplerate = waveform(filename, start, end)
        pcm = downsample(pcm, samplerate, self.sr)
        if type(pcm) == int:
            landmarks = 0
        else:
            landmarks = find_landmark(pcm, self.sr, self.density)
        return landmarks

    def _stripname(self, filename):
        """ Return the filename with only unique id left"""
        return int(find.findall(filename)[0])

    def _unique_first(self, target):
        """
        Return the first occurance of unique elements as well as their index from 
        the target array. Note that the input array will be sorted first.
        """
        target = np.sort(target)
        val = [target[0]]
        ind = [0]
        for i in range(len(target)):
            if target[i]!=val[-1]:
                val.append(target[i])
                ind.append(i)
        return val, ind
    
    def _findMostTypical(self, landmarks):
        """Return the landmarks with the richest extracted features within the given time slot"""
        start = 0
        maxc = 0
        time = landmarks[:,0]
        #time = np.unique(landmarks[:,0])
        stind = 0
        if time[-1] >= self.window:
            while start < time[-1]-self.window:
                end = start + self.window
                count = np.sum(time<end)-np.sum(time<start)
                if count >= maxc:
                    maxc = count
                    # Locate to the 1st occurance of the time stamp
                    stind = np.where(time>=start)[0][0]
                start += self.step
            landmarks = landmarks[stind:(stind+maxc+1),:]
        return landmarks

    def _findLargestCoverage(self, landmarks):
        """Return the landmarks with the largest coverage for given length of time slot"""
        start = 0
        maxc = 0
        time = np.unique(landmarks[:,0])
        #time = np.unique(landmarks[:,0])
        stind = 0
        if time[-1] >= self.window:
            while start < time[-1]-self.window:
                end = start + self.window
                count = np.sum(time<end)-np.sum(time<start)
                if count >= maxc:
                    maxc = count
                    # Locate to the 1st occurance of the time stamp
                    stind = np.where(time>=start)[0][0]
                start += self.step
            stend = np.where(landmarks[:,0]==time[stind+maxc])[0][0]
            stind = np.where(landmarks[:,0]==time[stind])[0][0]
            partial_lm = landmarks[min(stind,stend):max(stind,stend),:]
        else:
            partial_lm = landmarks
            stind = 0
            stend = len(landmarks)

        return partial_lm, landmarks[min(stind,stend),0], landmarks[max(stind,stend)-1,0]

    def _findSnippetNearBeginning(self, landmarks):
        """Return the landmarks somewhere near the beginning of the track"""
        start = 1000
        end = 5500
        time = landmarks[:,0]
        if time[-1]>=start:
            count = np.sum(time<=end)-np.sum(time<start)
            stind = np.where(time>=start)[0][0]
            landmarks = landmarks[stind:(stind+count),:]
        return landmarks
    
    def _postprocessing(self, result, satellite, querylen, time):
        """
        Conduct post-processing to the retrieved result.
        Return <song_id, hits for majority time offset, value of time offset, overall hits #>
        satellite: the naive hits from the hashing table. type(satellite) is ndarray.
        querylen: the length of time of query, the unit is 10ms.
        """
        # Permit +/- 10% tempo difference
#        tolerance = 0.1
        output = np.zeros((len(result), 4), dtype=int)
#        delta = querylen * tolerance
        # Find the most popular time offset
        for i in range(len(result)):
            # Fetch satellites contain specific track id
            tkR = satellite[satellite[:,0]==result[i,0]]
            # Drawing the histogram of the value of offset time
            dts, xx = self._unique_first(tkR[:,2])
            xx.append(len(tkR))
            dtcounts = np.diff(xx)
            xx = dtcounts.argmax(0)
            vv = dtcounts.max(0)

            hitted = np.array([tkR[k] for k in range(len(tkR)) if tkR[k,2]==dts[xx]])
            stamp, ind = self._unique_first(hitted[:,1])
            ind.append(len(hitted))
            dtcounts = np.diff(ind)

            hitlen = np.zeros(len(time), dtype=int)
            for j in stamp:
                hitlen[time.index(j-dts[xx])] = dtcounts[stamp.index(j)]
            from mlpy import dtw_std
            dis = dtw_std(querylen, hitlen)
            output[i]=[result[i,0],len(stamp),len(hitted),dis]

        # Sort the R in accordance with time coverage
        output.view('i8,i8,i8,i8').sort(order=['f1'], axis=0)
        return output[::-1]


    def validatelm(self, table, filename, start, end, landmarks):
        """
        Validate whether or not the input file with landmarks has already in database.
        """
        # Return no more than 100 hits
        # Display the first 20 results
        hitslimit = 100
        ndisplay = 15
        # Threshold for open-set test ratio of hits
        rhits = 0.03

        marklen = len(landmarks)
        thres = marklen*rhits

        time, ind = self._unique_first(landmarks[:,0])
        ind.append(marklen)
        lmhist = np.diff(ind)

        # The format of satellite should be <song_id, time, time-query_time>
        candidates = []

        if self.mode == 2:
            for item in landmarks:
                temp = self.dict[item[1]]
                for i in temp:
                    candidates.append([i[0],i[1],i[1]-item[0]])
        else:
            tbase = "hash_track_%d"%(filename%self.numoftable)
            candidates = store.execute("select target.song_id, target.time, CONVERT(target.time-base.time, SIGNED) from %s as target inner join %s as base on base.hid=target.hid where (base.song_id=%d and base.time>=%d and base.time<=%d)" % (table, tbase, filename, start, end))

        satellite = np.array(candidates)

        lsat = len(satellite)
        
        if lsat>0:
            # Find all the unique tracks referenced
            val, xx = self._unique_first(satellite[:,0])
            xx.append(lsat)
            utrkcounts = np.diff(xx)
            utcxx = sorted(range(len(utrkcounts)), key=lambda k: utrkcounts[k], reverse=True)
            utcvv = sorted(utrkcounts, reverse=True)
            # Keep at most 20 per hit
            utcxx = utcxx[:min(hitslimit,len(utcxx))]
            utcvv = utcvv[:len(utcxx)]
            # Unique values sorted according to occurence
            utrks = [val[k] for k in utcxx]
            nutrks = len(utrks)
            result = np.zeros((nutrks,2), dtype=int)

            result[:,0] = utrks
            result[:,1] = utcvv

            result = self._postprocessing(result, satellite, lmhist, time)
            
            # Used for dumping training data for SVM
            output = []
            for item in result:
                tc = np.log10(min(1000,max(20,item[1])))-2
                hc = np.log10(min(1000,max(20,item[2])))-2
                dc = np.log10(min(6000,max(200,item[3])))-3
                if self.svm.pred((tc,hc,dc))==1:
                    output.append(item[0])
                else:
                    break
        if lsat==0:
            output = []
        return output

    def iter_database(self, filename, landmarks):
        dup_flag = False
        partial_lm, start, end = self._findLargestCoverage(landmarks)
        
        for i in range(self.numoftable):
            table = "hash_track_%d"%(i%self.numoftable)   # balance the load
            hits = self.validatelm(table, filename, start, end, partial_lm)

            if filename in hits:
                hits.pop(hits.index(filename))
            if len(hits) >0:
                print "Hitting duplicated songs for " , filename
                saveDuplicated(filename, hits)
                dup_flag = True
            if self.mode == 2:
                # For mode 2, the database is preloaded into database @ superbatch
                break
        
        if dup_flag and self.mode==0:
            store = get_rivendell_store()
            table = "hash_track_%d"%(filename%self.numoftable)
            store.execute("delete from %s where song_id=%d" % (table, filename))
        print "Complete file ", filename

    def retrieving(self, filename):
        """
        Retrieving the query filename in the database to find the duplicated track.
        mode: 2 for filtering, 1 for save, and 0 for the regular work
        """
        if self.mode == 2:
            filename = self._stripname(filename)
            landmarks = fetchTrack(filename)
        else:
            landmarks = self._preprocessing(filename)
            filename = self._stripname(filename)

        if type(landmarks) != int and len(landmarks)!=0:
            if self.mode == 0 or self.mode == 1:
                saveData(filename, landmarks)
            if self.mode == 0 or self.mode == 2:
                self.iter_database(filename, landmarks)
                
        return 0


if __name__ == '__main__':
    import getopt, sys
    mode = 1

    def exit_with_usage():
        print "Usage: $ python retrieval.py [-f filename]"
        exit()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:")
    except getopt.GetoptError as ex:
        exit_with_usage()

    for o, a in opts:
        if o == '-f':
            filename = a
        else:
            exit_with_usage()

    m = RetrievalMusic(0,mode)
    m.retrieving(filename)

