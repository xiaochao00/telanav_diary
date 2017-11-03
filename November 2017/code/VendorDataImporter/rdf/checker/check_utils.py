import socket
import os
import sys
from disk_size import DiskSize

LEVEL0_FLAG = "LEVEL0"
LEVREL0_SUFFIX = 'Level0'


def parse_remainsize_response_lines(response_lines):
    """
    :param response_lines:
    the response_lines of command 'df -m directory'

    Filesystem     1M-blocks    Used Available Use% Mounted on

    :return:
    parser the size of 'Available'
    """

    if not response_lines:
        error_out_print('parse the response line of command failed. response lines can not none ')
        return None
    # parse line num of  'Filesystem     1M-blocks    Used Available Use% Mounted on'
    specified_line_index = -1
    for line in response_lines:
        specified_line_index += 1
        if line.find("Filesystem") != -1 and line.find("Available") != -1:
            break

    if specified_line_index == -1 or specified_line_index == len(response_lines):
        error_out_print("Error: in parse the response line of df command. lines is %s ." % response_lines)
        return None
    # names = response_lines[0].strip().split()
    # the next line of specified_line_index
    names = ['Filesystem', '1M-blocks', 'Used', 'Available', 'Use%', 'Mounted on']
    values = response_lines[specified_line_index + 1].strip().split()

    response_dict = {}
    for i in range(len(names)):
        name = names[i]
        value = values[i]
        response_dict[name] = value

    if not response_dict or not ('Available' in response_dict.keys()):
        standout_print(' response of cmd  failed. please check')
        return None

    available_size = int(response_dict['Available'])

    return available_size


def is_localhost(host):
    """
    :param host:
        hostname judgement
    :return:
        is or not local hostname
    """
    if not host or not host.strip():
        return None

    ip_list = socket.gethostbyname_ex(socket.gethostname())
    # ('hqd-ssdpostgis-04.mypna.com', ['hqd-ssdpostgis-04'], ['10.224.76.206'])
    localhost_names = [ip_list[0]]
    localhost_aliases_names = ['localhost'] + ip_list[1]
    localhost_addresses = ['127.0.0.1'] + ip_list[2]

    localhost_list = localhost_names + localhost_aliases_names + localhost_addresses

    if host.strip() in localhost_list:
        standout_print(' address %s is localhost ' % host)
        return True

    else:
        standout_print('%s is not local address' % host)
        return False


def get_all_remain_size(host, tablespace_list):
    """
    :param host:
        get the remain size of each directory of tablespaces
    :param tablespace_list:
        structure : {key-value,}
        key: tablespace name
        value: tablespace location/directory
    :return:
        structure{key-value,}
        key: tablespace name
        value: the remain size of this tablespace name. type is DiskSize (size: , unit: UNIT_FORMAT)
        unit size MB
    """
    if not tablespace_list:
        error_out_print("Error: all tablespaces can not be None. check need")
        return None

    tablespaces_remain_size = {}

    if is_localhost(host):
        for tablespace_name in tablespace_list.keys():
            tablespace_location = tablespace_list[tablespace_name]
            remain_disk_size = local_remaining_spacesize(tablespace_location)
            tablespaces_remain_size[tablespace_name] = remain_disk_size

    else:
        from remote_model import RemoteModel
        remote_model = RemoteModel(host)

        for tablespace_name in tablespace_list.keys():
            tablespace_location = tablespace_list[tablespace_name]
            remain_size = remote_model.remain_space_size(tablespace_location)
            remain_disk_size = DiskSize(remain_size, DiskSize.UNIT_MB)
            tablespaces_remain_size[tablespace_name] = remain_disk_size

        remote_model.close()
    standout_print("Info: all tablespace in host[%s] remaining space are : %s" % (host, dic_print(tablespaces_remain_size)))
    return tablespaces_remain_size


def local_remaining_spacesize(directory_path):
    """
     unit size : MB
    :param directory_path:

    :return:
        free space of directory_path
    """
    import platform
    import ctypes

    disk_size = None
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(directory_path), None, None,
                                                   ctypes.pointer(free_bytes))
        disk_size = DiskSize.format_size_unit(size=free_bytes.value, unit=DiskSize.UNIT_B)
    else:
        try:
            # exception of Permission denied:
            st = os.statvfs(directory_path)
            disk_size = DiskSize.format_disk_size(size=st.f_bavail * st.f_frsize, unit=DiskSize.UNIT_B)

        except Exception, e:

            import commands
            cmd = 'sudo df -m %s' % directory_path
            status, print_lines = commands.getstatusoutput(cmd)
            # status the Exit status; print_lines the output
            if status == 0 and print_lines:
                size = parse_remainsize_response_lines(print_lines.split('\n'))
                disk_size = DiskSize.format_disk_size(size, unit=DiskSize.UNIT_MB)

            else:
                error_out_print("Error: command sudo df -m %s failed" % cmd)
                error_out_print("Error: status " + str(status))
                standout_print(print_lines)

                sys.exit(-1)

    return disk_size


