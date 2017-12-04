# coding=utf-8

import os
import sys
from components import standout_print, error_out_print, remove_file, check_directory, execute_cmd, move_directory


class SpecifiedStructure:
    """
    the structure for specified directory
    extract the specified directory
    """

    def __init__(self, rar_file, base_path, specified_list):
        self.rar_file = rar_file
        self.base_path = base_path
        self.specified_list = specified_list


class FuzzyMatchStructure:
    """
    destination_path : base dir,zip file destination
    like_list : only if match one file in this list, return
    """

    def __init__(self, destination_path, like_list):
        self.destination_path = destination_path
        self.like_list = like_list


class PreparedDataDecompression:
    """
    unrar x xx.rar topath(destination)
    or
    unrar x aa.rar specified_directory(destination is :pwd )

    """
    MESH_DATA = "ROOT/MESH"
    MESH_DATA_SUFFIX = '.rar'

    ALL_FILE_NAME = "ROOT/ALL.rar"

    ALL_DATA_SPECIFIED_LIST = [
        "ALL/EX_INFO/SCENICROUT",
        "ALL/HIGHWAY",
        "ALL/HS",
        "ALL/POPULATION",
        "ALL/WIDE_BACKGROUND",
        "ALL/3D/DEM",
    ]
    JUNCTION_VIEW_SPECIFIED_LIST = ["ALL/GS_NEW", "ALL/RFSP_BMP"]
    LANDMARK_DATA_SPECIFIED_PATH = ["ALL/3DOBJECT"]

    ALL_DATA_NAME = "all data"
    JUNCTION_VIEW_DATA_NAME = "junction view data"
    LANDMARK_DATA_NAME = "land mark data"

    EXTRACT_SPECIFIED_MAP = {
        ALL_DATA_NAME: SpecifiedStructure(ALL_FILE_NAME, "ROOT", ALL_DATA_SPECIFIED_LIST),
        JUNCTION_VIEW_DATA_NAME: SpecifiedStructure(ALL_FILE_NAME, "ROOT", JUNCTION_VIEW_SPECIFIED_LIST),
        LANDMARK_DATA_NAME: SpecifiedStructure(ALL_FILE_NAME, "ROOT", LANDMARK_DATA_SPECIFIED_PATH)
    }

    JUNCTION_VIEW_TAR_FILE = "junctionview.tar.gz"
    JUNCTION_VIEW_DATA_MOVE_FROM = ["ROOT/ALL/GS_NEW", "ROOT/ALL/RFSP_BMP"]
    JUNCTION_VIEW_TAR_FROM = "GS_NEW/ RFSP_BMP/"

    LANDMARK_ZIP_FILE = "3DOBJECT.zip"
    LANDMARK_ZIP_FROM = "ALL/3DOBJECT"

    WOCEAN_DATA_TO = "ROOT/ALL/WIDE_BACKGROUND"
    WOCEAN_DATA_LIKE = ["Wocean", u"世界图"]

    TMC_DATA_LIKE = ["TMC"]
    TMC_DATA_TO = "trafficinfo"

    TOLL_COST_DATA_LIKE = ["CHARGEINFO"]
    TOLL_COST_DATA_TO = None

    VUI_DATA_LIKE = ["VUI"]
    TOLL_COST_DATA_TO = None

    WOCEAN_DATA_NAME = "WOcean data"
    TMC_DATA_NAME = "TMC data"
    TOLL_COST_DATA_NAME = "toll cost data"
    VUI_DATA_NAME = "VUI data"

    FuzzyMatchStructureMAP = {
        WOCEAN_DATA_NAME: FuzzyMatchStructure(WOCEAN_DATA_TO, like_list=WOCEAN_DATA_LIKE),
        TMC_DATA_NAME: FuzzyMatchStructure(TMC_DATA_TO, like_list=TMC_DATA_LIKE),
        TOLL_COST_DATA_NAME: FuzzyMatchStructure(TOLL_COST_DATA_TO, like_list=TOLL_COST_DATA_LIKE),
        VUI_DATA_NAME: FuzzyMatchStructure(TOLL_COST_DATA_TO, like_list=VUI_DATA_LIKE)
    }

    ROOT_PATH = "ROOT"

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
        standout_print("Info: check mesh data")
        mesh_data = os.path.join(self.base_dir, self.MESH_DATA)
        if not check_directory(mesh_data):
            error_out_print("MESH data[%s] have no files. please check." % mesh_data)
            sys.exit(-1)

        standout_print("Info: check all data")
        all_file = os.path.join(self.base_dir, self.ALL_FILE_NAME)
        if not os.path.exists(all_file):
            error_out_print("all rar[%s] is not exist. please check." % all_file)
            sys.exit(-1)

        standout_print("Info: check other data")
        for data_name in PreparedDataDecompression.FuzzyMatchStructureMAP.keys():
            fuzzy_struc = PreparedDataDecompression.FuzzyMatchStructureMAP[data_name]
            destination_path = fuzzy_struc.destination_path
            like_list = fuzzy_struc.like_list

            selected_file = None
            for like_str in like_list:
                selected_file = self.find_file(like_str)
                if selected_file:
                    break
            if not selected_file:
                error_out_print("Error: check data failed. match file str %s of %s" % (like_list, data_name))
                sys.exit(-1)

        pass

    def do_prepared(self, mesh_data=1, all_data=1, junction_view=1, landmark_data=1, tmc_data=1, toll_cost_data=1, voice_data=1, wocean_data=1):
        """
        judgement parameters

        :param mesh_data:
        :param all_data:
        :param junction_view:
        :param landmark_data:
        :param tmc_data:
        :param toll_cost_data:
        :param voice_data:
        :param wocean_data:
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
        if wocean_data:
            self._wocean_data()

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
            error_out_print("Error: can not find %s. like str is [%s]" % (data_name, like_str))
            sys.exit(-1)

        # 2. unrar
        if not destination_path:
            destination_path = self.base_dir
        else:
            destination_path = os.path.join(self.base_dir, destination_path)

        self.rar_decompression(selected_file, None, destination_path)
        standout_print("Info: unrar %s finished. to path [%s]" % (data_name, destination_path))

    def decompression_specified_directory(self, data_name):
        """
        decompression rar file extract specified directory
        by object SpecifiedStructure
        :param specifiedStructure:
        :return:
        """
        specifiedStructure = self.EXTRACT_SPECIFIED_MAP[data_name]
        rar_file = specifiedStructure.rar_file
        base_path = specifiedStructure.base_path
        specified_list = specifiedStructure.specified_list

        rar_file = os.path.join(self.base_dir, rar_file)
        destination_path = os.path.join(self.base_dir, base_path)

        for specified_directory in specified_list:
            # specified_directory = os.path.join(self.base_dir, specified_directory)
            self.rar_decompression(rar_file, specified_directory, destination_path)

        standout_print("Info: unrar %s finished. to path[%s]" % (data_name, destination_path))

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
        os.chdir(base_path)
        zip_cmd = "zip -r %s %s" % (self.LANDMARK_ZIP_FILE, self.LANDMARK_ZIP_FROM)
        execute_cmd(zip_cmd)
        standout_print("unrar and zip landmark data finished. to file [%s] in base directory[%s]" % (self.LANDMARK_ZIP_FILE, base_path))

    def _junction_view_data(self):

        # 1. rar
        junction_view_data_name = self.JUNCTION_VIEW_DATA_NAME
        junction_view_specified = self.EXTRACT_SPECIFIED_MAP[junction_view_data_name]
        self.decompression_specified_directory(junction_view_data_name)

        # 2. mv
        base_path = junction_view_specified.base_path
        destination_path = os.path.join(self.base_dir, base_path)
        for from_path in self.JUNCTION_VIEW_DATA_MOVE_FROM:
            from_path = os.path.join(self.base_dir, from_path)
            move_directory(from_path, destination_path)
        standout_print("Info: mv junction view finished")

        # 3. tar
        os.chdir(destination_path)
        tar_cmd = "tar -czf %s %s" % (self.JUNCTION_VIEW_TAR_FILE, self.JUNCTION_VIEW_TAR_FROM)
        self.execute_cmd(tar_cmd)
        rm_cmd = "rm -rf %" % self.JUNCTION_VIEW_TAR_FROM
        standout_print("Info: tar [%s] and rm[%s] success." % (self.JUNCTION_VIEW_TAR_FILE, self.JUNCTION_VIEW_TAR_FROM))

    def _wocean_data(self):
        data_name = self.WOCEAN_DATA_NAME
        self.decompression_fuzzy_match(data_name)

    def _tmc_data(self):
        data_name = self.TMC_DATA_NAME
        self.decompression_fuzzy_match(data_name)

    def _voice_data(self):
        data_name = self.VUI_DATA_NAME
        self.decompression_fuzzy_match(data_name)

    def _toll_cost_data(self):
        data_name = self.TOLL_COST_DATA_NAME
        self.decompression_fuzzy_match(data_name)

    def _mesh_data(self):
        """
        cd 17Q2_A5_20170630/ROOT/MESH;
         For i in `ls`; do unrar x $i; done;
        :return:
        """
        data_path = os.path.join(self.base_dir, self.MESH_DATA)

        files = os.listdir(data_path)
        rar_files = []
        for file in files:
            if file.endswith(self.MESH_DATA_SUFFIX):
                rar_path = os.path.join(data_path, file)
                rar_files.append(rar_path)
                # rar_decompression(rar_path, data_path)

        for rar_file in rar_files:
            self.rar_decompression(rar_files, None, data_path)

        standout_print("Info: unrar MESH data finished. to path [%s]" % data_path)

    @staticmethod
    def rar_decompression(self, rar_file, specified_directory, base_path):
        if not os.path.exists(base_path):
            error_out_print("Error: rar decompression failed, base path[%s] not exist." % base_path)
            sys.exit(-1)

        if not os.path.exists(rar_file):
            error_out_print("Error: rar file not exist.[%s] " % rar_file)
            sys.exit(-1)

        os.chdir(base_path)
        if specified_directory:
            # unrar extract the specified directory
            cmd = "unrar x %s %s" % (rar_file, specified_directory)
        else:
            # unrar this rar files
            cmd = "unrar x %s" % rar_file

        execute_cmd(cmd)
        # after unrar remove ,rar file
        remove_file(rar_file)

    def find_file(self, file_like):
        """
        in base dir and base/ROOT dir find file which like file_like
        :param base_dir:
        :param file_suffix:
        :return:
        return the selected file
        """
        file_list = os.listdir(self.base_dir)

        selected_file = None
        for fl in file_list:
            fl = fl.decode("gbk").encode("utf-8")
            if fl.find(file_like) != -1:
                selected_file = fl
                break
        root_path = os.path.join(self.base_dir, self.ROOT_PATH)
        root_files = os.listdir(root_path)
        if not selected_file:
            for fl in root_files:
                fl = fl.decode("gbk").encode("utf-8")
                if fl.find(file_like) != -1:
                    selected_file = os.path.join(self.ROOT_PATH, fl)
                    break
            if not selected_file:
                sys.stderr.write("Error: can not find file %s in directory %s,%s" % (file_like, self.base_dir, root_path))
                sys.stderr.write("Error: voice data is not exist. file like *_VUI.rar")

                return None

        return selected_file


if __name__ == '__main__':
    tmp_path = r"D:\test_temp\tmp_autonav"
    base_path = os.path.join(tmp_path, "17Q2_A5_20170630")
    pd = PreparedDataDecompression(base_path)
    pd.do_prepared()
