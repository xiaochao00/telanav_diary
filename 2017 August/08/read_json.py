import json

with open('Compilation Options.json','r') as jsonfile:
    data = json.load(jsonfile)
    #print data
    arr = data["Compilation Options"]
    #print arr[1]
    for a in arr:
        print 'region:',a['region'],
        print 'key_list:',a['key_list'],
        print 'database_operations:',a['database_operations']
