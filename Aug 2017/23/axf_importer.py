import ConfigParser
import glob
import itertools
import multiprocessing
import optparse
import os
import re
import shutil
import stat
import sys
import tempfile
import time

import psycopg2
import psycopg2.extras
from psycopg2 import Error

import addIndex
from axf import config, validate_axf
from axf.csv_importer import csv_import
from axf.csv_merger import gen_mesh_id
from axf.csv_merger import get_adjust_fields, csv_merge
from axf.shp2csv import axf_info, axf_error, shp2csv
from axf.shp2csv import execute
from axf.shp2csv import get_big_meshes, get_small_meshes
from axf.shp2csv import is_small_mesh
from axf.voice_importer import voice2db
from dbpreprocessing.addcolforhouseno import HouseNoHandler
from dbpreprocessing.addtnpoiid import PoiIdHandler
import axf.tollcost.importer as tollcost_import
from axf.config_reader import get_options
from axf.trafficpattern import traffic_extract

TOLLCOST_SECTION = 'tollcost'

class AxfImporter(object):
    TYPES_IN_ALL = ['wide_background', 'mid_background', 'population', 'highway', 'hs', 'ex_info']

    def __init__(self, axf_path, options):
        self.axf_path = axf_path
        self.options = options

        self.conn = None
        self.cursor = None

        self._init_pgsql()
        self._init_cfg_ex()

        self.dbf_tables = {}
        self.shp_tables = {}

    def __del__(self):
        # TODO
        pass

    def _init_pgsql(self):
        options = self.options
        db_args = "host=%s port=%s user=%s dbname=%s" % (options.host, options.port, options.user, options.dbname)
        try:
            self.conn = psycopg2.connect(db_args)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except Error, e:
            axf_error(e.__str__())
            sys.exit(-2)
        except Exception, e:
            axf_error(e.__str__())
            sys.exit(-3)

        self._init_database()

    def _init_database(self):
        sqls = [
            'CREATE EXTENSION IF NOT EXISTS postgis',
            'CREATE EXTENSION IF NOT EXISTS hstore',
        ]

        self._execute_sql(sqls)

    # added by yyli@telenav.cn on 2016-06-19
    def _init_cfg_ex(self):
        # get data version from db name
        m = re.match(r'.*(\d{2}q[1-4])', self.options.dbname.lower())
        if m:
            self.version = m.group(1)
            cp = ConfigParser.RawConfigParser()
            cp.add_section('all')
            cp.set('all', 'version', self.version)

            with open('axf/axf_external.cfg', 'wb') as f:
                cp.write(f)
        else:
            print "Wrong database format: missing version info"
            sys.exit(-1)

    def _check(self):
        psql = config.get_psql()
        if not psql:
            return False

        shp2psql = config.get_shp2pgsql()
        if not shp2psql:
            return False

        ogr2ogr = config.get_ogr2ogr()
        if not ogr2ogr:
            return False

        return True

    def import_axf(self):
        axf_info('Check tool existence!')
        if not self._check():
            return False
        #
        # tollcost
        if not self._import_tollcost():
            return False

        if not self.import_axf_all(self.axf_path):
            return False

        if not self.import_axf_mesh(self.axf_path):
            return False

        if not self.import_others():
            return False

        if not self._preprocess_db():
            return False

        # traffic
        if not self._traffic_extract():
            return False

        self.conn.close()
        return True

    def _preprocess_db(self):
        if not self._add_col_for_houseno():
            return False
        if not self._handle_poiid():
            return False

        return True

    # added by yyli@telenav.cn on 2015-11-12
    def _add_col_for_houseno(self):
        handler = HouseNoHandler(self.options)
        handler.execute()
        return True

    def _handle_poiid(self):
        v = self.version
        year = int(v[0:2])
        if year >= 16:
            handler = PoiIdHandler(self.options)
            handler.execute()

        return True

    #
    def _import_tollcost(self):
        tollcost_path = self._get_tollcost_path(self.axf_path)
        axf_info('Check path of tollcost  existence!')
        if not validate_axf.validate_tollcost(tollcost_path):
            axf_error('Error: filed in validate tollcost path.please check,Sorry')
            return False
        schema = self.options.version
        tollcost_outpath = self.options.tollcost_outpath
        optoins = get_options(TOLLCOST_SECTION)
        setattr(optoins, 'root', tollcost_path)
        setattr(optoins, 'version', schema)
        setattr(optoins, 'output', tollcost_outpath)

        tollcost_import.do_import(optoins)
        return True
    #
    def _traffic_extract(self):
        sqls = traffic_extract.extral_format_sqls(self.options.version)
        return self._execute_sql(sqls)

    def import_axf_all(self, axf_path):
        """
            import axf data in ALL directory
        """
        s = time.time()
        axf_info('IMPORT ALL')

        all_path = self._get_axf_all_path(axf_path)
        if not all_path:
            axf_info('ALL directory not found in %s' % axf_path)
            return True

        paths = [os.path.join(all_path, p) for p in os.listdir(all_path) if p.lower() in AxfImporter.TYPES_IN_ALL]
        paths = [p for p in paths if os.path.isdir(p)]

        for path in paths:
            self._import_axf_all_imp(path)

        axf_info('IMPORT ALL: %s seconds' % (time.time() - s))

        return True

    def _import_axf_all_imp(self, path):
        schema = os.path.basename(path)
        dbf_tables, shp_tables = self._get_axf_tables(path)

        self._create_schema_imp(schema, dbf_tables, shp_tables, under_mesh=False)

    def _get_axf_all_path(self, axf_path):
        for root, dirs, files in os.walk(axf_path):
            for d in dirs:
                if d == 'ALL':
                    return os.path.join(root, d)
        return None

    def import_axf_mesh(self, axf_path):
        axf_info('Importing AXF meshes')

        self.dbf_tables, self.shp_tables = self._get_axf_tables(axf_path, under_mesh=True)
        big_meshes = self._get_big_mesh_names(axf_path)

        for big_mesh in big_meshes:
            self._create_schema_imp(big_mesh, self.dbf_tables, self.shp_tables, under_mesh=True)

        axf_info('Make temp dir for CSV')
        # make csv temp dir
        import tempfile
        csv_tmp_dir = tempfile.mkdtemp(dir=os.getcwd())
        os.chmod(csv_tmp_dir, stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO)

        # shp2csv
        if not shp2csv(axf_path, csv_tmp_dir):
            axf_error('SHP2CSV failed\n')
            return False

        # merge csv
        csv_merge(csv_tmp_dir)

        # load csv
        if not csv_import(csv_tmp_dir, self._format_psql_db_args()):
            axf_error('CSV_IMPORT failed')
            return False

        # remove temp dir
        if self.options.remove_temp.upper() in ('TRUE', 'YES', 'Y', '1'):
            shutil.rmtree(csv_tmp_dir)

        # add index
        self._add_db_index(big_meshes)

        # process border nodes
        self._collect_border_nodes()

        # merge mesh to public via inherit
        self.merge_meshes_to_pubic(big_meshes)

        # mesh id mapping
        self._import_mesh_id_mapping(axf_path)

        return True

    def _create_schema_imp(self, schema, dbf_tables, shp_tables, under_mesh=True):
        # drop if template exists and create new schema
        sqls = ['DROP SCHEMA IF EXISTS %s CASCADE' % schema,
                'CREATE SCHEMA %s' % schema]
        self._execute_sql(sqls)

        # create axf tables
        db_args = self._format_psql_db_args()

        for table, dbf_file in dbf_tables.iteritems():
            multi_d = table.startswith('3d')
            geometry = table in shp_tables
            prepare_mode = under_mesh

            shp2pg_cmd = self._get_shp2pgsql_cmd(geometry, multi_d, prepare_mode)

            prefix = os.path.splitext(dbf_file)[0]
            prefix = '%s.shp' % prefix if geometry else '%s.dbf' % prefix

            cmd = '%s %s %s.%s|psql -q %s > /dev/null 2>&1' % (shp2pg_cmd, prefix, schema, table, db_args)
            if not execute(cmd):
                axf_error('Fail to create scheme %s' % schema)
                return False

            if under_mesh:
                sqls = ['ALTER TABLE %s."%s" DROP COLUMN gid' % (schema, table)]

                fields = get_adjust_fields(table)
                sqls.extend(
                    ['ALTER TABLE %s.%s ALTER COLUMN %s TYPE numeric(18,0)' % (schema, table, field) for field in
                     fields])
                self._execute_sql(sqls)

        return True

    def _add_db_index(self, big_meshes):
        s = time.time()
        axf_info('step ADD_DB_INDEX')

        psycopg_db_args = self._format_psycopg_db_args()
        # add_index = lambda schema: addIndex.addAXFIndex('AXF', psycopg_db_args, schema)
        db_args = [psycopg_db_args] * len(big_meshes)

        p = multiprocessing.Pool(multiprocessing.cpu_count())
        # p.map(add_index, big_meshes)
        p.map(_add_index, itertools.izip(db_args, big_meshes))

        axf_info('step ADD_DB_INDEX: %f seconds' % (time.time() - s))

    def _collect_border_nodes(self):
        import collectAxfBorderNode
        collectAxfBorderNode.collectNodes(self._format_psycopg_db_args())

    def _get_shp2pgsql_cmd(self, geometry=False, multi_d=False, prepare_mode=False):
        work_dir = os.path.dirname(os.path.abspath(__file__))
        os.putenv('LD_LIBRARY_PATH', work_dir)
        shp2pgsql = config.get_shp2pgsql()
        cmd = '%s -W gb18030 -D' % shp2pgsql
        cmd = '%s %s' % (cmd, '-g geom -I -S' if geometry else '-n')
        cmd = "%s %s" % (cmd, '-p' if prepare_mode else '')

        if geometry and multi_d:
            cmd = '%s -t "3DZ"' % cmd

        return cmd

    def _format_psql_db_args(self):
        return '-h %s -d %s -U %s' % (self.options.host, self.options.dbname, self.options.user)

    def _format_psycopg_db_args(self):
        return 'host=%s dbname=%s user=%s ' % (self.options.host, self.options.dbname, self.options.user)

    def _get_axf_tables(self, axf_path, under_mesh=False):
        dbf_tables = {}
        shp_tables = {}

        for root, dirs, files in os.walk(axf_path):
            if under_mesh and not is_small_mesh(root):
                continue

            dbfs = [f for f in files if f.endswith('.dbf')]
            shps = [f for f in files if f.endswith('.shp')]

            dbf_table_names = [os.path.splitext(f)[0].lower() for f in dbfs]
            shp_table_names = [os.path.splitext(f)[0].lower() for f in shps]

            dbf_files = [os.path.join(root, f) for f in dbfs]
            shp_files = [os.path.join(root, f) for f in shps]

            dbf_tables.update(itertools.izip(dbf_table_names, dbf_files))
            shp_tables.update(itertools.izip(shp_table_names, shp_files))

        return dbf_tables, shp_tables

    def _get_big_mesh_names(self, axf_path):
        big_meshes = get_big_meshes(axf_path)
        return [os.path.basename(mesh) for mesh in big_meshes]

    def merge_meshes_to_pubic(self, big_meshes):
        if not big_meshes:
            return

        self._schema_clone(big_meshes[0], 'public')

        for big_mesh in big_meshes:
            self._merge_mesh(big_mesh, 'public')

    def _merge_mesh(self, mesh_from, mesh_to):
        schema = mesh_from

        tables = self._get_tables_in_schema(schema)

        sqls = ['ALTER TABLE %s."%s" INHERIT %s."%s"' % (mesh_from, t, mesh_to, t) for t in tables]

        self._execute_sql(sqls)

    def _schema_clone(self, schema_from, schema_to):
        tables = self._get_tables_in_schema(schema_from)

        sqls = ['CREATE SCHEMA IF NOT EXISTS %s' % schema_to]
        sqls.extend(['DROP TABLE IF EXISTS %s."%s" CASCADE' % (schema_to, t) for t in tables])
        sqls.extend(
            ['CREATE TABLE %s."%s" AS SELECT * FROM %s."%s" LIMIT 0' % (schema_to, t, schema_from, t) for t in tables])

        self._execute_sql(sqls)

    def _get_tables_in_schema(self, schema):
        sql = "SELECT tablename FROM pg_tables WHERE schemaname='%s'" % (schema.lower())

        tables = []
        try:
            self.cursor.execute(sql)
            for rec in self.cursor:
                table = rec[0]
                tables.append(table)
            return tables
        except Error, e:
            self.conn.rollback()
            axf_error('%s, %s' % (e.__str__(), sql))
            sys.exit(-2)
        except Exception, e:
            self.conn.rollback()
            axf_error('%s, %s' % (e.__str__(), sql))
            sys.exit(-3)

    def _execute_sql(self, sqls):
        r = False
        try:
            for sql in sqls:
                self.cursor.execute(sql)
            self.conn.commit()
            r = True
        except Error, e:
            self.conn.rollback()
            axf_error('%s, %s' % (e.__str__(), sqls))
            sys.exit(-2)
        except Exception, e:
            self.conn.rollback()
            axf_error('%s, %s' % (e.__str__(), sqls))
            sys.exit(-3)

        return r

    def _import_mesh_id_mapping(self, shp_dir):
        axf_info('Import mesh id mapping')

        small_meshes = get_small_meshes(shp_dir)
        small_meshes = [os.path.basename(m) for m in small_meshes]

        mapping = [(mesh, gen_mesh_id(mesh)) for mesh in small_meshes]

        records = map(lambda m: '%s\t%d' % (m[0], m[1]), mapping)

        sqls = []
        sqls.append('CREATE SCHEMA IF NOT EXISTS mapping')
        sqls.append('DROP TABLE IF EXISTS mapping.mesh')
        sqls.append('CREATE TABLE mapping.mesh (mesh char(10) PRIMARY KEY, meshid INT)')

        self._execute_sql(sqls)

        fp = tempfile.NamedTemporaryFile(dir='.', delete=False)
        fp.write('\n'.join(records))
        fp.close()

        try:
            with open(fp.name) as ifs:
                self.cursor.copy_from(ifs, 'mapping.mesh')
                self.conn.commit()
        except Error, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-1)

        os.remove(fp.name)

        axf_info('Finish import mesh id mapping')

        return True

    def _import_mask_mapping(self):
        axf_info('Import mask mapping')

        self._execute_sql(['DROP TABLE IF EXISTS mapping.mask'])
        self._execute_sql(['DROP TABLE IF EXISTS mapping.chntext_mask'])
        self._execute_sql(['CREATE SCHEMA IF NOT EXISTS c99'])
        self._execute_sql(['DROP TABLE IF EXISTS c99.waterarea'])

        db_args = self._format_psql_db_args()
        psql = config.get_psql()

        sql_files = glob.glob(os.path.join('axf/sql', '*.sql'))
        for sql_file in sql_files:
            cmd = """%s -v ON_ERROR_STOP=1 -q %s -f %s """ % (psql, db_args, sql_file)
            if not execute(cmd):
                axf_error('import mask mapping failed, cmd=[%s]' % cmd)
                return False

        axf_info('Import mask mapping finished!')
        return True

    def _import_post_sql(self):
        axf_info('Import post sql scripts')

        db_args = self._format_psql_db_args()
        psql = config.get_psql()

        sql_files = glob.glob(os.path.join('axf/post_sql', '*.sql'))
        for sql_file in sql_files:
            cmd = """%s -v ON_ERROR_STOP=1 -q %s -f %s """ % (psql, db_args, sql_file)
            if not execute(cmd):
                axf_error('import mask mapping failed, cmd=[%s]' % cmd)
                return False

        axf_info('Import post sql scripts finished!')
        return True

    def import_others(self):
        if not self._import_mask_mapping():
            return False

        if not voice2db(self.axf_path, self._format_psql_db_args()):
            return False

        if not self._import_tmc():
            return False

        if not self._import_post_sql():
            return False

        return True

    def _import_tmc(self):
        start = time.time()

        tmc_path = self._get_tmc_path(self.axf_path)
        if not tmc_path:
            axf_info('No tmc path found in %s' % self.axf_path)
            return True

        schemes = os.listdir(tmc_path)
        schemes = [s for s in schemes if os.path.isdir(os.path.join(tmc_path, s))]

        paths = [os.path.join(tmc_path, s) for s in schemes]

        # import tmc
        for path in paths:
            self._import_axf_all_imp(path)

            schema = os.path.basename(path)
            sql = 'CREATE INDEX idx_{schema}rdstmc_link ON {schema}.rdstmc(link)'.format(schema=schema)
            if not self._execute_sql([sql]):
                return False

        # ref_data
        ref_path = self._get_ref_data(self.axf_path)
        if ref_path:
            self._import_axf_all_imp(ref_path)

        axf_info('Import tmc folder finished!')
        axf_info('Build tmc index!')

        # sqls
        sql = """DROP TABLE IF EXISTS tmc;
        CREATE TABLE tmc (
                loc_code    integer,
                dir         smallint,
                service_id  character varying(10),
                x_coord     double precision,
                y_coord     double precision,
                link        integer,
                mesh        char(10),
                road_id     bigint,
                road_dir    smallint,
                type        smallint,
                folder      char(10)
                )
        """
        if not self._execute_sql([sql]):
            print sql
            return False

        sql_template = """INSERT INTO tmc
            SELECT loc_code, dir, service_id, x_coord, y_coord, b.link, mesh, road_id::bigint, road_dir, "type", '{schema}'::text as folder
            FROM {schema}.rdstmc a, {schema}.rdslinkinfo b
            WHERE b.link between a.link and a.link + link_cnt - 1;
            """
        for s in schemes:
            print sql
            sql = sql_template.format(schema=s)
            if not self._execute_sql([sql]):
                return False

        axf_info('Merge tmc data to public')

        sqls = []
        sqls.append('update tmc set road_id=(road_id<<20)+meshid from mapping.mesh b where tmc.mesh= b.mesh')
        sqls.append('create index on tmc using btree(road_id)')

        if not self._execute_sql(sqls):
            axf_error('Update id and index')
            return False

        axf_info('Finish all tmc importing')
        axf_info('finish all tmc importing : %f seconds' % (time.time() - start))
        return True

    def _get_tmc_path(self, axf_path):
        for root, dirs, files in os.walk(axf_path):
            if os.path.basename(root) != 'CHN':
                continue
            if 'LOCTBL' in dirs:
                return os.path.join(root, 'LOCTBL')

        return None

    def _get_tollcost_path(self, axf_path):
        for root, dirs, files in os.walk(axf_path):
            for d in dirs:
                if d == 'CHARGEINFO':
                    return os.path.join(root, d)
        return None

    def _get_ref_data(self, axf_path):
        for root, dirs, files in os.walk(axf_path):
            if os.path.basename(root) == 'REF_DATA':
                return root

        return None


