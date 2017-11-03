# -*- coding: utf-8 -*-
import os
from db_model import DBModel
from disk_size import DiskSize
from config_reader import save_region_size, read_db_config
from check_utils import parser_previous_dbname, standout_print, get_all_remain_size, host_region_minsize, error_out_print, dic_print

DB_DIFFERENT_RATE = 1.5
DB_INCREMENTAL_SIZE = 204800
DB_DEFAULT_SIZE = 204800


def check_tablespace(host, dbname, tablespace):
    """
    space size of tablespace checker.
    is or not enough for use
    :param host:
    :param dbname:
    :param tablespace:
    :return: True or False
    """
    if not host or not tablespace:
        error_out_print("Error: in tablespace checker the host['%s']  or tablespace['%s'] cna not be none." % (host, tablespace))
        return False

    dm = DBModel(host=host)
    # 1. get the previous size of db. if not must give a default value like 150G=150*1024MB
    pre_dbname = parser_previous_dbname(dbname)
    pre_db_size = DiskSize.format_size_unit(size=dm.get_db_size(pre_dbname), unit=DiskSize.UNIT_B)
    if not pre_db_size:
        # if host have no this database name, load default size from config file
        standout_print("Info: get the size of the last db[%s] of db[%s] failed in host[%s]. load default min size" % (
            pre_dbname, dbname, host))
        standout_print("Info: as reason before, use default min_size from conf file")

        pre_db_size = get_min_tablespace_size(dbname)
        if not pre_db_size:
            error_out_print("Error:need check the config file of min size of db[%s], if host[%s] in it. Read failed" % (dbname, host))
            standout_print("Info: use default value  ")
            # use default value
            pre_db_size = DiskSize(DB_DEFAULT_SIZE, DiskSize.UNIT_MB)
            # return False

    # 2. get remain size of all tablespace
    tablespaces = dm.get_all_tablespace()
    remain_sizes_dic = get_all_remain_size(host, tablespaces)

    dm.close()

    if not (tablespace in remain_sizes_dic.keys()):
        error_out_print("Error: can not find tablespace[%s] in host[%s]" % (tablespace, host))
        error_out_print("Info: all the tablespaces in host[%s] are %s" % (host, tablespaces.keys()))
        return False

    remain_size = remain_sizes_dic[tablespace]

    # remain_size must big than size of previous db
    # and more than one time. such give the min-rate 1.5
    standout_print("Info: the need space size is %s and the remain size is %s." % (pre_db_size, remain_size))
    if remain_size.size > min_need_size(pre_db_size.size):
        return True
    else:
        error_out_print(
            "Info: the remain size[%s MB] of tablespace['%s'] is not enough to the evaluation size [%s MB]. check need " %
            (remain_size, tablespace, pre_db_size))
        error_out_print("Tablespaces space info:" + dic_print(remain_sizes_dic) + ". maybe can help you ")
        return False


def min_need_size(db_size):
    """
    :param db_size:
    :return:
        min(1.5 * db_size, db_size + 200G)
    """
    return min(DB_DIFFERENT_RATE * db_size, db_size + DB_INCREMENTAL_SIZE)


def get_min_tablespace_size(dbname):
    """
    dbname must satisfy rule: vendor_region[_]version[_level0]
        like : TN_CN_17Q1,HERE_EU17Q2,HERE_SA17Q2
    :param dbname:
    :return:
    """
    standout_print("Info: search size of last db of db[%s] failed, load default config file." % dbname)
    from check_utils import parse_region
    from config_reader import min_tablespace_size, TABLESPACE_SIZE_CONF

    if not os.path.exists(TABLESPACE_SIZE_CONF):
        # generator new tablespace size conf file
        generator_region_size()

    region = parse_region(dbname)
    disk_size = min_tablespace_size(region)

    return disk_size


def generator_region_size():
    """
    automatic generator the size of all region
    :return:
    save region_file done
    """
    # hosts = ['hqd-ssdpostgis-04.mypna.com', 'hqd-ssdpostgis-05.mypna.com', "10.179.1.110",
    #          'shd-dpc6x64ssd-02.china.telenav.com']
    host_options = read_db_config()
    region_size_dic = {}
    for host_option in host_options:
        region_size = host_region_minsize(host=host_option.host, username=host_option.username, password=host_option.password, port=host_option.port)
        region_size_dic = dict(region_size_dic.items() + region_size.items())

    save_region_size(region_size_dic)


if __name__ == '__main__':
    pass
    hostname = 'hqd-ssdpostgis-04.mypna.com'
    # # # tablespace_remain_size(hostname=hostname)
    # # # parser_last_dbname('HERE_EU_17Q')
    # print check_tablespace(hostname, 'HERE_SA17Q2', 'pg_default')
    # print get_min_tablespace_size('HERE_EU_17Q2')
    # #
    # prepared_db_list = ["NT_CN_17Q2_Level0", "NT_CN_17Q2", ""]

    print check_tablespace("hqd-ssdpostgis-05.mypna.com", "EU_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-05.mypna.com", "EU_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "SA_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "NA_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "IND_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "SEA_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "TWN_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "MEA_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "ANZ_HERE_17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "SEA_HERE_17Q3", "ssd2")
    print check_tablespace("shd-dpc6x64ssd-02.china.telenav.com", "CN_NT_17Q2_Level0", "pg_default")
    print check_tablespace("shd-dpc6x64ssd-02.china.telenav.com", "CN_NT_17Q2_Level0", "pg_default")

    # dm = DBModel("hqd-ssdpostgis-04.mypna.com")
    # tablespace_list = dm.get_all_tablespace()
    # remain_tablespace_remain_size_dic = get_all_remain_size("hqd-ssdpostgis-04.mypna.com",tablespace_list=tablespace_list)
    # print remain_tablespace_remain_size_dic.items()
    #
    # import pprint
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(remain_tablespace_remain_size_dic)
    #
    # import json
    # data_str = json.dumps(remain_tablespace_remain_size_dic)
    # print data_str
