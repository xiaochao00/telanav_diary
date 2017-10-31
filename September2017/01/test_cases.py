# -*- coding: utf-8 -*-

'''
test case file
in this
'''
from check_utils import is_localhost
import socket
import sys
from check_utils import format_disk_size
from config_reader import tablespace_size_config


def test_islocalhost():
    print socket.gethostname()
    socket.get


class DBModel:
    """
    get all database in every region
    and get it size
    """

    def __init__(self, host, dbname='postgres', username='postgres', password='postgres', port='5432'):
        # two default tablespace and directory of psql
        self.pg_default = 'pg_default'
        self.pg_global = 'pg_global'
        self.pg_default_dir = 'base'
        self.pg_global_dir = 'global'

        self.host = host
        self.dbname = dbname
        self.username = username
        self.password = password
        self.port = port

        self.init_db()

    def init_db(self):
        import psycopg2
        try:
            self.conn = psycopg2.connect(database=self.dbname, user=self.username, password=self.password,
                                         host=self.host,
                                         port="5432")
            self.cursor = self.conn.cursor()
        except Exception, e:
            standout_print("Error: connection to db %s : %s failed. check need" % (self.host, self.dbname))
            print e
            sys.exit(-1)

    def execute_sql(self, sql):
        """
            execute sql and return rows
        :param sql:
        :return:
            results of execute sql
        """
        print 'command sql : ', sql
        self.cursor.execute(sql)

        rows = self.cursor.fetchall()

        return rows

    def get_db_size(self, name):
        """
        size unit MB
        sql select pg_database_size('content_unidb'); -- size unit byte
        :param name:
        :return:
            the db size
        """
        try:
            sql = "select pg_database_size('%s');" % name
            rows = self.execute_sql(sql)
            for row in rows:
                db_size = format_disk_size(row[0])
                return db_size
        except Exception, e:
            standout_print("Error: get size of db[%s] failed, check need " % name)
            print e

        return None

    def all_dbs(self):
        """
        sql : select datname from pg_database;
        :return:
        """
        rows = self.execute_sql('select datname from pg_database order by datname;')
        db_list = []
        for row in rows:
            db_list.append(row[0])
        return db_list

    def size_dblist(self,db_list):
        """
        "select datname, pg_database_size(datname) from pg_datanase where datname in ( %s );"
        :param db_list:
        :return:
        """
        db_strs = str(db_list)[1:-1]
        sql = "select datname, pg_database_size(datname) from pg_database where datname in ( %s );" % db_strs
        dbsize_list = {}
        rows = self.execute_sql(sql)
        for row in rows:
            db = row[0]
            size = format_disk_size(row[1])
            dbsize_list[db] = size

        return dbsize_list

def db_minsize(host):
    region_list = tablespace_size_config()

    db_model = DBModel(host)

    selected_db = []
    dbname_list = db_model.all_dbs()
    for db in dbname_list:
        for region in region_list:
            if db.upper().find(region.upper()) and (db.upper().startswith('HERE') or db.upper().startswith('NT')):
                selected_db.append(db)

    dbsize_list = {}
    # for db in selected_db:
    #     size = db_model.get_db_size(db)
    #     dbsize_list[db] = size
    if not selected_db:
        return None
    dbsize_list = db_model.size_dblist(selected_db)

    print dbsize_list
    return dbsize_list


def standout_print(info):
    """
    print information to standout
    :param info:
    :return:
    """
    sys.stdout.write(info)
    sys.stdout.write("\n")


if __name__ == '__main__':
    # test_islocalhost()

    hosts = ['hqd-ssdpostgis-04.mypna.com','hqd-ssdpostgis-05.mypna.com','10.179.1.110','shd-dpc6x64ssd-02.china.telenav.com']
    for host in hosts:
        db_minsize(host)