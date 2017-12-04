#-------------------------------------------------------------------------------
# Name:        WaysNavigableLinkGeom model
# Purpose:     this model is used to mapping the rdf_nav_link, rdf_link and rdf_access
#              columns: [ link_id,iso_country_code,access_id,status_id,functional_class,controlled_access,travel_direction,boat_ferry,
#                         rail_ferry,multi_digitized,divider,divider_legal,frontage,paved,ramp,private,tollway,poi_access,intersection_category,
#                         speed_category,lane_category,coverage_indicator,from_ref_num_lanes,to_ref_num_lanes,physical_num_lanes,
#                         from_ref_speed_limit,to_ref_speed_limit,speed_limit_source,low_mobility,public_access,grade_category,confidence_level_rating,
#                         pedestrian_preferred,limited_access_road,road_class,overpass_underpassrdf,
#                         bridge, tunnel,
#                         automobiles, buses, taxis, carpools, pedestrians, trucks, deliveries, emergency_vehicles, through_traffic, motorcycles]
#
# Author:      rex
#
# Created:     10/12/2015
# Copyright:   (c) rex 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from record import Record
from constants import *
import os
import sys
import datetime
import json

ROOT_DIR          = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
GLOBAL_KEY_PREFIX = "ways_navlink_"
CSV_SEP           = '`'
LF                = '\n'

#(key, category, function)
STATISTIC_KEYS    = (("zlevel:ref",False,"zlevel_ref"),
("zlevel:nonref", True, "zlevel_nonref"))

class WaysNavigableLinkGeom(Record):
    def __init__(self, region):
        Record.__init__(self)
        self.navlink_file = os.path.join(ROOT_DIR, "temporary", self.__class__.__name__)
        self.stat         = {}
        self.region       = region

    def dump2file(self):
        cmd = "SELECT \
rnl.link_id, \
rlg.seq_num \
FROM \
public.rdf_nav_link as rnl left join public.rdf_link as rl on rnl.link_id=rl.link_id \
left join public.rdf_link_geometry as rlg on rnl.link_id=rlg.link_id \
WHERE rnl.iso_country_code in (%s) and (rlg.seq_num = 999999 or rlg.seq_num = 0)"%(REGION_COUNTRY_CODES(self.region, GLOBAL_KEY_PREFIX))
        print cmd
        self.cursor.copy_expert("COPY (%s) TO STDOUT DELIMITER '`'"%(cmd),open(self.navlink_file,"w"))

    def get_statistic(self):
        try:
            self.dump2file()
        except:
            print "Some table or schema don't exist! Please check the upper sql"
            return {}
        processcount = 0
        with open(self.navlink_file, "r",1024*1024*1024) as csv_f:
            for line in csv_f:
                line_p = line.split(CSV_SEP)
                if len(line_p) < 1:
                    continue
                self.__statistic(line_p)
                processcount += 1
                if processcount%5000 == 0:
                    print "\rProcess index [ "+str(processcount)+" ]",
            print "\rProcess index [ "+str(processcount)+" ]",
        # write to file
        with open(os.path.join(ROOT_DIR, "output", "stat", self.__class__.__name__), 'w') as stf:
            stf.write(json.dumps(self.stat))
        return self.stat

    def __statistic(self,line):
        for keys in STATISTIC_KEYS:
            try:
                getattr(self,'_%s__get_%s'%(self.__class__.__name__,keys[2]))(keys,line)
            except:
                print "The statistic [ %s ] didn't exist"%(keys[2])
                print "Unexpected error:[ %s.py->%s] %s"%(self.__class__.__name__, '__statistic', str(sys.exc_info()))

    def __count(self,key):
        if self.stat.has_key(key):
            self.stat[key] += 1
        else:
            self.stat[key] = 1

    # all statistic method
    def __get_zlevel_ref(self,keys,line):
        if '0' == line[1]:
            self.__count("%s%s"%(GLOBAL_KEY_PREFIX,keys[0]))

    def __get_zlevel_nonref(self,keys,line):
        if '999999' == line[1]:
            self.__count("%s%s"%(GLOBAL_KEY_PREFIX,keys[0]))

if __name__ == "__main__":
    # use to test this model
    bg = datetime.datetime.now()
    navlink_stat =  WaysNavigableLinkGeom('na').get_statistic()
    keys = navlink_stat.keys()
    print "==>"
    print "{%s}"%(",".join(map(lambda px: "\"%s\":%s"%(px,navlink_stat[px]) ,keys)))
    print "<=="
    ed = datetime.datetime.now()
    print "Cost time:"+str(ed - bg)
