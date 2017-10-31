
import psycopg2
import os
import csv
ROOT_DIR          = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
CSV_SEP           = '`'

class Test():
    def __init__(self):
        self.database = 'test'
        self.user = 'postgres'
        self.host = 'hqd-ssdpostgis-04.mypna.com'
        self.password = 'postgres'
        self.conn = psycopg2.connect("dbname='" + self.database + "' user='" + self.user + "' host='" + self.host + "' password='" + self.password + "'")
        self.cursor = self.conn.cursor()
        self.dump_file = 'test'

    def dump_Test(self):
        cmd='select * from public."Table1"'
        print cmd
        f = "%s_navstrand.csv" % (self.dump_file)
        self.cursor.copy_expert("COPY (%s) TO STDOUT DELIMITER '`' CSV   " % (cmd), open(f, "w"))

    def read_csv2(self):
        processcount = 0
        f = "%s_navstrand" % (self.dump_file)
        with open(f, "r", 1024 * 1024 * 1024) as csv_f:
            for line in csv_f:
                print line
    def read_csv(self):
        processcount = 0
        f = "%s_navstrand.csv" % (self.dump_file)
        with open(f) as csvfile:
            lines = csv.reader(csvfile,delimiter='`')
            for line in lines:
                print line
                for c in line:
                    print c.strip() == ''
    def get_statistic(self):
        self.dump_Test()
        self.read_csv()

if __name__ == "__main__":
    t = Test()
    t.get_statistic()
