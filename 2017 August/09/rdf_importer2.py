import re
import os
import sys
import time
import optparse
import shutil
import logging
import stat
import glob
import tempfile
import copy

from distutils.spawn import find_executable

import pgconnect
import import_rdf
import loadLmInfo
import postcode_importer
import import_hamlet
import import_gjv
import import_korea_addr
import import_toll_cost
import db_process

from preprocessor import PreProcessor
from cn_add_content.AddContentExtractor import AddContentExtractor
from cn_add_content.AddContentImporter import AddContentImporter




class LoadOption(object):
    # source name list
    SRC_NAME_RDF = ['rdf']
    SRC_NAME_3D_LANDMARK = ['3dlandmark', '3d_landmark']
    SRC_NAME_GJV = ['gjv']
    SRC_NAME_JUNCTION = ['junction']
    SRC_NAME_POSTAL_CODE = ['postal_code']
    SRC_NAME_SPEED_CAMERA = ['speed_camera', 'safety_camera']
    SRC_NAME_SPEED_PATTERN = ['speed_pattern']
    SRC_NAME_SENSITIVE_ISLAND = ['level0', 'sensitive_island', 'sensitive']
    SRC_NAME_CN_ADD_CONTENT = ['cn_add_content', 'cn_additional_content']
    SRC_NAME_HAMLET = ['hamlet']
    SRC_NAME_KOR_NEW_ADDRESS = ['new_address', 'korea_new_address', 'kor_new_address']
    SRC_NAME_KOR_TOLL_COST = ['toll_cost']

    def __init__(self, sources=None):
        self.src = []

        sources = sources.split('|') if sources else []
        self.load_rdf = self._check_options(sources, LoadOption.SRC_NAME_RDF)
        self.load_3d_landmark = self._check_options(sources, LoadOption.SRC_NAME_3D_LANDMARK)
        self.load_gjv = self._check_options(sources, LoadOption.SRC_NAME_GJV)
        self.load_kor_new_addr = self._check_options(sources, LoadOption.SRC_NAME_KOR_NEW_ADDRESS)
        self.load_junction = self._check_options(sources, LoadOption.SRC_NAME_JUNCTION)
        self.load_postal_code = self._check_options(sources, LoadOption.SRC_NAME_POSTAL_CODE)
        self.load_speed_camera = self._check_options(sources, LoadOption.SRC_NAME_SPEED_CAMERA)
        self.load_speed_pattern = self._check_options(sources, LoadOption.SRC_NAME_SPEED_PATTERN)
        self.load_sensitive_island = self._check_options(sources, LoadOption.SRC_NAME_SENSITIVE_ISLAND)
        self.load_cn_add_content = self._check_options(sources, LoadOption.SRC_NAME_CN_ADD_CONTENT)
        self.load_hamlet = self._check_options(sources, LoadOption.SRC_NAME_HAMLET)
        self.load_toll_cost = self._check_options(sources, LoadOption.SRC_NAME_KOR_TOLL_COST)

    def sources(self):
        return ', '.join(self.src)

    def load_all(self):
        import inspect

        members = ((n, v) for n, v in inspect.getmembers(self) if n.startswith('load_') and isinstance(v, bool))
        for name, value in members:
            setattr(self, name, True)

    def _check_options(self, sources, source_names):
        for comp in sources:
            if comp in source_names:
                self.src.append(source_names[0])
                return True
        return False


