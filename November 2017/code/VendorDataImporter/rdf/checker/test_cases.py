# -*- coding: utf-8 -*-

'''
test case file
in this
'''
import sys
from db_model import DBModel
from config_reader import tablespace_size_config
from check_utils import parse_region


def db_minsize(host):
    """
    get all size of db in host
    :param host:
    :return:
    all size of db
    """
    region_list = tablespace_size_config()

    db_model = DBModel(host)

    selected_db = []
    dbname_list = db_model.all_dbs()
    for db in dbname_list:
        for region in region_list:
            if db.upper().find(region.upper()) and (db.upper().startswith('HERE') or db.upper().startswith('NT')):
                selected_db.append(db)

    if not selected_db:
        return None

    dbsize_list = db_model.size_dblist(selected_db)
    print sorted(dbsize_list.iteritems(), key=lambda d: d[0], reverse=True)

    # test min_dbsize in config file
    from tablespace_checker import get_min_tablespace_size
    for db in selected_db:
        size = get_min_tablespace_size(db)
        print "min size of db[%s] is" % db, size

    return dbsize_list


def standout_print(info):
    """
    print information to standout
    :param info:
    :return:
    """
    sys.stdout.write(info)
    sys.stdout.write("\n")


def test_remote_model():
    from remote_model import RemoteModel
    # rm = RemoteModel('10.179.1.110')
    rm = RemoteModel('shd-dpc6x64ssd-02.china.telenav.com')


if __name__ == '__main__':
    # test_islocalhost()

    # hosts = ['hqd-ssdpostgis-04.mypna.com', 'hqd-ssdpostgis-05.mypna.com', '10.179.1.110',
    #          'shd-dpc6x64ssd-02.china.telenav.com']
    # # for host in hosts:
    # #     db_minsize(host)
    # for host in hosts:
    #     host_region_minsize(host=host)
    #     # test_remote_model()
    from check_utils import host_region_size

    host_region_size()
