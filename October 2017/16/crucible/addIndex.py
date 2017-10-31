# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      xlxu
#
# Created:     20-03-2013
# Copyright:   (c) xlxu 2013
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import sys
import os
import psycopg2
import psycopg2.extras
from psycopg2 import Warning, Error
import ConfigParser

AXF_EXTERNAL_PATH = os.path.join(os.path.dirname(__file__), 'axf/axf_external.cfg')

TTSHP_INDEX_MAP = {6: {"pi": ("ID",),
                       "pinm": ("ID",),
                       "piea": ("ID",),
                       "pr": ("POIID",),
                       "sm": ("ID",),
                       "smnm": ("ID",),
                       "smea": ("ID",),
                       "cf": ("ID",),
                       "is": ("ID",),
                       "wl": ("ID",),
                       "rr": ("ID", "F_JNCTID", "T_JNCTID",),
                       "oa08": ("ID",),
                       "wa": ("ID",),
                       "a8": ("ID",),
                       "bu": ("ID",),
                       "pd": ("ID",),
                       "pdnm": ("ID",),
                       "ap": ("ID",),
                       "lc": ("ID",),
                       "lu": ("ID",),
                       "nw": ("ID", "F_JNCTID", "T_JNCTID",),
                       "gc": ("ID",),
                       "ta": ("ID",),
                       "pc": ("ID",),
                       "rd": ("ID",),
                       "sg": ("ID",),
                       "jc": ("ID",),
                       "lp": ("ID",),
                       "ln": ("ID",),
                       "ps": ("ID",),
                       "se": ("ID",),
                       "locff": ("FEAT_ID",),
                       "locfp": ("FF_ID",),
                       },
                   3: {
                   },
                   }


def printUsage():
    print "Usage : python %s datatype dbstring" % (sys.argv[0])
    print 'Example : python %s ttshp "host=172.16.101.122 port=5432 user=postgres dbname=test"' % (sys.argv[0])
    print 'Example : python %s axf "host=172.16.101.122 port=5432 user=postgres dbname=test" h51f' % (sys.argv[0])


def addTTShpIndex(datatype, dbstring):
    try:
        conn = psycopg2.connect(dbstring)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Error, e:
        sys.stderr.write(e.__str__())
        sys.exit(-2)
    except:
        sys.exit(-3)

    # get all schema and table first
    dictSchema = dict()
    sql = 'select schemaname,tablename from pg_tables'
    cursor.execute(sql)
    for rec in cursor:
        schema = rec[0]
        table = rec[1]
        if schema not in dictSchema:
            dictSchema[schema] = set()
        dictSchema[schema].add(table)

    # get all indexs
    setIndex = set()
    sql = 'select schemaname,indexname from pg_indexes'
    cursor.execute(sql)
    for rec in cursor:
        schema = rec[0]
        index = rec[1]
        setIndex.add(index)

    # generate create index sql
    dictIndexSql = dict()
    im = get_im()
    for schema in dictSchema:
        if len(schema) in im[datatype.upper()]:
            dictTable = im[datatype.upper()][len(schema)]
            for table in dictTable:
                if table in dictSchema[schema]:
                    for field in dictTable[table]:
                        indexname = 'index_%s_%s_%s' % (schema.lower(), table.lower(), field.lower())
                        indexsql = 'CREATE INDEX %s on \"%s\".\"%s\" USING btree (\"%s\")' % (indexname, schema, table, field)
                        dictIndexSql[indexname] = indexsql

    # begin to build index in db
    for indexsql in dictIndexSql:
        if indexsql in setIndex:
            print '%s is already exist' % (indexsql)
        else:
            try:
                print 'Building index : %s' % (indexsql)
                cursor.execute(dictIndexSql[indexsql])
                conn.commit()
            except Error, e:
                conn.rollback()
                sys.stderr.write(e.__str__())
            except:
                conn.rollback()

    cursor.close()
    conn.close()


