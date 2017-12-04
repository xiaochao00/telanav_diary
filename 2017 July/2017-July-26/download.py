#coding=utf-8
import urllib
import os
def Schedule(a,b,c):
    '''''
        a:已经下载的数据块
        b:数据块的大小
        c:远程文件的大小
    '''
    per = 100.0 * a * b / c
    if per > 100 :
        per = 100
    print '%.2f%%' % per
url='https://tcs.ext.here.com/maptools/distributions/Map_Tools_20170413.zip'
local=os.path.join('C:\Users\shchshan\Desktop','Map_Tools_20170413.zip')
urllib.urlretrieve(url,local,Schedule)
