import sys
import psycopg2
import psycopg2.extras
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class PgConnect(object):
    def __init__(self, options):
        self.options = options

    def __del__(self):
        self.close()

    def close(self):
        if self.cursor and self.conn:
            self.cursor.close()
            self.cursor = None

    def init_db(self):
        return self._init_db()

    def _init_db(self):
        db_string = self._format_psql_db_args()

        try:
            self.conn = psycopg2.connect(db_string)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            psycopg2.extras.register_hstore(self.conn)
        except Error, e:
            sys.stderr.write('Init db failed, error_msg=[%s]\n' % e.__str__().strip())
            return False
        except Exception, e:
            sys.stderr.write('Unknown exception, error_msg=[%s]\n' % e.__str__().strip())
            return False

        return True

    def _format_psql_db_args(self):
        args = ['host=%s' % self.options.host,
                'dbname=%s' % self.options.dbname,
                'user=%s' % self.options.user,
                'port=%s' % self.options.port,
                'password=%s' % self.options.password,
                ]

        return ' '.join(args)

    def execute(self, sql):
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

        return True

    def execute_ex(self, sql):
        #recs = []

        try:
            self.cursor.execute(sql)
            for rec in self.cursor:
                #recs.append(rec)
                yield rec
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())

        #return recs

    def create_db(self, database, tablespace=None):
        try:
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            sql = 'CREATE DATABASE "%s"' % database
            if tablespace:
                sql = '%s TABLESPACE %s' % (sql, tablespace)
            self.conn.cursor().execute(sql)
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

        return True

    def copy_from(self, file_path, table, sep='\t'):
        try:
            self.cursor.copy_from(file_path, table, sep=sep)
            self.conn.commit()
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

        return True

    def copy_to(self, file_path, table, sep='\t'):
        try:
            self.cursor.copy_to(file_path, table, sep=sep)
            self.conn.commit()
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

        return True

    def copy_export(self, sql, fs):
        try:
            self.cursor.copy_expert(sql, fs)
            self.conn.commit()
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

        return True

    def exist(self, table):
        schema, table_name = PgConnect._parse_table(table)

        sql = "select exists(select * from pg_tables where schemaname='%s' and tablename ='%s')" % (schema, table_name)
        exists = False
        try:
            self.cursor.execute(sql)
            exists = self.cursor.fetchone()[0]
        except psycopg2.Error as e:
            sys.stderr.write(e.__str__())
        return exists

    @staticmethod
    def _parse_table(table):
        items = table.split('.')
        if len(items) == 2:
            return items[0], items[1]
        else:
            return 'public', table
