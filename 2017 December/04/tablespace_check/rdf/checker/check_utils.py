import os
import re
import socket
from disk_size import DiskSize
from db_module import DBModule
from remote_module import RemoteModel
from get_common_utils import print_standout, print_error, parse_size_info_response_lines, json_print, read_login_config, parse_rdf_db

LEVEL0_FLAG = "LEVEL0"
LEVEL0_SUFFIX = "Level0"


def is_localhost(host):
    """
    :param host: hostname judgement
    :return: is or not local host
    """
    if not host or not host.strip():
        return None

    ip_list = socket.gethostbyname_ex(socket.gethostname())
    # ("hqd-ssdpostgis-04.mypna.com", ["hqd-ssdpostgis-04"], ["10.224.76.206"])
    localhost_names = [ip_list[0]]
    localhost_aliases_names = ["localhost"] + ip_list[1]
    localhost_addresses = ["127.0.0.1"] + ip_list[2]

    localhost_list = localhost_names + localhost_aliases_names + localhost_addresses

    if host.strip() in localhost_list:
        print_standout("Address %s is localhost " % host)
        return True

    print_standout("%s is not local address" % host)
    return False


def get_all_remain_size(host, tablespace_path_dic):
    """
    :param host: hostname
    :param tablespace_path_dic:
        structure : {key-value,}
        key: tablespace name
        value: tablespace location/directory
    :return:
        structure{key-value,}
        key: tablespace name
        value: the remain size of this tablespace name. type is DiskSize (size: , unit: UNIT_FORMAT)
        unit size MB
    """
    if not tablespace_path_dic:
        print_error("Check tablespaces can not be None.")
        return None

    tablespaces_remain_size = {}
    tablespace_size_info_dic = get_tablespace_size_info(host, tablespace_path_dic)
    for tablespace_name, size_info in tablespace_size_info_dic.iteritems():
        disk_size = DiskSize.format_size_unit(size=size_info["Available"], unit=DiskSize.UNIT_B)
        tablespaces_remain_size[tablespace_name] = disk_size

    return tablespaces_remain_size


def get_tablespace_size_info(host, tablespace_path_dic):
    """Get the tablespace size info in this host

    :param host:
    :param tablespace_path_dic: {tablespace:path,...}
    :return:{tablespace:{"Available": ,"Used": ,"TotalSize": },...} . size unit is B
    """
    if not tablespace_path_dic:
        print_error("All tablespaces can not be None. check need")
        return None

    tablespace_size_info_dic = {}
    if is_localhost(host):
        for tablespace_name, tablespace_location in tablespace_path_dic.iteritems():
            cmd = "sudo df %s" % tablespace_location
            size_info_lines = os.popen(cmd).readlines()
            size_info = parse_size_info_response_lines(size_info_lines)
            tablespace_size_info_dic[tablespace_name] = size_info
    else:
        if host == "10.179.1.110":
            print_error("KOR data no right to access. pass it .")
            return {host: None}

        login_user, login_password = read_login_config(host)
        remote_model = RemoteModel(host, login_user, login_password)
        for tablespace_name, tablespace_location in tablespace_path_dic.iteritems():
            cmd = "sudo df %s" % tablespace_location
            size_info_lines = remote_model.execute_command(cmd)
            size_info = parse_size_info_response_lines(size_info_lines)
            tablespace_size_info_dic[tablespace_name] = size_info

        remote_model.close()
    print_standout("All tablespace in host[%s] size space info are :" % host)
    json_print(tablespace_size_info_dic)

    return tablespace_size_info_dic


def execute_cmd(cmd):
    print_standout("execute cmd is :%s" % cmd)
    os.system(cmd)


def parser_previous_dbname(name):
    """Get the dbname of last version

    NT_CN_17Q2_Level0 HERE_SKOR17Q1 HERE_EU17Q2
    :param name:
    :return:
     db name of last version
    """
    m = re.search("(\d+Q\d)", name, re.IGNORECASE)
    if not m:
        return None

    version = m.group(0)
    # print version
    m2 = re.match("(\d+)Q(\d)", version, re.IGNORECASE)
    if not m2:
        return None

    year = int(m2.group(1))
    q = int(m2.group(2))
    # print "year",year,"q",q
    if q > 1:
        q = q - 1
    else:
        q = 4
        year = year - 1

    last_version = str(year) + "Q" + str(q)
    last_dbname = name.replace(version, last_version)
    print_standout("The last version of[%s] is[%s]" % (name, last_dbname))
    return last_dbname


def host_region_minsize(host, username="postgres", password="postgres", port=5432):
    """Get max size of db(in history version) in host of each region as the min in this version

    :param host:
    :param username:
    :param password:
    :param port:
    :return:
    all max size of region
    format {"region":size,
        "region":(size:,unit: UNIT_FORMAT),...}
    """

    db_module = DBModule(host=host, username=username, password=password, port=port)

    region_selected_db = {}
    # 1.get all dbs of some regions in this host
    dbname_list = db_module.all_dbs()

    for db in dbname_list:
        if db.upper().startswith("HERE") or db.upper().startswith("NT") or db.upper().startswith("KOR"):
            region = parse_region(db)
            if not (region in region_selected_db):
                region_selected_db[region] = []
            region_selected_db[region].append(db)

    if not region_selected_db:
        return None
    # 2.get the max size as the min config size of this region
    region_maxsize = {}
    for region in region_selected_db.keys():
        dbs = region_selected_db[region]
        if not dbs:
            continue
        # {dbname:size,...}
        dbs_size_dic = db_module.size_db_list(dbs)
        # [(dbname,size),...] sorted by size
        size_list = sorted(dbs_size_dic.iteritems(), key=lambda d: d[1], reverse=True)

        db_maxsize = size_list[0]
        size = db_maxsize[1]
        region_maxsize[region] = DiskSize.format_size_unit(size=size, unit=DiskSize.UNIT_B)

    db_module.close()
    return region_maxsize


def parse_region(dbname):
    """Parse dbname, return region name

    :param dbname: like SEA_HERE_17Q3
    :return:
    """
    vendor, region, version, level0 = parse_rdf_db(dbname)
    if level0:
        region += " " + LEVEL0_SUFFIX
    return region


def dic_print(dic):
    format_dic = {}
    for key in dic.keys():
        format_dic[key] = str(dic.get(key))
    return str(format_dic)


if __name__ == "__main__":
    # is_localhost("localhost")
    # is_localhost("172.16.101.92")
    # is_localhost("192.168.229.1")
    #
    # # 192.168.229.1
    # print localhost_remaining_spacesize("d:/")
    hostname = "hqd-ssdpostgis-05.mypna.com"
    # from db_model import DBModel
    #
    # dm = DBModel(host=hostname, dbname="postgres")
    # tablespaces = dm.get_all_tablespace()
    #
    # print tablespaces
    # print dm.get_data_basedirectory()
    #
    # print get_all_remain_size(hostname, tablespaces)
    #
    # dm.close()
    print parse_region("HERE_EU17Q2")
    # print parse_region("NT_CN_16Q1_Level0")
    # print parser_previous_dbname("HERE_EU17Q2")
    host_region_minsize(host=hostname)
