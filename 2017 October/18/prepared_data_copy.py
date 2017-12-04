# coding=utf-8

import os
import sys
from components import standout_print, error_out_print, remove_file, check_directory, execute_cmd, move_directory, remove_dirs, make_targz, path_to_str, path_to_unicode, zip_decompression, make_zip, load_directory_json, parse_path, compare_dic_ge, get_version
import rarfile
from time import time

ROOT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))


class SpecifiedStructure:
    """
    the structure for specified directory
    extract the specified directory
    """

    def __init__(self, rar_file, base_path, specified_list):
        """
        from rar file
        in base path
        specified list : unrar the specified directory from rar file
        decompression steps:
        1. find rar file
        2. cd base path
        3. command execute : unrar x rar_file specified_list like - unrar x ALL.rar ALL/EX_INFO/SCENICROUT ALL/HIGHWAY ...
        :param rar_file:
        :param base_path:
        :param specified_list:
        """
        self.rar_file = rar_file
        self.base_path = base_path
        self.specified_list = specified_list


class FuzzyMatchStructure:
    """
    destination_path : base dir,zip file destination
    like_list : only if match one file in this list, return
    """

    def __init__(self, destination_path, like_list):
        """
        steps:
        1. in destination path find rar file by str in like_list
        2. unrar this rar file in this destination_path
        :param destination_path:
        :param like_list:
        """
        self.destination_path = destination_path
        self.like_list = like_list


