import ConfigParser
import os
import re
from rdf.checker.disk_size import DiskSize

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SSH_LOGIN_CONF = os.path.join(ROOT_DIR, 'config/ssh_login.conf')
TABLESPACE_SIZE_CONF = os.path.join(ROOT_DIR, 'config/database_size.conf')
DATABASE_CONFIG = os.path.join(ROOT_DIR, 'config/db_config.conf')

login_info_cf = None


def read_login_config(host):
    """Get the login user and password of this host by SSH from conf file"""
    global login_info_cf
    if not login_info_cf:
        login_info_cf = ConfigParser.ConfigParser()
        login_info_cf.read(SSH_LOGIN_CONF)

    if not login_info_cf:
        return None

    sections = login_info_cf.sections()
    if host not in sections:
        return None

    options = login_info_cf.options(host)
    if "password" in options and "username" in options:
        username = login_info_cf.get(host, "username")
        password = login_info_cf.get(host, "password")
        return username, password

    return None, None


def min_tablespace_size(region):
    """Read config file, read the min size of this region

    unit size MB in config file
    :param region:
    :return:
    DiskSize object
    """
    if not region:
        return None

    cf = ConfigParser.ConfigParser()
    cf.read(TABLESPACE_SIZE_CONF)

    if region in cf.sections():
        # unit = cf.get(region, 'unit')
        size_unit = cf.get(region, "size")
        disk_size = parse_size_unit(size_unit)

        return disk_size


def parse_size_unit(size_unit):
    """Parse str of size_unit to disk size class

    :param size_unit: str like '123MB' size unit
    :return: object:DiskSize
    """
    if not size_unit or not re.findall('\d+', size_unit) or not re.findall('[a-z]', size_unit, re.IGNORECASE)[0]:
        return None

    size = re.findall("\d+", size_unit)[0]
    unit = re.findall("[a-z]+", size_unit, re.IGNORECASE)[0]

    disk_size = DiskSize.format_size_unit(unit=unit, size=int(size))

    return disk_size


def save_region_size(region_size_dic):
    """Save file info of region size

    :param region_size_dic:
        the list of region disk_size(Object): {region:(DiskSize(size: , unit:MB)),...}
    :return:
    """
    with open(TABLESPACE_SIZE_CONF, "w") as f:
        for region, region_disk_size in region_size_dic.iteritems():
            region_disk_size = region_size_dic[region]
            f.write("[%s]\n" % region)
            f.write("size=%s\n" % str(region_disk_size))
        print "write database size info of region success. In file [%s]" % TABLESPACE_SIZE_CONF
        f.close()


class Options:
    def __init__(self):
        pass


def read_db_config():
    return config_options(DATABASE_CONFIG)


def config_options(config_file):
    cf = ConfigParser.ConfigParser()
    cf.read(config_file)
    hosts = cf.sections()
    db_options = []
    for host in hosts:
        host_option = Options()
        setattr(host_option, "host", host)
        for option in cf.options(host):
            setattr(host_option, option, cf.get(host, option))
        db_options.append(host_option)

    return db_options


if __name__ == '__main__':
    # print read_login_config("hqd-ssdpostgis-04.mypna.com")

    print min_tablespace_size("CN")
    # print tablespace_size_config()
    print read_db_config()
