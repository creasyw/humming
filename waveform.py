import numpy
import mad
from struct import unpack
from scipy.signal import resample

MAX_PULSE_CODE = 2**15
#SAMPLE_RATE = 44100


def open_audio(path):
    return mad.MadFile(path)

def downsample(data, preSamplerate, curSamplerate=8000):
    blocks = int(len(data)/preSamplerate)
    if blocks==0:
        print "WARNING: The audio file has nothing to extract."
        return 0
    numOfNewSample = curSamplerate*blocks
    return resample(data[:blocks*preSamplerate],numOfNewSample)

def read_audio(fh, st, to):
    """Decode mp3 audio file via MAD decoder"""
    assert st >= 0 and st < to
    buf = ''
    nbuf = ''
    while fh.current_time() < to and nbuf is not None:
        nbuf = fh.read()
        if fh.current_time() >= st:
            buf += str(nbuf)
    return st, fh.current_time(), buf


def pcm_bin2num(pcm_bins, join=False):
    """Make stero audio file deconvolution as left and right channels"""
    pcms = numpy.array(unpack('h'*(len(pcm_bins)/2), pcm_bins), float) / MAX_PULSE_CODE
    left = numpy.array([pcms[i] for i in range(0, len(pcms), 2)], float)
    right = numpy.array([pcms[i] for i in range(1, len(pcms), 2)], float)
    if join:
        return (left + right) / 2.
    return left, right


def walk_audio(fh, win, step, st=0, to=float('inf'), join=False):
    assert win > 0 and step > 0 and win >= step and st >= 0 and st < to
    nbuf = buf = ''
    bw = win * 4
    bs = step * 4
    #
    while fh.current_time() < to and nbuf is not None:
        nbuf = fh.read()
        if fh.current_time() >= st:
            buf += str(nbuf)
        while len(buf) > bw:
            yield pcm_bin2num(buf[ : bw], join)
            buf = buf[bs: ]
    #remained part
    buf += '\0' * (bw - len(buf))
    yield pcm_bin2num(buf, join)

def waveform (filename, start=0, end=float('inf')):
    """Decode the audio file and return the pcm file as [left, right]
    channels (assuming the mp3 is stero by default)"""
    mf = open_audio(filename)
    if mf.mode() == mad.MODE_SINGLE_CHANNEL:
        ch = 1
    else: ch = 2
#    print "SampleRate: %d Hz\nBitRate: %d kbps\nChannel(s): %d\nDuration: %d sec"\
#            % (mf.samplerate(), mf.bitrate()/1000, ch, mf.total_time() / 1000)
    if start < 0 or start >= end or start >= mf.total_time:
        print "Start time must be >= 0, <= end_time and total time."
        exit_with_usage()
    if end >= mf.total_time():
        end = float('inf')
    
    data = read_audio(mf, start, end)
    # plot the result, and save it in pdf (optional)
    pcmbin = pcm_bin2num(data[2], join=True)
    return pcmbin, mf.samplerate()


if __name__ == '__main__':
    import getopt, sys

    def exit_with_usage():
        print "Usage: $ python waveform.py [-s start_sec] [-t to_sec] song.mp3"
        exit()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:t:")
    except getopt.GetoptError as ex:
        print ex
        exit_with_usage()

    if len(args) != 1:
        #print args
        exit_with_usage()

    st = 0
    to = float('inf')
    for o, a in opts:
        if o == '-s':
            st = int(float(a) * 1000)
        elif o == '-t':
            to = int(float(a) * 1000)

    data = waveform(args[0], st, to)

