import os
import sys
import optparse
import shutil
from DBModule import DBModule
from util.save_file import XLSSave
from host_config.config_reader import read_db_config
from tablespace_util import find_tablespace_disk_space_info_dic, find_tablespace_name_path_dic
from util.common_utils import pretty_size, filter_database_name, parse_rdf_unidb_db_name, print_standout, print_error, json_print

TABLESPACE_INFO_SAVE_FILENAME = "tablespace_info_collections.xls"
DATABASE_INFO_SAVE_FILENAME = "database_info_collections.xls"
# JS file name and variable name
JS_TABLESPACE_CONF = {"var_name": "tablespaces_info", "filename": "tablespaces_statistic.js"}
JS_DATABASE_CONF = {"var_name": "dbs_info", "filename": "dbs_statistic.js"}
# js source directory
JS_SAVE_PATH = "spatial_statistic_html"
JS_SRC_PATH = os.path.join("statistic", JS_SAVE_PATH)


class DBInfo(object):
    """Database information class"""

    def __init__(self, database_name, region, version, size):
        self.database_name = database_name
        self.region = region
        self.version = version
        self.size = size


class TablespaceInfo:
    """Tablespace information class"""
    INFO_HEADERS = ("hostname\ttablespace_name\tmount_on\tlocation\ttotal_available_size\tdb_used_size\t"
                    "dir_used_size\tleft_size".split("\t"))

    def __init__(self, tablespace_name, location, mount_on, total_available_size, db_used_size,
                 dir_used_size, left_size):
        self.tablespace_name = tablespace_name
        self.location = location
        self.mount_on = mount_on
        self.total_available_size = total_available_size
        self.db_used_size = db_used_size
        self.left_size = left_size
        self.dir_used_size = dir_used_size

    @staticmethod
    def transform_dic_to_info(tablespace_name, location, info_dic, db_used_size):
        if info_dic:
            mount_on = info_dic['MountedOn']
            # total_size = info_dic['TotalSize']
            left_size = info_dic['Available']
            dir_used_size = info_dic["Used"]
        else:
            mount_on = ""
            left_size = dir_used_size = 0
        total_available_size = left_size + dir_used_size
        return TablespaceInfo(tablespace_name, location, mount_on, total_available_size,
                              db_used_size, dir_used_size, left_size)

    def to_array(self):
        format_total_available_size = pretty_size(self.total_available_size)
        format_db_used_size = pretty_size(self.db_used_size)
        format_dir_used_size = pretty_size(self.dir_used_size)
        format_left_size = pretty_size(self.left_size)

        return [self.tablespace_name, self.mount_on, self.location, format_total_available_size,
                format_db_used_size, format_dir_used_size, format_left_size]


