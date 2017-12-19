import os
import sys
import shutil
import logging
from archive import extract


class RDFArchive(object):
    def __init__(self, rdf_dir, rdf_archived_dir):
        self.rdf_dir = os.path.abspath(rdf_dir)
        self.rdf_archived_dir = os.path.abspath(rdf_archived_dir)

        self.rdf_software = None
        self.decompressed_dirs = set()

    def __del__(self):
        for path in self.decompressed_dirs:
            if os.path.exists(path):
                shutil.rmtree(path)

    def archive(self):
        try:
            self._decompress_imp(self.rdf_dir)
            self._archive()
            return True
        except shutil.Error, e:
            logging.error('RDF Archive error: %s' % e)
            return False

    def _decompress(self):
        self._decompress_imp(self.rdf_dir)

    def _decompress_imp(self, rdf_dir):
        # skip rdf software directory
        if self._in_rdf_software_path(rdf_dir):
            return

        # find all compressed files
        file_paths = (os.path.join(rdf_dir, f) for f in os.listdir(rdf_dir))
        compressed_files = (f for f in file_paths if RDFArchive._is_compressed(f))

        # decompress files
        for compress_file in compressed_files:
            dir_name, basename = os.path.dirname(compress_file), os.path.basename(os.path.splitext(compress_file)[0])
            decompressed_dir = os.path.join(dir_name, basename)
            self.decompressed_dirs.add(decompressed_dir)
            if not os.path.exists(decompressed_dir):
                os.makedirs(decompressed_dir)

            try:
                logging.info('decompress %s to %s ' % (compress_file, decompressed_dir))
                extract(compress_file, decompressed_dir)
            except Exception, e:
                logging.error('Error: decompress %s failed, msg=%s \n' % (compress_file, e))
                sys.exit(-1)

        # recursively decompress
        file_paths = (os.path.join(rdf_dir, f) for f in os.listdir(rdf_dir))
        dir_paths = (f for f in file_paths if os.path.isdir(f))
        for dir_path in dir_paths:
            self._decompress_imp(dir_path)

    @staticmethod
    def _is_compressed(f):
        for ext in ['.tar', '.zip', '.tgz', '.tar.gz']:
            if f.endswith(ext):
                return True
        return False

    def _in_rdf_software_path(self, path):
        rdf_software = self._get_rdf_software_path(path)

        if not rdf_software:
            return False

        return os.path.abspath(path).find(os.path.abspath(rdf_software)) != -1

    def _get_rdf_software_path(self, path):
        if self.rdf_software:
            return self.rdf_software

        path = os.path.abspath(path)
        for root, dirs, files in os.walk(path):
            if 'RDF' not in dirs:
                continue

            if 'BIN' in os.listdir(os.path.join(root, 'RDF')):
                self.rdf_software = os.path.join(root, 'RDF')
                return self.rdf_software

        return self.rdf_software

    def _archive(self):
        prefix = self._get_rdf_data_prefix(self.rdf_dir)
        rdf_packages, rdf_software = self._get_target_rdf_packages(self.rdf_dir)

        self._archive_rdf(rdf_packages, rdf_software, prefix)

    @staticmethod
    def _get_rdf_data_prefix(rdf_dir):
        for root, dirs, files in os.walk(rdf_dir):
            for f in files:
                if not f.upper().endswith('_ALLFILES.TAR') and 'rdf_customer_software' not in f:
                    continue

                return os.path.splitext(f)[0].split('_')[0]

        return ''

    def _get_target_rdf_packages(self, rdf_dir):
        rdf_packages = []

        package_list = ['CORE', 'WKT', 'SDO', 'ADAS']
        for root, dirs, files in os.walk(rdf_dir):
            if self._in_rdf_software_path(root):
                continue
            rdf_packages.extend([os.path.join(root, d) for d in dirs if d in package_list])

        if not self.rdf_software:
            logging.error('no rdf customer software is found!')
            sys.exit(-1)
        if not rdf_packages:
            logging.error('no rdf data is found!')
            sys.exit(-1)

        return rdf_packages, self.rdf_software

    def _archive_rdf(self, rdf_packages, rdf_software, prefix):
        self._clear_archive_dir()

        rdf_package_dir = os.path.join(self.rdf_archived_dir, '%s_ALLFiles' % prefix)
        rdf_software_dir = os.path.join(self.rdf_archived_dir, '%s_rdf_customer_software' % prefix)

        if not os.path.exists(rdf_package_dir):
            os.makedirs(rdf_package_dir)
        if not os.path.exists(rdf_software_dir):
            os.makedirs(rdf_software_dir)

        for package in rdf_packages:
            logging.info('Move %s to %s' % (package, rdf_package_dir))
            shutil.move(package, rdf_package_dir)

        logging.info('Move %s to %s' % (rdf_software, rdf_software_dir))
        shutil.move(rdf_software, rdf_software_dir)

        return self.rdf_archived_dir

    def _clear_archive_dir(self):
        if not os.path.exists(self.rdf_archived_dir):
            return

        shutil.rmtree(self.rdf_archived_dir)
        os.makedirs(self.rdf_archived_dir)

        if not os.path.exists(self.rdf_archived_dir):
            logging.error('cannot make dir %s\n' % self.rdf_archived_dir)
            sys.exit(-1)


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    import optparse
    parser = optparse.OptionParser()

    parser.add_option('-r', '--rdf', help='rdf', dest='rdf')
    parser.add_option('-c', '--archive', help='archive', dest='archive')

    options, args = parser.parse_args()
    if not options.rdf and not options.archive:
        sys.stderr.write('Error: rdf or archive dir not exists\n')
        parser.print_help()
        sys.exit(-1)

    arc = RDFArchive(options.rdf, options.archive)
    arc.archive()


if __name__ == '__main__':
    main()
