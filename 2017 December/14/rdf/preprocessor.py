import os
import re
import sys
import glob
import shutil
import tempfile
import logging
from util.misc import safe_execute
from rdf_archive import RDFArchive


class PreProcessor(object):
    DIR_COM = 'components'
    DIR_RDF = '__rdf'
    DIR_RDF_WEU = '__rdf_weu'
    DIR_RDF_ADD = '__rdf_add'

    DIR_SAFETY_CAMERA = 'components/speed_camera'

    REGION_EU = 'EU'

    def __init__(self, data, archive_dir, region, installer):
        self.data = data
        self.archive_dir = archive_dir
        self.region = region
        self.installer = installer  # HERE map tool

        self.rdf_dir = None
        self.rdf_dir_weu = None
        self.rdf_dir_add = None

        self.archived_rdf = None
        self.archived_rdf_add = []

    def process(self):
        if not self._process_safety_camera():
            return False

        if not self._process_rdf():
            return False

        return True

    def _process_safety_camera(self):
        # decompress the safety camera if it's archived.
        safety_camera_dir = os.path.join(self.data, PreProcessor.DIR_SAFETY_CAMERA)
        if not os.path.exists(safety_camera_dir) or not os.listdir(safety_camera_dir):
            logging.info('safety camera dir not exists %s' % PreProcessor.DIR_SAFETY_CAMERA)
            return True

        safety_camera_files = [os.path.join(safety_camera_dir, f) for f in os.listdir(safety_camera_dir)]
        if PreProcessor._is_all_tar_files(safety_camera_files):
            for safety_camera_file in safety_camera_files:
                cmd = 'tar xf %s -C %s' % (safety_camera_file, safety_camera_dir)
                logging.info(cmd)
                safe_execute(cmd)

        return True

    def _process_rdf(self):
        if not self._pre_process_rdf():
            return False

        if not self._archive_rdf():
            return False

        return True

    def _archive_rdf(self):
        clipper = os.path.abspath(os.path.join(self.installer, 'clip_RDF.sh'))

        if not self.rdf_dir:
            logging.error('No RDF found in %s' % self.data)
            return False

        base_archive_dir = os.path.join(self.archive_dir, 'base_rdf')
        if not archive_rdf(clipper, self.rdf_dir, base_archive_dir):
            logging.error('Archive RDF failed %s' % self.rdf_dir)
            return False
        self.archived_rdf = base_archive_dir

        if self.rdf_dir_weu:
            weu_archive_dir = os.path.join(self.archive_dir, 'weu_rdf')
            if not archive_rdf(clipper, self.rdf_dir_weu, weu_archive_dir):
                logging.error('Archive RDF failed %s' % self.rdf_dir_weu)
                return False
            self.archived_rdf_add.append(weu_archive_dir)

        if self.rdf_dir_add:
            countries = self._get_add_countries(self.region)
            add_archive_dir = os.path.join(self.archive_dir, 'add_rdf')
            if not archive_rdf(clipper, self.rdf_dir_add, add_archive_dir, countries):
                logging.error('Archive RDF failed %s' % self.rdf_dir_add)
                return False
            self.archived_rdf_add.append(add_archive_dir)

        return True

    @staticmethod
    def _get_add_countries(region):
        import util.add_config
        return util.add_config.get_add_countries(region)

    def _pre_process_rdf(self):
        if not self._pre_process_rdf_default():
            return False

        if not self._pre_process_rdf_eu():
            return False

        return True

    def _pre_process_rdf_eu(self):
        if self.region.upper() != PreProcessor.REGION_EU:
            return True

        weu_rdf_files = PreProcessor._get_weu_files(self.rdf_dir)
        if not weu_rdf_files:
            logging.error('West Europe RDF data not found in %s' % self.rdf_dir)
            return False

        # All Europe data including East & West Europe are placed together, move West Europe
        # to __rdf_weu
        weu_rdf_dir = os.path.join(self.data, PreProcessor.DIR_RDF_WEU)
        if not os.path.exists(weu_rdf_dir):
            os.makedirs(weu_rdf_dir)

        for weu_file in weu_rdf_files:
            shutil.move(weu_file, weu_rdf_dir)

        self.rdf_dir_weu = weu_rdf_dir

        return True

    def get_rdf_dir(self):
        return self.archived_rdf

    def get_rdf_dir_additional(self):
        return self.archived_rdf_add

    def _pre_process_rdf_default(self):
        rdf_dir = os.path.join(self.data, PreProcessor.DIR_RDF)

        if not os.path.exists(rdf_dir):
            logging.error('RDF data directory %s not exists\n' % rdf_dir)
            return False
        self.rdf_dir = rdf_dir

        add_rdf_dir = os.path.join(self.data, PreProcessor.DIR_RDF_ADD)
        if os.path.exists(add_rdf_dir) and os.listdir(add_rdf_dir):
            self.rdf_dir_add = add_rdf_dir

        return True

    @staticmethod
    def _get_weu_files(rdf):
        weu_files = glob.glob(os.path.join(rdf, "UW*.tar"))
        return weu_files

    @staticmethod
    def _is_all_tar_files(files):
        for f in files:
            if not (os.path.isfile(f) and os.path.splitext(f)[1].upper() == '.TAR'):
                return False

        return True


