import sys
import re
import socket
import json, pprint


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


def region_version(str):
    # HERE_ANZ17Q2
    m1 = re.match(".*_(.+\d{2}Q[1-4]).*", str, re.IGNORECASE)
    # NT_CN_15Q3
    m2 = re.match(".*_(.+_\d{2}Q[1-4]).*", str, re.IGNORECASE)
    if not m1 and not m2:
        return None, None

    m = m1 if m1 else m2
    region = m.group(1)[:-4].strip("_")
    version = m.group(1)[-4:]
    #
    if str.find("TUR") != -1:
        region = "TUR"
    if str.lower().find("level0") != -1:
        region = region + "_Level0"
    return region, version
