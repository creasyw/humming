import numpy as np
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, binary_erosion
from scipy.signal import lfilter, hamming, convolve2d
from scipy.fftpack import fft
from matplotlib.mlab import specgram
from segmentaxis import segment_axis
import csv

import warnings
warnings.simplefilter("ignore", np.ComplexWarning)

def detect_peak(image):
    """
    Takes an image and detect the peaks usingthe local maximum filter.
    Returns a boolean mask of the peaks (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    """
    # Define an 8-connected neighborhood
    neighborhood = generate_binary_structure(2,2)
    # Apply local maximum filter to generate the mask that contains the peaks, 
    # whose values are set to be 1. Meanwhile, the background is set to be 0.
    local_max = maximum_filter(image, footprint=neighborhood)==image
    background = (image==0)
    
    # Erode the background in order to successfully subtract it form local_max, 
    # otherwise a line will appear along the background border 
    # (artifact of the local maximum filter)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)
    # local peaks in boolean matrix format
    peaks = local_max-eroded_background
    return peaks*image

def detect_peaks(image):
    """
    Return the local maximum of the given array.
    The data type of both input and output are numpy.ndarray
    """
    end = np.hstack((image,image[-1]))
    fir = np.hstack((image[0],image))
    mask = [end[k]>=fir[k] for k in range(len(end))]
    return image*mask[:-1]*(np.ones(len(image))-mask[1:])


def _preemp(input, p):
    """Pre-emphasis filter."""
    return lfilter([1., -p], 1, input)

def _spread(spectrum, profile=4.):
    """
    Each point (maxima) in X is "spread" (convolved) with the profile.
    Return the pointwise max of all of these.
    "profile" is a scalar, it's the SD of a gaussian used as the spreading function.
    """
    w = int(4*profile)
    profile = np.exp([-0.5*((k/profile)**2) for k in range(-w, w+1)])
    spectrum = detect_peaks(spectrum)
    output = np.zeros(spectrum.shape)
    if spectrum.ndim!=1:
        lensptr = len(spectrum[0])
    else:
        lensptr = len(spectrum)
    for i in np.nonzero(spectrum)[0]:
        EE = [0 for k in range(i+1)]+[v for v in profile]
        if len(EE)<=lensptr:
            EE = EE+[0 for k in range(lensptr+1-len(EE))]
            EE = EE[1:lensptr+1]
        else:
            EE[lensptr]=0
            EE = EE[1:lensptr+1]
        EE = np.array(EE)
        output = np.maximum(output, spectrum[i]*EE)
    return output



def spectrum(pcm, nwin=512, nfft=512, fs=16000, stepr=0.5):
    """Compute spectrum for give audio snippet.
    pcm: the mono form audio input. 
    stepr: the step ratio for audio segmentation (aka. overlap).
    The shape of the returned spec is (frequency bin, temporal bin,)
    """
    # Pre-emphasis factor (to take into account the -6dB/octave rolloff of the
    # radiation at the lips level)
    prefac = 0.98
    overlap = nwin*(1-stepr)
    window = hamming(nwin, sym=0)
    extract = _preemp(pcm, prefac)
    framed = segment_axis(extract, nwin, overlap) * window
    # Compute the spectrum magnitude
    spec = np.log10(np.abs(fft(framed, nfft, axis=-1)))
    spec = spec.T[0:nfft/2+1]
    # Make it zero-mean, so the start-up transients for the filter are minimized
    spec = spec - np.ma.mean(spec)
    return spec

def dgauss(spectrum):
    '''generating a derivative of Gauss filter.'''
    sigma = 0.8
    fwid = np.int(2*np.ceil(sigma))
    G = np.array(range(-fwid,fwid+1))**2
    G = G.reshape((G.size,1)) + G
    G = np.exp(- G / 2.0 / sigma / sigma)
    G /= np.sum(G)
    GH,GW = np.gradient(G)
    GH *= 2.0/np.sum(np.abs(GH))
    GW *= 2.0/np.sum(np.abs(GW))
    IH = convolve2d(spectrum,GH,mode='same')
    IW = convolve2d(spectrum,GW,mode='same')
    return np.sqrt(IH**2+IW**2)

def find_landmark(pcm, samplerate, N=5):
    """Find landmarks of givien snippet.
    Returns four variables:
    L returns as a set of landmarks, as rows of a 4-column matrix
        {start-time-col start-freq-row delta-freq delta-time}
    For debug porpose, some other matrices return:
    S returns the filtered log-magnitude surface
    T returns the decaying threshold surface
    maxes returns a list of the actual time-frequency peaks extracted
    N is the target hashes-per-sec (approximately; default 5)
    """
    # Estimate for how many maxes we keep - < 30/sec (to preallocate array)
    maxespersec = 30
    # The spreading width applied to the masking skirt from each found peak 
    # (gaussian half-width in frequency bins). Larger value means fewer peaks.
    f_sd = 30.
    first = 10
    # The maximum number of peaks allowed for each frame.  In practice, this 
    # is rarely reached, since most peaks fall below the masking skirt
    maxpksperframe = 5
    maxespersec = maxpksperframe*100
    # The decay rate of the masking skirt behind each peak (proportion per frame).
    # A value closer to one means fewer peaks found.
    # For N=5, a_dec=0.998
    a_dec = 1-0.01*(N/35.)
    # The number of pairs made with each peak. All maxes within a "target region" 
    # following the seed max are made into pairs, so the larger this region is 
    # (in time and frequency), the more maxes there will be.
    # The target region is defined by a freqency half-width (in bins)
    # Note that targetdt also influences the value of hashlength in retrieval function
    targetdf = 32   # the range of delta-freq is (-32.32)
    targetdt = 256
    # Parameters for power spectral density (PSD)
    nfft = 512
    nwin = 512
    # he high-pass filter applied to the log-magnitude envelope, which is 
    # parameterized by the position of the single real pole.  A pole close 
    # to +1.0 results in a relatively flat high-pass filter that just 
    # removes very slowly varying parts; a pole closer to -1.0 introduces
    # increasingly extreme emphasis of rapid variations, which leads to more peaks initially.
    hpf_pole = 0.98
