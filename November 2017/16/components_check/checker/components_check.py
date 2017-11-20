import os
import sys
import re
import json
import optparse
from collections import OrderedDict

CHECK_FUNCTION_NAME_SUFFIX = "_check"
CONFIG_FILE_RELATIVE_PATH = "config/region_components.json"
ROOT_PATH = os.path.dirname(__file__)
region_component_conf = os.path.join(os.path.dirname(ROOT_PATH), CONFIG_FILE_RELATIVE_PATH)


class Importer(object):
    """ Copy from RDF_import

        class comment
    """
    DT_RDF = '__rdf'
    DT_POSTAL_CODE = 'components/postal_code'
    DT_3D_LANDMARK = 'components/3dlandmark_vendor'
    DT_SAFETY_CAMERA = 'components/speed_camera'
    DT_GJV = 'components/GJV'
    DT_LEVEL0_SENSITIVE_ISLAND = 'components/level0'
    DT_LEVEL2_SENSITIVE_ISLAND = 'components/level2_sensitive'
    DT_SENSITIVE_BOUNDARY_RIVER = 'components/sensitive_boundary_river'
    DT_CN_ADD_CONTENT = 'components/additional_content'
    DT_HAMLET = 'components/hamlet'
    DT_KOR_NEW_ADDRESS = 'components/NEW_ADDRESS'
    DT_KOR_TOLL_COST = 'components/TOLL_COST'


