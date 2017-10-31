import multiprocessing
import time
from xml.dom import minidom as minidom
from xml.dom import pulldom as pulldom
import os



def a(num):
    print 'begin  %s' % num, time.time()
    time.sleep(2)
    print 'end  %s' % num, time.time()
    return num * num


def parse(poi_file):
    # doc1 = minidom.parse(poi_file)
    # doc2 = pulldom.parse(open(poi_file))

    events = pulldom.parse(poi_file)
    toktype, doc2 = events.getEvent()
    events.expandNode(doc2)
    events.clear()
    # print doc1
    print doc2
    # print doc1 == doc2

    return 'parse file %s finish.' % os.path.basename(poi_file)

def parse_by_ET(file_path):
    import xml.etree.ElementTree as ET



if __name__ == '__main__':
    # pool = multiprocessing.Pool(processes=2)
    # parameters = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    #
    # results = pool.map(a, parameters)
    #
    # # pool.close()
    # # pool.join()
    #
    # print 'results', results
    # for result in results:
    #     print 'result', result
    # ############################
    # pool = multiprocessing.Pool(processes=1)
    # files = [r'C:\Users\shchshan\Desktop\vde\State_14120001\POI_1414000001.xml',
    #          r'C:\Users\shchshan\Desktop\vde\State_14120016\POI_1414001551.xml']
    # results = pool.map(parse,files)
    #
    # for r in results:
    #     print r
    # C:\Users\shchshan\Desktop\vde\Category_110000.xml
    # C:\Users\shchshan\Desktop\vde\State_14120001\POI_1414000001.xml
    print parse(r'C:\Users\shchshan\Desktop\vde\State_14120001\POI_1414000001.xml')
