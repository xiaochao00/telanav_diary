import re

LEVEL0_FLAG = "LEVEL0"


def parse_rdf_version(rdf_data):
    """
    rdf data format: XX_YY_ZZZZ (e.g. EU_HERE_17Q1 or XX_YY_ZZZZ_OO (eg. CN_NT_15Q1_Level0)'
            XX   : Region'
            YY   : Vendor Name'
            ZZZZ : Data version, for example 15Q1'
            OO   : Other Information, eg. Level0 data or not'
    :param rdf_data:
    :return: vendor, region, version, level0_or_not
    """
    m = re.match('([A-Z]+)_([A-Z0-9]+)_(\d+Q\d)(.*)', rdf_data, re.IGNORECASE)
    if m:
        is_level0 = m.group(4).upper().strip('_') == LEVEL0_FLAG
        return m.group(2).upper(), m.group(1).upper(), m.group(3).upper(), is_level0
    else:
        return None, None, None, None


def parse_rdf_db(rdf_db):
    """
    rdf data format: XX_YY_ZZZZ (e.g. HERE_EU17Q1 or XX_YY_ZZZZ_OO (eg. NT_CN_15Q1_Level0)'
            XX   : Region'
            YY   : Vendor Name'
            ZZZZ : Data version, for example 15Q1'
            OO   : Other information'
    :param rdf_db:
    :return: region, vendor, version, level0_or_not
    """
    m = re.match('([A-Z0-9]+)_([A-Z]+)_?(\d+Q\d)(.*)', rdf_db, re.IGNORECASE)
    if m:
        is_level0 = m.group(4).upper().strip('_') == LEVEL0_FLAG
        return m.group(1).upper(), m.group(2).upper(), m.group(3).upper(), is_level0
    else:
        return None, None, None, None


def data_match(rdf_data, rdf_db):
    rdf_version = parse_rdf_version(rdf_data)
    db_version = parse_rdf_db(rdf_db)

    # print rdf_version
    # print db_version

    if not rdf_version[0] or not db_version[0]:
        return False

    return rdf_version == db_version


if __name__ == '__main__':

    rdf_data_list = ['CN_NAV2_14Q1', 'CN_NT_17Q2_Level0', 'EU_HERE_17Q2']
    rdf_db_list = ['NAV2_CN_14Q1', 'NT_CN_17Q2_Level0', 'HERE_EU17Q2']

    for data, db in zip(rdf_data_list, rdf_db_list):
        print data_match(data, db)
