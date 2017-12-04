# -*- coding: utf-8 -*-

'''
得到远程目录的剩余空间大小
'''
import tablespace_checker


r = tablespace_checker.RemoteModel(hostname='hqd-ssdpostgis-04.mypna.com')

response_lines = r.excute_command('sudo df  /usr/local/pgsql/data/ssd1')

for line in response_lines:
    print line