def default_options(options):
    # give the default value of version/schema
    if not options.version:
        options.version = options.dbname


def _add_index(args):
    db_args, schema = args

    addIndex.addAXFIndex('AXF', db_args, schema)


def main():
    parser = optparse.OptionParser(usage='%prog [options] axf_mesh_dir')

    parser.add_option('-H', '--host', help='host', dest='host')
    parser.add_option('-D', '--dbname', help='database name', dest='dbname')
    parser.add_option('-P', '--port', help='port', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user', dest='user', default='postgres')
    parser.add_option('-p', '--password', help='password', dest='password', default='postgres')
    parser.add_option('-r', '--remove-temp', help='remove temp directory', dest='remove_temp', default='true')
    ##
    parser.add_option('-O', '--tollcost-output-path', help='tollcost output path  ', dest='tollcost_outpath')
    parser.add_option('-V', '--version', help='data version;also schema', dest='version')
    ##
    options, args = parser.parse_args()

    if not validate_axf.validate_axf_parameters(options):
        parser.print_help()
        sys.exit(-1)

    if len(args) != 1:
        parser.print_help()
        sys.exit(-1)
    #
    default_options(options)
    #
    axf_mesh_dir = args[0]
    imp = AxfImporter(axf_mesh_dir, options)
    imp.import_axf()


if __name__ == '__main__':
    main()
'''
Test for tollcost
-H 172.16.101.92
-D axf_cn_17q1
-O C:\Users\shchshan\Desktop\tollcost_test\out
C:\Users\shchshan\Desktop\tollcost_test

'''