def clip_rdf(clipper, rdf_dir, out_rdf_dir, countries):
    os.chdir(os.path.dirname(clipper))

    cmd = '{clipper} -rdf {rdf} -countries {countries} -out {out_rdf}'.format(clipper=clipper,
                                                                              rdf=rdf_dir,
                                                                              countries=','.join(countries),
                                                                              out_rdf=out_rdf_dir)
    #print cmd
    safe_execute(cmd)

    return True


def archive_rdf(clipper, rdf_dir, archive_rdf_dir, countries=None):
    cwd = os.getcwd()

    archived = False
    try:
        archived = archive_rdf_imp(clipper, rdf_dir, archive_rdf_dir, countries)
        print archived
    finally:
        os.chdir(cwd)

    return archived


def archive_rdf_imp(clipper, rdf_dir, archive_rdf_dir, countries=None):
    if not os.path.exists(archive_rdf_dir):
        os.makedirs(archive_rdf_dir)

    if countries is None:
        # TODO: archive successfully or not
        archive = RDFArchive(rdf_dir, archive_rdf_dir)
        if not archive.archive():
            return False
    else:
        tmp_dir_root = os.path.dirname(archive_rdf_dir)
        tmp_base_rdf = tempfile.mkdtemp(prefix='base_', dir=archive_rdf_dir)
        # os.chmod(rdf_tmp_dir, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)
        archive = RDFArchive(rdf_dir, tmp_base_rdf)
        if not archive.archive():
            return False

        tmp_clip_rdf = tempfile.mkdtemp(prefix='clip_', dir=archive_rdf_dir)
        clip_rdf(clipper, tmp_base_rdf, tmp_clip_rdf, countries)

        try:
            for p in os.listdir(tmp_clip_rdf):
                package = os.path.join(tmp_clip_rdf, p)
                logging.info('Move %s to %s' % (package, archive_rdf_dir))
                shutil.move(package, archive_rdf_dir)

            logging.info('Remove tmp base rdf directory tree %s' % tmp_base_rdf)
            shutil.rmtree(tmp_base_rdf)
            logging.info('Remove tmp clip rdf directory tree %s' % tmp_clip_rdf)
            shutil.rmtree(tmp_clip_rdf)
        except Exception, e:
            logging.error('error=[%s]' % e)
            return False

    return True


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    if len(sys.argv) != 5:
        print '%s rdf_data archived_rdf_dir region installer' % os.path.basename(sys.argv[0])
        return

    rdf_data = sys.argv[1]
    archived_rdf_dir = sys.argv[2]
    region = sys.argv[3]
    installer = sys.argv[4]

    pp = PreProcessor(rdf_data, archived_rdf_dir, region, installer)
    pp.process()

    print pp.get_rdf_dir()
    print pp.get_rdf_dir_additional()


if __name__ == '__main__':
    main()
