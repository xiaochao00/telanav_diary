import os
import sys
import glob
import time
import logging
from distutils.spawn import find_executable
from pgconnect import PgConnect


class DbProcessor(object):
    def __init__(self, options):
        self.options = options
        self.pg_connect = PgConnect(options)

        self.adaptor = self.options.adaptor

        self.opts = self._parse_opts()

        self.psql = find_executable('psql')

    def init(self):
        if not self.pg_connect.init_db():
            logging.error('init pg connect failed while process database')
            return False

        return True

    def process(self):
        if not self.init():
            return False

        return self._process_imp()

    def _process_imp(self):
        if not self._censorship_process():
            return False

        if not self._remove_premium():
            return False

        if not self._retrieve_turkey_ocean():
            return False

        if not self._split_database():
            return False

        if not self._modify_database():
            return False

        return True

    def _parse_opts(self):
        if not self.options.db_opts:
            return []

        opts = [op.lower() for op in self.options.db_opts.split('|')]
        return opts

    def _censorship_process(self):
        sql_files = self._get_censorship_sql_files()
        if not sql_files:
            logging.info('No sql files found for censorship')
            return True

        if not self.psql:
            logging.error('psql not exists!')
            return False

        args = self._format_psql_args()
        for sql_file in sql_files:
            cmd = '%s %s -v ON_ERROR_STOP=1 -f %s' % (self.psql, args, sql_file)
            logging.info(cmd)
            r = os.system(cmd)
            if r:
                logging.error('run censorship process sql failed!')
                return False

        return True

    def _get_censorship_sql_files(self):
        sql_files = glob.glob(os.path.join(self.adaptor, 'censorship', '*.sql'))
        if not sql_files:
            return None

        region, version = self._parse_database_name(self.options.database)
        if not region or not version:
            logging.warning('Can not extract region/version from %s' % self.options.database)
            return None

        sql_files.sort()
        return self._get_matched_sql_files(sql_files, region)

    def _remove_premium(self):
        if not self._need_remove_premium():
            logging.info('Skip premium removal')
            return True

        sql_file = self._get_premium_sql_file()
        logging.info('Best matched premium sql file for %s is %s' % (self.options.database, sql_file))
        if not sql_file or not os.path.exists(sql_file):
            logging.error('Can not find premium sql file')
            return False

        if not self.psql:
            logging.error('psql not exists!')
            return False

        args = self._format_psql_args()
        cmd = '%s %s -v ON_ERROR_STOP=1 -f %s' % (self.psql, args, sql_file)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('remove premium failed!')
            return False

        return True

    def _modify_database(self):
        if not self._need_modify():
            logging.info('Skip modify database')
            return True

        cur_dir = os.getcwd()
        os.chdir(self.adaptor)

        args = ['-H %s' % self.options.host,
                '-D %s' % self.options.database,
                '-U %s' % self.options.user,
                '-P %s' % self.options.port,
                '-p %s' % self.options.passwd,
                '-m ']

        cmd = 'python2.7 TableDivider.py %s' % ' '.join(args)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('Fail to modify database for %s' % args)
            os.chdir(cur_dir)
            return False

        os.chdir(cur_dir)
        return True

    def _split_database(self):
        if not self._need_divide():
            logging.info('Skip divide database')
            return True

        cur_dir = os.getcwd()
        os.chdir(self.adaptor)

        args = ['-H %s' % self.options.host,
                '-D %s' % self.options.database,
                '-U %s' % self.options.user,
                '-P %s' % self.options.port,
                '-p %s' % self.options.passwd]

        cmd = 'python2.7 TableDivider.py %s' % ' '.join(args)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('Fail to data division for %s' % args)
            os.chdir(cur_dir)
            return False

        os.chdir(cur_dir)
        return True

    def _is_turkey_data(self):
        return 'EU' in self.options.database or 'TUR' in self.options.database

    def _retrieve_turkey_ocean(self):
        if not self._is_turkey_data():
            return True

        extractor_dir = os.path.join(self.adaptor, 'customized/turkey/tools')
        if not os.path.exists(extractor_dir):
            logging.info('Turkey ocean extractor tool dir not exists!')
            return True
        extractor = os.path.join(extractor_dir, 'country_extractor.py')
        if not os.path.exists(extractor):
            logging.info('Turkey ocean extractor tool not exists!')
            return True

        cur_dir = os.getcwd()
        os.chdir(extractor_dir)

        args = ['-H %s' % self.options.host,
                '-D %s' % self.options.database,
                '-U %s' % self.options.user,
                '-P %s' % self.options.port,
                '-p %s' % self.options.passwd,
                '-t ocean',
                'turkey_ocean']

        cmd = 'python2.7 country_extractor.py %s' % ' '.join(args)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('Fail to extract turkey ocean for %s' % args)
            os.chdir(cur_dir)
            return False

        os.chdir(cur_dir)
        return True

    def _need_remove_premium(self):
        return 'remove_premium' in self.opts

    def _need_divide(self):
        return 'divide' in self.opts

    def _need_modify(self):
        return 'modify' in self.opts

    def _get_premium_sql_file(self):
        sql_files = glob.glob(os.path.join(self.adaptor, 'premium', '*.sql'))
        if not sql_files:
            return None

        # find the best match sql file
        region, version = self._parse_database_name(self.options.database)
        if not region or not version:
            logging.warning('Can not extract region/version from %s' % self.options.database)
            return None

        sql_files.sort()
        matched = self._get_matched_sql_files(sql_files, region, version)
        if matched:
            return matched[-1]

        matched = self._get_matched_sql_files(sql_files, region)
        if matched:
            return matched[-1]

        return None

    def _get_matched_sql_files(self, sql_files, region, version=None):
        base_names = (os.path.splitext(os.path.basename(sql_file))[0] for sql_file in sql_files)
        version_info = (self._parse_database_name(n) for n in base_names)
        sql_file_info = zip(version_info, sql_files)

        if version:
            return [info[1] for info in sql_file_info if info[0] == (region, version)]
        else:
            return [info[1] for info in sql_file_info if info[0][0] == region]

    def _parse_database_name(self, db_name):
        """
            Database name format: XX_YYZZZZ_OO or XX_YY_ZZZZ_OO (eg. HERE_NA15Q1_1)'
            XX   : Data vendor'
            YY   : Region'
            ZZZZ : Data version, for example 15Q1'
            OO   : Other information'
        """
        import re
        m = re.match('[^_]+_([a-zA-Z]+)_?(\d+Q\d)', db_name, re.IGNORECASE)
        if m:
            return m.group(1).upper(), m.group(2).upper()
        else:
            return None, None

    def _format_psql_args(self):
        args = ['-h %s' % self.options.host,
                '-p %s' % self.options.port,
                '-U %s' % self.options.user,
                '%s' % self.options.database,
                ]

        return ' '.join(args)


def init_logging(options):
    dbname = options.database

    filepath = 'dbprocess_%s_%s.log' % (dbname, time.strftime('%y%m%d_%H%M%S'))
    logging.basicConfig(filename=filepath, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def validate(options):
    if not options.host:
        sys.stderr.write('Error: host is not specified\n')
        return False

    if not options.adaptor or not os.path.exists(options.adaptor):
        sys.stderr.write('Error: Adaptor directory not exists!\n')
        return False

    return True


def main():
    import optparse

    parser = optparse.OptionParser()

    parser.add_option('-H', '--host', help='hostname', dest='host')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')

    parser.add_option('-A', '--adaptor', help='adaptorG2 path', dest='adaptor')
    parser.add_option('-o', '--db-operations', help='database operations', dest='db_opts', default='divide|modify')

    options, args = parser.parse_args()

    if not validate(options):
        parser.print_help()
        sys.exit(-1)

    init_logging(options)

    processor = DbProcessor(options)
    r = processor.process()

    if not r:
        sys.exit(-1)


if __name__ == '__main__':
    main()
