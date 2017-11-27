import os
import sys
import getopt
import optparse
import ConfigParser
from components_check import ExtendChecker, CheckStateInfo

ROOT_PATH = os.path.dirname(__file__)


def main():
    # 1. parse parameters
    parser = optparse.OptionParser()
    parser.add_option('-r', '--region', help='region', dest='region')
    parser.add_option('-q', '--quarter', help='quarter name', dest='quarter')
    parser.add_option('-p', '--project', help='project name', dest='project', default='auto')
    options, args = parser.parse_args()
    # 2.check
    if not options.region or not options.quarter:
        parser.print_help()
        sys.exit(-1)
    # 3. split region
    regions = options.region.split('|')
    data_base_path = Util.get_data_base_path(options.project)
    for region in regions:
        region_path = Util.generate_region_path(region, options.quarter)
        region_full_path = os.path.join(data_base_path, region_path)
        # 4. check signal region data directory structure
        check_state_info = ExtendChecker.check_single_region(region_full_path)
        # 5. save report
        ExtendChecker.generate_report([check_state_info], region_full_path)


class Util(object):
    """Util class

    1. generate_region_path : base on rule, generate region directory name
    2. get_data_base_path : get the data base directory /var/www/html/data
    """

    @staticmethod
    def generate_region_path(region, quarter):
        return "%s_HERE_%s" % (region, quarter)

    @staticmethod
    def get_data_base_path(project):
        config_file = os.path.join(os.path.dirname(ROOT_PATH), "config/%s_path.txt" % project)
        conf = ConfigParser.ConfigParser()
        conf.read(config_file)
        data_path = conf.get("ADD", "data_path")

        return data_path


if __name__ == '__main__':
    main()
