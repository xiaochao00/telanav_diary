import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from rdf.checker.config_reader import read_db_config
from rdf.checker.db_model import DBModel
from rdf.checker.remote_model import RemoteModel
from rdf.common_tool.common_utils import region_version, print_error, print_standout, is_localhost, json_print
from rdf.common_tool.disk_utils import pretty_size
from rdf.common_tool.command_utils import execute_cmd, parse_size_info_response_lines
import xlwt


def collection_tablespace():
    host_options = read_db_config()
    host_tablespace_info_dic = {}
    host_database_info_dic = {}
    for host_option in host_options:
        hostname = host_option.host
        if hostname == '10.179.1.110':
            print_error("KOR can not access. pass it")
            continue
        host_tablespace_info_dic[hostname], host_database_info_dic[hostname] = host_db_info(host_option)

    # save_tablespace_info(host_tablespace_info_dic)
    # save_database_info(host_database_info_dic)
    tablespace_info_save(host_tablespace_info_dic)
    database_info_save(host_database_info_dic)


class DBInfo:
    def __init__(self, database_name, region, version, size):
        self.database_name = database_name
        self.region = region
        self.version = version
        self.size = size


class TablespaceInfo:
    INFO_HEADERS = "hostname\ttablespace_name\tlocation\tmount_on\ttotal_size\tused_size\tleft_size".split("\t")

    def __init__(self, tablespace_name, location, mount_on, total_size, used_size, left_size):
        self.tablespace_name = tablespace_name
        self.location = location
        self.mount_on = mount_on
        self.total_size = total_size
        self.used_size = used_size
        self.left_size = left_size
        # total_size != used_size + left_size,

    def to_array(self):
        format_total_size = pretty_size(self.total_size)
        format_used_size = pretty_size(self.used_size)
        format_left_size = pretty_size(self.left_size)

        return [self.tablespace_name, self.location, self.mount_on, format_total_size, format_used_size, format_left_size]


def host_db_info(host_option):
    """
    size unit is B
    :param host_option:
    :return:
    """
    hostname = host_option.host
    username = host_option.username
    password = host_option.password
    port = host_option.port

    db_model = DBModel(host=hostname, username=username, password=password, port=port)

    # 1.tablespace info
    tablespace_name_location_dic = db_model.get_all_tablespace()
    tablespace_name_size_dic = db_model.get_tablespace_info()
    tablespace_size_info_dic = get_tablespace_size_info(hostname, tablespace_name_location_dic)
    tablespace_info_list = []
    for name, location in tablespace_name_location_dic.iteritems():
        size_info = tablespace_size_info_dic.get(name)
        if size_info:
            mount_on = size_info['MountedOn']
            total_size = size_info['TotalSize']
            left_size = size_info['Available']
        else:
            mount_on = total_size = left_size = ""

        used_size = tablespace_name_size_dic[name]
        tablespace_info = TablespaceInfo(name, location, mount_on, total_size, used_size, left_size)
        tablespace_info_list.append(tablespace_info)
    # 2. db info
    database_name_list = db_model.all_dbs()
    selected_database_name_list = filter(filtrate_database_name, database_name_list)
    # [(database_name, size), ]
    database_name_size_dic = db_model.size_db_list(selected_database_name_list)
    database_info_list = []
    for database_name, size in database_name_size_dic.iteritems():
        region, version = region_version(database_name)
        if not region or not version:
            continue
        db_info = DBInfo(database_name, region, version, size)
        database_info_list.append(db_info)
    db_model.close()
    return tablespace_info_list, database_info_list


def filtrate_database_name(database_name):
    if database_name.upper().startswith("HERE") or database_name.upper().startswith("UNIDB") or database_name.upper().startswith("NT"):
        if database_name.upper().find("TEST") != -1:
            return False
        return True
    return False


def get_tablespace_size_info(host, tablespace_path_dic):
    """

    :param host:
    :param tablespace_path_list:
    :return:
    """
    if not tablespace_path_dic:
        print_error("Error: all tablespaces can not be None. check need")
        return None
    if host == '10.179.1.110':
        print_error("kor data no right to access. pass it .")
        return None

    tablespace_size_info_dic = {}
    if is_localhost(host):
        for tablespace_name, tablespace_location in tablespace_path_dic.iteritems():
            cmd = 'sudo df %s' % tablespace_location
            size_info_lines = execute_cmd(cmd)
            size_info = parse_size_info_response_lines(size_info_lines)
            tablespace_size_info_dic[tablespace_name] = size_info

    else:
        remote_model = RemoteModel(host)
        for tablespace_name, tablespace_location in tablespace_path_dic.iteritems():
            cmd = 'sudo df %s' % tablespace_location
            size_info_lines = remote_model.execute_command(cmd)
            size_info = parse_size_info_response_lines(size_info_lines)
            tablespace_size_info_dic[tablespace_name] = size_info

        remote_model.close()
    print_standout("Info: all tablespace in host[%s] size space info are :" % host)
    json_print(tablespace_size_info_dic)

    return tablespace_size_info_dic


def tablespace_info_save(host_tablespace_info_dic):
    filename = "tablespace_info_collections.xls"
    header_list = TablespaceInfo.INFO_HEADERS
    data_list = []
    for hostname, tablespace_info_list in host_tablespace_info_dic.iteritems():
        for tablespace_info in tablespace_info_list:
            data = [hostname]
            data = data + tablespace_info.to_array()
            data_list.append(data)
    XLSSave.save_xls(data_list, header_list, filename, "tablespace_info")
    # save_csv(data_list, header_list, filename)


def database_info_save(host_database_info_dic):
    filename = "database_info_collections.xls"
    header_list = "hostname\tregion\tversion\tdatabase_name\tsize".split("\t")
    data_list = []
    for hostname, database_info_list in host_database_info_dic.iteritems():
        for database_info in database_info_list:
            database_name = database_info.database_name
            region = database_info.region
            version = database_info.version
            size = database_info.size
            format_size = "%s" % pretty_size(size)
            data_list.append([hostname, region, version, database_name, format_size])
    # save
    #
    data_list = sorted(data_list, key=lambda d: d[2], reverse=False)
    data_list = sorted(data_list, key=lambda d: d[1], reverse=False)
    data_list = sorted(data_list, key=lambda d: d[3][:6], reverse=False)
    # save_csv(data_list, header_list, filename)
    XLSSave.save_xls(data_list, header_list, filename, "database_info")


class CSVSave:
    def __init__(self):
        pass

    @staticmethod
    def save_csv(data_list, header_list, filename):
        with open(filename, 'w') as f:
            f.write("\t".join(header_list) + "\n")
            for data in data_list:
                f.write("\t".join(data) + "\n")
            f.close()
            print_standout("write to [%s] finished." % filename)


class XLSSave:
    def __init__(self):
        pass

    @staticmethod
    def save_xls(data_list, header_list, filename, sheet_name=u'sheet1'):
        f = xlwt.Workbook()
        sheet1 = f.add_sheet(sheet_name, cell_overwrite_ok=True)
        i, j = 0, 0
        for j in range(len(header_list)):
            sheet1.write(i, j, header_list[j])
        i = 1
        for row in data_list:
            for j in range(len(row)):
                sheet1.write(i, j, row[j])
            i += 1

        f.save(filename)


if __name__ == '__main__':
    collection_tablespace()
