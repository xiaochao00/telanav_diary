import os
import sys
from DBModule import DBModule
from host_config.config_reader import read_login_config
from RemoteModule import RemoteModule
from util.command_utils import parse_size_info_response_lines
from util.common_utils import is_localhost, print_error


def find_host_all_tablespace_remain_size_dic(host, database_name):
    """This host`s all tablespace remain size(left size)

    :param host:
    :param database_name:
    :return: {tablespace_name:remain_size,...} unit:B
    """
    tablespace_name_remain_size_dic = {}
    tablespace_name_size_info_dic = find_tablespace_disk_space_info_dic(host, database_name)
    for tablespace_name, size_info in tablespace_name_size_info_dic.iteritems():
        remain_size = size_info["Available"]
        tablespace_name_remain_size_dic[tablespace_name] = remain_size

    return tablespace_name_remain_size_dic


def find_tablespace_disk_space_info_dic(host, database_name="postgres"):
    """get the disk usage of each tablespace path
        Tips:
            1. be clear that the value "Used" do not means this tablespace`s size.
    :param host:
    :param database_name:
    :return:  {tablespace:{"Available": ,"Used": ,"TotalSize": }}
    """
    # 1.get all tablespace and path
    tablespace_name_path_dic = find_tablespace_name_path_dic(host, database_name)
    # 2.get the space information
    tablespace_disk_space_info_dic = {}
    response_lines_list = []
    if is_localhost(host):
        for tablespace_name, tablespace_location in tablespace_name_path_dic.iteritems():
            cmd = "sudo df %s" % tablespace_location
            size_info_lines = os.popen(cmd).readlines()
            response_lines_list.append(size_info_lines)
            size_info = parse_size_info_response_lines(size_info_lines)
            tablespace_disk_space_info_dic[tablespace_name] = size_info

    else:
        print_error("Host is not local.")
        sys.exit(-1)
        # if host == "10.179.1.110":
        #     print_error("KOR data no right to access. pass it .")
        #     return {host: None}
        #
        # login_user, login_password = read_login_config(host)
        # remote_model = RemoteModule(host, login_user, login_password)
        # for tablespace_name, tablespace_location in tablespace_name_path_dic.iteritems():
        #     cmd = "sudo df %s" % tablespace_location
        #     size_info_lines = remote_model.execute_command(cmd)
        #     response_lines_list.append(size_info_lines)
        #     size_info = parse_size_info_response_lines(size_info_lines)
        #     tablespace_disk_space_info_dic[tablespace_name] = size_info
        # remote_model.close()

    return tablespace_disk_space_info_dic


def find_tablespace_name_path_dic(host, database_name="postgres"):
    """Name:location path"""
    dm = DBModule(host, database_name)
    # {name:tablespace_location,...}
    tablespace_name_path_dic = dm.select_all_tablespace_path_dic()
    dm.close()
    return tablespace_name_path_dic
