# -*- coding: utf-8 -*-
from util.common_utils import print_standout, print_error, pretty_size
from tablespace_util import find_host_all_tablespace_remain_size_dic
from check_utils import find_required_db_size, get_min_required_size
import optparse

DEFAULT_SIZE = 200 * 1024 * 2014 * 2014


def check_tablespace(host, dbname, tablespace_name, default_required_size):
    """Tablespace checker

    is or not enough for use
    :param host:
    :param dbname:
    :param tablespace_name:
    :param default_required_size:
    :return: True or False
    """
    if host == "10.179.1.110":
        print_error("KOR data have not right access, Pass")
        return True
    # 1. get the previous size of db. compare with default value, like 150G=150*1024MB
    required_size = default_required_size
    if not required_size:
        required_size = find_required_db_size(host, dbname, DEFAULT_SIZE)
    # 2. get remain size of all tablespace
    host_tablespace_name_remain_size_dic = find_host_all_tablespace_remain_size_dic(host, dbname)

    if tablespace_name not in host_tablespace_name_remain_size_dic:
        print_error("Error: can not find tablespace[%s] in host[%s]" % (tablespace_name, host))
        print_error("Info: all the tablespaces in host[%s] are %s" % (host,
                                                                      host_tablespace_name_remain_size_dic.keys()))
        return False

    remain_size = host_tablespace_name_remain_size_dic[tablespace_name]

    # remain_size must big than size of previous db
    # and more than one time. such give the min-rate 1.5
    print_standout("The need space size is %s and the remain size is %s." % (pretty_size(required_size),
                                                                             pretty_size(remain_size)))
    if remain_size > get_min_required_size(required_size):
        return True
    else:
        print_error(
            "The required size[%s], min evaluation required size[%s]. The remain size of [%s] is [%s] not enough." %
            (pretty_size(required_size), pretty_size(get_min_required_size(required_size)), tablespace_name,
             pretty_size(remain_size)))
        print_error("Tablespaces space info:%s." % [(name, pretty_size(size)) for name, size in
                                                    host_tablespace_name_remain_size_dic.iteritems()])
        return False


def main():
    parser = optparse.OptionParser()
    parser.add_option("-H", "--check-host", help="check host", dest="check_host")
    parser.add_option("-D", "--check-database", help="check database", dest="check_database")
    parser.add_option("-T", "--check-tablespace", help="check tablespace", dest="check_tablespace")
    parser.add_option("-S", "--default-size", help="required default database size(unit is GB)", dest="default_size", type=int)

    input_options, input_args = parser.parse_args()
    # default check
    if not input_options.check_host or not input_options.check_database or not input_options.check_tablespace:
        print_error("input check host or tablespace or database should not be none")
        print_standout(parser.print_help())
        return False
    #
    if input_options.default_size:
        input_options.default_size *= 1024 * 1024 * 1024
    return check_tablespace(input_options.check_host, input_options.check_tablespace, input_options.check_database, input_options.default_size)


if __name__ == '__main__':
    if not main():
        import sys
        sys.exit(-1)
    # print check_tablespace("hqd-ssdpostgis-05.mypna.com", "HERE_EU16Q4", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-05.mypna.com", "HERE_EU17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_SA17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_NA17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_IND17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_SEA17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_TWN17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_MEA17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_ANZ17Q3", "ssd2")
    # print check_tablespace("hqd-ssdpostgis-04.mypna.com", "HERE_SEA17Q3", "ssd2")
    # print check_tablespace("shd-dpc6x64ssd-02.china.telenav.com", "NT_CN_17Q2", "pg_default")
    # print check_tablespace("shd-dpc6x64ssd-02.china.telenav.com", "NT_CN_17Q2_Level0", "pg_default")
