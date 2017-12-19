import os
import sys
import csv
import codecs
import pgconnect
import optparse


class HamletImporter(pgconnect.PgConnect):
    HAMLET_SCHEMA = 'usr'
    HAMLET_TABLE = '%s.usr_city_poi_display' % HAMLET_SCHEMA

    HAMLET_FIELD_TYPE = {
        'POI_ID': 'bigint NOT NULL PRIMARY KEY',
        'DISPLAY_LAT': 'bigint NOT NULL',
        'DISPLAY_LON': 'bigint NOT NULL',
        'NAME': 'text',
    }

    def __init__(self, options, hamlet):
        pgconnect.PgConnect.__init__(self, options)

        self.hamlet = hamlet

        self.hamlet_files = []

    def import_hamlet(self):
        if not self.init_db():
            sys.stderr.write('Error: init database failed for import hamlet\n')
            return False

        self._get_hamlet_files()
        if not self.hamlet_files:
            sys.stderr.write('Error: no hamlet files in %s\n' % self.hamlet)
            return False

        if not self._create_table():
            sys.stderr.write('Error: failed to create table for hamlet\n')
            return False

        if not self._import_hamlet():
            sys.stderr.write('Error: failed to import hamlet\n')
            return False

        return True

    def _get_hamlet_files(self):
        import glob

        if os.path.isdir(self.hamlet):
            self.hamlet_files = glob.glob(os.path.join(self.hamlet, "*.csv"))
        elif os.path.isfile(self.hamlet) and os.path.splitext(self.hamlet)[1] == '.csv':
            self.hamlet_files = [self.hamlet]

        self.hamlet_files = [os.path.abspath(hamlet) for hamlet in self.hamlet_files]

    def _create_table(self):
        sqls = []

        sql = 'CREATE SCHEMA IF NOT EXISTS %s' % HamletImporter.HAMLET_SCHEMA
        sqls.append(sql)

        sql = 'DROP TABLE IF EXISTS %s' % HamletImporter.HAMLET_TABLE
        sqls.append(sql)

        sql = self._get_table_create_sql()
        if not sql:
            return False

        sqls.append(sql)

        return self.execute(';'.join(sqls))

    def _import_hamlet(self):
        sql = """COPY %s FROM STDIN WITH CSV HEADER""" % HamletImporter.HAMLET_TABLE
        print sql

        for hamlet in self.hamlet_files:
            if not self.copy_export(open(hamlet), sql):
                return False

        return True

    def _get_table_titles(self, hamlet):
        with open(hamlet, 'rb') as csv_file:
            bom = csv_file.read(3)
            if bom != codecs.BOM_UTF8:
                csv_file.seek(0)

            for row in csv.reader(csv_file):
                print row
                return [t.upper() for t in row]
        return None

    def _get_table_create_sql(self):
        titles = self._get_table_titles(self.hamlet_files[0])

        if not titles:
            return None

        field_types = self._get_field_types(titles)
        fields = ['%s %s' % (title, typ) for title, typ in zip(titles, field_types)]

        return 'CREATE TABLE IF NOT EXISTS %s (%s)' % (HamletImporter.HAMLET_TABLE, ', '.join(fields))

    def _get_field_types(self, titles):
        field_types = []

        for title in titles:
            if title in HamletImporter.HAMLET_FIELD_TYPE:
                field_types.append(HamletImporter.HAMLET_FIELD_TYPE[title])
            else:
                field_types.append('text')

        return field_types


def validate(options):
    if not options.host:
        print 'Error: host not specified!'
        return False
    if not options.database:
        print 'Error: db name not specified!'
        return False
    if not options.hamlet:
        print 'Error: Hamlet file not exists!'
        return False

    return True


def main():
    import time

    parser = optparse.OptionParser()

    parser.add_option('-H', '--host', help='hostname', dest='host')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-m', '--hamlet', help='hamlet', dest='hamlet')

    options, args = parser.parse_args()

    if not validate(options):
        parser.print_help()
        sys.exit(-1)

    importer = HamletImporter(options, options.hamlet)
    importer.import_hamlet()


if __name__ == '__main__':
    main()
