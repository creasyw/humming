【Dependency】

libmad
python 2.6+
pymad
numpy
scipy
Mlpy with GNU-GSL


【主要文件与函数】

每个脚本所需参数的使用以及hard-coded变量的说明都在脚本中以注释形式给出。

waveform.py	包含读取音频文件以及降采样的函数。其中读取音频文件的函数，可按帧读取mp3文件数据，
		生成pcm一维数组，按顺序输出每个采样点的数值，直接运行可用于输出音频波形图。
		降采样函数，使用scipy函数对高采样的音频序列降采样到指定频率。

segmentaxis.py	按照指定的方向（对于二维数组而言，x轴或y轴），对数组进行分割。涉及的指定参数包括
		分割数组的步长，以及每次分割与之前重叠的长度。

find_landmarks.py	对提取的音频数组进行时频分析，返回以时频图中的局部最高点为依据的音频特征
			组。是算法的主要函数之一。

retrieval.py	检索音频文件的函数。其中包括寻找检索文件特征最丰富的片段，以及对检索返回结果进行
		时序筛选和其他后处理。是算法的另一个主要函数。其中的mode，单纯存储音频特征设定为
		1，过滤数据库则设置为2，正常使用（先过滤，后决定是否存储）设定为0。（mode值的设定
		在batchprocess.py和superbatch.py两个文件中。）

dataviasqlite.py	程序和数据库交互的函数。包含了按歌曲id将整首歌曲的特征存入/取出数据库，以
			及按照特征值在数据库进行检索。前期使用的是SQLite数据库，后期修改为MySQL数
			据库查询语句。

batchprocess.py		为整首歌的特征提取而加入的函数。因为整首歌提取时，会占用大量的内存，而部分
			数组无法及时释放导致程序占用内存的数量会始终上升。在这个脚本中，使用
			subprocess从而强制程序在完成一个音频文件的分析后释放所占用的资源。

superbatch.py	使用dpark并行处理时加入的脚本。因为每个音频文件处理需要的耗时再乘以需要处理的大量文
		件，导致depark并行化之后，排在队列靠后位置的任务总会因为超时而失败。这个脚本将需要处
		理的文件列表分块，并调用batchprocess使用dpark进行处理。

svm.model	离线训练的SVM模型，用于retrieval函数的后处理模块，筛选可能重复的歌曲。

track_list.npy	歌曲列表。从radio_track_stats表中，按照播放次数降序排列的数组，可用numpy.load直接
		读取。

misc/		对数据做特定操作的脚本，与整体工作流程无关。

output/		暂时存放音乐文件的文件夹。


【工作流程】
音乐特征提取：将superbatch.py和batchprocess.py的mode设置为1。（可在dpark环境中运行）
		程序会从当前目录中的track_list,npy中读取歌曲id，暂存在output目录中，运行结束后会删除
		相应的临时文件。注意：在程序目录中的output和matplot两个文件夹，需要将权限设置为777。
歌曲过滤去重：将superbatch.py的mode设置为2，此外，需要指定向内存中读取的表格存放位置，定义在
		superbatch.py中的table变量。是单机单核运行的。
两个工作任务均需要使用DoubalAlg库中的get_rivendell_store以连接数曲库。
命令行运行 $ python superbatch.py 即可。


【参考文献】
1. dongying 底层音频信号处理模块。
2. Avery Li-Chun Wang, An Industrial-Strength Audio Search Algorithm.
3. Shumeet Baluja, Michele Covell, Waveprint: Efficient wavelet-based audio fingerprinting.
4. Edith Cohen, etc. Finding Interesting Associations without Support Pruning.
5. Alexandr Andoni, Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor in High Dimensions.


