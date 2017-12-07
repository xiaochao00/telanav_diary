# -*- coding: utf-8 -*-
import os
from db_module import DBModule
from disk_size import DiskSize
from check_utils import parser_previous_dbname, get_all_remain_size, host_region_minsize, dic_print, parse_region
from get_common_utils import print_error, print_standout, save_region_size, read_db_config, min_tablespace_size, TABLESPACE_SIZE_CONF

DB_DIFFERENT_RATE = 1.5
DB_INCREMENTAL_SIZE = 204800
DB_DEFAULT_SIZE = 204800


def check_tablespace(host, dbname, tablespace_name):
    """Tablespace checker

    is or not enough for use
    :param host:
    :param dbname:
    :param tablespace_name:
    :return: True or False
    """
    if not host or not tablespace_name:
        print_error("Host[%s] or tablespace[%s] can not be none." % (host, tablespace_name))
        return False
    if host == "10.179.1.110":
        print_error("KOR data have not right access, Pass")
        return True
    dm = DBModule(host=host)
    # 1. get the previous size of db. if not must give a default value like 150G=150*1024MB
    pre_dbname = parser_previous_dbname(dbname)
    pre_db_size = DiskSize.format_size_unit(size=dm.get_db_size(pre_dbname), unit=DiskSize.UNIT_B)
    if not pre_db_size:
        # if host have no this database name, load default size from config file
        print_standout("Get the size of the last db[%s] of db[%s] failed in host[%s]. load default min size" %
                       (pre_dbname, dbname, host))
        print_standout("As reason before, use default min_size from conf file")
        pre_db_size = get_min_tablespace_size(dbname)

    # 2. get remain size of all tablespace
    tablespace_path_dic = dm.get_all_tablespace_size_dic()
    print_standout(tablespace_path_dic)
    remain_sizes_dic = get_all_remain_size(host, tablespace_path_dic)

    dm.close()

    if not (tablespace_name in remain_sizes_dic.keys()):
        print_error("Error: can not find tablespace[%s] in host[%s]" % (tablespace_name, host))
        print_error("Info: all the tablespaces in host[%s] are %s" % (host, tablespace_path_dic.keys()))
        return False

    remain_size = remain_sizes_dic[tablespace_name]

    # remain_size must big than size of previous db
    # and more than one time. such give the min-rate 1.5
    print("Info: the need space size is %s and the remain size is %s." % (pre_db_size, remain_size))
    if remain_size.size > min_need_size(pre_db_size.size):
        return True
    else:
        print_error(
            "Info: the remain size[%s] of tablespace['%s'] is not enough to the evaluation size [%s]. "
            "check need " % (remain_size, tablespace_name, pre_db_size))
        print_error("Tablespaces space info:" + dic_print(remain_sizes_dic) + ". maybe can help you ")
        return False


def min_need_size(db_size):
    """
    :param db_size:
    :return:
        min(1.5 * db_size, db_size + 200G)
    """
    return min(DB_DIFFERENT_RATE * db_size, db_size + DB_INCREMENTAL_SIZE)


def get_min_tablespace_size(dbname):
    """Min size of DB

    dbname must satisfy rule: vendor_region[_]version[_level0]
        like : TN_CN_17Q1,HERE_EU17Q2,HERE_SA17Q2
    :param dbname:
    :return:
    """
    print_standout("Load default config file.")

    if not os.path.exists(TABLESPACE_SIZE_CONF):
        # generator new tablespace size conf file
        generate_region_size()

    region = parse_region(dbname)
    disk_size = min_tablespace_size(region)

    if disk_size:
        # if all none, default value
        disk_size = DiskSize(DB_DEFAULT_SIZE, DiskSize.UNIT_MB)

    return disk_size


def generate_region_size():
    """Generate database_size.conf

    the need database size of each region
    :return:
    """
    host_options = read_db_config()
    region_size_dic = {}
    for host_option in host_options:
        if host_option.host == "10.179.1.110":
            print_error("KOR data have no right access! Please pass")
            continue
        region_size = host_region_minsize(host=host_option.host, username=host_option.username,
                                          password=host_option.password, port=host_option.port)
        region_size_dic = dict(region_size_dic.items() + region_size.items())

    save_region_size(region_size_dic)


if __name__ == '__main__':
    print check_tablespace("hqd-ssdpostgis-05.mypna.com", "HERE_EU16Q4", "ssd2")
    print check_tablespace("hqd-ssdpostgis-05.mypna.com", "HERE_EU17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_SA17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_NA17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_IND17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_SEA17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_TWN17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_MEA17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_ANZ17Q3", "ssd2")
    print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_SEA17Q3", "ssd2")
    print check_tablespace("shd-dpc6x64ssd-02.china.telenav.com", "NT_CN_17Q2", "pg_default")
    print check_tablespace("shd-dpc6x64ssd-02.china.telenav.com", "NT_CN_17Q2_Level0", "pg_default")
