import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from rdf_importer import Importer
from common_tool.common_utils import print_standout, print_error
import glob
import json
import re

region_component_conf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/region_components.json')


class ComponentCheck:
    def __init__(self, data_dir):
        self.data_dir = data_dir

        self._extend_function_dic = {}

    def _check_data_dir_exists(self):
        print_standout("check directory exists,empty or not. %s " % self.data_dir)

        if not self.data_dir or not os.path.exists(self.data_dir) or not os.listdir(self.data_dir):
            print_error("data directory is None or not exist or empty")
            return False
        return True

    def check_file_pattern_list_match(self, filename_pattern_list):
        print_standout("check file exists or not. %s" % filename_pattern_list)
        for filename_pattern in filename_pattern_list:
            if not filename_pattern or (not glob.glob(os.path.join(self.data_dir, filename_pattern)) and not glob.glob(os.path.join(self.data_dir, filename_pattern.lower())) and not glob.glob(os.path.join(self.data_dir, filename_pattern.upper()))):
                print_error("check filename pattern %s is None or not match." % filename_pattern)
                return False
        return True

    def check_sub_directory_pattern_list_match(self, sub_dir_name_pattern_list):
        print_standout("check sub directory by pattern.%s " % sub_dir_name_pattern_list)
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
                print_error("check sub directory failed. pattern %s in directory[%s] can not find" % (sub_dir_pattern, self.data_dir))
                return False

        # empty check
        for matched_dir in matched_dir_list:
            if not os.listdir(matched_dir):
                print_error("check sub directory failed. pattern %s matched directory[%s] in directory[%s] is empty" % (sub_dir_name, matched_dir, self.data_dir))
                return False
        return True

    def check_not_exist_empty_directory(self):
        print_standout("check is there haven`t empty directory.")
        for p, dirs, filename_list in os.walk(self.data_dir):
            for dir_name in dirs:
                if not os.listdir(os.path.join(p, dir_name)):
                    print_error("there exist empty directory in [%s] of [%s]" % (dir_name, self.data_dir))
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

    TOLL_COST_FILENAME_PATTERN = ["TGMATCH.TXT"]
    CSV_EXPANDED_NAME_PATTERN = ["*.csv*"]
    ZIP_EXPANDED_NAME_PATTERN = ["*.zip"]
    XML_EXPANDED_NAME_PATTERN = ["*.xml"]
    TXT_EXPANDED_NAME_PATTERN = ["*.txt"]
    TAR_EXPANDED_NAME_PATTERN = ["*.tar"]
    RDF_FILENAME_PATTERN_LIST = ["*CORE.tar", "*SDO.tar", "*WKT.tar", "*rdf_customer_software.tar"]
    EU_RDF_FILENAME_PATTERN_LIST = ["*EUE*CORE.tar", "*EUE*SDO.tar", "*EUE*WKT.tar", "*EUE*rdf_customer_software.tar",
                                    "*EUW*CORE.tar", "*EUW*SDO.tar", "*EUW*WKT.tar", "*EUW*rdf_customer_software.tar"]

    DT_JUNCTION_VIEW = "components/junction_view"
    DT_SPEED_PATTERN = "components/speed_pattern"
    DT_TRAFFIC_LOCATION = "components/traffic_location"
    DT_JUNCTION_VIEW_OTHER_REGION_SUB_LIST = ['2D_Generalized_Junction.*', '2D_Generalized_Signs.*', '2D_Junctions.*', '2D_Signs.*']

    @staticmethod
    def tollcost_check(data_path):
        toll_cost_path = os.path.join(data_path, Importer.DT_KOR_TOLL_COST)
        tollcost_component = ComponentCheck(toll_cost_path)
        tollcost_component.add_extend_function(tollcost_component.check_file_pattern_list_match, CheckFunctions.TOLL_COST_FILENAME_PATTERN)
        return tollcost_component

    @staticmethod
    def hamlet_check(data_path):
        hamlet_path = os.path.join(data_path, Importer.DT_HAMLET)
        hamlet_component = ComponentCheck(hamlet_path)
        hamlet_component.add_extend_function(hamlet_component.check_file_pattern_list_match, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return hamlet_component

    @staticmethod
    def new_address_check(data_path):
        new_address_path = os.path.join(data_path, Importer.DT_KOR_NEW_ADDRESS)
        new_address_component = ComponentCheck(new_address_path)
        new_address_component.add_extend_function(new_address_component.check_file_pattern_list_match, CheckFunctions.TXT_EXPANDED_NAME_PATTERN)
        return new_address_component

    @staticmethod
    def giv_check(data_path):
        giv_path = os.path.join(data_path, Importer.DT_GJV)
        giv_component = ComponentCheck(giv_path)
        giv_component.add_extend_function(giv_component.check_file_pattern_list_match, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return giv_component

    @staticmethod
    def postal_code_check(data_path):
        postal_code_path = os.path.join(data_path, Importer.DT_POSTAL_CODE)
        postal_component = ComponentCheck(postal_code_path)
        postal_component.add_extend_function(postal_component.check_file_pattern_list_match, CheckFunctions.TXT_EXPANDED_NAME_PATTERN)
        return postal_component

    @staticmethod
    def landmark_check(data_path):
        landmark_path = os.path.join(data_path, Importer.DT_3D_LANDMARK)
        landmark_component = ComponentCheck(landmark_path)
        landmark_component.add_extend_function(landmark_component.check_file_pattern_list_match, CheckFunctions.ZIP_EXPANDED_NAME_PATTERN)
        return landmark_component

    @staticmethod
    def speed_camera_check(data_path):
        speed_camera_path = os.path.join(data_path, Importer.DT_SAFETY_CAMERA)
        speed_camera_component = ComponentCheck(speed_camera_path)
        speed_camera_component.add_extend_function(speed_camera_component.check_not_exist_empty_directory)
        return speed_camera_component

    @staticmethod
    def rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        rdf_component = ComponentCheck(rdf_path)
        rdf_component.add_extend_function(rdf_component.check_file_pattern_list_match, CheckFunctions.RDF_FILENAME_PATTERN_LIST)
        return rdf_component

    @staticmethod
    def eu_rdf_check(data_path):
        rdf_path = os.path.join(data_path, Importer.DT_RDF)
        eu_rdf_component = ComponentCheck(rdf_path)
        eu_rdf_component.add_extend_function(eu_rdf_component.check_file_pattern_list_match, CheckFunctions.EU_RDF_FILENAME_PATTERN_LIST)
        return eu_rdf_component

    @staticmethod
    def level0_check(data_path):
        level0_path = os.path.join(data_path, Importer.DT_LEVEL0_SENSITIVE_ISLAND)
        return ComponentCheck(level0_path)

    @staticmethod
    def level2_check(data_path):
        level2_path = os.path.join(data_path, Importer.DT_LEVEL2_SENSITIVE_ISLAND)
        return ComponentCheck(level2_path)

    @staticmethod
    def other_region_junction_view_check(data_path):
        junction_view_path = os.path.join(data_path, CheckFunctions.DT_JUNCTION_VIEW)
        junction_view_component = ComponentCheck(junction_view_path)
        junction_view_component.add_extend_function(junction_view_component.check_sub_directory_pattern_list_match, CheckFunctions.DT_JUNCTION_VIEW_OTHER_REGION_SUB_LIST)
        return junction_view_component

    @staticmethod
    def cn_kor_junction_view_check(data_path):
        junction_view_path = os.path.join(data_path, CheckFunctions.DT_JUNCTION_VIEW)
        cn_kor_junction_view_component = ComponentCheck(junction_view_path)
        cn_kor_junction_view_component.add_extend_function(cn_kor_junction_view_component.check_not_exist_empty_directory, )
        return cn_kor_junction_view_component

    @staticmethod
    def speed_pattern_check(data_path):
        speed_pattern_path = os.path.join(data_path, CheckFunctions.DT_SPEED_PATTERN)
        speed_pattern_component = ComponentCheck(speed_pattern_path)
        speed_pattern_component.add_extend_function(speed_pattern_component.check_file_pattern_list_match, CheckFunctions.CSV_EXPANDED_NAME_PATTERN)
        return speed_pattern_component

    @staticmethod
    def cn_speed_pattern_check(data_path):
        speed_pattern_path = os.path.join(data_path, CheckFunctions.DT_SPEED_PATTERN)
        cn_speed_pattern_component = ComponentCheck(speed_pattern_path)
        cn_speed_pattern_component.add_extend_function(cn_speed_pattern_component.check_not_exist_empty_directory, )
        return cn_speed_pattern_component

    @staticmethod
    def traffic_location_check(data_path):
        traffic_location_path = os.path.join(data_path, CheckFunctions.DT_TRAFFIC_LOCATION)
        traffic_location_component = ComponentCheck(traffic_location_path)
        traffic_location_component.add_extend_function(traffic_location_component.check_file_pattern_list_match, CheckFunctions.TAR_EXPANDED_NAME_PATTERN)
        return traffic_location_component

    @staticmethod
    def additional_contents_check(data_path):
        additional_contents_path = os.path.join(data_path, Importer.DT_CN_ADD_CONTENT)
        additional_contents_component = ComponentCheck(additional_contents_path)
        additional_contents_component.add_extend_function(additional_contents_component.check_file_pattern_list_match, CheckFunctions.XML_EXPANDED_NAME_PATTERN)
        return additional_contents_component


def read_region_component_conf():
    with open(region_component_conf, 'r') as f:
        region_component_dic = json.load(f)
        return region_component_dic


def check_region_components(region, is_level0, base_path):
    if is_level0:
        region += "_level0"
    region_check_function_str = read_region_component_conf().get(region.upper())
    if not region_check_function_str:
        print_error("config file did not contain this region[%s] check function. check please" % region)
        return False
    region_check_function_list = region_check_function_str.split("|")

    region_check_component_list = []
    for region_check_function in region_check_function_list:
        # region_check_component_list.append(eval(region_check_function.strip())(base_path))
        if region_check_function.strip():
            region_check_component_list.append(getattr(CheckFunctions, region_check_function.strip())(base_path))
    for check_component in region_check_component_list:
        if not check_component.check():
            return False
    return True


if __name__ == '__main__':
    region = "CN"
    is_level0 = False
    data_dir = '/var/www/html/data/CN_NT_17Q2'
    print check_region_components(region, is_level0, data_dir)
    pass