class PreparedDataDecompression:
    """
    unrar x xx.rar topath(destination)
    or
    unrar x aa.rar specified_directory(destination is :pwd )

    """
    MESH_DATA_DIC_LIKE = "MESH"
    MESH_DATA_SUFFIX = '.rar'
    MESH_DATA_MOVE_TO = "ROOT"

    ALL_FILE_NAME_LIKE = "ALL.rar"

    ALL_DATA_SPECIFIED_LIST = [
        "ALL/EX_INFO/SCENICROUTE",
        "ALL/HIGHWAY",
        "ALL/HS",
        "ALL/POPULATION",
        "ALL/WIDE_BACKGROUND",
        "ALL/3D/DEM",
        # "ALL/EX_INFO/HTML"
    ]
    JUNCTION_VIEW_SPECIFIED_LIST = ["ALL/GS_NEW", "ALL/RFSP_BMP"]
    LANDMARK_DATA_SPECIFIED_PATH = ["ALL/3DOBJECT"]

    ALL_DATA_NAME = "all data"
    JUNCTION_VIEW_DATA_NAME = "junction view data"
    LANDMARK_DATA_NAME = "land mark data"

    EXTRACT_SPECIFIED_MAP = {
        ALL_DATA_NAME: SpecifiedStructure(ALL_FILE_NAME_LIKE, "ROOT", ALL_DATA_SPECIFIED_LIST),
        JUNCTION_VIEW_DATA_NAME: SpecifiedStructure(ALL_FILE_NAME_LIKE, "ROOT", JUNCTION_VIEW_SPECIFIED_LIST),
        LANDMARK_DATA_NAME: SpecifiedStructure(ALL_FILE_NAME_LIKE, "ROOT", LANDMARK_DATA_SPECIFIED_PATH)
    }

    JUNCTION_VIEW_TAR_FILE = "junctionview.tar.gz"
    JUNCTION_VIEW_DATA_MOVE_FROM = ["ROOT/ALL/GS_NEW", "ROOT/ALL/RFSP_BMP"]
    JUNCTION_VIEW_TAR_FROM = ["GS_NEW/", "RFSP_BMP/"]

    LANDMARK_ZIP_FILE = "3DOBJECT.zip"
    LANDMARK_ZIP_FROM = "ALL/3DOBJECT"

    WOCEAN_DATA_TO = "ROOT/ALL/WIDE_BACKGROUND"
    WOCEAN_DATA_LIKE = ["Wocean", u"世界图", 'Snowman']

    TMC_DATA_LIKE = ["TMC"]
    TMC_DATA_TO = "ROOT/TRAFFICINFO_TEMP"
    TMC_DATA_MOVE_LIKE = 'TRAFFICINFO'
    TMC_DATA_MOVE_TO = "ROOT"

    TOLL_COST_DATA_LIKE = ["CHARGEINFO"]
    TOLL_COST_DATA_TO = "ROOT"

    VUI_DATA_LIKE = ["VUI"]
    VUI_DATA_TO = None
    VUI_DATA_MOVE_TO = "ROOT/NDS"
    VUI_DATA_MOVE_FROM = "VUI/NaviDataVUI/CHN"

    WOCEAN_DATA_NAME = "WOcean data"
    TMC_DATA_NAME = "TMC data"
    TOLL_COST_DATA_NAME = "toll cost data"
    VUI_DATA_NAME = "VUI data"

    STRUCTURE_CHECKER_BASE = "ROOT"
    STRUCTURE_CHECKER_DEEP = 2
    STRUCTURE_CHECKER_FILE = os.path.join(ROOT_DIRECTORY, "data_format.json")
    SAVE_PATH_PREFIX = r'/var/www/html/data'
    SAVE_DATA_NAME_PREFIX = "cn_axf"
    JUNCTION_TAR_SAVE_PATH_SUFFIX = r'components/junction_view'
    LANDMARK_SAVE_PATH_SUFFIX = r'components/3dlandmark_vendor'

    FuzzyMatchStructureMAP = {
        WOCEAN_DATA_NAME: FuzzyMatchStructure(WOCEAN_DATA_TO, like_list=WOCEAN_DATA_LIKE),
        TMC_DATA_NAME: FuzzyMatchStructure(TMC_DATA_TO, like_list=TMC_DATA_LIKE),
        TOLL_COST_DATA_NAME: FuzzyMatchStructure(TOLL_COST_DATA_TO, like_list=TOLL_COST_DATA_LIKE),
        VUI_DATA_NAME: FuzzyMatchStructure(VUI_DATA_TO, like_list=VUI_DATA_LIKE)
    }

    def __init__(self, base_dir):
        self.base_dir = base_dir

        self.checker_data()

    def checker_data(self):
        """
        checker the need file
        list:
        MESH_DATA = "ROOT/MESH" not empty
        ALL_DATA_FILE = "ROOT/ALL.rar"  exist

        :return:
        """
        standout_print("check mesh data")
        self._find_mesh_data()

        standout_print("check all data")
        self._find_all_data()

        standout_print("check other data")
        self._find_fuzzy_match_data()

    def do_prepared(self, mesh_data=1, all_data=1, junction_view=1, landmark_data=1, tmc_data=1, toll_cost_data=1, voice_data=1, wocean_data=1, after_prepared=1, checker_final_structure=1):
        """
        judgement parameters

        :param mesh_data:
        :param all_data:
        :param junction_view:
        :param landmark_data:
        :param tmc_data:
        :param toll_cost_data:
        :param voice_data:
        :param wocean_data: no need wocean data update here
        :param after_prepared:
        :param checker_final_structure
        :return:
        """
        if mesh_data:
            self._mesh_data()
        if all_data:
            self._all_data()
        if junction_view:
            self._junction_view_data()
        if landmark_data:
            self._landmark_data()

        if tmc_data:
            self._tmc_data()
        if toll_cost_data:
            self._toll_cost_data()
        if voice_data:
            self._voice_data()
        # wocean is no need update, use 16Q2 as format because white line.
        if wocean_data:
            pass
        # self._wocean_data()
        if after_prepared:
            self._after_prepared()
        if checker_final_structure:
            if self._checker_final_structure():
                self.data_move()

    def data_move(self):
        """
        move junctionview.tar.gz to /var/www/html/data/CN_AXF_17Q2/components/junction_vie
        move 3DOBJECT.zip to /var/www/html/data/CN_AXF_17Q2/components/3dlandmark_vendor
        :return:
        """
        data_version = get_version(self.base_dir)
        data_save_path = os.path.join(self.SAVE_PATH_PREFIX, ('%s_%s' % (self.SAVE_DATA_NAME_PREFIX, data_version)).upper())
        junction_view_destination = os.path.join(data_save_path, self.JUNCTION_TAR_SAVE_PATH_SUFFIX)
        landmark_destination = os.path.join(data_save_path, self.LANDMARK_SAVE_PATH_SUFFIX)
        # 1. move junction view
        # /var/www/html/data/schema(cn_axf_17q2)/components/
        standout_print("move junction view data to [%s]." % junction_view_destination)
        junction_view_data_name = self.JUNCTION_VIEW_DATA_NAME
        junction_view_specified = self.EXTRACT_SPECIFIED_MAP[junction_view_data_name]
        junction_base_path = junction_view_specified.base_path
        junction_file_path = os.path.join(self.base_dir, junction_base_path, self.JUNCTION_VIEW_TAR_FILE)
        if not os.path.exists(junction_file_path) or (not os.path.exists(junction_view_destination)):
            error_out_print(" move junction view data failed.[%s] or destination directory[%s]not exist." % (junction_file_path, junction_view_destination))
        move_directory(junction_file_path, junction_view_destination)
        standout_print("move junction view data to [%s] finished." % junction_view_destination)
        # 2. landmark_data junction_view
        standout_print("move landmark data to [%s]." % landmark_destination)
        landmark_data_name = self.LANDMARK_DATA_NAME
        landmark_specified = self.EXTRACT_SPECIFIED_MAP[landmark_data_name]
        landmark_base_path = landmark_specified.base_path
        landmark_file_path = os.path.join(self.base_dir, landmark_base_path)
        if not os.path.exists(landmark_file_path) or (not os.path.exists(landmark_destination)):
            error_out_print(" move landmark data failed. file [%s] or destination directory[%s]not exist." % (landmark_file_path, landmark_destination))
        move_directory(landmark_file_path, landmark_destination)
        standout_print("move landmark data to [%s] finished." % landmark_destination)

    def decompression_fuzzy_match(self, data_name):
        """
        1. find file through like str
        2. unrar this search file
        :param data_name:
        :return:
        """
        fuzzy_match_object = self.FuzzyMatchStructureMAP[data_name]
        destination_path = fuzzy_match_object.destination_path
        like_list = fuzzy_match_object.like_list

        selected_file = None
        # 1. find rar file in this list
        for like_str in like_list:
            selected_file = self.find_file(like_str)
            if selected_file:
                break

        if not selected_file:
            error_out_print(" can not find %s. like str is [%s]" % (data_name, like_list))
            sys.exit(-1)
        selected_file = os.path.join(self.base_dir, selected_file)
        # 2. unrar
        if not destination_path:
            destination_path = self.base_dir
        else:
            destination_path = os.path.join(self.base_dir, destination_path)
        DecompressionModel.decompression(selected_file, destination_path)

        standout_print("unrar %s finished. to path [%s]" % (data_name, destination_path))

    def decompression_specified_directory(self, data_name):
        """
        decompression rar file extract specified directory
        by object SpecifiedStructure
        :param data_name: type of data
        :return:
        """
        specified_structure = self.EXTRACT_SPECIFIED_MAP[data_name]
        filename_like = specified_structure.rar_file
        rar_file = self.find_file(file_like=filename_like)

        base_path = specified_structure.base_path
        specified_list = specified_structure.specified_list

        # rar_file = os.path.join(self.base_dir, rar_file)
        destination_path = os.path.join(self.base_dir, base_path)

        DecompressionModel.decompression(rar_file, destination_path, specified_list)
        # self.decompression_unrar(rar_file=rar_file, specified_list=specified_list, base_path=destination_path)

        standout_print("unrar %s finished. to path[%s]" % (data_name, destination_path))

    def _all_data(self):
        all_data_name = self.ALL_DATA_NAME
        self.decompression_specified_directory(all_data_name)

    def _landmark_data(self):

        # 1. rar
        landmark_data_name = self.LANDMARK_DATA_NAME
        landmark_specified = self.EXTRACT_SPECIFIED_MAP[landmark_data_name]
        self.decompression_specified_directory(landmark_data_name)
        # 2. zip
        base_path = landmark_specified.base_path
        base_path = os.path.join(self.base_dir, base_path)
        # os.chdir(base_path)
        # zip_cmd = "zip -r %s %s" % (self.LANDMARK_ZIP_FILE, self.LANDMARK_ZIP_FROM)
        # execute_cmd(zip_cmd)
        make_zip(self.LANDMARK_ZIP_FROM, self.LANDMARK_ZIP_FILE, base_path)
        standout_print("unrar and zip landmark data finished. to file [%s] in base directory[%s]" % (self.LANDMARK_ZIP_FILE, base_path))

    def _junction_view_data(self):

        # 1. rar
        junction_view_data_name = self.JUNCTION_VIEW_DATA_NAME
        junction_view_specified = self.EXTRACT_SPECIFIED_MAP[junction_view_data_name]
        self.decompression_specified_directory(junction_view_data_name)

        # 2. mv directory GS_NEW RFSP_BMP from ALL to ROOT
        base_path = junction_view_specified.base_path
        destination_path = os.path.join(self.base_dir, base_path)
        for from_path in self.JUNCTION_VIEW_DATA_MOVE_FROM:
            from_path = os.path.join(self.base_dir, from_path)
            to_path = destination_path
            move_directory(from_path, to_path)

        standout_print("move junction view data finished.")

        # 3. tar
        make_targz(tar_from_path_list=self.JUNCTION_VIEW_TAR_FROM, tar_to_file_path=self.JUNCTION_VIEW_TAR_FILE, base_dir=destination_path)
        # 4 remove
        for tar_from in self.JUNCTION_VIEW_TAR_FROM:
            tar_from_path = os.path.join(destination_path, tar_from)
            remove_dirs(tar_from_path)

        standout_print("tar [%s] and rm[%s] success." % (self.JUNCTION_VIEW_TAR_FILE, self.JUNCTION_VIEW_TAR_FROM))

    def _wocean_data(self):
        """

        :return:
        """
        data_name = self.WOCEAN_DATA_NAME
        self.decompression_fuzzy_match(data_name)
        # there is a directory in WOCEAN_DATA_TO directory
        # but we need files in this directory, should move these files to WOCEAN_DATA_TO
        # mv
        wocean_destination_path = os.path.join(self.base_dir, self.WOCEAN_DATA_TO)
        wocean_destination_path = wocean_destination_path.replace("\\", "/")
        file_list = os.listdir(path_to_unicode(wocean_destination_path))
        for file_name in file_list:
            dir_path = os.path.join(wocean_destination_path, file_name)
            if os.path.isdir(dir_path):
                file_list = os.listdir(dir_path)
                for filename in file_list:
                    file_path = os.path.join(dir_path, filename)
                    move_directory(from_path=file_path, to_path=wocean_destination_path)
                standout_print("mv files from [%s] to [%s] finish." % (path_to_str(dir_path), wocean_destination_path))
                remove_dirs(dir_path)

    def _tmc_data(self):
        # 1. decompression
        data_name = self.TMC_DATA_NAME
        self.decompression_fuzzy_match(data_name)
        # in TRAFFICINFO_TEMP mv files in TRAFFICINFO to ROOT
        # 2. find TRAFFICINFO in TRAFFICINFO_TEMP
        tmc_search_base_path = os.path.join(self.base_dir, self.TMC_DATA_TO)
        tmc_move_from = self.find_directory(self.TMC_DATA_MOVE_LIKE, tmc_search_base_path)
        # 3. mv
        tmc_move_to_path = os.path.join(self.base_dir, self.TMC_DATA_MOVE_TO)
        move_directory(tmc_move_from, tmc_move_to_path)
        # 4. remove
        remove_dirs(tmc_search_base_path)

    def _voice_data(self):
        # 1. decompression
        data_name = self.VUI_DATA_NAME
        self.decompression_fuzzy_match(data_name)
        # 2. move files to ROOT/NDS
        # files in VUI/NaviDataVUI/CHN, not poi data
        path_vui_from = os.path.join(self.base_dir, self.VUI_DATA_MOVE_FROM)
        path_vui_to = os.path.join(self.base_dir, self.VUI_DATA_MOVE_TO)
        for file_name in os.listdir(path_vui_from):
            file_name_path = os.path.join(path_vui_from, file_name)
            # only move files , not poi data
            if os.path.isfile(file_name_path):
                move_directory(file_name_path, path_vui_to)
        # 3. remove
        remove_dirs(path_vui_from)

    def _toll_cost_data(self):
        data_name = self.TOLL_COST_DATA_NAME
        self.decompression_fuzzy_match(data_name)

    def _find_mesh_data(self):
        mesh_data_path = self.find_directory(self.MESH_DATA_DIC_LIKE)
        if not check_directory(mesh_data_path):
            error_out_print("MESH data[%s] have no files. please check." % mesh_data_path)
            sys.exit(-1)
        return mesh_data_path

    def _find_fuzzy_match_data(self):
        selected_file_list = []
        for data_name in PreparedDataDecompression.FuzzyMatchStructureMAP.keys():
            fuzzy_struc = PreparedDataDecompression.FuzzyMatchStructureMAP[data_name]
            like_list = fuzzy_struc.like_list

            selected_file = None
            for like_str in like_list:
                selected_file = self.find_file(like_str)
                if selected_file:
                    break
            if not selected_file:
                error_out_print(" check data failed. match file str %s of %s" % (like_list, data_name))
                sys.exit(-1)
            selected_file_list.append(selected_file)
        return selected_file_list

    def _find_all_data(self):
        all_file = self.find_file(self.ALL_FILE_NAME_LIKE)
        if not os.path.exists(all_file):
            error_out_print("all rar[%s] is not exist. please check." % all_file)
            sys.exit(-1)

        return all_file

    def _mesh_data(self):
        """
        cd 17Q2_A5_20170630/ROOT/MESH;
         For i in `ls`; do unrar x $i; done;
        :return:
        """
        # data_path = os.path.join(self.base_dir, self.MESH_DATA)
        data_path = self._find_mesh_data()
        files = os.listdir(data_path)
        rar_files = []
        for f in files:
            if f.endswith(self.MESH_DATA_SUFFIX):
                rar_path = os.path.join(data_path, f)
                rar_files.append(rar_path)

        for rar_file in rar_files:
            # self.rar_decompression(rar_file, None, data_path)
            # self.decompression_unrar(rarfile, None, data_path)
            # self.decompression_unrar(rar_file, None, data_path)
            #
            DecompressionModel.decompression(rar_file, data_path)

            remove_file(rar_file)

        standout_print("unrar MESH data finished. to path [%s]" % data_path)
        # move mesh data
        move_mesh_data_to_path = os.path.join(self.base_dir, self.MESH_DATA_MOVE_TO)
        move_directory(data_path, move_mesh_data_to_path)
        standout_print("move mesh to [%s] finished." % move_mesh_data_to_path)

    def _after_prepared(self):
        """
        at the end of data prepared
        1. remove some rar file
        2. tar.gz the prepared data
        3. cp to the specified directory

        tip:
        must add judgement of this back file, if exist use this back file, if not do this complex decompression

        :return:
        """
        # 1.1 remove mesh data in unrar mesh data
        mesh_data_directory = self._find_mesh_data()
        mesh_files = os.listdir(mesh_data_directory)
        for mesh_file in mesh_files:
            if mesh_file.endswith(".rar"):
                remove_file(os.path.join(mesh_data_directory, mesh_file))
        # 1.2 remove all.rar
        all_data_path = self.find_file(self.ALL_FILE_NAME_LIKE)
        remove_file(all_data_path)
        # 1.3 remove the other fuzzy match rar file
        fuzzy_match_selected_list = self._find_fuzzy_match_data()
        for selected_file in fuzzy_match_selected_list:
            remove_file(selected_file)
            # 2. check the result structure is or not right

    def _checker_final_structure(self):
        """
        check the structure
        compare the format structure with the decompress generate structure
        :return:
        """
        standout_print("check final decompress directory is or not match...")
        # 1. format structure
        format_structure_dic = load_directory_json(self.STRUCTURE_CHECKER_FILE)
        # 2. generate structure
        structure_dic_path = os.path.join(self.base_dir, self.STRUCTURE_CHECKER_BASE)
        generate_structure_dic = parse_path(structure_dic_path, self.STRUCTURE_CHECKER_DEEP)
        # 3. compare
        compare_result = compare_dic_ge(generate_structure_dic, format_structure_dic)
        if not compare_result:
            error_out_print(" decompress directory [%s] " % generate_structure_dic)
            error_out_print(" in path[%s]" % structure_dic_path)
            error_out_print(" is not match the format structure[%s]. please have a check" % format_structure_dic)
            sys.exit(-1)
        standout_print("check final decompress directory is match. can continue")
        return True

    def find_file(self, file_like):
        """
        in base dir and base/ROOT dir find file which like file_like
        :param file_like: the str of fuzzy match
        :return:
        return the selected file
        """

        selected_file = None
        for parent, dirs, files in os.walk(path_to_unicode(self.base_dir)):
            for f in files:
                if f.find(file_like) != -1:
                    selected_file = os.path.join(parent, f)
                    break
            if selected_file:
                break
        if not selected_file:
            standout_print("can not find filename like[%s]" % file_like)
        return selected_file

    def find_directory(self, dir_like, search_path=None):
        if not search_path:
            search_path = self.base_dir
        selected_dir = None
        base_path = path_to_unicode(search_path)
        for parent, dirs, files in os.walk(base_path):
            for dir_name in dirs:
                if dir_name.find(dir_like) != -1:
                    selected_dir = os.path.join(parent, dir_name)
                    break
            if selected_dir:
                break

        if not selected_dir:
            error_out_print(" can not find filename like[%s]" % selected_dir)
        return selected_dir


