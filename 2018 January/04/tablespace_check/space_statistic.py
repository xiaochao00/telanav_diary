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
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


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


class Component(object):
    def __init__(self, name, path, size, component_pretty_size):
        self.name = name
        self.path = path
        self.size = size
        self.component_pretty_size = component_pretty_size

    def __str__(self):
        return str(self.__dict__)


class VendorData(object):
    conf_component_list = []

    @staticmethod
    def load_components_conf():
        if VendorData.conf_component_list:
            return VendorData.conf_component_list

        components_conf_file_path = os.path.join(ROOT_PATH, "vendor_data_components.json")
        with open(components_conf_file_path, "r") as f:
            component_json_list = json.load(f)
            conf_component_list = [ConfigComponents(c["name"], c["path"], c["regions"].split("|"))
                                   for c in component_json_list]
            if not conf_component_list:
                print_error("components from config should not empty")
                sys.exit(-1)

            return conf_component_list

    def __init__(self, name, region, version, data_path):
        self.name = name
        self.region = region
        self.version = version
        self.data_path = data_path
        self.component_list = []

        self.size = 0
        self.vendor_pretty_size = ""
        self.statistic_init()

    def statistic_init(self):
        component_list = self.statistic_components()
        for component in component_list:
            component_size = component.size
            self.size += component_size

        self.component_list = [component.__dict__ for component in component_list]
        self.vendor_pretty_size = pretty_size(self.size)

    def statistic_components(self):
        VendorData.conf_component_list = VendorData.load_components_conf()
        component_list = []
        for conf_component in self.conf_component_list:
            if self.region not in conf_component.regions:
                continue
            component_path = os.path.join(self.data_path, conf_component.path)
            if not os.path.exists(component_path):
                continue
            size = DiskSpaceUtil.get_dir_size(component_path)
            print conf_component.name, component_path, pretty_size(size)
            component = Component(conf_component.name, component_path, size, pretty_size(size))
            component_list.append(component)

        return component_list

    @staticmethod
    def list2dic(vendor_data_list):
        dic_list = [vendor_data.__dict__ for vendor_data in vendor_data_list]
        return dic_list


def statistic_vendor_data(base_path, result_file):
    all_data_name = os.listdir(base_path)
    selected_data_name = filter(filter_raw_raw_data_name, all_data_name)

    vendor_data_list = []
    for data_name in selected_data_name:
        data_path = os.path.join(base_path, data_name)
        vendor, region, version = parse_vendor_raw_data_name(data_name)
        vendor_data = VendorData(data_name, region, version, data_path)

        vendor_data_list.append(vendor_data)

    with open(result_file, "w") as f:
        json.dump(VendorData.list2dic(vendor_data_list), f, ensure_ascii=False, indent=4, separators=(",", ":"))


RAW_DATA_STATISTIC_FILE_NAME = "raw_data_statistic_{host}.json"


def test_region():
    region = "CN_Level0"
    VendorData("CN_Level0_17Q1", "CN_Level0", "17Q1", "")


def test_raw_data_statistic():
    host_name = "Other"
    "D:\\test_temp\\test_rdf_data "
    base_path = "/var/www/html/data"
    result_file = RAW_DATA_STATISTIC_FILE_NAME.format(host=host_name)
    statistic_vendor_data(base_path, result_file)


if __name__ == '__main__':
    # VendorData.load_components_conf()
    # test_region()
    test_raw_data_statistic()
