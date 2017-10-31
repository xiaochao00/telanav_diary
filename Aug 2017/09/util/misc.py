import os
import sys


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

