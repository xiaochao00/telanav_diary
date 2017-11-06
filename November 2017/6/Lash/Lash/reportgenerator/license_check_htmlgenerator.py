# -------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# Name:        
# Purpose:     Create html report from license check json file
# Author:      xjhuangfu
# Created:     2017-11-03
# Copyright:   (c) xjhuangfu 2017
# Licence:     <your licence>
# -------------------------------------------------------------------------------

import time
import os
import sys
# sys.path.append("..")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from license_check.process_json import ProcessJson
from case_dump import CaseDump

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LICENSE_CHECK_TEMPLATE = os.path.join(ROOT_DIR, 'html_template', 'license_check.template')
OUTPUT = os.path.join(ROOT_DIR, '..', 'report', 'license_check.html')
TEST_OUTPUT = os.path.join(ROOT_DIR, "testoutput")
LICENSE_CHECK_JSON = "%s/license_check.out" % TEST_OUTPUT
ASSETS = os.path.join(ROOT_DIR, "assets")
CASE_FILE_TYPE_JSON = "json"

TAB = '\t'
# indent tabs for tr
TTR_CNT = 5
# indent tabs for td
TTD_CNT = 6


def create_page(json_dir):
    # copy license check json file there
    ProcessJson.copy_subtree(json_dir, TEST_OUTPUT)
    # dump json
    data_dict = CaseDump(LICENSE_CHECK_JSON, CASE_FILE_TYPE_JSON).dump()

    # copy assets there
    report_dir = os.path.join("../report", ASSETS)
    not os.path.exists(report_dir) and os.makedirs(report_dir)
    ProcessJson.copy_subtree(ASSETS, report_dir)

    with open(LICENSE_CHECK_TEMPLATE, 'r') as fin:
        template = fin.read()
    
    table = ''
    # case table
    line = 1
    for product, is_exist in data_dict.items():
        table += '<tr class="%s %s">\n' % ("even" if (0 == line % 2) else "odd", "pass" if is_exist else "fail")
        table += TAB * TTD_CNT + '<td>%s</td>\n' % line
        table += TAB * TTD_CNT + '<td>%s</td>\n' % product
        table += TAB * TTD_CNT + '<td>%s</td>\n' % is_exist
        table += TAB * TTR_CNT + '</tr>\n'
        line += 1

    date = time.strftime('%Y-%m-%d %H:%M:%S')
    content = template % (table, date)
    with open(OUTPUT, 'w') as fout: 
        fout.write(content)

if __name__ == "__main__":
    create_page("../license_check/output")
