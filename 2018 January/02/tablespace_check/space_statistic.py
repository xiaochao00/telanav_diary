# encoding=utf8
import os
import sys
import json
from collections import namedtuple
from host_config.config_reader import read_db_config
from DBModule import DBModule
from db_info_collections import DBInfo, TablespaceInfo
from util.common_utils import filter_database_name, parse_rdf_unidb_db_name, print_error, parse_vendor_raw_data_name, filter_raw_raw_data_name, pretty_size
from tablespace_util import find_tablespace_name_path_dic, find_tablespace_disk_space_info_dic

Disk_Usage = namedtuple("usage", "total used free percent")


class DBStatisticUtils(object):
    @staticmethod
    def get_all_database_info(host_option):
        hostname = host_option.host
        username = host_option.username
        password = host_option.password
        port = host_option.port

        db_model = DBModule(host=hostname, username=username, password=password, port=port)
        all_database_name_size_dic = db_model.select_all_db_size_dic()

        selected_database_name_size_dic = dict([(d_name, size) for d_name, size in all_database_name_size_dic.iteritems()
                                                if filter_database_name(d_name)])

        database_info_list = []
        for database_name, db_size in selected_database_name_size_dic.iteritems():
            db_type, db_region, db_version = parse_rdf_unidb_db_name(database_name)
            if not db_region or not db_version:
                continue
            db_info = DBInfo(database_name, db_region, db_version, db_size)
            database_info_list.append(db_info)

        db_model.close()
        return database_info_list

    @staticmethod
    def get_all_host_database_info():
        all_host_options = read_db_config()
        database_info_list = []
        for host_option in all_host_options:
            if host_option.host == "10.179.1.110":
                print_error("KOR database cannot access. have pass")
                continue

            host_db_info_list = DBStatisticUtils.get_all_database_info(host_option)
            DBInfo.sort_list(host_db_info_list)
            database_info_list += host_db_info_list
        DBInfo.sort_list(database_info_list)
        return database_info_list

    @staticmethod
    def get_tablespace_usage_info(host_option):
        hostname = host_option.host
        username = host_option.username
        password = host_option.password
        port = host_option.port

        db_model = DBModule(host=hostname, username=username, password=password, port=port)
        tablespace_name_location_dic = find_tablespace_name_path_dic(hostname)
        # {name:disk_space_info,...}
        tablespace_size_info_dic = find_tablespace_disk_space_info_dic(hostname)
        tablespace_name_size_dic = db_model.select_tablespace_size_info_dic()
        # collection below info dic, [TablespaceInfo:,...]
        tablespace_info_list = []
        for name, location in tablespace_name_location_dic.iteritems():
            info_dic = tablespace_size_info_dic.get(name)
            db_used_size = tablespace_name_size_dic.get(name)
            tablespace_info = TablespaceInfo.transform_dic_to_info(name, location, info_dic, db_used_size)
            tablespace_info_list.append(tablespace_info)


class DiskSpaceUtil(object):
    @staticmethod
    def get_dir_size(dir_path):
        """unit byte"""
        size = 0l
        for root, dirs, file_names in os.walk(dir_path):
            size += sum([os.path.getsize(os.path.join(root, file_name)) for file_name in file_names])
        return size

    @staticmethod
    def get_dir_usage(dir_path):
        """The usage of this dir_path`s mount path"""
        """Return disk usage associated with path."""
        st = os.statvfs(dir_path)
        free = (st.f_bavail * st.f_frsize)
        total = (st.f_blocks * st.f_frsize)
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        try:
            percent = ret = (float(used) / total) * 100
        except ZeroDivisionError:
            percent = 0

        return Disk_Usage(total, used, free, round(percent, 1))


ConfigComponents = namedtuple("component", "name path regions")
Components = namedtuple("component_size", "name path size pretty_size")


class VendorData(object):
    component_list = []

    @staticmethod
    def load_components_conf():
        if VendorData.component_list:
            return VendorData.component_list

        components_conf_file_path = "vendor_data_components.json"
        with open(components_conf_file_path, "r") as f:
            component_json_list = json.load(f)
            component_list = [ConfigComponents(c["name"], c["path"], c["regions"].split("|"))
                              for c in component_json_list]
            if not component_list:
                print_error("components from comfig should not empty")
                sys.exit(-1)

            return component_list

    def __init__(self, data_path, region):
        self.data_path = data_path
        self.region = region

    def statistic_components(self):
        conf_component_list = VendorData.load_components_conf()
        component_size_list = []
        for conf_component in conf_component_list:
            if self.region not in conf_component.regions:
                continue
            component_path = os.path.join(self.data_path, conf_component.path)
            if not os.path.exists(component_path):
                continue
            size = DiskSpaceUtil.get_dir_size(component_path)
            print conf_component.name, component_path, pretty_size(size)
            component_size = Components(conf_component.name, component_path, size, pretty_size(size))
            component_size_list.append(component_size)

        return component_size_list


def statistic_vendor_data():
    pass


RawDataStatistic = namedtuple("RawDataStatistic", "name region version components size pretty_size")
RAW_DATA_STATISTIC_FILE_NAME = "raw_data_statistic_host.json"


def test_raw_data_statistic():
    base_path = "/var/www/html/data"
    all_data_name = os.listdir(base_path)
    selected_data_name = filter(filter_raw_raw_data_name, all_data_name)

    raw_data_statistic_list = []
    for data_name in selected_data_name:
        data_path = os.path.join(base_path, data_name)
        vendor, region, version = parse_vendor_raw_data_name(data_name)
        vendor_data = VendorData(data_path, region)
        components = vendor_data.statistic_components()
        print components
        size = sum([component.size for component in components])
        raw_data_statistic = RawDataStatistic(data_name, region, version, components, size, pretty_size(size))
        raw_data_statistic_list.append(raw_data_statistic)

    with open(RAW_DATA_STATISTIC_FILE_NAME, "r") as f:
        json.dump(raw_data_statistic_list, f, ensure_ascii=False, indent=4, separators=(",", ":"))


if __name__ == '__main__':
    # VendorData.load_components_conf()

    test_raw_data_statistic()
