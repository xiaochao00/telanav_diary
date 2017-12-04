# coding=utf-8
import paramiko
import stat
import os
import sys
import json
import re
from check_utils import standout_print, error_out_print

paramiko.util.log_to_file("filename.log")
max_deep_map = {"__rdf": 1, "components": 2, '__statistics': 1, 'speed_camera': 3}


class SFTPModel:
    def __init__(self, host, username, password, data_dir):
        self.host = host
        self.username = username
        self.password = password
        self.data_dir = data_dir

        self.t = None
        self.sftp = None

        self.init_connection()

    def init_connection(self):
        try:
            self.t = paramiko.Transport((self.host, 22))
            self.t.connect(username=self.username, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.t)  # use the style of t connection remote server
            standout_print('connection success')
        except Exception, e:
            if self.t:
                self.t.close()
            if self.sftp:
                self.sftp.close()
            error_out_print(e)
            error_out_print('connection failed')
            sys.exit(-1)

    def list_dir(self, path):
        return self.sftp.listdir(path)

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.t:
            self.t.close()


def filter_dir(dir_name):
    m = re.match('[a-z]+_[a-z]+_1[6-7]Q[1-4]', dir_name, re.IGNORECASE)
    return m


class FileModel:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class DirectoryModel:
    directory_list = []
    file_list = []

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


def parse_path(sftp, path, deep=1, max_deep=2):
    path = path.replace("\\", "/")
    structure_dic = {}
    mode = sftp.stat(path).st_mode
    if stat.S_ISDIR(mode):
        dir_list = sftp.listdir(path)
        for d in dir_list:
            # adjust diff directory, parse diff max deep
            tmp_max_deep = None
            if d in max_deep_map:
                tmp_max_deep = max_deep_map[d]
            if not tmp_max_deep:
                tmp_max_deep = max_deep

            full_path = os.path.join(path, d).replace("\\", "/")
            mode_dir = sftp.stat(full_path).st_mode
            value = None
            if stat.S_ISDIR(mode_dir):
                if deep < tmp_max_deep:
                    try:
                        value = parse_path(sftp, full_path, deep=(deep + 1), max_deep=tmp_max_deep)
                    except UnicodeDecodeError, e:
                        error_out_print(e)
                        value = None
                else:
                    if not sftp.listdir(full_path):
                        value = None
                    else:
                        value = dir_file_type_list(sftp.listdir(full_path))

            if value is None and deep == 1:
                # if there file in root path, ignore it
                continue
            structure_dic[d] = value
        return structure_dic
    else:
        return None

    return structure_dic


def dir_file_type_list(filename_list):
    """
    give the filename_list and return the all file type list
    :param filename_list:
    :return:
    """
    file_type_list = []
    for file_name in filename_list:
        m = re.match(".+(\..+)", file_name)
        if m:
            file_type_list.append(m.group(1))
    return list(set(file_type_list))


def get_directory_structure(host, user, pwd, base_directory):
    sftp_model = SFTPModel(host, user, pwd, base_directory)

    data_dir_list = sftp_model.list_dir(base_directory)
    # filter_dirs = filter_region(data_dir_list)
    filter_dirs = filter(filter_dir, data_dir_list)
    standout_print(filter_dirs)

    structure_dic = {}
    for p in filter_dirs:
        path_dic = parse_path(sftp_model.sftp, os.path.join(data_path, p))
        structure_dic[p] = path_dic
        # standout_print(str(path_dic).encode('utf-8'))
    sftp_model.close()

    json_data = json.dumps(structure_dic)
    standout_print(json_data)

    # merge
    region_stru_dic = merge_region_structure(structure_dic)
    json_data = json.dumps(region_stru_dic)
    standout_print(json_data)


def merge_region_structure(structure_dic):
    # 1.get every region`s structure list
    region_structure_list_dic = {}
    for region_name in structure_dic:
        region, is_level0 = parse_region_name(region_name)
        if is_level0:
            region += "_level0"
        if region in region_structure_list_dic:
            region_structure_list_dic[region].append(structure_dic[region_name])
        else:
            region_structure_list_dic[region] = [structure_dic[region_name]]

    # 2.merge list
    region_stru_dic = {}
    for region in region_structure_list_dic:
        stru_list = region_structure_list_dic[region]
        sum_dic = union_dic_list(stru_list)
        region_stru_dic[region] = sum_dic
    return region_stru_dic


def union_dic_list(dic_list):
    """
    [dic1,dic2,...]
    :param dic_list:
    :return: result of union for dic
    """
    sum_dic = {}
    for dic in dic_list:
        sum_dic = union_dic(sum_dic, dic)
    return sum_dic


def union_dic(dic1, dic2):
    if dic1 is None or dic2 is None:
        return None

    sum_dic = {}
    union_keys = set(dic1.keys()) | set(dic2.keys())
    for key in union_keys:
        value1 = dic1.get(key)
        value2 = dic2.get(key)

        if value1 is None or value2 is None:
            if value1 is None:
                sum_dic[key] = value2
            if value2 is None:
                sum_dic[key] = value1

        elif type(value1).__name__ == 'dict' and type(value2).__name__ == 'dict':
            sum_dic[key] = union_dic(value1, value2)

        elif type(value1).__name__ == 'list' and type(value2).__name__ == 'list':
            sum_dic[key] = list(set(value1 + value2))
        elif type(value1) is type(value2):
            sum_dic[key] = list(set([value1, value2]))
        else:
            sum_dic[key] = [value1, value2]

    return sum_dic


def parse_region_name(region_name):
    m = re.match("([a-z]+)_[a-z]+_\d{2}Q[1-4].*", region_name, re.IGNORECASE)
    if m:
        region = m.group(1)
        is_level0 = None
        if region_name.lower().endswith("level0"):
            is_level0 = True
        return region, is_level0
    return None, None


def err_check():
    hostname = "d-tempo-01.telenav.com"
    username = "mapuser"
    password = "mappna"
    sftp_model = SFTPModel(hostname, username, password, None)
    print sftp_model.list_dir("/var/www/html/data/EU_NT_16Q3_ADAS/Additional_Content")


if __name__ == '__main__':
    # r_model = RemoteModel(host='10.224.76.196')
    data_path = "/var/www/html/data"
    # CN : shd-dpc6x64ssd-02.china.telenav.com      mapuser/mappna
    # Other : d-tempo-01.telenav.com  mapuser mappna/hqd-ssdpostgis-04.mypna.com  mapuser/mapssdaccess
    # KOR : ec5d-pbfcompilation-02.dev.mypna.com shchshan A1B2c3d4
    hostname = "ec5d-pbfcompilation-02.dev.mypna.com"
    username = "shchshan"
    password = "A1B2c3d4"

    get_directory_structure(host=hostname, user=username, pwd=password, base_directory=data_path)
    pass

    # err_check
