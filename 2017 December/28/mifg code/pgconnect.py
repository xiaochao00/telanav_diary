import sys
import os
import psycopg2
import psycopg2.extras
from psycopg2 import Warning, Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import StringIO


def catching_exception(func):
    def _decorate(obj, *args, **kwargs):
        try:
            result = func(obj, *args, **kwargs)
            return result
        except Error, e:
            obj.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            obj.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

    return _decorate


class PgConnect(object):
    def __init__(self, options):
        self.options = options

    def init_db(self):
        return self._init_db()

    def _init_db(self):
        dbstring = self._format_psql_db_args()

        try:
            self.conn = psycopg2.connect(dbstring)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except Error, e:
            sys.stderr.write('Init db failed, error_msg=[%s]\n' % e.__str__().strip())
            return False
        except Exception, e:
            sys.stderr.write('Unknown exception, error_msg=[%s]\n' % e.__str__().strip())
            return False

        return True

    def _format_psql_db_args(self):
        args = ['host=%s' % self.options.host,
                'dbname=%s' % self.options.database,
                'user=%s' % self.options.user,
                'port=%s' % self.options.port,
                'password=%s' % self.options.passwd,
                ]

        return ' '.join(args)

    @catching_exception
    def execute(self, sql):
        self.cursor.execute(sql)
        self.conn.commit()
        return True

    @catching_exception
    def create_db(self, database, tablespace=None):
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        sql = 'CREATE DATABASE "%s"' % database
        if tablespace:
            sql = '%s TABLESPACE %s' % (sql, tablespace)
        self.conn.cursor().execute(sql)
        return True

    @catching_exception
    def copy_export(self, fs, sql):
        self.cursor.copy_expert(sql, fs)
        self.conn.commit()
        return True

    @catching_exception
    def exist(self, table):
        schema, tablename = self._parse_table(table)
        exists = False
        self.cursor.execute("select exists(select * from pg_tables where schemaname='%s' and tablename ='%s')" % (schema, tablename))
        exists = self.cursor.fetchone()[0]
        return exists

    def _parse_table(self, table):
        items = table.split('.')
        if len(items) == 2:
            return items[0], items[1]
        else:
            return 'public', table

    @catching_exception
    def db_exist(self, dbname):
        self.cursor.execute("SELECT EXISTS(SELECT * FROM pg_database WHERE datname='%s')" % dbname)
        return bool(self.cursor.fetchone()[0])

    @catching_exception
    def query_sql(self, sql):
        self.cursor.execute(sql)
        for rec in self.cursor:
            yield rec

    @catching_exception
    def copy_from(self, f, table_name, column_name_list):
        columns = tuple(column_name_list)
        self.cursor.copy_from(f, table=table_name, columns=columns)
        self.conn.commit()


class Opt(object):
    pass


def main():
    opt = Opt()

    setattr(opt, 'host', '172.16.102.205')
    setattr(opt, 'database', 'postgres')
    setattr(opt, 'port', '5432')
    setattr(opt, 'user', 'postgres')
    setattr(opt, 'passwd', 'postgres')

    pgcon = PgConnect(opt)
    if not pgcon.init_db():
        print 'init db failed\n'
        return False

    print pgcon.db_exist('test2')
    print pgcon.db_exist('postgres')
    print pgcon.db_exist('NT_CN_16Q1')


if __name__ == '__main__':
    main()
