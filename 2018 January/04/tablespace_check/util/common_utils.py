import sys
import socket
import json
import re

LEVEL0_FLAG = "LEVEL0"
LEVEL0_SUFFIX = "Level0"

DB_NAME_PREFIX_HERE = "HERE"
DB_NAME_PREFIX_CN = "NT"
DB_NAME_PREFIX_UNIDB = "UNIDB"


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
        print_standout(' address %s is localhost ' % host)
        return True

    print_error('%s is not local address' % host)
    return False


def print_standout(info):
    """
    print information to standout
    :param info:
    :return:
    """
    sys.stdout.write("Info: %s" % info)
    sys.stdout.write("\n")
    sys.stdout.flush()


def json_print(info):
    data_str = json.dumps(info)
    print data_str
    return data_str


def print_error(err):
    """

    :param err: information of error
    :return:
    """
    sys.stderr.write("Error: %s" % err)
    sys.stderr.write("\n")
    sys.stderr.flush()


def region_version(database_name):
    """Parse database name, return region and version"""
    vendor, region, version = parse_rdf_unidb_db_name(database_name)
    if database_name.find("TUR") != -1:
        region = "TUR"
    return region, version


def parse_rdf_unidb_db_name(rdf_database_name):
    """Parse rdf and unidb database BD anme
    HERE_MEA17Q3 : HERE,MEA,17Q3,False
    NT_CN_17Q3
    Unidb_NT_CN_
    Unidb_HERE_MEA17
    :param rdf_database_name:
    :return:db_type,region,version,is_level0
    """
    p = r"([A-Z0-9_]+_)([A-Z]+)_?(\d+Q\d)(.*)"
    m = re.match(p, rdf_database_name, re.IGNORECASE)
    if not m:
        return None, None, None
    db_type = m.group(1).strip("_")
    db_region = m.group(2)
    db_version = m.group(3)
    db_is_level0 = (m.group(4).upper().strip("_").startswith(LEVEL0_FLAG))
    if db_is_level0:
        db_region += "_" + LEVEL0_SUFFIX
    if rdf_database_name.find("TUR") != -1:
        db_region = "TUR"
    return db_type, db_region, db_version


def parse_vendor_raw_data_name(data_name):
    """Parse raw data name
    region_vendor_17Q2, CN_NT_17Q1_Level0"""
    p = r"([A-Z]+)_([A-Z0-9_]+_)_?(\d+Q\d)(.*)"
    m = re.match(p, data_name, re.IGNORECASE)
    if not m:
        return None, None, None
    db_region = m.group(1)
    db_vendor = m.group(2).strip("_")
    db_version = m.group(3)
    db_is_level0 = (m.group(4).upper().strip("_").startswith(LEVEL0_FLAG))
    if db_is_level0:
        db_region += "_" + LEVEL0_SUFFIX
    if data_name.find("TUR") != -1:
        db_region = "TUR"
    return db_vendor, db_region, db_version


def pretty_size(size_b):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string

    :param size_b:
    :return:
    """
    B = float(size_b)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B / GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B / TB)


def filter_database_name(database_name):
    if database_name.upper().find("TEST") != -1 or database_name.upper().find("WORLDMAP") != -1:
        return False

    if (database_name.upper().startswith(DB_NAME_PREFIX_CN) or database_name.upper().startswith(DB_NAME_PREFIX_HERE) or
            database_name.upper().startswith(DB_NAME_PREFIX_UNIDB)):
        return True

    return False


def filter_raw_raw_data_name(data_name):
    vendor, region, version = parse_vendor_raw_data_name(data_name)
    if not vendor or not region or not version:
        return False
    for filter_str in ["TEST", "BAK", "V0", "PAN", "ADAS", "OLD", "ARP", "LOGAN", "WORLDMAP", "REVA",
                       "SAMPLAE", "V2", "BEACONS"]:
        if filter_str in data_name.upper():
            return False

    return True


if __name__ == '__main__':
    unidb_db_name = "UniDB_NT_CN_15Q3_1.0.0-gen3.421243-20160411222319-RC"
    rdf_db_name = "HERE"
    print parse_rdf_unidb_db_name("NT_CN_17Q2_Level0")
    pass
    print filter_database_name("UniDB_HERE_WORLDMAP17Q1_1.0.0.504326-20171013044235-RC-TURKEY")
    print parse_vendor_raw_data_name("CN_NT_17Q1")
    print parse_vendor_raw_data_name("CN_NT_17Q2_Level0")
    print parse_vendor_raw_data_name("EU_HERE_17Q1")
    print filter_raw_raw_data_name("CN_NT_14Q3_old")
