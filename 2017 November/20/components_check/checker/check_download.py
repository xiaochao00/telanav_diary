import os
import sys
import getopt
import optparse
import ConfigParser
from components_check import ExtendChecker, CheckStateInfo

ROOT_PATH = os.path.dirname(__file__)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "r:q:p")
    except getopt.GetoptError:
        print ("Usage: -r <region> -q <quarter name> -p <project name>\n")
        print ("Example: python2.7 check_download.py -r EU -q 17Q2 -p auto")
        sys.exit(2)

    if len(opts) != 3:
        print ("Usage: -r <region> -q <quarter name> -p <project name>\n")
        print ("Example: python2.7 check_download.py -r EU -q 17Q2 -p dcas")
        sys.exit(2)
    # 1. parse parameters
    parser = optparse.OptionParser()
    parser.add_option('-r', '--region', help='region', dest='region')
    parser.add_option('-q', '--quarter', help='quarter name', dest='quarter')
    parser.add_option('-p', '--project', help='project name', dest='project', default='auto')
    options, args = parser.parse_args()
    # 2. split region
    regions = options.region.split('|')
    data_base_path = Util.get_data_base_path(options.project)
    for region in regions:
        region_path = Util.generate_region_path(region, options.quarter)
        region_full_path = os.path.join(data_base_path, region_path)
        # 3. check signal region data directory structure
        check_state_info = ExtendChecker.check_single_region(region_full_path)
        # 4. save report
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
    main(sys.argv[1:])