class Importer(object):
    """
        class comment
    """
    DT_RDF                      = '__rdf'
    DT_POSTAL_CODE              = 'components/postal_code'
    DT_3D_LANDMARK              = 'components/3dlandmark_vendor'
    DT_SAFETY_CAMERA            = 'components/speed_camera'
    DT_GJV                      = 'components/GJV'
    DT_LEVEL0_SENSITIVE_ISLAND  = 'components/level0'
    DT_LEVEL2_SENSITIVE_ISLAND  = 'components/level2_sensitive'
    DT_CN_ADD_CONTENT           = 'components/additional_content'
    DT_HAMLET                   = 'components/hamlet'
    DT_KOR_NEW_ADDRESS          = 'components/NEW_ADDRESS'
    DT_KOR_TOLL_COST            = 'components/TOLL_COST'

    RDF_INSTALLER_FLAG = 'Map_Tools_'

    XML_IMPORTER = 'import_XML.sh'

    SAFETY_CAMERA_TABLE = "public.xml_safety_camera_poi"
    SAFETY_CAMERA_LOC_TABLE = "public.xml_safety_camera_loc"
    SAFETY_CAMERA_BK_TABLE = "public.xml_safety_camera_poi_bk"


    

    def __init__(self, data_dir, importer, adaptor, option):
        self.data_dir = os.path.abspath(data_dir)
        self.importer = os.path.abspath(importer)  # importer path
        self.adaptor = os.path.abspath(adaptor)  # adaptor path

        self.option = option

        self.src_options = self._check_source_list()

        self.pre_processor = None

    def import_all(self):
        logging.info("Loading list: [%s]\n" % self.src_options.sources())

        if not self._pre_process():
            return False

        if not self._create_db():
            return False

        if not self._import_toll_cost():
            return False

        if not self._import_hamlet():
            return False

        if not self._import_kor_new_address():
            return False

        if not self._import_gjv():
            return False

        if not self._import_postal_code():
            return False

        if not self._import_3d_landmark():
            return False

        if not self._import_safety_camera():
            return False

        if not self._import_rdf():
            return False

        if not self._import_sensitive_island():
            return False

        if not self._import_cn_add_content():
            return False

        if not self._db_process():
            return False

        return True

    def _pre_process(self):
        region, version = Importer._parse_database(self.option.database)
        if not region or not version:
            logging.error('Can not parse (region, version) from database %s' % self.option.database)
            return False

        # Pre Processor
        self.pre_processor = PreProcessor(self.data_dir, region)
        if not self.pre_processor.process():
            logging.error('RDF data pre-process failed %s' % self.data_dir)
            return False

        return True

    def _import_rdf(self):
        if not self.src_options.load_rdf:
            return True

        # rdf_data = self._get_rdf_data()
        # if not rdf_data:
        #     logging.error('No rdf data found in %s' % self.data_dir)
        #     return False

        rdf_data = self.pre_processor.get_rdf_dir()

        rdf_installer = self._get_rdf_installer()
        if not rdf_installer:
            logging.error('No rdf installer tool found in %s' % self.importer)
            return False

        adaptor = self.adaptor
        options = copy.deepcopy(self.option)
        setattr(options, 'mode', 'normal')

        if not Importer._import_rdf_imp(rdf_data, rdf_installer, adaptor, options):
            return False

        # merge additional rdf
        rdf_data_add = self.pre_processor.get_rdf_dir_additional()
        options.mode = 'merge'
        if rdf_data_add:
            if not Importer._import_rdf_imp(rdf_data_add, rdf_installer, adaptor, options):
                return False

        return True

    @staticmethod
    def _import_rdf_imp(rdf_data, rdf_installer, adaptor, options):
        rdf_importer = import_rdf.RDFImporter(rdf_data, rdf_installer, adaptor, options)
        if not rdf_importer.import_rdf():
            logging.error('Failed to import rdf %s' % rdf_data)
            return False

        return True

    def _import_hamlet(self):
        if not self.src_options.load_hamlet:
            return True

        logging.info('Importing hamlet .......')

        hamlet_dir = self._get_hamlet_data()
        if not hamlet_dir:
            logging.error('No hamlet file found in %s' % self.data_dir)
            return False

        importer = import_hamlet.HamletImporter(self.option, hamlet_dir)
        if not importer.import_hamlet():
            logging.error('Import hamlet failed')
            return False

        logging.info('Importing hamlet done!')

        return True

    def _import_toll_cost(self):
        if not self.src_options.load_toll_cost:
            return True

        logging.info('Importing toll cost .......')

        toll_cost = self._get_toll_cost_data()
        if not toll_cost:
            logging.error('No toll cost dir found in %s' % self.data_dir)
            return False

        import copy
        option = copy.deepcopy(self.option)
        setattr(option, 'schema', 'addition')
        importer = import_toll_cost.TollCostImporter(option, toll_cost)
        if not importer.import_toll_cost():
            logging.error('Import toll cost failed')
            return False

        logging.info('Importing toll cost done!')

        return True

    def _import_kor_new_address(self):
        if not self.src_options.load_kor_new_addr:
            return True

        logging.info('Importing KOR new address .......')

        new_addr_dir = self._get_kor_new_addr_data()
        if not new_addr_dir:
            logging.error('No KOR new address file found in %s' % self.data_dir)
            return False

        importer = import_korea_addr.AddrImporter(self.option, new_addr_dir)
        if not importer.import_addr():
            logging.error('Import KOR new address failed')
            return False

        logging.info('Importing KOR new address done!')

        return True

    def _import_gjv(self):
        if not self.src_options.load_gjv:
            return True

        logging.info('Importing gjv .......')

        gjv_dir = self._get_gjv_data()
        if not gjv_dir:
            logging.error('No gjv file found in %s' % self.data_dir)
            return False

        importer = import_gjv.GjvImporter(self.option, gjv_dir)
        if not importer.import_gjv():
            logging.error('Import gjv failed')
            return False

        logging.info('Importing gjv done!')

        return True

    def _import_postal_code(self):
        if not self.src_options.load_postal_code:
            return True

        logging.info('Importing postal code .......')

        postal_code_data = self._get_postal_code_data()
        if not postal_code_data:
            logging.error('No postal code data found in %s' % self.data_dir)
            return False

        db_args = self._format_psycopg2_args()

        if not postcode_importer.import_postcodes(postal_code_data, db_args):
            logging.error('Import post code failed\n')
            return False

        logging.info('Importing postal code done!')

        return True

    def _import_3d_landmark(self):
        if not self.src_options.load_3d_landmark:
            return True

        logging.info('Importing 3d landmark .......')

        landmark = self._get_3d_landmark_data()
        if not landmark:
            logging.error('No 3d landmark data found in %s' % self.data_dir)
            return False

        db_args = self._format_psycopg2_args()

        if not loadLmInfo.loadLandmarkInfo(landmark, db_args):
            logging.error('Import 3d landmark failed')
            return False

        logging.info('Importing 3d landmark done!')

        return True

    def _import_safety_camera(self):
        if not self.src_options.load_speed_camera:
            return True

        logging.info('Importing safety camera .......')

        safety_camera = self._get_safety_camera_data()
        if not safety_camera:
            logging.error('no safety camera data found in %s' % self.data_dir)
            return False

        # xml_importer_src = os.path.join(self.importer, Importer.XML_IMPORTER)
        xml_importer_src = self._get_xml_importer()
        logging.info('import_XML tool path: %s\n' % xml_importer_src)
        if not os.path.exists(xml_importer_src):
            logging.error('import_XML tool not exists in %s' % self.importer)
            return False
        xml_importer_des = os.path.join(self._get_rdf_installer(), Importer.XML_IMPORTER)

        print xml_importer_src, xml_importer_des

        shutil.copyfile(xml_importer_src, xml_importer_des)
        # os.system('cp -f %s %s' % (xml_importer_src, xml_importer_des))
        if not os.path.exists(xml_importer_des):
            logging.error('copy import_XML to %s failed' % xml_importer_des)
            return False

        cur_dir = os.getcwd()
        os.chdir(os.path.dirname(xml_importer_des))
        os.chmod(xml_importer_des, stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO)

        # drop old camera data
        pgconn = pgconnect.PgConnect(self.option)
        if not self._preprocess_safety_camrea(pgconn):
            return False

        args = ['-jdbcurl jdbc:postgresql://%s:%s/%s' % (self.option.host, self.option.port, self.option.database),
                '-user %s' % self.option.user,
                '-pass %s' % self.option.passwd,
                '-xmldirs %s' % safety_camera,
                '-tableprefix xml_safety_camera_'
                ]

        cmd = './import_XML.sh %s' % ' '.join(args)
        print cmd

        r = os.system(cmd)
        if r:
            logging.error('import XML %s failed!' % safety_camera)
            os.chdir(cur_dir)
            return False

        os.chdir(cur_dir)

        # Special process for Korea safety camera
        if not self._postprocess_korea_safety_camera(pgconn):
            logging.error('Safety camrea postal process for Korea failed!')
            return False

        if not pgconn.exist(Importer.SAFETY_CAMERA_TABLE):
            logging.error('load table %s to postgis failed!\n' % Importer.SAFETY_CAMERA_TABLE)
            return False

        logging.info('Importing safety camera done!')

        return True

    def _preprocess_safety_camrea(self, pgconn):
        if not pgconn.init_db():
            logging.error('Can not connect to postgis when loading camera\n')
            return False

        for table in [Importer.SAFETY_CAMERA_LOC_TABLE, Importer.SAFETY_CAMERA_TABLE, Importer.SAFETY_CAMERA_BK_TABLE]:
            if not pgconn.execute('DROP TABLE IF EXISTS %s CASCADE' % table):
                logging.error('Drop table %s failed!\n' % table)
                return False

        return True

    def _postprocess_korea_safety_camera(self, pgconn):
        # if xml_safety_camera_loc not exists, means it's same as global, do
        # nothing.
        poi, loc = Importer.SAFETY_CAMERA_TABLE, Importer.SAFETY_CAMERA_LOC_TABLE
        if not pgconn.exist(loc):
            return True

        poi_backup = Importer.SAFETY_CAMERA_BK_TABLE
        poi_backup_name = poi_backup.split('.')[-1]
        loc_type = 'Entry Point'

        sqls = [
            "ALTER TABLE %s RENAME TO %s" % (poi, poi_backup_name),
            "CREATE TABLE %s AS SELECT * FROM %s JOIN %s USING(poi_key) WHERE type='%s' " % (
            poi, poi_backup, loc, loc_type),
            "ALTER TABLE %s ADD PRIMARY KEY(poi_key)" % poi,
        ]

        sql = ';'.join(sqls)

        return pgconn.execute(sql);

    def _import_sensitive_island(self):
        if not self.src_options.load_sensitive_island:
            return True

        logging.info('Importing sensitive island .......')

        sensitive_island = self._get_sensitive_island_data()
        if not sensitive_island:
            logging.error('No sensitive_island data found in %s' % self.data_dir)
            return False

        db_args = self._format_psql_args()

        shp2pgsql = self._get_shp2pgsql()
        if not shp2pgsql:
            logging.error('No shp2pgsql tool found\n')
            return False

        # shp2pgsql = 'shp2pgsql'

        lib_paths = [os.getenv('LD_LIBRARY_PATH', None), os.path.dirname(shp2pgsql)]
        lib_paths = filter(None, lib_paths)
        os.putenv('LD_LIBRARY_PATH', ':'.join(lib_paths))
        # os.system('chmod +x %s' % shp2pgsql)

        cmd = 'psql %s -v ON_ERROR_STOP=1 -c "CREATE SCHEMA IF NOT EXISTS usr; DROP TABLE IF EXISTS usr.sensitive_island"' % db_args
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('drop usr.sensitive_island failed!\n')
            return False

        cmd = '%s -I -W gbk %s usr.sensitive_island > sensitive.sql' % (shp2pgsql, sensitive_island)
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('shp2pgsql generate sql failed!, exit code = %s\n' % r)
            return False

        cmd = 'psql %s -v ON_ERROR_STOP=1 -f sensitive.sql' % db_args
        logging.info(cmd)
        r = os.system(cmd)
        if r:
            logging.error('import shp file %s failed! exit code = %s\n' % (sensitive_island, r))
            return False

        logging.info('Importing sensitive island done!')

        return True

    def _import_cn_add_content(self):
        if not self.src_options.load_cn_add_content:
            return True

        logging.info('Importing cn additional content(elevated road, overpass/underpass .......')

        cn_add_content = self._get_cn_add_content()
        if not cn_add_content:
            logging.error('No cn add content found in %s' % self.data_dir)
            return False

        # unzip
        gzip_files = glob.glob(os.path.join(cn_add_content, '*.gz'))
        if gzip_files:
            os.system('gunzip %s' % os.path.join(cn_add_content, '*.gz'))

        inner_dir = tempfile.mkdtemp(dir='.')
        if not os.path.exists(inner_dir):
            os.makedirs(inner_dir)

        xml_files = glob.glob(os.path.join(cn_add_content, '*.xml'))
        for xml_file in xml_files:
            extractor = AddContentExtractor(xml_file, inner_dir)
            extractor.process()

        db_args = self._format_psycopg2_args()
        importer = AddContentImporter(db_args)
        if not importer.update(inner_dir):
            return False

        os.system('rm -rf %s' % inner_dir)

        logging.info('Importing cn add content done!')

        return True

    def _db_process(self):
        processor = db_process.DbProcessor(self.option)
        return processor.process()

    def _get_xml_importer(self):
        dir_path = os.path.dirname(os.path.relpath(__file__))
        return os.path.join(dir_path, Importer.XML_IMPORTER)

    def _get_rdf_installer(self):
        map_tools = []
        for root, dirs, files in os.walk(self.importer):
            names = [f for f in dirs if f.startswith(Importer.RDF_INSTALLER_FLAG)]

            map_tools.extend([os.path.join(root, n) for n in names])

        if not map_tools:
            return None

        map_tools.sort()

        return map_tools[-1]

    def _get_shp2pgsql(self):
        tool = find_executable('shp2pgsql')
        if tool:
            return tool

        tools = self._get_in_dir('shp2pgsql', self.importer)
        if not tools:
            return None

        shp2pgsql = tools[0]
        os.system('chmod +x %s' % shp2pgsql)
        return shp2pgsql

    def _get_rdf_data(self):
        rdf_path = os.path.join(self.data_dir, Importer.DT_RDF)

        if os.path.exists(rdf_path):
            return rdf_path

    def _get_hamlet_data(self):
        hamlet = os.path.join(self.data_dir, Importer.DT_HAMLET)

        if not os.path.exists(hamlet):
            return None

        return hamlet

    def _get_toll_cost_data(self):
        toll_cost = os.path.join(self.data_dir, Importer.DT_KOR_TOLL_COST)

        if not os.path.exists(toll_cost):
            return None

        return toll_cost

    def _get_gjv_data(self):
        gjv = os.path.join(self.data_dir, Importer.DT_GJV)

        # gjv_files = glob.glob(os.path.join(gjv, "*.csv"))
        #
        # if not gjv_files:
        #     return None
        # return gjv_files[0]
        if not os.path.exists(gjv):
            return None

        return gjv

    def _get_kor_new_addr_data(self):
        new_addr = os.path.join(self.data_dir, Importer.DT_KOR_NEW_ADDRESS)
        if not os.path.exists(new_addr):
            return None

        return new_addr

    def _get_postal_code_data(self):
        postal_code = os.path.join(self.data_dir, Importer.DT_POSTAL_CODE)

        if os.path.exists(postal_code):
            return postal_code

    def _get_3d_landmark_data(self):
        landmark = os.path.join(self.data_dir, Importer.DT_3D_LANDMARK)

        if os.path.exists(landmark):
            return landmark

    def _get_safety_camera_data(self):
        safety_camera = os.path.join(self.data_dir, Importer.DT_SAFETY_CAMERA)

        if os.path.exists(safety_camera):
            return safety_camera

    def _get_sensitive_island_data(self):
        is_level0 = self.option.database.upper().find('LEVEL0') != -1

        if is_level0:
            sensitive_dir = os.path.join(self.data_dir, Importer.DT_LEVEL0_SENSITIVE_ISLAND)
        else:
            sensitive_dir = os.path.join(self.data_dir, Importer.DT_LEVEL2_SENSITIVE_ISLAND)

        shp_files = self._get_sensitive_island_data_imp(sensitive_dir)
        if shp_files:
            return shp_files[0]

        zip_files = glob.glob(os.path.join(sensitive_dir, '*.zip'))
        if not zip_files:
            return None

        zip_files.sort()
        zip_file = zip_files[0]
        os.system('unzip %s -d %s' % (zip_file, sensitive_dir))

        shp_files = self._get_sensitive_island_data_imp(sensitive_dir)
        if shp_files:
            return shp_files[0]

        return None

    def _get_sensitive_island_data_imp(self, sensitive_dir):
        # get shp files
        shp_files = []
        for root, dirs, files in os.walk(sensitive_dir):
            shps = [f for f in files if f.endswith('.shp')]
            shp_files.extend([os.path.join(root, f) for f in shps])

        return shp_files

    def _get_cn_add_content(self):
        cn_add_content = os.path.join(self.data_dir, Importer.DT_CN_ADD_CONTENT)

        if os.path.exists(cn_add_content):
            return cn_add_content

    def _format_psycopg2_args(self):
        args = ['host=%s' % self.option.host,
                'dbname=%s' % self.option.database,
                'user=%s' % self.option.user,
                'port=%s' % self.option.port,
                ]

        return ' '.join(args)

    def _format_psql_args(self):
        args = ['-h %s' % self.option.host,
                '-p %s' % self.option.port,
                '-U %s' % self.option.user,
                '%s' % self.option.database,
                ]

        return ' '.join(args)

    def _check_source_list(self):
        return LoadOption(self.option.source_list.lower())

    def _create_pg_extension(self, pgconn):
        sql = 'CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore'
        logging.info(sql)
        return pgconn.execute(sql)

    def _create_db(self):
        dbname = self.option.database

        # connect to default database "postgres"
        self.option.database = 'postgres'
        pgconn = pgconnect.PgConnect(self.option)
        r = pgconn.init_db()
        if not r:
            logging.error("Can't connecting to default db postgres")
            return False

        # create db if not exist
        if not pgconn.db_exist(dbname):
            tablespace = self._get_tablespace(self.option)
            if not pgconn.create_db(dbname, tablespace):
                logging.error('Create db %s failed\n' % dbname)
                return False

        # connect to specified database
        self.option.database = dbname
        if not pgconn.init_db():
            logging.error("Can't connecting to db %s" % dbname)
            return False

        # create extensions
        return self._create_pg_extension(pgconn)

    def _get_tablespace(self, option):
        host2tablespace = {'hqd-ssdpostgis-04.mypna.com': 'ssd1',
                           'hqd-ssdpostgis-03.mypna.com': 'ssd1',
                           '10.224.76.206': 'ssd1',
                           '10.224.77.141': 'ssd1',
                           }

        tablespace = option.tablespace
        if tablespace:
            return tablespace

        host = option.host
        if host in host2tablespace:
            return host2tablespace[host]
        return None

    def _get_in_dir(self, tool_name, tool_dir):
        tools = []
        for root, dirs, files in os.walk(tool_dir):
            tools.extend(glob.glob(os.path.join(root, tool_name)))
        return tools

    @staticmethod
    def _parse_database(database):
        """ database pattern as: <vendor>_<region><version>
            example as: HERE_EU17Q1, NT_NA16Q1, etc
        """
        m = re.match(r'[A-Z]+_([A-Z]+)_?(\d{2}Q\d)', database)
        if not m:
            return None, None

        # return (region, version)
        return m.group(1), m.group(2)
    

        