class ComponentChecker(object):
    """Component class

    there are all need inner check function. And do check in check() method
    """

    def __init__(self, data_dir):
        self.data_dir = data_dir

        self._extend_function_dic = OrderedDict({})

    @staticmethod
    def _check_path_valid(check_path):
        """Check directory exist and empty or not

        :return: True if exist data directory path and no empty, False if not exist or empty
        """
        Util.print_standout("check directory exists,empty or not. %s " % check_path)

        if not check_path or not os.path.exists(check_path) or not os.listdir(check_path):
            Util.print_error("data directory[%s] is None or not exist or empty" % check_path)
            return False
        return True

    @staticmethod
    def _find_by_name_pattern(search_directory, name_pattern, is_file=True):
        """Find file or directory in search_directory, which filename or directory name match name_pattern

        :param search_directory: the search directory path
        :param name_pattern: pattern of matched filename
        :param is_file: only match file or directory
        :return: the matched absolute path if match, None if mismatches
        """
        if not os.listdir(search_directory):
            return None
        # filter check list
        choose_list = []
        if is_file:
            choose_list += filter(lambda x: os.path.isfile(x), [os.path.join(search_directory, y) for y in os.listdir(search_directory)])
        else:
            choose_list += filter(lambda x: os.path.isdir(x), [os.path.join(search_directory, y) for y in os.listdir(search_directory)])
        # check
        for sub_name in choose_list:
            if re.match(name_pattern, os.path.basename(sub_name), re.IGNORECASE):
                return sub_name
        return None

    def check_filename_pattern_list(self, filename_pattern_list):
        """Check files matched all these pattern in filename_pattern_list from data directory

        :param filename_pattern_list:
        :return: True if all matched, False if any one mismatches
        """
        Util.print_standout("check file exists or not. %s" % filename_pattern_list)
        for filename_pattern in filename_pattern_list:
            matched_file_name = self._find_by_name_pattern(self.data_dir, filename_pattern)
            if not filename_pattern or not matched_file_name:
                Util.print_error("check filename pattern [%s] is None or not match." % filename_pattern)
                return False
        return True

    def check_sub_directory_name_pattern_list(self, sub_dir_name_pattern_list):
        """Check subdirectory by subdirectory pattern conditions

        :param sub_dir_name_pattern_list: pattern list that all need to match
        :return: True if find all those directories by this pattern list; False if any one pattern mismatches
        """
        Util.print_standout("check sub directory by pattern.%s " % sub_dir_name_pattern_list)
        # matched check
        matched_dir_list = []
        for sub_dir_pattern in sub_dir_name_pattern_list:
            matched_dir_name = self._find_by_name_pattern(self.data_dir, sub_dir_pattern, False)
            if not matched_dir_name:
                Util.print_error("check sub directory failed. pattern [%s] in directory [%s] can not find" % (sub_dir_pattern, self.data_dir))
                return False
            matched_dir_list.append(os.path.join(self.data_dir, matched_dir_name))
        # empty check
        for matched_dir in matched_dir_list:
            if not os.listdir(matched_dir):
                Util.print_error("check sub directory failed. pattern %s matched directory [%s] in directory [%s] is empty" % (sub_dir_name_pattern_list, matched_dir, self.data_dir))
                return False
        return True

    def check_directory_valid(self):
        """Check if is there no empty directory in data directory ?

        :return: False if there is any empty directory, True if no empty directory
        """
        Util.print_standout("check is there haven`t empty directory.")
        for p, dirs, filename_list in os.walk(self.data_dir):
            for dir_name in dirs:
                if not os.listdir(os.path.join(p, dir_name)):
                    Util.print_error("there exist empty directory in [%s] of [%s]" % (dir_name, self.data_dir))
                    return False
        return True

    def check_filename_pattern_in_specific_dir_name(self, specific_dir_name, filename_pattern):
        """Search file from specific directory

        :param specific_dir_name:
        :param filename_pattern:
        :return:
        """
        Util.print_standout("search file[%s] from specific directory[%s]" % (filename_pattern, specific_dir_name))
        for p, dirs, filename_list in os.walk(self.data_dir):
            for dir_name in dirs:
                # 1.search directory
                if dir_name == specific_dir_name:
                    # 2.match file
                    Util.print_standout("path of specific directory[%s] is [%s]" % (specific_dir_name, os.path.join(p, dir_name)))
                    for filename in filename_list:
                        if re.match(filename_pattern, filename, re.IGNORECASE):
                            return True
                    Util.print_error("can not find file like[%s] in directory [%s]" % (filename_pattern, os.path.join(p, dir_name)))
                    break
        Util.print_error("can not find directory [%s] in data path[%s]" % (specific_dir_name, self.data_dir))
        return False

    def add_extend_function(self, function_name, *parameters):
        """Add the need check function for this component

        :param function_name: name of the added function
        :param parameters: parameters of this added function
        :return:
        """
        self._extend_function_dic[function_name] = parameters

    def _check_extend_function(self):
        """Check all added functions

        :return:
        """
        for function_name, parameters in self._extend_function_dic.iteritems():
            if not apply(function_name, parameters):
                return False
        return True

    def check(self):
        if not self._check_path_valid(self.data_dir):
            return False
        if not self._check_extend_function():
            return False

        return True


