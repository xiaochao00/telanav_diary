# coding=utf8
import os
import sys
import json
import optparse
from collections import OrderedDict
from pgconnect import PgConnect, Opt
from util.import_shp import ShapeImporter

MIFG_JSON_FILE = "mifg_pattern.json"
SEPARATOR_CHAT = "|"
TAILS_BITS = 10
OUT_FLAG_BITS = 8
CITY_ID_BITS = 9
GROUP_ID_BITS = 7
RDF_LPP_TABLE_NAME = "rdf_mifg_lpp"
RDF_LPP_RDF_FIELD_NAME = "link_id"
RDF_LPP_LPP_FIELD_NAME = "lpp_id"


class RdfLppTable(object):
    def __init__(self, link_id, lpp_id):
        self.link_id = link_id
        self.lpp_id = lpp_id

    @staticmethod
    def save_rdf_lpp_list(rdf_lpp_list, csv_save_file_name="temp_rdf_lpp.csv"):
        with open(csv_save_file_name, "w") as f:
            for rdf_lpp in rdf_lpp_list:
                f.write("%s\t%s\n" % (rdf_lpp.link_id, rdf_lpp.lpp_id))
            f.close()
            sys.stdout.write("write data rows to file[%s] done.\n" % csv_save_file_name)
            return csv_save_file_name


class LPPS(object):
    def __init__(self, admin_index, lpp_list):
        self.admin_index = admin_index
        self.lpp_list = lpp_list

    def format_to_dict(self):
        #
        lpp_dic_array = []
        for license_plate_pattern in self.lpp_list:
            lpp_dic_array.append(license_plate_pattern.format_to_dict())
        #
        to_dict = OrderedDict({})
        to_dict["city_id"] = self.admin_index
        to_dict["lpp"] = lpp_dic_array
        return to_dict

    @staticmethod
    def parser_admin_lpp_list_dic(admin_lpp_list_dic):
        """
        :param admin_lpp_list_dic:
        :return: [LPPS,...]
        """
        lpps_list = []
        admin_index_dic = LicensePlatePattern.get_admin_code_index_dic(admin_lpp_list_dic)
        for admin_code, lpp_list in admin_lpp_list_dic.iteritems():
            admin_index = admin_index_dic[admin_code]

            lpps = LPPS(admin_index=admin_index, lpp_list=lpp_list)
            lpps_list.append(lpps)
        return lpps_list

    @staticmethod
    def get_mifg_link_lpp_admin_dic(mifg_link_group_id_list_dic, admin_lpp_list_dic):
        """Get the relationship between mifg link id, lpp_id, and admin_code"""
        admin_index_dic = LicensePlatePattern.get_admin_code_index_dic(admin_lpp_list_dic)
        group_id_lpp_dic = LicensePlatePattern.transform_to_group_lpp_dic(admin_lpp_list_dic)

        link_lpp_dic = {}
        link_admin_dic = {}
        for link_id, group_id_list in mifg_link_group_id_list_dic.iteritems():
            link_admin_code_list = list(set(map(lambda x: group_id_lpp_dic[x].admin_code, group_id_list)))
            admin_code = link_admin_code_list[0]
            link_admin_dic[link_id] = admin_code

            city_index = admin_index_dic[admin_code]
            group_index_list = map(lambda x: group_id_lpp_dic[x].lpp_index, group_id_list)
            lpp_id_binary = Utils.generate_lpp_id(city_index=city_index, group_index_list=group_index_list)
            lpp_id_int = int(lpp_id_binary, 2)
            # link_lpp_id_dic[link_id] = lpp_id_binary
            link_lpp_dic[link_id] = lpp_id_int

        return link_lpp_dic, link_admin_dic

    @staticmethod
    def list_to_dic(lpps_list):
        to_dict = OrderedDict({})
        lpps_json_list = []
        for lpps in lpps_list:
            lpps_json_list.append(lpps.format_to_dict())
        to_dict["lpps"] = lpps_json_list

        return to_dict


