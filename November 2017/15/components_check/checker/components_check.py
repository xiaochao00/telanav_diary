import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from rdf_importer import Importer
import glob
import json
import re
from collections import OrderedDict

region_component_conf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/region_components.json')

CHECK_FUNCTION_NAME_SUFFIX = "_check"


class ComponentChecker:
    def __init__(self, data_dir):
        self.data_dir = data_dir

        self._extend_function_dic = OrderedDict({})

    def _check_data_dir_exists(self):
        Util.print_standout("check directory exists,empty or not. %s " % self.data_dir)

        if not self.data_dir or not os.path.exists(self.data_dir) or not os.listdir(self.data_dir):
            Util.print_error("data directory[%s] is None or not exist or empty" % self.data_dir)
            return False
        return True

    def check_file_pattern_list_match(self, filename_pattern_list):
        Util.print_standout("check file exists or not. %s" % filename_pattern_list)
        for filename_pattern in filename_pattern_list:
            if not filename_pattern or (not glob.glob(os.path.join(self.data_dir, filename_pattern)) and not glob.glob(os.path.join(self.data_dir, filename_pattern.lower())) and not glob.glob(os.path.join(self.data_dir, filename_pattern.upper()))):
                Util.print_error("check filename pattern [%s] is None or not match." % filename_pattern)
                return False
        return True

    def check_sub_directory_pattern_list_match(self, sub_dir_name_pattern_list):
        Util.print_standout("check sub directory by pattern.%s " % sub_dir_name_pattern_list)
        sub_dir_name_list = os.listdir(self.data_dir)
        # matched check
        matched_dir_list = []
        for sub_dir_pattern in sub_dir_name_pattern_list:
            flag = False
            for sub_dir_name in sub_dir_name_list:
                flag = flag or (re.match(sub_dir_pattern, sub_dir_name, re.IGNORECASE))
                if flag:
                    matched_dir_list.append(os.path.join(self.data_dir, sub_dir_name))
                    break
            if not flag:
                Util.print_error("check sub directory failed. pattern [%s] in directory [%s] can not find" % (sub_dir_pattern, self.data_dir))
                return False

        # empty check
        for matched_dir in matched_dir_list:
            if not os.listdir(matched_dir):
                Util.print_error("check sub directory failed. pattern [%s] matched directory [%s] in directory [%s] is empty" % (sub_dir_name, matched_dir, self.data_dir))
                return False
        return True

    def check_not_exist_empty_directory(self):
        Util.print_standout("check is there haven`t empty directory.")
        for p, dirs, filename_list in os.walk(self.data_dir):
            for dir_name in dirs:
                if not os.listdir(os.path.join(p, dir_name)):
                    Util.print_error("there exist empty directory in [%s] of [%s]" % (dir_name, self.data_dir))
                    return False
        return True

    def add_extend_function(self, function_name, *parameters):
        self._extend_function_dic[function_name] = parameters

    def _check_extend_function(self):
        for function_name, parameters in self._extend_function_dic.iteritems():
            if not apply(function_name, parameters):
                return False
        return True

    def check(self):
        if not self._check_data_dir_exists():
            return False
        if not self._check_extend_function():
            return False

        return True


