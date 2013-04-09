import waveform as wv
import numpy.fft as ft
import numpy


def flat_window(N):
	return numpy.array([1.] * N)


def walk_audio(fh, win, step, st=0, to=float('inf'), join=False, wt=numpy.hanning):
	weights = wt(win)
	ghw = numpy.sqrt(win)
	for pcms in wv.walk_audio(fh, win, step, st, to, join):
		freqs = []
		for ch in pcms:
			#print "ch:", ch
			freq_bins = ft.rfft(weights * ch) / ghw
			freqs.append(freq_bins)
		yield freqs


def plot_spectrogram(spec, Xd=(0,1), Yd=(0,1)):
	import matplotlib
	#matplotlib.use('GTKAgg')
	import matplotlib.pyplot as plt
	import matplotlib.cm as cm
	from matplotlib.image import NonUniformImage
	import matplotlib.colors as colo
	#
	x_min, x_max = Xd
	y_min, y_max = Yd
	#
	fig = plt.figure()
	nf = len(spec)
	for ch, data in enumerate(spec):
		#print ch, data.shape
		x = numpy.linspace(x_min, x_max, data.shape[0])
		y = numpy.linspace(y_min, y_max, data.shape[1])
		#print x[0],x[-1],y[0],y[-1]
		ax = fig.add_subplot(nf*100+11+ch)
		im = NonUniformImage(ax, interpolation='bilinear', cmap=cm.gray_r,
				norm=colo.LogNorm(vmin=.00001))
		im.set_data(x, y, data.T)
		ax.images.append(im)
		ax.set_xlim(x_min, x_max)
		ax.set_ylim(y_min, y_max)
		ax.set_title('Channel %d' % ch)
		#ax.set_xlabel('timeline')
		ax.set_ylabel('frequency')
		print 'Statistics: max<%.3f> min<%.3f> mean<%.3f> median<%.3f>' % (data.max(), data.min(), data.mean(), numpy.median(data))
	#
	plt.show()


if __name__ == '__main__':
	import getopt, sys
	def exit_with_usage():
		print "Usage: $ python spectrogram.py [-s start_sec] [-t to_sec] [-w window_size] [-h hop_size] song.mp3"
		exit()

	try:
		opts, args = getopt.getopt(sys.argv[1:], "s:t:w:h:")
	except getopt.GetoptError as ex:
		print ex
		exit_with_usage()

	if len(args) != 1:
		#print args
		exit_with_usage()

	mf = wv.open_audio(args[0])
	ch = 2
	if mf.mode() == wv.mad.MODE_SINGLE_CHANNEL:
		ch = 1
	total = mf.total_time()

	print "SampleRate: %d Hz\nBitRate: %d kbps\nChannel(s): %d\nDuration: %d sec"\
			% (mf.samplerate(), mf.bitrate()/1000, ch, mf.total_time() / 1000)

	st = 0
	to = float('inf')
	win = 1024
	hop = 512

	for o, a in opts:
		if o == '-s':
			st = int(float(a) * 1000)
		elif o == '-t':
			to = int(float(a) * 1000)
		elif o == '-w':
			win = int(a)
		elif o == '-h':
			hop = int(a)

	if st < 0 or st >= to or st >= mf.total_time:
		print "Start time must be >= 0, <= end_time and total time."
		exit_with_usage()
	if to >= mf.total_time():
		to = float('inf')
	if win < 16 or win < hop:
		print "Window size must be >= hop size and >= 16"
		exit_with_usage()

	spec = [[],[]]
	for freqs in walk_audio(mf, win, hop, st, to, join=False):
		spec[0].append(abs(freqs[0][1:]))
		spec[1].append(abs(freqs[1][1:]))

	if to == float('inf'):
		to = total

	samplerate = mf.samplerate()
	hz_min = samplerate / win
	hz_max = samplerate / 2
	plot_spectrogram(numpy.array(spec), (st/1000,to/1000), (hz_min,hz_max))