class LicensePlatePattern(object):
    """License Plate Pattern class"""

    def __init__(self, group_id, begin_date, end_date, local_restriction, tails, out_flag, time_range, admin_code,
                 lpp_index=0):
        self.group_id = group_id
        self.begin_date = begin_date
        self.end_date = end_date
        self.local_restriction = local_restriction
        self.tails = tails
        self.out_flag = out_flag
        self.time_range = time_range
        self.admin_code = admin_code
        self.lpp_index = lpp_index

    def _format_tails(self):
        tails_binary = Utils.list_to_binary(self.tails.split(SEPARATOR_CHAT), begin_index=0,
                                            end_index=TAILS_BITS)
        tails_binary += ("0" if u'字母'.encode("utf8") not in self.tails else "1")
        return int(tails_binary, 2)

    def _format_out_flag(self):
        out_flag_binary = Utils.list_to_binary(self.out_flag.split(SEPARATOR_CHAT), begin_index=0,
                                               end_index=OUT_FLAG_BITS)

        return int(out_flag_binary, 2)

    def format_to_dict(self):
        to_dict = OrderedDict({})
        to_dict["lpp_index"] = self.lpp_index
        to_dict["tail"] = self._format_tails()
        to_dict["out_flag"] = self._format_out_flag()
        to_dict["time"] = self.time_range
        return to_dict

    @staticmethod
    def transform_to_group_lpp_dic(admin_lpp_list_dic):
        group_lpp_dic = OrderedDict({})
        for admin_code, lpp_list in admin_lpp_list_dic.iteritems():
            for lpp in lpp_list:
                group_lpp_dic[lpp.group_id] = lpp
        return group_lpp_dic

    @staticmethod
    def get_admin_code_index_dic(admin_lpp_list_dic):
        admin_code_index_dic = dict(zip(admin_lpp_list_dic.keys(), range(0, len(admin_lpp_list_dic))))
        return admin_code_index_dic


class PlateManoeuvre(object):
    """PlateManoeuvre Table class"""

    def __init__(self, group_id, period_id, tail_char, out_flag):
        self.group_id = group_id
        self.period_id = period_id
        self.tail_char = tail_char
        self.out_flag = out_flag


class PlateGroup(object):
    """PlateGroup table class"""

    def __init__(self, admin_code, group_id, restrict, temp_plate, temp_p_num, charswitch, chartonum):
        self.admin_code = admin_code
        self.group_id = group_id
        self.restrict = restrict
        # below fields do nothing analysis;
        self.temp_plate = temp_plate
        self.temp_p_num = temp_p_num
        self.charswitch = charswitch
        self.chartonum = chartonum


