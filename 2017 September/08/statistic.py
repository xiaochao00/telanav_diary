import os
import re
import sys
import glob
import multiprocessing

from xml.dom import minidom as minidom

XML_COUNTRY = 1
XML_STATE = 2
XML_CITY = 3
XML_HIERARCHY = 4
XML_STREET_POI = 5

XML_STREET = 6
XML_POI = 7

XML_CATEGORY = 8
XML_CHAIN = 9

reload(sys)
sys.setdefaultencoding('utf-8')


class StatisticItem(object):
    """
        class comment
    """

    def __init__(self, typ, vals):
        self.typ = typ
        self.vals = vals

    def __str__(self):
        return '%s : %s ' % (self.typ, self.vals)


def get_city_id(street_poi_xml):
    return os.path.splitext(os.path.basename(street_poi_xml))[0].split('_')[1]


def get_admin_name(feature_elem):
    names = []

    for name in feature_elem.getElementsByTagName('Name'):
        orth = name.getAttribute('Value')
        lc = name.getAttribute('Language')

        names.append((orth, lc))

    if not names:
        return ''
    else:
        return '%s:%s' % (names[0][0], names[0][1])


##    if names[0][1] in ['ENG', 'FRE', 'SPA']:
##        return '%s:%s' % (names[0][0], names[0][1])
##
##    pre_names = [n for n in names if n[1] in ['ENG', 'FRE', 'SPA']]
##    if pre_names:
##        return '%s:%s' % (pre_names[0][0], pre_names[0][1])
##    else:
##        return ''

def parse_street_xml(street_file):
    if not os.path.exists(street_file):
        return StatisticItem(XML_STREET, [0, 0])

    doc = minidom.parse(street_file)

    # get root element
    root = doc.documentElement

    street_num = 0

    vde_streets = 0  # actual count
    # get children elements: <Streets/> <Streets/>
    for streets in root.getElementsByTagName('Streets'):
        street_num = streets.getAttribute('Num')

        for street in streets.getElementsByTagName('Street'):
            vde_streets += 1

        break

    return StatisticItem(XML_STREET, [vde_streets, street_num])


def parse_poi_xml(poi_file):
    if not os.path.exists(poi_file):
        return StatisticItem(XML_POI, [0, 0])
    doc = minidom.parse(poi_file)
    # get root element
    root = doc.documentElement

    street_num = 0

    vde_pois = 0  # actual count
    # get children elements: <Pois/> <Pois/>
    for pois in root.getElementsByTagName('Pois'):
        poi_num = pois.getAttribute('Num')

        for poi in pois.getElementsByTagName('Poi'):
            vde_pois += 1

        break

    return StatisticItem(XML_POI, [vde_pois, poi_num])


def parse_street_poi(street_poi_path):
    print 'PARSING %s' % street_poi_path

    assert os.path.isdir(street_poi_path)

    street_files = glob.glob(os.path.join(street_poi_path, 'Street_*.xml'))
    poi_files = glob.glob(os.path.join(street_poi_path, 'POI_*.xml'))

    if len(street_files) != len(poi_files):
        print sys.stderr.write(
            'Error: street/poi file count not equal in %s \n, street files count = %d, poi files count = %d' % (
                street_poi_path, len(street_files), len(poi_files)))

    city_ids = [get_city_id(f) for f in street_files]
    city_ids.extend(get_city_id(f) for f in poi_files)

    city_ids = list(set(city_ids))
    city_ids.sort()

    street_files = [os.path.join(street_poi_path, 'Street_%s.xml' % city_id) for city_id in city_ids]
    poi_files = [os.path.join(street_poi_path, 'POI_%s.xml' % city_id) for city_id in city_ids]

    procs = max(1, multiprocessing.cpu_count() / 2)
    pool = multiprocessing.Pool(processes=procs)

    street_stats = []
    poi_stats = []
    for street_file in street_files:
        street_stat = parse_street_xml(street_file)
        street_stats.append(street_stat)
    for poi_file in poi_files:
        poi_stat = parse_poi_xml(poi_file)
        poi_stats.append(poi_stat)
    # street_stats = pool.map(parse_street_xml, street_files)
    # poi_stats = pool.map(parse_poi_xml, poi_files)

    vde_stree_pois = {}
    for city_id, street_stat, poi_stat in zip(city_ids, street_stats, poi_stats):
        city_id = int(city_id)
        vde_stree_pois[city_id] = (street_stat.vals[0], poi_stat.vals[0])

    return StatisticItem(XML_STREET_POI, [vde_stree_pois, len(city_ids)])


