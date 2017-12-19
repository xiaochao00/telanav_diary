import os
import sys
import csv
from pgconnect import PgConnect


class CsvImporter(PgConnect):
    def __init__(self, options):
        PgConnect.__init__(self, options)

    def import_csv(self, csv_files, **kwargs):
        """
        Below are valid arguments:
            tables: database table name for each csv_files, eg. [table1, table2, ...]
            headers: the headers for each table, e.g.           [ [field1, field2, ...], [...], ... ]
            field_types: the field types for each table, e.g.   [{field1: int, field2: text, ...}, {...}, ... ]
            primary_keys: primary key for each, e.g.            [field1, field1, ... ]

        if table names are not specified by tables, will use csv file names as table names
        if headers are not specified by headers, will parse header from csv files
        if field_types aer not specified by field_types, default field type will be text

        :param csv_files:  csv files to be imported to database
        :param kwargs:  optional arguments
        :return: True if importing successfully, else False
        """
        if not self.init_db():
            sys.stderr.write('Error: init database failed %s\n' % self.options)
            return False

        tables = self._get_tables(csv_files, kwargs)
        headers = self._get_headers(csv_files, kwargs)
        if not self._create_tables(tables, headers, kwargs.get('field_types', {}), kwargs.get('primary_keys', {})):
            sys.stderr.write('Error: create database tables failed\n')
            return False

        return self._import_csv(csv_files, kwargs)

    def _import_csv(self, csv_files, kwargs):
        tables = self._get_tables(csv_files, kwargs)

        for table, csv_file in zip(tables, csv_files):
            with open(csv_file, 'rb') as ifs:
                sample = ifs.read(4096)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                has_header = sniffer.has_header(sample)

                sql_options = """ CSV DELIMITER '%s' %s""" % (dialect.delimiter, 'HEADER' if has_header else '')
                table_name = '%s.%s' % (self.options.schema, table)

                ifs.seek(0)
                sql = """COPY %s FROM STDIN WITH %s""" % (table_name, sql_options)
                sys.stdout.write('%s [%s]\n' % (sql, csv_file))
                if not self.copy_export(ifs, sql):
                    return False

        return True

    def _create_tables(self, tables, headers, field_types, primary_keys):
        sqls = ['CREATE SCHEMA IF NOT EXISTS %s' % self.options.schema]
        for i, table, header in zip(xrange(len(tables)), tables, headers):
            types = field_types[i] if field_types else {}
            primary_key = primary_keys[i] if primary_keys else None

            field_definitions = [
                ' %s %s %s' % (f, types.get(f, 'text'), 'PRIMARY KEY' if f == primary_key else '') for f in header]

            table_name = '%s.%s' % (self.options.schema, table)
            sqls.append('DROP TABLE IF EXISTS %s' % table_name)
            sqls.append('CREATE TABLE %s (%s)' % (table_name, ', '.join(field_definitions)))

        return self.execute('; '.join(sqls))

    def _get_tables(self, csv_files, kwargs):
        tables = kwargs.get('tables')
        if not tables:
            tables = [os.path.basename(os.path.splitext(csv_file)[0]) for csv_file in csv_files]

            if (len(set(tables))) != len(csv_files):
                raise Exception('Multiple csv files with same name! %s' % csv_files)
        return tables

    def _get_headers(self, csv_files, kwargs):
        headers = kwargs.get('headers')
        return headers if headers else [self._get_csv_headers(csv_file) for csv_file in csv_files]

    @staticmethod
    def _get_tables_from_csv(csv_files):
        tables = [os.path.basename(os.path.splitext(csv_file)[0]) for csv_file in csv_files]

        if (len(set(tables))) != len(csv_files):
            raise Exception('Multiple csv files with same name! %s' % csv_files)

        return [table.lower() for table in tables]

    @staticmethod
    def _get_csv_headers(csv_file):
        with open(csv_file, 'rb') as ifs:
            sample = ifs.read(4096)
            sniffer = csv.Sniffer()
            if not sniffer.has_header(sample):
                raise Exception('CSV file do not have header, %s' % csv_file)

            dialect = sniffer.sniff(sample)
            ifs.seek(0)
            reader = csv.reader(ifs, dialect)
            for row in reader:
                return row


def test():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', help='hostname', dest='host', default='localhost')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-S', '--schema', help='schema', dest='schema')
    parser.add_option('-c', '--csv_dir', help='csv dir', dest='csv_dir')

    options, args = parser.parse_args()

    importer = CsvImporter(options)

    csv_dir = options.csv_dir
    csv_files = filter(lambda f: f.endswith('.txt'), [os.path.join(csv_dir, f) for f in os.listdir(csv_dir)])


    tables = ['ff', 'dd']
    headers = [['field1', 'field2'], ['field1', 'field5', 'field3']]
    field_types = [{'field1': 'int'}, {'field1': 'int', 'field3': 'int'}]
    primary_keys = ['field1', 'field3']

    # importer.import_csv(csv_files)
    # importer.import_csv(csv_files, tables=tables, headers=headers)
    importer.import_csv(csv_files, tables=tables, headers=headers, field_types=field_types, primary_keys=primary_keys)


def main():
    test()


if __name__ == '__main__':
    main()