#    spec = spectrum(pcm, fs=samplerate)
#    spec = dgauss(dgauss(spec))
    spec,_,_ = np.abs(specgram(pcm, nfft, samplerate, window=hamming(nwin), noverlap=nwin/2))
    smax = spec.max()
    spec = np.log10(np.maximum(smax/1e6, spec))
    spec = spec - np.ma.mean(spec)
    spec = lfilter([1., -1], [1, -hpf_pole], spec.T).T

    maxes = np.zeros((3,maxespersec*np.ceil(len(pcm)/float(samplerate))))
    nmaxes = 0
    # Initial threshold envelope based on peaks in first 10 frames
    sthresh = _spread(spec[:,0:min(first,spec.shape[1])].max(1),f_sd)
    # T stores the actual decaying threshold
    #T = np.zeros(spec.shape)
    for i in range(spec.shape[1]-1):
        s_this = spec[:,i]
        sdiff = np.maximum(0, (s_this-sthresh))
        sdiff = detect_peaks(sdiff)
        # Make sure last bin is never a local max since its index doesn't fit in 8 bits
        sdiff[-1] = 0
        ind = sorted(range(len(sdiff)), key=lambda k: sdiff[k], reverse=True)
        val = sorted(sdiff, reverse=True)
        ind = [ind[k] for k in range(len(val)) if val[k]>0] 
        # store those peaks and update the decay envelope
        nmaxthistime = 0
        for j in range(len(ind)):
            p = ind[j]
            if nmaxthistime < maxpksperframe:
                # Check to see if this peak is under the updated threshold
                if s_this[p] > sthresh[p]:
                    nmaxthistime += 1
                    maxes[1, nmaxes] = p
                    maxes[0, nmaxes] = i
                    maxes[2, nmaxes] = s_this[p]
                    nmaxes += 1
                    eww = np.exp([-0.5*(((k-p)/f_sd)**2) for k in range(0,len(sthresh))])
                    sthresh = np.maximum(sthresh, s_this[p]*eww)
            else:
                break
        #T[:,i] = sthresh
        sthresh = a_dec*sthresh

    # Backwards pruning of maxes
    nmaxes2 = 0
    # Used as index to navigate in maxes[]
    whichmax = nmaxes-1
    sthresh = _spread(spec[:,-1],f_sd)
    temp = []
    for i in range(spec.shape[1]-2,-1,-1):
        while whichmax>=0 and maxes[0,whichmax]==i:
            p = maxes[1,whichmax]
            v = maxes[2,whichmax]
            if v>=sthresh[p]:
                # Keep this one
                nmaxes2+=1
                temp.append([i,p])
                eww = np.exp([-0.5*(((k-p)/f_sd)**2) for k in range(0,len(sthresh))])
                sthresh = np.maximum(sthresh, v*eww)
            whichmax = whichmax-1
        sthresh = a_dec*sthresh
    # Delete the original generated random column and then flip left to right
    maxes2 = np.array(temp).T
    
    # Pack the maxes into nearby pairs = landmarks
    # Limit the number of pairs that will be accepted from each peak
    maxpairsperpeak=3
    # Landmark is <starttime F1 endtime F2>
    L = np.zeros((nmaxes2*maxpairsperpeak,4), dtype=int)
    nlmarks = 0

    for i in range(nmaxes2):
        startt = maxes2[0,i]
        F1 = maxes2[1,i]
        maxt = startt + targetdt
        minf = F1 - targetdf
        maxf = F1 + targetdf
        maxmask = np.logical_and(np.logical_and(maxes2[0]>startt,maxes2[0]<maxt),\
                np.logical_and(maxes2[1]>minf,maxes2[1]<maxf))
        matchmaxs = [ k for k in range(len(maxmask)) if maxmask[k]==True]
        # Limit the number of pairs
        if len(matchmaxs) > maxpairsperpeak:
            matchmaxs = matchmaxs[0:maxpairsperpeak]
        for match in matchmaxs:
            L[nlmarks,0] = startt
            L[nlmarks,1] = F1
            # make the delta-freq to (0,64)
            L[nlmarks,2] = targetdf+maxes2[1,match]-F1
            L[nlmarks,3] = maxes2[0,match]-startt
            nlmarks +=1
    
    L = L[0:nlmarks]
    maxes = maxes2

    #return L, spec, T, maxes
    return L
