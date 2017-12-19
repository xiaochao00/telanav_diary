import os
import sys
import logging
import multiprocessing

from misc import find_psql
from misc import find_shp2pql
from misc import safe_execute


class ShapeImporter(object):
    def __init__(self, options):
        """
        :param options:
        """
        self.options = options
        # initialize postgis args with options
        self.db_args = self._format_psql_args(options)

        # get tool of shp2pgsql
        self.shp2pgsql = find_shp2pql()
        if not self.shp2pgsql:
            logging.error('No shp2pgsql tool found\n')
            sys.exit(-1)

        self.psql = find_psql()
        if not self.psql:
            logging.error('No psql tool found\n')
            sys.exit(-1)

    def import_shape(self, dbf_files, **kwargs):
        """
        Import shape file to database
        """
        # create schema
        schema = self.options.schema if self.options.schema else 'public'
        cmd = '{psql} {db_args} -v ON_ERROR_STOP=1 -c ' \
              '"CREATE SCHEMA IF NOT EXISTS {schema}" '.format(psql=self.psql,
                                                               db_args=self.db_args,
                                                               schema=schema)
        safe_execute(cmd)

        # get tables for each shp file/dbf file
        tables = self._get_tables(dbf_files, kwargs)
        tables = ['{schema}.{table}'.format(schema=schema, table=t) for t in tables]

        # generate execution commands
        cmds = []
        for table, dbf_file in zip(tables, dbf_files):
            geom_exists = os.path.exists(dbf_file.replace('.dbf', '.shp'))
            geom_options = '-s 4326 -I' if geom_exists else '-n'

            cmd = '{shp2pgsql} {geom_options} -D -W GB18030 {dbf_file} {table} |' \
                  ' {psql} {db_args} -v ON_ERROR_STOP=1'.format(shp2pgsql=self.shp2pgsql,
                                                                geom_options=geom_options,
                                                                dbf_file=dbf_file,
                                                                table=table,
                                                                psql=self.psql,
                                                                db_args=self.db_args)

            cmds.append(cmd)

        # execute shape file importing
        pool = multiprocessing.Pool(max(1, multiprocessing.cpu_count() / 2))
        pool.map(safe_execute, cmds)

        return True

    @staticmethod
    def _get_tables(dbf_files, kwargs):
        tables = kwargs.get('tables')
        if not tables:
            tables = [os.path.basename(os.path.splitext(dbf_file)[0]) for dbf_file in dbf_files]

            if (len(set(tables))) != len(dbf_files):
                raise Exception('Multiple csv files with same name! %s' % dbf_files)
        return tables

    @staticmethod
    def _format_psql_args(options):
        args = ['-h %s' % options.host,
                '-p %s' % options.port,
                '-U %s' % options.user,
                '%s' % options.database,
                ]

        return ' '.join(args)


def main():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', help='hostname', dest='host', default='localhost')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-S', '--schema', help='schema', dest='schema')
    parser.add_option('-s', '--shp_dir', help='shp dir', dest='shp_dir')

    options, args = parser.parse_args()

    importer = ShapeImporter(options)

    shp_dir = options.shp_dir
    if not shp_dir or not os.path.exists(shp_dir):
        sys.stderr.write('Error: shape directory not exists!')
        parser.print_help()
        sys.exit(-1)

    dbf_files = filter(lambda f: f.endswith('.dbf'), [os.path.join(shp_dir, f) for f in os.listdir(shp_dir)])
    dbf_names = [os.path.splitext(os.path.basename(dbf))[0] for dbf in dbf_files]
    tables = [dbf_name.replace('shanghai', '') for dbf_name in dbf_names]

    importer.import_shape(dbf_files, tables=tables)

if __name__ == '__main__':
    main()
