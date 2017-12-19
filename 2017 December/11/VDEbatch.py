# -------------------------------------------------------------------------------
# Name:        VDEbatch
# Purpose:
#
# Author:      fwu
#
# Created:     16/10/2014
# Copyright:   (c) Telenav 2014
# Licence:
# -------------------------------------------------------------------------------
import os
import psycopg2
import VDEbatch_CONST
import sys
import traceback
from multiprocessing import cpu_count
from multiprocessing import Pool
from optparse import OptionParser

global options
parser = OptionParser()
YANGZI_PROJECT_NAME = "yangzi"


def start():
    try:
        conn = psycopg2.connect(database=options.idatabase, host=options.ihost, user=options.iuser, password=options.ipassword, port=options.iport)
        cur = conn.cursor()
        cur.execute(VDEbatch_CONST.SQL_STATENUM % options.ischema)
        rows = cur.fetchall()
        if options.project_name == YANGZI_PROJECT_NAME:
            print "remove HK and MaCao state"
            cur.execute("DELETE FROM {schema}.state where id in (810000,820000);".format(schema=options.ischema))
            conn.commit()
        distributeTask(rows)
    except Exception, e:
        print e.args[0]
        return


def distributeTask(rownum):
    cmd = VDEbatch_CONST.CMD_MIKDIR % (options.outpath)

    command_execute(cmd)

    dh = options.ihost + ':' + options.iport
    pool = Pool(processes=max(1, cpu_count() / 4))
    for i in rownum:
        cmd = VDEbatch_CONST.CMD_OUTFILE_SPP % (dh, options.idatabase, options.iuser, options.ipassword, options.filetype, options.outpath, str(i[0]), options.region, options.version, options.ischema) + (" " + VDEbatch_CONST.CMD_CROSSSTREET if options.crossstreet else "") + (" " + VDEbatch_CONST.CMD_SUBCITY if options.subcity else "")
        print cmd
        pool.apply_async(command_execute, (cmd,))

    pool.close()
    pool.join()

    standout_print('[x].out files have been created successfully')

    cmd = VDEbatch_CONST.CMD_OUTFILE_OTHER % (
        dh, options.idatabase, options.iuser, options.ipassword, options.filetype, options.outpath, options.region, options.version, options.ischema)
    command_execute(cmd)

    cmd = VDEbatch_CONST.CMD_IDGENERATION % (dh, options.idatabase, options.iuser, options.ipassword, options.filetype, options.outpath, options.outpath, options.region, options.version, options.ischema)
    command_execute(cmd)

    cmd = VDEbatch_CONST.CMD_DELETEOUTFILE % (options.outpath)
    command_execute(cmd)

    standout_print('procedure done')


def optionInit():
    parser.add_option("-D", "--database", action='store', dest='idatabase', help='VDE database\'s name')
    parser.add_option("-H", "--host", action='store', dest='ihost', help='VDE database\'s host')
    parser.add_option("-P", "--port", action='store', dest='iport', help='VDE database\'s port')
    parser.add_option("-S", "--schema", action='store', dest='ischema', help='VDE database\'s schema')
    parser.add_option("-u", "--user", action='store', dest='iuser', help='VDE database\'s user name')
    parser.add_option("-p", "--password", action='store', dest='ipassword', help='VDE database\'s password')
    parser.add_option("-o", "--output path", action='store', dest='outpath', help='output path of files')
    parser.add_option("-v", "--version", action='store', dest='version', help='raw data version')
    parser.add_option("-r", "--region", action='store', dest='region', help='region of the data')
    parser.add_option("-t", "--file type", action='store', dest='filetype', help='type of the files going to be output')
    parser.add_option("-c", "--cross street", action='store_true', dest='crossstreet', help='calculate cross street or not')
    parser.add_option("-s", "--subcity", action='store_true', dest='subcity', help='add subcity or not')
    parser.add_option("-N", "--project-name", dest="project_name", help="project name")


def printUsage():
    print '*' * 40
    parser.print_help()
    print '*' * 40


def checkParameters():
    if not options.idatabase:
        print '[ERROR]: empty parameter: -D'
        printUsage()
        sys.exit(-1)
    if not options.ihost:
        print '[ERROR]: empty parameter: -H'
        printUsage()
        sys.exit(-1)
    if not options.iport:
        print '[ERROR]: empty parameter: -P'
        printUsage()
        sys.exit(-1)
    if not options.iuser:
        print '[ERROR]: empty parameter: -u'
        printUsage()
        sys.exit(-1)
    if not options.ipassword:
        print '[ERROR]: empty parameter: -p'
        printUsage()
        sys.exit(-1)
    if not options.outpath:
        print '[ERROR]: empty parameter: -o'
        printUsage()
        sys.exit(-1)
    if not options.region:
        print '[ERROR]: empty parameter: -r'
        printUsage()
        sys.exit(-1)
    if not options.filetype:
        print '[ERROR]: empty parameter: -t'
        printUsage()
        sys.exit(-1)
    if not options.version:
        print '[ERROR]: empty parameter: -v'
        printUsage()
        sys.exit(-1)
    if not options.ischema:
        print '[ERROR]: empty parameter: -S'
        printUsage()
        sys.exit(-1)
    if not options.project_name:
        print '[ERROR]: empty parameter(project name): -N'
        printUsage()
        sys.exit(-1)


def standout_print(info):
    """
    print information to standout
    :param info:
    :return:
    """
    sys.stdout.write(str(info))
    sys.stdout.write("\n")


def command_execute(cmd):
    """
    execute command
    :param cmd:
    :return: True or False
    """
    if not cmd:
        raise Exception("Error: execute command should not be None")

    try:
        standout_print("Info: execute %s" % cmd)
        r = os.system(cmd)
        if r:
            sys.stderr.write("Error:execute %s failed" % cmd)
            sys.exit(-1)

        standout_print("Info: execute %s success" % cmd)
    except Exception, e:
        sys.stderr.write("Error: execute %s error" % cmd)
        traceback.print_exc()
        sys.stderr.write(e.__str__().strip())
        sys.exit(-1)


if __name__ == '__main__':
    global options

    optionInit()
    (options, args) = parser.parse_args(sys.argv)
    checkParameters()
    start()
