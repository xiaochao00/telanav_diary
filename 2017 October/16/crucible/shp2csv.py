import os
import re
import sys
import time
import itertools
import multiprocessing

import config

DEBUG = False
INFO = True
ERROR = True


def execute(cmd):
    r = os.system(cmd)

    if r:
        sys.stderr.write('AxfError: cmd = [%s]\n' % cmd)

    return not r


def _axf_msg(msg, prefix):
    sys.stdout.write('%s: %s\n' % (prefix, msg))
    sys.stdout.flush()


def axf_info(msg, prefix=None):
    if not INFO:
        return

    if not prefix:
        prefix = 'AxfInfo'

    _axf_msg(msg, prefix)


def axf_debug(msg, prefix=None):
    if not DEBUG:
        return

    if not prefix:
        prefix = 'AxfDebug'

    axf_info(msg, prefix)


def axf_error(msg, prefix=None):
    if not prefix:
        prefix = 'AxfError'

    sys.stderr.write('%s: %s\n' % (prefix, msg))
    sys.stderr.flush()


def shp2csv(shp_dir, csv_dir):
    assert os.path.isdir(shp_dir)
    s = time.time()

    axf_info('step SHP2CSV')

    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    shp_dirs = get_small_meshes(shp_dir)
    csv_dirs = _get_csv_meshes(shp_dirs, shp_dir, csv_dir)

    # create out small mesh parent dir
    for d in set((os.path.dirname(c) for c in csv_dirs)):
        if os.path.exists(d):
            continue
        os.makedirs(d)

    # set shp encoding
    os.putenv('SHAPE_ENCODING', 'gb18030')
    p = multiprocessing.Pool(multiprocessing.cpu_count())
    r = p.map(_mesh2csv, itertools.izip(shp_dirs, csv_dirs))

    axf_info('finish SHP2CSV: %s seconds' % (time.time() - s))

    if False in r:
        axf_error('Faild SHP2CSV')
        return False

    return True


def get_big_meshes(path):
    meshes = []

    for root, dirs, files in os.walk(path):
        paths = (os.path.join(root, d) for d in dirs)
        meshes.extend(filter(is_big_mesh, paths))

    return meshes


def get_small_meshes(path):
    meshes = []

    for root, dirs, files in os.walk(path):
        paths = (os.path.join(root, d) for d in dirs)
        meshes.extend(filter(is_small_mesh, paths))

    return meshes

def _get_csv_meshes(shp_meshes, shp_dir, csv_dir):
    rel_paths = (os.path.relpath(p, shp_dir) for p in shp_meshes)
    csv_meshes = [os.path.join(csv_dir, p) for p in rel_paths]

    return csv_meshes


def _mesh2csv(args):
    mesh_dir, csv_dir = args

    assert len(os.path.basename(mesh_dir)) == 10
    axf_debug('generate csv, [form,to] = [%s,%s]' % (mesh_dir, csv_dir))

    ogr2ogr = config.get_ogr2ogr()
    os.putenv('LD_LIBRARY_PATH', os.path.dirname(ogr2ogr))
    
    # remove encoding option due to GDAL version update
    # cmd = '%s -f CSV %s %s -lco GEOMETRY=AS_WKT -lco SEPARATOR=TAB -lco ENCODING=UTF-8 ' % (ogr2ogr, csv_dir, mesh_dir)
    cmd = '%s -f CSV %s %s -lco GEOMETRY=AS_WKT -lco SEPARATOR=TAB ' % (ogr2ogr, csv_dir, mesh_dir)

    return execute(cmd)


def is_big_mesh(path):
    if not os.path.isdir(path):
        return False

    basename = os.path.basename(path)

    #return len(basename) == 4
    m = re.match(r'[A-Z]\d{2}F$', basename)
    return True if m else False

def is_small_mesh(path):
    if not os.path.isdir(path):
        return False

    # small meshes should not be under ALL directory
    if 'ALL' in [i.upper() for i in path.split(os.sep)]:
        return False

    basename = os.path.basename(path)

    #return len(basename) == 10
    m = re.match(r'[A-Z]\d{2}F\d{6}$', basename)
    return True if m else False

def main():
    if len(sys.argv) != 3:
        print 'Usage:\n\t%s shp_dir csv_dir\n\n' %(os.path.basename(sys.argv[0]))
        sys.exit(-1)

    shp_dir, csv_dir = sys.argv[1], sys.argv[2]

    shp2csv(shp_dir, csv_dir)

if __name__ == '__main__':
    main()
