# -------------------------------------------------------------------------------
# Name:        caseextractor
# Purpose:
#
# Author:      fwu
#
# Created:     26/04/2016
# Copyright:   (c) TeleNav 2016
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import sys
import CONST
import os
import suitesreader
import xml.sax
import re
from optparse import OptionParser
from casehandler import *
from log_processor import error_logging_recoder, warn_logging_recoder

global options
parser = OptionParser()
xmlparser = xml.sax.make_parser()
suitepath = os.path.join(sys.path[0], "testsuites")


def optionInit():
    parser.add_option("-d", "--dir", action='store', dest='idir', help='Input Dir')
    parser.add_option("-r", "--region", action='store', dest='iregion', help='Region')
    parser.add_option("-b", "--baseline", action='store_true', dest='ibaseline', default=False, help='is baseline or not')


def checkParameter():
    if not options.idir:
        error_logging_recoder("missing required parameter -d")
        parser.print_help()
        sys.exit(-1)

    if not options.iregion:
        error_logging_recoder("missing required parameter -r")
        parser.print_help()
        sys.exit(-1)


def readSuites(region):
    suitesReader = suitesreader.SuitesReader(suitepath, region)
    suitesReader.readSuites()
    return suitesReader


def extractCases(vdedir, b_baseline, suitesReader, region):
    cate_files = list()
    chain_file = os.path.join(vdedir, CONST.CHAIN_FILE_NAME)
    country_file = os.path.join(vdedir, CONST.COUNTRY_FILE_NAME)
    state_file = os.path.join(vdedir, CONST.STATE_FILE_NAME)
    city_file = os.path.join(vdedir, CONST.CITY_FILE_NAME)
    hierarchy_file = os.path.join(vdedir, CONST.HIERARCHY_FILE_NAME)

    for parent, subdirs, files in os.walk(vdedir):
        for file in files:
            if re.match("CATEGORY", file.upper()):
                cate_files.append(os.path.join(vdedir, file))

    # Read Hierarchy
    hierarchyHandler = HierarchyHandler()
    xmlparser.setContentHandler(hierarchyHandler)
    xmlparser.parse(hierarchy_file)

    # Country cases
    countryHandler = CountryHandler()
    countryHandler.setCaseList(suitesReader.getSuites()[CONST.TYPE_COUNTRY])
    xmlparser.setContentHandler(countryHandler)
    xmlparser.parse(country_file)
    countryHandler.outputcase(b_baseline, region)

    # State cases
    stateHandler = StateHandler()
    stateHandler.setCaseList(suitesReader.getSuites()[CONST.TYPE_STATE])
    for countryName, countryId in countryHandler.getIdMap().items():
        stateHandler.setCountryName(countryName).setTargetStateIdList(hierarchyHandler.getHierarchyTree()[countryId])
        xmlparser.setContentHandler(stateHandler)
        xmlparser.parse(state_file)
    stateHandler.outputcase(b_baseline, region)

    # City cases
    cityHandler = CityHandler()
    cityHandler.setCaseList(suitesReader.getSuites()[CONST.TYPE_CITY])
    for stateName, stateId in stateHandler.getIdMap().items():
        cityHandler.setStateName(stateName).setTargetCityIdList(hierarchyHandler.getHierarchyTree()[stateId])
        xmlparser.setContentHandler(cityHandler)
        xmlparser.parse(city_file)
    cityHandler.outputcase(b_baseline, region)

    # Street & POI cases
    streetHandler = StreetHandler()
    streetHandler.setCaseList(suitesReader.getSuites()[CONST.TYPE_STREET])
    poiHandler = POIHandler()
    poiHandler.setCaseList(suitesReader.getSuites()[CONST.TYPE_POI])
    for cityName, cityId in cityHandler.getIdMap().items():
        streetHandler.setCityName(cityName)
        xmlparser.setContentHandler(streetHandler)
        xmlparser.parse(os.path.join(vdedir, hierarchyHandler.getCityFilePath()[cityId][CONST.TYPE_STREET]))
        poiHandler.setCityName(cityName)
        xmlparser.setContentHandler(poiHandler)
        xml_file = os.path.join(vdedir, hierarchyHandler.getCityFilePath()[cityId][CONST.TYPE_POI])
        if os.path.exists(xml_file):
            xmlparser.parse(xml_file)
    streetHandler.outputcase(b_baseline, region)
    poiHandler.outputcase(b_baseline, region)

    # Chain cases
    chainHandler = ChainHandler()
    xmlparser.setContentHandler(chainHandler)
    xmlparser.parse(chain_file)
    chainHandler.outputcase(b_baseline, region)

    # Category cases
    categoryHandler = CategoryHandler()
    categoryHandler.setCaseList(suitesReader.getSuites()[CONST.TYPE_CATEGORY])
    xmlparser.setContentHandler(categoryHandler)
    for cate_file in cate_files:
        xmlparser.parse(cate_file)
    categoryHandler.outputcase(b_baseline, region)

    # statistic
    statistic_dir = os.path.join(os.path.dirname(os.path.abspath(vdedir)), 'statistic')
    if not os.path.exists(statistic_dir):
        statistic_dir = os.path.join('.', 'statistic')
    if os.path.exists(statistic_dir):
        case_dir = sys.path[0]  # TODO: trick
        extract_statistic(statistic_dir, case_dir, b_baseline)
    else:
        warn_logging_recoder("statistic dir[%s] not exist, please be know." % statistic_dir)


def extract_statistic(statistic_dir, case_dir, is_baseline):
    import glob
    import mcsv2json
    statistic_files = glob.glob(os.path.join(statistic_dir, '*/statistic*.txt'))

    final_case_dirs = [get_final_case_dir(f, case_dir, is_baseline) for f in statistic_files]
    key_fields = [get_statistic_key_fields(f) for f in statistic_files]

    for statistic_file, final_case_dir, key_field in zip(statistic_files, final_case_dirs, key_fields):
        if not os.path.exists(final_case_dir):
            os.makedirs(final_case_dir)
        mcsv2json.mcsv2json(statistic_file, key_field, final_case_dir)


def get_final_case_dir(statistic_file, case_dir, is_baseline):
    category = get_statistic_category(statistic_file)
    base_out = CONST.BASELINE_DIR if is_baseline else CONST.CASEOUTPUT_DIR
    return os.path.join(case_dir, base_out, 'stat', category.upper())


def get_statistic_category(statistic_file):
    base_name = os.path.basename(os.path.splitext(statistic_file)[0])
    parts = base_name.split('_', 1)
    category = parts[-1] if len(parts) == 2 else 'city'
    return category


def get_statistic_key_fields(statistic_file):
    category = get_statistic_category(statistic_file)
    return '%s_NAME' % category.upper()


if __name__ == '__main__':
    global options

    # initialization
    optionInit()
    (options, args) = parser.parse_args(sys.argv)
    checkParameter()

    # read testsuites
    suitesReader = readSuites(options.iregion)

    # extract cases
    extractCases(options.idir, options.ibaseline, suitesReader, options.iregion)