def addAXFIndex(datatype, dbstring, bigMesh):
    try:
        conn = psycopg2.connect(dbstring)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Error, e:
        sys.stderr.write(e.__str__())
        sys.exit(-2)
    except:
        sys.exit(-3)

    # get all schema and table first
    dictSchema = dict()
    sql = "select schemaname,tablename from pg_tables where schemaname='%s'" % (bigMesh.lower())
    cursor.execute(sql)
    for rec in cursor:
        schema = rec[0]
        table = rec[1]
        if schema not in dictSchema:
            dictSchema[schema] = set()
        dictSchema[schema].add(table)

    # begin to build index in db
    try:
        print 'Building index for %s' % bigMesh
        im = get_im()
        PkAndIndexMap = im['AXF'][10]
        for schema in dictSchema:
            for table in dictSchema[schema]:
                if table in PkAndIndexMap:
                    fields = PkAndIndexMap[table]
                    sqls = []
                    # for pk
                    sql = 'alter table %s."%s" add primary key (%s)' % (schema, table, fields[0])
                    sqls.append(sql)
                    # for fk
                    for field in fields[1:]:
                        sql = 'create index on %s."%s" USING btree (%s)' % (schema, table, field)
                        sqls.append(sql)
                    # execute
                    cursor.execute(";".join(sqls))
        conn.commit()
    except Error, e:
        conn.rollback()
        sys.stderr.write(e.__str__())
    except:
        conn.rollback()

    cursor.close()
    conn.close()