class PlatePeriod(object):
    """PlatePeriod class"""

    def __init__(self, period_id, start_date, end_date, datetype, time, spec_flag):
        self.period_id = period_id
        self.start_date = start_date
        self.end_date = end_date
        self.datetype = datetype
        self.time = time
        self.spec_flag = spec_flag

    def compute_time_range(self):
        # base on spec_flag
        format_str = self.time
        if not self.time:
            return "[(h0)(h24)]"
        if not self.time.startswith("["):
            format_str = "[" + format_str
        if not self.time.endswith("]"):
            format_str += "]"
        return format_str


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
        self.create_extension_postgis()

        dbf_files = filter(lambda f: f.endswith('.dbf'),
                           [os.path.join(mifg_shp_data_dir, f) for f in os.listdir(mifg_shp_data_dir)])
        dbf_names = [os.path.splitext(os.path.basename(dbf))[0] for dbf in dbf_files]
        tables = [dbf_name.replace("shanghai", "") for dbf_name in dbf_names]

        shp_import = ShapeImporter(self.db_options)
        return shp_import.import_shape(dbf_files=dbf_files, tables=tables)

    def create_extension_postgis(self):
        sql = "CREATE EXTENSION IF NOT EXISTS postgis;"
        if not self.db_pg_conn.execute(sql):
            sys.stderr.write("create extension postgres failed\n")

    def find_manoeuvre(self, group_id):
        """Select manoeuvre table"""
        sql = ("SELECT group_id, period_id, tail_char, out_flag FROM {schema}.plateres_manoeuvre "
               "WHERE group_id='{group_id}'".format(schema=self.db_options.schema, group_id=group_id))
        rows = self.db_pg_conn.query_sql(sql)
        if not rows:
            return None
        [group_id, period_id, tail_char, out_flag] = rows.next()
        return PlateManoeuvre(group_id=group_id, period_id=period_id, tail_char=tail_char, out_flag=out_flag)

    def find_manoeuvre_list(self):
        """Select manoeuvre list"""
        sql = "SELECT group_id, period_id, tail_char, out_flag FROM %s.plateres_manoeuvre;" % self.db_options.schema
        rows = self.db_pg_conn.query_sql(sql)
        manoeuvre_list = []
        for row in rows:
            [group_id, period_id, tail_char, out_flag] = row
            manoeuvre_list.append(PlateManoeuvre(group_id=group_id, period_id=period_id,
                                                 tail_char=tail_char, out_flag=out_flag))
        return manoeuvre_list

    def find_plate_group_list(self):
        """SELECT all group"""
        sql = ("SELECT distinct group_id,admincode,restrict,temp_plate,temp_p_num,charswitch,chartonum "
               "FROM {schema}.plateres_group ORDER BY admincode;".format(schema=self.db_options.schema))
        rows = self.db_pg_conn.query_sql(sql)
        if not rows:
            return None
        group_list = []
        for row in rows:
            [group_id, admin_code, restrict, temp_plate, temp_p_num, charswitch, chartonum] = row
            group_list.append(PlateGroup(admin_code=admin_code, group_id=group_id, restrict=restrict,
                                         temp_plate=temp_plate, temp_p_num=temp_p_num, charswitch=charswitch,
                                         chartonum=chartonum))
        return group_list

    def find_period(self, period_id):
        sql = ("SELECT period_id,start_date,end_date,datetype,time,spec_flag "
               "FROM {schema}.plateres_period "
               "WHERE period_id = '{period_id}'".format(schema=self.db_options.schema, period_id=period_id))
        rows = self.db_pg_conn.query_sql(sql)
        if not rows:
            return None

        [period_id, start_date, end_date, datetype, time, spec_flag] = rows.next()
        return PlatePeriod(period_id=period_id, start_date=start_date, end_date=end_date, datetype=datetype,
                           time=time, spec_flag=spec_flag)

    def find_mifg_link_group_list_dic(self):
        """
        :return: {mifg link_id:[group_id,...],...}
        """
        sql = "SELECT group_id,link_id FROM {schema}.plateres_rdlink ORDER BY link_id;".format(schema=self.db_options.schema)
        rows = self.db_pg_conn.query_sql(sql)
        link_group_list_dic = {}
        for row in rows:
            [group_id, link_id] = row
            if link_id not in link_group_list_dic:
                link_group_list_dic[link_id] = []
            link_group_list_dic[link_id].append(group_id)
        return link_group_list_dic

    def find_admin_lpp_dic(self):
        """
        {LPPS(admin_code,{LicensePlatePattern(...),...}),...}
        :return:
        """
        plate_group_list = self.find_plate_group_list()
        if not plate_group_list:
            return None

        plate_group_list.sort(key=lambda d: d.admin_code)
        admin_lpp_dic = OrderedDict({})
        lpp_index = 0
        for plate_group in plate_group_list:
            admin_code = plate_group.admin_code
            group_id = plate_group.group_id
            local_restriction = plate_group.restrict
            #
            if admin_code not in admin_lpp_dic:
                admin_lpp_dic[admin_code] = []
                lpp_index = 0
            # manoeuvre
            manoeuvre = self.find_manoeuvre(group_id=group_id)
            period_id = manoeuvre.period_id
            out_flag = manoeuvre.out_flag
            tail_char = manoeuvre.tail_char
            # period
            plate_period = self.find_period(period_id=period_id)
            begin_date = plate_period.start_date
            end_date = plate_period.end_date
            time_range = plate_period.compute_time_range()
            # lpp
            lpp = LicensePlatePattern(group_id=group_id, begin_date=begin_date, end_date=end_date,
                                      local_restriction=local_restriction, tails=tail_char, out_flag=out_flag,
                                      time_range=time_range, admin_code=admin_code, lpp_index=lpp_index)
            # lpp list
            lpp_index += 1
            admin_lpp_dic[admin_code].append(lpp)

        return admin_lpp_dic

    def create_rdf_lpp_table(self, division_schema):
        table_full_name = "{schema}.{table_name}".format(schema=division_schema, table_name=RDF_LPP_TABLE_NAME)
        create_sql = ("DROP TABLE IF EXISTS {table_name};"
                      "CREATE TABLE {table_name} ({rdf_field_name} bigint,{lpp_field_name} bigint,"
                      "PRIMARY KEY({rdf_field_name}));".format(table_name=table_full_name,
                                                               rdf_field_name=RDF_LPP_RDF_FIELD_NAME,
                                                               lpp_field_name=RDF_LPP_LPP_FIELD_NAME))
        if not self.db_pg_conn.execute(create_sql):
            sys.stderr.write("create rdf mifg lpp table[%s] failed.\n" % table_full_name)
            sys.exit(-1)
        sys.stdout.write("create rdf mifg lpp table[%s] success.\n" % table_full_name)

    def save_rdf_lpp_data(self, csv_file_name, division_schema):
        # 1. create table
        table_full_name = "{schema}.{table_name}".format(schema=division_schema, table_name=RDF_LPP_TABLE_NAME)

        with open(csv_file_name, "r") as csv_input:
            self.db_pg_conn.copy_from(csv_input, table_full_name,
                                      column_name_list=[RDF_LPP_RDF_FIELD_NAME, RDF_LPP_LPP_FIELD_NAME])
            sys.stdout.write("copy csv of rdf lpp to DB[dbname=%s,table_name=%s] done.\n" % (self.db_options.database,
                                                                                             table_full_name))

    def find_order1_name(self, admin_place_id):
        sql = "select order1_id from public.rdf_admin_hierarchy where admin_place_id=%s" % admin_place_id
        rows = self.db_pg_conn.query_sql(sql)
        if rows:
            return rows.next()[0]
        sys.stderr.write("query order1 id by city code failed.")
        sys.exit(-1)


