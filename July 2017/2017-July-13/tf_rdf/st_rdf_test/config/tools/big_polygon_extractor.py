#-------------------------------------------------------------------------------
# Name:        big_polygon_extractor.py
# Purpose:
#
# Author:      lgwu
#
# Created:     10-27-2016
# Copyright:   (c) lgwu 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os, re, sys
import time
import itertools

import pgconnect


class DbOption(object):
    pass


class BigPolygonExtractor(object):
    BIG_POLYGON = 'public.big_polygon_relations'

    def __init__(self, options):
        self.options = options
        self.conn = pgconnect.PgConnect(self.options)

    def __initialize(self):
        if not self.conn.init_db():
            sys.stderr.write('Error: connect to postgres failed\n')
            return False

        return True

    def extract(self):
        if not self.__initialize():
            return []

        if not self.conn.exist(BigPolygonExtractor.BIG_POLYGON):
            sys.stderr.write('Error: %s not exists in %s\n' % (BigPolygonExtractor.BIG_POLYGON, self.options.dbname))
            return []

        sql = "SELECT id/1000 FROM %s " % BigPolygonExtractor.BIG_POLYGON

        poly_ids = [int(row[0]) for row in self.conn.execute_ex(sql)]
        poly_ids.sort()

        return poly_ids


class BigPolygonExtractorEx(object):

    def __init__(self, options, output_dir):
        self.config = options.config
        self.output_dir = output_dir

    def __parse_config(self):
        if not os.path.exists(self.config):
            sys.stderr.write('Error: config file %s not exists\n' % self.config)
            return False

        hosts = []
        for line in open(self.config):
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            hosts.append(line)

        return hosts

    def extract(self):
        hosts = self.__parse_config()

        db_options = itertools.chain.from_iterable([self.__retrieve_db_info(host) for host in hosts])

        db_info = self.__classify_db_info(db_options)

        self.__dump(db_info)

    def __dump(self, db_info):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for k, v in db_info.iteritems():
            region, version = k
            db_option = v[-1]

            extractor = BigPolygonExtractor(db_option)
            poly_ids = extractor.extract()

            poly_config = os.path.join(self.output_dir, region.lower(), version.lower())
            poly_dir = os.path.dirname(poly_config)
            if not os.path.exists(poly_dir):
                os.makedirs(poly_dir)

            with open(poly_config, 'w') as ofs:
                ofs.write('# %s\n' % db_option.dbname)
                ofs.write('[carto_id_polygon_clipper]\n')
                ofs.write('\n'.join(map(str, poly_ids)))
                ofs.write('\n')

    def __retrieve_db_info(self, host):
        options = DbOption()

        setattr(options, 'host', host)
        setattr(options, 'dbname', 'postgres')
        setattr(options, 'user', 'postgres')
        setattr(options, 'password', 'postgres')
        setattr(options, 'port', '5432')

        conn = pgconnect.PgConnect(options)
        if not conn.init_db():
            sys.stderr.write('Error: connect to postgres failed\n')
            return []

        db_options = []
        sql = "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname LIKE 'UniDB_%-RC' ORDER BY datname"
        for row in conn.execute_ex(sql):
            db_option = DbOption()
            setattr(db_option, 'host', host)
            setattr(db_option, 'dbname', row[0])
            setattr(db_option, 'user', 'postgres')
            setattr(db_option, 'password', 'postgres')
            setattr(db_option, 'port', '5432')
            setattr(db_option, 'dbsize', row[1])
            db_options.append(db_option)

        return db_options

    def __classify_db_info(self, db_options):
        db_info = {}

        for db_option in db_options:
            dbname = db_option.dbname
            region, version = self.__parse_db(dbname)
            if not region or not version:
                continue
            if 'level0' in dbname.lower():
                continue

            if self.__is_turley(region, db_option.dbsize):
                region = 'tur'

            db_info.setdefault((region, version), []).append(db_option)

        return db_info

    def __is_turley(self, region, size):
        if region.lower() != 'eu':
            return False

        size = size.strip()
        items = size.split(' ', 1)
        return int(items[0]) < 50 and items[1].endswith('GB')


    def __parse_db(self, dbname):
        m = re.match('UniDB_(?:HERE|NT)_([A-Z]{2,3})_?(\d+Q\d)_', dbname)
        if m:
            return m.group(1), m.group(2)

        return None, None


def main():
    import optparse
    parser = optparse.OptionParser(usage='Usage: %prog [options] output_dir')
    parser.add_option('-c', '--config', help='config', dest='config', default='config.txt')

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(-1)

    output_dir = args[0]

    extractor = BigPolygonExtractorEx(options, output_dir)

    extractor.extract()

if __name__ == '__main__':
    import time
    print 'Big Polygon extractor start at %s ' %(time.asctime())
    time.clock()
    main()
    print 'Big Polygon extractor stop at %s ' %(time.asctime())

    print 'Time used: %s' %(time.clock())