class FormatTablespaceInfo:
    """Merge the tablespaces in same mount_on path of this host

    1. do statistic
    2. format data line
    db_used_size mean: this tablespace`s all databases size
    """
    FORMAT_INFO_HEADERS = ("hostname	mount_on	db_total_used   other_used_size left_size	"
                           "total_available_size    tablespace_name	location	db_used_size".split())

    def __init__(self, hostname, mount_on, tablespace_info_list):
        self.hostname = hostname
        self.mount_on = mount_on
        # the tablespace list in this host and mount on,
        self.tablespace_info_list = tablespace_info_list

        self.total_available_size = 0
        self.other_used_size = 0
        self.db_total_used_size = 0
        self.left_size = 0

    def do_statistic(self):
        """There are many tablespaces in this mount_on path of this host,

        statistic these tablespaces size info
        :return:
        """
        total_available_size_set = set([])
        left_size_set = set([])
        dir_used_size_set = set([])
        # check if the tablespace info list have the same left size & dir_used_size & total_available_size
        # and statistic all db used size
        for tablespace_info in self.tablespace_info_list:
            total_available_size = tablespace_info.total_available_size
            left_size = tablespace_info.left_size
            dir_used_size = tablespace_info.dir_used_size

            total_available_size_set.add(total_available_size)
            left_size_set.add(left_size)
            dir_used_size_set.add(dir_used_size)
            self.db_total_used_size += long(tablespace_info.db_used_size)

        if len(total_available_size_set) > 1 or len(left_size_set) > 1 or len(dir_used_size_set) > 1:
            temp_set = set([])
            for size in total_available_size_set:
                temp_set.add(pretty_size(size))
            if len(temp_set) > 1:
                print_error("error in statistic tablespace info merge. there have not unique size info in size "
                            "info list")
                sys.exit(-1)

        self.total_available_size = total_available_size_set.pop()
        self.left_size = left_size_set.pop()
        self.other_used_size = dir_used_size_set.pop() - self.db_total_used_size
        if self.other_used_size < 0:
            self.other_used_size = 0

    def to_data_list(self):
        """After do_statistic()

        generator data line for table show
        :return:
        """
        data_list = []
        for i in range(len(self.tablespace_info_list)):
            tablespace_info = self.tablespace_info_list[i]

            tablespace_name = tablespace_info.tablespace_name
            location = tablespace_info.location
            format_db_used_size = pretty_size(tablespace_info.db_used_size)

            if i == 0:
                format_total_size = pretty_size(self.total_available_size)
                format_other_used_size = pretty_size(self.other_used_size)
                format_db_total_used_size = pretty_size(self.db_total_used_size)
                format_left_size = pretty_size(self.left_size)

                data = [self.hostname, self.mount_on, format_db_total_used_size, format_other_used_size,
                        format_left_size, format_total_size, tablespace_name, location, format_db_used_size]
            else:
                data = ['', '', '', '', '', '', tablespace_name, location, format_db_used_size]
            data_list.append(data)
        return data_list


def host_db_info(host_option):
    """Get all tablespaces info and databases info in this host

    size unit is B
    :param host_option:
    :return:[TablespaceInfo, ],[DBInfo, ]
    """
    # 1.prepared host parameters
    hostname = host_option.host
    username = host_option.username
    password = host_option.password
    port = host_option.port

    db_model = DBModule(host=hostname, username=username, password=password, port=port)

    # 1.tablespace info
    # {name:location_path,...}
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
    # 2. db info
    all_database_name_size_dic = db_model.select_all_db_size_dic()
    selected_database_name_list = filter(filter_database_name, all_database_name_size_dic.keys())
    selected_database_name_size_dic = {}
    for d_name, size in all_database_name_size_dic.iteritems():
        if d_name in selected_database_name_list:
            selected_database_name_size_dic[d_name] = size

    database_info_list = []
    for database_name, db_size in selected_database_name_size_dic.iteritems():
        db_type, db_region, db_version = parse_rdf_unidb_db_name(database_name)
        if not db_region or not db_version:
            continue
        db_info = DBInfo(database_name, db_region, db_version, db_size)
        database_info_list.append(db_info)

    db_model.close()
    return tablespace_info_list, database_info_list


def tablespace_info_save(save_path, host_tablespace_info_dic):
    """Save tablespace information"""
    # 1. filename and head of table
    filename = os.path.join(save_path, TABLESPACE_INFO_SAVE_FILENAME)
    # header_list = TablespaceInfo.INFO_HEADERS
    header_list = FormatTablespaceInfo.FORMAT_INFO_HEADERS
    # 2.transform information to data lines of table
    data_list = transform_host_tablespace_info_dic(host_tablespace_info_dic)
    # 3.save data lines
    XLSSave.save_xls(data_list, header_list, filename, "tablespace_info")
    data_list_to_json(header_list, data_list, JS_TABLESPACE_CONF, save_path)


