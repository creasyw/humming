import matplotlib.pyplot as plt
import numpy
import matplotlib.cm as cm
from matplotlib.image import NonUniformImage
import matplotlib.colors as colo
from matplotlib.pyplot import specgram


def plot_curve(Y, X=None, xlim=None, ylim=None, title="", xlabel="", ylabel=""):
    if X is None:
        X = numpy.array(xrange(len(Y)))
    #plot.subplot(111)
    plt.plot(X, Y)
    if xlim: plt.xlim(*xlim)
    if ylim: plt.ylim(*ylim)
    if xlabel: plt.xlabel(xlabel)
    if ylabel: plt.ylabel(ylabel)
    plt.grid(True)
    plt.show()

def plot_img(img, filename='image.png', xlim=None, ylim=None, title="", xlabel="", ylabel=""):
    #
    if not xlim: xlim = (0, img.shape[1] - 1)
    if not ylim: ylim = (0, img.shape[0] - 1)
    x = numpy.linspace(xlim[0], xlim[1], img.shape[1])
    y = numpy.linspace(ylim[0], ylim[1], img.shape[0])
    #
    fig = plt.figure()
    ax = fig.add_subplot(111)
    im = NonUniformImage(ax, cmap=cm.Greys)#, norm=colo.LogNorm(vmin=.00001))
    im.set_data(x, y, img)
    ax.images.append(im)
    #
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    if title: ax.set_title(title)
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)
    #
    plt.show()
    plt.savefig(filename)


def plot_histrogram(data, xlabel=None,bins=1000,xlim=None):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(data, bins, normed=1)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel('Percentage')
    ax.grid(True)
    if xlim:
        ax.set_xlim(*xlim)
    plt.show()


def plot_multi_histrogram(rdic, bins=1000, xlim=None, ylim=None, inv=None):
    v_min = v_max = None
    if inv is None:
        for v in rdic.itervalues():
            if v_min is None or min(v) < v_min:
                v_min = min(v)
            if v_max is None or max(v) > v_max:
                v_max = max(v)
    else: v_min, v_max = inv
    assert v_min < v_max
    r_len = len(rdic)
    #
    fig = plt.figure()
    for i, k in enumerate(rdic):
        ax = fig.add_subplot(r_len,1,i+1)
        #print "%s: %s" % (k, rdic[k])
        ax.hist(rdic[k], bins, normed=1)
        ax.set_ylabel(k)
        if ylim:
            ax.set_ylim(*ylim)
        if xlim:
            ax.set_xlim(*xlim)
        else:
            ax.set_xlim(v_min,v_max)
        ax.grid(True)
    plt.show()
 

def plot_distribution(models, inv=(0,1), bins=1000, names=None, **kw):
    assert inv[0] < inv[1] 
    assert bins > 1
    if names is None:
        names = ["model_%d"%i for i in range(len(models))]
    assert len(names) == len(models)
    exp = kw.get('exp', True)
    #
    x = numpy.array([numpy.linspace(inv[0], inv[1], bins + 1)]).T
    figs = []
    for model in models:
        if not model: 
            continue
        y = model.score(x)
        if exp:
            y = numpy.exp(y)
        figs.append(plt.plot(x, y))
    plt.legend(figs, names, 'upper right')
    #
    plt.xlim(*inv)
    plt.xlabel(kw.get('xlabel', 'x'))
    plt.ylabel(kw.get('xlabel', 'y'))
    plt.title(kw.get('title', 'Distributions'))
    plt.show()

