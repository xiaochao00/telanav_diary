# coding=utf-8
import sys
import os
import shutil
import zipfile
import tarfile


def standout_print(info):
    """
    print information to standout
    :param info:
    :return:
    """
    if type(info) == unicode:
        info = info.encode("utf-8")
    sys.stdout.write("%s" % info)
    sys.stdout.write("\n")
    sys.stdout.flush()


def error_out_print(info):
    """
    print error message
    :param info:
    :return:
    """
    if type(info) == unicode:
        info = info.encode("utf-8")
    sys.stderr.write(info)
    sys.stderr.write("\n")
    sys.stderr.flush()


def remove_file(file_path):
    """
    remove file
    :param file_path:
    :return:
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        standout_print("Info: remove files %s finish." % file_path)
    else:
        error_out_print("Error: remove file not exist.[%s]" % file_path)
        sys.exit(-1)


def remove_dirs(dir_path):
    dir_path = dir_path.replace("\\", "/")
    dir_path = path_to_unicode(dir_path)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
        standout_print("Info: remove directory %s finish." % dir_path)
    else:
        error_out_print("Error: remove directory not exist.[%s]" % dir_path)
        sys.exit(-1)


def check_directory(dic_path):
    """
    check this directory is empty or not
    :param dic_path:
    :return:
    """
    if not os.path.exists(dic_path):
        return False

    if not os.listdir(dic_path):
        return False

    return True


def execute_cmd(cmd):
    cmd = cmd.strip()
    standout_print("Info: execute command [ %s ] . " % cmd)
    result_statue = os.system(cmd)

    if not cmd and result_statue:
        error_out_print("Error: execute command [%s]. program stop" % cmd)
        sys.exit(-1)

    standout_print("Info: execute cmd[%s] success." % cmd)
    return True


# def move_directory(from_directory, to_directory):
#     if not os.path.exists(from_directory):
#         error_out_print("Error: mv directory is not exist. please check [%s]" % from_directory)
#         sys.exit(-1)
#
#     mv_cmd = "mv %s %s" % (from_directory,to_directory)
#     execute_cmd(mv_cmd)


def move_directory(from_path, to_path):
    """
    directory from_path `s basename
    move directory of from_path to to_path
    example:
    from_path = a/b
    move b/ and the files in b to to_path
    :param from_path:
    :param to_path:
    :return:
    """
    if not os.path.exists(from_path):
        error_out_print("Error: mv directory is not exist. please check [%s]" % path_to_str(from_path))
        sys.exit(-1)
    standout_print("Info: begin move files in [%s] to [%s] finished." % (path_to_str(from_path), path_to_str(to_path)))
    to_file = os.path.join(to_path, os.path.basename(from_path))
    if os.path.exists(to_file):
        if os.path.isdir(to_file):
            remove_dirs(to_file)
        if os.path.isfile(to_file):
            remove_file(to_file)
    if not os.path.exists(to_path):
        os.makedirs(to_path)
    if not os.path.isdir(to_path):
        error_out_print("Error: mv directory or file from [%s] to [%s] failed. destination path[%s] is not directory." % (path_to_str(from_path), path_to_str(to_path), path_to_str(to_path)))
        sys.exit(-1)
    shutil.move(from_path, to_path)
    standout_print("Info: move directory from[%s] to [%s] finished." % (path_to_str(from_path), path_to_str(to_path)))


def zip_decompression(zip_file, to_path, specified_list=None):
    #
    if not os.path.exists(zip_file):
        error_out_print("Error: zip file[ % ] is not exist." % zip_file)
        sys.exit(-1)
    if not zipfile.is_zipfile(zip_file):
        error_out_print("Error: zip file[  % ] is not a zip file. please check" % zipfile)
        sys.exit(-1)

    fz = zipfile.ZipFile(zip_file, "r")
    if not specified_list:
        specified_list = fz.namelist()

    for file_name in specified_list:
        fz.extract(file_name, to_path)
    standout_print("Info: zip decompress finish. file[%s] to [%s]." % (zip_file, to_path))


def make_targz(tar_from_path_list, tar_to_file_path, base_dir):
    standout_print("Info: tar gz data in %s to [%s], in basedir [%s]" % (tar_from_path_list, tar_to_file_path, base_dir))
    tar_to_file_path = os.path.join(base_dir, tar_to_file_path)
    tar_to_file_path = tar_to_file_path.replace("\\", "/")
    with tarfile.open(tar_to_file_path, "w:gz") as tar_file:
        for tar_from_path in tar_from_path_list:
            tar_from_path = os.path.join(base_dir, tar_from_path.strip())
            tar_from_path = tar_from_path.replace("\\", "/")
            arc_name = tar_from_path.replace(base_dir, "").strip(os.path.sep)
            tar_file.add(tar_from_path, arcname=arc_name)
        tar_file.close()
        standout_print("Info: tar directory %s to file [%s] finish." % (tar_from_path_list, tar_to_file_path))
        return

    standout_print("Error: tar directory %s to file [%s] failed. please have a check." % (tar_from_path_list, tar_to_file_path))
    sys.exit(-1)


def make_zip(zip_from_file_path, zip_to_file_path, base_dir):
    standout_print("Info: zip [%s] to file [%s] in path[%s]." % (zip_from_file_path, zip_to_file_path, base_dir))
    zip_to_file_path = os.path.join(base_dir, zip_to_file_path)
    zip_file = zipfile.ZipFile(zip_to_file_path, 'w', zipfile.ZIP_DEFLATED)

    data_path = os.path.join(base_dir, zip_from_file_path)
    data_path = data_path.replace("\\", "/")

    pre_len = len(data_path)
    for p, dirs, file_names in os.walk(data_path):
        for filename in file_names:
            file_path = os.path.join(p, filename).replace("\\", "/")
            arc_name = file_path[pre_len:].strip(os.path.sep)
            zip_file.write(file_path, arc_name)

    zip_file.close()
    standout_print("Info: finish zip.")


def path_to_unicode(path_name, coding="utf-8"):
    """
    this method use to find file or directory which contains chinese
    if not use this transform
    os.listdir(path) and os.walk() will wrong in window platform
    :param path_name: name of path
    :param coding:
    :return:
    """
    if not type(path_name) == unicode:
        return unicode(path_name, coding)
    return path_name


def path_to_str(path_name, coding="utf-8"):
    """
    this method will change path which is unicode type
    to str type
    because in linux platform unicode obj + str obi will exception
    :param path_name:
    :param coding:
    :return:
    """
    if type(path_name) == unicode:
        return path_name.encode(coding)
    return path_name


def parse_path(path, deep=1):
    """

    :param path:
    :param deep:
    :return:
    """
    path = path_to_unicode(path)
    structure_dic = {}
    file_list = os.listdir(path)
    for f in file_list:
        f_path = os.path.join(path, f)
        structure_value = None
        if os.path.isdir(f_path):
            if deep < 3:
                structure_value = parse_path(f_path, deep=(deep + 1))
            else:
                structure_value = ""
        structure_dic[f] = structure_value
    return structure_dic


def compare_dic(dic_new, dic_format):
    import operator
    return operator.ge(dic_new, dic_format)


if __name__ == '__main__':
    # parse_directory = r'D:\test_temp\tmp_autonav\17Q2_A5_20170630'
    # structure_directory = parse_path(parse_directory)
    # import json
    #
    # json_data = json.dumps(structure_directory)
    # print json_data

    move_d = u'D:/test_temp/tmp_autonav/17Q2_A5_20170630/ROOT/ALL/WIDE_BACKGROUND/泰为_A5_17Q2_大中华_Snowman世界图数据_20170626'
    remove_dirs(move_d)