class DecompressionModel:
    def __init__(self):
        pass

    @staticmethod
    def decompression(rar_file, destination_path, specified_list=None, use_command=1):
        """

        :param rar_file: abstract path of rar_file
        :param specified_list: the specified directory list
        :param destination_path: destination path for unrar
        :param use_command: if use shell command to execute decompression, if not use package of python(rarfile,)
        :return:
        """
        # DecompressionModel._rar_decompression_command(rarfile, specified_list, base_path)
        rar_file = path_to_unicode(rar_file)

        if rar_file.endswith(".rar"):
            if not use_command:
                DecompressionModel._rar_decompression_unrar(rar_file, specified_list, destination_path)
            else:
                DecompressionModel._rar_decompression_command(rar_file, specified_list, destination_path)
        else:
            if rar_file.endswith(".zip"):
                DecompressionModel._zip_decompression(rar_file, specified_list, destination_path)
            else:
                error_out_print(" decompression file [%s] is not zip or rar file. please have a check." % rar_file)
                sys.exit(-1)

    @staticmethod
    def _zip_decompression(zip_file, specified_list, destination_path):
        zip_decompression(zip_file, destination_path, specified_list)

    @staticmethod
    def _rar_decompression_command(rar_file, specified_list, destination_path):
        standout_print("decompression use command.rar file [%s],specified list %s, in base path[%s]" % (path_to_str(rar_file), specified_list, path_to_str(destination_path)))
        if specified_list:
            for specified_directory in specified_list:
                DecompressionModel._unrar_command(rar_file, specified_directory, destination_path)
        else:
            DecompressionModel._unrar_command(rar_file, None, destination_path)

    @staticmethod
    def _rar_decompression_unrar(rar_file, specified_list, destination_path):
        standout_print("decompression use unrar package. rar file [%s],specified list %s, in base path[%s]" % (path_to_str(rar_file), specified_list, destination_path))
        rar_file = rar_file.replace("\\", "/")
        destination_path = destination_path.replace("\\", "/")

        if not os.path.exists(rar_file) or rar_file.find(".rar") == -1:
            error_out_print(" rar file not exist or this file is not rar file.[%s] " % path_to_str(rar_file))
            sys.exit(-1)

        unrar_model = UNRARModel(rar_filename=rar_file, to_path=destination_path)

        if specified_list:
            unrar_model.decompression_list(specified_list)
        else:
            unrar_model.decompression_file()
        standout_print("unrar file done.from [%s] to [%s]." % (path_to_str(rar_file), destination_path))
        if specified_list:
            standout_print("the specified directory is [%s]" % specified_list)

    @staticmethod
    def _unrar_command(rar_file, specified_directory, base_path):
        rar_file = path_to_str(rar_file)
        if not os.path.exists(rar_file) or (not rar_file.endswith(".rar")):
            error_out_print(" rar file not exist.[%s] or is not a rar file. please have a check" % path_to_str(rar_file))
            sys.exit(-1)

        if not os.path.exists(base_path):
            standout_print("Failed: rar decompression base path[%s] not exist." % base_path)
            os.makedirs(base_path)
            # sys.exit(-1)

        os.chdir(base_path)
        temp_dir = None
        if specified_directory:
            # unrar extract the specified directory
            # if the specified directory exist, it will full decompression, but we want partly
            # 1. create temp
            if os.path.exists(specified_directory):
                temp_dir = os.path.join(base_path, str(time()))
                os.chdir(temp_dir)
            # 2. unrar
            cmd = "unrar x -y %s %s>/dev/null 2>&1" % (path_to_str(rar_file), specified_directory)
        else:
            # unrar this rar files
            cmd = "unrar x -y %s>/dev/null 2>&1" % path_to_str(rar_file)
        standout_print("base dir [%s]" % os.path.abspath(os.curdir))
        execute_cmd(cmd)
        # after unrar remove ,rar file
        # remove_file(rar_file)
        if temp_dir:
            for file_name in os.listdir(os.path.join(temp_dir, specified_directory)):
                # move files in tmp_path/specified_directory to to_path
                from_path = os.path.join(temp_dir, specified_directory, file_name)
                to_path = os.path.join(base_path, specified_directory)
                move_directory(from_path, to_path)
            remove_dirs(temp_dir)


