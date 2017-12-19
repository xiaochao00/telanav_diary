import os
import sys
import logging
import glob
from distutils.spawn import find_executable


class ShapeImporter(object):
    # final variable
    ZIP_FILE_SUFFIX = '*.zip'
    SHAPE_FILE_SUFFIX = '.shp'
    LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
    # sql format
    CMD_DROP_TABLE = 'psql %s -v ON_ERROR_STOP=1 -c "CREATE SCHEMA IF NOT EXISTS %s; DROP TABLE IF EXISTS %s" '
    CMD_GENERATE_SQL = '%s -I -W LATIN1 %s %s > %s.sql'
    CMD_IMPORT_SHAPE = 'psql %s -v ON_ERROR_STOP=1 -f %s.sql'

    def __init__(self, options, importer):
        """
        Initialize ShapeImporter
        :param options: options used to initialize database connection
        :param importer: file path of importer
        """
        # initialize postgis args with options
        self.db_args = self._format_psql_args(options)

        # get tool of shp2pgsql
        self.shp2pgsql = self._get_shp2pgsql(importer)
        if not self.shp2pgsql:
            logging.error('No shp2pgsql tool found\n')
            sys.exit(-1)
        # set shp2pgsql to library path
        lib_paths = [os.getenv(ShapeImporter.LD_LIBRARY_PATH, None), os.path.dirname(self.shp2pgsql)]
        lib_paths = filter(None, lib_paths)
        os.putenv(ShapeImporter.LD_LIBRARY_PATH, ':'.join(lib_paths))

    def import_shape(self, shape_dir, table_name):
        """
        Import shape file to database
        :param shape_dir: shape file directory
        :param table_name: table name
        :return: True/False
        """

        # get shape file from shape dir, if shape file is not exist, output error log
        shape_file = self._get_shape_file(shape_dir)
        if not shape_file:
            logging.info('No shape data found in %s' % shape_dir)
            return True

        # drop table is exist
        schema_name = self._get_schema_name(table_name)
        cmd = ShapeImporter.CMD_DROP_TABLE % (self.db_args, schema_name, table_name)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('drop %s failed!\n' % table_name)
            return False

        # create sql file with shp2pgsql
        cmd = ShapeImporter.CMD_GENERATE_SQL % (self.shp2pgsql, shape_file, table_name, table_name)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('shp2pgsql generate sql failed!, exit code = %s\n' % r)
            return False

        # import shape file
        cmd = ShapeImporter.CMD_IMPORT_SHAPE % (self.db_args, table_name)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('import shp file %s failed! exit code = %s\n' % (shape_file, r))
            return False

        return True

    def _get_shape_file(self, shape_dir):
        # get shape file by suffix of "shp"
        shape_files = self._get_shape_files(shape_dir)
        if shape_files:
            return shape_files[0]

        # get zip files if there is no shape file exist
        zip_files = glob.glob(os.path.join(shape_dir, ShapeImporter.ZIP_FILE_SUFFIX))
        if not zip_files:
            return None

        zip_files.sort()
        os.system('unzip %s -d %s' % (zip_files[0], shape_dir))

        # get shape file by suffix of "shp" after unzip the zip file
        shape_files = self._get_shape_files(shape_dir)
        if shape_files:
            return shape_files[0]

        # return None if there is no shape file exist
        return None

    @staticmethod
    def _get_shape_files(shape_dir):
        shape_files = []
        for root, dirs, files in os.walk(shape_dir):
            # get shp file by mapping suffix
            shp_file_names = [file_name for file_name in files if file_name.endswith(ShapeImporter.SHAPE_FILE_SUFFIX)]
            shape_files.extend([os.path.join(root, file_name) for file_name in shp_file_names])

        return shape_files

    def _get_shp2pgsql(self, importer):
        tool = find_executable('shp2pgsql')
        if tool:
            return tool

        tools = self._get_in_dir('shp2pgsql', importer)
        if not tools:
            return None

        shp2pgsql = tools[0]
        os.system('chmod +x %s' % shp2pgsql)
        return shp2pgsql

    @staticmethod
    def _get_in_dir(tool_name, tool_dir):
        tools = []
        for root, dirs, files in os.walk(tool_dir):
            tools.extend(glob.glob(os.path.join(root, tool_name)))
        return tools

    @staticmethod
    def _format_psql_args(options):
        args = ['-h %s' % options.host,
                '-p %s' % options.port,
                '-U %s' % options.user,
                '%s' % options.database,
                ]

        return ' '.join(args)

    def _get_schema_name(self, table_name):
        """
        Get schema name from table_name, the default schema name is public
        :param table_name: name of table which contains schema name
        :return:
        """
        items = table_name.split('.')
        if len(items) == 2:
            return items[0]
        else:
            return 'public'


if __name__ == '__main__':
    pass