def parse_street_poi_xml(xmls):
    street_xml, poi_xml = xmls
    city_id = get_city_id(street_xml)
    if city_id != get_city_id(poi_xml):
        return StatisticItem(XML_STREET_POI, [{}, 0])

    vde_stree_poi = {}
    # street_stat = parse_street_xml(street_xml)
    # poi_stat = parse_poi_xml(poi_xml)

    from parse_xml_tool import parse_poi_xml_by_ET, parse_street_xml_by_ET
    street_stat = parse_street_xml_by_ET(street_xml)
    poi_stat = parse_poi_xml_by_ET(poi_xml)

    city_id = int(city_id)
    vde_stree_poi[city_id] = (street_stat.vals[0], poi_stat.vals[0])

    # print vde_stree_poi

    return StatisticItem(XML_STREET_POI, [vde_stree_poi, 1])


def parse_country_xml(country_file):
    print 'PARSING %s' % country_file

    doc = minidom.parse(country_file)

    # get root element
    root = doc.documentElement

    country_num = 0
    vde_countries = {}
    # get children elements: <Countries/> <Countries/>
    for countries in root.getElementsByTagName('Countries'):
        country_num = countries.getAttribute('Num')

        for country in countries.getElementsByTagName('Country'):
            country_id = int(country.getAttribute('Id'))
            ##            for name in country.getElementsByTagName('Name'):
            ##                orth = name.getAttribute('Value')
            ##                lc = name.getAttribute('Language')
            ##
            ##                vde_countries[country_id] = '%s:%s' %(orth, lc)
            ##
            ##                break
            ##        break
            vde_countries[country_id] = get_admin_name(country)

    return StatisticItem(XML_COUNTRY, [vde_countries, country_num])


def parse_state_xml(state_file):
    print 'PARSING %s' % state_file

    doc = minidom.parse(state_file)

    # get root element
    root = doc.documentElement

    state_num = 0
    vde_states = {}
    # get children elements: <States/> <States/>
    for states in root.getElementsByTagName('States'):
        state_num = states.getAttribute('Num')

        for state in states.getElementsByTagName('State'):
            state_id = int(state.getAttribute('Id'))
            ##            for name in state.getElementsByTagName('Name'):
            ##                orth = name.getAttribute('Value')
            ##                lc = name.getAttribute('Language')
            ##
            ##                vde_states[state_id] = '%s:%s' %(orth, lc)
            ##
            ##                break

            name = get_admin_name(state)
            vde_states[state_id] = name

    return StatisticItem(XML_STATE, [vde_states, state_num])


def parse_city_xml(city_file):
    print 'PARSING %s' % city_file
    doc = minidom.parse(city_file)

    # get root element
    root = doc.documentElement

    city_num = 0
    vde_cities = {}
    # get children elements: <Cities/> <Cities/>
    for cities in root.getElementsByTagName('Cities'):
        city_num = cities.getAttribute('Num')

        for city in cities.getElementsByTagName('City'):
            city_id = int(city.getAttribute('Id'))
            ##            for name in city.getElementsByTagName('Name'):
            ##                orth = name.getAttribute('Value')
            ##                lc = name.getAttribute('Language')
            ##
            ##                vde_cities[city_id] = '%s:%s' %(orth, lc)
            name = get_admin_name(city)
            vde_cities[city_id] = name

    return StatisticItem(XML_CITY, [vde_cities, city_num])


