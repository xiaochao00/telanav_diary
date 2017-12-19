import os
import sys
import pgconnect
import optparse


class GjvImporter(pgconnect.PgConnect):
    GJV_SCHEMA = 'usr'
    GJV_TABLE = '%s.gjv' % GJV_SCHEMA

    GJV_FIELD_TYPE = {
            'DP_NODE_ID': 'bigint NOT NULL',
            'ORIGINATING_LINK_ID': 'bigint NOT NULL',
            'DEST_LINK_ID': 'bigint NOT NULL',
            'RAMP': 'char(1)',
            'BIF': 'char(1)',
            'CA': 'char(1)',
            'FILENAME': 'text',
            'SIDE': 'char(1)',
            'SIGN_DEST': 'bigint',
            'JV_ORIGIN': 'bigint',
            'ISO_COUNTRY_CODE': 'char(3)',
            'GMS_SVG': 'text',
            'GMS_TEMPLATE': 'text',
            'LATITUDE': 'float',
            'LONGITUDE': 'float',
            'MDPS': 'char(1)',
            'MDPS_APPROX': 'text',
            'TUNNEL_ORIGIN_LINK': 'text',
            'TUNNEL_DEST_LINK': 'text',
            'ORIGIN_BEARING': 'float',
            'DEST_BEARING': 'float',
            'DP2_NODE_ID': 'text',
            'ORIGIN_CA': 'char(1)',
    }

    def __init__(self, options, gjv):
        pgconnect.PgConnect.__init__(self, options)

        self.gjv = gjv

        self.gjv_files = []


    def import_gjv(self):
        if not self.init_db():
            sys.stderr.write('Error: init database failed for import GJV\n')
            return False

        self._get_gjv_files()
        if not self.gjv_files:
            sys.stderr.write('Error: no GJV files in %s\n' % self.gjv)
            return False

        if not self._create_table():
            sys.stderr.write('Error: failed to create table for GJV\n')
            return False

        if not self._import_gjv():
            sys.stderr.write('Error: failed to import gjv\n')
            return False

        return True

    def _get_gjv_files(self):
        import glob

        self.gjv_files = glob.glob(os.path.join(self.gjv, "*.csv"))

        self.gjv_files = [os.path.abspath(gjv) for gjv in self.gjv_files]


    def _create_table(self):
        sqls = []

        sql = 'CREATE SCHEMA IF NOT EXISTS %s' % GjvImporter.GJV_SCHEMA
        sqls.append(sql)

        sql = 'DROP TABLE IF EXISTS %s' % GjvImporter.GJV_TABLE
        sqls.append(sql)

        # sql = """CREATE TABLE %s (
        #     DP_NODE_ID bigint NOT NULL,
        #     ORIGINATING_LINK_ID bigint NOT NULL,
        #     DEST_LINK_ID bigint NOT NULL,
        #     RAMP char(1),
        #     BIF char(1),
        #     CA char(1),
        #     FILENAME text,
        #     SIDE char(1),
        #     SIGN_DEST bigint,
        #     JV_ORIGIN bigint,
        #     ISO_COUNTRY_CODE char(3),
        #     GMS_SVG text,
        #     GMS_TEMPLATE text,
        #     LATITUDE float,
        #     LONGITUDE float,
        #     MDPS char(1),
        #     MDPS_APPROX text,
        #     TUNNEL_ORIGIN_LINK text,
        #     TUNNEL_DEST_LINK text,
        #     ORIGIN_BEARING float,
        #     DEST_BEARING float,
        #     DP2_NODE_ID text,
        #     ORIGIN_CA char(1)
        #     )
        #     """ % GjvImporter.GJV_TABLE

        sql = self._get_table_create_sql()
        if not sql:
            return False

        sqls.append(sql)

        return self.execute(';'.join(sqls))

    def _import_gjv(self):
        sql = """COPY %s FROM STDIN WITH CSV HEADER""" % GjvImporter.GJV_TABLE
        print sql

        for gjv in self.gjv_files:
            if not self.copy_export(open(gjv), sql):
                return False

        return True

    def _get_table_titles(self, gjv):
        for line in open(gjv):
            titles = line.split(',')
            return [t.upper() for t in titles]
        return None

    def _get_table_create_sql(self):
        titles = self._get_table_titles(self.gjv_files[0])

        if not titles:
            return None

        field_types = self._get_field_types(titles)
        fields = ['%s %s' % (title, typ) for title, typ in zip(titles, field_types)]

        return 'CREATE TABLE IF NOT EXISTS %s (%s)' % (GjvImporter.GJV_TABLE, ', '.join(fields))

    def _get_field_types(self, titles):
        field_types = []

        for title in titles:
            if title in GjvImporter.GJV_FIELD_TYPE:
                field_types.append(GjvImporter.GJV_FIELD_TYPE[title])
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
    if not options.gjv:
        print 'Error: GJV file not exists!'
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
    parser.add_option('-G', '--gjv', help='gjv', dest='gjv')

    options, args = parser.parse_args()

    if not validate(options):
        parser.print_help()
        sys.exit(-1)

    importer = GjvImporter(options, options.gjv)
    importer.import_gjv()

if __name__ == '__main__':
    main()