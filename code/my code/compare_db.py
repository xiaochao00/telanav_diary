import psycopg2
import sys


class PdbModel:
    def __init__(self, host, dbname, username='postgres', password='postgres', port='5432'):
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
                                         host=self.host,
                                         port="5432")
            self.cursor = self.conn.cursor()

        except Exception, e:
            error_out_print("Error: connection to db %s : %s failed. check need" % (self.host, self.dbname))
            print e
            sys.exit(-1)

    def execute_sql(self, sql, is_exist=True):
        """
            execute sql and return rows
        :param sql:
        :return:
            results of execute sql
        """
        try:
            standout_print('command sql : %s' % sql)
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return rows

        except Exception, e:
            self.conn.rollback()
            error_out_print("Failed: failed execute sql [%s]" % sql)
            error_out_print(e)
            if is_exist:
                self.close()
                sys.exit(-1)
            else:
                return None

    def get_tables_size(self):
        """
        select table_schema || '.' || table_name as table_full_name , pg_size_pretty(pg_total_relation_size('"'||table_schema||'"."'||table_name||'"')) as size
from information_schema.tables
order by pg_total_relation_size('"'||table_schema||'"."'||table_name||'"') DESC

        :return:
        """
        standout_print("get the size of tables in db [%s]." % self.dbname)
        sql = """ 
        select table_schema || '.' || table_name as table_full_name , pg_size_pretty(pg_total_relation_size('"'||table_schema||'"."'||table_name||'"')) as size
from information_schema.tables
order by pg_total_relation_size('"'||table_schema||'"."'||table_name||'"') DESC
        """
        rows = self.execute_sql(sql)
        table_size_dic = {}
        for row in rows:
            table_name = row[0]
            table_size = row[1]
            table_size_dic[table_name] = table_size
        return table_size_dic


def standout_print(info):
    sys.stdout.write("Info: %s " % info)
    sys.stdout.flush()


def error_out_print(info):
    sys.stderr.write("Error: %s " % info)
    sys.stderr.flush()


if __name__ == '__main__':
    db1 = 'cn_axf_17q2'
    db2 = 'cn_axf_17q2_test1016'
    host = "172.16.101.92"
    db_model1 = PdbModel(host, db1)
    db_model2 = PdbModel(host, db2)
    table_size_dic1 = db_model1.get_tables_size()
    table_size_dic2 = db_model2.get_tables_size()
    import pprint

    # pprint.pprint(table_size_dic1)
    # pprint.pprint(table_size_dic2)
    print cmp(table_size_dic1, table_size_dic2)
    is_equal = cmp(table_size_dic1, table_size_dic2)
    different_table_size_dic = {}
    if is_equal == 0:
        print "these tables in two database are same."
    else:
        keys1 = table_size_dic1.keys()
        keys2 = table_size_dic2.keys()

        for key in keys1:
            value1 = table_size_dic1.get(key)
            value2 = table_size_dic2.get(key)
            if cmp(value1, value2) != 0:
                different_table_size_dic[key] = (value1,value2)

    pprint.pprint(different_table_size_dic)
