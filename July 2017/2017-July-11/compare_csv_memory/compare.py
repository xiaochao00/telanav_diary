#coding=utf-8
'''
http://python3-cookbook.readthedocs.io/zh_CN/latest/c06/p02_read-write_json_data.html

compare the json result of static csv files with memory json data result 
'''

import json

def loadJSON(filepath):
    with open(filepath,'r') as json_file:
        data = json.load(json_file)
    #print data
    return data

data1 = loadJSON('NodesCitycenter')
data2 = loadJSON('NodesCitycenter_2')
#print data1['nodes_city_center_capital#yes']
print 'data1 key num:',len(data1.keys())
print 'data2 key num:',len(data2.keys())
for key in data1.keys():
    if data2.has_key(key):
        v1 = data1[key]
        v2 = data2[key]
        if v1 != v2:
            print 'error value not match: key-',key,'v1,v2:',v1,v2
    else:
        print 'error of key is not match: key-',key,'v1,v2:',data1[key]
for key in data2.keys():
    if not data1.has_key(key):
        print '%s is not in data1' % key


