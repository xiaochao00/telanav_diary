# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      xlxu
#
# Created:     24-07-2014
# Copyright:   (c) xlxu 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import sys
import os
import psycopg2
import psycopg2.extras
from psycopg2 import Warning, Error
import StringIO


def printUsage():
    print "Usage : python %s landmark_dir dbstring" % (sys.argv[0])
    print 'Example : python %s /home/mapusder/lm/ "host=172.16.101.122 port=5432 user=postgres dbname=test"' % (
    sys.argv[0])


def loadLandmarkInfo(landmark_dir, dbstring):
    try:
        conn = psycopg2.connect(dbstring)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Error, e:
        sys.stderr.write(e.__str__())
        sys.exit(-2)
    except:
        sys.exit(-3)

    # create table
    sqls = ["create schema if not exists usr",
            "drop table if exists usr.usr_landmark_info",
            "create table usr.usr_landmark_info (id serial, file_name text not null, file_dir text not null,CONSTRAINT pk_usrlandmarkinfo PRIMARY KEY (file_name))"
            ]
    sql = ';'.join(sqls)
    try:
        cursor.execute(sql)
        conn.commit()
    except Error, e:
        conn.rollback()
        sys.stderr.write(e.__str__())
        sys.exit(-4)
    except:
        conn.rollback()
        sys.exit(-5)

    # get landmark file info
    dictFile2Dir = dict()
    listFile2Dir = list()
    for root, dirs, files in os.walk(landmark_dir):
        for f in files:
            # normalize the dir
            newroot = os.path.abspath(root).replace(os.path.abspath(landmark_dir), "")
            listFile2Dir.append((f, newroot))

    if not listFile2Dir:
        sys.stdout.write("No landmark data in %s\n" % landmark_dir)
        return False

    listFile2Dir = process_zipped_landmark(listFile2Dir, landmark_dir, dbstring)

    if not listFile2Dir:
        sys.stderr.write("Error: not find valid landmark data in %s\n" % landmark_dir)
        sys.exit(-1)

    tmp_file_name = "temp_copy_file"
    tmp_file = open(tmp_file_name, 'w')
    for f, root in listFile2Dir:
        tmp_file.write("%s\t%s\n" % (f, root))
    tmp_file.close()

    tmp_file = open(tmp_file_name, 'r')
    try:
        cursor.copy_from(tmp_file, 'usr.usr_landmark_info', sep='\t', null='\\N', columns=('file_name', 'file_dir'))
        conn.commit()
    except Error, e:
        conn.rollback()
        sys.stderr.write(e.__str__())
    except:
        conn.rollback()

    tmp_file.close()
    os.remove(tmp_file_name)

    cursor.close()
    conn.close()

    return True


def filter_night_mode(file2dir, dbstring):
    if 'KOR' not in dbstring.upper():
        return file2dir
    return (fd for fd in file2dir if '_NIGHT' not in fd[1])


def process_zipped_landmark(file2dir, landmark_dir, dbstring):
    import zipfile

    unzipped = filter(lambda fd: not fd[0].endswith('.zip'), file2dir)
    zipped = filter(lambda fd: fd[0].endswith('.zip'), file2dir)

    finals = dict(filter_night_mode(unzipped, dbstring))

    for fd in zipped:
        file_name, file_dir = fd
        zip_file = os.path.join(landmark_dir, file_dir, file_name)

        if not zipfile.is_zipfile(zip_file):
            sys.stderr.write("Error: %s is not valid zip file\n" % zip_file)
            continue

        infolist = zipfile.ZipFile(zip_file).infolist()
        infolist = [info for info in infolist if info.compress_type == zipfile.ZIP_DEFLATED]

        files = [info.filename for info in infolist]
        names = [os.path.basename(f) for f in files]

        paths = [os.path.dirname(os.path.join(landmark_dir, f)) for f in files]
        rel_paths = [os.path.relpath(p, landmark_dir) for p in paths]

        finals.update(dict(filter_night_mode(zip(names, rel_paths), dbstring)))

    return sorted(finals.items())


if __name__ == '__main__':

    if len(sys.argv) != 3:
        printUsage()
        sys.exit(-1)

    lm_dir = sys.argv[1]
    dbstring = sys.argv[2]

    if not os.path.isdir(lm_dir):
        print "%s is not a directory" % (lm_dir)
        sys.exit(-9)

    loadLandmarkInfo(lm_dir, dbstring)