class Utils(object):
    @staticmethod
    def write_dic_to_json_file(data_dic, file_name):
        with open(file_name, "w") as f:
            json.dump(data_dic, f, ensure_ascii=False, indent=4, separators=(",", ":"))
            sys.stdout.write("write data to json file[%s] done\n" % file_name)
            return True

    @staticmethod
    def print_json(data_dic):
        data_json = json.dumps(data_dic, ensure_ascii=False, indent=4, separators=(",", ":"))
        print data_json

    @staticmethod
    def list_to_binary(str_list, begin_index=0, end_index=10, default_value=None):
        """Transform [0,1,2] to binary string
        the value of the index in list will be 1, otherwise 0
        """
        if not str_list:
            return default_value
        str_list = [str(x) for x in str_list]
        binary_str = ""
        for i in range(begin_index, end_index):
            i_binary = "1" if str(i) in str_list else "0"
            binary_str = i_binary + binary_str
        return binary_str

    @staticmethod
    def generate_lpp_id(city_index, group_index_list):
        # 9 bits for city; 7 bits lpp
        group_index_binary = Utils.list_to_binary(group_index_list, begin_index=0, end_index=GROUP_ID_BITS)
        city_index_binary = bin(city_index).replace("0b", "")
        #
        lpp_id_binary = city_index_binary + group_index_binary
        return lpp_id_binary


