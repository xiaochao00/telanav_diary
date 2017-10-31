import re
import rdf_meta
import rdf_config
import logging
import sys
import os

LEVEL0_DATABASE_NAME_SUFFIX = "_Level0"
CN_REGION_FLAG = 'CN'


def combine_dbname(region, vendor, version, is_level0=False):
    '''
    merge database name by these parameters:
    E.g NT_CN_17Q2_Level0 : vendor_region_version(is_level0 _Level0)
    '''
    if is_empty(region):
        logging.error('combine database name : region can not be None')
        return None
    if is_empty(vendor):
        logging.error('combine database name : vendor can not be None')
        return None
    if is_empty(version):
        logging.error('combine database name : version can not be None')
        return None
    if region == CN_REGION_FLAG:
        database_name = vendor + "_" + region + "_" + version
    else:
        database_name = vendor + "_" + region + version

    if is_level0:
        database_name += LEVEL0_DATABASE_NAME_SUFFIX
    return database_name


def is_empty(s):
    return not s or not s.strip()


def options_automatic(options):
    '''
    edit options by auto rules:
    if database name is None, edit it by parse vendordata(rdf_data)
    if database options and source_list are None, edit it by read json config file

    :param options:
    :return:
    '''
    rdf_data = os.path.basename(options.data)
    # print "rdf_data : ",rdf_data
    vendor, region, version, isLevel0 = rdf_meta.parse_rdf_version(rdf_data)
    if is_empty(options.database):
        database_name = combine_dbname(region, vendor, version, isLevel0)
        if is_empty(database_name):
            logging.error(
                'can not combine daname by parameters: %s %s %s isLevel0:%s' % (region, vendor, version, isLevel0))
            sys.exit(-1)
        options.database = database_name
    if is_empty(options.db_opts) or is_empty(options.source_list):
        db_options, source_list = rdf_config.get_parameters(region, isLevel0)
        if is_empty(db_options) or is_empty(source_list):
            logging.error('db options or source_list from config is not exist. please check')
            sys.exit(-1)
        if is_empty(options.db_opts):
            options.db_opts = db_options
        if is_empty(options.source_list):
            options.source_list = source_list


'''
    for Test
'''


class Options:
    def __init__(self):
        self.data = ""
        self.db_options = ""
        self.source_list = ""
        self.database = None
        self.db_opts = ""


if __name__ == '__main__':
    options = Options()
    options.data = '/var/www/html/data/EU_HERE_16Q4'
    options_automatic(options)
    print 'database name : ', options.database
    print 'db options:', options.db_opts
    print 'db source list: ', options.source_list
