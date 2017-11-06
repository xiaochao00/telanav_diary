# Name:        process json
# Purpose: process pbf statistic report json file and generate license check report json file
#
# Author:      xjhuangfu
#
# Created:     10/31/2017
# Copyright:   (c) TeleNav 2017
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import os
import shutil
import sys
import xml.dom.minidom
import json
import re
import stat
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
print os.path.dirname(os.path.dirname(__file__))
from st_osm.configreader import ConfigReader
# from reportgenerator.case_dump import CaseDump


OUT_SUFFIX = ".out"
CASE_FILE_TYPE_JSON = "json"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RULE_XML = "config/rule.xml"
CONFIGURE_XML = "config/configure.xml"
# the dict dum from json file
# formation: RESULT_DICT[table][type][key] = sub_value
# while the conception of table, type, key is the same as configure.xml
RESULT_DICT = {}


class ProcessJson:
    def __init__(self):
        pass

    def parse_json(self, test_output_dir):
        """
        make RESULT_DICT from statistic report json file
        :param test_output_dir:
        :return:
        """
        # get table list
        table_list = list(set(map(lambda px: px.endswith(OUT_SUFFIX) and os.path.splitext(px)[0] or None,
                                  os.listdir(test_output_dir))))

        # get types from config file
        config = ConfigReader()
        config.readerConfigure(CONFIGURE_XML)
        types = list(set(reduce(lambda x, y: x + y, map(lambda px: config.itemslist[px].keys(), config.itemslist))))
        # make RESULT_DICT from statistic report json file
        map(lambda tb: self.__generate_dict(test_output_dir, types, tb), table_list)

        global RESULT_DICT
        return RESULT_DICT

    def collect_data(self, output_dir=os.path.join(ROOT_DIR, "output", "license_check.out")):
        """
        this program is to generate license check result as json file.
        the rules of each product that should be checked are written in ./config/rule.xml,
        and the pbf data is stored in a dict called RESULT_DICT which is built before in function parse_json.
        we compare the pbf data with the rules use regular expression.
        :param output_dir: the directory of the result formed in json file
        :return:
        """
        # read rules from RULE_XML
        _dom = xml.dom.minidom.parse(RULE_XML)
        _root = _dom.documentElement
        if _root:
            items_node = _root.getElementsByTagName("items")
            if items_node:
                # load rule.xml into item_list
                item_list = items_node[0].getElementsByTagName("item")
                license_check_result_dict = {}
                # iterate to check every item
                for _item in item_list:
                    product = _item.getAttribute('product')
                    # the product is exit if there are one or more conditions fit
                    if product in license_check_result_dict.keys():
                        license_check_result_dict[product] = \
                            license_check_result_dict[product] or self.check_product(_item)
                    else:
                        license_check_result_dict[product] = self.check_product(_item)
                # write dict to json file
                ProcessJson.output_json_file(license_check_result_dict, output_dir)

    def check_product(self, xml_item):
        """
        check whether the current product is exit depend on the rules
        :param xml_item: the current item
        :return:
        """
        _table = xml_item.getAttribute('table')
        _item = xml_item.getAttribute('item')
        _condition = xml_item.getAttribute('condition')
        _sub_value = xml_item.getAttribute('subvalue')

        # always true
        if "true" == _table and "true" == _item and "true" == _condition:
            return True

        # key restriction
        if "key" == _item and not _sub_value:
            for tb in _table.split("/"):
                # get keys list from RESULT_DICT
                keys_list = reduce(lambda x, y: x + y, map(lambda px: px.keys(), RESULT_DICT[tb].values()))
                for k in keys_list:
                    if re.match(_condition, k):
                        return True

        # key and sub_value restriction
        if "key" == _item and _sub_value:
            for tb in _table.split("/"):
                # get key_sub_value dict from RESULT_DICT
                key_sub_value_dict = dict(
                    reduce(lambda x, y: x + y, map(lambda x: x.items(), RESULT_DICT[tb].values())))
                for k, v in key_sub_value_dict.items():
                    if re.match(_condition, k) and re.match(_sub_value, v):
                        return True

        # type restriction
        if "type" == _item:
            for tb in _table.split("/"):
                # get types list from RESULT_DICT
                types_list = RESULT_DICT[tb].keys()
                for t in types_list:
                    if re.match(_condition, t):
                        return True

        # if non of above conditions matched, return False
        return False

    def __generate_dict(self, test_output_dir, types, _table):
        """
        construct pbf data dict
        :param test_output_dir: the directory where pbf data is
        :param types: all types list in pbf data
        :param _table:
        :return:
        """
        # dump json from file to dict

        table_dict = CaseDump(os.path.join(test_output_dir, _table + OUT_SUFFIX), CASE_FILE_TYPE_JSON).dump()

        # foreach key from statistic report, split it into table/type/key/sub_value
        type_dict = {}
        for _key in table_dict.keys():
            # wipe off table
            _key = _key.replace("%s_" % _table, "")
            for _type in types:
                # wipe off type
                if _type and _type in _key:
                    if _type not in type_dict.keys():
                        type_dict[_type] = {}
                    _key = _key.replace("%s_" % _type, "")
                    # if has sub_value, set RESULT_DICT[table][type][key] = sub_value
                    # else set RESULT_DICT[table][type][key] = None
                    if "#" in _key:
                        sub_value = _key.split("#")
                        type_dict[_type][sub_value[0]] = sub_value[1]
                    else:
                        type_dict[_type][_key] = ""
                    break

        global RESULT_DICT
        RESULT_DICT[_table] = type_dict

    @staticmethod
    def copy_subtree(src, dst):
        """
        copy files from src to dst
        :param src:
        :param dst:
        :return:
        """
        for src_f in os.listdir(src):
            src_path = os.path.join(src, src_f)
            if os.path.isdir(src_path):
                dst_path = os.path.join(dst, src_f)
                if not os.path.exists(dst_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    ProcessJson.copy_subtree(src_path, dst_path)
            elif os.path.isfile(src_path):
                dst_path = os.path.join(dst, src_f)
                if not os.path.exists(dst_path):
                    shutil.copy(src_path, dst_path)

    @staticmethod
    def output_json_file(dict, output_file):
        """
        write dict to json file
        :param dict:
        :param output_file:
        :return:
        """
        output_dir = os.path.dirname(output_file)
        # make output dir
        not os.path.exists(output_dir) and os.makedirs(output_dir)
        # change output dir mod
        os.chmod(output_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)  # mode:777

        # write json file
        with open(output_file, 'w') as outfile:
            outfile.write(json.dumps(dict))

if __name__ == '__main__':
    json_dir = os.path.join(ROOT_DIR, 'test_output')
    process_json = ProcessJson()
    process_json.parse_json(json_dir)
    process_json.collect_data()