def parse_hierarchy_xml(hierachy_xml):
    print 'PARSING %s' % hierachy_xml

    doc = minidom.parse(hierachy_xml)

    # get root element
    root = doc.documentElement

    vde_hierachy = {}
    for hierarchy in root.getElementsByTagName('Hierarchy'):
        for country in hierarchy.getElementsByTagName('Country'):
            country_id = int(country.getAttribute('Id'))
            vde_hierachy.setdefault(country_id, {})

            for state in country.getElementsByTagName('State'):
                state_id = int(state.getAttribute('Id'))
                vde_country = vde_hierachy[country_id]
                vde_country.setdefault(state_id, [])

                for city in state.getElementsByTagName('City'):
                    city_id = int(city.getAttribute('Id'))
                    vde_state = vde_country[state_id]
                    vde_state.append(city_id)

    return StatisticItem(XML_HIERARCHY, [vde_hierachy])


def parse_category_chain_xmls(category_xmls, chain_xml):
    category_items = map(parse_category_xml, category_xmls)
    chain_item = parse_chain_xml(chain_xml)

    main_category_num = len(category_xmls)
    sub_category_num = sum([i.vals[1] for i in category_items])
    chain_num = chain_item.vals[1]

    return main_category_num, sub_category_num, chain_num


def parse_category_xml(category_xml):
    print 'PARSING %s' % category_xml

    doc = minidom.parse(category_xml)

    # get root element
    root = doc.documentElement

    category_num = 0
    for categories in root.getElementsByTagName('Categories'):
        for category in categories.getElementsByTagName('Category'):
            category_num += 1

    return StatisticItem(XML_CATEGORY, [[], category_num])


def parse_chain_xml(chain_xml):
    print 'PARSING %s' % chain_xml

    doc = minidom.parse(chain_xml)

    # get root element
    root = doc.documentElement

    chain_num = 0
    for chains in root.getElementsByTagName('Chains'):
        for chain in chains.getElementsByTagName('Chain'):
            chain_num += 1

    return StatisticItem(XML_CHAIN, [[], chain_num])


class FeatureFiles(object):
    def __init__(self, vde_path):
        self.country_xml = None
        self.state_xml = None
        self.city_xml = None
        self.hierarchy_xml = None
        self.street_xmls = []
        self.poi_xmls = []

        self.category_xmls = []
        self.chain_xml = None
        self.subcity_xml = None
        self.cross_street_xmls = []
        self.main_xml = None

        self._search(vde_path)

    def _search(self, vde_path):
        for f in os.listdir(vde_path):
            vde = os.path.join(vde_path, f)

            if f == 'Country.xml':
                self.country_xml = vde
            elif f == 'State.xml':
                self.state_xml = vde
            elif f == 'City.xml':
                self.city_xml = vde
            elif f == 'Hierarchy.xml':
                self.hierarchy_xml = vde
            elif f == 'SubCity.xml':
                self.subcity_xml = vde
            elif f == 'Chain.xml':
                self.chain_xml = vde
            elif f.startswith('TN_VDE_') and f.endswith('.xml'):
                self.main_xml = vde
            elif f.startswith('Category_') and f.endswith('.xml'):
                self.category_xmls.append(vde)
            elif os.path.isdir(vde) and f.startswith('State_'):
                self.street_xmls.extend(glob.glob(os.path.join(vde, 'Street_*.xml')))
                self.poi_xmls.extend(glob.glob(os.path.join(vde, 'POI_*.xml')))
                self.cross_street_xmls.extend(glob.glob(os.path.join(vde, 'CrossStreet_*.xml')))

        fail = False
        if not self.country_xml or not os.path.exists(self.country_xml):
            sys.stderr.write('Error: Country.xml can not be found!\n')
            fail = True
        elif not self.state_xml or not os.path.exists(self.state_xml):
            sys.stderr.write('Error: State.xml can not be found!\n')
            fail = True
        elif not self.city_xml or not os.path.exists(self.city_xml):
            sys.stderr.write('Error: City.xml can not be found!\n')
            fail = True
        elif not self.subcity_xml or not os.path.exists(self.subcity_xml):
            sys.stderr.write('Warning: SubCity.xml can not be found!\n')
            # fail = True
        elif not self.hierarchy_xml or not os.path.exists(self.hierarchy_xml):
            sys.stderr.write('Error: Hierarchy.xml can not be found!\n')
            fail = True
        elif not self.chain_xml or not os.path.exists(self.chain_xml):
            sys.stderr.write('Error: Chain.xml can not be found!\n')
            fail = True
        elif not self.street_xmls or not self.poi_xmls:
            sys.stderr.write('Error: no street xmls or poi xmls!\n')
            fail = True
        elif not self.category_xmls:
            sys.stderr.write('Error: no category xmls!\n')
            fail = True

        if len(self.street_xmls) != len(self.poi_xmls):
            sys.stderr.write('Error: no street xmls count not equal poi xmls count!\n')
            return not fail

        self.street_xmls.sort()
        self.poi_xmls.sort()
        self.cross_street_xmls.sort()
        self.category_xmls.sort()

        return not fail


