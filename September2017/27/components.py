import sys
import os


def standout_print(info):
    """
    print information to standout
    :param info:
    :return:
    """
    sys.stdout.write(info)
    sys.stdout.write("\n")


def error_out_print(info):
    """
    print error message
    :param info:
    :return:
    """
    sys.stderr.write(info)
    sys.stderr.write("\n")


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
    result_statue = os.system(cmd)

    if not cmd and result_statue:
        error_out_print("Error: execute command [%s]. program stop" % cmd)
        sys.exit(-1)

    standout_print("Info: execute cmd[%s] success." % cmd)
    return True


def move_directory(from_directory, to_directory):
    if not os.path.exists(from_directory):
        error_out_print("Error: mv directory is not exist. please check [%s]" % from_directory)

    mv_cmd = "mv %s %s"
    execute_cmd(mv_cmd)