class MIFGProcessor(object):
    @staticmethod
    def import_mifg(mifg_db_options, lpp_db_option, lpp_json_file_path=MIFG_JSON_FILE, mifg_data_path=None):
        """
        1.Import mifg data
        2.Analysis, generate json config file
        3.Save lpp data to table for compiler PBF.(divide by admin, because rdf data is divide by admin)
        """
        is_mifg_import = True if mifg_data_path else False
        # generate to json
        admin_lpp_list_dic = MIFGProcessor.generate_mifg_lpp_json(mifg_db_options, lpp_json_file_path,
                                                                  mifg_data_path, is_mifg_import)
        # get all admin`s rdf lpp list, group by admin for division
        admin_rdf_lpp_list_dic = MIFGProcessor.get_admin_rdf_lpp_list_dic(mifg_db_options, admin_lpp_list_dic)
        # save rdf lpp data
        MIFGProcessor.save_lpp_by_admin_division(lpp_db_option, admin_rdf_lpp_list_dic)

    @staticmethod
    def generate_mifg_lpp_json(db_options, lpp_json_file_path=MIFG_JSON_FILE, mifg_data_path=None, is_mifg_import=False):
        """Generate JSON config file for mifg
        Return admin_code and index map, group id and pattern map
        """
        mifg_db = MIFGDB(db_options=db_options)
        # 0.import data if need
        if is_mifg_import:
            if not mifg_db.import_mifg_data(mifg_shp_data_dir=mifg_data_path):
                sys.stderr.write("import mifg data failed.\n")
                sys.exit(-1)
            sys.stdout.write("import success\n")

        # 1.get all admin code and group
        admin_lpp_list_dic = mifg_db.find_admin_lpp_dic()
        if not admin_lpp_list_dic:
            sys.stderr.write("mifg data should not empty.\n")
            sys.exit(-1)
        # 2.get relationship between admin_code and index, group id and lpp, lpps list
        lpps_list = LPPS.parser_admin_lpp_list_dic(admin_lpp_list_dic)
        # 3.write lpps to json file
        lpps_data_dic = LPPS.list_to_dic(lpps_list)
        Utils.print_json(lpps_data_dic)
        Utils.write_dic_to_json_file(lpps_data_dic, lpp_json_file_path)

        return admin_lpp_list_dic

    @staticmethod
    def get_admin_rdf_lpp_list_dic(db_options, admin_lpp_list_dic):
        """Mapping mifg link with rdf link"""
        mifg_db = MIFGDB(db_options)
        # 4.relationship between link id and group
        mifg_link_group_list_dic = mifg_db.find_mifg_link_group_list_dic()
        # 5.relationship between link id , lpp id, and admin_code
        mifg_link_rdf_dic, mifg_link_admin_dic = LPPS.get_mifg_link_lpp_admin_dic(mifg_link_group_list_dic,
                                                                                  admin_lpp_list_dic)
        # 6.relationship between rdf link id and mifg link id
        rdf_mifg_link_dic = MIFGProcessor.get_rdf_mifg_link_dic(mifg_link_rdf_dic.keys())
        # 7.relationship between rdf link id and lpp id, group by admin code
        admin_rdf_lpp_list_dic = MIFGProcessor.admin_rdf_lpp_list_dic_generator(rdf_mifg_dic=rdf_mifg_link_dic,
                                                                                mifg_lpp_dic=mifg_link_rdf_dic,
                                                                                mifg_admin_dic=mifg_link_admin_dic)
        return admin_rdf_lpp_list_dic

    @staticmethod
    def save_lpp_by_admin_division(db_options, admin_rdf_lpp_list_dic):
        rdf_db = MIFGDB(db_options)
        # 8.save this relationship to csv file
        rdf_division_schema_list = []  # for there are many admin have same order1 name, same table name
        for admin_code, rdf_lpp_list in admin_rdf_lpp_list_dic.iteritems():
            csv_save_file_name_pattern = os.path.join(os.path.dirname(__file__), "temp_rdf_lpp_{admin_code}.csv")
            csv_save_file_name = csv_save_file_name_pattern.format(admin_code=admin_code)
            if RdfLppTable.save_rdf_lpp_list(rdf_lpp_list, csv_save_file_name):
                # 9.save to table
                order1_place_id = rdf_db.find_order1_name(admin_code)
                rdf_division_schema = get_schema_name(order1_place_id)
                if rdf_division_schema not in rdf_division_schema_list:
                    rdf_db.create_rdf_lpp_table(rdf_division_schema)
                rdf_db.save_rdf_lpp_data(csv_save_file_name, rdf_division_schema)

    @staticmethod
    def admin_rdf_lpp_list_dic_generator(rdf_mifg_dic, mifg_lpp_dic, mifg_admin_dic):
        """Generate the relationship between rdf link id and lpp_id"""
        # relationship between rdf link and lpp id, group by admin code
        admin_rdf_lpp_list_dic = {}
        for rdf_link_id, mifg_link_id in rdf_mifg_dic.iteritems():
            admin_code = mifg_admin_dic[mifg_link_id]
            if admin_code not in admin_rdf_lpp_list_dic:
                admin_rdf_lpp_list_dic[admin_code] = []

            lpp_id = mifg_lpp_dic[mifg_link_id]
            admin_rdf_lpp_list_dic[admin_code].append(RdfLppTable(link_id=rdf_link_id, lpp_id=lpp_id))
        return admin_rdf_lpp_list_dic

    @staticmethod
    def get_rdf_mifg_link_dic(mifg_link_id_list):
        """The map relation between rdf link id and mifg link id"""
        rdf_mifg_link_dic = {}
        for mifg_link_id in mifg_link_id_list:
            rdf_mifg_link_dic[mifg_link_id] = mifg_link_id
        return rdf_mifg_link_dic

    @staticmethod
    def check_import():
        # TODO
        # 1.check all import tables: five
        # 2.check import data is not empty
        # 3.check the schema of destination database(rdf database) which was divided by admin_code is exist
        pass
        return True