class Statistic(object):
    """
        class comment
    """

    def __init__(self, vde_path):
        self.vde_path = os.path.abspath(vde_path)

        self.pool = multiprocessing.Pool(processes=max(1, multiprocessing.cpu_count() / 2))

        self.feature_files = FeatureFiles(self.vde_path)

    def parse(self):
        print '*' * 80
        print 'PARSING XML ...'
        assert os.path.isdir(self.vde_path)

        country_xml = self.feature_files.country_xml
        state_xml = self.feature_files.state_xml
        city_xml = self.feature_files.city_xml
        hierarchy_xml = self.feature_files.hierarchy_xml
        street_xmls = self.feature_files.street_xmls
        poi_xmls = self.feature_files.poi_xmls

        country_stat = parse_country_xml(country_xml)
        state_stat = parse_state_xml(state_xml)
        city_stat = parse_city_xml(city_xml)
        hirerarchy_stat = parse_hierarchy_xml(hierarchy_xml)

        # street_poi_stats = self.pool.map(parse_street_poi_xml, zip(street_xmls, poi_xmls))
        # self.pool.close()
        # self.pool.join()
        street_poi_stats = []
        for i in range(len(street_xmls)):
            street_xml = street_xmls[i]
            poi_xml = poi_xmls[i]
            stat = parse_street_poi_xml((street_xml, poi_xml))
            street_poi_stats.append(stat)

        street_poi_stat = StatisticItem(XML_STREET_POI, [])
        vde_street_pois = {}
        city_count = 0

        for stat in street_poi_stats:
            vde_street_pois.update(stat.vals[0])
            city_count += stat.vals[1]

        street_poi_stat.vals = [vde_street_pois, city_count]

        return country_stat, state_stat, city_stat, hirerarchy_stat, street_poi_stat

    def _generate_detais(self, stats):
        country_stat, state_stat, city_stat, hirerarchy_stat, street_poi_stat = stats

        detail_items = []
        for country_id in hirerarchy_stat.vals[0]:
            country = hirerarchy_stat.vals[0][country_id]
            country_name = country_stat.vals[0].get(country_id, '')
            if not country_name:
                print "no country name for country id: %s" % country_id
                continue

            for state_id in country:
                state = country[state_id]
                state_name = state_stat.vals[0].get(state_id, '')
                if not state_name:
                    print "no state name for state id: %s" % state_id
                    continue

                for city_id in state:
                    city_name = city_stat.vals[0].get(city_id, '')
                    if not city_name:
                        print "no city name for city id: %s" % city_id
                        continue

                    street_num, poi_num = street_poi_stat.vals[0].get(city_id, [0, 0])

                    item = [country_id, country_name, state_id, state_name, city_id, city_name, street_num, poi_num]

                    detail_items.append(item)

        return detail_items

    def statistic(self, stats):
        print '*' * 80
        print 'STATISTIC ... '

        statistic_dir = self.get_statistic_dir()
        if not os.path.exists(statistic_dir):
            os.makedirs(statistic_dir)

        detail_items = self._generate_detais(stats)

        detail_stat_file = os.path.join(statistic_dir, 'statistic.txt')
        state_stat_file = os.path.join(statistic_dir, 'statistic_state.txt')
        country_stat_file = os.path.join(statistic_dir, 'statistic_country.txt')
        region_stat_file = os.path.join(statistic_dir, 'statistic_region.txt')

        self.write_detail_statistic(detail_items, detail_stat_file)
        self.write_state_statistic(detail_items, state_stat_file)
        self.write_country_statistic(detail_items, country_stat_file)
        self.write_reion_statistic(detail_items, region_stat_file)

        self.statistic_category_chain(statistic_dir)
        self.statistic_feature_files(statistic_dir)

    def statistic_category_chain(self, statistic_dir):
        import glob
        category_xmls = self.feature_files.category_xmls
        chain_xml = self.feature_files.chain_xml

        category_chain_stat_file = os.path.join(statistic_dir, 'statistic_category_chain.txt')
        print category_chain_stat_file

        self.write_category_chain_statistic(parse_category_chain_xmls(category_xmls, chain_xml),
                                            category_chain_stat_file)

    def statistic_feature_files(self, statistic_dir):
        feature_stat_file = os.path.join(statistic_dir, 'statistic_files.txt')
        self.write_feature_files_statistic(feature_stat_file)

    def get_version_num(self):
        import time
        now = int(time.time())
        timeArray = time.localtime(now)
        return time.strftime("%Y%m%d_%H%M%S", timeArray)

    def get_statistic_dir(self):
        statistic_root = os.path.dirname(self.vde_path)
        return os.path.join(statistic_root, 'statistic', self.get_version_num())
        # return os.path.join(statistic_root, 'statistic')

    def write_detail_statistic(self, detail_items, statistic_file):
        # details of statistic
        ofs = open(statistic_file, 'w')
        title = ['COUNTRY_ID', 'COUNTRY_NAME', 'STATE_ID', 'STATE_NAME', 'CITY_ID', 'CITY_NAME', 'STREET_NUM',
                 'POI_NUM']
        detail_items.sort()

        ofs.write('%s\n' % ('\t'.join(title)))
        for item in detail_items:
            country_id, country_name, state_id, state_name, city_id, city_name, street_num, poi_num = item
            line = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                country_id, country_name, state_id, state_name, city_id, city_name, street_num, poi_num)
            ofs.write(line)

        ofs.close()

    def write_state_statistic(self, detail_items, statistic_file):
        # summary of statistic
        state_summary = []
        state_statistic = {}
        for item in detail_items:
            country_id, country_name, state_id, state_name, city_id, city_name, street_num, poi_num = item
            state_statistic.setdefault((country_name, state_name), []).append((city_id, street_num, poi_num))

        state_summary = []
        for key in state_statistic:
            val = state_statistic[key]

            country_name, state_name = key
            city_num = len(val)
            street_num = sum((v[1] for v in val))
            poi_num = sum((v[2] for v in val))

            state_summary.append((country_name, state_name, city_num, street_num, poi_num))
        state_summary.sort()

        ofs = open(statistic_file, 'w')
        title = ['COUNTRY_NAME', 'STATE_NAME', 'CITY_NUM', 'STREET_NUM', 'POI_NUM']
        ofs.write('%s\n' % ('\t'.join(title)))
        for item in state_summary:
            country_name, state_name, city_num, street_num, poi_num = item
            line = '%s\t%s\t%s\t%s\t%s\n' % (country_name, state_name, city_num, street_num, poi_num)
            ofs.write(line)
        ofs.close()

    def write_country_statistic(self, detail_items, statistic_file):
        country_statistic = {}
        for item in detail_items:
            country_id, country_name, state_id, state_name, city_id, city_name, street_num, poi_num = item
            country_statistic.setdefault(country_name, []).append((state_id, city_id, street_num, poi_num))

        country_summary = []
        for key in country_statistic:
            val = country_statistic[key]
            country_name = key

            state_num = len(set(v[0] for v in val))
            city_num = len(set(v[1] for v in val))
            street_num = sum((v[2] for v in val))
            poi_num = sum((v[3] for v in val))

            country_summary.append((country_name, state_num, city_num, street_num, poi_num))
        country_summary.sort()

        ofs = open(statistic_file, 'w')
        title = ['COUNTRY_NAME', 'STATE_NUM', 'CITY_NUM', 'STREET_NUM', 'POI_NUM']
        ofs.write('%s\n' % ('\t'.join(title)))
        for item in country_summary:
            country_name, state_num, city_num, street_num, poi_num = item
            line = '%s\t%s\t%s\t%s\t%s\n' % (country_name, state_num, city_num, street_num, poi_num)
            ofs.write(line)
        ofs.close()

    def write_reion_statistic(self, detail_items, statistic_file):
        summary = []

        country_num = len(set(v[0] for v in detail_items))
        state_num = len(set(v[2] for v in detail_items))
        city_num = len(set(v[4] for v in detail_items))
        street_num = sum((v[6] for v in detail_items))
        poi_num = sum((v[7] for v in detail_items))

        summary = [(country_num, state_num, city_num, street_num, poi_num)]

        ofs = open(statistic_file, 'w')
        title = ['COUNTRY_NUM', 'STATE_NUM', 'CITY_NUM', 'STREET_NUM', 'POI_NUM']
        ofs.write('%s\n' % ('\t'.join(title)))
        for item in summary:
            line = '%s\t%s\t%s\t%s\t%s\n' % (country_num, state_num, city_num, street_num, poi_num)
            ofs.write(line)
        ofs.close()

    def write_category_chain_statistic(self, category_chain_stat, statistic_file):
        main_category_num, sub_category_num, chain_num = category_chain_stat
        ofs = open(statistic_file, 'w')
        title = ['MAIN_CATEGORY_NUM', 'SUB_CATEGORY_NUM', 'CHAIN_NUM']
        ofs.write('%s\n' % ('\t'.join(title)))
        line = '%s\t%s\t%s\n' % (main_category_num, sub_category_num, chain_num)
        ofs.write(line)
        ofs.close()

    def write_feature_files_statistic(self, statistic_file):
        poi_file_num = len(self.feature_files.poi_xmls)
        street_file_num = len(self.feature_files.street_xmls)
        cross_street_file_num = len(self.feature_files.cross_street_xmls)
        category_file_num = len(self.feature_files.category_xmls)

        chain_file_num = 1 if self.feature_files.chain_xml else 0
        city_file_num = 1 if self.feature_files.city_xml else 0
        state_file_num = 1 if self.feature_files.state_xml else 0
        country_file_num = 1 if self.feature_files.country_xml else 0
        hierarchy_file_num = 1 if self.feature_files.hierarchy_xml else 0
        subcity_file_num = 1 if self.feature_files.subcity_xml else 0
        main_file_num = 1 if self.feature_files.main_xml else 0

        ofs = open(statistic_file, 'w')
        title = ['POI_FILE_NUM', 'STREET_FILE_NUM', 'CROSS_STREET_FILE_NUM', 'CATEGORY_FILE_NUM',
                 'CHAIN_FILE_NUM', 'CITY_FILE_NUM', 'STATE_FILE_NUM', 'COUNTRY_FILE_NUM',
                 'HIERARCHY_FILE_NUM', 'SUB_CITY_FILE_NUM', 'MAIN_VDE_FILE'
                 ]
        ofs.write('%s\n' % ('\t'.join(title)))
        fields = [poi_file_num, street_file_num, cross_street_file_num, category_file_num,
                  chain_file_num, city_file_num, state_file_num, country_file_num,
                  hierarchy_file_num, subcity_file_num, main_file_num
                  ]
        line = '%s\n' % '\t'.join(map(str, fields))
        ofs.write(line)
        ofs.close()


##print parse_hierarchy_xml(sys.argv[1])
##print parse_country_xml(sys.argv[2])
##print parse_state_xml(sys.argv[3])
##print parse_city_xml(sys.argv[4])
# parse_street_xml('..\lgwu\State_10120098\Street_1014093290.xml')

def main():
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import time
    s = time.time()

    stat = Statistic(sys.argv[1])

    stats = stat.parse()
    stat.statistic(stats)

    print 'Time cost: %s' % (time.time() - s)


if __name__ == '__main__':
    main()
