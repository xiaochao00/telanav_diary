import os
import ConfigParser

SSH_LOGIN_CONF = os.path.join(os.path.dirname(__file__), "ssh_login.conf")
DATABASE_CONFIG = os.path.join(os.path.dirname(__file__), "db_config.conf")

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


class Options:
    def __init__(self):
        pass


def read_db_config():
    """[{host: ,username: ,password: ,port: },...]"""
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
    # print tablespace_size_config()
    print read_db_config()