def init_logging(options):
    data = os.path.basename(options.data)

    filepath = 'dataimport_%s_%s.log' % (data, time.strftime('%y%m%d_%H%M%S'))
    logging.basicConfig(filename=filepath, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def validate(options):
    if not options.data or not os.path.exists(options.data):
        print 'Error: Raw data directory not exists!'
        return False
    if not options.adaptor or not os.path.exists(options.adaptor):
        print 'Error: Adaptor directory not exists!'
        return False
    if not options.importer or not os.path.exists(options.importer):
        print 'Error: Importer directory not exists!'
        return False

    return True
#  edit 2017-08-08
def edit_options_auto(options):
    '''
    edit options by auto rules:
    if database name is None, edit it by parse vendordata(rdf_data)
    if database options and source_list are None, edit it by read json config file

    :param options:
    :return:
    '''
    rdf_data = parse_rdf_data_from_path(options.data)
    region, version, vendor, isLevel0 = parse_region_version_vendor_isLevel0_By_rdfdata(rdf_data)
    if not options.database or options.database == None:
        database_name = auto_combine_dbname_by_region_vendor_version_islevel0(region,version,vendor,isLevel0)
        if database_name == None:
            sys.exit(-1)
    if isEmpty_value(options.db_opts) or isEmpty_value(options.source_list):
        db_options,source_list = auto_load_db_opts_source_list_by_region(region)
        if isEmpty_value(db_options) or isEmpty_value(source_list):
            sys.exit(-1)
        if isEmpty_value(options.db_opts):
            options.db_opts = db_options
        if isEmpty_value(options.source_list):
            options.source_list = source_list
def parse_rdf_data_from_path(data_path):
    '''
    because the data of options is a path, so here need to parse. get the ref_data
    '''
    arr = data_path.split("/")
    return arr[len(arr)-1]

# edit 2017-08-08

def main():
    parser = optparse.OptionParser()

    parser.add_option('-H', '--host', help='hostname', dest='host', default='localhost')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-t', '--tablespace', help='tablespace', dest='tablespace')
    parser.add_option('-A', '--adaptor', help='adaptorG2 path', dest='adaptor')
    parser.add_option('-I', '--importer', help='data import tools', dest='importer')
    parser.add_option('-d', '--data', help='data dir', dest='data')
    parser.add_option('-L', '--source-list', help='components source list', dest='source_list')
    parser.add_option('-o', '--db-operations', help='database operations, [divide|modify|remove_premium]',
                      dest='db_opts')
    # parser.add_option('-m', '--mode', help='rdf load mode, [normal|merge]', dest='mode', default='normal')

    options, args = parser.parse_args()

    # if not validate(options):
    #     parser.print_help()
    #     sys.exit(-1)

    init_logging(options)
    #
    edit_options_auto(options)
    #
    importer = Importer(options.data, options.importer, options.adaptor, options)

    if not importer.import_all():
        logging.error('Import all rdf & side file failed')
        sys.exit(-1)

    logging.info('Import all rdf & side file successfully')


if __name__ == '__main__':
    main()
