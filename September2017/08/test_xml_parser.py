try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import time


def parse_poi_by_elementTree(filepath):
    t0 = time.time()

    tree = ET.ElementTree(file=filepath)
    pois_element_num = 0
    vde_poi = 0
    # for elem in tree.iter(tag='Pois'):
    #     pois_element_num = elem.get('Num')
    #     print pois_element_num
    #     for e in elem.iter():
    #         if e.tag == 'Poi':
    #             vde_poi += 1
    pois_element_num = tree.iter(tag='Pois').next().get('Num')
    vde_poi = len(list(tree.iter(tag='Poi')))

    cost_time = time.time() - t0
    print 'parse_poi_by_elementTree time cost is %s' % cost_time
    return pois_element_num, vde_poi


def parse_poi_by_iterparse(filepath):
    t0 = time.time()

    pois_element_num = 0
    vde_poi = 0
    for event, elem in ET.iterparse(filepath):
        if event == 'end':
            if elem.tag == 'Poi':
                vde_poi += 1
            if elem.tag == "Pois":
                pois_element_num = int(elem.get('Num'))
                break

        elem.clear()

    cost_time = time.time() - t0
    print 'parse_poi_by_iterparse time cost is %s' % cost_time
    return pois_element_num, vde_poi


from statistic import StatisticItem, XML_STREET, XML_POI
import os


def parse_street_xml_by_ET(street_file):
    """

    :param street_file:
    :return:
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


if __name__ == '__main__':
    # C:\Users\shchshan\Desktop\vde\State_14120002\POI_1414000018.xml
    # C:\Users\shchshan\Desktop\vde\State_14120001\POI_1414000001.xml
    filepath = r'C:\Users\shchshan\Desktop\Denali_VDE_CN_17Q1_20170814\VDE_CN_17Q1_20170814\State_14120001\POI_1414000001.xml'
    print parse_poi_by_elementTree(filepath)
    print parse_poi_by_iterparse(filepath)
