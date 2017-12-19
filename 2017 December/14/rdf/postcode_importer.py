# -------------------------------------------------------------------------------
# Name:        postcode_importer
# Purpose:
#
# Author:      lgwu
#
# Created:     16-03-2015
# Copyright:   (c) lgwu 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import sys
import os
import psycopg2
import psycopg2.extras
from psycopg2 import Warning, Error
import StringIO
import subprocess

POSTAL_CODE_SCHEME = 'usr'


def usage():
    print "Usage : python %s postcode_dir dbstring" % (sys.argv[0])
    print 'Example : python %s /home/mapuser/postal_code/ "host=172.16.101.122 port=5432 user=postgres dbname=test"' \
          % sys.argv[0]


def import_postcodes(path, dbstring):
    global POSTAL_CODE_SCHEME

    try:
        conn = psycopg2.connect(dbstring)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Error, e:
        sys.stderr.write(e.__str__())
        sys.exit(-2)
    except:
        sys.exit(-3)

    postcode_files = get_postalcode_files(path)

    for base in postcode_files:
        postcode_file = postcode_files[base]
        table = '%s.%s' % (POSTAL_CODE_SCHEME, base)

        sqls = []

        sqls.append('CREATE SCHEMA IF NOT EXISTS %s' % POSTAL_CODE_SCHEME)
        sqls.append('DROP TABLE if EXISTS %s' % table)

        sql = """CREATE TABLE %s (
              post_main char(6),
              post_full char(8),
              iso_ctry char(3),
              nt_city varchar(35),
              geo_level char(1),
              rec_type char(1),
              lat float,
              lon float,
              nt_linkid bigint,
              country varchar(35)
              )""" % table
        sqls.append(sql)

        try:
            cursor.execute(';'.join(sqls))
            conn.commit()
        except Error, e:
            conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-4)
        except:
            conn.rollback()
            sys.exit(-5)

        print 'copy %s to %s' % (postcode_file, table)
        tmp_file = open(postcode_file, 'r')
        try:
            #cursor.copy_from(tmp_file, table, sep='|', null='\\N')
            cursor.copy_from(tmp_file, table, sep='|', null='')
            # cursor.copy_expert("COPY %s FROM STDIN DELIMITER '|'" % table, tmp_file)
            conn.commit()
        except Error, e:
            conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-6)
        except:
            conn.rollback()
            sys.stderr.write('Error: load postal code failed\n')
            sys.exit(-7)

    cursor.close()
    conn.close()

    return True


def get_postalcode_files(path):
    files = [f for f in os.listdir(path) if os.path.splitext(f)[1].upper() == '.TXT']

    bases = [os.path.splitext(f)[0].lower() for f in files]
    paths = [os.path.join(path, f) for f in files]

    status = [convert_postal_files(p) for p in paths]

    paris = (i for i in zip(bases, paths) if os.path.isfile(i[1]))

    return dict(paris)


def convert_postal_files(file_path):
    filename = os.path.basename(file_path)
    if not filename.startswith('NL_') and not filename.startswith('NLD_'):
        return True

    print 'Convert Encoding of %s' % file_path

    temp_file = '%s.utf8' % file_path

    # TODO: Dangerous to convert one file multiple times.
    # covert NL postal code to utf8
    cmd = 'iconv -f latin1 -t utf8 %s -o %s' % (file_path, temp_file)
    r = subprocess.call(cmd, shell=True)

    if not r:
        cmd = 'mv %s %s' % (temp_file, file_path)
        r = subprocess.call(cmd, shell=True)

    return not r

if __name__ == '__main__':

    if len(sys.argv) != 3:
        usage()
        sys.exit(-1)

    post_dir = sys.argv[1]
    dbstring = sys.argv[2]

    if not os.path.isdir(post_dir):
        print "Error: %s is not a directory" % post_dir
        sys.exit(-2)

    import_postcodes(post_dir, dbstring)
