import os
import json
import logging


COMPILATION_OPTIONS_KEYLIST_KEY = 'key_list'
COMPILATION_OPTIONS_DATABASE_OPERATIONS_KEY = 'database_operations'
LEVEL0_SUFFIX = 'Level0'

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
COMPILATION_OPTIONS_FILE = os.path.join(ROOT_DIR, 'config/compilation_options.json')


def get_parameters(region, is_level0=False):
    '''
    load database options and source list parameters by region
    through json config file
    '''
    if not region or not region.strip():
        logging.error('region can not be None')
        return None, None
    search_region = region
    if is_level0:
        search_region += " " + LEVEL0_SUFFIX  # here have one space

    with open(COMPILATION_OPTIONS_FILE, 'r') as f:
        data = json.load(f)

        if not data.has_key(search_region):
            logging.error("parameters config have no parameters of  this region: %s" % search_region)
            return None,None
        parameters = data[search_region]
        db_options = parameters[COMPILATION_OPTIONS_DATABASE_OPERATIONS_KEY].strip()
        source_list = parameters[COMPILATION_OPTIONS_KEYLIST_KEY].strip()
        return db_options, source_list
    logging.error('region:%s can not find from config file %s . please have a check' % (search_region, COMPILATION_OPTIONS_FILE))
    return None, None


if __name__ == '__main__':
    region = 'NA'
    is_level0 = True
    db_options, source_list = get_parameters(region, is_level0)
    print '%s db_options:%s,source_list:%s' % (region, db_options, source_list)
