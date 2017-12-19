import re
import os
import sys
import time
import optparse
import shutil
import logging
import stat
import tempfile
import glob

from util.misc import safe_execute


def execute(cmd):
    logging.info(cmd)
    r = os.system(cmd)
    if r != 0:
        logging.error('execute(%s) failed' % cmd)
        sys.exit(-1)

    return True


class RDFImporter(object):
    """
        class comment
    """
    ARCHIVE = 'archive'

    def __init__(self, rdf_dir, rdf_loader, adaptor, option):
        self.rdf_dir = rdf_dir
        self.rdf_loader = rdf_loader
        self.adaptor = adaptor

        self.decompress_dirs = []

        self.option = option

        self.archive = None

        self.rdf_software = None

    def __del__(self):
        self.__clear_archive()

    def _validate(self):
        if not os.path.isdir(self.rdf_dir):
            logging.error('Error: rdf data path [%s] should be directory!' % self.rdf_dir)
            return False

        return True

    def import_rdf(self):
        if not self._validate():
            return False

        #self.archive = self._get_tmp_dir(parent_dir=self.rdf_dir, prefix=self.ARCHIVE)

        #self.__prepare_rdf_data(self.rdf_dir, self.archive)

        #self.__install_rdf(self.archive)

        self.__install_rdf(self.rdf_dir)

        # if not self.__post_process():
        #     return False

        return True

    # def __post_process(self):
    #     if not self._remove_premium():
    #         return False
    #
    #     if not self._split_database():
    #         return False
    #
    #     if not self._modify_database():
    #         return False
    #
    #     return True

    # def _remove_premium(self):
    #     if not self._need_remove_premium():
    #         logging.info('Skip premium removal')
    #         return True
    #
    #     sql_file = self._get_premium_sql_file()
    #     logging.info('Best matched premium sql file for %s is %s' % (self.option.database, sql_file))
    #     if not sql_file or not os.path.exists(sql_file):
    #         logging.error('Can not find premium sql file')
    #         return False
    #
    #     args = self._format_psql_args()
    #     cmd = 'psql %s -v ON_ERROR_STOP=1 -f %s' % (args, sql_file)
    #     logging.info(cmd)
    #     r = os.system(cmd)
    #     if r:
    #         logging.error('remove premium failed!')
    #         return False
    #
    #     return True
    #
    # def _need_remove_premium(self):
    #     return self.option.remove_premium.upper() in ['TRUE', 'YES', 'Y', '1']
    #
    # def _get_premium_sql_file(self):
    #     sql_files = glob.glob(os.path.join(self.adaptor, 'premium', '*.sql'))
    #     if not sql_files:
    #         return None
    #
    #     # find the best match sql file
    #     region, version = self._parse_database_name(self.option.database)
    #     if not region or not version:
    #         logging.warning('Can not extract region/version from %s' % self.option.database)
    #         return None
    #
    #     sql_file_info = []
    #
    #     for sql_file in sql_files:
    #         base_name = os.path.basename(os.path.splitext(sql_file)[0])
    #         r, v = self._parse_database_name(base_name)
    #         if not r or not v:
    #             logging.warning('Can not extract region/version from %s' % sql_file)
    #             continue
    #
    #         sql_file_info.append((r, v, sql_file))
    #
    #     sql_file_info.sort()
    #
    #     premium_sql_info = [i for i in sql_file_info if i[0] == region and i[1] == version]
    #     if premium_sql_info:
    #         return premium_sql_info[-1][2]
    #
    #     # only match region if no matched data version
    #     premium_sql_info = [i for i in sql_file_info if i[0] == region]
    #     if premium_sql_info:
    #         return premium_sql_info[-1][2]
    #
    #     return None
    #
    # def _parse_database_name(self, db_name):
    #     """
    #         Database name format: XX_YYZZZZ_OO or XX_YY_ZZZZ_OO (eg. HERE_NA15Q1_1)'
    #         XX   : Data vendor'
    #         YY   : Region'
    #         ZZZZ : Data version, for example 15Q1'
    #         OO   : Other information'
    #     """
    #     import re
    #     m = re.match('[^_]+_([a-zA-Z]+)_?(\d+Q\d)', db_name, re.IGNORECASE)
    #     if m:
    #         return m.group(1).upper(), m.group(2).upper()
    #     else:
    #         return None, None

    def _format_psql_args(self):
        args = ['-h %s' % self.option.host,
                '-p %s' % self.option.port,
                '-U %s' % self.option.user,
                '%s' % self.option.database,
                ]

        return ' '.join(args)

    def __prepare_rdf_data(self, rdf_dir, archive_dir):
        assert os.path.isdir(self.rdf_dir)

        prefix = self.__get_rdf_data_prefix(rdf_dir)

        os.chmod(rdf_dir, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)

        self.__decompress_tar_files(rdf_dir)

        rdf_packages, rdf_software = self.__get_target_rdf_packages(rdf_dir)

        self.__archive_rdf(archive_dir, rdf_packages, rdf_software, prefix)

    def __decompress_tar_files(self, rdf_dir):
        for root, dirs, files in os.walk(rdf_dir):
            if root.find(self.archive) != -1:
                continue

            if self.__in_rdf_software_path(root):
                continue

            for f in files:
                if not f.endswith('.tar') and not f.endswith('.zip'):
                    continue

                compressed_file = os.path.join(root, f)
                decompressed_dir = os.path.join(root, os.path.splitext(f)[0])

                self.__decompress(compressed_file, decompressed_dir)

                self.__decompress_rdf_packages(decompressed_dir)

                self.decompress_dirs.append(decompressed_dir)

    def __decompress_rdf_packages(self, rdf_dir):
        for root, dirs, files in os.walk(rdf_dir):
            for f in files:
                if self.__is_rdf_core_tar(f):
                    cmd = 'tar xf %s -C %s' % (os.path.join(root, f), root)
                    execute(cmd)

    @staticmethod
    def __is_rdf_core_tar(tar):
        base, ext = os.path.splitext(os.path.basename(tar))

        if ext != '.tar':
            return False

        for suffix in ['CORE', 'WKT', 'SDO', 'ADAS']:
            if base.upper().endswith(suffix):
                return True

        return False

    def __decompress(self, compressed_file, decompressed_dir):
        if not os.path.exists(decompressed_dir):
            os.makedirs(decompressed_dir)

        cmd = ''
        if compressed_file.endswith('.tar'):
            cmd = 'tar xf %s -C %s' % (compressed_file, decompressed_dir)
        elif compressed_file.endswith('.zip'):
            cmd = 'unzip -q %s -d %s' % (compressed_file, decompressed_dir)

        if cmd:
            execute(cmd)

    def __get_rdf_data_prefix(self, rdf_dir):
        for root, dirs, files in os.walk(rdf_dir):
            for f in files:
                if not f.upper().endswith('_ALLFILES.TAR'):
                    continue

                return os.path.splitext(f)[0].split('_')[0]

        return ''

    def __get_rdf_software_path(self, path):
        if self.rdf_software:
            return self.rdf_software

        for root, dirs, files in os.walk(path):
            if 'RDF' not in dirs:
                continue

            if 'BIN' in os.listdir(os.path.join(root, 'RDF')):
                self.rdf_software = os.path.join(root, 'RDF')
                return self.rdf_software

        return self.rdf_software

    def __in_rdf_software_path(self, path):
        # if self.rdf_software and path.find(self.rdf_software) != -1:
        #     return True
        #
        # items = path.split(os.sep)
        # if 'RDF' not in items:
        #     return False
        #
        # if items[-1] == 'RDF':
        #     self.rdf_software = path  # set rdf software
        #     return 'BIN' in os.listdir(path)
        # else:
        #     return 'BIN' in items and (items.index('RDF') == items.index('BIN') - 1)

        rdf_software = self.__get_rdf_software_path(path)

        if not rdf_software:
            return False

        return os.path.abspath(path).find(os.path.abspath(rdf_software)) != -1

    def __get_target_rdf_packages(self, rdf_dir):
        rdf_packages = []
        # rdf_software = ''

        package_list = ['CORE', 'WKT', 'SDO', 'ADAS']
        for root, dirs, files in os.walk(rdf_dir):
            if os.path.basename(root) == RDFImporter.ARCHIVE:
                continue

            if self.__in_rdf_software_path(root):
                continue

            rdf_packages.extend([os.path.join(root, d) for d in dirs if d in package_list])

            # for d in dirs:
            #     if d.upper() in ['CORE', 'WKT', 'SDO', 'ADAS']:
            #         rdf_packages.append(os.path.join(root, d))
                #elif d in ['RDF'] and root.endswith('customer_software'):

                # if self.__is_rdfsoftware(os.path.join(root, d)):
                #     rdf_software = os.path.join(root, d)

        if not self.rdf_software:
            logging.error('no rdf customer software is found!')
            sys.exit(-1)
        if not rdf_packages:
            logging.error('no rdf data is found!')
            sys.exit(-1)

        # return rdf_packages, rdf_software
        return rdf_packages, self.rdf_software

    def __archive_rdf(self, archive_dir, rdf_packages, rdf_software, prefix):
        # archive_dir = self._get_tmp_dir(parent_dir=rdf_dir, prefix=self.ARCHIVE)
        #
        # # set archive directory
        # self.archive = archive_dir

        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        if not os.path.exists(archive_dir):
            logging.error('cannot make dir %s' % archive_dir)
            sys.exit(-1)

        rdf_package_dir = os.path.join(archive_dir, '%s_ALLFiles' % prefix)
        rdf_software_dir = os.path.join(archive_dir, '%s_rdf_customer_software' % prefix)

        if not os.path.exists(rdf_package_dir):
            os.makedirs(rdf_package_dir)
        if not os.path.exists(rdf_software_dir):
            os.makedirs(rdf_software_dir)

        for package in rdf_packages:
            logging.info('Move %s to %s' % (package, rdf_package_dir))
            shutil.move(package, rdf_package_dir)

        logging.info('Move %s to %s' % (rdf_software, rdf_software_dir))
        shutil.move(rdf_software, rdf_software_dir)

        return archive_dir

    def __clear_archive(self):
        for path in self.decompress_dirs:
            if os.path.exists(path):
                shutil.rmtree(path)

        if self.archive and os.path.exists(self.archive):
            shutil.rmtree(self.archive)

    def __install_rdf(self, rdf_dir):
        """
        ./install_RDF.sh  -jdbcurl jdbc:postgresql://10.224.76.206:5432/NT_NA14Q1_1 -user postgres  -rdfdir /data/01/rdf/na/14q1 -tempdir /data/01/lgwu/tmp/14q1/  -pass postgres -wkt -wktString
        """
        option = self.option

        curdir = os.getcwd()

        os.chdir(self.rdf_loader)

        self._preprocess_rdf_installer()

        jdbc = '-jdbcurl jdbc:postgresql://%s:%s/%s' % (option.host, option.port, option.database)
        user = '-user %s' % option.user
        passwd = '-pass %s ' % option.passwd
        rdfdir = '-rdfdir %s' % rdf_dir
        tempdir = '-tempdir %s' % self._get_tmp_dir(rdf_dir)
        merge = option.mode.strip()
        merge = '' if merge != 'merge' else '-merge'
        print 'option mode: %s' % merge 
        cmd = './install_RDF.sh %s -wkt -wktString' % ' '.join((merge, jdbc, user, passwd, rdfdir, tempdir))
        print 'install rdf command: %s' % cmd
        logging.info(cmd)
        
        r = os.system(cmd)
        if r:
            logging.error("Load RDF to Postgres failed!")
            os.chdir(curdir)
            sys.exit(-1)
            
        os.chdir(curdir)

    def _get_tmp_dir(self, parent_dir, prefix=''):
        rdf_tmp_dir = tempfile.mkdtemp(prefix=prefix, dir=parent_dir)
        os.chmod(rdf_tmp_dir, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)
        return rdf_tmp_dir

    # def _split_database(self):
    #     cur_dir = os.getcwd()
    #     os.chdir(self.adaptor)
    #
    #     args = ['-H %s' % self.option.host,
    #             '-D %s' % self.option.database,
    #             '-U %s' % self.option.user,
    #             '-P %s' % self.option.port,
    #             '-p %s' % self.option.passwd ]
    #
    #     cmd = 'python2.7 TableDivider.py %s' % ' '.join(args)
    #     logging.info(cmd)
    #     r = os.system(cmd)
    #     if r:
    #         logging.error('Fail to data division for %s' % args)
    #         os.chdir(cur_dir)
    #         return False
    #
    #     os.chdir(cur_dir)
    #     return True

    # def _modify_database(self):
    #     cur_dir = os.getcwd()
    #     os.chdir(self.adaptor)
    #
    #     args = ['-H %s' % self.option.host,
    #             '-D %s' % self.option.database,
    #             '-U %s' % self.option.user,
    #             '-P %s' % self.option.port,
    #             '-p %s' % self.option.passwd,
    #             '-m ']
    #
    #     cmd = 'python2.7 TableDivider.py %s' % ' '.join(args)
    #     logging.info(cmd)
    #     r = os.system(cmd)
    #     if r:
    #         logging.error('Fail to modify database for %s' % args)
    #         os.chdir(cur_dir)
    #         return False
    #
    #     os.chdir(cur_dir)
    #     return True

    def _preprocess_rdf_installer(self):
        os.system("""awk '{ sub("\r$", ""); print }' install_RDF.sh  > tmp.sh""")
        os.system('mv tmp.sh install_RDF.sh')
        os.system('chmod 755 install_RDF.sh')


def init_logging(options):
    dbname = options.database

    filepath = 'rdfimport_%s_%s.log' % (dbname, time.strftime('%y%m%d_%H%M%S'))
    logging.basicConfig(filename=filepath, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def validate(options):
    if not options.rdfdata or not os.path.exists(options.rdfdata):
        print 'Error: RDF data directory not exists!'
        return False
    if not options.adaptor or not os.path.exists(options.adaptor):
        print 'Error: Adaptor directory not exists!'
        return False
    if not options.installer or not os.path.exists(options.installer):
        print 'Error: RDF Installer directory not exists!'
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
    parser.add_option('-A', '--adaptor', help='adaptorG2 path', dest='adaptor')
    parser.add_option('-I', '--installer', help='RDF Installer Tool', dest='installer')
    parser.add_option('-d', '--data', help='RDF data dir', dest='rdfdata')

    options, args = parser.parse_args()

    if not validate(options):
        parser.print_help()
        sys.exit(-1)

    init_logging(options)

    importer = RDFImporter(options.rdfdata, options.installer, options.adaptor, options)

    r = importer.import_rdf()

    if not r:
        sys.exit(-1)

if __name__ == '__main__':
    main()

