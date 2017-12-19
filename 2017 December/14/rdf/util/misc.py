import os
import sys
import glob
from distutils.spawn import find_executable

_SHP2PGSQL = 'shp2pgsql' + ".exe"
_PSQL = 'psql' + ".exe"
_TOOL_DIR = os.path.dirname(os.path.dirname(__file__))


def find_shp2pql():
    tool = find_executable(_SHP2PGSQL)
    if tool:
        return tool

    tools = find_in_dir(_TOOL_DIR, _SHP2PGSQL)
    if not tools:
        return None

    shp2pgsql = os.path.abspath(tools[0])
    os.system('chmod +x %s' % shp2pgsql)
    return shp2pgsql


def find_psql():
    tool = find_executable(_PSQL)
    if tool:
        return tool

    tools = find_in_dir(_TOOL_DIR, _PSQL)
    if not tools:
        return None

    shp2pgsql = os.path.abspath(tools[0])
    os.system('chmod +x %s' % shp2pgsql)
    return shp2pgsql


def find_in_dir(tool_dir, tool_name):
    tools = []
    for root, dirs, files in os.walk(tool_dir):
        for dir_name in dirs:
            tools.extend(glob.glob(os.path.join(root, dir_name, tool_name)))
    return tools


def safe_execute(cmd, exit_code=0):
    """
    :param cmd: the command to be executed.
    :param exit_code: the successful execution exit code expected.
    :return: N/A
    """
    sys.stdout.write('%s\n' % cmd)
    ec = os.system(cmd)
    if ec != exit_code:
        sys.stderr.write('Error: execute [%s] failed, exit code = %s\n' % (cmd, ec))
        sys.exit(-1)


if __name__ == '__main__':
    print find_shp2pql()
    print find_in_dir(_TOOL_DIR, _PSQL)
