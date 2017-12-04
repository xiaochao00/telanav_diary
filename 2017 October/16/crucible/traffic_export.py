import time
import os
from axf.utils import create_path, safe_execute, parse_axf_db
from axf.shp2csv import axf_info, axf_error

TRAFFIC_SAVE_PATH_PREFIX = r'/var/www/html/data'
TRAFFIC_SAVE_PATH_SUFFIX = r'components/speed_pattern'
OLDFORMAT_PATH = 'oldformat'
NEWFORMAT_PATH = 'newformat'


def export_traffic(schema, cursor, traffic_save_path=None):
    '''
    the generate directory structure is
    #/var/www/html/ec_latest_builds/SPEED_PATTERN/
    /var/www/html/data/
            ---schema/speed_pattern/
            time/oldformat/file1,file2
                           /newformat/file3
    '''
    try:
        save_path = None
        if not traffic_save_path:
            save_path = os.path.abspath(os.path.join(TRAFFIC_SAVE_PATH_PREFIX, schema.upper(), TRAFFIC_SAVE_PATH_SUFFIX, time.strftime("%Y_%m_%d_%H_%M", time.localtime())))
        else:
            save_path = os.path.join(traffic_save_path, time.strftime("%Y_%m_%d_%H_%M", time.localtime()))
        region, type, version = parse_axf_db(schema)

        oldformat_path = os.path.join(save_path, OLDFORMAT_PATH)
        create_path(oldformat_path)

        newformat_path = os.path.join(save_path, NEWFORMAT_PATH)
        create_path(newformat_path)

        old1_path = os.path.join(oldformat_path, 'hsnp.csv')
        old1_sql = "COPY (SELECT * FROM public.hsnp) TO STDOUT DELIMITER ';' CSV HEADER"
        export_to_file(sql=old1_sql, filepath=old1_path, cursor=cursor)

        old2_path = os.path.join(oldformat_path, 'hspr.csv')
        old2_sql = "COPY (SELECT profile_id, time_slot, rel_sp FROM hs.hspr) TO STDOUT DELIMITER ';' CSV HEADER"
        export_to_file(sql=old2_sql, filepath=old2_path, cursor=cursor)

        new1_path = os.path.join(newformat_path, 'speedprofile_%s.csv' % version)
        new1_sql = "COPY (SELECT sp.*, rs.road_id FROM public.speedprofile sp, public.roadsegment rs WHERE sp.road = rs.road) TO STDOUT DELIMITER ',' CSV HEADER "
        export_to_file(sql=new1_sql, filepath=new1_path, cursor=cursor)
        return True
    except Exception, e:
        axf_error("Error in traffic export. Please check, Sorry")
        axf_error(e)
        axf_error(e.message)
        return False


def export_to_file(sql, filepath, cursor):
    f = open(filepath, 'w')
    cursor.copy_expert(sql, f)
    axf_info('success export to file. %s ' % filepath)
    f.close()


if __name__ == '__main__':
    export_traffic('cn_axf_17q2', None)
