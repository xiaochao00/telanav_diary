#-------------------------------------------------------------------------------
# Name:        AddContentExtractor.py
# Purpose:
#
# Author:      Michael
#
# Created:     01/08/2011
# Copyright:   (c) Michael 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import sys
import os
import xml.parsers.expat

import optparse

class Content(object):

    def __init__(self):
        self.type = None
        self.map_refers = []
        self.att_refers = []

    def to_string(self):
        if not self.map_refers or not self.type:
            return ''

        map_ref = self.map_refers[0]

        for map_refer in self.map_refers:
            assert 'Type' in map_refer
            assert 'Feature_ID' in map_refer

        att_ref = {}
        for att_refer in self.att_refers:
            att_typ = att_refer['Attribute_Type']
            att_val = att_refer['Attribute_Value']

            # filter useless phonetic data
            if att_typ == 'PhoneticLanguageCode' and att_val != 'PYM':
                return ''
            if att_typ == 'TypeOfName' and att_val == 'Address':
                return ''

            att_ref[att_typ] = att_val

        items = ['Content_Type=%s' % (self.type)]
        items.extend(map(lambda x: '%s=%s' %(x[0], x[1]), map_ref.items()))
        items.extend(map(lambda x: '%s=%s' %(x[0], x[1]), att_ref.items()))

        return ';'.join(items)

    def conten_type(self):
        return self.type.replace(' ', '_')

    def clear(self):
        self.type = None
        del self.map_refers[:]
        del self.att_refers[:]

    def __str__(self):
        return self.to_string()

class AddContentExtractor(object):

    def __init__(self, add_content_xml, out_dir):
        self.add_content_xml = add_content_xml

        self.element_status = {}

        self.content = Content()

        self.map_refer = {}
        self.att_refer = {}

        self.out_dir = out_dir

        self.add_writers = {}

        self.buffer = ''

    def __del__(self):
        for filename in self.add_writers:
            self.add_writers[filename].close()

    def start_element(self, name, attrs):
        self.element_status[name] = True

        if name == 'Content' :
            self.content.clear()
            if 'Content_Type' in attrs:
                self.content.type = attrs['Content_Type'].encode('utf-8')

        elif name == 'Map_Reference':
            self.map_refer.clear()

        elif name == 'Attribute_Reference':
            if 'Content_Type' in attrs and not self.content.type:
                self.content.type = attrs['Content_Type'].encode('utf-8')
            self.att_refer.clear()

        self.buffer = ''

    def end_element(self, name):
        if 'Type' in self.element_status and self.element_status['Type']:
            self.map_refer['Type'] = self.buffer
        elif 'Feature_ID' in self.element_status and self.element_status['Feature_ID']:
            self.map_refer['Feature_ID'] = self.buffer

        # process attribute reference
        elif 'Attribute_Type' in self.element_status and self.element_status['Attribute_Type']:
            #self.pair_att = data
            self.att_refer['Attribute_Type'] = self.buffer
        elif 'Attribute_Value' in self.element_status and self.element_status['Attribute_Value']:
            #self.pair_val = data
            self.att_refer['Attribute_Value'] = self.buffer

        if name == 'Content':
            self.dump()
        elif name == 'Map_Reference':
            map_refer = {}
            map_refer.update(self.map_refer)
            self.content.map_refers.append(map_refer)
            self.map_refer.clear()
        elif name == 'Attribute_Reference':
            att_refer = {}
            att_refer.update(self.att_refer)
            self.content.att_refers.append(att_refer)
            self.att_refer.clear()

        self.element_status[name] = False

    def dump(self):
        string = self.content.to_string()
        cont_type = self.content.conten_type()
        if not string or not cont_type:
            return

        if cont_type not in self.add_writers:
            filename = os.path.join(self.out_dir, '%s.txt'% cont_type)
            filename = os.path.abspath(filename)

            ofs = open(filename, 'w')
            self.add_writers[cont_type] = ofs

        ofs = self.add_writers[cont_type]
        ofs.write('%s\n' % string)

    def character_data(self, data):
        self.buffer += data.encode('utf-8')

    def process(self):
        parser = xml.parsers.expat.ParserCreate()

        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.character_data

        parser.ParseFile(open(self.add_content_xml,'r'))

        for writer in self.add_writers.values():
            writer.close()

def usage():
    cmd = os.path.basename(sys.argv[0])
    print 'Usage:\n'
    print '\t%s china_additional_xml_dir output_dir' %(cmd)

def main():
    """
    parser = xml.parsers.expat.ParserCreate()

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    #parser.CharacterDataHander = character_data
    parser.CharacterDataHandler = character_data

    parser.ParseFile(open(sys.argv[1],'r'))
    """
    if len(sys.argv) != 3:
        usage()
        sys.exit(-1)

    for filename in os.listdir(sys.argv[1]):
        ext = os.path.splitext(filename)[1]
        if ext != '.xml': continue

        xml_file = os.path.join(sys.argv[1], filename)
        parser = AddContentExtractor(xml_file, sys.argv[2])
        parser.process()

if __name__ == '__main__':
    main()
