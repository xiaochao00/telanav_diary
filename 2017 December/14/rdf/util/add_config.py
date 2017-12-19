import os
import sys
import json
from rdf_meta import parse_rdf_version

"""
That config defines the countries in HERE data that should be moved from one region to another region. for example:
 in HERE data, Panama belongs to North American, but Program ask putting Panama into South American product.
"""


class AddConfig(object):
    ADD_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/add_config.json')

    KEY_ADD_COUNTRIES = 'add_countries'
    KEY_ADD_REGION = 'add_region'

    def __init__(self):
        self.init = False
        self.configs = None

    def load(self):
        if not os.path.exists(AddConfig.ADD_CONFIG):
            sys.stderr.write('Error: %s not exists\n' % AddConfig.ADD_CONFIG)
            return False

        with open(AddConfig.ADD_CONFIG) as f:
            self.configs = json.load(f)
            return True

        return False

    def get_add_countries(self, region):
        if not self.configs:
            return None

        region_configs = self.configs.get(region)
        if not region_configs:
            return None

        return region_configs.get(AddConfig.KEY_ADD_COUNTRIES)

    def get_add_data_path(self, data_path):
        vendor, region, version, is_level0 = parse_rdf_version(os.path.basename(data_path))
        if not vendor or not region:
            sys.stderr.write('Error: error to parse rdf data version %s\n' % data_path)
            return None

        add_region = self._get_add_region(region)
        add_data = '_'.join([add_region, vendor, version]).upper()
        add_data_path = os.path.join(os.path.dirname(data_path), add_data)

        return add_data_path

    def _get_add_region(self, region):
        if not self.configs:
            return None

        region_configs = self.configs.get(region)
        if not region_configs:
            return None

        return region_configs.get(AddConfig.KEY_ADD_REGION)


_config = AddConfig()
if not _config.load():
    raise Exception('Load config/add_config.json failure')


def get_add_countries(region):
    return _config.get_add_countries(region)


def get_add_data_path(data_path):
    return _config.get_add_data_path(data_path)


def main():
    print get_add_countries('SA')
    print get_add_countries('NA')

    print get_add_data_path('/var/www/html/data/SA_HERE_17Q3')


if __name__ == '__main__':
    main()