class CheckFunctions:
    def __init__(self):
        pass

    TOLL_COST_FILENAME_PATTERN = ["TGMATCH.txt"]
    CSV_EXPANDED_NAME_PATTERN = ["*.csv*"]
    ZIP_EXPANDED_NAME_PATTERN = ["*.zip"]
    XML_EXPANDED_NAME_PATTERN = ["*.xml"]
    TXT_EXPANDED_NAME_PATTERN = ["*.txt"]
    TAR_EXPANDED_NAME_PATTERN = ["*.tar"]
    RDF_FILENAME_PATTERN_LIST = ["*CORE.tar", "*SDO.tar", "*WKT.tar", "*rdf_customer_software.tar"]
    EU_RDF_FILENAME_PATTERN_LIST = ["*EUE*CORE.tar", "*EUE*SDO.tar", "*EUE*WKT.tar", "*EUE*rdf_customer_software.tar",
                                    "*EUW*CORE.tar", "*EUW*SDO.tar", "*EUW*WKT.tar", "*EUW*rdf_customer_software.tar"]
    KOR_RDF_FILENAME_PATTERN_LIST = ["*Core.zip", "*rdf_customer_software.tar"]

    DT_JUNCTION_VIEW = "components/junction_view"
    DT_SPEED_PATTERN = "components/speed_pattern"
    DT_TRAFFIC_LOCATION = "components/traffic_location"
    DT_JUNCTION_VIEW_OTHER_REGION_SUB_LIST = ['2D_Generalized_Junction.*', '2D_Generalized_Signs.*', '2D_Junctions.*', '2D_Signs.*']

    @staticmethod
    def tollcost_check(data_path):
        toll_cost_path = os.path.join(data_path, Importer.DT_KOR_TOLL_COST)
        tollcost_component = ComponentChecker(toll_cost_path)
        tollcost_component.add_extend_function(tollcost_component.check_file_pattern_list_match, CheckFunctions.TOLL_COST_FILENAME_PATTERN)
        return tollcost_component

    @staticmethod
    def hamlet_check(data_path):
        hamlet_path = os.path.join(data_path, Importer.DT_HAMLET)
        hamlet_component = ComponentChecker(hamlet_path)
        hamlet_component.add_extend_function(hamlet_component.check_file_pattern_list_match, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return hamlet_component

    @staticmethod
    def new_address_check(data_path):
        new_address_path = os.path.join(data_path, Importer.DT_KOR_NEW_ADDRESS)
        new_address_component = ComponentChecker(new_address_path)
        new_address_component.add_extend_function(new_address_component.check_file_pattern_list_match, CheckFunctions.TXT_EXPANDED_NAME_PATTERN)
        return new_address_component

    @staticmethod
    def giv_check(data_path):
        giv_path = os.path.join(data_path, Importer.DT_GJV)
        giv_component = ComponentChecker(giv_path)
        giv_component.add_extend_function(giv_component.check_file_pattern_list_match, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return giv_component

    @staticmethod
    def postal_code_check(data_path):
        postal_code_path = os.path.join(data_path, Importer.DT_POSTAL_CODE)
        postal_component = ComponentChecker(postal_code_path)
        postal_component.add_extend_function(postal_component.check_file_pattern_list_match, CheckFunctions.TXT_EXPANDED_NAME_PATTERN)
        return postal_component

    @staticmethod
    def landmark_check(data_path):
        landmark_path = os.path.join(data_path, Importer.DT_3D_LANDMARK)
        landmark_component = ComponentChecker(landmark_path)
        landmark_component.add_extend_function(landmark_component.check_file_pattern_list_match, CheckFunctions.ZIP_EXPANDED_NAME_PATTERN)
        return landmark_component

    @staticmethod
    def speed_camera_check(data_path):
        speed_camera_path = os.path.join(data_path, Importer.DT_SAFETY_CAMERA)
        speed_camera_component = ComponentChecker(speed_camera_path)
        speed_camera_component.add_extend_function(speed_camera_component.check_not_exist_empty_directory)
        return speed_camera_component

    @staticmethod
    def rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        rdf_component = ComponentChecker(rdf_path)
        rdf_component.add_extend_function(rdf_component.check_file_pattern_list_match, CheckFunctions.RDF_FILENAME_PATTERN_LIST)
        return rdf_component

    @staticmethod
    def eu_rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        eu_rdf_component = ComponentChecker(rdf_path)
        eu_rdf_component.add_extend_function(eu_rdf_component.check_file_pattern_list_match, CheckFunctions.EU_RDF_FILENAME_PATTERN_LIST)
        return eu_rdf_component

    @staticmethod
    def kor_rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        kor_rdf_component = ComponentChecker(rdf_path)
        kor_rdf_component.add_extend_function(kor_rdf_component.check_file_pattern_list_match, CheckFunctions.KOR_RDF_FILENAME_PATTERN_LIST)
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
        junction_view_component.add_extend_function(junction_view_component.check_sub_directory_pattern_list_match, CheckFunctions.DT_JUNCTION_VIEW_OTHER_REGION_SUB_LIST)
        return junction_view_component

    @staticmethod
    def cn_kor_junction_view_check(data_path):
        junction_view_path = os.path.join(data_path, CheckFunctions.DT_JUNCTION_VIEW)
        cn_kor_junction_view_component = ComponentChecker(junction_view_path)
        cn_kor_junction_view_component.add_extend_function(cn_kor_junction_view_component.check_not_exist_empty_directory, )
        return cn_kor_junction_view_component

    @staticmethod
    def speed_pattern_check(data_path):
        speed_pattern_path = os.path.join(data_path, CheckFunctions.DT_SPEED_PATTERN)
        speed_pattern_component = ComponentChecker(speed_pattern_path)
        speed_pattern_component.add_extend_function(speed_pattern_component.check_file_pattern_list_match, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return speed_pattern_component

    @staticmethod
    def cn_speed_pattern_check(data_path):
        speed_pattern_path = os.path.join(data_path, CheckFunctions.DT_SPEED_PATTERN)
        cn_speed_pattern_component = ComponentChecker(speed_pattern_path)
        cn_speed_pattern_component.add_extend_function(cn_speed_pattern_component.check_not_exist_empty_directory, )
        return cn_speed_pattern_component

    @staticmethod
    def traffic_location_check(data_path):
        traffic_location_path = os.path.join(data_path, CheckFunctions.DT_TRAFFIC_LOCATION)
        traffic_location_component = ComponentChecker(traffic_location_path)
        traffic_location_component.add_extend_function(traffic_location_component.check_file_pattern_list_match, CheckFunctions.TAR_EXPANDED_NAME_PATTERN)
        return traffic_location_component

    @staticmethod
    def additional_contents_check(data_path):
        additional_contents_path = os.path.join(data_path, Importer.DT_CN_ADD_CONTENT)
        additional_contents_component = ComponentChecker(additional_contents_path)
        additional_contents_component.add_extend_function(additional_contents_component.check_file_pattern_list_match, CheckFunctions.XML_EXPANDED_NAME_PATTERN)
        return additional_contents_component


def check_region_components(region, is_level0, base_path):
    if is_level0:
        region += "_LEVEL0"

    with open(region_component_conf, 'r') as f:
        region_component_dic = json.load(f)

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
        for name, check_component in region_check_component_dic.iteritems():
            try:
                if not check_component.check():
                    return False
            except Exception, e:
                return name, e.message

        return True


def main(data_path):
    vendor, region, version, is_level0 = Util.parse_rdf_version(os.path.basename(data_path))
    if region and version:
        check_result = check_region_components(region, is_level0, data_path)
        if check_result is True:
            check_state = "pass"
            error_component_name = error_msg = ''
        else:
            check_state = "failed"
            error_component_name = check_result[0]
            error_msg = check_result[1]
    if is_level0:
        region += "_Level0"
    return region, version, check_state, error_component_name, error_msg


class ExtendChecker:
    def __init__(self, data_base_path):
        self.data_base_path = data_base_path

    def check_all_region(self, to_path=os.path.dirname(__file__)):
        region_path_list = os.listdir(self.data_base_path)
        region_path_list = filter(Util.region_fileter, region_path_list)

        check_result_data_list = []
        for region_path in region_path_list:
            region, version, check_state, error_component_name, error_msg = main(region_path)
            check_result_data = OrderedDict()
            check_result_data["region"] = region
            check_result_data["version"] = version
            check_result_data["check_state"] = check_state
            check_result_data["error_component_name"] = error_component_name
            check_result_data["error_msg"] = error_msg

            check_result_data_list.append(check_result_data)

        Util.write_to_js_file(to_path, check_result_data_list)


class Util:
    def __init__(self):
        pass

    LEVEL0_FLAG = "LEVEL0"
    REPORT_JS_FILEPATH = "html/result.js"
    REPORT_JS_VAR_NAME = "result_info"

    @staticmethod
    def print_standout(info):
        """
        print information to standout
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
        raise Exception(err)

    @staticmethod
    def parse_rdf_version(rdf_data):
        """
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
        if re.match(".*17Q[1-4]", name, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def write_to_js_file(file_path, data_list):
        save_file_path = os.path.join(file_path, Util.REPORT_JS_FILEPATH)
        data_json_str = json.dumps(data_list)
        print data_json_str
        with open(save_file_path, 'w') as f:
            f.write("var %s=%s" % (Util.REPORT_JS_VAR_NAME, data_json_str))
            Util.print_standout("write to file[%s] finish." % save_file_path)


if __name__ == '__main__':
    # region = "CN"
    # is_level0 = False
    # data_dir = '/var/www/html/data/CN_NT_17Q2'
    # print check_region_components(region, is_level0, data_dir)
    # pass

    base_path = '/var/www/html/data'
    ExtendChecker(base_path).check_all_region()