def execute_cmd(cmd):
    standout_print("execute cmd is :%s" % cmd)
    os.system(cmd)


def standout_print(info):
    """
    print information to standout
    :param info:
    :return:
    """
    sys.stdout.write("CheckInfo: %s" % info)
    sys.stdout.write("\n")
    sys.stdout.flush()


def error_out_print(err):
    """

    :param err: information of error
    :return:
    """
    sys.stderr.write("CheckError: %s" % err)
    sys.stderr.write("\n")
    sys.stderr.flush()


def parser_previous_dbname(name):
    """
    parser the db name of last version
    NT_CN_17Q2_Level0 HERE_SKOR17Q1 HERE_EU17Q2
    :param name:
    :return:
     db name of last version
    """
    import re
    m = re.search('(\d+Q\d)', name, re.IGNORECASE)
    if not m:
        return None

    version = m.group(0)
    # print version
    m2 = re.match('(\d+)Q(\d)', version, re.IGNORECASE)
    if not m2:
        return None

    year = int(m2.group(1))
    q = int(m2.group(2))
    # print 'year',year,'q',q
    if q > 1:
        q = q - 1
    else:
        q = 4
        year = year - 1

    pre_version = str(year) + "Q" + str(q)
    pre_dbname = name.replace(version, pre_version)
    print 'the last one version is ', pre_dbname
    return pre_dbname


def host_region_minsize(host, username="postgres", password="postgres", port=5432):
    """
    get max size of db(in history version) in host of each region as the min in this version
    :param host:
    :return:
    all max size of region
    format {'region':size,
        'region':(size:,unit: UNIT_FORMAT),...}
    """
    from db_model import DBModel
    db_model = DBModel(host=host, username=username, password=password, port=port)

    region_selected_db = {}

    dbname_list = db_model.all_dbs()

    for db in dbname_list:
        if db.upper().startswith('HERE') or db.upper().startswith('NT') or db.upper().startswith("KOR"):
            region = parse_region(db)
            if not (region in region_selected_db):
                region_selected_db[region] = []
            region_selected_db[region].append(db)

    if not region_selected_db:
        return None

    region_maxsize = {}
    for region in region_selected_db.keys():
        dbs = region_selected_db[region]
        if not dbs:
            continue
        # {dbname:size,...}
        dbs_size_dic = db_model.size_db_list(dbs)
        # [(dbname,size),...] sorted by size
        size_list = sorted(dbs_size_dic.iteritems(), key=lambda d: d[1], reverse=True)

        db_maxsize = size_list[0]
        size = db_maxsize[1]
        region_maxsize[region] = DiskSize.format_size_unit(size=size, unit=DiskSize.UNIT_B)

    db_model.close()
    return region_maxsize


def parse_region(dbname):
    """
    parse dbname, return version name
    :param dbname: like SEA_HERE_17Q3
    :return:
    """
    if not dbname:
        return None
    # KOR db like KOR_HERE_15Q2
    if dbname.find("KOR") != -1:
        return "KOR"

    import re
    m = re.search(r'([a-z]+)_', dbname, re.IGNORECASE)
    if m:
        region = m.group(1)
        if dbname.upper().endswith(LEVEL0_FLAG):
            region += ' ' + LEVREL0_SUFFIX
        return region

    return None


def dic_print(dic):
    format_dic = {}
    for key in dic.keys():
        format_dic[key] = str(dic.get(key))
    return str(format_dic)


if __name__ == '__main__':
    # is_localhost('localhost')
    # is_localhost('172.16.101.92')
    # is_localhost('192.168.229.1')
    #
    # # 192.168.229.1
    # print localhost_remaining_spacesize("d:/")
    hostname = 'hqd-ssdpostgis-05.mypna.com'
    # from db_model import DBModel
    #
    # dm = DBModel(host=hostname, dbname='postgres')
    # tablespaces = dm.get_all_tablespace()
    #
    # print tablespaces
    # print dm.get_data_basedirectory()
    #
    # print get_all_remain_size(hostname, tablespaces)
    #
    # dm.close()
    # print parse_region('HERE_EU17Q2')
    # print parse_region('NT_CN_16Q1_Level0')
    # print parser_previous_dbname('HERE_EU17Q2')
    host_region_minsize(host=hostname)