class CheckFunctions(object):
    """CheckFunction class

    each method package a ComponentChecker object
    """

    def __init__(self):
        pass

    TOLL_COST_FILENAME_PATTERN = ["TGMATCH\.txt"]
    CSV_EXPANDED_NAME_PATTERN = [".*\.csv*"]
    ZIP_EXPANDED_NAME_PATTERN = [".*\.zip"]
    XML_EXPANDED_NAME_PATTERN = [".*\.xml"]
    KOR_SPEED_CAMERA_XML_NAME_PATTERN = ".*\.xml.*"
    TXT_EXPANDED_NAME_PATTERN = [".*\.txt"]
    TAR_EXPANDED_NAME_PATTERN = [".*\.tar"]
    RDF_FILENAME_PATTERN_LIST = [".*CORE\.tar", ".*SDO\.tar", ".*WKT\.tar", ".*rdf_customer_software\.tar"]
    EU_RDF_FILENAME_PATTERN_LIST = [".*EUE.*CORE\.tar", ".*EUE.*SDO\.tar", ".*EUE.*WKT\.tar", ".*EUE.*rdf_customer_software\.tar",
                                    ".*EUW.*CORE\.tar", ".*EUW.*SDO\.tar", ".*EUW.*WKT\.tar", ".*EUW.*rdf_customer_software\.tar"]
    KOR_RDF_FILENAME_PATTERN_LIST = [".*Core\.zip", ".*rdf_customer_software\.tar"]

    DT_JUNCTION_VIEW = "components/junction_view"
    DT_SPEED_PATTERN = "components/speed_pattern"
    DT_TRAFFIC_LOCATION = "components/traffic_location"
    DT_JUNCTION_VIEW_OTHER_REGION_SUB_LIST = ['2D_Generalized_Junction.*', '2D_Generalized_Signs.*', '2D_Junctions.*', '2D_Signs.*']
    DT_KOR_SPECIFIED_SPEED_CAMERA_DIR_NAME = "KOR"

    @staticmethod
    def tollcost_check(data_path):
        toll_cost_path = os.path.join(data_path, Importer.DT_KOR_TOLL_COST)
        tollcost_component = ComponentChecker(toll_cost_path)
        tollcost_component.add_extend_function(tollcost_component.check_filename_pattern_list, CheckFunctions.TOLL_COST_FILENAME_PATTERN)
        return tollcost_component

    @staticmethod
    def hamlet_check(data_path):
        hamlet_path = os.path.join(data_path, Importer.DT_HAMLET)
        hamlet_component = ComponentChecker(hamlet_path)
        hamlet_component.add_extend_function(hamlet_component.check_filename_pattern_list, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return hamlet_component

    @staticmethod
    def new_address_check(data_path):
        new_address_path = os.path.join(data_path, Importer.DT_KOR_NEW_ADDRESS)
        new_address_component = ComponentChecker(new_address_path)
        new_address_component.add_extend_function(new_address_component.check_filename_pattern_list, CheckFunctions.TXT_EXPANDED_NAME_PATTERN)
        return new_address_component

    @staticmethod
    def giv_check(data_path):
        giv_path = os.path.join(data_path, Importer.DT_GJV)
        giv_component = ComponentChecker(giv_path)
        giv_component.add_extend_function(giv_component.check_filename_pattern_list, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return giv_component

    @staticmethod
    def postal_code_check(data_path):
        postal_code_path = os.path.join(data_path, Importer.DT_POSTAL_CODE)
        postal_component = ComponentChecker(postal_code_path)
        postal_component.add_extend_function(postal_component.check_filename_pattern_list, CheckFunctions.TXT_EXPANDED_NAME_PATTERN)
        return postal_component

    @staticmethod
    def landmark_check(data_path):
        landmark_path = os.path.join(data_path, Importer.DT_3D_LANDMARK)
        landmark_component = ComponentChecker(landmark_path)
        landmark_component.add_extend_function(landmark_component.check_filename_pattern_list, CheckFunctions.ZIP_EXPANDED_NAME_PATTERN)
        return landmark_component

    @staticmethod
    def speed_camera_check(data_path):
        speed_camera_path = os.path.join(data_path, Importer.DT_SAFETY_CAMERA)
        speed_camera_component = ComponentChecker(speed_camera_path)
        speed_camera_component.add_extend_function(speed_camera_component.check_directory_valid, )
        return speed_camera_component

    @staticmethod
    def kor_speed_camera_check(data_path):
        kor_speed_camera_path = os.path.join(data_path, Importer.DT_SAFETY_CAMERA)
        kor_speed_camera_component = ComponentChecker(kor_speed_camera_path)
        kor_speed_camera_component.add_extend_function(kor_speed_camera_component.check_filename_pattern_in_specific_dir_name, CheckFunctions.DT_KOR_SPECIFIED_SPEED_CAMERA_DIR_NAME, CheckFunctions.KOR_SPEED_CAMERA_XML_NAME_PATTERN)
        return kor_speed_camera_component

    @staticmethod
    def rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        rdf_component = ComponentChecker(rdf_path)
        rdf_component.add_extend_function(rdf_component.check_filename_pattern_list, CheckFunctions.RDF_FILENAME_PATTERN_LIST)
        return rdf_component

    @staticmethod
    def eu_rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        eu_rdf_component = ComponentChecker(rdf_path)
        eu_rdf_component.add_extend_function(eu_rdf_component.check_filename_pattern_list, CheckFunctions.EU_RDF_FILENAME_PATTERN_LIST)
        return eu_rdf_component

    @staticmethod
    def kor_rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        kor_rdf_component = ComponentChecker(rdf_path)
        kor_rdf_component.add_extend_function(kor_rdf_component.check_filename_pattern_list, CheckFunctions.KOR_RDF_FILENAME_PATTERN_LIST)
        return kor_rdf_component

    @staticmethod
    def level0_check(data_path):
        level0_path = os.path.join(data_path, Importer.DT_LEVEL0_SENSITIVE_ISLAND)
        return ComponentChecker(level0_path)

    @staticmethod
    def level2_check(data_path):
        level2_path = os.path.join(data_path, Importer.DT_LEVEL2_SENSITIVE_ISLAND)
        return ComponentChecker(level2_path)

    @staticmethod
    def other_region_junction_view_check(data_path):
        junction_view_path = os.path.join(data_path, CheckFunctions.DT_JUNCTION_VIEW)
        junction_view_component = ComponentChecker(junction_view_path)
        junction_view_component.add_extend_function(junction_view_component.check_sub_directory_name_pattern_list, CheckFunctions.DT_JUNCTION_VIEW_OTHER_REGION_SUB_LIST)
        return junction_view_component

    @staticmethod
    def cn_kor_junction_view_check(data_path):
        junction_view_path = os.path.join(data_path, CheckFunctions.DT_JUNCTION_VIEW)
        cn_kor_junction_view_component = ComponentChecker(junction_view_path)
        cn_kor_junction_view_component.add_extend_function(cn_kor_junction_view_component.check_directory_valid, )
        return cn_kor_junction_view_component

    @staticmethod
    def speed_pattern_check(data_path):
        speed_pattern_path = os.path.join(data_path, CheckFunctions.DT_SPEED_PATTERN)
        speed_pattern_component = ComponentChecker(speed_pattern_path)
        speed_pattern_component.add_extend_function(speed_pattern_component.check_filename_pattern_list, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return speed_pattern_component

    @staticmethod
    def cn_speed_pattern_check(data_path):
        speed_pattern_path = os.path.join(data_path, CheckFunctions.DT_SPEED_PATTERN)
        cn_speed_pattern_component = ComponentChecker(speed_pattern_path)
        cn_speed_pattern_component.add_extend_function(cn_speed_pattern_component.check_directory_valid, )
        return cn_speed_pattern_component

    @staticmethod
    def traffic_location_check(data_path):
        traffic_location_path = os.path.join(data_path, CheckFunctions.DT_TRAFFIC_LOCATION)
        traffic_location_component = ComponentChecker(traffic_location_path)
        traffic_location_component.add_extend_function(traffic_location_component.check_filename_pattern_list, CheckFunctions.TAR_EXPANDED_NAME_PATTERN)
        return traffic_location_component

    @staticmethod
    def additional_contents_check(data_path):
        additional_contents_path = os.path.join(data_path, Importer.DT_CN_ADD_CONTENT)
        additional_contents_component = ComponentChecker(additional_contents_path)
        additional_contents_component.add_extend_function(additional_contents_component.check_filename_pattern_list, CheckFunctions.XML_EXPANDED_NAME_PATTERN)
        return additional_contents_component


class CheckStateInfo(object):
    """ Checker result info class
    """

    def __init__(self, region, version, detail_info_list, state):
        self.region = region
        self.version = version
        self.state = state
        self.detail_info_list = detail_info_list


def check_region_components(region, is_level0, base_path):
    """Every component check state info of this region

    :param region:
    :param is_level0:
    :param base_path:
    :return: {component_name:msg,...} for success and failed
    """
    if is_level0:
        region = "_".join([region, Util.LEVEL0_FLAG])
        # 1.load config file
    with open(region_component_conf, 'r') as f:
        region_component_dic = json.load(f)
        # 2.get all check components of this region
        region_check_function_str = region_component_dic.get(region.upper())
        if not region_check_function_str:
            Util.print_error("config file did not contain this region[%s] check function. check please" % region)
            return False
        region_check_function_list = region_check_function_str.split("|")

        region_check_component_dic = {}
        for region_check_function in region_check_function_list:
            function_name = region_check_function.strip()
            if function_name:
                function_full_name = function_name + CHECK_FUNCTION_NAME_SUFFIX
                region_check_component_dic[function_name] = getattr(CheckFunctions, function_full_name)(base_path)
        # 3.check each component of this region
        failed_components_check_info_dic = OrderedDict({})
        success_components_check_info_dic = OrderedDict({})
        for name, check_component in region_check_component_dic.iteritems():
            try:
                if check_component.check():
                    success_components_check_info_dic[name] = ""
                else:
                    failed_components_check_info_dic[name] = ""

            except CheckException, e:
                failed_components_check_info_dic[name] = e.message

        return success_components_check_info_dic, failed_components_check_info_dic


def main():
    """Check this data path`s structure

    :return: True if pass check, False if failed check
    """
    # 1.get the input value
    parser = optparse.OptionParser()
    parser.add_option('-D', '--data-path', help='data path for check', dest='data_path')

    options, args = parser.parse_args()
    if not options.data_path:
        parser.print_help()
        sys.exit(-1)
    data_path = options.data_path
    vendor, region, version, is_level0 = Util.parse_rdf_version(os.path.basename(data_path))
    # 2.check
    if region and version:
        success_components_check_info_dic, failed_components_check_info_dic = check_region_components(region, is_level0, data_path)

        if not failed_components_check_info_dic:
            return True
        return False


class ExtendChecker(object):
    """Extend checker for main

    check all region base on single region`s components check
    1. save check report
    """
    CHECK_SUCCESS_STR = "Pass"
    CHECK_FAILED_STR = "Failed"

    def __init__(self):
        pass

    @staticmethod
    def check_all_region(data_base_path, report_path=ROOT_PATH):
        """Check all region in base path, and generate check report

        :param data_base_path: all data parent path
        :param report_path: path to save the report
        :return:
        """
        # 1.get and filter all region`s data path
        region_path_list = os.listdir(data_base_path)
        region_path_list = filter(Util.region_fileter, region_path_list)

        ExtendChecker.check_multi_region([os.path.join(data_base_path, x) for x in region_path_list], report_path)

    @staticmethod
    def check_multi_region(region_path_list, report_path=ROOT_PATH):
        check_info_list = []
        for region_path in region_path_list:
            # 1.check single region
            check_info = ExtendChecker.check_single_region(region_path)
            check_info_list.append(check_info)
        # 2.save report
        ExtendChecker.generate_report(check_info_list, report_path)

    @staticmethod
    def check_single_region(region_data_path):
        # 1.check every components of this region path
        vendor, region, version, is_level0 = Util.parse_rdf_version(os.path.basename(region_data_path))
        if region and version:
            success_components_check_info_dic, failed_components_check_info_dic = check_region_components(region, is_level0, region_data_path)
            # 2.collection success check info and failed check info
            if is_level0:
                region = "_".join([region, Util.LEVEL0_FLAG])
            detail_msg_list = []
            for failed_component_name, failed_msg in failed_components_check_info_dic.iteritems():
                detail_msg_list.append(":".join([failed_component_name, failed_msg]))
            for component_name, msg in success_components_check_info_dic.iteritems():
                detail_msg_list.append(component_name)
            check_state_str = ExtendChecker.CHECK_FAILED_STR if failed_components_check_info_dic else ExtendChecker.CHECK_SUCCESS_STR

            return CheckStateInfo(region, version, detail_msg_list, check_state_str)

    @staticmethod
    def generate_report(check_info_list, to_path):
        # 1.generate info list to dictionary structure
        check_result_data_list = []
        for check_info in check_info_list:
            check_result_data = OrderedDict()
            check_result_data["region"] = check_info.region
            check_result_data["version"] = check_info.version

            check_result_data["check_message"] = check_info.detail_info_list
            check_result_data["check_state"] = check_info.state

            check_result_data_list.append(check_result_data)
        # 2.sort data list
        check_result_data_list.sort(key=lambda d: d['version'])
        check_result_data_list.sort(key=lambda d: d['region'])
        # check_result_data_list.sort(key=lambda d: d['check_state'])
        # 3.save js report
        Util.write_to_js_file(to_path, check_result_data_list)


class Util(object):
    """Util class for use

    """

    def __init__(self):
        pass

    LEVEL0_FLAG = "LEVEL0"
    REPORT_JS_FILEPATH = "html/result.js"
    REPORT_JS_VAR_NAME = "result_info"

    @staticmethod
    def print_standout(info):
        """Print information to standout

        :param info:
        :return:
        """
        sys.stdout.write("Info: %s" % info)
        sys.stdout.write("\n")
        sys.stdout.flush()

    @staticmethod
    def print_error(err):
        """
        :param err: information of error
        :return:
        """
        sys.stderr.write("Error: %s" % err)
        sys.stderr.write("\n")
        sys.stderr.flush()
        # raise exception to catch the wrong message
        raise CheckException(err)

    @staticmethod
    def parse_rdf_version(rdf_data):
        """Parse rdf data name to vendor, region, version, level0_or_not

        rdf data format: XX_YY_ZZZZ (e.g. EU_HERE_17Q1 or XX_YY_ZZZZ_OO (eg. CN_NT_15Q1_Level0)'
                XX   : Region'
                YY   : Vendor Name'
                ZZZZ : Data version, for example 15Q1'
                OO   : Other Information, eg. Level0 data or not'
        :param rdf_data:
        :return: vendor, region, version, level0_or_not
        """
        m = re.match('([A-Z]+)_([A-Z0-9]+)_(\d+Q\d)(.*)', rdf_data, re.IGNORECASE)
        if m:
            is_level0 = m.group(4).upper().strip('_') == Util.LEVEL0_FLAG
            return m.group(2).upper(), m.group(1).upper(), m.group(3).upper(), is_level0
        else:
            return None, None, None, None

    @staticmethod
    def region_fileter(name):
        if 'WORLDMAP' in name.upper() or 'test' in name.lower():
            return False
        if re.match(".*\d[7-9]Q[1-4]", name, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def write_to_js_file(file_path, data_list):
        """Write data list to js file

        :param file_path:  save file path
        :param data_list: [{key:value,},{},...]
        :return:
        """
        # 1. save path
        save_file_path = os.path.join(file_path, Util.REPORT_JS_FILEPATH)
        html_res_path = os.path.dirname(save_file_path)
        # 2. copy html js resources
        if not os.path.exists(html_res_path):
            import shutil
            shutil.copy(os.path.join(ROOT_PATH, os.path.basename(html_res_path)), os.path.dirname(html_res_path))
        # 3. json str and save to file
        data_json_str = json.dumps(data_list)
        print data_json_str
        with open(save_file_path, 'w') as f:
            f.write("var %s=%s" % (Util.REPORT_JS_VAR_NAME, data_json_str))
            Util.print_standout("write to file[%s] finish." % save_file_path)


class CheckException(Exception):
    """CheckException

    used to raise exception in check
    """

    def __init__(self, message):
        self.message = message


if __name__ == '__main__':
    # base_path = '/var/www/html/data'
    # ExtendChecker().check_all_region(base_path)

    print main()
