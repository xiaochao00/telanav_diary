try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from statistic import StatisticItem, XML_STREET, XML_POI
import os


def parse_street_xml_by_ET(street_file):
    """
    parse street file, statistic the num of street
    street_num : value of the attribute "Num" of node tag "Streets"
    vde_streets : the statistic sum of the count of node "Street" in first tag node "Streets"
    :param street_file: input file of street_file
    :return: statistic result
    """
    if not os.path.exists(street_file):
        return StatisticItem(XML_STREET, [0, 0])

    street_num = 0
    vde_streets = 0  # actual count

    for event, elem in ET.iterparse(street_file):
        if event == 'end':
            if elem.tag == 'Street':
                vde_streets += 1

            if elem.tag == "Streets":
                street_num = int(elem.get('Num'))
                break

        elem.clear()
    return StatisticItem(XML_STREET, [vde_streets, street_num])


def parse_poi_xml_by_ET(poi_file):
    """
    poi_num : value of the num attribute of node Pois
    vde_pois : the statistic sum of the count of node Poi in the first node Pois
    :param poi_file:  poi parse file
    :return:
    statistic result
    """
    if not os.path.exists(poi_file):
        return StatisticItem(XML_POI, [0, 0])

    poi_num = 0
    vde_pois = 0  # actual count

    # make sure first pois node and poi node in it
    for event, elem in ET.iterparse(poi_file):
        if event == 'end':
            if elem.tag == 'Poi':
                vde_pois += 1

            if elem.tag == "Pois":
                poi_num = int(elem.get('Num'))
                break

        elem.clear()
    return StatisticItem(XML_POI, [vde_pois, poi_num])