class UNRARModel:
    def __init__(self, rar_filename, to_path):
        self.rar_file = rar_filename
        self.to_path = to_path
        self.infolist = None
        self.rar_obj = None

        self.init()

    def init(self):
        self.rar_obj = rarfile.RarFile(path_to_unicode(self.rar_file))
        self.infolist = self.rar_obj.infolist()

    def _extract_list(self, selected_dir):
        """
        use rarfile decompression specified directory must give the full name of file
        like unrar ALL.rar ALL/EX_INFO/SCENICROUT is wrong here,
        must :
        1. find files which in ALL/EX_INFO/SCENICROUT
        2. get these files name and return
        :param selected_dir:
        :return:
        """
        selected_infolist = []
        for d in selected_dir:
            for info in self.infolist:
                filename = info.filename.replace("\\", "/")  # in win
                if filename.find(d) != -1 and info.file_size != 0L:
                    selected_infolist.append(info)

        return selected_infolist

    def decompression_list(self, selected_dir):
        """
        extract the Specified directory
        :param selected_dir: Specified directory
        :return:
        """
        selected_infolist = self._extract_list(selected_dir)
        for member in selected_infolist:
            self.rar_obj.extract(path=self.to_path, member=member)

    def decompression_file(self):
        # for info in self.infolist:
        #     filename = info.filename
        #     self.rar_obj.extract(filename, path=self.to_path)
        self.rar_obj.extractall(path=self.to_path)


if __name__ == '__main__':
    data_from_directory = r"D:\test_temp\tmp_autonav"
    data_base_dir = os.path.join(data_from_directory, "17Q2_A5_20170630")
    pd = PreparedDataDecompression(data_base_dir)
    pd.do_prepared(mesh_data=0, all_data=0, junction_view=0, landmark_data=0, tmc_data=0, toll_cost_data=0, voice_data=0, wocean_data=1, after_prepared=0)
    # pd.data_move()