def set_options(host, db_name, port, username, password, schema="mifg"):
    db_options = Opt()
    setattr(db_options, "host", host)
    setattr(db_options, "database", db_name)
    setattr(db_options, "port", port)
    setattr(db_options, "user", username)
    setattr(db_options, "passwd", password)
    setattr(db_options, "schema", schema)
    return db_options


def get_schema_name(admin_code):
    return "chn_order1_%s" % admin_code


def test_mifg():
    mifg_db_options = set_options("localhost", "mifg_17q3",
                                  "5432", "postgres", "postgres", "mifg")
    lpp_db_options = set_options("shd-dpc6x64ssd-02.china.telenav.com", "NT_CN_16Q1",
                                 "5432", "postgres", "postgres", "mifg")
    mifg_data_path = (r"C:\\Users\\shchshan\\Desktop\\Latest_Project\\Car_Plate_Restriction"
                      "\\Limited_Plates\\shanghai".replace("\\", "/"))

    MIFGProcessor.import_mifg(lpp_db_options, lpp_db_options, mifg_data_path=None)


def validate_parameters(options):
    if not options.host or not options.database:
        return False
    if not os.path.exists(os.path.dirname(options.pattern_file)):
        sys.stderr.write("json file parent path should not no exist\n")
        sys.exit(-1)
    return True


def main():
    parse = optparse.OptionParser()
    parse.add_option("-H", "--host", help="host", dest="host")
    parse.add_option("-D", "--database", help="", dest="database")
    parse.add_option("-P", "--port", help="", dest="port", default="5432")
    parse.add_option("-U", "--username", help="username", dest="username", default="postgres")
    parse.add_option("-p", "--password", help="password", dest="password", default="postgres")
    parse.add_option("-S", "--schema", help="schema", dest="schema", default="mifg")

    parse.add_option("-d", "--data-path", help="mifg source data path", dest="mifg_data_path", default="")

    parse.add_option("-F", "--pattern-file", help="pattern file path", dest="pattern_file",
                     default=os.path.join(os.path.dirname(os.path.abspath(__file__)), MIFG_JSON_FILE))

    options, args = parse.parse_args()
    # validate
    if not validate_parameters(options):
        parse.print_help()
        sys.exit(-1)
    # default value
    # TODO
    # import
    db_options = set_options(options.host, options.database, options.port, options.username, options.password,
                             options.schema)

    MIFGProcessor.import_mifg(mifg_db_options=db_options, lpp_db_option=db_options, lpp_json_file_path=options.pattern_file,
                              mifg_data_path=options.mifg_data_path)


if __name__ == '__main__':
    # test_mifg()
    main()
