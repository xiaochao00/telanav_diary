import os
import sys
import pgconnect
import optparse


class AddrImporter(pgconnect.PgConnect):
    ADDR_SCHEMA = 'public'

    ADDR_FIELDS = [
        'lcode',
        'sido',
        'sigungu',
        'dong',
        'li',
        'san',
        'bunji',
        'ho',
        'x_coord',
        'y_coord',
        'road_name',
        'new_bunji',
        'new_ho',
        'bd_name',
        'bd_dname',
        'recid',
        'link_pvid',
        'conf_level',
    ]

    ADDR_FIELD_TYPE = {
        'lcode': 'bigint',
        'sido': 'text',
        'sigungu': 'text',
        'dong': 'text',
        'li': 'text',
        'san': 'text',
        'bunji': 'text',
        'ho': 'text',
        'x_coord': 'float',
        'y_coord': 'float',
        'road_name': 'text',
        'new_bunji': 'text',
        'new_ho': 'text',
        'bd_name': 'text',
        'bd_dname': 'text',
        'recid': 'bigint',
        'link_pvid': 'bigint',
        'conf_level': 'smallint',
    }

    def __init__(self, options, addr):
        pgconnect.PgConnect.__init__(self, options)

        self.addr = addr

        self.addr_files = []

    def import_addr(self):
        if not self.init_db():
            sys.stderr.write('Error: init database failed for import ADDR\n')
            return False

        self._get_addr_files()
        if not self.addr_files:
            sys.stderr.write('Error: no ADDR files in %s\n' % self.addr)
            return False

        if not self._create_table():
            sys.stderr.write('Error: failed to create table for ADDR\n')
            return False

        if not self._import_addr():
            sys.stderr.write('Error: failed to import addr\n')
            return False

        return True

    def _get_addr_files(self):
        import glob

        self.addr_files = glob.glob(os.path.join(self.addr, "*.txt"))
        self.addr_files = glob.glob(os.path.join(self.addr, "*.TXT"))

        self.addr_files = [os.path.abspath(addr) for addr in self.addr_files]

    def _create_table(self):
        sqls = []

        sql = 'CREATE SCHEMA IF NOT EXISTS %s' % AddrImporter.ADDR_SCHEMA
        sqls.append(sql)

        sqls.extend(self._get_table_create_sql())

        return self.execute(';'.join(sqls))

    def _import_addr(self):
        for addr in self.addr_files:
            table_name = os.path.basename(os.path.splitext(addr)[0]).lower()
            sql = """COPY %s FROM STDIN WITH CSV DELIMITER ','""" % table_name
            sys.stdout.write('%s [%s]\n' % (sql, addr))
            if not self.copy_export(open(addr), sql):
                return False

        return True

    def _get_table_titles(self, addr):
##        for line in open(addr):
##            titles = line.split(',')
##            return [t.upper() for t in titles]
##        return None
        return AddrImporter.ADDR_FIELDS

    def _get_table_create_sql(self):
        addr_files = self.addr_files
        if not addr_files:
            return []

        titles = self._get_table_titles(self.addr_files[0])

        if not titles:
            return None

        field_types = self._get_field_types(titles)
        fields = ['%s %s' % (title, typ) for title, typ in zip(titles, field_types)]

        sqls = []
        for addr_file in addr_files:
            table_name = os.path.basename(os.path.splitext(addr_file)[0]).lower()
            sqls.append('DROP TABLE IF EXISTS %s' % table_name)
            sqls.append('CREATE TABLE %s (%s)' % (table_name, ', '.join(fields)))

        return sqls

    def _get_field_types(self, titles):
        field_types = []

        for title in titles:
            if title in AddrImporter.ADDR_FIELD_TYPE:
                field_types.append(AddrImporter.ADDR_FIELD_TYPE[title])
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
    if not options.addr:
        print 'Error: ADDR file not exists!'
        return False

    return True


def main():
    parser = optparse.OptionParser()

    parser.add_option('-H', '--host', help='hostname', dest='host', default='localhost')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-a', '--addr', help='addr', dest='addr')

    options, args = parser.parse_args()

    if not validate(options):
        parser.print_help()
        sys.exit(-1)

    importer = AddrImporter(options, options.addr)
    importer.import_addr()

if __name__ == '__main__':
    main()