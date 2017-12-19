import os
import sys
from pgconnect import PgConnect, Opt
from util.import_shp import ShapeImporter


class LicensePlatePattern(object):
    """License Plate Pattern class"""

    def __init__(self, lpp_index, begin_date, end_date, local_restriction, tails, out_flag, time_range):
        self.lpp_index = lpp_index
        self.begin_date = begin_date
        self.end_date = end_date
        self.local_restriction = local_restriction
        self.tails = tails
        self.out_flag = out_flag
        self.time_range = time_range

    def to_dic(self):
        return self.__dict__


class MIFGDB(object):
    """MIFG database"""
    GROUP_TABLE_NAME = "plateres_group"
    RDLink_TABLE_NAME = "plateres_rdlink"
    MANOEUVRE_TABLE_NAME = "plateres_manoeuvre"
    PERIOD_TABLE_NAME = "plateres_period"
    HOLIDAY_TABLE_NAME = "plateres_holiday"

    def __init__(self, db_options):
        self.db_options = db_options
        self.db_pg_conn = PgConnect(db_options)
        if not self.db_pg_conn.init_db():
            sys.stderr.write("Connection database failed.\n")
            sys.exit(-1)

    def import_mifg_data(self, mifg_shp_data_dir):
        dbf_files = filter(lambda f: f.endswith('.dbf'),
                           [os.path.join(mifg_shp_data_dir, f) for f in os.listdir(mifg_shp_data_dir)])
        dbf_names = [os.path.splitext(os.path.basename(dbf))[0] for dbf in dbf_files]
        tables = [dbf_name.replace("shanghai", "") for dbf_name in dbf_names]

        shp_import = ShapeImporter(self.db_options)
        shp_import.import_shape(dbf_files=dbf_files, tables=tables)

    def create_extension_postgis(self):
        sql = "CREATE EXTENSION IF NOT EXIST postgis;"
        if not self.db_pg_conn.execute(sql):
            sys.stderr.write("create extension postgres failed\n")


def set_options(host, db_name, port, username, password):
    db_options = Opt()
    setattr(db_options, "host", host)
    setattr(db_options, "database", db_name)
    setattr(db_options, "port", port)
    setattr(db_options, "user", username)
    setattr(db_options, "passwd", password)
    setattr(db_options, "schema", "mifg")
    return db_options


def test_import():
    """Test Import"""
    db_options = set_options(host="localhost", db_name="mifg_17q3", port="5432", username="postgres", password="postgres")
    mifg_db = MIFGDB(db_options=db_options)

    mifg_dir = "C:\\Users\\shchshan\\Desktop\\Car Plate Restriction\\Limited Plates\\shanghai".replace("\\", "/")
    mifg_db.import_mifg_data(mifg_dir)


if __name__ == "__main__":
    test_import()
    pass
