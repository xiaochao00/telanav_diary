import sys
import socket
import json

from rdf_meta import parse_rdf_db


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

    else:
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
    vendor, region, version, level0 = parse_rdf_db(database_name)
    if database_name.find("TUR") != -1:
        region = "TUR"
    if level0:
        region = region + "_Level0"
    return region, version
