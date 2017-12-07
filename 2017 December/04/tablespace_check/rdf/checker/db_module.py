import sys
import os
import psycopg2
from get_common_utils import print_error, print_standout


class DBModule:
    """Database connection class"""

    def __init__(self, host, dbname="postgres", username="postgres", password="postgres", port="5432"):
        # two default tablespace and directory of psql
        self.pg_default = "pg_default"
        self.pg_global = "pg_global"
        self.pg_default_dir = "base"
        self.pg_global_dir = "global"

        self.host = host
        self.dbname = dbname
        self.username = username
        self.password = password
        self.port = port

        self.conn = None
        self.cursor = None
        self.init_db()

    def init_db(self):
        try:
            self.conn = psycopg2.connect(database=self.dbname, user=self.username, password=self.password,
                                         host=self.host, port=self.port)
            self.cursor = self.conn.cursor()
        except Exception, e:
            print_error("Connection to db %s:%s failed." % (self.host, self.dbname))
            print_error(e)
            sys.exit(-1)

    def execute_sql(self, sql, is_exist=True):
        """Execute sql and return rows

        :param sql:
        :param is_exist:
        :return:
            results of execute sql
        """
        try:
            print_standout("Command sql : %s" % sql)
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return rows

        except Exception, e:
            self.conn.rollback()
            print_error("Failed execute sql [%s]" % sql)
            print_error(e)
            if is_exist:
                self.close()
                sys.exit(-1)
            else:
                return None

    def get_data_basedirectory(self):
        """Tablespace`s root/base directory

            execute sql : show data_directory;
        :return:
            base data directory
        """
        rows = self.execute_sql("show data_directory;")

        for row in rows:
            db_basedir = row[0]
            return db_basedir

        print_error("Get data base directory failed.")
        return None

    def get_all_tablespace_size_dic(self):
        """All tablespace

            execute sql : select spcname, pg_tablespace_location(oid) from pg_tablespace;
        :return:
            all tablespace names and locations of tablespace names {name:location,...}
        """
        tablespace_path_dic = {}

        rows = self.execute_sql("SELECT spcname, pg_tablespace_location(oid) FROM pg_tablespace;")

        basedir = self.get_data_basedirectory()
        if not basedir:
            return None

        for row in rows:
            tablespace_name = row[0].strip()
            tablespace_location = row[1].strip()

            # give basedir to tablespace of global & base
            if tablespace_location == '' and tablespace_name == self.pg_global:
                tablespace_location = os.path.join(basedir, self.pg_global_dir)

            if tablespace_location == '' and tablespace_name == self.pg_default:
                tablespace_location = os.path.join(basedir, self.pg_default_dir)

            tablespace_location = tablespace_location.replace("\\", "/")
            # need do this in window platform

            tablespace_path_dic[tablespace_name] = tablespace_location

        return tablespace_path_dic

    def get_tablespace_info(self):
        """Tablespace size

        select spcname, pg_tablespace_size(spcname)  from pg_tablespace;
        :return:
        """
        name_size_dic = {}
        sql = "SELECT spcname, pg_tablespace_size(spcname)  FROM pg_tablespace;"
        rows = self.execute_sql(sql)
        for row in rows:
            name = row[0]
            size = row[1]
            name_size_dic[name] = size
        return name_size_dic

    def close(self):
        """
        remember to close
        :return:
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_db_size(self, name):
        """
        size unit B
        sql select pg_database_size("content_unidb"); -- size unit byte
        :param name:
        :return:
            size  unit(B)
        """
        if not name:
            return None

        sql = "select pg_database_size('%s');" % name
        rows = self.execute_sql(sql, False)
        if not rows:
            return None

        for row in rows:
            db_size = row[0]
            return db_size

        return None

    def all_dbs(self):
        """Get all db in this connection

        sql : select datname from pg_database;
        :return:
        [dbname,dbname2,...]
        """
        rows = self.execute_sql("SELECT datname FROM pg_database ORDER BY datname;")
        db_list = []
        for row in rows:
            db_list.append(row[0])
        return db_list

    def size_db_list(self, db_list):
        """Get database size of database name list

        "select datname, pg_database_size(datname) from pg_datanase where datname in ( %s );"
        :param db_list:
        :return:
        the size of each db
        {dbname:size,...} unit is B
        """
        if not db_list:
            return None

        db_strs = str(db_list)[1:-1]
        if not db_strs.strip():
            return None

        sql = "SELECT datname, pg_database_size(datname) FROM pg_database WHERE datname IN ( %s );" % db_strs
        db_size_dic = {}
        rows = self.execute_sql(sql)
        for row in rows:
            db = row[0]
            size = row[1]
            db_size_dic[db] = size

        return db_size_dic


if __name__ == "__main__":
    pass
