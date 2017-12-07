from rdf.tablespace_check.DBModule import DBModule
from util.common_utils import parse_rdf_unidb_db_name, filter_database_name

DB_DIFFERENT_RATE = 1.5
DB_INCREMENTAL_SIZE = 200 * 1024 * 1024 * 2014


def find_required_db_size(host, database_name, default_size=0):
    """Get the db`s required size. unit:B

    :param host:
    :param database_name:
    :param default_size: If can not find same database in host, return this default size
    :return:
    """
    dm = DBModule(host=host, dbname=database_name)
    # 1. get all database size dictionary structure
    all_database_name_size_dic = dm.select_all_db_size_dic()
    dm.close()
    # 2. select the same region and same type database name list
    same_db_list = find_same_db_list(all_database_name_size_dic.keys(), database_name)
    # 3.get the same database name size list
    same_db_size_list = [y for x, y in all_database_name_size_dic.iteritems() if x in same_db_list]
    # 4. sort, make the max size as required size. compare with default size ,too
    same_db_size_list.append(default_size)
    same_db_size_list.sort(reverse=True)
    return same_db_size_list[0]


def find_same_db_list(all_database_name_list, specified_database_name):
    """From specified database name , find the same region database names in history. """
    work_database_name_list = filter(filter_database_name, all_database_name_list)
    # 1. classify all database name {type_region:database_name,...}
    db_type_region_name_dic = {}
    for dbname in work_database_name_list:
        db_type, db_region, db_version = parse_rdf_unidb_db_name(dbname)
        if not db_type or not db_region:
            continue
        dic_key = "_".join([db_type, db_region])
        if dic_key not in db_type_region_name_dic:
            db_type_region_name_dic[dic_key] = []
        db_type_region_name_dic[dic_key].append(dbname)
    # 2. select need database list
    spe_db_type, spe_db_region, spe_db_version = parse_rdf_unidb_db_name(specified_database_name)
    specified_dic_key = "_".join([spe_db_type, spe_db_region])
    return db_type_region_name_dic[specified_dic_key]


def get_min_required_size(required_size):
    """
    min(1.5 * db_size, db_size + 200G)
    :param required_size:
    :return:
    """
    return min(required_size * DB_DIFFERENT_RATE, required_size + DB_INCREMENTAL_SIZE)


if __name__ == "__main__":
    hostname = "hqd-ssdpostgis-05.mypna.com"