def database_info_save(save_path, host_database_info_dic):
    """Save database information"""
    # 1.filename and head of table
    filename = os.path.join(save_path, DATABASE_INFO_SAVE_FILENAME)
    header_list = "hostname\tregion\tversion\tdatabase_name\tsize".split("\t")
    # 2.transform information to data lines of table
    data_list = []
    for hostname, database_info_list in host_database_info_dic.iteritems():
        for database_info in database_info_list:
            database_name = database_info.database_name
            region = database_info.region
            version = database_info.version
            size = database_info.size
            format_size = "%s" % pretty_size(size)
            data_list.append([hostname, region, version, database_name, format_size])
    # 3.sorted and save data lines
    data_list = sorted(data_list, key=lambda d: d[2], reverse=False)
    data_list = sorted(data_list, key=lambda d: d[1], reverse=False)
    data_list = sorted(data_list, key=lambda d: d[3][:6], reverse=False)

    XLSSave.save_xls(data_list, header_list, filename, "database_info")
    data_list_to_json(header_list, data_list, JS_DATABASE_CONF, save_path)


def transform_host_tablespace_info_dic(host_tablespace_info_dic):
    """Transform all tablespace info list in host to data line list
    Merge cell
    1. transform to structure {hostname:{mount_on:[TablespaceInfo,...]}}
    2. transform to format tablespace info list
    3. transform to data line list
    :param host_tablespace_info_dic: {hostname:[TablespaceInfo, ],}
    :return:  data line list [data,...]
    """
    host_format_info = {}
    for hostname, tablespace_info_list in host_tablespace_info_dic.iteritems():
        host_format_info[hostname] = {}
        for tablespace_info in tablespace_info_list:
            if tablespace_info.mount_on not in host_format_info[hostname]:
                host_format_info[hostname][tablespace_info.mount_on] = []
            host_format_info[hostname][tablespace_info.mount_on].append(tablespace_info)
    #
    format_tablespace_info_list = []
    for hostname, mount_tablespace_info_list_dic in host_format_info.iteritems():
        for mount_on, tablespace_info_list in mount_tablespace_info_list_dic.iteritems():
            format_tablespace_info_list.append(FormatTablespaceInfo(hostname, mount_on, tablespace_info_list))
    #
    format_tablespace_info_list.sort(key=lambda d: d.hostname)

    data_list = []
    for format_tablespace_info in format_tablespace_info_list:
        format_tablespace_info.do_statistic()
        data_list += format_tablespace_info.to_data_list()

    return data_list


def data_list_to_json(header_list, data_list, save_conf, save_path):
    data_json_list = []
    from collections import OrderedDict
    for data in data_list:
        data_json = OrderedDict({})
        for i in range(len(header_list)):
            name = header_list[i]
            value = data[i]
            data_json[name] = value
        data_json_list.append(data_json)

    js_content = "var %s = %s" % (save_conf["var_name"], json_print(data_json_list))
    js_file_path = os.path.join(save_path, save_conf["filename"])
    with open(js_file_path, 'w') as f:
        f.write(js_content)
        f.close()
        print_standout("write js file[%s] finish." % js_file_path)


def collection_tablespace(save_path):
    """Collection tablespace information and show"""
    # 1. collection information:Tablespace and Database information
    # [Options(host: ,username: ,password: ,port: ),...]
    host_options = read_db_config()
    host_tablespace_info_dic = {}
    host_database_info_dic = {}
    for host_option in host_options:
        if host_option.host=="10.179.1.110":
            print_error("KOR database cannot access. have pass")
            continue
        hostname = host_option.host
        host_tablespace_info_dic[hostname], host_database_info_dic[hostname] = host_db_info(host_option)
    # 2.prepared js resource directory
    data_save_dir = os.path.join(save_path, JS_SAVE_PATH)
    if os.path.exists(data_save_dir):
        shutil.rmtree(data_save_dir)
    js_src_path = os.path.join(os.path.dirname(__file__), JS_SRC_PATH)
    shutil.copytree(js_src_path, data_save_dir)
    # 3.transform and save data
    tablespace_info_save(data_save_dir, host_tablespace_info_dic)
    database_info_save(data_save_dir, host_database_info_dic)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-O', '--output-directory', help='output directory', dest='output')

    options, args = parser.parse_args()
    if not options.output:
        print_error(parser.print_help())
        sys.exit(-1)

    collection_tablespace(options.output)


if __name__ == '__main__':
    main()
