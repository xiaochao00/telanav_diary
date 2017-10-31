﻿#-------------------------------------------------------------------------------
# Name:        RelationsGeneralCarto model
# Purpose:     this model is used to mapping the
#              columns: [ ]
#
# Author:      Kuang
#
# Created:     10/12/2015
# Copyright:   (c) rex 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from model.record import Record
from model.constants import *
from operator import itemgetter

import os
import sys
import datetime
import json
import csv

ROOT_DIR          = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
GLOBAL_KEY_PREFIX = "relations_signpost_"
CSV_SEP           = '`'
LF                = '\n'

PREV_SIGNPOST_ID = -1

STATISTIC_GENERAL_NAME_FEATURE_KEYS = (
)

STATISTIC_TRANS_NAME_FEATURE_KEYS = (
)

class RelationsSignpostDestination(Record):
    def __init__(self, region):
        Record.__init__(self)
        self.signpost_dump_file = os.path.join(ROOT_DIR, 'temporary', self.__class__.__name__)
        self.admin_hierarchy_dump_file = os.path.join(ROOT_DIR, 'temporary', 'signpost_destination_admin_hierarchy')
        self.stat                    = {}
        self.region                  = region
        self.sign_destination_dict       = {}
        self.admin_hierarchy_dict    = {}

    def dump2file(self):
        cmd = "select distinct \
            rsd.*, \
            rsdt.*, \
            vsd.*, \
            vpt.*, \
            vgo.*, \
            rl.left_admin_place_id, \
            rl.right_admin_place_id \
            from rdf_nav_link rnl \
            inner join rdf_sign_origin rso on rnl.link_id = rso.originating_link_id \
            inner join rdf_sign_destination rsd on rso.sign_id = rsd.sign_id \
            left join rdf_sign_destination_trans rsdt on rsd.sign_id = rsdt.sign_id and rsd.destination_number = rsdt.destination_number \
            left join vce_sign_destination vsd on rsd.sign_id = vsd.sign_id and rsd.destination_number = vsd.destination_number \
            left join vce_phonetic_text vpt on vsd.phonetic_id = vpt.phonetic_id \
            left join vce_geo_override vgo on vpt.phonetic_id = vgo.phonetic_id \
            inner join rdf_link rl on rsd.dest_link_id = rl.link_id \
            where rsd.exit_number is not null and iso_country_code in (%s) \
            order by rsd.sign_id, rsd.destination_number" % (REGION_COUNTRY_CODES(self.region, GLOBAL_KEY_PREFIX))
        print cmd
        self.cursor.copy_expert("COPY (%s) TO STDOUT DELIMITER '%s' CSV "%(cmd,CSV_SEP),open(self.signpost_dump_file,"w"))

    def dumpadminhierarchyfile(self):
        cmd = "select * from rdf_admin_hierarchy"
        print cmd
        self.cursor.copy_expert("COPY (%s) TO STDOUT DELIMITER '%s' CSV " % (cmd,CSV_SEP), open(self.admin_hierarchy_dump_file, "w"))
        #load admin hierarchy file into memory
        with open(self.admin_hierarchy_dump_file, "r") as admin_hierarchy_f:
            lines = csv.reader(admin_hierarchy_f, delimiter=CSV_SEP)
            for admin_line in lines:
                admin_line_p = [x.strip() for x in admin_line]
            # for admin_line in admin_hierarchy_f:
            #     admin_line = admin_line.strip()
            #     #admin_line_p = admin_line.split(CSV_SEP)
            #     admin_line_p = Record.split(admin_line)
                if len(admin_line_p) < 1:
                    continue
                self.admin_hierarchy_dict[admin_line_p[0]] = [admin_line_p[3], admin_line_p[4], admin_line_p[5], admin_line_p[6], admin_line_p[7]]

    def get_statistic(self):
        self.dumpadminhierarchyfile()
        try:
            self.dump2file()
        except Exception, e:
            print 'Exception: %s' % e
            return {}
        processcount = 0
        with open(self.signpost_dump_file, "r",1024*1024*1024) as csv_f:
            lines = csv.reader(csv_f, delimiter=CSV_SEP)
            for line in lines:
                line_p = [x.strip() for x in line]

            # for line in csv_f:
            #     line = line.rstrip()
            #     #line_p = line.split(CSV_SEP)
            #     line_p = Record.split(line)
                if len(line_p) < 1:
                    continue
                if len(line_p) != 26:
                    print '\n%s\n'% line
                    continue
                self._build(line_p)
                processcount += 1
                if processcount%5000 == 0:
                    print "\rProcess index [ "+str(processcount)+" ]",
            print "\rProcess index [ "+str(processcount)+" ]",
            self.__statistic()

        # write to file
        with open(os.path.join(ROOT_DIR, "output", "stat", self.__class__.__name__), 'w') as stf:
            stf.write(json.dumps(self.stat))
        return self.stat

    #0:exit_number, 1:straight_on_sign, 2:language_code, 3:alt_exit_number
    #trans: 0:trans:transliteration_type, 1:trans:exit_number
    def __statistic(self):
        sign_destination_list = list(self.sign_destination_dict.values())
        for sign_destination in sign_destination_list:
            if sign_destination[0] != "":
                self.__count("{0}ref:{1}".format(GLOBAL_KEY_PREFIX, sign_destination[2]))
            if sign_destination[3] != "":
                self.__count("{0}alt_ref:{1}".format(GLOBAL_KEY_PREFIX, sign_destination[2]))
            if [''] == sign_destination[4]:
                sign_destination_trans = ['']
            else:
                print sign_destination[4]
                sign_destination_trans = sorted(sign_destination[4], key=itemgetter(1,0))
            for sign_destination_tran in sign_destination_trans:
                if sign_destination_tran != "":
                    self.__count("{0}ref:{1}:trans:{2}".format(GLOBAL_KEY_PREFIX, sign_destination[2], sign_destination_tran))

            sign_destination_phonetics = sign_destination[5]
            for p_keys in self._get_phonetic_key(sign_destination_phonetics):
                self.__count("{0}ref:{1}:{2}".format(GLOBAL_KEY_PREFIX, sign_destination[2], p_keys))

    #phonetic:
    #0:phonetic_id, 1:preferred, 2:type
    #3:phonetic_id, 4:phonetic_string, 5:phonetic_language_code, 6:transcription_method
    #7:geo_override_id, 8:phonetic_id, 9:admin_place_id, 10:preferred
    #11:left_admin_place_id, 12:right_admin_place_idW
    def _get_phonetic_key(self, listphonetics):
        preferred_phonetics_dict = {}
        for phonetics in listphonetics:
            if phonetics[9] != "":
                if self._is_geo_override(phonetics[11], phonetics[9]) or self._is_geo_override(phonetics[12], phonetics[9]):
                    preferred_phonetics_dict[phonetics[0]] = phonetics

        if len(preferred_phonetics_dict) == 0:
            for phonetics in listphonetics:
                if phonetics[1] == "Y":
                    preferred_phonetics_dict[phonetics[0]] = phonetics

        preferred_phonetic = {}
        length = 0
        for key, vals in preferred_phonetics_dict.items():
            phonetic_key = "phonetics:{0}:{1}:{2}".format(vals[5], vals[6], vals[2])
            if not preferred_phonetic.has_key(phonetic_key):
                preferred_phonetic[phonetic_key] = None

        if len(preferred_phonetic) == 0:
            return []
        return preferred_phonetic.keys()

    def _is_geo_override(self, admin_place_id, geo_admin_place_id):
        if admin_place_id not in self.admin_hierarchy_dict:
            return False

        if self.admin_hierarchy_dict.has_key(admin_place_id):
            admin_hierarchy = self.admin_hierarchy_dict.get(admin_place_id)
        if admin_hierarchy[4] == geo_admin_place_id:
            return True
        if admin_hierarchy[3] == geo_admin_place_id:
            return True
        if admin_hierarchy[2] == geo_admin_place_id:
            return True
        if admin_hierarchy[1] == geo_admin_place_id:
            return True
        if admin_hierarchy[0] == geo_admin_place_id:
            return True

    #0:sign_id, 1:destination_number, 2:dest_link_id, 3:exit_number, 4:straight_on_sign, 5:language_code, 6:alt_exit_number
    #7:trans:sign_id, 8:trans:destination_number, 9:trans:transliteration_type, 10:trans:exit_number
    #11:sign_id, 12:destination_number, 13:phonetic_id, 14:preferred, 15:type
    #16:phonetic_id, 17:phonetic_string, 18:phonetic_language_code, 19:transcription_method
    #20:geo_override_id, 21:phonetic_id, 22:admin_place_id, 23:preferred
    #24:left_admin_place_id, 25:right_admin_place_idW
    def _build(self, line_p):
        global PREV_SIGNPOST_ID
        sign_destination_id = "{0:d}{1:04d}".format(int(line_p[0]), int(line_p[1]))
        if sign_destination_id != PREV_SIGNPOST_ID:
            if len(self.sign_destination_dict) != 0:
                self.__statistic()
                self.sign_destination_dict.clear()
            PREV_SIGNPOST_ID = sign_destination_id
        if not self.sign_destination_dict.has_key(sign_destination_id):
            sign_destination_list = [line_p[3], line_p[4], line_p[5], line_p[6], [], []]
        else:
            sign_destination_list = self.sign_destination_dict[sign_destination_id]
        if line_p[9] not in sign_destination_list[4]:
            sign_destination_list[4].append(line_p[9])
        phonetics = [line_p[13], line_p[14], line_p[15], line_p[16], line_p[17], line_p[18], line_p[19], line_p[20], line_p[21], line_p[22], line_p[23], line_p[24], line_p[25]]
        sign_destination_list[5].append(phonetics)
        self.sign_destination_dict[sign_destination_id] = sign_destination_list

    def __add(self, line, dict):
        subdict = {}
        if not dict.has_key(line[0]):
           dict[line[0]] = subdict
        else:
           subdict = dict.get(line[0])
        subdict[line[2]] = (float(line[3])/100000, float(line[4])/100000)

    def __count(self,key):
        key = key.lower()
        if self.stat.has_key(key):
            self.stat[key] += 1
        else:
            self.stat[key] = 1

if __name__ == "__main__":
    # use to test this model
    bg = datetime.datetime.now()
    stat =  RelationsSignpostDestination('na').get_statistic()
    keys = stat.keys()
    print "==>"
    print "{%s}"%(",".join(map(lambda px: "\"%s\":%s"%(px,stat[px]) ,keys)))
    print "<=="
    ed = datetime.datetime.now()
    print "Cost time:"+str(ed - bg)
