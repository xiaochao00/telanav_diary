#-------------------------------------------------------------------------------
# Name:        base record model
# Purpose:     list database information and the basic method
#
# Author:      rex
#
# Created:     08/10/2015
# Copyright:   (c) rex 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import ConfigParser
import psycopg2
import sys

import option_cfg

CSV_SEP = '`'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

class Record:
    def __init__(self, mode="development", region=''):
        # data base config file path is constant
        self.database_cfg = os.path.join(ROOT_DIR, "..", "config", "database.cfg")
        self.mode = mode
        self.region = region
        self.opt_cfg = None

        self.__parse_cfg()
        self.__connect()

    # public method
    def close_cursor(self):
        self.cursor.close()

    def close_conn(self):
        self.conn.close()

    def run_sql(self,execute,cmd):
        result = None
        try:
            print cmd
            result = execute(cmd)
            self.conn.commit()
            #print result
        except:
            print "Unexpected error:[ %s.py->%s] %s"%(self.__class__.__name__, 'run_sql', str(sys.exc_info()))
            self.conn.rollback()
        return result

    def rollback(self):
        self.conn.rollback()

    # private method
    def __parse_cfg(self):
        cf = ConfigParser.ConfigParser()
        cf.read(self.database_cfg)
        #database=None, user=None, password=None, host=None, port=None,
        self.host     = cf.get(self.mode,"host")
        self.database = cf.get(self.mode,"database")
        self.user     = cf.get(self.mode,"username")
        self.password = cf.get(self.mode,"password")
        #print [self.host, self.database, self.user, self.password]

        # load options config
        self.__load_options_cfg()

    def __connect(self):
        try:
            self.conn = psycopg2.connect("dbname='" + self.database + "' user='" + self.user + "' host='" + self.host + "' password='"+self.password+"'")
        except:
            print "[ERROR] Unable to connect to the database!"
            #return None
            sys.exit(-1)

        try:
            self.cursor = self.conn.cursor()
        except:
            self.close_conn()
            print "[ERROR] Unable to get cursor!"
            #return None
            sys.exit(-1)

        return True

    def is_existtable(self,schema,table):
        self.run_sql(self.cursor.execute,"select tablename from pg_tables where schemaname='"+schema+"';")
        return 0 != map(lambda px:px[0],self.cursor.fetchall()).count(table)

    def __load_options_cfg(self):
        if not self.region:
            sys.stdout.write('Warning: region is not specified for OptionCfg\n')
            return True

        config_dir = os.path.join(ROOT_DIR, '../config/options')
        version = self.__get_data_version()
        if not version:
            sys.stderr.write('Error: can not get data version from %s\n' % self.database)
            sys.exit(-1)

        self.opt_cfg = option_cfg.OptionCfg(config_dir, version, self.region)

        for opt in self.opt_cfg.OPTS:
            print opt, self.opt_cfg.options[opt]

        return True

    def __get_data_version(self):
        """
        Expected database format: HERE_NA16Q1, NT_CN_16Q1, etc.
        :return:
        """
        import re
        m = re.match('.*(\d{2}Q[1-4])', self.database)
        if m:
            return m.group(1)
        return None

    def execute(self, sql):
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except psycopg2.Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            return False

        return True

    def execute_ex(self, sql):
        try:
            self.cursor.execute(sql)
            for rec in self.cursor:
                yield rec
        except psycopg2.Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())

    @staticmethod
    def split(line):
        #line = line.replace('\\%s' % CSV_SEP, '\0')
        return line.split(CSV_SEP)
    def do_static(self):
        pass
    def strIsEmpty(self,s):
        if None != s and '\N' != s:
            return True
        return False
if __name__ == "__main__":
    # use to test this model
    pass

