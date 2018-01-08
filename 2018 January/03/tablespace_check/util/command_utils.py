import os
import sys

from common_utils import print_error, print_standout


def execute_cmd(cmd):
    print_standout("execute cmd is :%s" % cmd)
    s = os.system(cmd)
    if s:
        print_error("execute cmd[%s] failed" % cmd)
        sys.exit(-1)


def parse_size_info_response_lines(response_lines):
    """
    :param response_lines:
    the response_lines of command 'df -m directory'

    Filesystem     1M-blocks    Used Available Use% Mounted on
    tips:
        1. Used + Available < 1M-blocks, for linux system  make some space reserved for administrators
    :return: response dict
    {'Filesystem': , 'TotalSize': , 'Used': , 'Available': , 'UsedRate': , 'MountedOn': }
    default unit is KB
    """
    if not response_lines:
        print_error("Parse the response line of command failed. response lines can not none.")
        sys.exit(-1)
    # parse line num of  'Filesystem     1M-blocks    Used Available Use% Mounted on'
    specified_line_index = -1
    for line in response_lines:
        specified_line_index += 1
        if line.find("Filesystem") != -1 and line.find("Available") != -1:
            break

    if specified_line_index == -1 or specified_line_index == len(response_lines):
        print_error("in parse the response line of df command. lines is %s ." % response_lines)
        return None
    # names = response_lines[0].strip().split()
    # the next line of specified_line_index
    names = ['Filesystem', 'TotalSize', 'Used', 'Available', 'UsedRate', 'MountedOn']
    values = response_lines[specified_line_index + 1].strip().split()
    if len(names) != len(values):
        print_error("parse command response line failed. lines : %s" % response_lines)

    response_dict = {}
    for i in range(len(names)):
        name = names[i]
        value = values[i]
        response_dict[name] = value
    # change unit to B
    response_dict["TotalSize"] = long(response_dict["TotalSize"]) * 1024
    response_dict["Used"] = long(response_dict["Used"]) * 1024
    response_dict["Available"] = long(response_dict["Available"]) * 1024

    return response_dict
