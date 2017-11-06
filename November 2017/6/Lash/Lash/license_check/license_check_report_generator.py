# -------------------------------------------------------------------------------
# Name:        license_check_report_generator
# Purpose: to generator license check report which is to check whether the specific attribute is contained in PBF
#
# Author:      xjhuangfu
#
# Created:     10/31/2017
# Copyright:   (c) TeleNav 2017
# Licence:     <your licence>
# -------------------------------------------------------------------------------

import os
import argparse
import sys
# sys.path.append("..")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from process_json import ProcessJson


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_OUTPUT_DIR = "test_output"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-pbf', dest='pbf', default=os.path.abspath(os.path.join(ROOT_DIR, "..", "st_osm", "output")),
                        help='pbf statistic')
    args = parser.parse_args()
    print "args.pbf= ", args.pbf
    test_output_dir = get_test_output_file(args.pbf)
    process_data(test_output_dir)
    from reportgenerator import license_check_htmlgenerator
    license_check_htmlgenerator.create_page(os.path.join(ROOT_DIR, "output"))


def get_test_output_file(pbf_statistic_dir):
    """
    copy pbf statistic output file to license check test_output path
    :param pbf_statistic_dir: pbf statistic report output path
    :return: test_output_dir: license check test_output path
    """
    # if the pbf statistic report path doesn't exist, exit
    if not os.path.exists(pbf_statistic_dir):
        print "%s doesn't exit!\n" % pbf_statistic_dir
        exit(1)

    test_output_dir = os.path.join(ROOT_DIR, TEST_OUTPUT_DIR)
    # if license check test output path doesn't exist, make it
    not os.path.exists(test_output_dir) and os.makedirs(test_output_dir)
    # copy all test output files from pbf to license check
    ProcessJson.copy_subtree(pbf_statistic_dir, test_output_dir)
    # Utility.copy(pbf_statistic_dir, test_output_dir)
    return test_output_dir


def process_data(test_output_dir):
    process_json = ProcessJson()
    process_json.parse_json(test_output_dir)
    process_json.collect_data()

if __name__ == '__main__':
    main()
