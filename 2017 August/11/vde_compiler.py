import os
import sys
import time
import compile_vde
import create_vde_db
import statistic

from options import Options
from options import parse_database_options


def execute_cmd(cmd):
    print cmd
    if os.system(cmd):
        sys.stderr.write('Error: execute <%s> failed\n' % cmd)
        sys.exit(-1)


class VDECompiler(object):
    def __init__(self, opts):
        self.opts = opts
        self.opts.poi_csv = os.path.abspath(self.opts.poi_csv)
        self.opts.vde_baseline = os.path.abspath(self.opts.vde_baseline)
        self.opts.out_dir = os.path.abspath(self.opts.out_dir)

        self.map_db_options = None
        self.poi_db_options = None
        self.vde_db_options = None

    def compile(self):
        if not self._import_poi():
            sys.stderr.write('Error: import POI csv failed\n')
            return False

        if not self._create_vde_db():
            sys.stderr.write('Error: create VDE db failed\n')
            return False

        if not self._compile_vde():
            sys.stderr.write('Error: compile VDE failed\n')
            return False

        if not self._generate_statistic():
            sys.stderr.write('Error: generate statistic failed\n')
            return False

        if not self._run_regression():
            sys.stderr.write('Error: run regression failed\n')
            return False

        return True

    def _import_poi(self):
        poi_csv = self.opts.poi_csv
        if not poi_csv or not os.path.exists(poi_csv):
            sys.stderr.write('Error: poi csv %s not exist!\n' % poi_csv)
            return False

        poi_db_options = Options()
        if not parse_database_options(self.opts.poi_db, poi_db_options):
            sys.stderr.write('Error: parse poi db options <%s> failed!\n' % self.opts.poi_db)
            return False

        args = ['-H %s' % poi_db_options.host,
                '-D %s' % poi_db_options.dbname,
                '-P %s' % poi_db_options.port,
                '-U %s' % poi_db_options.user,
                '-p %s' % poi_db_options.password,
                '-C %s' % self.opts.poi_csv
                ]
        compiler_path = os.path.dirname(os.path.abspath(__file__))
        content_importer = os.path.join(compiler_path, 'sql/snapshot', 'content_importer.py')

        cmd = 'python2.7 %s %s' % (content_importer, ' '.join(args))
        execute_cmd(cmd)

        poi_db_options.schema = os.path.basename(self.opts.poi_csv)
        self.poi_db_options = poi_db_options
        return True

    def _create_vde_db(self):
        if not self.poi_db_options:
            return False

        self.map_db_options = Options()
        if not parse_database_options(self.opts.map_db, self.map_db_options):
            sys.stderr.write('Error: parse map db options <%s> failed!\n' % self.opts.map_db)
            return False

        self.vde_db_options = Options()
        if not parse_database_options(self.opts.vde_db, self.vde_db_options):
            sys.stderr.write('Error: parse vde db options <%s> failed!\n' % self.opts.vde_db)
            return False
        project, region, version = self.__parse_poi_csv()
        if not project or not region or not version:
            sys.stderr.write('Error: parse vde schema from poi csv <%s> failed!\n' % self.opts.poi_csv)
            return False

        vde_schema = '%s_vde_%s_%s_%s' % (project, region, version, time.strftime('%y%m%d'))
        # vde_schema = '%s_vde_%s_%s_%s' % (project, region, version, '20170518')
        self.vde_db_options.schema = vde_schema
        setattr(self.opts, 'region', region)
        setattr(self.opts, 'version', version)

        return create_vde_db.create_vde_db(self.map_db_options, self.poi_db_options, self.vde_db_options, self.opts)

    def __parse_poi_csv(self):
        import re
        poi_csv_name = os.path.basename(self.opts.poi_csv)
        m = re.match(r'([a-z]+)_([a-z]+)_(\d+q\d)_.*', poi_csv_name, re.IGNORECASE)
        if m:
            # project, region, version
            return m.group(1), m.group(2), m.group(3)
        return '', '', ''

    def _compile_vde(self):
        return compile_vde.compile_vde(self.vde_db_options, self.opts)

    def _generate_statistic(self):
        stat = statistic.Statistic(self.opts.out_dir)
        stats = stat.parse()
        stat.statistic(stats)

        return True

    def _run_regression(self):
        cwd = os.getcwd()
        regression_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VDERegression')
        os.chdir(regression_dir)

        args = ['-d %s' % self.opts.out_dir,
                '-r %s' % self.opts.region]
        cmd = 'python2.7 %s %s ' % (os.path.join(regression_dir, 'caseextractor.py'), ' '.join(args))
        execute_cmd(cmd)

        args = ['-d %s' % self.opts.vde_baseline,
                '-r %s' % self.opts.region,
                '-b']
        cmd = 'python2.7 %s %s ' % (os.path.join(regression_dir, 'caseextractor.py'), ' '.join(args))
        execute_cmd(cmd)

        report_dir = os.path.join(os.path.dirname(self.opts.out_dir), 'report')
        cmd = 'python2.7 %s -ref %s -out %s -r %s' % (
        'reportgenerator/reportgenerator.py', 'baseline', 'output', report_dir)
        execute_cmd(cmd)

        os.chdir(cwd)

        return True


def validate(options, args):
    if not options.poi_csv:
        sys.stderr.write('Error: no poi csv path specified\n')
        return False

    return True


def main():
    import optparse

    parser = optparse.OptionParser()

    group = optparse.OptionGroup(parser, 'Map UniDB Options')
    group.add_option('-M', '--map-db', help='map unidb options', dest='map_db')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'POI UniDB Options')
    group.add_option('-P', '--poi-db', help='poi unidb options', dest='poi_db')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'VDE DB Options')
    group.add_option('-V', '--vde-db', help='vde db options', dest='vde_db')
    parser.add_option_group(group)

    parser.add_option('-t', '--tablespace', help='tablespace', dest='tablespace', default='pg_default')

    parser.add_option('-c', '--poi-csv', help='poi csv path', dest='poi_csv')

    parser.add_option('-b', '--vde-baseline', help='vde baseline', dest='vde_baseline')
    parser.add_option('-o', '--vde-output', help='vde out dir', dest='out_dir')

    options, args = parser.parse_args()

    if not validate(options, args):
        parser.print_help()
        sys.exit(-1)

    compiler = VDECompiler(options)
    if not compiler.compile():
        sys.stderr.write('Error: compile VDE failed\n')
        sys.exit(-1)

'''
Test
'''
class Options:
    def __init__(self):
        self.map_db = "dbname=unidb_cn_axf_17q1_1.0.0.113970_170608_105105_allregion-RC"
        self.poi_db = 'dbname=content_unidb'
        self.vde_db = 'dbname=denali_vde'
        self.tablespace = 'pg_default'
        self.poi_csv = '/home/mapuser/workspace_users/lgwu/vde/content_data/denali_cn_17q1_20170804_epl'
        self.vde_baseline = '/home/mapuser/workspace_users/lgwu/vde/vde_data/17q1_20170605/VDE_CN_17Q1_20170613'
        self.out_dir = '/home/mapuser/workspace_users/lgwu/vde/vde_data/17q1_20170809/VDE_CN_17Q1_20170809'


if __name__ == '__main__':
    main()