def get_aim():
    cp = ConfigParser.SafeConfigParser()
    cp.read(AXF_EXTERNAL_PATH)
    version = cp.get('all', 'version')
    year = int(version[0:2])

    cols_poi = ["poi", "poi_id", "name", "alias", "addr", "road", "sapa"]
    cols_poiinfo = ["poi", "poi_id"]
    cols_poiplus = ["poi", "poi_id", "abbr"]

    # after 16Q1 version, poi_id have been change to STRING instead of INT
    if year >= 16:
        cols_poi.remove("poi_id")
        cols_poiinfo.remove("poi_id")
        cols_poiplus.remove("poi_id")

    axf_index_map = {10: {"uncoveredmeshlist": ("uml", "uml_id",),  # background
                          "settmeshlist": ("sml", "sml_id",),
                          "contour": ("contour", "contour_id",),
                          "settlementline": ("lsett", "lsett_id",),
                          "landuseline": ("lul", "lul_id",),
                          "railway": ("rail", "rail_id",),
                          "landcoverarea": ("lca", "lca_id",),
                          "landusearea": ("lua", "lua_id",),
                          "builtuparea": ("bua", "bua_id",),
                          "engtext": ("engtext", "engtext_id", "chntext", "poi"),
                          "landmarkcrsplus": ("lm", "lm_id", "engtext"),
                          "chntext": ("chntext", "chntext_id", "engtext", "poi"),
                          "landmarkmapplus": ("lm", "lm_id", "engtext"),
                          "landmarkcrs": ("lm", "lm_id", "poi", "text"),
                          "landmarkmap": ("lm", "lm_id", "poi", "text"),
                          "settlementarea": ("sett", "sett_id", "lm"),
                          "settgroup": ("sgroup", "sgroup_id", "vir_sett", "sett"),
                          "hotspots": ("hs", "hs_id",),
                          "facilityarea": ("fa", "fa_id", "poi"),
                          "texttypecode": ("type",),  # metadata
                          "poitypecode": ("type",),
                          "brandtypecode": ("type",),
                          "landmarktypecode": ("type",),
                          "adcode": ("ad", "ad_id",),
                          "poiinsidehotspots": ("pih", "pih_id", "hs", "poi"),  # ?
                          "poichildren": ("pchild", "pchild_id", "parent_poi", "child_poi"),  # ?
                          "poibackground": ("poibg", "poibg_id", "poi", "bg"),  # ?
                          "adminline": ("adl", "adl_id",),  # administrative
                          "adminarea": ("ada", "ada_id",),
                          "postcode": ("pc", "pc_id",),  # postcode
                          "t_int": ("fint", "fint_id", "inti"),  # intersection
                          "intindex": ("inti", "inti_id", "elemid"),
                          "fwinode": ("fwin", "fwin_id", "fwir", "node"),  # freewayintersection
                          "fwiroad": ("fwir", "fwir_id", "road"),
                          "highway": ("hwy", "hwy_id",),  # highway
                          "highwaydouble": ("hwd", "hwd_id", "hwp", "node", "from_road"),
                          "sapaname": ("name", "name_id",),
                          "sapa": ("sapa", "sapa_id", "name", "node", "road", "node_entr"),
                          "interchange": ("ic", "ic_id", "node", "hwy",),
                          "interchangeroad": ("icr", "icr_id", "road", "hwy",),
                          "highwaydoublepath": ("hwp", "hwp_id", "road",),
                          "highwaysingle": ("hws", "hws_id", "node", "from_road", "to_road"),
                          "population": ("ad_code",),  # population
                          "zlevel": ("zlevel", "zlevel_id", "link_up", "link_down"),  # zlevel
                          "roadsegmentplus": ("road", "road_id",),  # road
                          "roadmark": ("rm", "rm_id",),
                          "roadrule": ("rule", "rule_id",),
                          "roadsegment": ("road", "road_id", "fnode", "tnode", "rule"),
                          "airlineaccess": ("ala", "ala_id", "poi"),  # poi
                          "iata": ("iata", "iata_id", "poi"),
                          "addressno": ("an", "an_id", "hn"),
                          "houseno": ("hn", "hn_id", "poi"),
                          "poi": cols_poi,
                          "poiname": ("name", "name_id",),
                          "poiinfo": cols_poiinfo,
                          "poihotline": ("ph", "ph_id", "poi", "hotline"),
                          "poiplus": cols_poiplus,
                          "poinameplus": ("name", "name_id",),
                          "energy": ("energy", "energy_id", "poi"),
                          "hotline": ("hotline", "hotline_id",),
                          "poiabbr": ("abbr", "abbr_id",),
                          "poiaddress": ("addr", "addr_id",),
                          "poialias": ("alias", "alias_id",),
                          "sideroadcross": ("sr", "sr_id",),  # road network/complex node
                          "roadcrosssignpost": ("sp", "sp_id",),
                          "roadcrossrule": ("rule", "rule_id",),
                          "roadcrossmaat": ("maat", "maat_id", "node", "from_road", "to_road", "rule", "sp"),
                          "roadcrosssaat": ("saat", "saat_id", "node", "road"),
                          "roadcross": ("node", "node_id", "begm_id", "endm_id", "begs_id", "ends_id"),
                          "extendlane": ("lane", "lane_id", "maat", "xlpath"),  # road network/node
                          "sideroadnode": ("sr", "sr_id", "maat"),
                          "roadnodesignpost": ("sp", "sp_id",),
                          "roadnoderule": ("rule", "rule_id",),
                          "xlpath": ("xlpath", "xlpath_id"),
                          "roadnodemaat": ("maat", "maat_id", "node", "from_road", "to_road", "sp", "rule"),
                          "roadnodetollgate": ("toll", "toll_id", "node", "from_road", "to_road"),
                          "roadnodesaat": ("saat", "saat_id", "node", "road"),
                          "roadnode": ("node", "node_id", "begm_id", "endm_id", "begs_id", "ends_id", "comp_node"),
                          "sprelation": ("sp", "sp_id", "rf", "road"),  # ?
                          "roadfurnituresignpost": ("rfsp", "rfsp_id", "road", "path"),  # road furniture
                          "rfsppathlink": ("link", "link_id"),
                          "roadfurniture": ("rf", "rf_id", "road", "rfp",),
                          "rfsppath": ("path", "path_id", "link",),
                          "roadfurnitureplus": ("rfp", "rfp_id",),
                          "roadcrosslaneconnectivity": ("lanecon", "lanecon_id", "maat"),
                          "roadnodelaneconnectivity": ("lanecon", "lanecon_id", "maat"),
                          "hsnp": ("road", "road_id"),
                          "detailslope": ("ds", "ds_id", "road"),
                          "curvature": ("cv", "cv_id", "road"),
                          "lane": ("lane", "lane_id", "road"),
                          "speedprofile": ("histspd", "histspd_id", "road",),
                          "chargepile": ("cp", "cp_id", "energy"),
                          "chargepileplus": ("cp", "cp_id"),
                          "chargepiledetail": ("cpd", "cpd_id", "cp"),
                          },
                     3: {
                     },
                     # some tables' mesh id column will be generated by column value instead of folder mesh value
                     11: {"houseno": {"road": "road_mesh"},
                          },
                     }

    return axf_index_map


def get_im():
    aim = get_aim()
    index_map = {"TTSHP": TTSHP_INDEX_MAP,
                 "AXF": aim}
    return index_map


if __name__ == '__main__':

    if len(sys.argv) not in (3, 4):
        printUsage()
        sys.exit(-1)

    datatype = sys.argv[1]
    dbstring = sys.argv[2]
    if len(sys.argv) == 4:
        bigMesh = sys.argv[3]

    im = get_im()

    if not datatype.upper() in im:
        print "%s is not in index map, so no index will be build" % (datatype)
        sys.exit(-4)

    if datatype.upper() == "TTSHP":
        addTTShpIndex(datatype, dbstring)
    elif datatype.upper() == "AXF":
        addAXFIndex(datatype, dbstring, bigMesh)
